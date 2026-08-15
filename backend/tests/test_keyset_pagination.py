"""
Tests for keyset pagination.

The existing pagination test only ever asked for page 1, which is why the
inclusive-boundary bug survived: it is invisible until you follow a cursor.
Most of what is here walks the pages and asserts on the *concatenation*, which
is the only way duplicates and dropped rows show up.
"""

from __future__ import annotations

import datetime as dt
import uuid

import pytest

from app.core.pagination import (
    InvalidCursor,
    decode_cursor_value,
    encode_cursor_value,
    paginate_and_respond,
    paginate_query,
)
from app.models.skill import Skill
from app.schemas.pagination import encode_cursor

CATEGORY = "KeysetTest"


def _make_skills(
    db, names: list[str], created: list[dt.datetime] | None = None
) -> list[Skill]:
    """Insert skills in `names` order, optionally with explicit created_at."""
    rows = []
    for index, name in enumerate(names):
        skill = Skill(
            id=uuid.uuid4(),
            name=name,
            normalized_name=f"{CATEGORY.lower()}_{name.lower()}",
            slug=f"{CATEGORY.lower()}-{name.lower()}",
            category=CATEGORY,
        )
        if created is not None:
            skill.created_at = created[index]
        rows.append(skill)
        db.add(skill)
    db.commit()
    return rows


def _query(db):
    return db.query(Skill).filter(Skill.category == CATEGORY)


def _walk_forward(db, limit: int, **kwargs) -> list[Skill]:
    """Follow next_cursor to the end and return every row, in order."""
    seen: list[Skill] = []
    cursor = None
    # A guard so a regression that never terminates fails the test instead of
    # hanging the suite.
    for _ in range(50):
        items, _total, next_cursor, _prev, has_next, _has_prev = paginate_query(
            _query(db), limit=limit, cursor=cursor, **kwargs
        )
        seen.extend(items)
        if not has_next:
            return seen
        assert next_cursor is not None
        cursor = next_cursor
    pytest.fail("pagination did not terminate")


class TestBoundary:
    def test_next_page_does_not_repeat_the_last_row(self, db):
        _make_skills(db, ["a", "b", "c", "d", "e"])

        page1, _, next_cursor, _, has_next, _ = paginate_query(
            _query(db),
            limit=3,
            sort_column=Skill.name,
            is_desc=False,
            id_column=Skill.id,
        )
        assert [s.name for s in page1] == ["a", "b", "c"]
        assert has_next is True

        page2, _, _, _, _, _ = paginate_query(
            _query(db),
            limit=3,
            cursor=next_cursor,
            sort_column=Skill.name,
            is_desc=False,
            id_column=Skill.id,
        )
        # This is the regression: page 2 used to start with "c" again.
        assert [s.name for s in page2] == ["d", "e"]

    def test_full_walk_returns_every_row_exactly_once(self, db):
        names = [f"skill{i:02d}" for i in range(11)]
        _make_skills(db, names)

        seen = _walk_forward(
            db, limit=3, sort_column=Skill.name, is_desc=False, id_column=Skill.id
        )

        assert [s.name for s in seen] == names
        assert len({s.id for s in seen}) == len(names)

    def test_full_walk_descending(self, db):
        names = [f"skill{i:02d}" for i in range(11)]
        _make_skills(db, names)

        seen = _walk_forward(
            db, limit=4, sort_column=Skill.name, is_desc=True, id_column=Skill.id
        )

        assert [s.name for s in seen] == list(reversed(names))

    def test_walk_when_limit_exactly_divides_the_row_count(self, db):
        names = [f"skill{i:02d}" for i in range(6)]
        _make_skills(db, names)

        seen = _walk_forward(
            db, limit=3, sort_column=Skill.name, is_desc=False, id_column=Skill.id
        )

        assert [s.name for s in seen] == names

    def test_id_only_pagination_has_no_overlap(self, db):
        _make_skills(db, ["a", "b", "c", "d", "e"])

        seen = _walk_forward(db, limit=2, id_column=Skill.id, is_desc=False)

        assert len(seen) == 5
        assert len({s.id for s in seen}) == 5


class TestTies:
    """Rows sharing a sort value must still be totally ordered."""

    def test_rows_with_identical_sort_values_are_not_duplicated(self, db):
        shared = dt.datetime(2026, 8, 11, 10, 54, 43)
        names = [f"tied{i}" for i in range(6)]
        _make_skills(db, names, created=[shared] * 6)

        seen = _walk_forward(
            db, limit=2, sort_column=Skill.created_at, is_desc=True, id_column=Skill.id
        )

        # Six rows, one page boundary inside each tied group: without the id
        # tiebreaker the whole tied set came back on every page.
        assert len(seen) == 6
        assert len({s.id for s in seen}) == 6

    def test_partial_ties_keep_the_overall_order(self, db):
        early = dt.datetime(2026, 8, 10, 9, 0, 0)
        late = dt.datetime(2026, 8, 11, 9, 0, 0)
        _make_skills(
            db,
            ["p", "q", "r", "s"],
            created=[late, late, early, early],
        )

        seen = _walk_forward(
            db, limit=1, sort_column=Skill.created_at, is_desc=True, id_column=Skill.id
        )

        assert len(seen) == 4
        assert [s.created_at for s in seen] == [late, late, early, early]


