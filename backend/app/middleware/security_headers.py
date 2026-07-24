from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:

        response = await call_next(request)

        if settings.ENABLE_X_CONTENT_TYPE_OPTIONS:
            response.headers["X-Content-Type-Options"] = "nosniff"

        if settings.ENABLE_X_FRAME_OPTIONS:
            response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        if settings.ENABLE_CROSS_DOMAIN_POLICIES:
            response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        if settings.ENABLE_DNS_PREFETCH_CONTROL:
            response.headers["X-DNS-Prefetch-Control"] = "off"

        if settings.ENABLE_HSTS:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        if settings.ENABLE_CSP:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https: data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )

        return response
