"""
Authentication and zone detection for Autotask API.

This module handles the authentication flow and automatic zone detection
required for Autotask API access.
"""

import logging
import time
from typing import Dict, Optional, Union

import requests
from requests.auth import HTTPBasicAuth

from .exceptions import (
    AutotaskAPIError,
    AutotaskAuthError,
    AutotaskConnectionError,
    AutotaskZoneError,
)
from .types import AuthCredentials, ZoneInfo

logger = logging.getLogger(__name__)


class AutotaskAuth:
    """
    Handles authentication and zone detection for Autotask API.

    The Autotask API uses regional zones, and the correct zone must be
    determined before making API calls. This class handles that process
    automatically with intelligent caching and fallback strategies.
    """

    ZONE_INFO_URL = (
        "https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation"
    )

    # Zone URL mappings for all Autotask regions
    ZONE_URLS = {
        1: "https://webservices2.autotask.net/atservicesrest",  # US East
        2: "https://webservices6.autotask.net/atservicesrest",  # US West
        3: "https://webservices14.autotask.net/atservicesrest",  # EU London
        4: "https://webservices16.autotask.net/atservicesrest",  # Australia
        5: "https://webservices5.autotask.net/atservicesrest",  # Germany
        6: "https://webservices12.autotask.net/atservicesrest",  # China
        7: "https://webservices24.autotask.net/atservicesrest",  # India
    }

    # Cache for zone information
    _zone_cache: Dict[str, Dict] = {}

    def __init__(self, credentials: AuthCredentials) -> None:
        """
        Initialize authentication with credentials.

        Args:
            credentials: Authentication credentials
        """
        self.credentials = credentials
        self._zone_info: Optional[ZoneInfo] = None
        self._session: Optional[requests.Session] = None
        self._cache_expiry = 3600  # 1 hour cache expiry

    @property
    def zone_info(self) -> Optional[ZoneInfo]:
        """Get cached zone information."""
        return self._zone_info

    @property
    def api_url(self) -> str:
        """Get the API base URL, detecting zone if necessary."""
        if self.credentials.api_url:
            return self.credentials.api_url

        if not self._zone_info:
            self._detect_zone()

        if not self._zone_info:
            raise AutotaskZoneError("Failed to detect API zone")

        return self._zone_info.url

    def get_session(self) -> requests.Session:
        """
        Get authenticated session for API requests with connection pooling.

        Returns:
            Configured requests session with authentication and retry logic
        """
        if not self._session:
            self._session = requests.Session()

            # Set up authentication
            self._session.auth = HTTPBasicAuth(
                self.credentials.username, self.credentials.secret
            )

            # Configure headers
            self._session.headers.update(
                {
                    "Content-Type": "application/json",
                    "ApiIntegrationcode": self.credentials.integration_code,
                    "User-Agent": "py-autotask/2.0.0",
                    "Accept": "application/json",
                }
            )

            # Configure connection pooling for better performance
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST", "PUT", "PATCH", "DELETE"],
            )

            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=20,
                pool_block=False,
            )

            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

        return self._session

    def _detect_zone(self) -> None:
        """
        Detect the correct API zone for the authenticated user.

        This method calls the zone information endpoint to determine
        the correct regional API endpoint to use, with intelligent caching
        and fallback strategies.

        Raises:
            AutotaskZoneError: If zone detection fails
            AutotaskAuthError: If authentication fails
            AutotaskConnectionError: If connection fails
        """
        # Check cache first
        cache_key = f"{self.credentials.username}:{self.credentials.integration_code}"
        if cache_key in self._zone_cache:
            cached_data = self._zone_cache[cache_key]
            cache_time = cached_data.get("timestamp", 0)
            if time.time() - cache_time < self._cache_expiry:
                self._zone_info = ZoneInfo(**cached_data["zone_info"])
                logger.info(f"Using cached zone: {self._zone_info.url}")
                return

        try:
            # Build zone detection URL with user parameter
            zone_url = f"{self.ZONE_INFO_URL}?user={self.credentials.username}"
            logger.info(f"Detecting Autotask API zone using: {zone_url}")

            # Create a temporary session for zone detection
            session = requests.Session()
            session.auth = HTTPBasicAuth(
                self.credentials.username, self.credentials.secret
            )
            session.headers.update(
                {
                    "Content-Type": "application/json",
                    "ApiIntegrationcode": self.credentials.integration_code,
                    "User-Agent": "py-autotask/2.0.0",
                }
            )

            # Allow redirects and log them
            response = session.get(zone_url, timeout=30, allow_redirects=True)

            # Log if there was a redirect
            if response.history:
                logger.warning(
                    f"Zone detection was redirected from {self.ZONE_INFO_URL} to {response.url}"
                )

            if response.status_code == 404:
                logger.error(f"Zone detection endpoint not found at {response.url}")
                # Try with HTTP as a fallback in case of environment-specific issues
                # Also try without user parameter as a second fallback
                if response.url.startswith("https://"):
                    http_url = response.url.replace("https://", "http://", 1)
                    logger.warning(f"Trying HTTP fallback: {http_url}")
                    try:
                        http_response = session.get(
                            http_url, timeout=30, allow_redirects=True
                        )
                        if http_response.ok:
                            response = http_response
                            logger.info("HTTP fallback succeeded")
                        else:
                            raise AutotaskConnectionError(
                                f"Zone detection endpoint not found at either HTTPS or HTTP.\n"
                                f"HTTPS URL: {response.url} (404)\n"
                                f"HTTP URL: {http_url} ({http_response.status_code})\n"
                                "Please ensure you have the latest version of py-autotask."
                            )
                    except requests.exceptions.RequestException:
                        raise AutotaskConnectionError(
                            f"Zone detection endpoint not found. URL: {response.url}\n"
                            "This may indicate an API endpoint change. Please ensure you have "
                            "the latest version of py-autotask or check Autotask API documentation."
                        )
                else:
                    raise AutotaskConnectionError(
                        f"Zone detection endpoint not found. URL: {response.url}\n"
                        "This may indicate an API endpoint change. Please ensure you have "
                        "the latest version of py-autotask or check Autotask API documentation."
                    )
            elif response.status_code == 401:
                raise AutotaskAuthError(
                    "Authentication failed during zone detection. "
                    "Please check your username, integration code, and secret."
                )
            elif response.status_code == 500:
                # Autotask returns 500 for various auth errors
                error_data = response.json() if response.content else {}
                errors = error_data.get("errors", [])

                if any(
                    "Zone information could not be determined" in str(err)
                    for err in errors
                ):
                    # This usually means invalid username or domain
                    raise AutotaskAuthError(
                        "Invalid API username or domain. Zone information could not be determined."
                    )
                elif any("IntegrationCode is invalid" in str(err) for err in errors):
                    raise AutotaskAuthError(
                        "Invalid integration code. Please check your credentials."
                    )
                else:
                    raise AutotaskAPIError(
                        f"Zone detection failed: {', '.join(map(str, errors))}"
                    )
            elif not response.ok:
                # Try fallback zone detection for other errors
                self._fallback_zone_detection()
                return

            # Parse zone information
            try:
                zone_data = response.json()
                if not isinstance(zone_data, dict) or "url" not in zone_data:
                    raise AutotaskZoneError(
                        "Invalid zone information received from API. "
                        "Response missing required fields."
                    )

                self._zone_info = ZoneInfo(**zone_data)
                logger.info(f"Detected API zone: {self._zone_info.url}")

                # Cache the zone information
                self._zone_cache[cache_key] = {
                    "zone_info": {
                        "url": self._zone_info.url,
                        "dataBaseType": self._zone_info.data_base_type,
                        "ciLevel": self._zone_info.ci_level,
                    },
                    "timestamp": time.time(),
                }

            except (ValueError, TypeError) as e:
                raise AutotaskZoneError(f"Invalid zone information format: {str(e)}")

        except requests.exceptions.Timeout:
            raise AutotaskConnectionError("Request timeout during zone detection")
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(
                f"Connection error during zone detection: {str(e)}"
            )
        except requests.exceptions.RequestException as e:
            raise AutotaskConnectionError(
                f"Network error during zone detection: {str(e)}"
            )

    def _fallback_zone_detection(self) -> None:
        """
        Fallback zone detection using intelligent heuristics.
        Tries HTTP if HTTPS fails as some environments may have redirect issues.
        """
        logger.info("Using fallback zone detection strategy")

        # Strategy 1: Detect from email domain patterns
        domain = (
            self.credentials.username.split("@")[-1].lower()
            if "@" in self.credentials.username
            else ""
        )

        zone_id = 1  # Default to US East

        # Common domain to zone mappings
        if any(tld in domain for tld in [".eu", ".uk", ".fr", ".es", ".it", ".nl"]):
            zone_id = 3  # Europe
        elif ".de" in domain:
            zone_id = 5  # Germany
        elif ".au" in domain:
            zone_id = 4  # Australia
        elif any(tld in domain for tld in [".in", ".asia"]):
            zone_id = 7  # India
        elif ".cn" in domain:
            zone_id = 6  # China
        elif ".ca" in domain:
            zone_id = 1  # US East for Canada

        zone_url = self.ZONE_URLS.get(zone_id, self.ZONE_URLS[1])

        self._zone_info = ZoneInfo(
            url=zone_url,
            dataBaseType="Production",  # Default for production environments
            ciLevel=1,  # Default CI level
        )
        logger.info(f"Fallback zone selected: {zone_url} (Zone {zone_id})")

    def set_zone_manually(self, zone: Union[int, str]) -> None:
        """
        Manually set the zone instead of auto-detecting.

        Args:
            zone: Zone ID (1-7) or zone name

        Raises:
            ValueError: If invalid zone specified
        """
        if isinstance(zone, int) and zone in self.ZONE_URLS:
            zone_url = self.ZONE_URLS[zone]
            self._zone_info = ZoneInfo(
                url=zone_url,
                dataBaseType="Production",  # Default for production environments
                ciLevel=1,  # Default CI level
            )
            logger.info(f"Manually set zone to: {zone_url} (Zone {zone})")
        else:
            raise ValueError(f"Invalid zone: {zone}. Must be 1-7.")

    def validate_credentials(self) -> bool:
        """
        Validate the provided credentials by attempting zone detection and API test.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            self._detect_zone()
            return self.test_connection()
        except (AutotaskAuthError, AutotaskZoneError, AutotaskConnectionError):
            return False

    def reset_zone_cache(self) -> None:
        """Reset cached zone information to force re-detection."""
        self._zone_info = None

    def close(self) -> None:
        """Close the authentication session and cleanup resources."""
        if self._session:
            self._session.close()
            self._session = None

    def test_connection(self) -> bool:
        """
        Test the connection to Autotask API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try a simple API call to test connection
            session = self.get_session()
            test_url = f"{self.api_url}/v1.0/Companies/query"

            # Send a minimal query to test connectivity
            response = session.post(test_url, json={"maxRecords": 1}, timeout=10)

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    @classmethod
    def clear_zone_cache(cls) -> None:
        """Clear the zone detection cache."""
        cls._zone_cache.clear()
        logger.info("Zone cache cleared")
