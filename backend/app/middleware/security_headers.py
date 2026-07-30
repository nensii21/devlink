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
            response.headers["X-Frame-Options"] = getattr(
                settings, "X_FRAME_OPTIONS_VALUE", "DENY"
            )

        if getattr(settings, "ENABLE_REFERRER_POLICY", True):
            response.headers["Referrer-Policy"] = getattr(
                settings, "REFERRER_POLICY_VALUE", "strict-origin-when-cross-origin"
            )

        if getattr(settings, "ENABLE_PERMISSIONS_POLICY", True):
            response.headers["Permissions-Policy"] = getattr(
                settings,
                "PERMISSIONS_POLICY_VALUE",
                "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
            )

        if getattr(settings, "ENABLE_COOP", True):
            response.headers["Cross-Origin-Opener-Policy"] = getattr(
                settings, "CROSS_ORIGIN_OPENER_POLICY", "same-origin"
            )

        if getattr(settings, "ENABLE_CORP", True):
            response.headers["Cross-Origin-Resource-Policy"] = getattr(
                settings, "CROSS_ORIGIN_RESOURCE_POLICY", "same-origin"
            )

        if getattr(settings, "ENABLE_COEP", True):
            response.headers["Cross-Origin-Embedder-Policy"] = getattr(
                settings, "CROSS_ORIGIN_EMBEDDER_POLICY", "require-corp"
            )

        if settings.ENABLE_CROSS_DOMAIN_POLICIES:
            response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        if settings.ENABLE_DNS_PREFETCH_CONTROL:
            response.headers["X-DNS-Prefetch-Control"] = "off"

        if settings.ENABLE_HSTS:
            response.headers["Strict-Transport-Security"] = getattr(
                settings,
                "HSTS_HEADER_VALUE",
                "max-age=63072000; includeSubDomains; preload",
            )

        if settings.ENABLE_CSP:
            response.headers["Content-Security-Policy"] = getattr(
                settings,
                "CSP_HEADER_VALUE",
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https: data:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self';",
            )

        return response
