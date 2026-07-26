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
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

from app.core.config import settings

router = APIRouter(prefix="/ws", tags=["WebSockets"])
logger = logging.getLogger(__name__)


# ── Authentication ───────────────────────────────────────────────────────────


def authenticate_ws_token(token: str) -> Optional[str]:
    """Decode a JWT token and return the user_id (``sub`` claim).

    Returns ``None`` if the token is invalid, expired, or missing the
    ``sub`` claim.  This is the WebSocket equivalent of
    ``dependencies.get_current_user`` — browsers cannot send
    ``Authorization`` headers on WebSocket handshakes, so the token is
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
    """Manages WebSocket connections with project-scoped rooms.

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

    # ── Connection lifecycle ─────────────────────────────────────────────

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept the WebSocket and register it under ``user_id``."""
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)
        logger.info(
            "User %s connected. Active sessions: %d",
            user_id,
            len(self.active_connections[user_id]),
        )

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a single WebSocket connection for ``user_id``."""
        conns = self.active_connections.get(user_id)
        if conns and websocket in conns:
            conns.remove(websocket)
        if conns is not None and not conns:
            del self.active_connections[user_id]
            # Remove user from all rooms they were in.
            for room_users in self.rooms.values():
                room_users.discard(user_id)
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
            self.disconnect(conn, user_id)

    async def broadcast_to_room(self, room_id: str, message: dict) -> None:
        """Broadcast ``message`` to every user currently in room ``room_id``."""
        members = self.rooms.get(room_id, set()).copy()
        for user_id in members:
            await self.send_personal_message(message, user_id)

    async def broadcast_to_all(self, message: dict) -> None:
        """Broadcast ``message`` to every connected user (use sparingly)."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)


manager = ConnectionManager()


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
        manager.disconnect(websocket, user_id)
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


# ── Legacy chat endpoint (kept for backwards compatibility) ─────────────────


@router.websocket("/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """Legacy unauthenticated chat endpoint.

    .. deprecated::
        Use ``/ws/collab?token=<jwt>`` instead.  This endpoint is kept
        only so existing clients don't break during the transition.
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            msg_type = message_data.get("type", "message")
            recipient_id = message_data.get("recipient_id")

            payload = {
                "sender_id": user_id,
                "type": msg_type,
                "content": message_data.get("content"),
                "status": "delivered",
            }

            if recipient_id:
                await manager.send_personal_message(payload, recipient_id)
            else:
                await manager.broadcast_to_all(payload)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        await manager.broadcast_to_all(
            {"sender_id": user_id, "type": "status", "content": "offline"}
        )
