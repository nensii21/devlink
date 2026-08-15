"""
Unit & Integration Tests for Rate Limiting on Authentication Endpoints (#590)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import Request, status
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.error_handlers import rate_limit_exception_handler
from app.middleware.rate_limit import (
    AUTH_LIMIT,
    LOGIN_LIMIT,
    REGISTER_LIMIT,
    PASSWORD_RESET_LIMIT,
    VERIFY_EMAIL_LIMIT,
    MFA_LIMIT,
)


class TestAuthRateLimitingConfig:
    def test_configurable_rate_limit_settings(self):
        """Verify all auth rate limits are present and configurable via app settings."""
        assert settings.ENABLE_RATE_LIMIT is True
        assert settings.AUTH_RATE_LIMIT == "5/minute"
        assert settings.LOGIN_RATE_LIMIT == "5/minute"
        assert settings.REGISTER_RATE_LIMIT == "3/hour"
        assert settings.PASSWORD_RESET_RATE_LIMIT == "3/15minutes"
        assert settings.VERIFY_EMAIL_RATE_LIMIT == "5/minute"
        assert settings.MFA_RATE_LIMIT == "5/minute"

    def test_middleware_limits_export(self):
        """Verify middleware exports limits correctly."""
        assert AUTH_LIMIT is not None
        assert LOGIN_LIMIT is not None
        assert REGISTER_LIMIT is not None
        assert PASSWORD_RESET_LIMIT is not None
        assert VERIFY_EMAIL_LIMIT is not None
        assert MFA_LIMIT is not None


@pytest.mark.asyncio
class TestRateLimitExceptionHandler:
    async def test_handler_returns_429_and_retry_after_header(self):
        """Verify rate_limit_exception_handler returns HTTP 429 and Retry-After header."""
        request = MagicMock(spec=Request)
        mock_limit = MagicMock()
        mock_limit.error_message = None

        exc = RateLimitExceeded(mock_limit)
        exc.retry_after = 45

        response = await rate_limit_exception_handler(request, exc)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.headers.get("Retry-After") == "45"

        payload = response.body.decode("utf-8")
        assert "RATE_LIMIT_EXCEEDED" in payload
        assert "Too many requests" in payload
        assert "retry_after_seconds" in payload

    async def test_handler_defaults_retry_after(self):
        """Verify default retry_after seconds when not specified on exception."""
        request = MagicMock(spec=Request)
        mock_limit = MagicMock()
        mock_limit.error_message = None

        exc = RateLimitExceeded(mock_limit)

        response = await rate_limit_exception_handler(request, exc)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.headers.get("Retry-After") == "60"
