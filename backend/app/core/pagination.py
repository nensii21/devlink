"""
Keyset ("cursor") pagination for SQLAlchemy queries.

The rule that makes keyset pagination work is that the cursor must describe a
*strict* boundary over a *total* order. Get either half wrong and pages overlap
or drop rows:

* **Strict.** The cursor points at the last row of the page you just got. The
  next page must be the rows strictly after it. An inclusive ``<=`` returns
  that row again as the first row of the next page.
* **Total.** ``created_at`` is not unique. Two rows written in the same
  transaction share a timestamp, so ordering by it alone leaves their relative
  order up to the planner, and it is free to answer differently between two
  queries. Every comparison here carries the primary key as a tiebreaker, so
  the order is total even when the sort column is not.

Cursors are opaque to clients but not encrypted -- they are base64 of a small
JSON object, and a client that decodes one learns only the sort value of a row
it was already shown. They *are* type-tagged: a cursor over a ``DateTime``
column has to come back out of the cursor as a ``datetime``, not as the string
``'2026-08-11 10:54:43.123456+00:00'``, or the comparison against the column
either raises or silently degrades to a text comparison with different ordering
than the index.
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any, List, Literal, Optional, Tuple, TypeVar

from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.orm import Query

from app.schemas.pagination import PaginatedResponse, decode_cursor, encode_cursor

T = TypeVar("T")

Direction = Literal["next", "prev"]


class InvalidCursor(ValueError):
    """
    Raised when a cursor cannot be decoded or does not describe this query.

    This is a client error, not a server error: a caller that sends a cursor
    from a different sort order, or a truncated one, has asked for something we
    cannot answer. Silently falling back to page 1 is worse -- an infinite
    scroll that hits it restarts from the top and loops forever.
    """


# ---------------------------------------------------------------------------
# Cursor value encoding
# ---------------------------------------------------------------------------
#
# JSON has no datetime and no UUID, so a tag travels with the value and is used
# to rebuild the original type on the way back in.

_TAG_NULL = "null"
_TAG_STR = "str"
_TAG_INT = "int"
_TAG_FLOAT = "float"
_TAG_BOOL = "bool"
_TAG_DECIMAL = "dec"
_TAG_UUID = "uuid"
_TAG_DATETIME = "dt"
_TAG_DATE = "date"
_TAG_TIME = "time"


def encode_cursor_value(value: Any) -> dict:
    """Tag a Python value so it survives a JSON round trip with its type."""
    if value is None:
        return {"t": _TAG_NULL, "v": None}
    # bool before int: bool is a subclass of int and would otherwise be tagged
    # as one and come back as 0/1.
    if isinstance(value, bool):
        return {"t": _TAG_BOOL, "v": value}
    if isinstance(value, int):
        return {"t": _TAG_INT, "v": value}
    if isinstance(value, float):
        return {"t": _TAG_FLOAT, "v": value}
    if isinstance(value, Decimal):
        return {"t": _TAG_DECIMAL, "v": str(value)}
    if isinstance(value, uuid.UUID):
        return {"t": _TAG_UUID, "v": str(value)}
    # datetime before date: datetime is a subclass of date.
    if isinstance(value, dt.datetime):
        return {"t": _TAG_DATETIME, "v": value.isoformat()}
    if isinstance(value, dt.date):
        return {"t": _TAG_DATE, "v": value.isoformat()}
    if isinstance(value, dt.time):
        return {"t": _TAG_TIME, "v": value.isoformat()}
    return {"t": _TAG_STR, "v": str(value)}


def decode_cursor_value(payload: Any) -> Any:
    """Rebuild a value tagged by :func:`encode_cursor_value`."""
    if not isinstance(payload, dict) or "t" not in payload:
        raise InvalidCursor("Cursor value is missing its type tag.")

    tag = payload["t"]
    raw = payload.get("v")

    try:
        if tag == _TAG_NULL:
            return None
        if tag == _TAG_BOOL:
            return bool(raw)
        if tag == _TAG_INT:
            return int(raw)
        if tag == _TAG_FLOAT:
            return float(raw)
        if tag == _TAG_DECIMAL:
            return Decimal(str(raw))
        if tag == _TAG_UUID:
            return uuid.UUID(str(raw))
        if tag == _TAG_DATETIME:
            return dt.datetime.fromisoformat(str(raw))
        if tag == _TAG_DATE:
            return dt.date.fromisoformat(str(raw))
        if tag == _TAG_TIME:
            return dt.time.fromisoformat(str(raw))
        if tag == _TAG_STR:
            return str(raw)
    except (TypeError, ValueError) as exc:
        raise InvalidCursor(f"Cursor value is not a valid {tag}.") from exc

    raise InvalidCursor(f"Unknown cursor value type: {tag!r}")


def _column_key(column: Any, fallback: str) -> str:
    """The attribute name behind a mapped column, for ``getattr``."""
    return getattr(column, "key", None) or fallback


def _build_cursor(
    item: Any,
    sort_column: Optional[Any],
    id_column: Optional[Any],
    direction: Direction,
) -> str:
    """Encode the boundary row that the next (or previous) page starts after."""
    payload: dict[str, Any] = {"d": direction}

    if sort_column is not None:
        key = _column_key(sort_column, "id")
        payload["val"] = encode_cursor_value(getattr(item, key, None))

    if id_column is not None:
        key = _column_key(id_column, "id")
        payload["id"] = encode_cursor_value(getattr(item, key, None))

    return encode_cursor(payload)


def _parse_cursor(cursor: str) -> tuple[Direction, Any, Any, bool, bool]:
    """
    Decode a cursor into ``(direction, sort_value, id_value, has_val, has_id)``.

    Raises :class:`InvalidCursor` rather than returning ``None``, so a bad
    cursor surfaces as a client error instead of quietly restarting at page 1.
    """
    data = decode_cursor(cursor)
    if data is None or not isinstance(data, dict):
        raise InvalidCursor("Cursor could not be decoded.")

    direction = data.get("d", "next")
    if direction not in ("next", "prev"):
        raise InvalidCursor(f"Unknown cursor direction: {direction!r}")

    has_val = "val" in data
    has_id = "id" in data

    if not has_val and not has_id:
        raise InvalidCursor("Cursor does not identify a row.")

    sort_value = decode_cursor_value(data["val"]) if has_val else None
    id_value = decode_cursor_value(data["id"]) if has_id else None

    return direction, sort_value, id_value, has_val, has_id


# ---------------------------------------------------------------------------
# Keyset filter
# ---------------------------------------------------------------------------


def _keyset_filter(
    sort_column: Optional[Any],
    id_column: Optional[Any],
    sort_value: Any,
    id_value: Any,
    has_val: bool,
    has_id: bool,
    descending: bool,
):
    """
    The ``WHERE`` clause for "strictly after this row in this order".

    With a tiebreaker the comparison is lexicographic over the pair, which is
    the standard row-value form written out longhand because not every backend
    we run on supports ``(a, b) < (:a, :b)`` with an index behind it::

        sort < :sort  OR  (sort = :sort  AND  id < :id)

    Ascending flips both operators. When only one column is available the pair
    degenerates to a plain strict comparison on that column.
    """
    usable_sort = sort_column is not None and has_val and sort_value is not None
    usable_id = id_column is not None and has_id and id_value is not None

    if usable_sort and usable_id:
        if descending:
            return or_(
                sort_column < sort_value,
                and_(sort_column == sort_value, id_column < id_value),
            )
        return or_(
            sort_column > sort_value,
            and_(sort_column == sort_value, id_column > id_value),
        )

    if usable_sort:
        # No tiebreaker available. Strict is still the right call -- it can drop
        # rows that tie on the sort value, but inclusive duplicates them on
        # every page, and a duplicate is the worse failure in a feed.
        return sort_column < sort_value if descending else sort_column > sort_value

    if usable_id:
        return id_column < id_value if descending else id_column > id_value

    return None


def _order_by(
    query: Query,
    sort_column: Optional[Any],
    id_column: Optional[Any],
    descending: bool,
) -> Query:
    """Order by the sort column with the id as a tiebreaker, in that order."""
    direction = desc if descending else asc

    clauses = []
    if sort_column is not None:
        clauses.append(direction(sort_column))
    if id_column is not None:
        clauses.append(direction(id_column))

    return query.order_by(*clauses) if clauses else query


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def paginate_query(
    query: Query,
    limit: int = 20,
    cursor: Optional[str] = None,
    offset: Optional[int] = 0,
    sort_column: Optional[Any] = None,
    is_desc: bool = True,
    id_column: Optional[Any] = None,
) -> Tuple[List[Any], int, Optional[str], Optional[str], bool, bool]:
    """
    Paginate a SQLAlchemy query.

    Returns ``(items, total, next_cursor, prev_cursor, has_next, has_prev)``.

    Pass ``cursor`` for keyset pagination (what you want for feeds and infinite
    scroll) or ``offset`` for offset pagination (what you want for a page
    picker that shows "page 7 of 40"). A cursor wins if both are given.

    ``id_column`` should be the primary key. It is not strictly required, but
    without it rows that tie on ``sort_column`` have no defined order and the
    page boundary between them is not stable.

    Raises :class:`InvalidCursor` if ``cursor`` is malformed.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    total = query.count()

    direction: Direction = "next"
    sort_value = id_value = None
    has_val = has_id = False

    if cursor:
        direction, sort_value, id_value, has_val, has_id = _parse_cursor(cursor)

    effective_offset = 0 if cursor else max(0, offset or 0)

    # Walking backwards means running the query in the opposite order and
    # flipping the page over at the end.
    descending = is_desc if direction == "next" else not is_desc

    if cursor:
        condition = _keyset_filter(
            sort_column,
            id_column,
            sort_value,
            id_value,
            has_val,
            has_id,
            descending,
        )
        if condition is not None:
            query = query.filter(condition)

    query = _order_by(query, sort_column, id_column, descending)

    if effective_offset:
        query = query.offset(effective_offset)

    # One extra row tells us whether there is another page without a second
    # count query.
    raw_items = query.limit(limit + 1).all()
    has_more = len(raw_items) > limit
    items = raw_items[:limit]

    if direction == "prev":
        # The rows came back in reverse order; put them back the way the caller
        # asked for them.
        items = list(reversed(items))
        has_next = True  # we necessarily came from a page after this one
        has_prev = has_more
    else:
        has_next = has_more
        has_prev = bool(cursor) or effective_offset > 0

    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None

    if items:
        if has_next:
            next_cursor = _build_cursor(items[-1], sort_column, id_column, "next")
        if has_prev:
            prev_cursor = _build_cursor(items[0], sort_column, id_column, "prev")

    return items, total, next_cursor, prev_cursor, has_next, has_prev


