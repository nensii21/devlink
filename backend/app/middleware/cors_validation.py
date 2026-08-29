from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_403_FORBIDDEN

from app.core.config import settings


class CORSValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate the Origin header for CORS requests.

    This middleware ensures that:
    1. Requests must have an Origin header
    2. The Origin must be in the allowed origins list

    This prevents requests without an Origin header from being processed,
    which could expose the API to local network access in development.
    """

    def __init__(self, app, allowed_origins: list[str] | None = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or settings.cors_origins

    async def dispatch(self, request: Request, call_next) -> Response:
        origin = request.headers.get("origin")

        if not origin:
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"detail": "Missing Origin header"},
            )

        if origin not in self.allowed_origins:
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"detail": f"Origin '{origin}' not allowed"},
            )

        return await call_next(request)