Here's the complete `docs/WEBSOCKETS.md` documentation file:

---

## 📁 `docs/WEBSOCKETS.md` (NEW — full contents)

````markdown
# Real-Time Team Collaboration (WebSockets)

## Overview

DevLink uses WebSockets to deliver real-time updates to team members without page refreshes. The implementation provides authenticated connections, project-scoped rooms, and typed events for team collaboration.

## Architecture

```
┌─────────────┐     JWT (query param)     ┌──────────────────┐
│  Frontend   │◄─────────────────────────►│   Backend        │
│  ws.ts      │    WebSocket (JSON)        │   websockets.py  │
│             │                            │                  │
│  WsClient   │                            │  ConnectionManager│
│  - connect  │                            │  - connect()     │
│  - joinRoom │                            │  - join_room()   │
│  - on(event)│                            │  - broadcast()   │
└─────────────┘                            └──────────────────┘
```

### Backend (`backend/app/routers/websockets.py`)

- **`ConnectionManager`** — maintains a two-level mapping:
  - `user_id → [WebSocket, ...]` (multi-tab support — a user with two tabs gets events on both)
  - `room_id → {user_id, ...}` (project-scoped rooms — broadcasts only reach room members)
- **`/ws/collab?token=<jwt>`** — authenticated WebSocket endpoint for real-time collaboration
- **`/ws/chat/{user_id}`** — legacy unauthenticated endpoint (deprecated, kept for backwards compatibility)

#### `ConnectionManager` API

| Method | Description |
|--------|-------------|
| `connect(websocket, user_id)` | Accept the WebSocket and register it under `user_id` |
| `disconnect(websocket, user_id)` | Remove a single WebSocket connection; if no connections remain, remove user from all rooms |
| `join_room(room_id, user_id)` | Add `user_id` to room `room_id` |
| `leave_room(room_id, user_id)` | Remove `user_id` from room `room_id` |
| `get_room_members(room_id)` | Return the set of user_ids currently in `room_id` |
| `send_personal_message(message, user_id)` | Send `message` to every active connection for `user_id` |
| `broadcast_to_room(room_id, message)` | Broadcast `message` to every user in `room_id` |
| `broadcast_to_all(message)` | Broadcast `message` to every connected user (use sparingly) |

### Frontend (`frontend/src/api/ws.ts`)

- **`WsClient`** — singleton WebSocket client with:
  - Auto-reconnect with exponential backoff (capped at 30s)
  - JWT auth via query param
  - Project room join/leave
  - Typed event bus (`on(handler)`)
  - Auto re-join of rooms on reconnect

#### `WsClient` API

| Method | Description |
|--------|-------------|
| `connect()` | Open the WebSocket connection (idempotent) |
| `disconnect()` | Close the connection and stop auto-reconnect |
| `on(handler)` | Register an event handler; returns an unsubscribe function |
| `send(payload)` | Send a JSON payload to the server |
| `joinProject(projectId)` | Join a project room |
| `leaveProject(projectId)` | Leave a project room |
| `sendProjectMessage(projectId, content)` | Send a chat message to a project room |
| `notifyTaskUpdate(projectId, taskId, status)` | Notify a project room of a task status change |
| `notifyProjectUpdate(projectId, changes)` | Notify a project room of project metadata changes |

---

## Authentication

Browsers cannot send custom headers on WebSocket handshakes, so the JWT token is passed as the `token` query parameter:

```
ws://api.devlink.app/ws/collab?token=eyJhbGciOiJIUzI1NiIs...
```

The backend decodes the token using the same `SECRET_KEY` and `JWT_ALGORITHM` as REST auth (`app.core.config.settings`). The `authenticate_ws_token()` function:

1. Decodes the JWT with `jose.jwt.decode()`.
2. Extracts the `sub` claim (user ID).
3. Returns the user ID string, or `None` if the token is invalid/expired.

Invalid or missing tokens result in a **`4001` (policy violation)** WebSocket close code — the connection is rejected before the handshake completes. No anonymous connections are accepted.

