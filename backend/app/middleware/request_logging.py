import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database.session import SessionLocal
from app.models.request_log import RequestLog

# Paths that should not be recorded (noise, static assets, or self-generated)
SKIP_PREFIXES = (
    "/uploads",
    "/health",
    "/openapi",
    "/redoc",
    "/docs",
    "/static",
    "/metrics",
    "/favicon",
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Records metadata for every API request into the ``request_logs`` table.

    Stored per request: method, path, status code, duration in ms, the
    authenticated user id (best-effort), whether the request was rate
    limited (HTTP 429), and a timestamp.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.startswith(SKIP_PREFIXES):
            return await call_next(request)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._record(
                request=request,
                status_code=500,
                duration_ms=duration_ms,
                is_rate_limited=False,
            )
            raise

        self._record(
            request=request,
            status_code=response.status_code,
            duration_ms=duration_ms,
            is_rate_limited=response.status_code == 429,
        )
        return response

    @staticmethod
    def _record(
        request: Request,
        status_code: int,
        duration_ms: float,
        is_rate_limited: bool,
    ) -> None:
        user_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            from app.core.security import decode_access_token

            # Attribution only, but still access-token-only: a request bearing
            # anything else is not an authenticated request, and logging it as
            # one makes the request log disagree with what actually happened.
            try:
                payload = decode_access_token(auth_header[7:])
                user_id = payload.get("sub")
            except ValueError:
                user_id = None

        try:
            db = SessionLocal()
            try:
                db.add(
                    RequestLog(
                        method=request.method,
                        path=request.url.path,
                        status_code=status_code,
                        duration_ms=round(duration_ms, 2),
                        user_id=user_id,
                        is_rate_limited=is_rate_limited,
                    )
                )
                db.commit()
            finally:
                db.close()
        except Exception:
            # Never let request logging crash the request
            pass
