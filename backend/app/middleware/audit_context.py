import contextvars
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.client_address import client_address

# Context variables to hold request-scoped data for audit logging
audit_ip_address = contextvars.ContextVar("audit_ip_address", default=None)
audit_user_agent = contextvars.ContextVar("audit_user_agent", default=None)
audit_request_method = contextvars.ContextVar("audit_request_method", default=None)
audit_request_path = contextvars.ContextVar("audit_request_path", default=None)


class AuditContextMiddleware(BaseHTTPMiddleware):
    """
    Extracts common request attributes (IP, User Agent, Method, Path)
    and stores them in contextvars so they can be accessed anywhere
    during the request lifecycle without passing the Request object around.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # This used the leftmost `X-Forwarded-For` entry, which is the one
        # the client fully controls -- so the IP on every audit record was
        # whatever the caller claimed it was. `client_address` honours the
        # header only for requests that arrived through a trusted proxy.
        ip = client_address(request)

        ua = request.headers.get("user-agent")

        # Set context variables
        ip_token = audit_ip_address.set(ip)
        ua_token = audit_user_agent.set(ua)
        method_token = audit_request_method.set(request.method)
        path_token = audit_request_path.set(request.url.path)

        try:
            response = await call_next(request)
            return response
        finally:
            audit_ip_address.reset(ip_token)
            audit_user_agent.reset(ua_token)
            audit_request_method.reset(method_token)
            audit_request_path.reset(path_token)
