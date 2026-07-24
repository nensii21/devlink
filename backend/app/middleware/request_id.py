import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import log_request


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adds a unique Request ID to every request.

    Useful for debugging, logging and tracing.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:

        # Generate a unique Request ID
        request_id = str(uuid.uuid4())

        # Store it in the request state
        request.state.request_id = request_id

        # Start timing the request
        start_time = time.perf_counter()

        # Process the request
        response = await call_next(request)

        # Calculate request duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log request details
        log_request(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # Attach Request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
