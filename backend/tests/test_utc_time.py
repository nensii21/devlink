"""Tests for app.utils.time and the naive/aware mixing it exists to prevent."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.utils.time import (
    ensure_utc,
    is_expired,
    isoformat_utc,
    utc_from_timestamp,
    utcnow,
)

IST = timezone(timedelta(hours=5, minutes=30))


class TestUtcnow:
    def test_returns_an_aware_datetime(self):
        now = utcnow()

        assert now.tzinfo is not None
        assert now.utcoffset() == timedelta(0)

    def test_is_comparable_with_other_aware_values(self):
        """The whole point: this is what `datetime.utcnow()` could not do."""
        earlier = utcnow() - timedelta(seconds=1)

        assert earlier < utcnow()

    def test_raises_when_compared_with_a_naive_value(self):
        """Documents the failure mode, so the contract stays deliberate.

        `utcnow()` is aware, and Python refuses to order an aware value against
        a naive one. Anything that still produces naive datetimes will fail
        loudly here rather than silently storing a shifted timestamp.
        """
        naive = datetime(2026, 1, 1, 12, 0, 0)

        with pytest.raises(TypeError, match="offset-naive and offset-aware"):
            _ = utcnow() < naive


class TestEnsureUtc:
    def test_none_passes_through(self):
        assert ensure_utc(None) is None

    def test_naive_is_tagged_as_utc_without_shifting_the_clock(self):
        naive = datetime(2026, 1, 1, 12, 0, 0)

        result = ensure_utc(naive)

        assert result is not None
        assert result.tzinfo == timezone.utc
        # Same wall clock, now labelled -- not converted.
        assert result.hour == 12
        assert result.replace(tzinfo=None) == naive

    def test_aware_utc_is_unchanged(self):
        aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        assert ensure_utc(aware) == aware

    def test_other_zone_is_converted(self):
        # 12:00 in IST is 06:30 UTC.
        in_ist = datetime(2026, 1, 1, 12, 0, 0, tzinfo=IST)

        result = ensure_utc(in_ist)

        assert result is not None
        assert result.tzinfo == timezone.utc
        assert (result.hour, result.minute) == (6, 30)

    def test_normalised_values_are_comparable(self):
        """A row written before the fix, next to one written after."""
        legacy_naive = datetime(2026, 1, 1, 12, 0, 0)
        current_aware = datetime(2026, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        assert ensure_utc(legacy_naive) < ensure_utc(current_aware)


class TestIsoformatUtc:
    def test_none_passes_through(self):
        assert isoformat_utc(None) is None

    def test_naive_serialises_with_an_explicit_offset(self):
        result = isoformat_utc(datetime(2026, 1, 1, 12, 0, 0))

        assert result == "2026-01-01T12:00:00+00:00"

    def test_other_zone_serialises_as_utc(self):
        result = isoformat_utc(datetime(2026, 1, 1, 12, 0, 0, tzinfo=IST))

        assert result == "2026-01-01T06:30:00+00:00"


class TestUtcFromTimestamp:
    def test_returns_an_aware_datetime(self):
        result = utc_from_timestamp(0)

        assert result.tzinfo == timezone.utc
        assert result == datetime(1970, 1, 1, tzinfo=timezone.utc)


class TestIsExpired:
    def test_none_means_no_expiry(self):
        assert is_expired(None) is False

    def test_past_is_expired(self):
        assert is_expired(utcnow() - timedelta(minutes=1)) is True

    def test_future_is_not_expired(self):
        assert is_expired(utcnow() + timedelta(minutes=1)) is False

    def test_naive_input_does_not_raise(self):
        """The comparison that used to raise TypeError on legacy rows."""
        naive_past = datetime.now() - timedelta(days=1)

        assert is_expired(naive_past) is True

    def test_leeway_expires_a_token_early(self):
        expires_soon = utcnow() + timedelta(seconds=30)

        assert is_expired(expires_soon) is False
        assert is_expired(expires_soon, leeway=timedelta(minutes=1)) is True


class TestNoNaiveUtcnowRemains:
    """Guard against the deprecated call coming back.

    A grep test is blunt, but it is the only thing that catches a
    `datetime.utcnow()` reintroduced in a service nobody has written a test
    for -- which is exactly how the eight original call sites accumulated.
    """

    def test_no_service_calls_datetime_utcnow(self):
        from pathlib import Path

        app_root = Path(__file__).resolve().parent.parent / "app"
        offenders = []

        for path in sorted(app_root.rglob("*.py")):
            # The helper module names the deprecated call in its docstring to
            # explain what it replaces.
            if path.name == "time.py" and path.parent.name == "utils":
                continue

            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if "datetime.utcnow()" in line or "datetime.utcfromtimestamp(" in line:
                    offenders.append(f"{path.relative_to(app_root.parent)}:{lineno}")

        assert not offenders, (
            "These call sites return naive datetimes and are deprecated in "
            f"Python 3.12: {offenders}. Use app.utils.time.utcnow() instead."
        )
