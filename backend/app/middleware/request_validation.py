from __future__ import annotations
from datetime import datetime, timezone
from app.core.tracing import get_request_id

import json
from typing import Any, Callable, Dict, List, Optional
from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Centralized middleware to format and standardize request validation errors
    across body, query params, and path parameters for all backend API endpoints.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except RequestValidationError as exc:
            return format_validation_error_response(exc.errors())
        except ValidationError as exc:
            return format_validation_error_response(exc.errors())

def format_validation_error_response(errors: List[Dict[str, Any]]) -> JSONResponse:
    formatted_details = []

    for err in errors:
        loc_parts = [str(part) for part in err.get("loc", []) if str(part) != "body"]
        field_name = ".".join(loc_parts) if loc_parts else "request"

        formatted_details.append({
            "field": field_name,
            "message": err.get("msg", "Invalid value provided"),
            "type": err.get("type", "value_error"),
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": get_request_id() or "unknown",
                "details": formatted_details,
            }
        },
    )

# Reusable Validation Utility Functions
def validate_query_param(value: Any, param_name: str, min_val: Optional[int] = None, max_val: Optional[int] = None):
    """Utility to validate individual query parameter boundaries."""
    if value is not None:
        if min_val is not None and value < min_val:
            raise RequestValidationError([
                {"loc": ["query", param_name], "msg": f"Value must be >= {min_val}", "type": "greater_than_equal"}
            ])
        if max_val is not None and value > max_val:
            raise RequestValidationError([
                {"loc": ["query", param_name], "msg": f"Value must be <= {max_val}", "type": "less_than_equal"}
            ])


def validate_path_param(value: str, param_name: str, pattern: Optional[str] = None):
    """Utility to validate route path parameter format."""
    if not value or not value.strip():
        raise RequestValidationError([
            {"loc": ["path", param_name], "msg": f"Path parameter {param_name} cannot be empty", "type": "value_error.missing"}
        ])
