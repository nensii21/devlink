# Built-in CI/CD Pipeline Orchestrator Specification

## 1. Executive Summary
The Built-in CI/CD Pipeline Orchestrator brings native continuous integration and deployment automation directly to DevLink repositories. It enables repository maintainers to define lightweight build, lint, test, and release jobs that execute within secure, ephemeral sandboxes.

---

## 2. Core Capabilities
- **YAML Pipeline Parser**: Decodes declarative pipeline specs (`.devlink-ci.yml`) into directed acyclic dependency graphs (DAGs).
- **Matrix Job Execution**: Allows concurrent job matrix expansions across language runtimes and environments.
- **Live Output Streaming**: Publishes terminal stdout/stderr chunks to subscribed frontend clients over WebSocket connections.
- **Status Reporting & Commit Badging**: Generates commit status checks, badges, and automated PR review feedback.

---

## 3. Architecture & Execution Lifecycle
1. **Trigger Phase**: Ingests Git webhooks (push, pull_request, manual_dispatch) and validates branch protection filters.
2. **Orchestration Phase**:
   - Resolves step dependencies and environment secrets.
   - Instantiates `PipelineJob` and initializes step queues.
3. **Execution Phase**:
   - Workers claim jobs from Redis task queues.
   - Micro-VM / OCI containers spawn with isolated network namespaces and timeout enforcement.
4. **Teardown & Archival Phase**:
   - Collects exit codes, execution duration, and test artifact summaries.
   - Broadcasts terminal state (`PASSED`, `FAILED`, `CANCELLED`).

---

## 4. Pipeline Configuration Schema (`.devlink-ci.yml`)

```yaml
version: "1.0"
name: Core Pipeline

on:
  push:
    branches: [main, release/*]
  pull_request:
    branches: [main]

jobs:
  lint-and-typecheck:
    name: Lint & Typecheck
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        run: devlink-checkout
      - name: Run Linter
        run: npm run lint
      - name: Typecheck
        run: npx tsc --noEmit

  test-suite:
    name: Run Unit Tests
    needs: [lint-and-typecheck]
    steps:
      - name: Backend Pytest
        run: pytest backend/app/tests/ -v
```

---

## 5. API Endpoints

### 5.1 Trigger New Pipeline Run
- **Endpoint**: `POST /api/v1/ci/pipelines/{project_id}/trigger`
- **Authentication**: Bearer JWT (Maintainer/Contributor)
- **Request Body**:
```json
{
  "commit_sha": "7a8b9c0d1e2f",
  "branch": "feat/my-feature",
  "environment_variables": {
    "NODE_ENV": "test"
  }
}
```

### 5.2 Get Pipeline Job Status
- **Endpoint**: `GET /api/v1/ci/jobs/{job_id}`
- **Response**:
```json
{
  "job_id": "job_proj_101_1724500000",
  "project_id": "proj_101",
  "commit_sha": "7a8b9c0d1e2f",
  "status": "passed",
  "duration_seconds": 45.2,
  "steps": [
    { "name": "lint", "status": "passed", "exit_code": 0, "duration": 8.1 },
    { "name": "test", "status": "passed", "exit_code": 0, "duration": 37.1 }
  ]
}
```

---

## 6. Sandboxing, Isolation & Security Policies
- **Resource Constraints**: Default quota limits (2 vCPU, 4GB RAM, 15-minute runtime ceiling).
- **Secret Masking**: Environment secrets are masked with asterisks in stdout logs.
- **Network Egress Controls**: Outbound traffic can be scoped to approved package repositories.
