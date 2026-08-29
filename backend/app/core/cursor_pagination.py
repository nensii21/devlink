"""
Cursor-Based Keyset Pagination Engine (#1068)

Replaces high-overhead offset pagination for high-volume endpoints (Activities, Notifications,
Projects, Users) with stable O(1) keyset cursors:
- Base64 opaque cursor token: timestamp + ID + direction
- Handles deleted records gracefully (boundary condition independent of row existence)
- Bi-directional navigation: next_cursor, prev_cursor, has_more
- Backward compatibility: automatic fallback to offset pagination if `page` or `offset` query parameter is passed
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import uuid
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, Union
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import asc, desc, or_, and_
from sqlalchemy.orm import Query

T = TypeVar("T")


class InvalidCursorError(ValueError):
    """Raised when a cursor cannot be decoded or is malformed."""
    pass


class CursorData(BaseModel):
    """Structured representation of decoded cursor state."""
    model_config = ConfigDict(extra="ignore")

    t: str = Field(..., description="Timestamp ISO string or numeric sort key")
    id: str = Field(..., description="Unique record identifier for tie-breaking")
    d: str = Field(default="next", description="Pagination direction: next | prev")


class CursorPageResponse(BaseModel, Generic[T]):
    """Standard generic model for cursor-paginated responses."""
    model_config = ConfigDict(extra="ignore")

    items: List[T] = Field(default_factory=list, description="Page of records")
    limit: int = Field(..., ge=1, description="Page size limit applied")
    next_cursor: Optional[str] = Field(None, description="Opaque cursor to fetch next page")
    prev_cursor: Optional[str] = Field(None, description="Opaque cursor to fetch previous page")
    has_more: bool = Field(False, description="Whether more items exist in forward direction")
    has_prev: bool = Field(False, description="Whether items exist in backward direction")
    total: Optional[int] = Field(None, description="Optional total count when requested")


def encode_cursor(
    sort_value: Union[dt.datetime, dt.date, int, float, str],
    record_id: Union[uuid.UUID, int, str],
    direction: str = "next",
) -> str:
    """
    Encodes sort key and unique ID into an opaque URL-safe base64 cursor.
    """
    if isinstance(sort_value, (dt.datetime, dt.date)):
        t_str = sort_value.isoformat()
    else:
        t_str = str(sort_value)

    id_str = str(record_id)
    payload = {"t": t_str, "id": id_str, "d": direction}
    raw_json = json.dumps(payload, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw_json.encode("utf-8")).decode("utf-8").rstrip("=")


def decode_cursor(cursor_str: Optional[str]) -> Optional[CursorData]:
    """
    Decodes an opaque base64 cursor token into structured CursorData.
    Returns None if cursor_str is empty.
    Raises InvalidCursorError if cursor is malformed.
    """
    if not cursor_str:
        return None

    try:
        # Add padding back if stripped
        padded = cursor_str + "=" * (-len(cursor_str) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded.encode("utf-8"))
        payload = json.loads(decoded_bytes.decode("utf-8"))
        if not isinstance(payload, dict) or "t" not in payload or "id" not in payload:
            raise InvalidCursorError("Missing required cursor keys ('t', 'id')")
        return CursorData(
            t=str(payload["t"]),
            id=str(payload["id"]),
            d=str(payload.get("d", "next")),
        )
    except Exception as exc:
        raise InvalidCursorError(f"Invalid cursor format: {exc}") from exc


def parse_cursor_sort_value(t_str: str) -> Any:
    """Parses cursor sort value string back into native python type."""
    try:
        cleaned = t_str.replace("Z", "+00:00")
        parsed_dt = dt.datetime.fromisoformat(cleaned)
        # If naive in db comparison, return naive dt if no tz specified
        if parsed_dt.tzinfo is None:
            return parsed_dt
        return parsed_dt
    except Exception:
        try:
            if "." in t_str:
                return float(t_str)
            return int(t_str)
        except Exception:
            return t_str


def apply_cursor_pagination(
    query: Query,
    model_class: Any,
    limit: int = 20,
    cursor: Optional[str] = None,
    page: Optional[int] = None,
    order: str = "desc",
    sort_column_name: str = "created_at",
    id_column_name: str = "id",
) -> CursorPageResponse[Any]:
    """
    Applies keyset or fallback offset pagination to a SQLAlchemy Query.
    
    1. If `page` is provided (page > 0), gracefully falls back to offset pagination.
    2. Otherwise applies O(1) indexed keyset filtering on (sort_col, id_col).
    3. Fetches `limit + 1` rows to accurately determine `has_more` without extra COUNT query.
    4. Handles deleted records seamlessly since boundary is strictly value-based.
    """
    sort_col = getattr(model_class, sort_column_name)
    id_col = getattr(model_class, id_column_name)

    # 1. Fallback to offset pagination if legacy `page` param was passed
    if page is not None and page > 0:
        offset = (page - 1) * limit
        ordered_query = query.order_by(
            desc(sort_col) if order == "desc" else asc(sort_col),
            desc(id_col) if order == "desc" else asc(id_col),
        )
        total = query.count()
        items = ordered_query.offset(offset).limit(limit + 1).all()
        has_more = len(items) > limit
        page_items = items[:limit]

        next_cur = None
        if has_more and page_items:
            last = page_items[-1]
            next_cur = encode_cursor(
                getattr(last, sort_column_name),
                getattr(last, id_column_name),
                "next",
            )

        prev_cur = None
        if page > 1 and page_items:
            first = page_items[0]
            prev_cur = encode_cursor(
                getattr(first, sort_column_name),
                getattr(first, id_column_name),
                "prev",
            )

        return CursorPageResponse(
            items=page_items,
            limit=limit,
            next_cursor=next_cur,
            prev_cursor=prev_cur,
            has_more=has_more,
            has_prev=page > 1,
            total=total,
        )

    # 2. Keyset (Cursor-Based) Pagination
    decoded = decode_cursor(cursor)

    filtered_query = query
    if decoded:
        cursor_sort_val = parse_cursor_sort_value(decoded.t)
        try:
            cursor_id = uuid.UUID(decoded.id)
        except Exception:
            cursor_id = decoded.id

        if order == "desc":
            if decoded.d == "next":
                filtered_query = filtered_query.filter(
                    or_(
                        sort_col < cursor_sort_val,
                        and_(sort_col == cursor_sort_val, id_col < cursor_id),
                    )
                )
            else:
                filtered_query = filtered_query.filter(
                    or_(
                        sort_col > cursor_sort_val,
                        and_(sort_col == cursor_sort_val, id_col > cursor_id),
                    )
                )
        else:  # asc
            if decoded.d == "next":
                filtered_query = filtered_query.filter(
                    or_(
                        sort_col > cursor_sort_val,
                        and_(sort_col == cursor_sort_val, id_col > cursor_id),
                    )
                )
            else:
                filtered_query = filtered_query.filter(
                    or_(
                        sort_col < cursor_sort_val,
                        and_(sort_col == cursor_sort_val, id_col < cursor_id),
                    )
                )

    # Apply ordering and overfetch by 1 to detect has_more
    ordered_query = filtered_query.order_by(
        desc(sort_col) if order == "desc" else asc(sort_col),
        desc(id_col) if order == "desc" else asc(id_col),
    )

    rows = ordered_query.limit(limit + 1).all()
    has_more = len(rows) > limit
    page_items = rows[:limit]

    next_cursor_str = None
    if has_more and page_items:
        last_item = page_items[-1]
        next_cursor_str = encode_cursor(
            getattr(last_item, sort_column_name),
            getattr(last_item, id_column_name),
            "next",
        )

    prev_cursor_str = None
    if decoded and page_items:
        first_item = page_items[0]
        prev_cursor_str = encode_cursor(
            getattr(first_item, sort_column_name),
            getattr(first_item, id_column_name),
            "prev",
        )

    return CursorPageResponse(
        items=page_items,
        limit=limit,
        next_cursor=next_cursor_str,
        prev_cursor=prev_cursor_str,
        has_more=has_more,
        has_prev=decoded is not None,
    )
