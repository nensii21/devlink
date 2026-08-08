# User Session Activity Documentation (#588)

DevLink **User Session Activity** enables users to review, audit, and manage active devices and login sessions currently authenticated into their account. Users can view device names, browsers, operating systems, IP addresses (with an IP masking toggle for privacy), last active timestamps, and current session indicators. They can selectively revoke individual sessions or revoke all other sessions with a single click.

---

## 1. Features & Security Safeguards

- **Device & System Details**: Displays device category (Laptop, Desktop, Smartphone, Tablet), browser, operating system, and user agent.
- **Current Session Indicator**: Prominently highlights the session corresponding to the active browser request.
- **Privacy IP Masking**: Includes a toggle to obscure IP addresses (e.g. `192.168.***.***` or `127.0.0.1` masked as `127.0.0.***`) when taking screenshots or sharing screen.
- **Granular Session Revocation**: Users can revoke any individual non-current session immediately.
- **Bulk Revocation ("Revoke all other sessions")**: Instantly invalidates all other active sessions while preserving the current active session.
- **Backend Authorization**: All session retrieval and revocation endpoints strictly verify ownership against the current JWT subject (`current_user.id`).

---

## 2. Component Architecture

Component: `frontend/src/components/settings/UserSessionsActivity.tsx`

Integration: Rendered inside the Security tab of `frontend/src/routes/_app.settings.tsx`.

API Module: `frontend/src/api/modules/sessions.ts`

---

## 3. API Reference

### 1. List Active Sessions
`GET /api/auth/sessions`

**Response:**
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "device_name": "MacBook Pro",
    "device_type": "Laptop",
    "browser": "Chrome 124",
    "operating_system": "macOS 14.4",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "is_revoked": false,
    "created_at": "2026-08-04T10:00:00Z",
    "last_used_at": "2026-08-05T16:00:00Z",
    "expires_at": "2026-08-18T10:00:00Z",
    "is_current": true
  }
]
```

---

### 2. Revoke Individual Session
`DELETE /api/auth/sessions/{session_id}`

**Response:**
```json
{
  "success": true,
  "message": "Session revoked successfully.",
  "revoked_count": 1
}
```

---

### 3. Revoke All Other Sessions
`POST /api/auth/sessions/revoke-others?current_session_id={current_session_id}`

**Response:**
```json
{
  "success": true,
  "message": "Revoked 2 other session(s).",
  "revoked_count": 2
}
```

---

## 4. Running Tests

Execute backend unit and integration tests:
```bash
cd backend
./venv/bin/pytest tests/test_user_session_activity.py -v
```

Expected output: **4 passed**.
