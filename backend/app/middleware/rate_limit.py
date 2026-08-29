# ------------------------------------------------------------------
# Global Rate Limiter (#590)
# ------------------------------------------------------------------
#
# Two things decide whether a rate limit means anything: what it counts
# against, and where it keeps the count.
#
# **What it counts against.** This used `slowapi.util.get_remote_address`,
# which returns the peer socket address. Behind a reverse proxy -- which is
# every deployment described in this repo, both the `k8s/` manifests and the
# compose stack -- the peer is the ingress, so every request in the world
# hashed to one key. `REGISTER_RATE_LIMIT = "3/hour"` became three
# registrations per hour *across the entire site*, which one client can
# exhaust on its own. See `app/core/client_address.py` for how the real
# client is established without trusting a header any client can forge.
#
# **Where it keeps the count.** SlowAPI defaults to an in-memory store, which
# is per worker process. With N workers or replicas the effective limit is N
# times what is configured, unpredictably, and every counter resets on deploy.
# `RATE_LIMIT_STORAGE_URI` points it at Redis instead.

import logging
import os
import sys

from slowapi import Limiter

from app.core.client_address import rate_limit_key
from app.core.config import settings

logger = logging.getLogger(__name__)

is_testing = "pytest" in sys.modules
force_rate_limits = os.getenv("TEST_RATE_LIMITS", "false").lower() in ("true", "1")


def _storage_uri() -> str:
    """
    Where counters live.

    Falls back to in-memory when nothing is configured, and logs loudly when
    that happens outside of tests -- a limiter that silently counts per
    process looks like it is working right up until it matters.
    """
    uri = settings.RATE_LIMIT_STORAGE_URI.strip()

    if not uri:
        if not is_testing:
            logger.warning(
                "RATE_LIMIT_STORAGE_URI is not set; rate limit counters are "
                "per-process and reset on restart. Set it to a Redis URL for "
                "any deployment running more than one worker."
            )
        return "memory://"

    return uri


def _build_limiter() -> Limiter:
    """
    Build the limiter, degrading to in-memory if the configured store is
    unreachable.

    A misconfigured or briefly-down Redis should not stop the application
    booting. The degraded state is logged at error level because the limits it
    leaves behind are weaker than the ones that were asked for.
    """
    uri = _storage_uri()

    try:
        return Limiter(
            key_func=rate_limit_key,
            default_limits=[settings.DEFAULT_RATE_LIMIT],
            enabled=settings.ENABLE_RATE_LIMIT,
            headers_enabled=True,
            storage_uri=uri,
        )
    except Exception as exc:  # pragma: no cover - depends on the environment
        if uri == "memory://":
            raise

        logger.error(
            "Rate limit storage %r is unreachable (%s); falling back to "
            "in-memory counters. Limits are now per-process.",
            uri,
            exc,
        )
        return Limiter(
            key_func=rate_limit_key,
            default_limits=[settings.DEFAULT_RATE_LIMIT],
            enabled=settings.ENABLE_RATE_LIMIT,
            headers_enabled=True,
            storage_uri="memory://",
        )


limiter = _build_limiter()

# ------------------------------------------------------------------
# Configurable Auth & API Limits
# ------------------------------------------------------------------
#
# Tests run with the limits effectively disabled unless TEST_RATE_LIMITS is
# set, so a suite that logs in twenty times does not trip LOGIN_RATE_LIMIT.

_DISABLED = "1000000/minute"


def _limit(configured: str) -> str:
    """The configured limit, or an unreachable one while testing."""
    if is_testing and not force_rate_limits:
        return _DISABLED
    return configured


AUTH_LIMIT = _limit(settings.AUTH_RATE_LIMIT)
LOGIN_LIMIT = _limit(settings.LOGIN_RATE_LIMIT)
REGISTER_LIMIT = _limit(settings.REGISTER_RATE_LIMIT)
PASSWORD_RESET_LIMIT = _limit(settings.PASSWORD_RESET_RATE_LIMIT)
VERIFY_EMAIL_LIMIT = _limit(settings.VERIFY_EMAIL_RATE_LIMIT)
MFA_LIMIT = _limit(settings.MFA_RATE_LIMIT)

MESSAGE_LIMIT = _limit(settings.MESSAGE_RATE_LIMIT)
SEARCH_LIMIT = _limit(settings.SEARCH_RATE_LIMIT)
PROJECT_LIMIT = _limit(settings.PROJECT_RATE_LIMIT)
UPLOAD_LIMIT = _limit(settings.UPLOAD_RATE_LIMIT)
COMMENT_LIMIT = _limit(settings.COMMENT_RATE_LIMIT)
RECOMMENDATION_LIMIT = _limit(settings.RECOMMENDATION_RATE_LIMIT)
AUTH_LIMIT = (
    settings.AUTH_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
LOGIN_LIMIT = (
    settings.LOGIN_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
REGISTER_LIMIT = (
    settings.REGISTER_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
PASSWORD_RESET_LIMIT = (
    settings.PASSWORD_RESET_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
VERIFY_EMAIL_LIMIT = (
    settings.VERIFY_EMAIL_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
MFA_LIMIT = (
    settings.MFA_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)

MESSAGE_LIMIT = (
    settings.MESSAGE_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
SEARCH_LIMIT = (
    settings.SEARCH_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
PROJECT_LIMIT = (
    settings.PROJECT_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
UPLOAD_LIMIT = (
    settings.UPLOAD_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
COMMENT_LIMIT = (
    settings.COMMENT_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
RECOMMENDATION_LIMIT = (
    settings.RECOMMENDATION_RATE_LIMIT
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)

# User Tier Rate Limits (#1061)
ANONYMOUS_LIMIT = (
    settings.RATE_LIMIT_ANONYMOUS
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
AUTHENTICATED_LIMIT = (
    settings.RATE_LIMIT_AUTHENTICATED
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
PREMIUM_LIMIT = (
    settings.RATE_LIMIT_PREMIUM
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)
ADMIN_LIMIT = (
    settings.RATE_LIMIT_ADMIN
    if (not is_testing or force_rate_limits)
    else "1000000/minute"
)

from app.core.rate_limiter import (
    RateLimitResult,
    RateLimitTier,
    TierRateLimitMiddleware,
    TierRateLimiter,
    parse_rate_limit_string,
    rate_limit_tier,
    tier_rate_limiter,
)

