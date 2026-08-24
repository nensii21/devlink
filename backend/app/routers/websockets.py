from __future__ import annotations

"""
websockets.py
-------------

Real-time team collaboration via WebSockets.

Provides authenticated WebSocket connections with project-scoped rooms.
Team members receive live updates for:
  - Team member joins / leaves
  - Project updates
  - New messages
  - Task (issue) status changes

Security:
  Connections are authenticated via a JWT token passed as the ``token``
  query parameter (browsers cannot send custom headers on WebSocket
  handshakes).  The token is decoded with the same secret / algorithm
  used for REST auth, so every WebSocket connection is tied to a real
  authenticated user — no anonymous connections are accepted.

Architecture:
  ``ConnectionManager`` maintains a two-level mapping:
    user_id  →  set of WebSocket connections (a user may have multiple tabs)
    room_id  →  set of user_ids currently in that room

  All broadcast methods iterate over the room's user set and deliver to
  every active connection for each user, so a user with two tabs open
  receives the event on both.
"""


import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

from app.core.config import settings
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ws", tags=["WebSockets"])
logger = logging.getLogger(__name__)


# ── Authentication ───────────────────────────────────────────────────────────


def authenticate_ws_token(token: str) -> Optional[str]:
    """Decode a JWT token and return the user_id (``sub`` claim).

    Returns ``None`` if the token is invalid, expired, or missing the
    ``sub`` claim.  This is the WebSocket equivalent of
    `dependencies.get_current_user` — browsers cannot send
    `Authorization` headers on WebSocket handshakes, so the token is
    passed as a query parameter instead.
    """
    try:
        payload: Dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            return None
        return str(user_id)
    except JWTError:
        return None


# ── Connection Manager ───────────────────────────────────────────────────────


