"""
Cursor Pagination Pydantic Schemas (#1068)
"""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class CursorPaginationParams(BaseModel):
    """Query parameters for cursor-based pagination with backward-compatible offset fallback."""
    model_config = ConfigDict(extra="ignore")

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of records to return per page",
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Opaque base64 cursor token pointing to page boundary",
    )
    page: Optional[int] = Field(
        default=None,
        ge=1,
        description="Legacy 1-indexed page number (triggers offset pagination fallback)",
    )
    direction: Optional[str] = Field(
        default="next",
        pattern="^(next|prev)$",
        description="Pagination direction: 'next' for forward, 'prev' for backward",
    )


class CursorPaginationResponse(BaseModel, Generic[T]):
    """Standardized response schema for cursor-paginated endpoints."""
    model_config = ConfigDict(extra="ignore")

    items: List[T] = Field(default_factory=list, description="Array of paginated items")
    limit: int = Field(..., description="Requested page size limit")
    next_cursor: Optional[str] = Field(default=None, description="Opaque token for fetching next page")
    prev_cursor: Optional[str] = Field(default=None, description="Opaque token for fetching previous page")
    has_more: bool = Field(default=False, description="True if subsequent records exist")
    has_prev: bool = Field(default=False, description="True if preceding records exist")
    total: Optional[int] = Field(default=None, description="Total record count (optional)")


CursorPageResponse = CursorPaginationResponse
