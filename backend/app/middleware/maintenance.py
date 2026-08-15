from datetime import datetime, timezone
import typing

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from cachetools import TTLCache

from app.models.maintenance import MaintenanceWindow
from app.models.user import UserRole
from app.core.security import decode_access_token

# Cache the maintenance window state for 30 seconds
maintenance_cache = TTLCache(maxsize=1, ttl=30)
CACHE_KEY = "active_maintenance"


def get_active_maintenance():
    if CACHE_KEY in maintenance_cache:
        return maintenance_cache[CACHE_KEY]

    from app.database.session import SessionLocal

    try:
        with SessionLocal() as db:
            now = datetime.now(timezone.utc)
            from sqlalchemy import select

            stmt = (
                select(MaintenanceWindow)
                .where(
                    MaintenanceWindow.is_active == True,
                    MaintenanceWindow.start_time <= now,
                    MaintenanceWindow.end_time >= now,
                )
                .order_by(MaintenanceWindow.start_time.desc())
                .limit(1)
            )
            window = db.scalar(stmt)
            result = None
            if window:
                result = {
                    "message": window.message,
                    "end_time": window.end_time.isoformat(),
                }
    except Exception:
        # If we cannot query the maintenance window, fail open so a DB blip
        # never takes the whole API down.
        result = None

    maintenance_cache[CACHE_KEY] = result
    return result


class MaintenanceMiddleware(BaseHTTPMiddleware):
    """
    Blocks requests if the system is currently under maintenance, unless the user is an admin.
    """

    async def dispatch(self, request: Request, call_next) -> typing.Any:
        # Exclude paths that should always be available
        if (
            request.url.path.startswith("/api/v1/health")
            or request.url.path.startswith("/docs")
            or request.url.path.startswith("/openapi")
        ):
            return await call_next(request)

        maintenance = get_active_maintenance()

        if maintenance:
            # System is under maintenance. Check if user is admin.
            is_admin = False
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                # This is an authorisation decision -- it decides who gets past
                # a maintenance lockout -- so the token type is checked.
                try:
                    payload = decode_access_token(token)
                    if payload and payload.get("role") == UserRole.ADMIN:
                        is_admin = True
                except ValueError:
                    pass

            # If not admin, return 503
            if not is_admin:
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "Maintenance Mode",
                        "maintenance": maintenance,
                    },
                    headers={"Retry-After": "300"},
                )

        response = await call_next(request)
        return response
