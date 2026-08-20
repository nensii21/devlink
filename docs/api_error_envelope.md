# API error envelope

Every error response from the backend has the same shape, whatever produced it —
a route raising `HTTPException`, a Pydantic validation failure, a rate limit, a
duplicate key, or an unhandled exception.

```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "error_code": "PROJECT_NOT_FOUND",
    "message": "Project not found.",
    "timestamp": "2026-08-20T15:32:23.934285+00:00",
    "request_id": "eb13279e-d0b9-48e9-94ef-ea1612da2d11",
    "details": null
  },
  "detail": "Project not found."
}
```

## Fields

| Field | Purpose |
|---|---|
| `error.code` | **Branch on this.** `UPPER_SNAKE_CASE`, stable across releases. |
| `error.error_code` | Deprecated alias for `code`, always the same value. See below. |
| `error.message` | For humans. May be reworded at any time — do not match on it. |
| `error.timestamp` | UTC, ISO 8601, timezone-aware. |
| `error.request_id` | Correlates with the server log line. Quote it in bug reports. |
| `error.details` | Present only when there is something structured to add. Shape depends on `code`. |
| `detail` | Mirror of `error.message`, for callers written against plain FastAPI. |

## `error_code` is deprecated

The envelope shipped emitting `error_code` while the rest of the codebase — the
input side of `http_exception_handler`, the docstrings, and the tests — used
`code`. `code` is the canonical spelling. `error_code` is still sent, carrying
the identical value, so that anything that started reading it does not break;
it will be removed in a future release. Read `code`.

## Where `code` comes from

A route can set it explicitly by raising with a structured detail:

```python
raise HTTPException(
    status_code=403,
    detail={
        "code": "PROJECT_FORBIDDEN",
        "message": "You cannot touch this project.",
        "details": {"project_id": str(project.id)},
    },
)
```

Or by raising one of the typed exceptions in `app/core/exceptions.py`, which
carry their own status code, code and details:

```python
raise ValidationException(
    message="That slug is already taken.",
    code="SLUG_TAKEN",
    details={"field": "slug"},
)
```

If a route raises with a plain string detail, the code is derived from the
message — `"Project not found."` becomes `PROJECT_NOT_FOUND` — falling back to
a per-status default (`NOT_FOUND`, `CONFLICT`, …) when the message is empty or
too long to be a useful identifier. Derived codes are convenient but not
stable; anything a client needs to branch on should be set explicitly.

## What never appears in an error response

Error bodies are returned to unauthenticated callers, so the handlers keep
server-side detail out of them:

- database driver messages, which can contain the statement and its bound
  parameters, and the host it failed to reach;
- unique-constraint text, which names the physical index **and echoes the
  value that collided** — a duplicate-email 409 returns
  `{"duplicate_field": "email"}`, never the address already on the account;
- exception messages and tracebacks from unhandled errors.

All of that is logged with the `request_id` from the response instead.

## Handlers

Registered in `app/main.py`; Starlette picks the most specific one for the
exception's MRO, so the order in that file is documentation rather than
precedence.

| Exception | Handler | Status |
|---|---|---|
| `HTTPException` / Starlette `HTTPException` | `http_exception_handler` | as raised |
| `RequestValidationError` | `validation_exception_handler` | 422 |
| `RateLimitExceeded` | `rate_limit_exception_handler` | 429 (+ `Retry-After`) |
| `AppException` and subclasses | `app_exception_handler` | as raised |
| `IntegrityError` | `integrity_error_handler` | 409 |
| `SQLAlchemyError` | `sqlalchemy_error_handler` | 500 |
| anything else | `global_exception_handler` | 500 |

## Tests

- `backend/tests/test_error_envelope.py` — the shape of the envelope itself,
  parametrised across every handler.
- `backend/tests/test_error_responses.py` — per-handler codes and messages.
- `backend/tests/test_global_error_handler.py` — the handlers as wired into the
  real app.
