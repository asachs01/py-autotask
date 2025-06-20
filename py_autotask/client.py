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
    AutotaskAPIError,
    AutotaskConnectionError,
    AutotaskRateLimitError,
    AutotaskTimeoutError,
)
from .types import (
    AuthCredentials,
    RequestConfig,
    QueryRequest,
    QueryResponse,
    CreateResponse,
    EntityDict,
    EntityList,
)
from .utils import (
    paginate_query,
    validate_filter,
    build_query_url,
    parse_api_response,
    handle_api_error,
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
        self,
        auth: AutotaskAuth,
        config: Optional[RequestConfig] = None
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
        username: str,
        integration_code: str,
        secret: str,
        api_url: Optional[str] = None,
        config: Optional[RequestConfig] = None,
    ) -> "AutotaskClient":
        """
        Create a new client with credentials.
        
        Args:
            username: API username
            integration_code: Integration code from Autotask
            secret: API secret
            api_url: Override API URL (optional, will auto-detect)
            config: Request configuration
            
        Returns:
            Configured AutotaskClient instance
        """
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
                allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
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
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
            handle_api_error(response)
    
    def query(
        self,
        entity: str,
        query_request: Optional[Union[QueryRequest, Dict[str, Any]]] = None
    ) -> QueryResponse:
        """
        Query entities with filtering and pagination.
        
        Args:
            entity: Entity name
            query_request: Query parameters
            
        Returns:
            Query response with items and pagination info
        """
        if isinstance(query_request, dict):
            query_request = QueryRequest(**query_request)
        elif query_request is None:
            query_request = QueryRequest()
            
        # Validate filters
        if query_request.filter:
            for filter_item in query_request.filter:
                validate_filter(filter_item)
        
        url = f"{self.auth.api_url}/v1.0/{entity}/query"
        
        try:
            response = self.session.post(
                url,
                json=query_request.dict(exclude_unset=True, by_alias=True),
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            return QueryResponse(**data)
            
        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
            handle_api_error(response)
    
    def create(self, entity: str, entity_data: EntityDict) -> CreateResponse:
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
                url,
                json=entity_data,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            return CreateResponse(**data)
            
        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
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
                url,
                json=entity_data,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data.get("item", {})
            
        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
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
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
            handle_api_error(response)
    
    def count(
        self,
        entity: str,
        query_request: Optional[Union[QueryRequest, Dict[str, Any]]] = None
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
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data.get("queryCount", 0)
            
        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError("Request timed out")
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
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
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
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
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
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