import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.client_address import client_address

logger = structlog.get_logger("devlink.request")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured Logging Middleware.

    Responsibilities:
    1. Extract or generate X-Request-ID and X-Correlation-ID.
    2. Bind them to structlog contextvars so all logs in the request share them.
    3. Log request lifecycle (duration, status, path, method).
    4. Attach the IDs to the response headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Extract or Generate IDs
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex}"
        correlation_id = (
            request.headers.get("X-Correlation-ID") or f"corr_{uuid.uuid4().hex}"
        )

        # 2. Bind to structlog ContextVars
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        start_time = time.perf_counter()

        # Extract useful IP and User Agent. This took the leftmost
        # `X-Forwarded-For` entry, which is the one the client fully controls,
        # so the logged IP was whatever the caller claimed. `client_address`
        # believes the header only when the request came through a proxy we
        # trust.
        ip = client_address(request)

        user_agent = request.headers.get("user-agent")

        try:
            # 3. Process the Request
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log Success
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration=round(duration_ms, 2),
                ip=ip,
                user_agent=user_agent,
            )

            # 4. Attach Headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            # Log Failure
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "http_request_error",
                method=request.method,
                path=request.url.path,
                status=500,
                duration=round(duration_ms, 2),
                ip=ip,
                user_agent=user_agent,
                exc_info=exc,
            )
            raise