### Security model

- **No anonymous connections** — every WebSocket connection requires a valid JWT.
- **Same secret as REST** — the token is decoded with the same `SECRET_KEY` used for all REST API auth.
- **Token in query param** — the only way to pass auth on browser WebSocket handshakes (W3C limitation).
- **No `dangerouslySetInnerHTML`** — all event data is rendered as React children (auto-escaped by React).
- **Dead connection cleanup** — `send_personal_message()` catches send failures and calls `disconnect()` on dead sockets, so stale connections are pruned automatically.

---

## Events

### Client → Server

The client sends JSON messages with a `type` field:

| Type | Fields | Description |
|------|--------|-------------|
| `join` | `project_id` | Join a project room to receive project-scoped events |
| `leave` | `project_id` | Leave a project room |
| `message` | `project_id`, `content` | Send a chat message to all members of a project room |
| `task_update` | `project_id`, `task_id`, `status` | Notify room members that a task's status changed |
| `project_update` | `project_id`, `changes` | Notify room members that project metadata changed |

**Examples:**

```json
{"type": "join", "project_id": "550e8400-e29b-41d4-a716-446655440000"}
```

```json
{"type": "message", "project_id": "550e8400-...", "content": "Hey team!"}
```

```json
{"type": "task_update", "project_id": "550e8400-...", "task_id": "task-42", "status": "done"}
```

### Server → Client

Every event has a `type` field plus event-specific fields:

| Type | Fields | Description |
|------|--------|-------------|
| `connected` | `user_id` | Connection established and authenticated |
| `team.member_joined` | `project_id`, `user_id` | A team member joined the project room |
| `team.member_left` | `project_id`, `user_id` | A team member left the project room |
| `project.updated` | `project_id`, `user_id`, `changes` | Project metadata changed |
| `message.new` | `project_id`, `user_id`, `content` | A new chat message arrived in the room |
| `task.status_changed` | `project_id`, `user_id`, `task_id`, `status` | A task's status changed |
| `error` | `message` | An error occurred (e.g. invalid JSON, unknown message type) |
| `status` | `sender_id`, `content` | Legacy presence status (from `/ws/chat/{user_id}`) |

**Examples:**

```json
{"type": "connected", "user_id": "550e8400-e29b-41d4-a716-446655440000"}
```

```json
{"type": "team.member_joined", "project_id": "proj-1", "user_id": "user-abc"}
```

```json
{"type": "message.new", "project_id": "proj-1", "user_id": "user-abc", "content": "Hello team!"}
```

```json
{"type": "task.status_changed", "project_id": "proj-1", "user_id": "user-abc", "task_id": "task-42", "status": "done"}
```

```json
{"type": "error", "message": "Unknown message type: bogus"}
```

---

## Usage (Frontend)

### Basic setup

```typescript
import { ws } from "@/api/ws";

// The client auto-connects when a JWT token is available
// (via tokenStore.subscribe). You don't need to call connect() manually.
```

### Listen for events

```typescript
import { ws, type CollabEvent } from "@/api/ws";

const unsubscribe = ws.on((event: CollabEvent) => {
  switch (event.type) {
    case "connected":
      console.log("WebSocket connected");
      break;

    case "team.member_joined":
      console.log(`User ${event.user_id} joined project ${event.project_id}`);
      // Update UI: show "User X is now online" toast
      break;

    case "team.member_left":
      console.log(`User ${event.user_id} left project ${event.project_id}`);
      // Update UI: show "User X went offline" toast
      break;

    case "message.new":
      console.log(`[${event.project_id}] ${event.user_id}: ${event.content}`);
      // Append message to chat UI
      break;

    case "task.status_changed":
      console.log(`Task ${event.task_id} → ${event.status}`);
      // Update task board / kanban UI
      break;

    case "project.updated":
      console.log("Project updated:", event.changes);
      // Refetch project data or apply changes locally
      break;

    case "error":
      console.error("WebSocket error:", event.message);
      break;
  }
});

// Clean up when the component unmounts
// unsubscribe();
```

