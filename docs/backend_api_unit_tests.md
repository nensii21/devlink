# Backend API Unit Tests Documentation (#388)

Comprehensive unit test suite for backend API endpoints using Pytest, covering happy paths, negative error paths, security authorization paths (401/403/404/422), duplicate operation prevention, and cross-user resource protection.

---

## Technical Test Coverage & HTTP Status Code Matrix

| Feature / Domain | Test Suite | Happy Paths | Negative & Authorization Paths Covered | Status Codes Asserted |
|---|---|---|---|---|
| **Authentication** | `tests/test_auth.py` | Signup, Login, Me, Token Refresh, Password Reset, Resend Verification | Invalid Credentials (`401`), Refresh Invalid Token (`401`), Wrong Current Password (`401`), Duplicate Email Registration (`409`), Missing Fields / Validation (`422`) | `200`, `201`, `401`, `409`, `422` |
| **User Profiles** | `tests/test_users.py` | Get Me, Get Profile, Update Profile, List Users, User Search, Activate/Deactivate/Verify User | Unauthenticated Get Me (`401`), Unauthenticated Update Me (`401`), Non-existent User ID (`404`), Invalid Website URL Payload (`422`), Duplicate Username / Email (`409`) | `200`, `401`, `404`, `409`, `422` |
| **Projects** | `tests/test_projects.py` | Create Project, Get Project, List Projects, Update Details, Status Transitions, Star/Bookmark, Invites | Unauthenticated Project Creation (`401`), Non-owner Update Attempt (`403`), Non-owner Delete Attempt (`403`), Non-existent Project (`404`), Invalid/Empty Title (`422`), Duplicate Invite (`400`) | `200`, `201`, `204`, `400`, `401`, `403`, `404`, `422` |
| **Applications** | `tests/test_applications.py` | Create Application, Get Application, My Applications, Project Applications, Accept/Reject, Withdraw, Delete | Unauthenticated Application (`401`), Non-owner Accept Attempt (`403`), Non-applicant Withdraw Attempt (`403`), Non-applicant Delete Attempt (`403`), Application Not Found (`404`), Missing Project ID (`422`) | `200`, `201`, `204`, `401`, `403`, `404`, `422` |
| **Notifications** | `tests/test_notifications.py` | Create Notification, Get Notification, List Notifications, Unread Count, Mark Read, Mark All Read, Delete | Unauthenticated Access (`401`), Non-recipient Delete Attempt (`403`), Notification Not Found (`404`), Mark Read Non-existent (`404`) | `200`, `201`, `204`, `401`, `403`, `404` |

---

## Execution Command

```bash
cd backend && ./venv/bin/python -m pytest tests/test_auth.py tests/test_users.py tests/test_projects.py tests/test_applications.py tests/test_notifications.py -v
```

**Total Suite Verification**: **94 passed out of 94 tests (100% SUCCESS)** ✅
