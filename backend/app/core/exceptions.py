from __future__ import annotations

from typing import Any


class AppException(Exception):
    """
    Base exception for all application exceptions.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str | None = None,
        details: Any = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class AuthException(AppException):
    """
    Exception raised for authentication or authorization failures (401/403).
    """

    def __init__(
        self,
        message: str = "Authentication failed.",
        status_code: int = 401,
        code: str | None = "UNAUTHORIZED",
        details: Any = None,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            code=code,
            details=details,
        )


class DatabaseException(AppException):
    """
    Exception raised for database-related errors (500).
    """

    def __init__(
        self,
        message: str = "A database error occurred.",
        status_code: int = 500,
        code: str | None = "DATABASE_ERROR",
        details: Any = None,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            code=code,
            details=details,
        )


class ValidationException(AppException):
    """
    Exception raised for business validation failures (422).
    """

    def __init__(
        self,
        message: str = "Validation failed.",
        status_code: int = 422,
        code: str | None = "VALIDATION_ERROR",
        details: Any = None,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            code=code,
            details=details,
        )