class TestBackwards:
    def test_prev_cursor_goes_back_one_page_not_to_the_start(self, db):
        names = [f"skill{i:02d}" for i in range(9)]
        _make_skills(db, names)

        kwargs = dict(sort_column=Skill.name, is_desc=False, id_column=Skill.id)

        page1, _, cursor1, _, _, _ = paginate_query(_query(db), limit=3, **kwargs)
        page2, _, cursor2, _, _, _ = paginate_query(
            _query(db), limit=3, cursor=cursor1, **kwargs
        )
        page3, _, _, prev3, _, has_prev3 = paginate_query(
            _query(db), limit=3, cursor=cursor2, **kwargs
        )

        assert [s.name for s in page1] == ["skill00", "skill01", "skill02"]
        assert [s.name for s in page2] == ["skill03", "skill04", "skill05"]
        assert [s.name for s in page3] == ["skill06", "skill07", "skill08"]
        assert has_prev3 is True

        back, _, _, _, _, _ = paginate_query(
            _query(db), limit=3, cursor=prev3, **kwargs
        )

        # Previously prev_cursor was always {"offset": 0} and this was page 1.
        assert [s.name for s in back] == ["skill03", "skill04", "skill05"]

    def test_backwards_page_is_returned_in_forward_order(self, db):
        _make_skills(db, ["a", "b", "c", "d", "e", "f"])

        kwargs = dict(sort_column=Skill.name, is_desc=False, id_column=Skill.id)

        _page1, _, cursor1, _, _, _ = paginate_query(_query(db), limit=2, **kwargs)
        _page2, _, cursor2, _, _, _ = paginate_query(
            _query(db), limit=2, cursor=cursor1, **kwargs
        )
        _page3, _, _, prev3, _, _ = paginate_query(
            _query(db), limit=2, cursor=cursor2, **kwargs
        )

        back, _, _, _, _, _ = paginate_query(
            _query(db), limit=2, cursor=prev3, **kwargs
        )

        # Ascending means ascending, even when we walked backwards to get here.
        assert [s.name for s in back] == ["c", "d"]

    def test_first_page_reports_no_previous(self, db):
        _make_skills(db, ["a", "b", "c"])

        _items, _total, _next, prev, _has_next, has_prev = paginate_query(
            _query(db),
            limit=2,
            sort_column=Skill.name,
            is_desc=False,
            id_column=Skill.id,
        )

        assert has_prev is False
        assert prev is None

    def test_walking_back_from_the_second_page_reports_no_previous(self, db):
        _make_skills(db, ["a", "b", "c", "d"])

        kwargs = dict(sort_column=Skill.name, is_desc=False, id_column=Skill.id)

        _page1, _, cursor1, _, _, _ = paginate_query(_query(db), limit=2, **kwargs)
        _page2, _, _, prev2, _, _ = paginate_query(
            _query(db), limit=2, cursor=cursor1, **kwargs
        )

        back, _, _, _, has_next, has_prev = paginate_query(
            _query(db), limit=2, cursor=prev2, **kwargs
        )

        assert [s.name for s in back] == ["a", "b"]
        assert has_next is True
        assert has_prev is False


class TestCursorValues:
    """Cursor values must come back as the type they went in as."""

    @pytest.mark.parametrize(
        "value",
        [
            None,
            True,
            False,
            0,
            -17,
            3.5,
            "plain string",
            "a string that looks like 2026-08-11T10:54:43",
            uuid.UUID("11111111-1111-4111-8111-111111111111"),
            dt.datetime(2026, 8, 11, 10, 54, 43, 123456),
            dt.datetime(2026, 8, 11, 10, 54, 43, tzinfo=dt.timezone.utc),
            dt.date(2026, 8, 11),
            dt.time(10, 54, 43),
        ],
    )
    def test_round_trip_preserves_type_and_value(self, value):
        restored = decode_cursor_value(encode_cursor_value(value))

        assert restored == value
        assert type(restored) is type(value)

    def test_bool_is_not_flattened_to_int(self):
        assert encode_cursor_value(True)["t"] == "bool"
        assert encode_cursor_value(1)["t"] == "int"

    def test_datetime_is_not_flattened_to_date(self):
        assert encode_cursor_value(dt.datetime(2026, 8, 11))["t"] == "dt"
        assert encode_cursor_value(dt.date(2026, 8, 11))["t"] == "date"

    def test_datetime_cursor_survives_a_real_page_walk(self, db):
        base = dt.datetime(2026, 8, 11, 10, 0, 0)
        names = [f"dated{i}" for i in range(7)]
        _make_skills(
            db, names, created=[base + dt.timedelta(minutes=i) for i in range(7)]
        )

        seen = _walk_forward(
            db, limit=2, sort_column=Skill.created_at, is_desc=True, id_column=Skill.id
        )

        assert len(seen) == 7
        assert [s.name for s in seen] == list(reversed(names))