class ConnectionManager:
    """Manages WebSocket connections with project-scoped rooms and user presence.

    A "room" is identified by a project UUID string.  Users join rooms
    to receive project-scoped broadcasts (member joins/leaves, project
    updates, task status changes).  Personal events (direct messages,
    typing indicators) are delivered directly to the user's connections
    regardless of room membership.
    """

    def __init__(self) -> None:
        # user_id → list of active WebSocket connections (multi-tab support)
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # room_id (project UUID string) → set of user_ids currently in room
        self.rooms: Dict[str, Set[str]] = {}
        # user_id → presence status ("online", "away", "busy", "offline")
        self.presence_states: Dict[str, str] = {}
        # user_id → collaboration status ("coding", "reviewing_pr", ...)
        self.collaboration_states: Dict[str, str] = {}
        # user_id → timestamp of last activity
        self.last_activity: Dict[str, datetime] = {}

    # ── Connection lifecycle ─────────────────────────────────────────────

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept the WebSocket and register it under ``user_id``."""
        await websocket.accept()
        is_first_connection = user_id not in self.active_connections
        self.active_connections.setdefault(user_id, []).append(websocket)

        self.last_activity[user_id] = datetime.now(timezone.utc)
        if is_first_connection:
            self.presence_states[user_id] = "online"
            await self.broadcast_to_all(
                _event("presence.status_changed", user_id=user_id, status="online"),
                exclude_user_id=user_id,
            )

        logger.info(
            "User %s connected. Active sessions: %d",
            user_id,
            len(self.active_connections[user_id]),
        )

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a single WebSocket connection for ``user_id``."""
        conns = self.active_connections.get(user_id)
        if conns and websocket in conns:
            conns.remove(websocket)
        if conns is not None and not conns:
            del self.active_connections[user_id]
            # Remove user from all rooms they were in.
            for room_users in self.rooms.values():
                room_users.discard(user_id)

            # Set user offline and notify others
            self.presence_states[user_id] = "offline"
            await self.broadcast_to_all(
                _event("presence.status_changed", user_id=user_id, status="offline"),
                exclude_user_id=user_id,
            )
            self.presence_states.pop(user_id, None)
            self.collaboration_states.pop(user_id, None)
            self.last_activity.pop(user_id, None)

        logger.info("User %s disconnected a session.", user_id)

    # ── Room management ──────────────────────────────────────────────────

    def join_room(self, room_id: str, user_id: str) -> None:
        """Add ``user_id`` to room ``room_id``."""
        self.rooms.setdefault(room_id, set()).add(user_id)

    def leave_room(self, room_id: str, user_id: str) -> None:
        """Remove ``user_id`` from room ``room_id``."""
        room = self.rooms.get(room_id)
        if room:
            room.discard(user_id)
            if not room:
                del self.rooms[room_id]

    def get_room_members(self, room_id: str) -> Set[str]:
        """Return the set of user_ids currently in ``room_id``."""
        return self.rooms.get(room_id, set()).copy()

    # ── Presence Helpers ─────────────────────────────────────────────────

    async def update_activity(self, user_id: str) -> None:
        """Update last activity timestamp for user, and wake up from away status."""
        self.last_activity[user_id] = datetime.now(timezone.utc)
        current_status = self.presence_states.get(user_id)
        if current_status == "away":
            self.presence_states[user_id] = "online"
            await self.broadcast_to_all(
                _event("presence.status_changed", user_id=user_id, status="online")
            )

    async def update_presence_status(self, user_id: str, status: str) -> None:
        """Manually update user's presence status."""
        allowed_statuses = {"online", "away", "busy", "offline"}
        if status not in allowed_statuses:
            raise ValueError(f"Invalid presence status: {status}")

        self.presence_states[user_id] = status
        await self.broadcast_to_all(
            _event("presence.status_changed", user_id=user_id, status=status)
        )

    def set_collaboration_status(self, user_id: str, status: str) -> None:
        """Record a user's collaboration presence status (persisted elsewhere).

        Synchronous — called from REST handlers. The actual broadcast is done
        by ``broadcast_collaboration_status`` so the async broadcast is not
        blocked on the request path.
        """
        allowed_statuses = {
            "coding",
            "reviewing_pr",
            "in_meeting",
            "looking_for_project",
            "available",
        }
        if status not in allowed_statuses:
            raise ValueError(f"Invalid collaboration status: {status}")
        self.collaboration_states[user_id] = status

    async def broadcast_collaboration_status(self, user_id: str, status: str) -> None:
        """Broadcast a collaboration status change to all connected clients."""
        self.collaboration_states[user_id] = status
        await self.broadcast_to_all(
            _event(
                "presence.collaboration_status_changed",
                user_id=user_id,
                status=status,
            )
        )

    async def check_timeouts(self, timeout_seconds: int = 300) -> None:
        """Check for inactive users and transition them to away status."""
        now = datetime.now(timezone.utc)
        for user_id, last_act in list(self.last_activity.items()):
            if self.presence_states.get(user_id) == "online":
                if (now - last_act).total_seconds() > timeout_seconds:
                    self.presence_states[user_id] = "away"
                    await self.broadcast_to_all(
                        _event(
                            "presence.status_changed", user_id=user_id, status="away"
                        )
                    )

    # ── Message delivery ─────────────────────────────────────────────────

    async def send_personal_message(self, message: dict, user_id: str) -> None:
        """Send ``message`` to every active connection for ``user_id``."""
        conns = self.active_connections.get(user_id, [])
        dead: List[WebSocket] = []
        for conn in conns:
            try:
                await conn.send_text(json.dumps(message))
            except Exception:
                dead.append(conn)
        for conn in dead:
            await self.disconnect(conn, user_id)

    async def broadcast_to_room(self, room_id: str, message: dict) -> None:
        """Broadcast ``message`` to every user currently in room ``room_id``."""
        members = self.rooms.get(room_id, set()).copy()
        for user_id in members:
            await self.send_personal_message(message, user_id)

    async def broadcast_to_all(
        self, message: dict, exclude_user_id: Optional[str] = None
    ) -> None:
        """Broadcast ``message`` to every connected user (use sparingly)."""
        for user_id in list(self.active_connections.keys()):
            if user_id == exclude_user_id:
                continue
            await self.send_personal_message(message, user_id)


