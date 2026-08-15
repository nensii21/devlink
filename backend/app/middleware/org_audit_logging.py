import uuid
import re
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.models.audit_log import AuditAction
from app.services.audit_log_service import AuditLogService

# Organization path regex: /api/v1/organizations/{org_id}/...
ORG_PATH_REGEX = re.compile(
    r"^/api/v1/organizations/([a-f0-9\-]+)(/.*)?$", re.IGNORECASE
)


class OrganizationAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Only process mutating operations (POST, PUT, PATCH, DELETE) under /api/v1/organizations/
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return response

        path = request.url.path
        match = ORG_PATH_REGEX.match(path)
        if not match:
            return response

        org_id_str = match.group(1)
        subpath = match.group(2) or ""

        # Skip logging audit query endpoints themselves
        if "/audit-logs" in subpath:
            return response

        try:
            org_id = uuid.UUID(org_id_str)
        except ValueError:
            return response

        action = self._determine_action(request.method, subpath)
        if not action:
            return response

        actor_id: Optional[uuid.UUID] = None
        # Try to extract current user from request state if set by auth dependency
        if hasattr(request.state, "user") and request.state.user:
            actor_id = getattr(request.state.user, "id", None)

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Record immutable audit entry
        try:
            from app.database.session import SessionLocal

            db = SessionLocal()
            try:
                AuditLogService.create_log(
                    db,
                    actor_id=actor_id,
                    action=action,
                    entity_type="organization",
                    entity_id=str(org_id),
                    organization_id=org_id,
                    description=f"{request.method} {path} (HTTP {response.status_code})",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_method=request.method,
                    request_path=path,
                    success=response.status_code < 400,
                    status_code=response.status_code,
                )
                db.commit()
            finally:
                db.close()
        except Exception:
            pass  # Do not block request flow on logging failure

        return response

    def _determine_action(self, method: str, subpath: str) -> Optional[AuditAction]:
        subpath = subpath.lower()
        if "invite" in subpath or "members/invite" in subpath:
            return AuditAction.MEMBER_INVITED
        elif "members" in subpath and method == "DELETE":
            return AuditAction.MEMBER_REMOVED
        elif "role" in subpath or "members" in subpath and method in {"PUT", "PATCH"}:
            return AuditAction.ROLE_UPDATED
        elif "settings" in subpath or subpath == "" and method in {"PUT", "PATCH"}:
            return AuditAction.SETTINGS_CHANGED
        elif "projects" in subpath and method == "POST":
            return AuditAction.PROJECT_CREATED
        elif "archive" in subpath or "projects" in subpath and method == "DELETE":
            return AuditAction.PROJECT_ARCHIVED
        elif "api-keys" in subpath or "keys" in subpath:
            if method == "POST":
                return AuditAction.API_KEY_CREATED
            elif method == "DELETE":
                return AuditAction.API_KEY_REVOKED
            return AuditAction.API_TOKEN_CREATED
        return AuditAction.ORGANIZATION_UPDATED
