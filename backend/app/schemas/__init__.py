"""
Pydantic schemas package with standardized response envelopes (#1067).
"""

from app.schemas.response import (
    CursorPaginationMetadata,
    PaginationMetadata,
    ResponseMetadata,
    StandardCursorResponse,
    StandardErrorItem,
    StandardErrorResponse,
    StandardListResponse,
    StandardResponse,
    cursor_response,
    error_response,
    paginated_response,
    success_response,
)

__all__ = [
    "ResponseMetadata",
    "PaginationMetadata",
    "CursorPaginationMetadata",
    "StandardResponse",
    "StandardListResponse",
    "StandardCursorResponse",
    "StandardErrorItem",
    "StandardErrorResponse",
    "success_response",
    "paginated_response",
    "cursor_response",
    "error_response",
]