manager = ConnectionManager()


# ── HTTP REST Endpoints ─────────────────────────────────────────────────────


@router.get("/presence", response_model=Dict[str, str])
def get_all_presences(current_user: User = Depends(get_current_user)):
    """Retrieve active presence states for all connected users."""
    return manager.presence_states.copy()


@router.get("/collaboration-status", response_model=Dict[str, str])
def get_all_collaboration_statuses(current_user: User = Depends(get_current_user)):
    """Retrieve collaboration statuses for all connected users."""
    return manager.collaboration_states.copy()


@router.get("/presence/{user_id}", response_model=Dict[str, str])
def get_user_presence(user_id: str, current_user: User = Depends(get_current_user)):
    """Retrieve presence status of a specific user."""
    status = manager.presence_states.get(user_id, "offline")
    return {"user_id": user_id, "status": status}


# ── Event helpers ────────────────────────────────────────────────────────────


def _event(
    event_type: str,
    *,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **extra: Any,
) -> dict:
    """Build a typed event envelope."""
    evt: dict = {"type": event_type}
    if project_id:
        evt["project_id"] = project_id
    if user_id:
        evt["user_id"] = user_id
    evt.update(extra)
    return evt


# ── WebSocket endpoint ───────────────────────────────────────────────────────


@router.websocket("/collab")
async def websocket_collab(websocket: WebSocket, token: str = ""):
    """Authenticated WebSocket endpoint for real-time team collaboration.

    Authentication:
      The ``token`` query parameter must contain a valid JWT.  If it's
      missing or invalid the connection is closed with code 4001
      (policy violation) before the handshake completes.

    Client → Server messages:
      ``{"type": "join", "project_id": "<uuid>"}``     — Join a project room
      ``{"type": "leave", "project_id": "<uuid>"}``    — Leave a project room
      ``{"type": "message", "project_id": "...", "content": "..."}``
      ``{"type": "task_update", "project_id": "...", "task_id": "...", "status": "..."}``
      ``{"type": "project_update", "project_id": "...", "changes": {...}}``

    Server → Client events:
      ``connected``  ``team.member_joined``  ``team.member_left``
      ``message.new``  ``task.status_changed``  ``project.updated``
      ``error``  ``status``
    """
    # ── Authenticate ─────────────────────────────────────────────────────
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = authenticate_ws_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ── Accept & register ────────────────────────────────────────────────
    await manager.connect(websocket, user_id)

    # Confirm connection to the client.
    await manager.send_personal_message(
        _event("connected", user_id=user_id),
        user_id,
    )

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    _event("error", message="Invalid JSON"),
                    user_id,
                )
                continue

            await manager.update_activity(user_id)

            msg_type = data.get("type", "")
            project_id = data.get("project_id", "")

            # ── Join a project room ─────────────────────────────────────
            if msg_type == "join" and project_id:
                manager.join_room(project_id, user_id)
                await manager.broadcast_to_room(
                    project_id,
                    _event(
                        "team.member_joined",
                        project_id=project_id,
                        user_id=user_id,
                    ),
                )
                logger.info("User %s joined room %s", user_id, project_id)

            # ── Leave a project room ─────────────────────────────────────
            elif msg_type == "leave" and project_id:
                await manager.broadcast_to_room(
                    project_id,
                    _event(
                        "team.member_left",
                        project_id=project_id,
                        user_id=user_id,
                    ),
                )
                manager.leave_room(project_id, user_id)

                logger.info("User %s left room %s", user_id, project_id)

            # ── New message in a project room ────────────────────────────
            elif msg_type == "message" and project_id:
                await manager.broadcast_to_room(
                    project_id,
                    _event(
                        "message.new",
                        project_id=project_id,
                        user_id=user_id,
                        content=data.get("content", ""),
                    ),
                )

            # ── Task status change ───────────────────────────────────────
            elif msg_type == "task_update" and project_id:
                await manager.broadcast_to_room(
                    project_id,
                    _event(
                        "task.status_changed",
                        project_id=project_id,
                        user_id=user_id,
                        task_id=data.get("task_id", ""),
                        status=data.get("status", ""),
                    ),
                )

            # ── Chat Conversations ───────────────────────────────────────
            elif msg_type == "chat.join" and data.get("conversation_id"):
                conv_id = data["conversation_id"]
                manager.join_room(conv_id, user_id)
                logger.info("User %s joined conversation %s", user_id, conv_id)

            elif msg_type == "chat.leave" and data.get("conversation_id"):
                conv_id = data["conversation_id"]
                manager.leave_room(conv_id, user_id)
                logger.info("User %s left conversation %s", user_id, conv_id)

            elif msg_type == "chat.message" and data.get("conversation_id"):
                conv_id = data["conversation_id"]
                await manager.broadcast_to_room(
                    conv_id,
                    _event(
                        "chat.message.new",
                        conversation_id=conv_id,
                        user_id=user_id,
                        content=data.get("content", ""),
                    ),
                )

            elif msg_type == "chat.typing" and data.get("conversation_id"):
                conv_id = data["conversation_id"]
                await manager.broadcast_to_room(
                    conv_id,
                    _event(
                        "chat.typing",
                        conversation_id=conv_id,
                        user_id=user_id,
                    ),
                )

            elif msg_type == "chat.delivered" and data.get("conversation_id"):
                conv_id = data["conversation_id"]
                await manager.broadcast_to_room(
                    conv_id,
                    _event(
                        "chat.message.delivered",
                        conversation_id=conv_id,
                        user_id=user_id,
                        message_ids=data.get("message_ids", []),
                    ),
                )

            elif msg_type == "chat.read" and data.get("conversation_id"):
                conv_id = data["conversation_id"]
                await manager.broadcast_to_room(
                    conv_id,
                    _event(
                        "chat.message.read",
                        conversation_id=conv_id,
                        user_id=user_id,
                        message_ids=data.get("message_ids", []),
                    ),
                )

            # ── Project update ───────────────────────────────────────────
            elif msg_type == "project_update" and project_id:
                await manager.broadcast_to_room(
                    project_id,
                    _event(
                        "project.updated",
                        project_id=project_id,
                        user_id=user_id,
                        changes=data.get("changes", {}),
                    ),
                )

            # ── Presence Update ─────────────────────────────────────────
            elif msg_type == "presence_update":
                status_val = data.get("status")
                try:
                    await manager.update_presence_status(user_id, status_val)
                except ValueError as exc:
                    await manager.send_personal_message(
                        _event("error", message=str(exc)),
                        user_id,
                    )

            # ── Presence Query ──────────────────────────────────────────
            elif msg_type == "presence_query":
                queried_ids = data.get("user_ids")
                if isinstance(queried_ids, list):
                    presences = {
                        uid: manager.presence_states.get(uid, "offline")
                        for uid in queried_ids
                    }
                else:
                    presences = manager.presence_states.copy()

                await manager.send_personal_message(
                    _event("presence.query_response", presences=presences),
                    user_id,
                )

            # ── Collaboration Status Update ─────────────────────────────
            elif msg_type == "collaboration_status_update":
                status_val = data.get("status")
                allowed_statuses = {
                    "coding",
                    "reviewing_pr",
                    "in_meeting",
                    "looking_for_project",
                    "available",
                }
                if status_val not in allowed_statuses:
                    await manager.send_personal_message(
                        _event("error", message=f"Invalid collaboration status: {status_val}"),
                        user_id,
                    )
                else:
                    await manager.broadcast_collaboration_status(user_id, status_val)

            # ── Document Collaboration Events ───────────────────────────
            elif msg_type == "doc.join" and project_id:
                manager.join_room(project_id, user_id)
                await manager.broadcast_to_room(
                    project_id,
                    _event(
                        "doc.user_joined",
                        project_id=project_id,
                        user_id=user_id,
                        doc_id=data.get("doc_id", ""),
                    ),
                )

            elif msg_type == "doc.edit" and project_id:
                doc_id = data.get("doc_id", "")
                content = data.get("content", "")
                title = data.get("title")
                base_version = data.get("base_version")

                from app.database.session import SessionLocal
                from app.services.project_document_service import ProjectDocumentService

                db_session = SessionLocal()
                try:
                    doc_uuid = UUID(doc_id) if doc_id else None
                    if doc_uuid:
                        updated_doc, is_conflict = (
                            ProjectDocumentService.update_document(
                                db_session,
                                doc_id=doc_uuid,
                                user_id=UUID(user_id) if user_id else user_id,
                                title=title,
                                content=content,
                                base_version=base_version,
                            )
                        )
                        event_payload = _event(
                            "doc.updated",
                            project_id=project_id,
                            doc_id=doc_id,
                            user_id=user_id,
                            content=updated_doc.content,
                            title=updated_doc.title,
                            version=updated_doc.version,
                            conflict=is_conflict,
                        )
                        await manager.broadcast_to_room(project_id, event_payload)

                        if is_conflict:
                            await manager.send_personal_message(
                                _event(
                                    "doc.conflict",
                                    doc_id=doc_id,
                                    version=updated_doc.version,
                                    server_content=updated_doc.content,
                                    message="Conflict detected. Merged with server version.",
                                ),
                                user_id,
                            )
                    else:
                        await manager.broadcast_to_room(
                            project_id,
                            _event(
                                "doc.updated",
                                project_id=project_id,
                                doc_id=doc_id,
                                user_id=user_id,
                                content=content,
                                title=title,
                                version=(base_version or 1) + 1,
                                conflict=False,
                            ),
                        )
                except Exception as exc:
                    logger.warning("Error updating document in websocket: %s", exc)
                    await manager.broadcast_to_room(
                        project_id,
                        _event(
                            "doc.updated",
                            project_id=project_id,
                            doc_id=doc_id,
                            user_id=user_id,
                            content=content,
                            title=title,
                            version=(base_version or 1) + 1,
                            conflict=False,
                        ),
                    )
                finally:
                    db_session.close()

            elif msg_type == "doc.cursor" and project_id:
                await manager.broadcast_to_room(
                    project_id,
                    _event(
                        "doc.cursor_moved",
                        project_id=project_id,
                        doc_id=data.get("doc_id", ""),
                        user_id=user_id,
                        cursor_offset=data.get("cursor_offset", 0),
                        selection_start=data.get("selection_start"),
                        selection_end=data.get("selection_end"),
                    ),
                )

            # ── Unknown message type ─────────────────────────────────────
            else:
                await manager.send_personal_message(
                    _event(
                        "error",
                        message=f"Unknown message type: {msg_type}",
                    ),
                    user_id,
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)
        # Notify all rooms the user was in that they left.
        for room_id in list(manager.rooms.keys()):
            if user_id in manager.rooms[room_id]:
                manager.leave_room(room_id, user_id)
                await manager.broadcast_to_room(
                    room_id,
                    _event(
                        "team.member_left",
                        project_id=room_id,
                        user_id=user_id,
                    ),
                )


# ── Legacy chat endpoint (removed) ──────────────────────────────────────────
#
# The unauthenticated `/ws/chat/{user_id}` endpoint has been removed
# because it allowed anyone to connect as any user with zero authentication,
# enabling user impersonation. Use `/ws/collab?token=<jwt>` instead.