### Join a project room

```typescript
import { ws } from "@/api/ws";
import { useEffect } from "react";

function ProjectPage({ projectId }: { projectId: string }) {
  useEffect(() => {
    // Join the project room when the page loads
    ws.joinProject(projectId);

    return () => {
      // Leave when navigating away
      ws.leaveProject(projectId);
    };
  }, [projectId]);
}
```

### Send a chat message

```typescript
ws.sendProjectMessage(projectId, "Hey team, check out this PR!");
```

### Notify team of a task status change

```typescript
ws.notifyTaskUpdate(projectId, "task-42", "done");
```

### Notify team of project metadata changes

```typescript
ws.notifyProjectUpdate(projectId, { title: "New Project Name", status: "active" });
```

### Full React component example

```tsx
import { useEffect, useState } from "react";
import { ws, type CollabEvent } from "@/api/ws";

interface Message {
  userId: string;
  content: string;
}

export function ProjectChat({ projectId }: { projectId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    // Join the project room
    ws.joinProject(projectId);

    // Listen for new messages
    const unsubscribe = ws.on((event: CollabEvent) => {
      if (event.type === "message.new" && event.project_id === projectId) {
        setMessages((prev) => [
          ...prev,
          { userId: event.user_id, content: event.content },
        ]);
      }
    });

    return () => {
      ws.leaveProject(projectId);
      unsubscribe();
    };
  }, [projectId]);

  const handleSend = (text: string) => {
    ws.sendProjectMessage(projectId, text);
    // Optimistic: show own message immediately
    setMessages((prev) => [...prev, { userId: "me", content: text }]);
  };

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i}>
          <strong>{msg.userId}:</strong> {msg.content}
        </div>
      ))}
      <button onClick={() => handleSend("Hello!")}>Send</button>
    </div>
  );
}
```

---

## Auto-Reconnection

The frontend client automatically reconnects with exponential backoff:

| Attempt | Delay |
|---------|-------|
| 1 | 1s |
| 2 | 2s |
| 3 | 4s |
| 4 | 8s |
| 5 | 16s |
| 6+ | 30s (capped) |

### How it works

1. When the WebSocket closes unexpectedly (not a manual `disconnect()`), `scheduleReconnect()` is called.
2. The delay is calculated as `min(30000, 1000 * 2^attempts)` — exponential backoff capped at 30 seconds.
3. After the delay, `connect()` is called again.
4. On successful connection (`onopen`), `reconnectAttempts` resets to 0.

### Auto re-join

On reconnect, the client automatically re-joins all project rooms that were active before the disconnection:

```typescript
this.socket.onopen = () => {
  this.reconnectAttempts = 0;
  // Re-join any project rooms that were active before the reconnect.
  for (const projectId of this.joinedProjects) {
    this.send({ type: "join", project_id: projectId });
  }
};
```

This means if a user is viewing a project page and their network drops, the client reconnects and re-joins the project room automatically — **no manual re-join is needed**. The `joinedProjects` Set tracks which rooms the user has joined via `joinProject()`.

---

## Graceful Disconnection

When a user disconnects (closes tab, loses network, etc.):

### Backend behavior

1. The `WebSocketDisconnect` exception is caught in the `websocket_collab` endpoint.
2. `manager.disconnect(websocket, user_id)` removes the WebSocket from the active connections list.
3. If the user has no remaining connections (all tabs closed), the user is removed from all rooms.
4. Each room the user was in receives a `team.member_left` event so other team members are notified.

```python
except WebSocketDisconnect:
    manager.disconnect(websocket, user_id)
    # Notify all rooms the user was in that they left.
    for room_id in list(manager.rooms.keys()):
        if user_id in manager.rooms[room_id]:
            manager.leave_room(room_id, user_id)
            await manager.broadcast_to_room(
                room_id,
                _event("team.member_left", project_id=room_id, user_id=user_id),
            )
```

