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
        # Mock zone detection response
        responses.add(
            responses.GET,
            AutotaskAuth.ZONE_INFO_URL,
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
        responses.add(responses.GET, AutotaskAuth.ZONE_INFO_URL, status=401)

        auth = AutotaskAuth(sample_credentials)

        with pytest.raises(AutotaskAuthError, match="Authentication failed"):
            _ = auth.api_url

    @responses.activate
    def test_zone_detection_invalid_integration_code(self, sample_credentials):
        """Test zone detection with invalid integration code."""
        responses.add(
            responses.GET,
            AutotaskAuth.ZONE_INFO_URL,
            json={"errors": ["IntegrationCode is invalid"]},
            status=500,
        )

        auth = AutotaskAuth(sample_credentials)

        with pytest.raises(AutotaskAuthError, match="Invalid integration code"):
            _ = auth.api_url

    @responses.activate
    def test_zone_detection_invalid_username(self, sample_credentials):
        """Test zone detection with invalid username."""
        responses.add(
            responses.GET,
            AutotaskAuth.ZONE_INFO_URL,
            json={"errors": ["Zone information could not be determined"]},
            status=500,
        )

        auth = AutotaskAuth(sample_credentials)

        with pytest.raises(AutotaskAuthError, match="Invalid API username"):
            _ = auth.api_url

    @responses.activate
    def test_zone_detection_network_error(self, sample_credentials):
        """Test zone detection with network error."""
        responses.add(
            responses.GET, AutotaskAuth.ZONE_INFO_URL, body=responses.ConnectionError()
        )

        auth = AutotaskAuth(sample_credentials)

        with pytest.raises(AutotaskConnectionError, match="Connection error"):
            _ = auth.api_url

    @responses.activate
    def test_zone_detection_invalid_response(self, sample_credentials):
        """Test zone detection with invalid response format."""
        responses.add(
            responses.GET,
            AutotaskAuth.ZONE_INFO_URL,
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
        assert session.auth is not None
        assert (
            session.headers["ApiIntegrationcode"] == sample_credentials.integration_code
        )
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
        responses.add(
            responses.GET,
            AutotaskAuth.ZONE_INFO_URL,
            json={
                "url": "https://webservices123.autotask.net/atservicesrest",
                "dataBaseType": "Production",
                "ciLevel": 1,
            },
            status=200,
        )

        auth = AutotaskAuth(sample_credentials)
        assert auth.validate_credentials() is True

    @responses.activate
    def test_validate_credentials_failure(self, sample_credentials):
        """Test credential validation failure."""
        responses.add(responses.GET, AutotaskAuth.ZONE_INFO_URL, status=401)

        auth = AutotaskAuth(sample_credentials)
        assert auth.validate_credentials() is False

    @responses.activate
    def test_reset_zone_cache(self, sample_credentials):
        """Test zone cache reset."""
        responses.add(
            responses.GET,
            AutotaskAuth.ZONE_INFO_URL,
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
