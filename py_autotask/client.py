"""
Main client class for the Autotask REST API.

This module provides the primary interface for interacting with the Autotask API,
including automatic zone detection, entity management, and HTTP operations.
"""

import logging
from typing import Any, Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth import AutotaskAuth
from .entities import EntityManager
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
from .utils import (
    handle_api_error,
    validate_filter,
)

logger = logging.getLogger(__name__)


class AutotaskClient:
    """
    Main client for interacting with the Autotask REST API.

    This client provides:
    - Automatic zone detection and authentication
    - Entity-specific operations through managers
    - Intelligent pagination and error handling
    - Retry mechanisms with backoff
    - Rate limiting awareness

    Example:
        client = AutotaskClient.create(
            username="user@example.com",
            integration_code="YOUR_CODE",
            secret="YOUR_SECRET"
        )

        # Get a ticket
        ticket = client.tickets.get(12345)

        # Query companies
        companies = client.companies.query({
            "filter": [{"op": "eq", "field": "isActive", "value": "true"}]
        })
    """

    def __init__(
        self, auth: AutotaskAuth, config: Optional[RequestConfig] = None
    ) -> None:
        """
        Initialize the client with authentication and configuration.

        Args:
            auth: Configured authentication handler
            config: Request configuration options
        """
        self.auth = auth
        self.config = config or RequestConfig()
        self._session: Optional[requests.Session] = None
        self._entities: Optional[EntityManager] = None

        # Set up logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @classmethod
    def create(
        cls,
        credentials: Optional[AuthCredentials] = None,
        username: Optional[str] = None,
        integration_code: Optional[str] = None,
        secret: Optional[str] = None,
        api_url: Optional[str] = None,
        config: Optional[RequestConfig] = None,
    ) -> "AutotaskClient":
        """
        Create a new client with credentials.

        Args:
            credentials: Pre-configured credentials object
            username: API username (alternative to credentials)
            integration_code: Integration code from Autotask (alternative to credentials)
            secret: API secret (alternative to credentials)
            api_url: Override API URL (optional, will auto-detect)
            config: Request configuration

        Returns:
            Configured AutotaskClient instance
        """
        if credentials is None:
            if not all([username, integration_code, secret]):
                raise ValueError(
                    "Must provide either credentials object or username/integration_code/secret"
                )
            credentials = AuthCredentials(
                username=username,
                integration_code=integration_code,
                secret=secret,
                api_url=api_url,
            )

        auth = AutotaskAuth(credentials)
        return cls(auth, config)

    @property
    def session(self) -> requests.Session:
        """Get or create HTTP session with retry configuration."""
        if not self._session:
            self._session = self.auth.get_session()

            # Configure retry strategy
            retry_strategy = Retry(
                total=self.config.max_retries,
                backoff_factor=self.config.retry_backoff,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=[
                    "HEAD",
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "OPTIONS",
                    "TRACE",
                ],
            )

            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

        return self._session

    @property
    def entities(self) -> EntityManager:
        """Get entity manager for accessing API entities."""
        if not self._entities:
            self._entities = EntityManager(self)
        return self._entities

    # Convenience properties for common entities
    @property
    def tickets(self):
        """Access to Tickets entity operations."""
        return self.entities.tickets

    @property
    def companies(self):
        """Access to Companies entity operations."""
        return self.entities.companies

    @property
    def contacts(self):
        """Access to Contacts entity operations."""
        return self.entities.contacts

    @property
    def projects(self):
        """Access to Projects entity operations."""
        return self.entities.projects

    @property
    def resources(self):
        """Access to Resources entity operations."""
        return self.entities.resources

    @property
    def contracts(self):
        """Access to Contracts entity operations."""
        return self.entities.contracts

    @property
    def time_entries(self):
        """Access to TimeEntries entity operations."""
        return self.entities.time_entries

    @property
    def attachments(self):
        """Access to Attachments entity operations."""
        return self.entities.attachments

    def get(self, entity: str, entity_id: int) -> Optional[EntityDict]:
        """
        Get a single entity by ID.

        Args:
            entity: Entity name (e.g., 'Tickets', 'Companies')
            entity_id: Entity ID

        Returns:
            Entity data or None if not found
        """
        url = f"{self.auth.api_url}/v1.0/{entity}/{entity_id}"

        try:
            response = self.session.get(url, timeout=self.config.timeout)

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            return data.get("item")

        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise AutotaskConnectionError("Connection error")
        except requests.exceptions.HTTPError:
            handle_api_error(response)

    def query(
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
        Query entities with filtering and pagination.

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
            # Convert list of filters to QueryRequest format
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

        return self._query_with_request(entity, query_request)

    def _query_with_request(
        self, entity: str, query_request: QueryRequest
    ) -> QueryResponse:
        """
        Internal method to execute a query with a QueryRequest object.

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

        url = f"{self.auth.api_url}/v1.0/{entity}/query"

        try:
            response = self.session.post(
                url,
                json=query_request.dict(exclude_unset=True, by_alias=True),
                timeout=self.config.timeout,
            )

            response.raise_for_status()
            data = response.json()

            return QueryResponse(**data)

        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise AutotaskConnectionError("Connection error")
        except requests.exceptions.HTTPError:
            handle_api_error(response)

    def create_entity(self, entity: str, entity_data: EntityDict) -> CreateResponse:
        """
        Create a new entity.

        Args:
            entity: Entity name
            entity_data: Entity data to create

        Returns:
            Create response with new entity ID
        """
        url = f"{self.auth.api_url}/v1.0/{entity}"

        try:
            response = self.session.post(
                url, json=entity_data, timeout=self.config.timeout
            )

            response.raise_for_status()
            data = response.json()

            return CreateResponse(**data)

        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise AutotaskConnectionError("Connection error")
        except requests.exceptions.HTTPError:
            handle_api_error(response)

    def update(self, entity: str, entity_data: EntityDict) -> EntityDict:
        """
        Update an existing entity.

        Args:
            entity: Entity name
            entity_data: Entity data with ID and fields to update

        Returns:
            Updated entity data
        """
        entity_id = entity_data.get("id")
        if not entity_id:
            raise ValueError("Entity data must include 'id' field for updates")

        url = f"{self.auth.api_url}/v1.0/{entity}/{entity_id}"

        try:
            response = self.session.patch(
                url, json=entity_data, timeout=self.config.timeout
            )

            response.raise_for_status()
            data = response.json()

            return data.get("item", {})

        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise AutotaskConnectionError("Connection error")
        except requests.exceptions.HTTPError:
            handle_api_error(response)

    def delete(self, entity: str, entity_id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity: Entity name
            entity_id: Entity ID to delete

        Returns:
            True if successful
        """
        url = f"{self.auth.api_url}/v1.0/{entity}/{entity_id}"

        try:
            response = self.session.delete(url, timeout=self.config.timeout)
            response.raise_for_status()
            return True

        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise AutotaskConnectionError("Connection error")
        except requests.exceptions.HTTPError:
            handle_api_error(response)

    def count(
        self,
        entity: str,
        query_request: Optional[Union[QueryRequest, Dict[str, Any]]] = None,
    ) -> int:
        """
        Count entities matching query criteria.

        Args:
            entity: Entity name
            query_request: Query parameters

        Returns:
            Count of matching entities
        """
        if isinstance(query_request, dict):
            query_request = QueryRequest(**query_request)
        elif query_request is None:
            query_request = QueryRequest()

        url = f"{self.auth.api_url}/v1.0/{entity}/query/count"

        try:
            response = self.session.post(
                url,
                json=query_request.dict(exclude_unset=True, by_alias=True),
                timeout=self.config.timeout,
            )

            response.raise_for_status()
            data = response.json()

            return data.get("queryCount", 0)

        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise AutotaskConnectionError("Connection error")
        except requests.exceptions.HTTPError:
            handle_api_error(response)

    def get_field_info(self, entity: str) -> Dict[str, Any]:
        """
        Get field metadata for an entity.

        Args:
            entity: Entity name

        Returns:
            Field metadata information
        """
        url = f"{self.auth.api_url}/v1.0/{entity}/entityInformation/fields"

        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise AutotaskConnectionError("Connection error")
        except requests.exceptions.HTTPError:
            handle_api_error(response)

    def get_entity_info(self, entity: str) -> Dict[str, Any]:
        """
        Get general information about an entity.

        Args:
            entity: Entity name

        Returns:
            Entity information
        """
        url = f"{self.auth.api_url}/v1.0/{entity}/entityInformation"

        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise AutotaskConnectionError("Connection error")
        except requests.exceptions.HTTPError:
            handle_api_error(response)

    def close(self) -> None:
        """Close the client and clean up resources."""
        if self._session:
            self._session.close()
        self.auth.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # Batch Operations for Phase 4
    def batch_create(
        self, entity: str, entities_data: List[EntityDict], batch_size: int = 200
    ) -> List[CreateResponse]:
        """
        Create multiple entities in batches.

        Args:
            entity: Entity name
            entities_data: List of entity data to create
            batch_size: Maximum entities per batch (API limit is 200)

        Returns:
            List of create responses
        """
        if batch_size > 200:
            raise ValueError("Batch size cannot exceed 200 (API limit)")

        results = []
        total_batches = (len(entities_data) + batch_size - 1) // batch_size

        for i in range(0, len(entities_data), batch_size):
            batch = entities_data[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            logger.info(
                f"Processing batch {batch_num}/{total_batches} ({len(batch)} entities)"
            )

            url = f"{self.auth.api_url}/v1.0/{entity}/batch"

            try:
                response = self.session.post(
                    url, json=batch, timeout=self.config.timeout
                )

                response.raise_for_status()
                data = response.json()

                # Handle batch response format
                if isinstance(data, list):
                    batch_results = [CreateResponse(**item) for item in data]
                else:
                    batch_results = [CreateResponse(**data)]

                results.extend(batch_results)

            except requests.exceptions.Timeout:
                raise AutotaskTimeoutError(f"Batch {batch_num} timed out")
            except requests.exceptions.ConnectionError:
                raise AutotaskConnectionError(f"Batch {batch_num} connection error")
            except requests.exceptions.HTTPError:
                logger.error(f"Batch {batch_num} failed with HTTP error")
                handle_api_error(response)

        return results

    def batch_update(
        self, entity: str, entities_data: List[EntityDict], batch_size: int = 200
    ) -> List[EntityDict]:
        """
        Update multiple entities in batches.

        Args:
            entity: Entity name
            entities_data: List of entity data to update (must include 'id' field)
            batch_size: Maximum entities per batch (API limit is 200)

        Returns:
            List of updated entity data
        """
        if batch_size > 200:
            raise ValueError("Batch size cannot exceed 200 (API limit)")

        # Validate all entities have ID
        for i, entity_data in enumerate(entities_data):
            if not entity_data.get("id"):
                raise ValueError(
                    f"Entity at index {i} missing 'id' field for batch update"
                )

        results = []
        total_batches = (len(entities_data) + batch_size - 1) // batch_size

        for i in range(0, len(entities_data), batch_size):
            batch = entities_data[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            logger.info(
                f"Processing update batch {batch_num}/{total_batches} ({len(batch)} entities)"
            )

            url = f"{self.auth.api_url}/v1.0/{entity}/batch"

            try:
                response = self.session.patch(
                    url, json=batch, timeout=self.config.timeout
                )

                response.raise_for_status()
                data = response.json()

                # Handle batch response format
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)

            except requests.exceptions.Timeout:
                raise AutotaskTimeoutError(f"Update batch {batch_num} timed out")
            except requests.exceptions.ConnectionError:
                raise AutotaskConnectionError(
                    f"Update batch {batch_num} connection error"
                )
            except requests.exceptions.HTTPError:
                logger.error(f"Update batch {batch_num} failed with HTTP error")
                handle_api_error(response)

        return results

    def batch_delete(
        self, entity: str, entity_ids: List[int], batch_size: int = 200
    ) -> List[bool]:
        """
        Delete multiple entities in batches.

        Args:
            entity: Entity name
            entity_ids: List of entity IDs to delete
            batch_size: Maximum entities per batch (API limit is 200)

        Returns:
            List of success indicators
        """
        if batch_size > 200:
            raise ValueError("Batch size cannot exceed 200 (API limit)")

        results = []
        total_batches = (len(entity_ids) + batch_size - 1) // batch_size

        for i in range(0, len(entity_ids), batch_size):
            batch = entity_ids[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            logger.info(
                f"Processing delete batch {batch_num}/{total_batches} ({len(batch)} entities)"
            )

            url = f"{self.auth.api_url}/v1.0/{entity}/batch"

            try:
                response = self.session.delete(
                    url, json={"ids": batch}, timeout=self.config.timeout
                )

                response.raise_for_status()

                # Successful deletion for all items in batch
                batch_results = [True] * len(batch)
                results.extend(batch_results)

            except requests.exceptions.Timeout:
                raise AutotaskTimeoutError(f"Delete batch {batch_num} timed out")
            except requests.exceptions.ConnectionError:
                raise AutotaskConnectionError(
                    f"Delete batch {batch_num} connection error"
                )
            except requests.exceptions.HTTPError:
                logger.error(f"Delete batch {batch_num} failed with HTTP error")
                # For deletions, we might want to continue with other batches
                batch_results = [False] * len(batch)
                results.extend(batch_results)

        return results
