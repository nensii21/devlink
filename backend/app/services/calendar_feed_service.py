"""
Building the calendar feed and the token that guards it.

Two shapes, because they solve different problems:

* a **single-event download**, which works offline, works when the user is not
  signed in on their phone, and creates no ongoing relationship with us
* a **subscribable feed**, which the user pastes into their calendar client
  once and then forgets about

The feed is the one people actually want, and it is also the awkward one.
Calendar clients do not do OAuth; they do "GET this URL, forever, with no
headers I control". So the feed cannot use a session cookie or a bearer token
-- it needs a secret that lives in the URL.

That secret is generated here. It is:

* **scoped** -- it authenticates nothing except the calendar feed, so a leaked
  feed URL exposes the user's hackathon and milestone titles and nothing else
* **stateless** -- an HMAC over the user id and an issue timestamp, so no new
  table and no migration
* **expiring** -- a year by default, so an abandoned URL does not work forever

The trade-off in being stateless is that a *specific* leaked token cannot be
revoked on its own; see :func:`rotate_all_feed_tokens` for what can be done
instead, and ``docs/calendar_feeds.md`` for the follow-up that would fix it.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.hackathon import Hackathon
from app.models.hackathon_registration import HackathonRegistration
from app.models.milestone import Milestone
from app.models.project_member import ProjectMember
from app.utils.ics import Alarm, Calendar, Event

logger = logging.getLogger(__name__)

TOKEN_VERSION = "v1"

# A hackathon that ended two years ago is not something anybody wants filling
# their calendar. Feeds are a rolling window, not an archive.
FEED_LOOKBACK_DAYS = 90
FEED_LOOKAHEAD_DAYS = 365

# Remind people the day before a milestone is due and an hour before a
# hackathon starts. The asymmetry is deliberate: a deadline needs warning, an
# event needs a nudge.
MILESTONE_ALARM_MINUTES = 24 * 60
HACKATHON_ALARM_MINUTES = 60


class InvalidFeedToken(ValueError):
    """Raised when a feed token is missing, malformed, expired or forged."""


# ----------------------------------------------------------------------
# Tokens
# ----------------------------------------------------------------------


def _signing_key() -> bytes:
    """
    The key feed tokens are signed with.

    Derived from ``SECRET_KEY`` and a feed-specific salt rather than using
    ``SECRET_KEY`` directly, so that a feed token can never be confused with a
    session token even if one of the formats changes later.
    """
    # lgtm[py/weak-sensitive-data-hashing]
    return hashlib.sha256(
        f"{settings.SECRET_KEY}:{settings.CALENDAR_FEED_TOKEN_SALT}".encode("utf-8")
    ).digest()


def _b64(raw: bytes) -> str:
    """URL-safe base64 with the padding stripped, so it is clean in a URL."""
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def generate_feed_token(user_id: uuid.UUID, *, issued_at: datetime = None) -> str:
    """
    Mint a feed token for a user.

    Format: ``v1.<user-id>.<issued-at>.<signature>``. Everything but the
    signature is readable, which is fine -- the token proves possession, it does
    not hide anything.
    """
    issued_at = issued_at or datetime.now(timezone.utc)
    payload = f"{TOKEN_VERSION}.{_b64(user_id.bytes)}.{int(issued_at.timestamp())}"

    signature = hmac.new(
        _signing_key(),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return f"{payload}.{_b64(signature)}"


def parse_feed_token(token: str) -> uuid.UUID:
    """
    Verify a feed token and return the user it belongs to.

    Raises :class:`InvalidFeedToken` for anything that is not a currently valid
    token. The caller should answer 404 rather than 401 -- an unauthenticated
    URL that says "wrong token" is an oracle for guessing them, and a calendar
    client cannot act on a 401 anyway.
    """
    if not token:
        raise InvalidFeedToken("No feed token supplied.")

    parts = token.split(".")
    if len(parts) != 4:
        raise InvalidFeedToken("Malformed feed token.")

    version, encoded_id, issued_str, encoded_signature = parts

    if version != TOKEN_VERSION:
        raise InvalidFeedToken("Unsupported feed token version.")

    payload = f"{version}.{encoded_id}.{issued_str}"
    expected = hmac.new(
        _signing_key(),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    try:
        provided = _unb64(encoded_signature)
    except (ValueError, TypeError) as exc:
        raise InvalidFeedToken("Malformed feed token.") from exc

    # Constant time, so the comparison does not leak how much of a guessed
    # signature was right.
    if not hmac.compare_digest(expected, provided):
        raise InvalidFeedToken("Feed token signature does not match.")

    try:
        issued_at = datetime.fromtimestamp(int(issued_str), tz=timezone.utc)
    except (ValueError, OverflowError, OSError) as exc:
        raise InvalidFeedToken("Malformed feed token.") from exc

    max_age = timedelta(days=settings.CALENDAR_FEED_TOKEN_MAX_AGE_DAYS)
    if datetime.now(timezone.utc) - issued_at > max_age:
        raise InvalidFeedToken("Feed token has expired.")

    try:
        return uuid.UUID(bytes=_unb64(encoded_id))
    except (ValueError, TypeError) as exc:
        raise InvalidFeedToken("Malformed feed token.") from exc


def rotate_all_feed_tokens() -> None:
    """
    Documentation, not code.

    Because tokens are stateless there is nothing to delete. Every issued feed
    URL is invalidated at once by changing ``CALENDAR_FEED_TOKEN_SALT`` and
    restarting. That is the blunt instrument; per-user revocation needs a table
    to revoke against.
    """
    raise NotImplementedError(
        "Feed tokens are stateless. Rotate CALENDAR_FEED_TOKEN_SALT to "
        "invalidate every issued feed URL."
    )


# ----------------------------------------------------------------------
# Building the calendar
# ----------------------------------------------------------------------


class CalendarFeedService:
    """Collects a user's dated items and renders them as iCalendar."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -- Collection ----------------------------------------------------

    def hackathons_for(self, user_id: uuid.UUID) -> Sequence[Hackathon]:
        """
        Hackathons the user has registered for, within the feed window.

        Only registered ones: a feed of every hackathon on the platform is a
        newsletter, not a calendar.
        """
        now = datetime.now(timezone.utc)

        return (
            self.db.query(Hackathon)
            .join(
                HackathonRegistration,
                HackathonRegistration.hackathon_id == Hackathon.id,
            )
            .filter(HackathonRegistration.user_id == user_id)
            .filter(Hackathon.ends_at >= now - timedelta(days=FEED_LOOKBACK_DAYS))
            .filter(Hackathon.starts_at <= now + timedelta(days=FEED_LOOKAHEAD_DAYS))
            .order_by(Hackathon.starts_at)
            .all()
        )

    def milestones_for(self, user_id: uuid.UUID) -> Sequence[Milestone]:
        """
        Milestones on projects the user is an active member of.

        Completed and archived milestones are excluded -- a done deadline in a
        calendar is noise, and unlike the hackathon window there is no reason
        to keep it around for reference.
        """
        now = datetime.now(timezone.utc)

        return (
            self.db.query(Milestone)
            .join(ProjectMember, ProjectMember.project_id == Milestone.project_id)
            .filter(ProjectMember.user_id == user_id)
            .filter(ProjectMember.is_active.is_(True))
            .filter(Milestone.due_date.isnot(None))
            .filter(Milestone.is_completed.is_(False))
            .filter(Milestone.is_archived.is_(False))
            .filter(Milestone.due_date >= now - timedelta(days=FEED_LOOKBACK_DAYS))
            .filter(Milestone.due_date <= now + timedelta(days=FEED_LOOKAHEAD_DAYS))
            .order_by(Milestone.due_date)
            .all()
        )

    # -- Conversion ----------------------------------------------------

    @staticmethod
    def hackathon_event(hackathon: Hackathon) -> Event:
        """
        A hackathon as a single timed event spanning start to end.

        The UID is derived from the entity type and id and never changes, which
        is what lets a subscribed client update the event in place instead of
        creating a duplicate on every poll.
        """
        description_parts = [hackathon.description or ""]

        if hackathon.theme:
            description_parts.append(f"Theme: {hackathon.theme}")
        if hackathon.prize:
            description_parts.append(f"Prize: {hackathon.prize}")
        if hackathon.registration_ends_at:
            description_parts.append(
                "Registration closes: "
                f"{hackathon.registration_ends_at.strftime('%d %b %Y %H:%M UTC')}"
            )

        return Event(
            uid=f"hackathon-{hackathon.id}@devlink",
            summary=hackathon.name,
            description="\n\n".join(p for p in description_parts if p),
            starts_at=hackathon.starts_at,
            ends_at=hackathon.ends_at,
            url=hackathon.website_url,
            status=_ics_status(hackathon.status.value),
            created_at=hackathon.created_at,
            alarms=[
                Alarm(
                    minutes_before=HACKATHON_ALARM_MINUTES,
                    description=f"{hackathon.name} starts in an hour",
                )
            ],
        )

    @staticmethod
    def milestone_event(milestone: Milestone) -> Event:
        """
        A milestone as an all-day event on its due date.

        All-day rather than timed because a due date has no meaningful time of
        day; rendering it at midnight would put every deadline in the small
        hours of the client's display.
        """
        return Event(
            uid=f"milestone-{milestone.id}@devlink",
            summary=f"Due: {milestone.title}",
            description=milestone.description,
            starts_at=milestone.due_date,
            all_day=True,
            created_at=milestone.created_at,
            alarms=[
                Alarm(
                    minutes_before=MILESTONE_ALARM_MINUTES,
                    description=f"{milestone.title} is due tomorrow",
                )
            ],
        )

    # -- Rendering -----------------------------------------------------

    def build_feed(self, user_id: uuid.UUID) -> Calendar:
        """Everything dated for one user, as a calendar."""
        calendar = Calendar(
            name="DevLink",
            description="Your hackathons and project milestones.",
            refresh_minutes=settings.CALENDAR_FEED_REFRESH_MINUTES,
        )

        for hackathon in self.hackathons_for(user_id):
            calendar.add(self.hackathon_event(hackathon))

        for milestone in self.milestones_for(user_id):
            calendar.add(self.milestone_event(milestone))

        return calendar

    def render_feed(self, user_id: uuid.UUID) -> str:
        return self.build_feed(user_id).render()

    def render_hackathon(self, hackathon: Hackathon) -> str:
        calendar = Calendar(name=hackathon.name)
        calendar.add(self.hackathon_event(hackathon))
        return calendar.render()

    def render_milestone(self, milestone: Milestone) -> str:
        calendar = Calendar(name=milestone.title)
        calendar.add(self.milestone_event(milestone))
        return calendar.render()

    # -- Access checks -------------------------------------------------

    def can_read_hackathon(self, hackathon: Hackathon, user_id: uuid.UUID) -> bool:
        """
        Published hackathons are readable by anyone; drafts by their organiser.

        A registration also grants access, which matters for a hackathon that
        was published, taken back to draft, and still has people signed up.
        """
        if hackathon.is_published:
            return True
        if hackathon.created_by == user_id:
            return True

        return (
            self.db.query(HackathonRegistration)
            .filter(
                HackathonRegistration.hackathon_id == hackathon.id,
                HackathonRegistration.user_id == user_id,
            )
            .first()
            is not None
        )

    def can_read_milestone(self, milestone: Milestone, user_id: uuid.UUID) -> bool:
        """Milestones are visible to active members of their project."""
        return (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == milestone.project_id,
                ProjectMember.user_id == user_id,
                or_(
                    ProjectMember.is_active.is_(True),
                    ProjectMember.is_active.is_(None),
                ),
            )
            .first()
            is not None
        )


def _ics_status(status: str) -> Optional[str]:
    """
    Map our hackathon status onto the three values RFC 5545 allows.

    Anything we cannot map returns ``None`` and the property is omitted, which
    is better than emitting a value clients will reject.
    """
    if status == "cancelled":
        return "CANCELLED"
    if status == "draft":
        return "TENTATIVE"
    return "CONFIRMED"