### Frontend behavior

1. `socket.onclose` fires.
2. If the close was not manual (`manualClose === false`), `scheduleReconnect()` is called.
3. The client attempts to reconnect with exponential backoff.
4. On reconnect, the client re-joins all previously joined rooms.

### Dead connection cleanup

The backend proactively cleans up dead connections. When `send_personal_message()` fails to send to a WebSocket (e.g. the connection is broken but the server hasn't detected it yet), the dead connection is removed:

```python
async def send_personal_message(self, message: dict, user_id: str) -> None:
    conns = self.active_connections.get(user_id, [])
    dead: List[WebSocket] = []
    for conn in conns:
        try:
            await conn.send_text(json.dumps(message))
        except Exception:
            dead.append(conn)
    for conn in dead:
        self.disconnect(conn, user_id)
```

---

## Security

### Authentication

- **No anonymous connections** — every WebSocket connection requires a valid JWT.
- **Token in query param** — the only way to pass auth on browser WebSocket handshakes (W3C limitation; browsers cannot set custom headers on `new WebSocket()`).
- **Same secret as REST** — the token is decoded with the same `SECRET_KEY` and `JWT_ALGORITHM` used for all REST API auth (`app.core.config.settings`).
- **Invalid tokens rejected** — missing or invalid tokens result in a `4001` (policy violation) close code before the handshake completes.

### XSS prevention

- **No `dangerouslySetInnerHTML`** — all event data is rendered as React children, which React escapes automatically.
- **No raw HTML** — the WebSocket events are plain JSON objects, never HTML strings.
- **URL sanitisation** — if rendering links from WebSocket events, always sanitise URLs (e.g. via the `sanitizeUrl()` pattern) to block `javascript:` schemes.

### Room isolation

- **Project-scoped rooms** — broadcasts only reach users who have explicitly joined the room via `{"type": "join", "project_id": "..."}`.
- **No cross-room leakage** — `broadcast_to_room()` iterates only over the room's member set.
- **User removal on disconnect** — when a user's last connection closes, they are removed from all rooms.

---

## Testing

### Backend tests (`backend/tests/test_websockets.py`)

8 tests covering:

| Test | Description |
|------|-------------|
| `test_ws_rejects_missing_token` | Connection without a token is closed |
| `test_ws_rejects_invalid_token` | Connection with an invalid JWT is closed |
| `test_ws_accepts_valid_token` | A valid JWT receives a `connected` event |
| `test_ws_join_and_leave_project` | Joining/leaving a room broadcasts member events |
| `test_ws_message_broadcast` | A message sent to a room is broadcast as `message.new` |
| `test_ws_task_status_change` | A `task_update` is broadcast as `task.status_changed` |
| `test_ws_invalid_json_returns_error` | Malformed JSON returns an `error` event without closing |
| `test_ws_unknown_message_type_returns_error` | Unknown message types return an `error` event |

### Running tests

```bash
cd backend
pytest tests/test_websockets.py -v
```

### Running formatting checks

```bash
# Backend (black)
cd backend
black --check app/routers/websockets.py tests/test_websockets.py

# Frontend (prettier + eslint)
cd frontend
npx prettier --check src/api/ws.ts
npx eslint src/api/ws.ts
```

---

## API Reference (Quick)

### Backend endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/ws/collab?token=<jwt>` | WebSocket | JWT (query param) | Authenticated real-time collaboration |
| `/ws/chat/{user_id}` | WebSocket | None (deprecated) | Legacy unauthenticated chat |

### Frontend exports

```typescript
// Singleton client
export const ws: WsClient;

// Event type union
export type CollabEvent =
  | { type: "connected"; user_id: string }
  | { type: "team.member_joined"; project_id: string; user_id: string }
  | { type: "team.member_left"; project_id: string; user_id: string }
  | { type: "project.updated"; project_id: string; user_id: string; changes: Record<string, unknown> }
  | { type: "message.new"; project_id: string; user_id: string; content: string }
  | { type: "task.status_changed"; project_id: string; user_id: string; task_id: string; status: string }
  | { type: "error"; message: string }
  | { type: string; [k: string]: unknown };

// WsClient methods
ws.connect(): void
ws.disconnect(): void
ws.on(handler: (event: CollabEvent) => void): () => void  // returns unsubscribe
ws.send(payload: Record<string, unknown>): void
ws.joinProject(projectId: string): void
ws.leaveProject(projectId: string): void
ws.sendProjectMessage(projectId: string, content: string): void
ws.notifyTaskUpdate(projectId: string, taskId: string, status: string): void
ws.notifyProjectUpdate(projectId: string, changes: Record<string, unknown>): void
```

---

## Migration Guide

### From the legacy `/ws/chat/{user_id}` endpoint

The legacy endpoint is kept for backwards compatibility but is deprecated. To migrate:

**Before (legacy):**
```typescript
const socket = new WebSocket(`ws://api/ws/chat/${userId}`);
socket.send(JSON.stringify({ type: "message", recipient_id: "user-2", content: "hi" }));
```

**After (authenticated):**
```typescript
import { ws } from "@/api/ws";

// Auto-connects with JWT
ws.on((event) => {
  if (event.type === "message.new") {
    console.log(event.content);
  }
});

ws.joinProject("project-1");
ws.sendProjectMessage("project-1", "hi");
```

### Key differences

| Feature | Legacy `/ws/chat/{user_id}` | New `/ws/collab` |
|---------|----------------------------|------------------|
| Authentication | None (user_id in URL) | JWT (query param) |
| Rooms | No rooms (broadcast all) | Project-scoped rooms |
| Events | `message`, `status` | 7 typed events |
| Auto-reconnect | No | Yes (exponential backoff) |
| Multi-tab | No (one connection per user_id) | Yes (multiple connections per user) |
| Graceful leave | Broadcasts "offline" to all | Notifies only joined rooms |

---

## Troubleshooting

### Connection keeps dropping

- Check that `GROQ_API_KEY`... wait, wrong project. Check that `SECRET_KEY` is set consistently across backend instances.
- Verify the JWT token hasn't expired (tokens have a TTL configured in `app.core.config`).
- Check browser console for WebSocket close codes:
  - `4001` = invalid/missing token
  - `1006` = abnormal closure (network issue)
  - `1011` = server error

### Messages not reaching all team members

- Verify all team members have called `ws.joinProject(projectId)` — only room members receive broadcasts.
- Check that the `project_id` matches exactly (UUID strings are case-sensitive).
- Verify the user's JWT is valid — an expired token will cause silent disconnection.

### Auto-reconnect not working

- Ensure `manualClose` is not `true` (set by `ws.disconnect()`).
- Check that `tokenStore.getAccess()` returns a valid token — the client won't reconnect without one.
- Verify `isBackendConfigured()` returns `true` (requires `VITE_API_BASE_URL` to be set).

### Dead connections accumulating

- The backend proactively cleans up dead connections in `send_personal_message()`.
- If a user has no active connections, they are removed from all rooms automatically.
- No manual cleanup is needed.
````

---

That's the complete `docs/WEBSOCKETS.md` documentation. It covers:

1. **Architecture** — full diagram + backend/frontend API reference tables
2. **Authentication** — JWT via query param, security model, XSS prevention
3. **Events** — complete client→server and server→client event tables with JSON examples
4. **Usage** — basic setup, event listening, room join/leave, sending messages, full React component example
5. **Auto-Reconnection** — backoff table, how it works, auto re-join behavior
6. **Graceful Disconnection** — backend/frontend behavior, dead connection cleanup
7. **Security** — auth, XSS, room isolation
8. **Testing** — 8 test descriptions, how to run tests + formatting checks
9. **API Reference** — backend endpoints + frontend exports quick reference
10. **Migration Guide** — from legacy `/ws/chat/{user_id}` to new `/ws/collab`
11. **Troubleshooting** — common issues and solutions
