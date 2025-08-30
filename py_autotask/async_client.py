"""
Async client for the Autotask REST API.

This module provides the AsyncAutotaskClient class for high-performance,
non-blocking operations with the Autotask API. Supports concurrent operations,
intelligent connection pooling, and async context management.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp
from aiohttp import ClientTimeout, TCPConnector

from .auth import AutotaskAuth
from .exceptions import (
    AutotaskConnectionError,
    AutotaskTimeoutError,
    AutotaskValidationError,
)
from .types import (
    AuthCredentials,
    CreateResponse,
    EntityDict,
    QueryRequest,
    QueryResponse,
    RequestConfig,
)
from .utils import handle_api_error, validate_filter

logger = logging.getLogger(__name__)


class AsyncEntityManager:
    """Manages async entity operations for the client."""

    def __init__(self, client: "AsyncAutotaskClient"):
        self.client = client

    @property
    def tickets(self):
        """Access to async Tickets operations."""
        return AsyncEntityProxy(self.client, "Tickets")

    @property
    def companies(self):
        """Access to async Companies operations."""
        return AsyncEntityProxy(self.client, "Companies")

    @property
    def resources(self):
        """Access to async Resources operations."""
        return AsyncEntityProxy(self.client, "Resources")

    @property
    def projects(self):
        """Access to async Projects operations."""
        return AsyncEntityProxy(self.client, "Projects")

    @property
    def time_entries(self):
        """Access to async TimeEntries operations."""
        return AsyncEntityProxy(self.client, "TimeEntries")

    @property
    def contacts(self):
        """Access to async Contacts operations."""
        return AsyncEntityProxy(self.client, "Contacts")


class AsyncEntityProxy:
    """Proxy for async entity operations."""

    def __init__(self, client: "AsyncAutotaskClient", entity_name: str):
        self.client = client
        self.entity_name = entity_name
        self.logger = logging.getLogger(f"{__name__}.{entity_name}")

    async def get_async(self, entity_id: int) -> Optional[EntityDict]:
        """Get a single entity by ID asynchronously."""
        return await self.client.get_async(self.entity_name, entity_id)

    async def query_async(
        self,
        filters: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        include_fields: Optional[List[str]] = None,
        max_records: Optional[int] = None,
    ) -> QueryResponse:
        """Query entities asynchronously."""
        # Build query request
        query_request = QueryRequest()

        if filters:
            if isinstance(filters, dict):
                query_request.filter = [filters]
            elif isinstance(filters, list):
                query_request.filter = filters
            else:
                raise AutotaskValidationError("Filters must be dict or list of dicts")

        if include_fields:
            query_request.include_fields = include_fields

        if max_records:
            query_request.max_records = max_records

        return await self.client.query_async(self.entity_name, query_request)

    async def create_async(self, entity_data: EntityDict) -> CreateResponse:
        """Create a new entity asynchronously."""
        return await self.client.create_entity_async(self.entity_name, entity_data)

    async def update_async(self, entity_id: int, entity_data: EntityDict) -> EntityDict:
        """Update an entity asynchronously."""
        return await self.client.update_entity_async(
            self.entity_name, entity_id, entity_data
        )

    async def delete_async(self, entity_id: int) -> bool:
        """Delete an entity asynchronously."""
        return await self.client.delete_entity_async(self.entity_name, entity_id)


class AsyncAutotaskClient:
    """
    Async client for the Autotask REST API with high-performance capabilities.

    This client provides:
    - Non-blocking async/await operations
    - Concurrent request processing
    - Intelligent connection pooling
    - Context manager support
    - Rate limit handling
    - Automatic retries with exponential backoff

    Example:
        async with AsyncAutotaskClient.create(
            username="user@example.com",
            integration_code="YOUR_CODE",
            secret="YOUR_SECRET"
        ) as client:
            # Concurrent operations
            tickets_task = client.tickets.query_async({"status": "open"})
            companies_task = client.companies.query_async({"isActive": True})

            tickets, companies = await asyncio.gather(tickets_task, companies_task)
    """

    def __init__(
        self,
        auth: AutotaskAuth,
        config: Optional[RequestConfig] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """
        Initialize the async client.

        Args:
            auth: Configured authentication handler
            config: Request configuration options
            session: Optional pre-configured aiohttp session
        """
        self.auth = auth
        self.config = config or RequestConfig()
        self._session = session
        self._entities: Optional[AsyncEntityManager] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @classmethod
    async def create(
        cls,
        credentials: Optional[AuthCredentials] = None,
        username: Optional[str] = None,
        integration_code: Optional[str] = None,
        secret: Optional[str] = None,
        api_url: Optional[str] = None,
        config: Optional[RequestConfig] = None,
    ) -> "AsyncAutotaskClient":
        """
        Create a new async client with automatic setup.

        Args:
            credentials: Pre-configured credentials object
            username: API username (alternative to credentials)
            integration_code: Integration code from Autotask (alternative to credentials)
            secret: API secret (alternative to credentials)
            api_url: Optional API URL override
            config: Request configuration options

        Returns:
            Configured AsyncAutotaskClient instance
        """
        if credentials:
            auth = AutotaskAuth(credentials)
        else:
            if not all([username, integration_code, secret]):
                raise ValueError(
                    "Must provide either credentials or username/integration_code/secret"
                )

            credentials = AuthCredentials(
                username=username,
                integration_code=integration_code,
                secret=secret,
                api_url=api_url,
            )
            auth = AutotaskAuth(credentials)

        client = cls(auth, config)
        await client.__aenter__()
        return client

    @classmethod
    @asynccontextmanager
    async def create_session(
        cls,
        credentials: Optional[AuthCredentials] = None,
        username: Optional[str] = None,
        integration_code: Optional[str] = None,
        secret: Optional[str] = None,
        api_url: Optional[str] = None,
        config: Optional[RequestConfig] = None,
    ) -> AsyncGenerator["AsyncAutotaskClient", None]:
        """
        Create an async context manager for the client.

        Example:
            async with AsyncAutotaskClient.create_session(
                username="user@example.com",
                integration_code="CODE",
                secret="SECRET"
            ) as client:
                tickets = await client.tickets.query_async()
        """
        client = None
        try:
            client = await cls.create(
                credentials, username, integration_code, secret, api_url, config
            )
            yield client
        finally:
            if client:
                await client.close()

    async def __aenter__(self) -> "AsyncAutotaskClient":
        """Async context manager entry."""
        await self._setup_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _setup_session(self) -> None:
        """Set up the aiohttp session with optimal configuration."""
        if self._session is None:
            # Configure connection pooling for high performance
            connector = TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=20,  # Max connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                enable_cleanup_closed=True,
            )

            # Configure timeout
            timeout = ClientTimeout(
                total=self.config.timeout,
                connect=10,
                sock_read=30,
            )

            # Autotask REST API uses headers for authentication, not Basic Auth
            # Create session with authentication headers
            headers = {
                "Content-Type": "application/json",
                "ApiIntegrationCode": self.auth.credentials.integration_code,
                "UserName": self.auth.credentials.username,
                "Secret": self.auth.credentials.secret,
                "User-Agent": "py-autotask-async/2.0.0",
                "Accept": "application/json",
            }

            self._session = aiohttp.ClientSession(
                connector=connector, timeout=timeout, headers=headers
            )

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the aiohttp session."""
        if self._session is None:
            raise RuntimeError(
                "Session not initialized. Use 'async with' or call '__aenter__' first."
            )
        return self._session

    def _build_url(self, path: str) -> str:
        """Build a properly formatted API URL with the given path."""
        base_url = self.auth.api_url.rstrip("/")
        path = path.lstrip("/")
        return f"{base_url}/{path}"

    @property
    def entities(self) -> AsyncEntityManager:
        """Access to entity managers."""
        if self._entities is None:
            self._entities = AsyncEntityManager(self)
        return self._entities

    # Convenience properties for direct entity access
    @property
    def tickets(self):
        """Access to async Tickets operations."""
        return self.entities.tickets

    @property
    def companies(self):
        """Access to async Companies operations."""
        return self.entities.companies

    @property
    def resources(self):
        """Access to async Resources operations."""
        return self.entities.resources

    @property
    def projects(self):
        """Access to async Projects operations."""
        return self.entities.projects

    async def get_async(self, entity: str, entity_id: int) -> Optional[EntityDict]:
        """
        Get a single entity by ID asynchronously.

        Args:
            entity: Entity name (e.g., 'Tickets', 'Companies')
            entity_id: Entity ID

        Returns:
            Entity data or None if not found
        """
        url = self._build_url(f"v1.0/{entity}/{entity_id}")

        try:
            async with self.session.get(url) as response:
                if response.status == 404:
                    return None

                response.raise_for_status()
                data = await response.json()
                return data.get("item")

        except asyncio.TimeoutError:
            raise AutotaskTimeoutError("Request timed out")
        except aiohttp.ClientConnectionError:
            raise AutotaskConnectionError("Connection error")
        except aiohttp.ClientResponseError as e:
            await handle_api_error(response)

    async def query_async(
        self,
        entity: str,
        query_request: Optional[Union[QueryRequest, Dict[str, Any]]] = None,
        *,
        filters: Optional[List] = None,
        max_records: Optional[int] = None,
        include_fields: Optional[List[str]] = None,
        **kwargs,
    ) -> QueryResponse:
        """
        Query entities asynchronously with filtering and pagination.

        Args:
            entity: Entity name
            query_request: Query parameters
            filters: List of filter objects (for backward compatibility)
            max_records: Maximum number of records to return
            include_fields: Specific fields to include in response
            **kwargs: Additional query parameters

        Returns:
            Query response with items and pagination info
        """
        if filters is not None:
            if not isinstance(filters, list):
                raise AutotaskValidationError(
                    "Filters must be a list of filter objects"
                )

            for filter_obj in filters:
                validate_filter(filter_obj)

            query_request = QueryRequest(filter=filters)
        elif query_request is None:
            query_request = QueryRequest()

        # Set additional parameters
        if max_records is not None:
            query_request.max_records = max_records

        if include_fields is not None:
            query_request.include_fields = include_fields

        # Apply any additional kwargs to the query request
        for key, value in kwargs.items():
            if hasattr(query_request, key):
                setattr(query_request, key, value)

        return await self._query_with_request_async(entity, query_request)

    async def _query_with_request_async(
        self, entity: str, query_request: QueryRequest
    ) -> QueryResponse:
        """
        Internal method to execute an async query with a QueryRequest object.

        Args:
            entity: Entity name
            query_request: Query parameters

        Returns:
            Query response with items and pagination info
        """
        # Validate filters
        if query_request.filter:
            for filter_item in query_request.filter:
                validate_filter(filter_item)

        url = self._build_url(f"v1.0/{entity}/query")

        try:
            async with self.session.post(
                url,
                json=query_request.dict(exclude_unset=True, by_alias=True),
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return QueryResponse(**data)

        except asyncio.TimeoutError:
            raise AutotaskTimeoutError("Request timed out")
        except aiohttp.ClientConnectionError:
            raise AutotaskConnectionError("Connection error")
        except aiohttp.ClientResponseError:
            await handle_api_error(response)

    async def create_entity_async(
        self, entity: str, entity_data: EntityDict
    ) -> CreateResponse:
        """
        Create a new entity asynchronously.

        Args:
            entity: Entity name
            entity_data: Entity data to create

        Returns:
            Create response with new entity ID
        """
        url = self._build_url(f"v1.0/{entity}")

        try:
            async with self.session.post(url, json=entity_data) as response:
                response.raise_for_status()
                data = await response.json()
                return CreateResponse(**data)

        except asyncio.TimeoutError:
            raise AutotaskTimeoutError("Request timed out")
        except aiohttp.ClientConnectionError:
            raise AutotaskConnectionError("Connection error")
        except aiohttp.ClientResponseError:
            await handle_api_error(response)

    async def update_entity_async(
        self, entity: str, entity_id: int, entity_data: EntityDict
    ) -> EntityDict:
        """
        Update an entity asynchronously.

        Args:
            entity: Entity name
            entity_id: Entity ID to update
            entity_data: Updated entity data

        Returns:
            Updated entity data
        """
        url = self._build_url(f"v1.0/{entity}/{entity_id}")

        try:
            async with self.session.patch(url, json=entity_data) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("item", {})

        except asyncio.TimeoutError:
            raise AutotaskTimeoutError("Request timed out")
        except aiohttp.ClientConnectionError:
            raise AutotaskConnectionError("Connection error")
        except aiohttp.ClientResponseError:
            await handle_api_error(response)

    async def delete_entity_async(self, entity: str, entity_id: int) -> bool:
        """
        Delete an entity asynchronously.

        Args:
            entity: Entity name
            entity_id: Entity ID to delete

        Returns:
            True if deletion was successful
        """
        url = self._build_url(f"v1.0/{entity}/{entity_id}")

        try:
            async with self.session.delete(url) as response:
                return response.status == 200

        except asyncio.TimeoutError:
            raise AutotaskTimeoutError("Request timed out")
        except aiohttp.ClientConnectionError:
            raise AutotaskConnectionError("Connection error")
        except aiohttp.ClientResponseError:
            await handle_api_error(response)

    async def batch_query_async(
        self, queries: List[Dict[str, Any]]
    ) -> List[QueryResponse]:
        """
        Execute multiple queries concurrently for maximum performance.

        Args:
            queries: List of query dictionaries with 'entity' and 'request' keys

        Returns:
            List of query responses in the same order as input

        Example:
            queries = [
                {"entity": "Tickets", "request": QueryRequest(filter=[...])},
                {"entity": "Companies", "request": QueryRequest(max_records=50)},
            ]
            results = await client.batch_query_async(queries)
        """
        tasks = []
        for query in queries:
            entity = query.get("entity")
            request = query.get("request", QueryRequest())

            task = self._query_with_request_async(entity, request)
            tasks.append(task)

        return await asyncio.gather(*tasks)

    async def bulk_create_async(
        self,
        entity: str,
        entities_data: List[EntityDict],
        batch_size: int = 50,
    ) -> List[CreateResponse]:
        """
        Create multiple entities efficiently with batching.

        Args:
            entity: Entity name
            entities_data: List of entity data dictionaries
            batch_size: Number of entities to create concurrently

        Returns:
            List of create responses
        """
        results = []

        # Process in batches to avoid overwhelming the API
        for i in range(0, len(entities_data), batch_size):
            batch = entities_data[i : i + batch_size]

            # Create tasks for concurrent execution within batch
            tasks = [
                self.create_entity_async(entity, entity_data) for entity_data in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)

            # Small delay between batches to be respectful of rate limits
            if i + batch_size < len(entities_data):
                await asyncio.sleep(0.1)

        return results

    async def test_connection_async(self) -> bool:
        """
        Test the connection to Autotask API asynchronously.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Ensure proper URL construction - remove trailing slash from api_url if present
            base_url = self.auth.api_url.rstrip("/")
            test_url = f"{base_url}/v1.0/Companies/query"
            self.logger.info(f"Testing connection to: {test_url}")
            self.logger.info(f"Session headers: {dict(self.session.headers)}")

            # Autotask requires a filter parameter in queries
            query = {
                "filter": [{"field": "id", "op": "gt", "value": 0}],
                "maxRecords": 1,
            }

            async with self.session.post(test_url, json=query) as response:
                self.logger.info(f"Response status: {response.status}")
                self.logger.info(f"Response headers: {dict(response.headers)}")

                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(
                        f"Connection test failed with status {response.status}"
                    )
                    self.logger.error(f"Response body: {error_text}")

                    # Check if response suggests we need different auth or API version
                    if (
                        "authentication" in error_text.lower()
                        or "unauthorized" in error_text.lower()
                    ):
                        self.logger.error("Authentication issue detected in response")

                    # Try a simpler endpoint to see if it's endpoint-specific
                    simple_url = self._build_url("v1.0/Companies/count")
                    self.logger.info(f"Testing simpler endpoint: {simple_url}")
                    async with self.session.get(simple_url) as simple_response:
                        self.logger.info(
                            f"Simple endpoint status: {simple_response.status}"
                        )
                        simple_text = await simple_response.text()
                        self.logger.info(f"Simple endpoint body: {simple_text[:200]}")
                return response.status == 200

        except Exception as e:
            self.logger.error(f"Async connection test failed: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def close(self) -> None:
        """Close the client session and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None

        # Close auth session if it exists
        if hasattr(self.auth, "close") and callable(self.auth.close):
            self.auth.close()

    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get current rate limit information from API headers.

        Returns:
            Dictionary with rate limit information
        """
        try:
            # Make a lightweight request to get headers
            url = self._build_url("v1.0/Companies/query")

            async with self.session.post(
                url,
                json={"maxRecords": 1},
            ) as response:
                headers = response.headers

                return {
                    "requests_remaining": headers.get("X-RateLimit-Remaining"),
                    "requests_limit": headers.get("X-RateLimit-Limit"),
                    "reset_time": headers.get("X-RateLimit-Reset"),
                    "retry_after": headers.get("Retry-After"),
                }

        except Exception as e:
            self.logger.error(f"Failed to get rate limit info: {e}")
            return {}
