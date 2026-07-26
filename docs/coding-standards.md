# DevLink Coding Standards & Best Practices

This document establishes the coding conventions, API guidelines, error handling rules, logging practices, and testing standards for all code written in DevLink.

---

## 1. Naming Conventions

### Frontend (TypeScript / React)

* **Files & Directories**:
  * React Components: `PascalCase.tsx` (e.g. `BioCard.tsx`, `MatchBreakdown.tsx`)
  * Custom Hooks: `camelCase.ts` starting with `use` (e.g. `useTeamMatch.ts`, `useDebounce.ts`)
  * Utility Files / Services: `camelCase.ts` (e.g. `profile.ts`, `commandSearchUtils.ts`)
  * Directories: `kebab-case` or `camelCase` matching module purpose (e.g. `components/command-palette`, `lib/validation`)

* **Variables & Functions**:
  * Variables, parameters, and function names: `camelCase` (e.g. `calculateScore`, `userProfile`)
  * Interfaces, Types, Enums: `PascalCase` (e.g. `UserProfileProps`, `TeamMatchScore`)
  * Constants: `UPPER_SNAKE_CASE` (e.g. `MAX_MATCH_RETRY_COUNT`, `DEFAULT_PAGE_SIZE`)

### Backend (Python / FastAPI)

* **Files & Directories**:
  * Python modules/files: `snake_case.py` (e.g. `auth_service.py`, `user_models.py`)
  * Directory / Package names: `snake_case` (e.g. `app/api/v1`)

* **Classes & Functions**:
  * Classes / Pydantic Models / ORM Models: `PascalCase` (e.g. `UserResponse`, `ProjectModel`)
  * Functions, methods, variables: `snake_case` (e.g. `get_user_by_id`, `verify_password`)
  * Constants: `UPPER_SNAKE_CASE` (e.g. `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`)

---

## 2. API Standards

All DevLink REST endpoints must adhere to standard JSON REST design principles.

### Endpoint Structure
* Base API URL: `/api/v1`
* Nouns for Resources: Use plural nouns for resources (e.g. `/api/v1/projects`, `/api/v1/users`).

### HTTP Methods & Usage
* `GET`: Retrieve resource data. Read-only without side effects.
* `POST`: Create a new resource or perform stateful actions (e.g. login).
* `PUT`: Replace an existing resource completely.
* `PATCH`: Partially update an existing resource.
* `DELETE`: Remove a resource.

### JSON Response Format
Standardize responses for consistency across client API modules.

**Success Response**:
```json
{
  "success": true,
  "data": {
    "id": "usr_12345",
    "username": "johndoe",
    "email": "john@example.com"
  },
  "message": "User fetched successfully"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "The requested user ID does not exist.",
    "details": null
  }
}
```

---

## 3. Error Handling

### Backend Error Handling (FastAPI)
* Never swallow exceptions silently without logging.
* Use FastAPI's `HTTPException` with explicit HTTP status codes.
* Validate all incoming request payloads using Pydantic models.

```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

def get_project_by_id(project_id: str, db: Session):
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found."
            )
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred on the server."
        )
```

### Frontend Error Handling (React)
* Wrap UI sections in React Error Boundaries to prevent whole-app crashes.
* Use asynchronous try-catch blocks in service calls or handle via React Query error state callbacks.
* Present user-friendly toast error messages rather than raw stack traces.

---

## 4. Logging Guidelines

### Backend Logging Standards
* Do NOT use raw `print()` statements in production code. Use standard Python `logging`.
* Log levels:
  * `DEBUG`: Detailed diagnostics for local debugging.
  * `INFO`: General operational events (e.g. server start, user login, background job dispatch).
  * `WARNING`: Non-critical anomalies (e.g. deprecated API call, retry attempt).
  * `ERROR`: Runtime exceptions affecting user requests.
  * `CRITICAL`: Failures requiring immediate administrator action (e.g. database connectivity loss).

```python
import logging

logger = logging.getLogger("devlink")

logger.info("User %s successfully logged in", user_id)
logger.warning("Rate limit threshold approached for IP %s", client_ip)
logger.error("Failed to sync GitHub profile for user %s: %s", user_id, str(err))
```

---

## 5. Testing Guidelines

### Principles
* Write unit tests for business logic, algorithm calculations, and service helper utilities.
* Maintain clean test isolation—mock external network requests (GitHub API, OpenAI API).
* Use meaningful test function names describing expected outcomes (`test_calculate_match_score_with_empty_skills_returns_zero`).

### Frontend Tests (Vitest / React Testing Library)
* Target component rendering, user interactions, and custom hooks.

```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BioCard } from './BioCard';

describe('BioCard Component', () => {
  it('renders user bio text correctly', () => {
    render(<BioCard bio="Full-stack open source builder." />);
    expect(screen.getByText('Full-stack open source builder.')).toBeInTheDocument();
  });
});
```

### Backend Tests (Pytest / FastAPI TestClient)
* Test API routes, HTTP status codes, and ORM query results.

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_healthcheck():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

---

## Related Documentation
* [Architecture Documentation](architecture.md)
* [Development Guide](development.md)
* [Deployment Guide](deployment.md)
