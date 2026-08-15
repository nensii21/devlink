import base64
import json
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    limit: int = Field(
        default=20, ge=1, le=100, description="Number of items to return"
    )
    cursor: Optional[str] = Field(default=None, description="Cursor for pagination")
    offset: Optional[int] = Field(
        default=0, ge=0, description="Offset for offset-based pagination"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_next: bool = False
    has_prev: bool = False

    class Config:
        arbitrary_types_allowed = True


def encode_cursor(data: dict) -> str:
    """Encode dictionary into a URL-safe base64 cursor string."""
    json_str = json.dumps(data)
    return base64.urlsafe_b64encode(json_str.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor_str: str) -> Optional[dict]:
    """Decode URL-safe base64 cursor string into a dictionary."""
    if not cursor_str:
        return None
    try:
        json_bytes = base64.urlsafe_b64decode(cursor_str.encode("utf-8"))
        return json.loads(json_bytes.decode("utf-8"))
    except Exception:
        return None
