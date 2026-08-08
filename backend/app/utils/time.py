"""Timezone-aware UTC helpers.

Every timestamp column in the app is declared `DateTime(timezone=True)`, so
every value written to one should be timezone-aware UTC. Most of the code
already does that with `datetime.now(timezone.utc)`; a handful of call sites
used `datetime.utcnow()`, which returns a *naive* datetime, and mixing the two
fails in two different ways:

  * Comparing them raises `TypeError: can't compare offset-naive and
    offset-aware datetimes`.
  * Writing a naive value into a `TIMESTAMP WITH TIME ZONE` column makes the
    driver interpret it in the session time zone rather than UTC. On any
    deployment whose session is not UTC the stored instant is silently wrong.

`datetime.utcnow()` is also deprecated as of Python 3.12, which is the version
this project targets.

Prefer `utcnow()` from this module over calling `datetime.now(timezone.utc)`
inline: it is shorter, it is greppable, and it gives tests a single place to
freeze.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

__all__ = [
    "ensure_utc",
    "is_expired",
    "isoformat_utc",
    "utc_from_timestamp",
    "utcnow",
]


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime.

    The replacement for `datetime.utcnow()`, which returns a naive value and is
    deprecated in Python 3.12.
    """
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | None) -> datetime | None:
    """Return `value` as timezone-aware UTC, or None if it was None.

    A naive input is *assumed* to already be UTC and is tagged as such, which
    matches how the naive values in the database were written. An aware input
    in another zone is converted.

    This is the function to reach for when handling a datetime that may have
    come from an older row, an external API, or a client payload -- anywhere
    the tzinfo is not guaranteed.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def isoformat_utc(value: datetime | None) -> str | None:
    """Serialise a datetime as an ISO 8601 UTC string, or None.

    Normalises first, so a naive value does not serialise without an offset and
    leave the consumer guessing.
    """
    normalised = ensure_utc(value)

    return None if normalised is None else normalised.isoformat()


def utc_from_timestamp(seconds: float) -> datetime:
    """Convert a POSIX timestamp to a timezone-aware UTC datetime.

    `datetime.utcfromtimestamp()` is deprecated alongside `utcnow()` and has
    the same naive-return problem.
    """
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def is_expired(expires_at: datetime | None, *, leeway: timedelta | None = None) -> bool:
    """Return True when `expires_at` is in the past.

    Normalises the input, so this is safe against rows written before the
    naive/aware mix was cleaned up -- the comparison that used to raise
    `TypeError` now just works.

    A None `expires_at` means "no expiry" and returns False. `leeway` treats a
    token as expired that many seconds early, which is the usual way to absorb
    clock skew between the app and the database.
    """
    if expires_at is None:
        return False

    deadline = ensure_utc(expires_at)
    assert deadline is not None  # narrowed by the None check above

    if leeway is not None:
        deadline -= leeway

    return utcnow() >= deadline
