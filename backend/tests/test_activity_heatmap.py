"""
Unit & integration tests for the contribution heatmap and streaks (#1040).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.activity import ActivityType
from app.models.user import User
from app.services.activity_heatmap_service import (
    DEFAULT_WINDOW_DAYS,
    MAX_WINDOW_DAYS,
    ActivityHeatmapService,
)

TODAY = date(2026, 6, 15)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(username: str = "ada", is_private: bool = False) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = username
    user.is_private = is_private
    return user


def _days(*offsets: int, anchor: date = TODAY) -> set[date]:
    """Build a set of dates ``offsets`` days before ``anchor``."""
    return {anchor - timedelta(days=offset) for offset in offsets}


def _stub_db(rows: list[tuple[datetime, ActivityType]]) -> MagicMock:
    """A Session whose ``execute(...).all()`` yields the supplied rows."""
    db = MagicMock(spec=Session)
    result = MagicMock()
    result.all.return_value = rows
    db.execute.return_value = result
    return db


def _at(offset_days: int, hour: int = 12, anchor: date = TODAY) -> datetime:
    day = anchor - timedelta(days=offset_days)
    return datetime(day.year, day.month, day.day, hour, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# 1. Window resolution
# ---------------------------------------------------------------------------


class TestResolveWindow:
    def test_single_day_window_is_today_only(self):
        start, end = ActivityHeatmapService.resolve_window(1, today=TODAY)
        assert start == TODAY
        assert end == TODAY

    def test_default_window_spans_a_year_inclusive(self):
        start, end = ActivityHeatmapService.resolve_window(
            DEFAULT_WINDOW_DAYS, today=TODAY
        )
        assert end == TODAY
        assert (end - start).days == DEFAULT_WINDOW_DAYS - 1

    def test_max_window_is_accepted(self):
        start, end = ActivityHeatmapService.resolve_window(MAX_WINDOW_DAYS, today=TODAY)
        assert (end - start).days == MAX_WINDOW_DAYS - 1

    @pytest.mark.parametrize("bad", [0, -1, MAX_WINDOW_DAYS + 1, 10_000])
    def test_out_of_range_rejected(self, bad: int):
        with pytest.raises(HTTPException) as exc:
            ActivityHeatmapService.resolve_window(bad, today=TODAY)
        assert exc.value.status_code == 422


# ---------------------------------------------------------------------------
# 2. Current streak
# ---------------------------------------------------------------------------


class TestCurrentStreak:
    def test_empty_history_is_zero(self):
        assert ActivityHeatmapService.compute_current_streak(set(), TODAY) == 0

    def test_active_today_only(self):
        assert ActivityHeatmapService.compute_current_streak(_days(0), TODAY) == 1

    def test_active_yesterday_keeps_streak_alive(self):
        # Nothing logged yet today; the streak should not be reported broken.
        assert ActivityHeatmapService.compute_current_streak(_days(1, 2, 3), TODAY) == 3

    def test_run_ending_today(self):
        assert (
            ActivityHeatmapService.compute_current_streak(_days(0, 1, 2, 3, 4), TODAY)
            == 5
        )

    def test_single_day_gap_breaks_streak(self):
        # Active 2..6 days ago but nothing yesterday or today.
        assert (
            ActivityHeatmapService.compute_current_streak(_days(2, 3, 4, 5, 6), TODAY)
            == 0
        )

    def test_gap_inside_run_truncates_at_the_gap(self):
        # Active today, yesterday, then a hole at -2, then more.
        assert (
            ActivityHeatmapService.compute_current_streak(_days(0, 1, 3, 4), TODAY) == 2
        )

    def test_future_days_are_ignored(self):
        active = _days(0, 1) | {TODAY + timedelta(days=1)}
        assert ActivityHeatmapService.compute_current_streak(active, TODAY) == 2


# ---------------------------------------------------------------------------
# 3. Longest streak
# ---------------------------------------------------------------------------


class TestLongestStreak:
    def test_empty(self):
        length, start, end = ActivityHeatmapService.compute_longest_streak(set())
        assert (length, start, end) == (0, None, None)

    def test_single_day(self):
        day = date(2026, 1, 4)
        length, start, end = ActivityHeatmapService.compute_longest_streak({day})
        assert length == 1
        assert start == end == day

    def test_picks_the_longest_of_several_runs(self):
        active = (
            {date(2026, 1, 1), date(2026, 1, 2)}
            | {date(2026, 2, 1) + timedelta(days=i) for i in range(5)}
            | {date(2026, 3, 1)}
        )
        length, start, end = ActivityHeatmapService.compute_longest_streak(active)
        assert length == 5
        assert start == date(2026, 2, 1)
        assert end == date(2026, 2, 5)

    def test_longest_run_at_the_start_of_the_window(self):
        active = {date(2026, 1, 1) + timedelta(days=i) for i in range(4)} | {
            date(2026, 5, 1)
        }
        length, start, end = ActivityHeatmapService.compute_longest_streak(active)
        assert (length, start, end) == (4, date(2026, 1, 1), date(2026, 1, 4))

    def test_longest_run_at_the_end_of_the_window(self):
        active = {date(2026, 1, 1)} | {
            date(2026, 5, 1) + timedelta(days=i) for i in range(4)
        }
        length, start, end = ActivityHeatmapService.compute_longest_streak(active)
        assert (length, start, end) == (4, date(2026, 5, 1), date(2026, 5, 4))

    def test_ties_keep_the_first_run(self):
        active = {
            date(2026, 1, 1),
            date(2026, 1, 2),
            date(2026, 3, 1),
            date(2026, 3, 2),
        }
        length, start, _ = ActivityHeatmapService.compute_longest_streak(active)
        assert length == 2
        assert start == date(2026, 1, 1)

    def test_every_day_active(self):
        active = {date(2026, 1, 1) + timedelta(days=i) for i in range(60)}
        length, start, end = ActivityHeatmapService.compute_longest_streak(active)
        assert length == 60
        assert start == date(2026, 1, 1)
        assert end == date(2026, 3, 1)


# ---------------------------------------------------------------------------
# 4. Intensity levels
# ---------------------------------------------------------------------------


class TestLevels:
    def test_zero_count_is_level_zero(self):
        assert ActivityHeatmapService.level_for(0, (1, 2, 3)) == 0

    def test_thresholds_default_when_nothing_is_active(self):
        assert ActivityHeatmapService.compute_level_thresholds([0, 0, 0]) == (1, 2, 3)

    def test_uniform_activity_all_lands_on_level_one(self):
        thresholds = ActivityHeatmapService.compute_level_thresholds([1] * 20)
        assert thresholds == (1, 1, 1)
        assert ActivityHeatmapService.level_for(1, thresholds) == 1

    def test_thresholds_are_non_decreasing(self):
        thresholds = ActivityHeatmapService.compute_level_thresholds([1, 1, 2, 9, 40])
        assert thresholds[0] <= thresholds[1] <= thresholds[2]

    def test_busiest_day_reaches_level_four(self):
        counts = [1, 1, 2, 3, 4, 5, 30]
        thresholds = ActivityHeatmapService.compute_level_thresholds(counts)
        assert ActivityHeatmapService.level_for(30, thresholds) == 4

    def test_levels_are_monotonic_in_count(self):
        thresholds = ActivityHeatmapService.compute_level_thresholds(
            [1, 2, 3, 4, 5, 6, 7, 8]
        )
        levels = [ActivityHeatmapService.level_for(c, thresholds) for c in range(0, 12)]
        assert levels == sorted(levels)
        assert max(levels) == 4


# ---------------------------------------------------------------------------
# 5. Summary assembly
# ---------------------------------------------------------------------------


class TestBuildSummary:
    def test_empty_window(self):
        start = TODAY - timedelta(days=6)
        counts = {start + timedelta(days=i): 0 for i in range(7)}
        summary = ActivityHeatmapService.build_summary(counts, start, TODAY, TODAY)

        assert summary.total_activities == 0
        assert summary.active_days == 0
        assert summary.total_days == 7
        assert summary.current_streak == 0
        assert summary.longest_streak == 0
        assert summary.busiest_day is None
        assert summary.daily_average == 0.0
        assert summary.active_day_average == 0.0

    def test_averages_and_busiest_day(self):
        start = TODAY - timedelta(days=3)
        counts = {
            start: 1,
            start + timedelta(days=1): 0,
            start + timedelta(days=2): 5,
            start + timedelta(days=3): 2,
        }
        summary = ActivityHeatmapService.build_summary(counts, start, TODAY, TODAY)

        assert summary.total_activities == 8
        assert summary.active_days == 3
        assert summary.total_days == 4
        assert summary.busiest_day == start + timedelta(days=2)
        assert summary.busiest_day_count == 5
        assert summary.daily_average == 2.0
        assert summary.active_day_average == 2.67

    def test_busiest_day_tie_resolves_to_the_earlier_day(self):
        start = TODAY - timedelta(days=2)
        counts = {start: 3, start + timedelta(days=1): 3, TODAY: 1}
        summary = ActivityHeatmapService.build_summary(counts, start, TODAY, TODAY)
        assert summary.busiest_day == start


# ---------------------------------------------------------------------------
# 6. Full build
# ---------------------------------------------------------------------------


class TestBuild:
    def test_grid_has_no_holes(self):
        db = _stub_db([(_at(0), ActivityType.PROJECT_CREATED)])
        user = _make_user()

        result = ActivityHeatmapService.build(db, subject=user, days=30, today=TODAY)

        assert len(result.days) == 30
        assert result.days[0].day == TODAY - timedelta(days=29)
        assert result.days[-1].day == TODAY
        # Strictly ascending, one day apart, all the way through.
        for previous, current in zip(result.days, result.days[1:]):
            assert current.day - previous.day == timedelta(days=1)

    def test_counts_are_bucketed_by_utc_day(self):
        rows = [
            (_at(0, hour=0), ActivityType.COMMENT_CREATED),
            (_at(0, hour=23), ActivityType.COMMENT_CREATED),
            (_at(1, hour=9), ActivityType.PROJECT_CREATED),
        ]
        result = ActivityHeatmapService.build(
            _stub_db(rows), subject=_make_user(), days=7, today=TODAY
        )

        by_day = {d.day: d.count for d in result.days}
        assert by_day[TODAY] == 2
        assert by_day[TODAY - timedelta(days=1)] == 1
        assert result.streak.total_activities == 3

    def test_naive_timestamps_are_treated_as_utc(self):
        naive = datetime(TODAY.year, TODAY.month, TODAY.day, 8)
        result = ActivityHeatmapService.build(
            _stub_db([(naive, ActivityType.MESSAGE_SENT)]),
            subject=_make_user(),
            days=5,
            today=TODAY,
        )
        by_day = {d.day: d.count for d in result.days}
        assert by_day[TODAY] == 1

    def test_activity_outside_the_window_is_discarded(self):
        # The query filters by window, but a row on the boundary must not be
        # double counted or land in the wrong bucket if one slips through.
        rows = [
            (_at(400), ActivityType.PROJECT_CREATED),
            (_at(2), ActivityType.PROJECT_CREATED),
        ]
        result = ActivityHeatmapService.build(
            _stub_db(rows), subject=_make_user(), days=30, today=TODAY
        )
        assert result.streak.total_activities == 1

    def test_breakdown_is_sorted_by_count_descending(self):
        rows = [
            (_at(0), ActivityType.COMMENT_CREATED),
            (_at(1), ActivityType.COMMENT_CREATED),
            (_at(2), ActivityType.COMMENT_CREATED),
            (_at(3), ActivityType.PROJECT_CREATED),
            (_at(4), ActivityType.PROJECT_CREATED),
            (_at(5), ActivityType.MESSAGE_SENT),
        ]
        result = ActivityHeatmapService.build(
            _stub_db(rows), subject=_make_user(), days=30, today=TODAY
        )

        assert [b.count for b in result.breakdown] == [3, 2, 1]
        assert result.breakdown[0].activity_type == ActivityType.COMMENT_CREATED.value

    def test_streak_reflects_a_continuous_run(self):
        rows = [(_at(offset), ActivityType.PROJECT_UPDATED) for offset in range(0, 5)]
        result = ActivityHeatmapService.build(
            _stub_db(rows), subject=_make_user(), days=30, today=TODAY
        )

        assert result.streak.current_streak == 5
        assert result.streak.longest_streak == 5
        assert result.streak.active_days == 5

    def test_identity_fields_are_echoed_back(self):
        user = _make_user(username="grace")
        result = ActivityHeatmapService.build(
            _stub_db([]), subject=user, days=10, today=TODAY
        )

        assert result.username == "grace"
        assert result.user_id == user.id
        assert result.start_date == TODAY - timedelta(days=9)
        assert result.end_date == TODAY


# ---------------------------------------------------------------------------
# 7. Access control
# ---------------------------------------------------------------------------


class TestVisibility:
    def test_public_profile_visible_to_anonymous(self):
        ActivityHeatmapService.require_visible(_make_user(), None)

    def test_private_profile_hidden_from_anonymous(self):
        with pytest.raises(HTTPException) as exc:
            ActivityHeatmapService.require_visible(_make_user(is_private=True), None)
        assert exc.value.status_code == 403

    def test_private_profile_hidden_from_other_users(self):
        with pytest.raises(HTTPException) as exc:
            ActivityHeatmapService.require_visible(
                _make_user(is_private=True), _make_user("mallory")
            )
        assert exc.value.status_code == 403

    def test_private_profile_visible_to_owner(self):
        subject = _make_user(is_private=True)
        ActivityHeatmapService.require_visible(subject, subject)


# ---------------------------------------------------------------------------
# 8. Activity type filter parsing
# ---------------------------------------------------------------------------


class TestParseActivityTypes:
    def test_none_and_blank_mean_no_filter(self):
        assert ActivityHeatmapService.parse_activity_types(None) is None
        assert ActivityHeatmapService.parse_activity_types("") is None
        assert ActivityHeatmapService.parse_activity_types("  ,  ") is None

    def test_parses_a_list(self):
        parsed = ActivityHeatmapService.parse_activity_types(
            "project_created, comment_created"
        )
        assert parsed == [ActivityType.PROJECT_CREATED, ActivityType.COMMENT_CREATED]

    def test_unknown_type_is_rejected(self):
        with pytest.raises(HTTPException) as exc:
            ActivityHeatmapService.parse_activity_types(
                "project_created,not_a_real_type"
            )
        assert exc.value.status_code == 422
        assert "not_a_real_type" in exc.value.detail


# ---------------------------------------------------------------------------
# 9. HTTP surface
# ---------------------------------------------------------------------------


class TestHeatmapEndpoints:
    def test_unknown_username_returns_404(self, client):
        response = client.get("/api/v1/users/definitely-not-a-user/activity-heatmap")
        assert response.status_code == 404

    def test_days_out_of_range_returns_422(self, client):
        response = client.get(
            "/api/v1/users/someone/activity-heatmap", params={"days": 5000}
        )
        assert response.status_code == 422

    def test_me_endpoint_requires_authentication(self, client):
        response = client.get("/api/v1/users/me/activity-heatmap")
        assert response.status_code in (401, 403)

    def test_heatmap_for_a_real_user(self, client, register_and_login):
        register_and_login("heatmap@example.com", "heatmapuser")

        response = client.get(
            "/api/v1/users/heatmapuser/activity-heatmap", params={"days": 30}
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["username"] == "heatmapuser"
        assert len(payload["days"]) == 30
        assert payload["streak"]["total_days"] == 30
        assert all(day["level"] == 0 or day["count"] > 0 for day in payload["days"])
