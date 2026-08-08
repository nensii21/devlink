from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ErrorDetail(BaseModel):
    error_code: str = Field(
        ...,
        description="Machine-readable error code in UPPER_SNAKE_CASE",
        examples=["PROJECT_NOT_FOUND", "UNAUTHORIZED", "VALIDATION_ERROR"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Project not found.", "Invalid authentication credentials."],
    )
    timestamp: datetime = Field(
        ...,
        description="Time the error occurred (ISO 8601)"
    )
    request_id: str = Field(
        ...,
        description="Unique trace ID for the request"
    )
    details: Optional[Any] = Field(
        None,
        description="Optional additional error context or validation details",
    )

class ErrorResponse(BaseModel):
    error: ErrorDetail
