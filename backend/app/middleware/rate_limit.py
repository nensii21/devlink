# ------------------------------------------------------------------
# Global Rate Limiter (#590)
# ------------------------------------------------------------------
import os
import sys

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

is_testing = "pytest" in sys.modules
force_rate_limits = os.getenv("TEST_RATE_LIMITS", "false").lower() in ("true", "1")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        settings.DEFAULT_RATE_LIMIT,
    ],
    enabled=settings.ENABLE_RATE_LIMIT,
    headers_enabled=True,
)

# ------------------------------------------------------------------
# Configurable Auth & API Limits
# ------------------------------------------------------------------

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
