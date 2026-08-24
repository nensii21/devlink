from __future__ import annotations

"""
Contribution heatmap and streak calculation (#1040).

Everything here is *derived* from the existing ``activities`` table. Nothing new
is written when a user acts -- the feed rows we already record are the source of
truth, which means the heatmap is correct retroactively and can never drift out
of sync with the feed it summarises.
"""

import logging
import uuid
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity, ActivityType
from app.models.user import User
from app.schemas.activity_heatmap import (
    ActivityHeatmapResponse,
    ActivityTypeCount,
    HeatmapDay,
    StreakSummary,
)

logger = logging.getLogger(__name__)

# A year of squares is what the grid is designed around. 366 leaves room for a
# leap year without letting a caller ask for an unbounded scan.
DEFAULT_WINDOW_DAYS = 365
MAX_WINDOW_DAYS = 366
MIN_WINDOW_DAYS = 1


class ActivityHeatmapService:
    """Builds heatmap grids and streak summaries from activity rows."""

    # ------------------------------------------------------------------
    # Lookup & access control
    # ------------------------------------------------------------------

    @staticmethod
    def get_user_or_404(db: Session, username: str) -> User:
        stmt = select(User).where(User.username == username)
        user = db.scalar(stmt)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    @staticmethod
    def require_visible(subject: User, viewer: User | None, db: Session | None = None) -> None:
        """
        Check if the subject profile is private OR if their activity privacy settings
        restrict the viewer from viewing.
        """
        # 1. Profile visibility
        if subject.is_private:
            if viewer is None or viewer.id != subject.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this private profile.",
                )

        # 2. Activity visibility settings
        settings = subject.get_privacy_settings()
        activity_visibility = settings.get("activity", "public")

        is_visible = False
        if activity_visibility == "public":
            is_visible = True
        elif activity_visibility == "authenticated" and viewer is not None:
            is_visible = True
        elif activity_visibility == "followers" and viewer is not None and db is not None:
            if viewer.id == subject.id or getattr(viewer, "is_superuser", False):
                is_visible = True
            else:
                from app.services.follower_service import FollowerService
                is_visible = FollowerService.is_following(
                    db, follower_id=viewer.id, following_id=subject.id
                )
        elif activity_visibility == "private":
            if viewer is not None and (viewer.id == subject.id or getattr(viewer, "is_superuser", False)):
                is_visible = True

        if not is_visible:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user's activity details are private.",
            )

    # ------------------------------------------------------------------
    # Window helpers
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_window(days: int, today: date | None = None) -> tuple[date, date]:
        """
        Return the inclusive ``(start, end)`` calendar window for ``days``.

        ``days=1`` means "today only", so the window spans ``days - 1`` days
        backwards from today.
        """
        if days < MIN_WINDOW_DAYS or days > MAX_WINDOW_DAYS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"days must be between {MIN_WINDOW_DAYS} and {MAX_WINDOW_DAYS}",
            )
        end = today or datetime.now(timezone.utc).date()
        start = end - timedelta(days=days - 1)
        return start, end

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------

    @staticmethod
    def fetch_activity_days(
        db: Session,
        user_id: uuid.UUID,
        start: date,
        end: date,
        activity_types: Sequence[ActivityType] | None = None,
    ) -> list[tuple[date, str]]:
        """
        Fetch ``(utc_day, activity_type)`` pairs for the window.

        Bucketing happens in Python rather than via ``date_trunc`` on purpose:
        the two backends we run on (Postgres in production, SQLite under
        pytest) disagree about which timezone a timestamp-to-date cast uses,
        and a heatmap that silently shifts by one day per environment is worse
        than a slightly chattier query. The window is capped at 366 days for a
        single user, so the row count stays small.
        """
        window_start = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        # Exclusive upper bound at midnight after ``end``.
        window_end = datetime.combine(
            end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
        )

        stmt = select(Activity.created_at, Activity.activity_type).where(
            Activity.actor_id == user_id,
            Activity.created_at >= window_start,
            Activity.created_at < window_end,
        )
        if activity_types:
            stmt = stmt.where(Activity.activity_type.in_(list(activity_types)))

        rows: list[tuple[date, str]] = []
        for created_at, activity_type in db.execute(stmt).all():
            if created_at is None:
                continue
            # SQLite hands back naive datetimes; treat those as UTC, which is
            # what the writers store.
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            else:
                created_at = created_at.astimezone(timezone.utc)

            type_value = getattr(activity_type, "value", activity_type)
            rows.append((created_at.date(), str(type_value)))
        return rows

    # ------------------------------------------------------------------
    # Intensity levels
    # ------------------------------------------------------------------

    @staticmethod
    def compute_level_thresholds(counts: Iterable[int]) -> tuple[int, int, int]:
        """
        Derive the three cut points between levels 1-4 from the user's own
        distribution of active-day counts.

        Fixed thresholds (1/3/6/9, say) make a casual contributor's whole year
        look identical. Quartiles of the non-zero counts keep the gradient
        meaningful at any scale. Thresholds are clamped to be non-decreasing and
        at least 1, so a user whose every active day has exactly one activity
        still lands entirely on level 1 rather than splitting arbitrarily.
        """
        ordered = sorted(c for c in counts if c > 0)
        if not ordered:
            return (1, 2, 3)

        def percentile(fraction: float) -> int:
            if len(ordered) == 1:
                return ordered[0]
            index = int(round(fraction * (len(ordered) - 1)))
            return ordered[min(index, len(ordered) - 1)]

        t1 = max(1, percentile(0.25))
        t2 = max(t1, percentile(0.50))
        t3 = max(t2, percentile(0.75))
        return (t1, t2, t3)

    @staticmethod
    def level_for(count: int, thresholds: tuple[int, int, int]) -> int:
        if count <= 0:
            return 0
        t1, t2, t3 = thresholds
        if count <= t1:
            return 1
        if count <= t2:
            return 2
        if count <= t3:
            return 3
        return 4

    # ------------------------------------------------------------------
    # Streaks
    # ------------------------------------------------------------------

    @staticmethod
    def compute_current_streak(active_days: set[date], today: date) -> int:
        """
        Count back from ``today``. If today has no activity yet we anchor on
        yesterday instead -- otherwise every streak would read as broken until
        the user's first action of the day, which is both wrong and demoralising.
        """
        if today in active_days:
            cursor = today
        elif (today - timedelta(days=1)) in active_days:
            cursor = today - timedelta(days=1)
        else:
            return 0

        streak = 0
        while cursor in active_days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    @staticmethod
    def compute_longest_streak(
        active_days: set[date],
    ) -> tuple[int, date | None, date | None]:
        """Return ``(length, start, end)`` of the longest consecutive run."""
        if not active_days:
            return 0, None, None

        ordered = sorted(active_days)
        best_len = 1
        best_start = best_end = ordered[0]

        run_len = 1
        run_start = ordered[0]

        for previous, current in zip(ordered, ordered[1:]):
            if current - previous == timedelta(days=1):
                run_len += 1
            else:
                run_len = 1
                run_start = current

            if run_len > best_len:
                best_len = run_len
                best_start = run_start
                best_end = current

        return best_len, best_start, best_end

    # ------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------

    @staticmethod
    def build_summary(
        daily_counts: dict[date, int],
        start: date,
        end: date,
        today: date,
    ) -> StreakSummary:
        total_days = (end - start).days + 1
        active = {day for day, count in daily_counts.items() if count > 0}
        total_activities = sum(daily_counts.values())

        longest, longest_start, longest_end = (
            ActivityHeatmapService.compute_longest_streak(active)
        )

        busiest_day: date | None = None
        busiest_count = 0
        # Iterate in date order so ties resolve to the earliest day rather than
        # whatever the dict happens to yield.
        for day in sorted(daily_counts):
            count = daily_counts[day]
            if count > busiest_count:
                busiest_count = count
                busiest_day = day

        return StreakSummary(
            current_streak=ActivityHeatmapService.compute_current_streak(active, today),
            longest_streak=longest,
            longest_streak_start=longest_start,
            longest_streak_end=longest_end,
            total_activities=total_activities,
            active_days=len(active),
            total_days=total_days,
            busiest_day=busiest_day,
            busiest_day_count=busiest_count,
            daily_average=round(total_activities / total_days, 2)
            if total_days
            else 0.0,
            active_day_average=round(total_activities / len(active), 2)
            if active
            else 0.0,
        )

    @staticmethod
    def build(
        db: Session,
        subject: User,
        days: int = DEFAULT_WINDOW_DAYS,
        activity_types: Sequence[ActivityType] | None = None,
        today: date | None = None,
    ) -> ActivityHeatmapResponse:
        start, end = ActivityHeatmapService.resolve_window(days, today=today)
        reference_day = today or datetime.now(timezone.utc).date()

        rows = ActivityHeatmapService.fetch_activity_days(
            db,
            user_id=subject.id,
            start=start,
            end=end,
            activity_types=activity_types,
        )

        # Seed every day in the window so the grid has no holes.
        daily_counts: dict[date, int] = {}
        cursor = start
        while cursor <= end:
            daily_counts[cursor] = 0
            cursor += timedelta(days=1)

        type_counter: Counter[str] = Counter()
        for day, type_value in rows:
            if day in daily_counts:
                daily_counts[day] += 1
                type_counter[type_value] += 1

        thresholds = ActivityHeatmapService.compute_level_thresholds(
            daily_counts.values()
        )

        grid = [
            HeatmapDay(
                day=day,
                count=count,
                level=ActivityHeatmapService.level_for(count, thresholds),
            )
            for day, count in sorted(daily_counts.items())
        ]

        breakdown = [
            ActivityTypeCount(activity_type=type_value, count=count)
            # Sort by count descending, then name, so the order is stable.
            for type_value, count in sorted(
                type_counter.items(), key=lambda item: (-item[1], item[0])
            )
        ]

        return ActivityHeatmapResponse(
            user_id=subject.id,
            username=subject.username,
            start_date=start,
            end_date=end,
            days=grid,
            streak=ActivityHeatmapService.build_summary(
                daily_counts, start, end, reference_day
            ),
            breakdown=breakdown,
        )

    # ------------------------------------------------------------------
    # Query-string parsing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_activity_types(raw: str | None) -> list[ActivityType] | None:
        """
        Turn a comma-separated ``activity_types`` query value into enum members.

        An unknown name is a client bug, not something to silently drop -- a
        typo that quietly widens the result to "everything" is the kind of thing
        nobody notices until the numbers are wrong.
        """
        if not raw:
            return None

        parsed: list[ActivityType] = []
        for chunk in raw.split(","):
            name = chunk.strip()
            if not name:
                continue
            try:
                parsed.append(ActivityType(name))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Unknown activity type: {name}",
                )
        return parsed or None
