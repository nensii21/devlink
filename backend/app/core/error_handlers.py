from __future__ import annotations

import logging
import re
from typing import Any, Dict, Final
from datetime import datetime, timezone
from app.core.tracing import get_request_id

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import AppException

logger = logging.getLogger("devlink")

DEFAULT_STATUS_CODES: Dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    408: "REQUEST_TIMEOUT",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_SERVER_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}


def generate_error_code(status_code: int, message: str | None) -> str:
    """
    Generate a machine-readable UPPER_SNAKE_CASE code from message or status code.
    Example: "Project not found." -> "PROJECT_NOT_FOUND"
    Example: "Invalid email or password." -> "INVALID_EMAIL_OR_PASSWORD"
    """
    if not message or not isinstance(message, str):
        return DEFAULT_STATUS_CODES.get(status_code, "ERROR")

    cleaned = re.sub(r"[^a-zA-Z0-9\s_]", "", message).strip()
    if not cleaned:
        return DEFAULT_STATUS_CODES.get(status_code, "ERROR")

    words = cleaned.split()
    if len(words) > 6:
        return "_".join(words[:5]).upper()

    return "_".join(words).upper()


#: The key clients are meant to branch on.
#:
#: This used to be spelled two ways at once. `format_error_response` emitted
#: `error_code`, while the docstring example, the *input* side of
#: `http_exception_handler` (`exc.detail.get("code")`) and every test written
#: for the envelope used `code`. A route would raise
#: `HTTPException(detail={"code": "PROJECT_NOT_FOUND"})` and the caller would
#: receive `{"error": {"error_code": "PROJECT_NOT_FOUND"}}`: write `code`,
#: read `error_code`.
ERROR_CODE_KEY: Final[str] = "code"

#: The spelling that shipped by accident, kept as an alias.
#:
#: Nothing in this repository reads it, but the responses have been going out
#: with it for a while and something outside may have started depending on it.
#: Removing it in the same change that fixes the contract would trade one
#: silent break for another, so it stays -- carrying the same value -- until a
#: release that says it is going.
DEPRECATED_ERROR_CODE_KEY: Final[str] = "error_code"


def format_error_response(
    code: str,
    message: str,
    details: Any = None,
    request: Request | None = None,
) -> Dict[str, Any]:
    """
    Build standardized JSON response payload.

    The envelope is::

        {
          "error": {
            "code": "PROJECT_NOT_FOUND",
            "error_code": "PROJECT_NOT_FOUND",   # deprecated alias
            "message": "Project not found.",
            "timestamp": "2026-08-20T15:32:23.934285+00:00",
            "request_id": "eb13279e-d0b9-48e9-94ef-ea1612da2d11",
            "details": ...                       # only when there are any
          },
          "detail": "Project not found."         # FastAPI compatibility
        }

    `code` is machine-readable and stable; `message` is for humans and may be
    reworded; `detail` exists so callers written against plain FastAPI keep
    working.
    """
    request_id = getattr(request.state, "request_id", None) if request else None
    request_id = request_id or get_request_id() or "unknown"

    error_dict: Dict[str, Any] = {
        ERROR_CODE_KEY: code,
        DEPRECATED_ERROR_CODE_KEY: code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }
    if details is not None:
        error_dict["details"] = details

    return {"error": error_dict}


async def http_exception_handler(
    request: Request,
    exc: HTTPException | StarletteHTTPException,
) -> JSONResponse:
    """
    Handle HTTP exceptions raised in route handlers.
    """
    status_code = exc.status_code

    if isinstance(exc.detail, dict):
        code = exc.detail.get("code") or DEFAULT_STATUS_CODES.get(status_code, "ERROR")
        message = (
            exc.detail.get("message")
            or exc.detail.get("detail")
            or "An error occurred."
        )
        details = exc.detail.get("details")
    elif isinstance(exc.detail, str):
        message = exc.detail
        code = generate_error_code(status_code, message)
        details = None
    else:
        message = str(exc.detail) if exc.detail else "An error occurred."
        code = DEFAULT_STATUS_CODES.get(status_code, "ERROR")
        details = exc.detail

    payload = format_error_response(code=code, message=message, details=details)
    payload["detail"] = message
    return JSONResponse(status_code=status_code, content=payload)