def build_paginated_response(
    items: List[T],
    total: int,
    limit: int,
    next_cursor: Optional[str] = None,
    prev_cursor: Optional[str] = None,
    has_next: bool = False,
    has_prev: bool = False,
) -> PaginatedResponse[T]:
    """Helper to build a PaginatedResponse pydantic model."""
    return PaginatedResponse[T](
        items=items,
        total=total,
        limit=limit,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
        has_next=has_next,
        has_prev=has_prev,
    )


def paginate_and_respond(
    query: Query,
    limit: int = 20,
    cursor: Optional[str] = None,
    offset: Optional[int] = 0,
    sort_column: Optional[Any] = None,
    is_desc: bool = True,
    id_column: Optional[Any] = None,
) -> PaginatedResponse[Any]:
    """
    :func:`paginate_query` and :func:`build_paginated_response` in one call.

    Most routers want exactly this and nothing else, and threading six
    positional results through by hand is how the two halves drift apart.
    """
    items, total, next_cursor, prev_cursor, has_next, has_prev = paginate_query(
        query,
        limit=limit,
        cursor=cursor,
        offset=offset,
        sort_column=sort_column,
        is_desc=is_desc,
        id_column=id_column,
    )
    return build_paginated_response(
        items=items,
        total=total,
        limit=limit,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
        has_next=has_next,
        has_prev=has_prev,
    )
