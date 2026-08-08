from __future__ import annotations

import logging
import re
from typing import Any, Dict
from datetime import datetime, timezone
from app.core.tracing import get_request_id

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError

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

def format_error_response(
    code: str,
    message: str,
    details: Any = None,
    request: Request | None = None,
) -> Dict[str, Any]:
    """
    Build standardized JSON response payload.
    """
    request_id = getattr(request.state, "request_id", None) if request else None
    request_id = request_id or get_request_id() or "unknown"

    error_dict: Dict[str, Any] = {
        "error_code": code,
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


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic / FastAPI request validation errors (422).
    """
    errors = exc.errors()
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
    )
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
    )

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
    if "already exists" in detail.lower() or "unique constraint" in detail.lower():
        message = "This record already exists. Please use a unique value."

        # Try to extract the field name from the detail
        # e.g., Key (username)=(admin) already exists.
        match = re.search(r"Key \((.*?)\)=", detail)
        if match:
            field = match.group(1)
            message = f"The {field} provided is already in use."

    payload = format_error_response(
        code="CONFLICT",
        message=message,
        details=detail,
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=payload,
    )
