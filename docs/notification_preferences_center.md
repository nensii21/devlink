# Notification Preferences Center Documentation (#586)

The **Notification Preferences Center** provides a centralized interface and RESTful APIs allowing developers to manage notification delivery channels, event categories, and email notification controls.

---

## 1. Supported Notification Categories

The system supports granular toggles across 6 primary categories:

1. **Messages (`messages` & `email_messages`)**: Direct messages and active conversation alerts.
2. **Team Invitations (`team_invitations` & `email_team_invitations`)**: Project invitations, team membership, and role updates.
3. **Project Updates (`project_updates` & `email_project_updates`)**: Milestones, status updates, and repository activity.
4. **Mentions (`mentions` & `email_mentions`)**: Developers tagging or mentioning `@username` in discussions and issues.
5. **System Announcements (`system_announcements` & `email_system_announcements`)**: Platform updates, scheduled maintenance, and system alerts.
6. **Email Notifications (`email_enabled` master toggle)**: Master email toggle and per-category email controls.

---

## 2. API Reference

### Get Notification Preferences
`GET /api/v1/notifications/preferences` (and `/api/notifications/preferences`)

**Authorization:** Requires authenticated user session (`get_current_user`).

**Response Payload Example:**
```json
{
  "id": "e2a1b3c4-d5e6-7890-abcd-ef1234567890",
  "user_id": "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "email_enabled": true,
  "websocket_enabled": true,
  "database_enabled": true,
  "messages": true,
  "team_invitations": true,
  "project_updates": true,
  "mentions": true,
  "system_announcements": true,
  "email_messages": true,
  "email_team_invitations": true,
  "email_project_updates": true,
  "email_mentions": true,
  "email_system_announcements": true,
  "updated_at": "2026-08-04T10:00:00Z"
}
```

---

### Update Notification Preferences
`PUT /api/v1/notifications/preferences` or `PATCH /api/v1/notifications/preferences`

**Request Payload Example:**
```json
{
  "email_enabled": true,
  "messages": true,
  "email_messages": false,
  "team_invitations": true,
  "project_updates": true,
  "mentions": true,
  "system_announcements": true
}
```

---

## 3. Frontend Settings Component

Location: `frontend/src/routes/_app.settings.notifications.tsx`

Features:
- Master Delivery Channel Switches (Email, Database, Real-time WebSockets)
- Per-category matrix for In-App and Email notifications
- Auto-saves changes per switch toggle with instant toast feedback
- Disables per-category email switches automatically when Master Email is disabled

---

## 4. How preferences are enforced

Storing a preference and honouring it are separate things, and for a long time
only the first half was true (#1247). The mapping from notification type to
category now lives in one place, `app/services/notifications/preferences.py`,
rather than in an `if` chain inside the dispatcher.

### Gated categories

| Notification type | Category | Email column |
|---|---|---|
| `message` | `messages` | `email_messages` |
| `mention` | `mentions` | `email_mentions` |
| `project_invite` | `team_invitations` | `email_team_invitations` |
| `project_update` | `project_updates` | `email_project_updates` |
| `application`, `application_accepted`, `application_rejected` | `project_updates` | `email_project_updates` |
| `builder_flare` | `project_updates` | `email_project_updates` |
| `system`, `welcome`, `ai` | `system_announcements` | `email_system_announcements` |
| `role_change` | `role_changes` | *(none — follows `email_enabled` alone)* |

Two gates, in order: the category switch decides whether the notification is
sent at all, and `email_<category>` decides whether email is one of the
channels that carries it. `email_enabled` sits above both as the master switch.

### Not gated

- `password_reset` and `security_alert` are **always delivered**. A user who
  switches off system announcements should still be told their password was
  reset. Channel switches still apply — turning email off means they see it
  in-app, not that they see it twice.
- `follow` has **no preference column anywhere in the model**, so there is
  nothing to read and it is always delivered. This is a known gap rather than a
  decision; adding a column means a migration and a settings row.

### Legacy column names

`invitations` and `system_alerts` predate the #586 rename to `team_invitations`
and `system_announcements`. Both old and new columns still exist and both
default to `true`, so a row written before the rename that opted out via
`invitations` has `team_invitations = true`.

A category is therefore enabled only if its own column **and** every legacy
alias are enabled — any `false` is a no. Reading only the newer column would
silently re-enable notifications that a user had already opted out of.

### Adding a notification type

Add it to `CATEGORY_BY_TYPE`, or to `ALWAYS_DELIVERED` / `UNGATED` with a
comment saying why. `test_every_notification_type_is_accounted_for` fails on
any `NotificationType` member that appears in none of the three.

`should_deliver()` deliberately fails *open* for an unmapped type — dropping
someone's notifications is a worse way to discover a missing entry than sending
one too many — so that test is the thing standing between a forgotten entry and
a silently ungated category.

---

## 5. Running Unit Tests

```bash
cd backend
./venv/bin/pytest tests/test_notification_preferences.py \
                  tests/test_notification_preference_enforcement.py -v
```

`test_notification_preferences.py` covers storage and serialisation;
`test_notification_preference_enforcement.py` covers whether the dispatcher
acts on what was stored. Every case in the second file asserts both directions
— off means silence, on means delivery — because a change that only checks the
first passes just as well when the answer is silence for everybody.
