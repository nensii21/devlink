"""
Standardized API Response Schemas (#1067)

Provides universal generic Pydantic models for consistent API responses across all endpoints:
- StandardResponse[T]: Single resource or payload {"success": true, "data": ..., "message": ...}
- StandardListResponse[T]: Offset-paginated resource list
- StandardCursorResponse[T]: Cursor-paginated resource list
- StandardErrorResponse: Consistent error envelope {"success": false, "error": {"code": ..., "message": ..., "details": ...}}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ResponseMetadata(BaseModel):
    """Metadata attached to standardized API responses."""
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of response generation",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request tracing / correlation identifier",
    )
    version: Optional[str] = Field(
        default="v1",
        description="API version identifier",
    )


class PaginationMetadata(BaseModel):
    """Metadata describing offset-based pagination."""
    model_config = ConfigDict(extra="ignore")

    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    limit: int = Field(..., ge=1, description="Number of items per page")
    total: int = Field(..., ge=0, description="Total count of items across all pages")
    total_pages: int = Field(..., ge=0, description="Total number of pages available")
    has_next: bool = Field(..., description="Whether a subsequent page exists")
    has_prev: bool = Field(..., description="Whether a preceding page exists")


class CursorPaginationMetadata(BaseModel):
    """Metadata describing cursor-based pagination."""
    model_config = ConfigDict(extra="ignore")

    limit: int = Field(..., ge=1, description="Requested page limit")
    next_cursor: Optional[str] = Field(None, description="Opaque cursor for fetching next page")
    prev_cursor: Optional[str] = Field(None, description="Opaque cursor for fetching previous page")
    has_more: bool = Field(..., description="Whether more records exist after this cursor")


class StandardResponse(BaseModel, Generic[T]):
    """Standard success response envelope for single objects or operations."""
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(True, description="Indicates operation success")
    data: Optional[T] = Field(default=None, description="Response payload data")
    message: Optional[str] = Field(default=None, description="Optional human-readable informational message")
    meta: Optional[ResponseMetadata] = Field(
        default_factory=ResponseMetadata,
        description="Response execution metadata",
    )


class StandardListResponse(BaseModel, Generic[T]):
    """Standard success response envelope for offset-paginated lists."""
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(True, description="Indicates operation success")
    data: List[T] = Field(default_factory=list, description="Array of item objects")
    pagination: Optional[PaginationMetadata] = Field(default=None, description="Pagination metadata")
    message: Optional[str] = Field(default=None, description="Optional human-readable informational message")
    meta: Optional[ResponseMetadata] = Field(
        default_factory=ResponseMetadata,
        description="Response execution metadata",
    )


class StandardCursorResponse(BaseModel, Generic[T]):
    """Standard success response envelope for cursor-paginated lists."""
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(True, description="Indicates operation success")
    data: List[T] = Field(default_factory=list, description="Array of item objects")
    cursor: Optional[CursorPaginationMetadata] = Field(default=None, description="Cursor pagination metadata")
    message: Optional[str] = Field(default=None, description="Optional human-readable informational message")
    meta: Optional[ResponseMetadata] = Field(
        default_factory=ResponseMetadata,
        description="Response execution metadata",
    )


class StandardErrorItem(BaseModel):
    """Details describing an API error condition."""
    model_config = ConfigDict(extra="ignore")

    code: str = Field(
        ...,
        description="Machine-readable UPPER_SNAKE_CASE error code",
        examples=["NOT_FOUND", "VALIDATION_ERROR", "UNAUTHORIZED", "RATE_LIMIT_EXCEEDED"],
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of the error",
        examples=["Project not found.", "Invalid authentication credentials."],
    )
    details: Optional[Union[List[Dict[str, Any]], Dict[str, Any], List[Any], str]] = Field(
        default=None,
        description="Detailed contextual information or per-field validation error list",
    )
    field: Optional[str] = Field(
        default=None,
        description="Specific input parameter or body field associated with error",
    )


class StandardErrorResponse(BaseModel):
    """Standard error response envelope returned on 4xx/5xx responses."""
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(False, description="Always false for error responses")
    error: StandardErrorItem = Field(..., description="Error payload details")
    meta: Optional[ResponseMetadata] = Field(
        default_factory=ResponseMetadata,
        description="Response execution metadata",
    )


# ------------------------------------------------------------------
# Response Builder Helpers
# ------------------------------------------------------------------

def success_response(
    data: Optional[T] = None,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
) -> StandardResponse[T]:
    """Helper to construct a StandardResponse object."""
    meta = ResponseMetadata(request_id=request_id) if request_id else ResponseMetadata()
    return StandardResponse(success=True, data=data, message=message, meta=meta)


def paginated_response(
    data: List[T],
    page: int,
    limit: int,
    total: int,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
) -> StandardListResponse[T]:
    """Helper to construct a StandardListResponse with calculated pagination metadata."""
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    pagination = PaginationMetadata(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    meta = ResponseMetadata(request_id=request_id) if request_id else ResponseMetadata()
    return StandardListResponse(
        success=True,
        data=data,
        pagination=pagination,
        message=message,
        meta=meta,
    )


def cursor_response(
    data: List[T],
    limit: int,
    next_cursor: Optional[str] = None,
    prev_cursor: Optional[str] = None,
    has_more: bool = False,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
) -> StandardCursorResponse[T]:
    """Helper to construct a StandardCursorResponse with cursor metadata."""
    cursor = CursorPaginationMetadata(
        limit=limit,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
        has_more=has_more,
    )
    meta = ResponseMetadata(request_id=request_id) if request_id else ResponseMetadata()
    return StandardCursorResponse(
        success=True,
        data=data,
        cursor=cursor,
        message=message,
        meta=meta,
    )


def error_response(
    code: str,
    message: str,
    details: Optional[Any] = None,
    field: Optional[str] = None,
    request_id: Optional[str] = None,
) -> StandardErrorResponse:
    """Helper to construct a StandardErrorResponse object."""
    meta = ResponseMetadata(request_id=request_id) if request_id else ResponseMetadata()
    error_item = StandardErrorItem(
        code=code,
        message=message,
        details=details,
        field=field,
    )
    return StandardErrorResponse(
        success=False,
        error=error_item,
        meta=meta,
    )
