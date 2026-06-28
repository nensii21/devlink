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
# Common Limits
# ------------------------------------------------------------------

LOGIN_LIMIT = settings.LOGIN_RATE_LIMIT

REGISTER_LIMIT = settings.REGISTER_RATE_LIMIT

PASSWORD_RESET_LIMIT = "3/15minutes"

UPLOAD_LIMIT = "10/hour"

MESSAGE_LIMIT = "60/minute"

SEARCH_LIMIT = "120/minute"

PROJECT_LIMIT = "20/hour"

FLARE_LIMIT = "10/hour"
