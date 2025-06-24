"""
Authentication and zone detection for Autotask API.

This module handles the authentication flow and automatic zone detection
required for Autotask API access.
"""

import logging
from typing import Optional

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
    automatically.
    """

    ZONE_INFO_URL = (
        "https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation"
    )

    def __init__(self, credentials: AuthCredentials) -> None:
        """
        Initialize authentication with credentials.

        Args:
            credentials: Authentication credentials
        """
        self.credentials = credentials
        self._zone_info: Optional[ZoneInfo] = None
        self._session: Optional[requests.Session] = None

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
        Get authenticated session for API requests.

        Returns:
            Configured requests session with authentication
        """
        if not self._session:
            self._session = requests.Session()
            self._session.auth = HTTPBasicAuth(
                self.credentials.username, self.credentials.secret
            )
            self._session.headers.update(
                {
                    "Content-Type": "application/json",
                    "ApiIntegrationcode": self.credentials.integration_code,
                    "User-Agent": "py-autotask/0.1.0",
                }
            )

        return self._session

    def _detect_zone(self) -> None:
        """
        Detect the correct API zone for the authenticated user.

        This method calls the zone information endpoint to determine
        the correct regional API endpoint to use.

        Raises:
            AutotaskZoneError: If zone detection fails
            AutotaskAuthError: If authentication fails
            AutotaskConnectionError: If connection fails
        """
        try:
            logger.info("Detecting Autotask API zone...")

            # Create a temporary session for zone detection
            session = requests.Session()
            session.auth = HTTPBasicAuth(
                self.credentials.username, self.credentials.secret
            )
            session.headers.update(
                {
                    "Content-Type": "application/json",
                    "ApiIntegrationcode": self.credentials.integration_code,
                    "User-Agent": "py-autotask/0.1.0",
                }
            )

            response = session.get(self.ZONE_INFO_URL, timeout=30)

            if response.status_code == 401:
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
                    raise AutotaskAuthError(
                        "Invalid API username. Please check your credentials."
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
                raise AutotaskAPIError(
                    f"Zone detection failed with status {response.status_code}: "
                    f"{response.text}"
                )

            # Parse zone information
            try:
                zone_data = response.json()
                if not isinstance(zone_data, dict) or "url" not in zone_data:
                    raise AutotaskZoneError(
                        f"Invalid zone information response: {zone_data}"
                    )

                self._zone_info = ZoneInfo(**zone_data)
                logger.info(f"Detected API zone: {self._zone_info.url}")

            except (ValueError, TypeError) as e:
                raise AutotaskZoneError(f"Failed to parse zone information: {e}")

        except requests.exceptions.Timeout:
            raise AutotaskConnectionError(
                "Timeout during zone detection. Please check your connection."
            )
        except requests.exceptions.ConnectionError:
            raise AutotaskConnectionError(
                "Connection error during zone detection. Please check your connection."
            )
        except requests.exceptions.RequestException as e:
            raise AutotaskConnectionError(f"Network error during zone detection: {e}")

    def validate_credentials(self) -> bool:
        """
        Validate the provided credentials by attempting zone detection.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            self._detect_zone()
            return True
        except (AutotaskAuthError, AutotaskZoneError):
            return False

    def reset_zone_cache(self) -> None:
        """Reset cached zone information to force re-detection."""
        self._zone_info = None

    def close(self) -> None:
        """Close the authentication session."""
        if self._session:
            self._session.close()
            self._session = None
