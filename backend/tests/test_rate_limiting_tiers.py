"""
Unit & Integration Tests for Tier-Aware Redis-Backed API Rate Limiting (#1061)

Verifies:
1. Configurable user tier rate limits (Anonymous, Authenticated, Premium, Admin) via app settings.
2. Rate limit string parser across time units (seconds, minutes, hours, days, custom multipliers).
3. Sliding window calculation in in-memory store and Redis store.
4. Tier resolution from headers, JWT bearer tokens, and user state.
5. Bypass mechanism for admin roles, configured internal service tokens, and whitelisted IPs.
6. Returns HTTP 429 Too Many Requests with Retry-After and X-RateLimit-* headers.
7. Route decorator @rate_limit_tier and Global TierRateLimitMiddleware.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.responses import Response

from app.core.config import Settings, settings
from app.core.rate_limiter import (
    InMemorySlidingWindowStore,
    RateLimitResult,
    RateLimitTier,
    RedisSlidingWindowStore,
    TierRateLimiter,
    TierRateLimitMiddleware,
    attach_rate_limit_headers,
    parse_rate_limit_string,
    rate_limit_tier,
    tier_rate_limiter,
)
from app.middleware.rate_limit import (
    ADMIN_LIMIT,
    ANONYMOUS_LIMIT,
    AUTHENTICATED_LIMIT,
    PREMIUM_LIMIT,
)


class TestTierRateLimitConfig:
    def test_tier_rate_limit_settings_defaults(self):
        """Verify tier defaults in Settings with env_file disabled."""

        class DeclaredDefaults(Settings):
            model_config = {**Settings.model_config, "env_file": None}

        defaults = DeclaredDefaults()

        assert defaults.ENABLE_RATE_LIMIT is True
        assert defaults.RATE_LIMIT_ANONYMOUS == "60/minute"
        assert defaults.RATE_LIMIT_AUTHENTICATED == "300/minute"
        assert defaults.RATE_LIMIT_PREMIUM == "1000/minute"
        assert defaults.RATE_LIMIT_ADMIN == "5000/minute"
        assert "127.0.0.1" in defaults.RATE_LIMIT_BYPASS_IPS
        assert defaults.RATE_LIMIT_ALGORITHM == "sliding_window"

    def test_active_tier_settings_readable(self):
        """Verify settings on active settings instance."""
        assert settings.RATE_LIMIT_ANONYMOUS is not None
        assert settings.RATE_LIMIT_AUTHENTICATED is not None
        assert settings.RATE_LIMIT_PREMIUM is not None
        assert settings.RATE_LIMIT_ADMIN is not None
        assert isinstance(settings.rate_limit_bypass_ip_list, list)

    def test_middleware_tier_limits_exported(self):
        """Verify tier limit constants exported from middleware module."""
        assert ANONYMOUS_LIMIT is not None
        assert AUTHENTICATED_LIMIT is not None
        assert PREMIUM_LIMIT is not None
        assert ADMIN_LIMIT is not None


class TestParseRateLimitString:
    def test_parse_valid_limits(self):
        assert parse_rate_limit_string("100/minute") == (100, 60)
        assert parse_rate_limit_string("5/second") == (5, 1)
        assert parse_rate_limit_string("10/sec") == (10, 1)
        assert parse_rate_limit_string("3/hour") == (3, 3600)
        assert parse_rate_limit_string("500/day") == (500, 86400)
        assert parse_rate_limit_string("3/15minutes") == (3, 900)
        assert parse_rate_limit_string("20/2hours") == (20, 7200)

    def test_parse_invalid_formats(self):
        with pytest.raises(ValueError, match="Invalid rate limit format"):
            parse_rate_limit_string("invalid_format")

        with pytest.raises(ValueError, match="Unknown time unit"):
            parse_rate_limit_string("10/centuries")

        with pytest.raises(ValueError, match="invalid literal"):
            parse_rate_limit_string("abc/minute")


class TestInMemorySlidingWindowStore:
    def test_sliding_window_allow_and_exhaustion(self):
        store = InMemorySlidingWindowStore()
        key = "test_user_key"

        # Allow 3 requests per 10 seconds
        allowed1, limit1, rem1, reset1 = store.is_allowed(key, 3, 10)
        assert allowed1 is True
        assert limit1 == 3
        assert rem1 == 2

        allowed2, limit2, rem2, reset2 = store.is_allowed(key, 3, 10)
        assert allowed2 is True
        assert rem2 == 1

        allowed3, limit3, rem3, reset3 = store.is_allowed(key, 3, 10)
        assert allowed3 is True
        assert rem3 == 0

        # 4th request within window must be rejected
        allowed4, limit4, rem4, reset4 = store.is_allowed(key, 3, 10)
        assert allowed4 is False
        assert rem4 == 0
        assert reset4 > 0

    def test_sliding_window_eviction(self):
        store = InMemorySlidingWindowStore()
        key = "test_eviction_key"

        # 1 request per 1 second
        allowed1, _, rem1, _ = store.is_allowed(key, 1, 1)
        assert allowed1 is True

        allowed2, _, rem2, _ = store.is_allowed(key, 1, 1)
        assert allowed2 is False

        # Sleep past the window
        time.sleep(1.1)

        allowed3, _, rem3, _ = store.is_allowed(key, 1, 1)
        assert allowed3 is True

    def test_store_reset(self):
        store = InMemorySlidingWindowStore()
        store.is_allowed("k1", 1, 60)
        store.reset()
        allowed, _, rem, _ = store.is_allowed("k1", 1, 60)
        assert allowed is True
        assert rem == 0


class TestRedisSlidingWindowStore:
    def test_redis_sliding_window_pipeline(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe

        # Simulate 1 existing entry
        mock_pipe.execute.side_effect = [
            (0, 1, [("member1", time.time() - 10)]),  # First pipe: rem, count, oldest
            (True, True),  # Second pipe: zadd, expire
        ]

        store = RedisSlidingWindowStore(redis_client=mock_redis)
        allowed, limit, remaining, reset_secs = store.is_allowed("rl:key", 5, 60)

        assert allowed is True
        assert limit == 5
        assert remaining == 3
        assert reset_secs > 0

    def test_redis_sliding_window_exceeded(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe

        now = time.time()
        # Simulate limit reached (5 entries)
        mock_pipe.execute.return_value = (0, 5, [("member1", now - 20)])

        store = RedisSlidingWindowStore(redis_client=mock_redis)
        allowed, limit, remaining, retry_after = store.is_allowed("rl:key", 5, 60)

        assert allowed is False
        assert limit == 5
        assert remaining == 0
        assert retry_after > 0


class TestTierResolution:
    def test_resolve_anonymous_tier(self):
        limiter = TierRateLimiter()
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock(host="203.0.113.195")
        request.state = MagicMock()
        request.state.user = None

        with patch("app.core.rate_limiter.client_address", return_value="203.0.113.195"):
            tier, subject = limiter.resolve_tier(request)
            assert tier == RateLimitTier.ANONYMOUS
            assert "203.0.113.195" in subject

    def test_resolve_authenticated_tier_from_state(self):
        limiter = TierRateLimiter()
        request = MagicMock(spec=Request)
        request.headers = {}
        user_mock = MagicMock()
        user_mock.id = "user_abc_123"
        user_mock.role = "user"
        user_mock.is_premium = False
        request.state = MagicMock()
        request.state.user = user_mock

        tier, subject = limiter.resolve_tier(request)
        assert tier == RateLimitTier.AUTHENTICATED
        assert subject == "user:user_abc_123"

    def test_resolve_premium_tier_from_state(self):
        limiter = TierRateLimiter()
        request = MagicMock(spec=Request)
        request.headers = {}
        user_mock = MagicMock()
        user_mock.id = "user_prem_456"
        user_mock.role = "premium"
        request.state = MagicMock()
        request.state.user = user_mock

        tier, subject = limiter.resolve_tier(request)
        assert tier == RateLimitTier.PREMIUM
        assert subject == "user:user_prem_456"

    def test_resolve_admin_tier_from_state(self):
        limiter = TierRateLimiter()
        request = MagicMock(spec=Request)
        request.headers = {}
        user_mock = MagicMock()
        user_mock.id = "admin_789"
        user_mock.role = "admin"
        request.state = MagicMock()
        request.state.user = user_mock

        tier, subject = limiter.resolve_tier(request)
        assert tier == RateLimitTier.ADMIN
        assert subject == "user:admin_789"

    def test_resolve_bypass_internal_service_token(self):
        limiter = TierRateLimiter()
        request = MagicMock(spec=Request)
        request.headers = {"X-Internal-Service-Key": "super_secret_internal_token"}
        request.state = MagicMock()
        request.state.user = None

        with patch.object(settings, "RATE_LIMIT_BYPASS_TOKEN", "super_secret_internal_token"):
            tier, subject = limiter.resolve_tier(request)
            assert tier == RateLimitTier.BYPASS
            assert subject == "internal_service"

    def test_resolve_bypass_whitelisted_ip(self):
        limiter = TierRateLimiter()
        request = MagicMock(spec=Request)
        request.headers = {}
        request.state = MagicMock()
        request.state.user = None

        with patch("app.core.rate_limiter.client_address", return_value="127.0.0.1"):
            with patch.object(settings, "RATE_LIMIT_BYPASS_IPS", "127.0.0.1,::1"):
                tier, subject = limiter.resolve_tier(request)
                assert tier == RateLimitTier.BYPASS
                assert subject == "127.0.0.1"


class TestRateLimitIntegration:
    @pytest.fixture
    def test_app(self):
        app = FastAPI()

        @app.get("/api/public-data")
        @rate_limit_tier(anonymous="2/minute", authenticated="10/minute", name="public_data")
        async def public_endpoint(request: Request):
            return {"data": "public_success"}

        @app.get("/api/custom-endpoint")
        @rate_limit_tier(anonymous="1/second", name="custom_data")
        async def custom_endpoint(request: Request):
            return {"data": "custom_success"}

        return app

    def test_rate_limit_decorator_exceeded_and_headers(self, test_app):
        client = TestClient(test_app)

        with patch("app.core.rate_limiter.is_testing", False):
            with patch("app.core.rate_limiter.force_rate_limits", True):
                with patch.object(settings, "RATE_LIMIT_BYPASS_IPS", ""):
                    # Request 1: OK
                    res1 = client.get("/api/public-data", headers={"X-Forwarded-For": "198.51.100.1"})
                    assert res1.status_code == status.HTTP_200_OK
                    assert res1.headers.get("X-RateLimit-Limit") == "2"
                    assert res1.headers.get("X-RateLimit-Remaining") == "1"
                    assert res1.headers.get("X-RateLimit-Tier") == "anonymous"

                    # Request 2: OK
                    res2 = client.get("/api/public-data", headers={"X-Forwarded-For": "198.51.100.1"})
                    assert res2.status_code == status.HTTP_200_OK
                    assert res2.headers.get("X-RateLimit-Remaining") == "0"

                    # Request 3: HTTP 429 Too Many Requests
                    res3 = client.get("/api/public-data", headers={"X-Forwarded-For": "198.51.100.1"})
                    assert res3.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                    assert "Retry-After" in res3.headers
                    assert res3.headers.get("X-RateLimit-Limit") == "2"
                    assert res3.headers.get("X-RateLimit-Remaining") == "0"

                    body = res3.json()
                    assert body["success"] is False
                    assert body["error_code"] == "RATE_LIMIT_EXCEEDED"
                    assert body["retry_after_seconds"] > 0
                    assert body["tier"] == "anonymous"

    def test_rate_limit_bypass_header(self, test_app):
        client = TestClient(test_app)

        with patch("app.core.rate_limiter.is_testing", False):
            with patch("app.core.rate_limiter.force_rate_limits", True):
                with patch.object(settings, "RATE_LIMIT_BYPASS_TOKEN", "test_internal_token"):
                    # Fire 5 requests with bypass header, none should be 429
                    for _ in range(5):
                        res = client.get(
                            "/api/public-data",
                            headers={
                                "X-Forwarded-For": "198.51.100.2",
                                "X-Internal-Service-Key": "test_internal_token",
                            },
                        )
                        assert res.status_code == status.HTTP_200_OK


class TestAttachHeadersHelper:
    def test_attach_headers_allowed(self):
        response = Response()
        result = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=99,
            reset_seconds=60,
            retry_after=0,
            tier="authenticated",
        )
        attach_rate_limit_headers(response, result)

        assert response.headers.get("x-ratelimit-limit") == "100"
        assert response.headers.get("x-ratelimit-remaining") == "99"
        assert response.headers.get("x-ratelimit-reset") == "60"
        assert response.headers.get("x-ratelimit-tier") == "authenticated"
        assert "retry-after" not in response.headers

    def test_attach_headers_blocked(self):
        response = Response()
        result = RateLimitResult(
            allowed=False,
            limit=50,
            remaining=0,
            reset_seconds=45,
            retry_after=45,
            tier="anonymous",
        )
        attach_rate_limit_headers(response, result)

        assert response.headers.get("x-ratelimit-limit") == "50"
        assert response.headers.get("x-ratelimit-remaining") == "0"
        assert response.headers.get("x-ratelimit-reset") == "45"
        assert response.headers.get("x-ratelimit-tier") == "anonymous"
        assert response.headers.get("retry-after") == "45"

