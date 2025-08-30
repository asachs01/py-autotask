"""
Tests for authentication and zone detection functionality.

This module tests the AutotaskAuth class and related authentication
mechanisms including zone detection and credential validation.
"""

import pytest
import responses

from py_autotask.auth import AutotaskAuth
from py_autotask.exceptions import (
    AutotaskAuthError,
    AutotaskConnectionError,
    AutotaskZoneError,
)
from py_autotask.types import AuthCredentials


class TestAutotaskAuth:
    """Test cases for AutotaskAuth class."""

    def test_init(self, sample_credentials):
        """Test authentication initialization."""
        auth = AutotaskAuth(sample_credentials)
        assert auth.credentials == sample_credentials
        assert auth.zone_info is None
        assert auth._session is None

    def test_api_url_with_override(self):
        """Test API URL when override is provided."""
        credentials = AuthCredentials(
            username="test@example.com",
            integration_code="TEST123",
            secret="test_secret",
            api_url="https://custom.api.url",
        )
        auth = AutotaskAuth(credentials)
        assert auth.api_url == "https://custom.api.url"

    @responses.activate
    def test_zone_detection_success(self, sample_credentials):
        """Test successful zone detection."""
        # Mock zone detection response with user parameter
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )
        responses.add(
            responses.GET,
            zone_url_with_user,
            json={
                "url": "https://webservices123.autotask.net/atservicesrest",
                "dataBaseType": "Production",
                "ciLevel": 1,
            },
            status=200,
        )

        auth = AutotaskAuth(sample_credentials)
        api_url = auth.api_url

        assert api_url == "https://webservices123.autotask.net/atservicesrest"
        assert auth.zone_info is not None
        assert auth.zone_info.url == api_url

    @responses.activate
    def test_zone_detection_auth_error(self, sample_credentials):
        """Test zone detection with authentication error."""
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )
        responses.add(responses.GET, zone_url_with_user, status=401)

        auth = AutotaskAuth(sample_credentials)

        with pytest.raises(AutotaskAuthError, match="Authentication failed"):
            _ = auth.api_url

    @responses.activate
    def test_zone_detection_invalid_integration_code(self, sample_credentials):
        """Test zone detection with invalid integration code."""
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )
        responses.add(
            responses.GET,
            zone_url_with_user,
            json={"errors": ["IntegrationCode is invalid"]},
            status=500,
        )

        auth = AutotaskAuth(sample_credentials)

        with pytest.raises(AutotaskAuthError, match="Invalid integration code"):
            _ = auth.api_url

    @responses.activate
    def test_zone_detection_invalid_username(self, sample_credentials):
        """Test zone detection with invalid username."""
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )
        responses.add(
            responses.GET,
            zone_url_with_user,
            json={"errors": ["Zone information could not be determined"]},
            status=500,
        )

        auth = AutotaskAuth(sample_credentials)

        with pytest.raises(AutotaskAuthError, match="Invalid API username"):
            _ = auth.api_url

    @responses.activate
    def test_zone_detection_network_error(self, sample_credentials):
        """Test zone detection with network error."""
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )
        responses.add(
            responses.GET, zone_url_with_user, body=responses.ConnectionError()
        )

        auth = AutotaskAuth(sample_credentials)

        with pytest.raises(AutotaskConnectionError, match="Connection error"):
            _ = auth.api_url

    @responses.activate
    def test_zone_detection_invalid_response(self, sample_credentials):
        """Test zone detection with invalid response format."""
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )
        responses.add(
            responses.GET,
            zone_url_with_user,
            json={"invalid": "response"},
            status=200,
        )

        auth = AutotaskAuth(sample_credentials)

        with pytest.raises(AutotaskZoneError, match="Invalid zone information"):
            _ = auth.api_url

    def test_get_session(self, sample_credentials):
        """Test session creation."""
        auth = AutotaskAuth(sample_credentials)
        session = auth.get_session()

        assert session is not None
        # Autotask uses headers for auth, not Basic Auth
        assert session.auth is None
        assert (
            session.headers["ApiIntegrationCode"] == sample_credentials.integration_code
        )
        assert session.headers["UserName"] == sample_credentials.username
        assert session.headers["Secret"] == sample_credentials.secret
        assert "py-autotask" in session.headers["User-Agent"]

    def test_get_session_cached(self, sample_credentials):
        """Test that session is cached."""
        auth = AutotaskAuth(sample_credentials)
        session1 = auth.get_session()
        session2 = auth.get_session()

        assert session1 is session2

    @responses.activate
    def test_validate_credentials_success(self, sample_credentials):
        """Test credential validation success."""
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )
        responses.add(
            responses.GET,
            zone_url_with_user,
            json={
                "url": "https://webservices123.autotask.net/atservicesrest",
                "dataBaseType": "Production",
                "ciLevel": 1,
            },
            status=200,
        )

        # Mock the test connection endpoint
        responses.add(
            responses.POST,
            "https://webservices123.autotask.net/atservicesrest/v1.0/Companies/query",
            json={"items": [], "pageDetails": {"count": 0}},
            status=200,
        )

        auth = AutotaskAuth(sample_credentials)
        assert auth.validate_credentials() is True

    @responses.activate
    def test_validate_credentials_failure(self, sample_credentials):
        """Test credential validation failure."""
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )
        responses.add(responses.GET, zone_url_with_user, status=401)

        auth = AutotaskAuth(sample_credentials)
        assert auth.validate_credentials() is False

    @responses.activate
    def test_reset_zone_cache(self, sample_credentials):
        """Test zone cache reset."""
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )
        responses.add(
            responses.GET,
            zone_url_with_user,
            json={
                "url": "https://webservices123.autotask.net/atservicesrest",
                "dataBaseType": "Production",
                "ciLevel": 1,
            },
            status=200,
        )

        auth = AutotaskAuth(sample_credentials)

        # Trigger zone detection
        _ = auth.api_url
        assert auth.zone_info is not None

        # Reset cache
        auth.reset_zone_cache()
        assert auth.zone_info is None

    def test_close(self, sample_credentials):
        """Test session cleanup."""
        auth = AutotaskAuth(sample_credentials)
        auth.get_session()

        auth.close()
        assert auth._session is None

    @responses.activate
    def test_zone_detection_404_with_http_fallback(self, sample_credentials):
        """Test zone detection handles 404 and tries HTTP fallback."""
        # Build URLs with user parameter
        zone_url_with_user = (
            f"{AutotaskAuth.ZONE_INFO_URL}?user={sample_credentials.username}"
        )

        # HTTPS returns 404
        responses.add(responses.GET, zone_url_with_user, status=404)

        # HTTP fallback succeeds
        http_url = zone_url_with_user.replace("https://", "http://")
        responses.add(
            responses.GET,
            http_url,
            json={
                "url": "https://webservices123.autotask.net/atservicesrest",
                "dataBaseType": "Production",
                "ciLevel": "1",
            },
            status=200,
        )

        auth = AutotaskAuth(sample_credentials)

        # This should succeed with HTTP fallback
        api_url = auth.api_url
        assert auth._zone_info is not None
        assert api_url == "https://webservices123.autotask.net/atservicesrest"
