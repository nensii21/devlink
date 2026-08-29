# Advanced Access Control & Custom Roles (RBAC) Specification

## 1. Executive Summary
DevLink's Role-Based Access Control (RBAC) engine delivers fine-grained authorization policies across projects, teams, organizations, and administrative workflows. It empowers project maintainers to create custom roles with bespoke permission matrices and inheritance hierarchies.

---

## 2. Core Authorization Architecture
1. **Hierarchical Scopes**:
   - **System Tier**: Global site administration, user moderation, telemetry inspection.
   - **Organization Tier**: Billing management, organization member directory, shared API key provisioning.
   - **Project Tier**: Code merging, issue management, release publishing, environment secret configuration.
2. **Role Inheritance Engine**: Allows custom roles to inherit base capabilities from standard archetypes (`viewer`, `contributor`, `maintainer`) while appending specific privileges.
3. **High-Performance Permission Cache**: In-memory and Redis-backed bitset evaluation yielding sub-millisecond policy resolution.

---

## 3. Permissions Matrix & Default Roles

| Permission Key | Description | Viewer | Contributor | Maintainer | Admin | Owner |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `project:read` | View project details and code | ✅ | ✅ | ✅ | ✅ | ✅ |
| `code:review` | Submit PR comments and reviews | ❌ | ✅ | ✅ | ✅ | ✅ |
| `code:merge` | Merge pull requests | ❌ | ❌ | ✅ | ✅ | ✅ |
| `member:manage`| Invite or remove team members | ❌ | ❌ | ❌ | ✅ | ✅ |
| `project:admin`| Full administrative privileges | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 4. API Endpoints

### 4.1 Define Custom Role
- **Endpoint**: `POST /api/v1/rbac/projects/{project_id}/roles`
- **Authentication**: Bearer JWT (Project Admin/Owner)
- **Request Body**:
```json
{
  "name": "release_manager",
  "inherits_from": "maintainer",
  "permissions": [
    "release:create",
    "release:publish",
    "deployment:trigger"
  ]
}
```

### 4.2 Evaluate User Permission
- **Endpoint**: `POST /api/v1/rbac/evaluate`
- **Request Body**:
```json
{
  "project_id": "proj_900",
  "user_id": "usr_456",
  "required_permission": "code:merge"
}
```
- **Response**:
```json
{
  "allowed": true,
  "granted_by_role": "maintainer",
  "evaluated_at": "2026-08-27T18:00:00Z"
}
```

---

## 5. Security Policies & Audit Trails
- **Privilege Escalation Prevention**: Non-owners cannot grant permissions exceeding their own role tier.
- **Immutable Owner Protection**: The primary project creator / owner cannot have their `owner` role revoked without explicit project ownership transfer.
- **Audit Logging**: Every permission evaluation failure or role modification triggers an immutable audit log record.

---

## 6. Comprehensive RBAC Integration Patterns & Middleware

```python
from fastapi import Request, HTTPException, Depends
from app.services.rbac_service import rbac_service

async def require_permission(permission: str):
    async def dependency(request: Request):
        project_id = request.path_params.get("project_id", "")
        user_role = getattr(request.state, "user_role", "viewer")
        user_id = getattr(request.state, "user_id", "anonymous")
        
        if not rbac_service.has_permission(project_id, user_role, permission, user_id):
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: User role '{user_role}' lacks required permission '{permission}'."
            )
        return True
    return dependency
```

### 6.1 Permission Resolution Sequence Diagram
```
Client             FastAPI Route             RBAC Service             Redis Cache
  |                      |                         |                       |
  |--- [HTTP Request] -->|                         |                       |
  |                      |-- [has_permission()] -->|                       |
  |                      |                         |-- [Get Bitset Perms]->|
  |                      |                         |<-- [Perms Bitset]-----|
  |                      |<-- [Granted: True/False]|                       |
  |<-- [200 OK / 403] ---|                         |                       |
```

### 6.2 Edge Cases and Error Handling
1. **Dynamic Project Deletion**: When a project is marked deleted, all custom role records are soft-deleted and evicted from the Redis cache.
2. **Circular Role Inheritance**: Role inheritance validation detects and rejects circular dependency chains at creation time.
3. **Role Downgrades & Session Invalidation**: When a user's role is demoted, active JWT session claims are revoked via token blacklist.
