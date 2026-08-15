from app.schemas.pagination import (
    PaginationParams,
    encode_cursor,
    decode_cursor,
)
from app.core.pagination import build_paginated_response, paginate_query
from app.models.skill import Skill


def test_encode_decode_cursor():
    data = {"id": "12345", "val": "2026-08-04T12:00:00"}
    encoded = encode_cursor(data)
    assert isinstance(encoded, str)
    decoded = decode_cursor(encoded)
    assert decoded == data


def test_decode_invalid_cursor():
    assert decode_cursor("invalid_cursor_string!!!") is None
    assert decode_cursor("") is None


def test_pagination_params_defaults():
    params = PaginationParams()
    assert params.limit == 20
    assert params.cursor is None
    assert params.offset == 0


def test_build_paginated_response():
    items = ["item1", "item2"]
    resp = build_paginated_response(
        items=items,
        total=10,
        limit=2,
        next_cursor="next123",
        prev_cursor=None,
        has_next=True,
        has_prev=False,
    )
    assert resp.items == items
    assert resp.total == 10
    assert resp.limit == 2
    assert resp.next_cursor == "next123"
    assert resp.has_next is True
    assert resp.has_prev is False


def test_paginate_query_basic(db):
    # Add dummy skill objects
    for i in range(5):
        db.add(
            Skill(
                name=f"PaginationSkill_{i}",
                normalized_name=f"paginationskill_{i}",
                slug=f"paginationskill_{i}",
                category="Test",
            )
        )
    db.commit()

    query = db.query(Skill).filter(Skill.category == "Test")
    items, total, next_c, prev_c, has_n, has_p = paginate_query(
        query, limit=2, sort_column=Skill.name, is_desc=False, id_column=Skill.id
    )

    assert total >= 5
    assert len(items) == 2
    assert has_n is True
    assert next_c is not None
