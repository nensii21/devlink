# ------------------------------------------------------------------
# Global Rate Limiter
# ------------------------------------------------------------------
import sys

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

is_testing = "pytest" in sys.modules

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        settings.DEFAULT_RATE_LIMIT,
    ],
    enabled=False,
)

# ------------------------------------------------------------------
# Common Limits (all configurable via settings)
# ------------------------------------------------------------------

LOGIN_LIMIT = "1000000/minute" if is_testing else settings.LOGIN_RATE_LIMIT

REGISTER_LIMIT = "1000000/minute" if is_testing else settings.REGISTER_RATE_LIMIT

MESSAGE_LIMIT = "1000000/minute" if is_testing else settings.MESSAGE_RATE_LIMIT

SEARCH_LIMIT = "1000000/minute" if is_testing else settings.SEARCH_RATE_LIMIT

PROJECT_LIMIT = "1000000/minute" if is_testing else settings.PROJECT_RATE_LIMIT

PASSWORD_RESET_LIMIT = (
    "1000000/minute" if is_testing else settings.PASSWORD_RESET_RATE_LIMIT
)
PASSWORD_RESET_LIMIT = settings.PASSWORD_RESET_RATE_LIMIT

# Recommendations are expensive (multiple joins + scoring).
# Keep a tighter limit than the default search limit.
RECOMMENDATION_LIMIT = settings.RECOMMENDATION_RATE_LIMIT