def _jsonable_validation_errors(errors: list[Any]) -> list[Dict[str, Any]]:
    """Make `RequestValidationError.errors()` safe to serialise.

    When a Pydantic `field_validator` rejects a value by raising `ValueError`,
    Pydantic v2 puts the exception *object* in the entry's `ctx`:

        {'type': 'value_error', 'loc': (...), 'msg': '...',
         'ctx': {'error': ValueError('...')}}

    `JSONResponse` cannot encode that, so the handler blew up with a TypeError
    while rendering the response -- turning what should have been a clean 422
    into a crash. It affects every endpoint whose schema uses a custom
    validator; `schemas/skill.py` and `schemas/user.py` already have some.

    `msg` already carries the human-readable text, so the exception object adds
    nothing. Anything non-primitive in `ctx` is stringified rather than dropped,
    which keeps the detail useful without assuming what it holds.
    """
    cleaned: list[Dict[str, Any]] = []

    for error in errors:
        entry = dict(error)

        # loc is a tuple, and may contain ints for list indices.
        if "loc" in entry:
            entry["loc"] = [str(part) for part in entry["loc"]]

        ctx = entry.get("ctx")
        if isinstance(ctx, dict):
            entry["ctx"] = {
                key: (
                    value
                    if isinstance(value, (str, int, float, bool, type(None)))
                    else str(value)
                )
                for key, value in ctx.items()
            }

        # The offending input can be an arbitrary object on a nested model.
        if "input" in entry and not isinstance(
            entry["input"], (str, int, float, bool, type(None), list, dict)
        ):
            entry["input"] = str(entry["input"])

        # Pydantic includes a docs link that is a plain string, but drop
        # anything else unexpected rather than risk the same crash.
        cleaned.append(
            {
                key: value
                for key, value in entry.items()
                if key in {"type", "loc", "msg", "ctx", "input", "url"}
            }
        )

    return cleaned


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic / FastAPI request validation errors (422).
    """
    errors = _jsonable_validation_errors(exc.errors())
    message = "Request validation failed."
    if errors:
        first_err = errors[0]
        loc = " -> ".join(str(l) for l in first_err.get("loc", []) if l != "body")
        msg = first_err.get("msg", "Invalid value")
        if loc:
            message = f"Validation error: {loc}: {msg}"
        else:
            message = f"Validation error: {msg}"

    payload = format_error_response(
        code="VALIDATION_ERROR",
        message=message,
        details=errors,
        request=request,
    )
    payload["detail"] = message
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload,
    )


async def rate_limit_exception_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """
    Handle SlowAPI rate limit exceeded exceptions (429).
    Enforces HTTP 429 status code and includes Retry-After header (#590).
    """
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is None:
        retry_after = 60

    try:
        retry_after_int = max(1, int(retry_after))
    except (ValueError, TypeError):
        retry_after_int = 60

    headers = {"Retry-After": str(retry_after_int)}

    payload = format_error_response(
        code="RATE_LIMIT_EXCEEDED",
        message="Too many requests. Rate limit exceeded. Please try again later.",
        details={"retry_after_seconds": retry_after_int},
        request=request,
    )
    payload["detail"] = payload["error"]["message"]

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=payload,
        headers=headers,
    )


async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all unhandled exception handler (500).
    """
    logger.exception(f"Unhandled exception during request {request.url.path}: {exc}")
    payload = format_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred.",
        request=request,
    )
    payload["detail"] = payload["error"]["message"]
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload,
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """
    Handle SQLAlchemy IntegrityError (e.g. Unique Constraint Violations) -> 409 Conflict.
    """
    # Extract the error detail from the exception
    detail = str(exc.orig) if exc.orig else str(exc)

    # Generic message, but try to find the specific field if possible
    message = "A record with this information already exists."

    # PostgreSQL duplicate key error usually looks like:
    # duplicate key value violates unique constraint "ix_users_email"
    # DETAIL:  Key (email)=(test@example.com) already exists.
    #
    # `details` used to carry that whole string. It names the physical index,
    # and -- worse -- it echoes the value that collided, so a signup form that
    # hit a duplicate email replied with the email already on the account. The
    # field name is the only part a client can act on, so it is the only part
    # that goes out; the raw text is logged instead.
    duplicate_field: str | None = None

    if "already exists" in detail.lower() or "unique constraint" in detail.lower():
        message = "This record already exists. Please use a unique value."

        # e.g. Key (username)=(admin) already exists.
        match = re.search(r"Key \((.*?)\)=", detail)
        if match:
            duplicate_field = match.group(1)
            message = f"The {duplicate_field} provided is already in use."

    logger.warning("IntegrityError on %s: %s", request.url.path, detail)

    payload = format_error_response(
        code="CONFLICT",
        message=message,
        details={"duplicate_field": duplicate_field} if duplicate_field else None,
        request=request,
    )
    payload["detail"] = message
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=payload,
    )


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """
    Handle the application's own typed exceptions.

    `AppException` and its subclasses (`AuthException`, `DatabaseException`,
    `ValidationException`) each carry the status code, the machine-readable
    code and the details they want returned -- and none of that reached the
    client, because no handler was ever registered for them. They fell through
    to `global_exception_handler` and came back as a flat 500
    `INTERNAL_SERVER_ERROR`, discarding the 401 or 422 the raiser asked for.

    That is why nothing in the codebase raises them: they did not work.
    """
    status_code = getattr(exc, "status_code", None) or status.HTTP_500_INTERNAL_SERVER_ERROR
    message = getattr(exc, "message", None) or str(exc) or "An error occurred."
    code = getattr(exc, "code", None) or DEFAULT_STATUS_CODES.get(status_code, "ERROR")

    # A 5xx is still a server fault even when it is typed, so it is logged with
    # the same weight as an unhandled one. 4xx is the caller's business.
    if status_code >= 500:
        logger.exception("AppException on %s: %s", request.url.path, message)

    payload = format_error_response(
        code=code,
        message=message,
        details=getattr(exc, "details", None),
        request=request,
    )
    payload["detail"] = message
    return JSONResponse(status_code=status_code, content=payload)


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """
    Handle any database error that is not an `IntegrityError` -> 500.

    `IntegrityError` is a subclass of `SQLAlchemyError` and keeps its own
    handler; Starlette resolves handlers along the exception's MRO, so the
    more specific registration still wins.

    The driver's message can contain the failing statement and its bound
    parameters, so it is logged and never returned.
    """
    logger.exception("Database error on %s: %s", request.url.path, exc)

    payload = format_error_response(
        code="DATABASE_ERROR",
        message="A database error occurred. Please try again later.",
        request=request,
    )
    payload["detail"] = payload["error"]["message"]
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload,
    )
