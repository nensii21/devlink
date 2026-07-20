from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database.session import SessionLocal
from app.models.user import User

THROTTLE_SECONDS = 300  # 5 minutes


class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    """
    Updates the ``last_active_at`` timestamp for authenticated users.

    To avoid excessive database writes the update is throttled: the
    timestamp is only written when the previous value is older than
    ``THROTTLE_SECONDS`` (5 minutes).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Only track after a successful-ish response (skip 4xx/5xx for perf)
        if response.status_code >= 500:
            return response

        # Attempt to extract user ID from the Authorization header.
        # We intentionally keep this lightweight — no full JWT validation
        # here, just a best-effort extraction so the auth dependency can
        # handle the real security checks.
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return response

        token = auth_header[7:]
        if not token:
            return response

        # Lazy import to avoid circular imports at module level
        from app.core.security import decode_token

        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            if not user_id:
                return response
        except Exception:
            return response

        try:
            db = SessionLocal()
            try:
                user = db.get(User, user_id)
                if user and user.is_active:
                    now = datetime.now(timezone.utc)
                    # Throttle: only write if last_active_at is older than 5 min
                    if (
                        user.last_active_at is None
                        or (now - user.last_active_at).total_seconds()
                        > THROTTLE_SECONDS
                    ):
                        user.last_active_at = now
                        db.commit()
            finally:
                db.close()
        except Exception:
            # Never let activity tracking crash the request
            pass

        return response