class TestInvalidCursors:
    def test_undecodable_cursor_is_rejected(self, db):
        _make_skills(db, ["a"])

        with pytest.raises(InvalidCursor):
            paginate_query(
                _query(db), limit=2, cursor="not base64 at all!!!", id_column=Skill.id
            )

    def test_cursor_without_a_row_reference_is_rejected(self, db):
        _make_skills(db, ["a"])

        with pytest.raises(InvalidCursor):
            paginate_query(_query(db), limit=2, cursor=encode_cursor({"d": "next"}))

    def test_unknown_direction_is_rejected(self, db):
        _make_skills(db, ["a"])

        cursor = encode_cursor({"d": "sideways", "id": {"t": "str", "v": "x"}})

        with pytest.raises(InvalidCursor):
            paginate_query(_query(db), limit=2, cursor=cursor, id_column=Skill.id)

    def test_untagged_cursor_value_is_rejected(self, db):
        _make_skills(db, ["a"])

        # The old cursor format, which stored bare stringified values.
        cursor = encode_cursor({"id": "11111111-1111-4111-8111-111111111111"})

        with pytest.raises(InvalidCursor):
            paginate_query(_query(db), limit=2, cursor=cursor, id_column=Skill.id)

    def test_value_that_does_not_match_its_tag_is_rejected(self, db):
        _make_skills(db, ["a"])

        cursor = encode_cursor({"id": {"t": "uuid", "v": "definitely not a uuid"}})

        with pytest.raises(InvalidCursor):
            paginate_query(_query(db), limit=2, cursor=cursor, id_column=Skill.id)


class TestOffsetMode:
    def test_offset_still_works_for_page_pickers(self, db):
        names = [f"skill{i:02d}" for i in range(7)]
        _make_skills(db, names)

        kwargs = dict(sort_column=Skill.name, is_desc=False, id_column=Skill.id)

        page1, total, _, _, _, has_prev1 = paginate_query(
            _query(db), limit=3, offset=0, **kwargs
        )
        page2, _, _, _, has_next2, has_prev2 = paginate_query(
            _query(db), limit=3, offset=3, **kwargs
        )

        assert total == 7
        assert [s.name for s in page1] == ["skill00", "skill01", "skill02"]
        assert [s.name for s in page2] == ["skill03", "skill04", "skill05"]
        assert has_prev1 is False
        assert has_prev2 is True
        assert has_next2 is True

    def test_offset_past_the_end_returns_nothing_and_no_cursors(self, db):
        _make_skills(db, ["a", "b"])

        items, total, next_c, prev_c, has_next, _ = paginate_query(
            _query(db),
            limit=3,
            offset=99,
            sort_column=Skill.name,
            is_desc=False,
            id_column=Skill.id,
        )

        assert items == []
        assert total == 2
        assert has_next is False
        assert next_c is None
        assert prev_c is None

    def test_negative_offset_is_clamped_rather_than_raising(self, db):
        _make_skills(db, ["a", "b", "c"])

        items, _, _, _, _, _ = paginate_query(
            _query(db),
            limit=2,
            offset=-5,
            sort_column=Skill.name,
            is_desc=False,
            id_column=Skill.id,
        )

        assert [s.name for s in items] == ["a", "b"]


class TestMisc:
    def test_total_counts_the_whole_set_not_the_page(self, db):
        _make_skills(db, [f"skill{i:02d}" for i in range(9)])

        kwargs = dict(sort_column=Skill.name, is_desc=False, id_column=Skill.id)

        _page1, total1, cursor1, _, _, _ = paginate_query(_query(db), limit=4, **kwargs)
        _page2, total2, _, _, _, _ = paginate_query(
            _query(db), limit=4, cursor=cursor1, **kwargs
        )

        assert total1 == 9
        assert total2 == 9

    def test_empty_result_set(self, db):
        items, total, next_c, prev_c, has_next, has_prev = paginate_query(
            _query(db),
            limit=5,
            sort_column=Skill.name,
            is_desc=False,
            id_column=Skill.id,
        )

        assert items == []
        assert total == 0
        assert (next_c, prev_c, has_next, has_prev) == (None, None, False, False)

    def test_limit_below_one_is_rejected(self, db):
        with pytest.raises(ValueError):
            paginate_query(_query(db), limit=0, id_column=Skill.id)

    def test_paginate_and_respond_matches_paginate_query(self, db):
        _make_skills(db, ["a", "b", "c", "d"])

        kwargs = dict(sort_column=Skill.name, is_desc=False, id_column=Skill.id)

        items, total, next_c, prev_c, has_next, has_prev = paginate_query(
            _query(db), limit=2, **kwargs
        )
        response = paginate_and_respond(_query(db), limit=2, **kwargs)

        assert [s.id for s in response.items] == [s.id for s in items]
        assert response.total == total
        assert response.limit == 2
        assert response.next_cursor == next_c
        assert response.prev_cursor == prev_c
        assert response.has_next == has_next
        assert response.has_prev == has_prev
