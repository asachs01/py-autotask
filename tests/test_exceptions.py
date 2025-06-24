"""
Tests for exception classes and error handling.

This module tests all custom exception classes and ensures
proper error handling throughout the library.
"""

from py_autotask.exceptions import (
    AutotaskAPIError,
    AutotaskAuthError,
    AutotaskConfigurationError,
    AutotaskConnectionError,
    AutotaskError,
    AutotaskRateLimitError,
    AutotaskTimeoutError,
    AutotaskValidationError,
    AutotaskZoneError,
)


class TestAutotaskError:
    """Test base AutotaskError exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = AutotaskError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    def test_error_with_details(self):
        """Test error with additional details."""
        details = {"field": "test", "code": 123}
        error = AutotaskError("Test error", details)
        assert error.details == details


class TestAutotaskAPIError:
    """Test AutotaskAPIError exception."""

    def test_basic_api_error(self):
        """Test basic API error."""
        error = AutotaskAPIError("API error")
        assert str(error) == "API error"
        assert error.status_code is None
        assert error.response_data == {}

    def test_api_error_with_status_code(self):
        """Test API error with status code."""
        error = AutotaskAPIError("API error", status_code=400)
        assert str(error) == "HTTP 400: API error"
        assert error.status_code == 400

    def test_api_error_with_response_data(self):
        """Test API error with response data."""
        response_data = {"errors": ["Field is required", "Invalid value"]}
        error = AutotaskAPIError("API error", response_data=response_data)
        assert error.response_data == response_data
        assert error.errors == ["Field is required", "Invalid value"]

    def test_api_error_no_errors_in_response(self):
        """Test API error when response has no errors field."""
        response_data = {"message": "Something went wrong"}
        error = AutotaskAPIError("API error", response_data=response_data)
        assert error.errors == []


class TestAutotaskAuthError:
    """Test AutotaskAuthError exception."""

    def test_default_auth_error(self):
        """Test default authentication error."""
        error = AutotaskAuthError()
        assert str(error) == "Authentication failed"

    def test_custom_auth_error(self):
        """Test custom authentication error message."""
        error = AutotaskAuthError("Invalid credentials")
        assert str(error) == "Invalid credentials"


class TestAutotaskConnectionError:
    """Test AutotaskConnectionError exception."""

    def test_default_connection_error(self):
        """Test default connection error."""
        error = AutotaskConnectionError()
        assert str(error) == "Connection error"

    def test_custom_connection_error(self):
        """Test custom connection error message."""
        error = AutotaskConnectionError("Network timeout")
        assert str(error) == "Network timeout"


class TestAutotaskValidationError:
    """Test AutotaskValidationError exception."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        error = AutotaskValidationError("Validation failed")
        assert str(error) == "Validation error: Validation failed"
        assert error.field is None
        assert error.value is None

    def test_validation_error_with_field(self):
        """Test validation error with field information."""
        error = AutotaskValidationError("Invalid value", field="email", value="invalid")
        assert str(error) == "Validation error for field 'email': Invalid value"
        assert error.field == "email"
        assert error.value == "invalid"


class TestAutotaskRateLimitError:
    """Test AutotaskRateLimitError exception."""

    def test_default_rate_limit_error(self):
        """Test default rate limit error."""
        error = AutotaskRateLimitError()
        assert str(error) == "API rate limit exceeded"
        assert error.retry_after is None

    def test_rate_limit_error_with_retry_after(self):
        """Test rate limit error with retry after value."""
        error = AutotaskRateLimitError(
            "Rate limit exceeded", status_code=429, retry_after=60
        )
        assert str(error) == "HTTP 429: Rate limit exceeded"
        assert error.retry_after == 60


class TestAutotaskTimeoutError:
    """Test AutotaskTimeoutError exception."""

    def test_default_timeout_error(self):
        """Test default timeout error."""
        error = AutotaskTimeoutError()
        assert str(error) == "Request timeout"

    def test_custom_timeout_error(self):
        """Test custom timeout error message."""
        error = AutotaskTimeoutError("Operation timed out after 30s")
        assert str(error) == "Operation timed out after 30s"


class TestAutotaskZoneError:
    """Test AutotaskZoneError exception."""

    def test_default_zone_error(self):
        """Test default zone error."""
        error = AutotaskZoneError()
        assert str(error) == "Zone detection failed"

    def test_custom_zone_error(self):
        """Test custom zone error message."""
        error = AutotaskZoneError("Cannot determine API zone")
        assert str(error) == "Cannot determine API zone"


class TestAutotaskConfigurationError:
    """Test AutotaskConfigurationError exception."""

    def test_configuration_error(self):
        """Test configuration error."""
        error = AutotaskConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all exceptions inherit from AutotaskError."""
        exceptions = [
            AutotaskAPIError("test"),
            AutotaskAuthError("test"),
            AutotaskConnectionError("test"),
            AutotaskValidationError("test"),
            AutotaskRateLimitError("test"),
            AutotaskTimeoutError("test"),
            AutotaskZoneError("test"),
            AutotaskConfigurationError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, AutotaskError)
            assert isinstance(exc, Exception)

    def test_rate_limit_inherits_from_api_error(self):
        """Test that RateLimitError inherits from APIError."""
        error = AutotaskRateLimitError("test")
        assert isinstance(error, AutotaskAPIError)
        assert isinstance(error, AutotaskError)
