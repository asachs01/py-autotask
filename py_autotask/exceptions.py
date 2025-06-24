"""
Exception classes for py-autotask.

This module provides a hierarchy of exceptions for different types of errors
that can occur when interacting with the Autotask API.
"""

from typing import Any, Dict, Optional


class AutotaskError(Exception):
    """Base exception class for all py-autotask errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AutotaskAPIError(AutotaskError):
    """
    Exception raised for HTTP errors from the Autotask API.

    This exception wraps HTTP error responses and provides structured
    access to error details returned by the Autotask API.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"HTTP {self.status_code}: {self.message}"
        return self.message

    @property
    def errors(self) -> list:
        """Extract error list from Autotask API response."""
        if isinstance(self.response_data, dict):
            return self.response_data.get("errors", [])
        return []


class AutotaskAuthError(AutotaskError):
    """Exception raised for authentication-related errors."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class AutotaskConnectionError(AutotaskError):
    """Exception raised for connection-related errors."""

    def __init__(self, message: str = "Connection error") -> None:
        super().__init__(message)


class AutotaskValidationError(AutotaskError):
    """Exception raised for data validation errors."""

    def __init__(
        self, message: str, field: Optional[str] = None, value: Optional[Any] = None
    ) -> None:
        super().__init__(message)
        self.field = field
        self.value = value

    def __str__(self) -> str:
        if self.field:
            return f"Validation error for field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


class AutotaskRateLimitError(AutotaskAPIError):
    """Exception raised when API rate limits are exceeded."""

    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class AutotaskTimeoutError(AutotaskError):
    """Exception raised when API requests timeout."""

    def __init__(self, message: str = "Request timeout") -> None:
        super().__init__(message)


class AutotaskZoneError(AutotaskError):
    """Exception raised for zone detection or access errors."""

    def __init__(self, message: str = "Zone detection failed") -> None:
        super().__init__(message)


class AutotaskNotFoundError(AutotaskAPIError):
    """Exception raised when a requested resource is not found (HTTP 404)."""

    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(message, status_code=404, **kwargs)


class AutotaskConfigurationError(AutotaskError):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
