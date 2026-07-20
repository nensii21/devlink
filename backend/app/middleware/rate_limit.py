from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# ------------------------------------------------------------------
# Global Rate Limiter
# ------------------------------------------------------------------

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        settings.DEFAULT_RATE_LIMIT,
    ],
)

# ------------------------------------------------------------------
# Common Limits (all configurable via settings)
# ------------------------------------------------------------------

LOGIN_LIMIT = settings.LOGIN_RATE_LIMIT

REGISTER_LIMIT = settings.REGISTER_RATE_LIMIT

MESSAGE_LIMIT = settings.MESSAGE_RATE_LIMIT

SEARCH_LIMIT = settings.SEARCH_RATE_LIMIT

PROJECT_LIMIT = settings.PROJECT_RATE_LIMIT

PASSWORD_RESET_LIMIT = settings.PASSWORD_RESET_RATE_LIMIT

# Recommendations are expensive (multiple joins + scoring).
# Keep a tighter limit than the default search limit.
RECOMMENDATION_LIMIT = settings.RECOMMENDATION_RATE_LIMIT
