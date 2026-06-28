import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


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

        request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response
