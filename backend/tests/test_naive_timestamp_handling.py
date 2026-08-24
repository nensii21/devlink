"""
Naive datetimes and the columns that are not (#1318).

Every timestamp column in this app is `DateTime(timezone=True)`, and
`app/utils/time.py` exists so nothing naive gets near one. Two things kept
getting past that:

* `datetime.utcnow()` came back into the announcement services, where it is
  used as the *bound parameter* of a window query. Postgres reads a naive
  parameter in the session time zone rather than as UTC, so the window moves by
  the deployment's offset -- silently, with no error anywhere.
* the expiry comparisons in `auth_service` were written three different ways,
  and two of the three raised `TypeError` on a stored value that came back
  naive, turning "your reset link has expired" into a 500.

`tests/test_utc_time.py` covers the helpers themselves. This covers the call
sites that were getting it wrong.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.global_announcement import (
    AnnouncementSeverity,
    GlobalAnnouncement,
    TargetAudience,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.feature_announcement import FeatureAnnouncementCreate
from app.services.feature_announcement_service import FeatureAnnouncementService
from app.services.global_announcement_service import GlobalAnnouncementService
from app.utils.time import ensure_utc, is_expired, utcnow

IST = timezone(timedelta(hours=5, minutes=30))


def _admin(db, username: str = "admin") -> User:
    user = User(
        first_name="Ada",
        last_name="Admin",
        username=username,
        email=f"{username}@example.com",
        password_hash="hashed",
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _announcement(db, admin, *, start, end=None, title="Notice") -> GlobalAnnouncement:
    row = GlobalAnnouncement(
        created_by_id=admin.id,
        title=title,
        content="body",
        severity=AnnouncementSeverity.INFO,
        target_audience=TargetAudience.ALL,
        start_date=start,
        end_date=end,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ---------------------------------------------------------------------------
# The clock the window query is compared against
# ---------------------------------------------------------------------------


class TestGlobalAnnouncementWindow:
    def test_a_live_announcement_is_returned(self, db):
        admin = _admin(db)
        _announcement(
            db,
            admin,
            start=utcnow() - timedelta(hours=1),
            end=utcnow() + timedelta(hours=1),
        )

        found = GlobalAnnouncementService.get_active_announcements_for_user(db)

        assert [row.title for row in found] == ["Notice"]

    def test_one_that_has_not_started_is_not(self, db):
        admin = _admin(db)
        _announcement(db, admin, start=utcnow() + timedelta(hours=1))

        assert GlobalAnnouncementService.get_active_announcements_for_user(db) == []

    def test_one_that_has_finished_is_not(self, db):
        admin = _admin(db)
        _announcement(
            db,
            admin,
            start=utcnow() - timedelta(days=2),
            end=utcnow() - timedelta(days=1),
        )

        assert GlobalAnnouncementService.get_active_announcements_for_user(db) == []

    def test_no_end_date_means_no_end(self, db):
        admin = _admin(db)
        _announcement(db, admin, start=utcnow() - timedelta(days=30))

        assert len(GlobalAnnouncementService.get_active_announcements_for_user(db)) == 1

    def test_the_query_is_compared_against_the_shared_clock(self, db, monkeypatch):
        """
        The bound parameter comes from `utils.time.utcnow`, not from a naive
        `datetime.utcnow()` the module reached for itself.

        Pinned by moving the clock rather than by inspecting the parameter:
        with the clock a year forward, an announcement whose window closed
        yesterday is still shut and one that opens next week is now open.
        """
        admin = _admin(db)
        next_year = utcnow() + timedelta(days=365)
        monkeypatch.setattr(
            "app.services.global_announcement_service.utcnow", lambda: next_year
        )

        _announcement(
            db,
            admin,
            start=utcnow() + timedelta(days=7),
            end=utcnow() + timedelta(days=400),
            title="opens next week",
        )
        _announcement(
            db,
            admin,
            start=utcnow() - timedelta(days=2),
            end=utcnow() - timedelta(days=1),
            title="closed yesterday",
        )

        found = GlobalAnnouncementService.get_active_announcements_for_user(db)

        assert [row.title for row in found] == ["opens next week"]

    @pytest.mark.parametrize("minutes", [1, 30, 90, 5 * 60 + 29])
    def test_the_boundary_does_not_move_by_a_utc_offset(self, db, minutes):
        """
        The failure mode a naive `utcnow()` produces, at the sizes that matter.

        A window that ended `minutes` ago must stay closed, and one starting in
        `minutes` must stay shut. Compared against a clock read in, say,
        Asia/Kolkata, anything inside 5h30m flips -- which is exactly the range
        an announcement's edges live in.
        """
        admin = _admin(db)
        _announcement(
            db,
            admin,
            start=utcnow() - timedelta(days=1),
            end=utcnow() - timedelta(minutes=minutes),
            title="ended",
        )
        _announcement(
            db,
            admin,
            start=utcnow() + timedelta(minutes=minutes),
            title="not yet",
        )

        assert GlobalAnnouncementService.get_active_announcements_for_user(db) == []


class TestFeatureAnnouncementPublishedAt:
    """
    An announcement created without an explicit timestamp gets one from the
    service, and `published_at` is `DateTime(timezone=True)`.

    Asserted by substituting the clock rather than by inspecting `tzinfo` on the
    way back out. SQLite does not round-trip `tzinfo` at all, so a returned
    naive value says nothing about what was written -- and it was the *write*
    that was wrong. If the service goes back to calling `datetime.utcnow()`
    directly, the substituted clock is never consulted and these fail.
    """

    FIXED = datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc)

    def test_an_implicit_publish_time_comes_from_the_shared_clock(
        self, db, monkeypatch
    ):
        admin = _admin(db)
        monkeypatch.setattr(
            "app.services.feature_announcement_service.utcnow",
            lambda: self.FIXED,
        )

        row = FeatureAnnouncementService.create_announcement(
            db,
            admin.id,
            FeatureAnnouncementCreate(
                title="Shipped",
                summary="Something new",
                content="Details",
            ),
        )

        assert ensure_utc(row.published_at) == self.FIXED

    def test_an_explicit_publish_time_is_kept(self, db, monkeypatch):
        admin = _admin(db)
        when = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)
        monkeypatch.setattr(
            "app.services.feature_announcement_service.utcnow",
            lambda: self.FIXED,
        )

        row = FeatureAnnouncementService.create_announcement(
            db,
            admin.id,
            FeatureAnnouncementCreate(
                title="Backdated",
                summary="Something older",
                content="Details",
                published_at=when,
            ),
        )

        assert ensure_utc(row.published_at) == when


# ---------------------------------------------------------------------------
# Expiry comparisons
# ---------------------------------------------------------------------------


def _reset_token(db, user, expires_at) -> PasswordResetToken:
    token = PasswordResetToken(
        user_id=user.id,
        jti=str(uuid.uuid4()),
        token_hash=uuid.uuid4().hex,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


class TestExpiryComparisons:
    """
    The three call sites in `auth_service` now ask one question through one
    helper. These pin the answers the helper has to give for the rows those
    sites actually see.
    """

    def test_a_naive_stored_value_does_not_raise(self, db):
        """
        The comparison that produced a 500 on `/api/auth/verify-recovery-token`.

        A naive value is what a row written before the cleanup holds, and what
        any backend that does not round-trip tzinfo hands back.
        """
        naive_past = datetime.utcnow() - timedelta(minutes=1)  # noqa: DTZ003

        assert is_expired(naive_past) is True

    def test_a_naive_future_value_is_not_expired(self):
        naive_future = datetime.utcnow() + timedelta(minutes=15)  # noqa: DTZ003

        assert is_expired(naive_future) is False

    def test_an_aware_value_in_another_zone_is_compared_as_the_same_instant(self):
        # One minute in the future, expressed in IST.
        future_ist = (utcnow() + timedelta(minutes=1)).astimezone(IST)

        assert is_expired(future_ist) is False

    def test_a_null_expiry_means_no_expiry(self):
        assert is_expired(None) is False

    def test_a_reset_token_read_back_from_the_database_can_be_compared(self, db):
        """
        End to end through a real column, which is where the naive value comes
        from in the first place.
        """
        user = _admin(db, "resetuser")
        token = _reset_token(db, user, utcnow() + timedelta(minutes=15))
        db.expire_all()

        stored = db.get(PasswordResetToken, token.id)

        assert is_expired(stored.expires_at) is False

    def test_an_expired_reset_token_read_back_is_expired(self, db):
        user = _admin(db, "resetuser2")
        token = _reset_token(db, user, utcnow() - timedelta(minutes=1))
        db.expire_all()

        stored = db.get(PasswordResetToken, token.id)

        assert is_expired(stored.expires_at) is True

    def test_a_refresh_token_read_back_can_be_compared(self, db):
        """
        The third site. It normalised by hand and was therefore already
        correct; routing it through the helper is about there being one answer
        rather than three spellings of it.
        """
        user = _admin(db, "refreshuser")
        row = RefreshToken(
            user_id=user.id,
            token=uuid.uuid4().hex,
            expires_at=utcnow() + timedelta(days=7),
        )
        db.add(row)
        db.commit()
        db.expire_all()

        stored = db.get(RefreshToken, row.id)

        assert is_expired(stored.expires_at) is False
