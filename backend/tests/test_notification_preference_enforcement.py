"""
The stored notification preferences are actually enforced.

Companion to `test_notification_preferences.py`, which covers the other half:
that the API stores what it is given and returns it. Those four tests pass on
`main` and always did -- which is exactly why this gap was invisible. Every
preference was written correctly, read back correctly, and rendered correctly.
Nothing asked whether the dispatcher consults them.

`notification_preferences` has seventeen columns. The dispatcher read four of
them, and everything its `if` chain did not name fell through to `return True`
(#1247). A user could switch a category off, reload the settings page, see it
off, and keep receiving the notifications.

Every test here asserts **both directions**. That is the whole discipline of
this file: an authorization-style change that only checks "off means silence"
passes just as well when the answer is silence for everybody, and turning off
notifications for people who want them is a worse bug than the one being
fixed.
"""

from __future__ import annotations

import uuid

import pytest

from app.models.notification import (
    Notification,
    NotificationPreference,
    NotificationType,
)
from app.models.user import User
from app.services.notifications import dispatcher
from app.services.notifications.preferences import (
    ALWAYS_DELIVERED,
    CATEGORY_BY_TYPE,
    UNGATED,
)

ALL_TYPES = list(NotificationType)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def make_recipient(db):
    """A user plus a preference row, with the given flags applied."""
    counter = {"n": 0}

    def _make(**flags):
        counter["n"] += 1
        n = counter["n"]
        user = User(
            id=uuid.uuid4(),
            email=f"pref{n}@example.com",
            username=f"prefuser{n}",
            first_name="Pref",
            last_name="User",
            password_hash="x_hashed",
        )
        db.add(user)
        db.commit()

        prefs = NotificationPreference(user_id=user.id)
        for field, value in flags.items():
            assert hasattr(prefs, field), f"no such preference column: {field}"
            setattr(prefs, field, value)
        db.add(prefs)
        db.commit()

        return user

    return _make


@pytest.fixture()
def emails_sent(monkeypatch):
    """Records every address the email channel tries to send to."""
    sent: list[str] = []

    def _capture(to_email, title, message, action_url=None):
        sent.append(to_email)
        return True

    monkeypatch.setattr(
        "app.services.email_service.EmailService.send_notification_email",
        staticmethod(_capture),
    )
    return sent


def _dispatch(db, user, n_type, channels=None):
    return dispatcher.dispatch(
        db=db,
        recipient_id=user.id,
        sender_id=None,
        notification_type=n_type,
        title="A title",
        message="A message",
        channels=channels,
    )


def _stored(db, user) -> int:
    return db.query(Notification).filter(Notification.recipient_id == user.id).count()


# ---------------------------------------------------------------------------
# The table covers the enum
# ---------------------------------------------------------------------------


def test_every_notification_type_is_accounted_for():
    """
    The test that keeps the fix from decaying back into the bug.

    `should_deliver` fails open for an unmapped type, on the grounds that
    dropping somebody's notifications is a bad way to discover a missing entry.
    That safety valve is only acceptable if something else is loud about it,
    and this is that something.
    """
    accounted = set(CATEGORY_BY_TYPE) | ALWAYS_DELIVERED | UNGATED
    missing = set(ALL_TYPES) - accounted

    assert missing == set(), (
        f"NotificationType members with no entry in preferences.py: "
        f"{sorted(t.value for t in missing)}. Add them to CATEGORY_BY_TYPE, or "
        "to ALWAYS_DELIVERED / UNGATED with a comment saying why they are not "
        "gated."
    )


def test_the_three_buckets_do_not_overlap():
    assert not (set(CATEGORY_BY_TYPE) & ALWAYS_DELIVERED)
    assert not (set(CATEGORY_BY_TYPE) & UNGATED)
    assert not (ALWAYS_DELIVERED & UNGATED)


# ---------------------------------------------------------------------------
# Off means off
# ---------------------------------------------------------------------------


GATED_CASES = sorted(
    ((n_type, category) for n_type, category in CATEGORY_BY_TYPE.items()),
    key=lambda pair: pair[0].value,
)
GATED_IDS = [f"{t.value}-{c.name}" for t, c in GATED_CASES]


@pytest.mark.parametrize("n_type,category", GATED_CASES, ids=GATED_IDS)
def test_disabling_the_category_stops_the_notification(
    db, make_recipient, n_type, category
):
    user = make_recipient(**{category.enabled_field: False})

    _dispatch(db, user, n_type)

    assert _stored(db, user) == 0, (
        f"{category.enabled_field}=False did not stop {n_type.value}"
    )


@pytest.mark.parametrize("n_type,category", GATED_CASES, ids=GATED_IDS)
def test_leaving_the_category_on_still_delivers(db, make_recipient, n_type, category):
    """
    The half that is easy to forget. Six of the twelve cases above pass
    trivially if the dispatcher stops delivering anything at all.
    """
    user = make_recipient()

    _dispatch(db, user, n_type)

    assert _stored(db, user) == 1, f"{n_type.value} was not delivered by default"


# ---------------------------------------------------------------------------
# The two toggles that were joined with `or`
# ---------------------------------------------------------------------------


def test_project_updates_and_invitations_are_independent(db, make_recipient):
    """
    The original read `prefs.project_updates or prefs.invitations` for both
    PROJECT_UPDATE and PROJECT_INVITE, so neither switch did anything alone and
    the pair was off only when both were.
    """
    no_updates = make_recipient(project_updates=False)
    _dispatch(db, no_updates, NotificationType.PROJECT_UPDATE)
    assert _stored(db, no_updates) == 0

    # ...and the same user still gets invitations.
    _dispatch(db, no_updates, NotificationType.PROJECT_INVITE)
    assert _stored(db, no_updates) == 1

    no_invites = make_recipient(team_invitations=False)
    _dispatch(db, no_invites, NotificationType.PROJECT_INVITE)
    assert _stored(db, no_invites) == 0

    _dispatch(db, no_invites, NotificationType.PROJECT_UPDATE)
    assert _stored(db, no_invites) == 1


# ---------------------------------------------------------------------------
# Per-category email
# ---------------------------------------------------------------------------


EMAIL_CASES = [
    (n_type, category)
    for n_type, category in GATED_CASES
    if category.email_field is not None
]
EMAIL_IDS = [f"{t.value}-{c.email_field}" for t, c in EMAIL_CASES]


@pytest.mark.parametrize("n_type,category", EMAIL_CASES, ids=EMAIL_IDS)
def test_disabling_category_email_stops_the_email_only(
    db, make_recipient, emails_sent, n_type, category
):
    """
    The five `email_*` columns were never read by anything. This is the
    behaviour the settings page has been offering and not delivering.
    """
    user = make_recipient(**{category.email_field: False})

    _dispatch(db, user, n_type)

    assert emails_sent == [], f"{category.email_field}=False still sent an email"
    assert _stored(db, user) == 1, "the in-app notification should be unaffected"


@pytest.mark.parametrize("n_type,category", EMAIL_CASES, ids=EMAIL_IDS)
def test_category_email_on_by_default_sends(
    db, make_recipient, emails_sent, n_type, category
):
    user = make_recipient()

    _dispatch(db, user, n_type)

    assert emails_sent == [user.email]


def test_the_global_email_switch_still_wins(db, make_recipient, emails_sent):
    """
    `email_enabled` is the master switch and sits above the per-category ones.
    """
    user = make_recipient(email_enabled=False, email_messages=True)

    _dispatch(db, user, NotificationType.MESSAGE)

    assert emails_sent == []
    assert _stored(db, user) == 1


def test_disabling_the_category_stops_the_email_too(db, make_recipient, emails_sent):
    """
    Turning off the category, not just its email row, should not leave email
    running -- the per-channel gate is underneath the category gate, not
    beside it.
    """
    user = make_recipient(messages=False, email_messages=True)

    _dispatch(db, user, NotificationType.MESSAGE)

    assert emails_sent == []
    assert _stored(db, user) == 0


def test_role_changes_have_no_email_column_and_follow_the_global_switch(
    db, make_recipient, emails_sent
):
    """
    `role_changes` is the one gated category with no `email_role_changes`.
    Rather than invent one, it follows `email_enabled` alone -- asserted so the
    asymmetry is deliberate rather than an oversight.
    """
    user = make_recipient()
    _dispatch(db, user, NotificationType.ROLE_CHANGE)
    assert emails_sent == [user.email]

    silent = make_recipient(email_enabled=False)
    _dispatch(db, silent, NotificationType.ROLE_CHANGE)
    assert emails_sent == [user.email]  # unchanged


# ---------------------------------------------------------------------------
# Legacy column names
# ---------------------------------------------------------------------------


def test_the_legacy_invitations_column_still_opts_out(db, make_recipient):
    """
    #586 renamed `invitations` to `team_invitations` and left both columns on
    the model. Every column defaults to True, so a row written before the
    rename that opted out via `invitations` has `team_invitations=True` -- and
    reading only the new name would silently re-enable it.
    """
    user = make_recipient(invitations=False)  # team_invitations left at default

    _dispatch(db, user, NotificationType.PROJECT_INVITE)

    assert _stored(db, user) == 0


def test_the_legacy_system_alerts_column_still_opts_out(db, make_recipient):
    user = make_recipient(system_alerts=False)

    _dispatch(db, user, NotificationType.SYSTEM)

    assert _stored(db, user) == 0


def test_a_legacy_opt_in_does_not_override_a_new_opt_out(db, make_recipient):
    """
    The combination is `and`, not "prefer the newer column". Both mean the same
    thing, so either saying no is a no.
    """
    user = make_recipient(team_invitations=False, invitations=True)

    _dispatch(db, user, NotificationType.PROJECT_INVITE)

    assert _stored(db, user) == 0


# ---------------------------------------------------------------------------
# The notifications a preference must not silence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "n_type", sorted(ALWAYS_DELIVERED, key=lambda t: t.value), ids=lambda t: t.value
)
def test_security_notifications_survive_every_preference(db, make_recipient, n_type):
    """
    `PASSWORD_RESET` used to sit under `system_alerts`, so a user who switched
    off system alerts stopped being told their password had been reset. That is
    a behaviour change in this PR and it is deliberate.
    """
    user = make_recipient(
        messages=False,
        mentions=False,
        team_invitations=False,
        project_updates=False,
        system_announcements=False,
        system_alerts=False,
        invitations=False,
        role_changes=False,
    )

    _dispatch(db, user, n_type)

    assert _stored(db, user) == 1, f"{n_type.value} was suppressed by a preference"


def test_security_notifications_still_respect_the_channel_switches(
    db, make_recipient, emails_sent
):
    """
    Always-delivered is about *categories*, not channels. A user who has turned
    email off entirely should still not get email -- they will see it in-app.
    """
    user = make_recipient(email_enabled=False)

    _dispatch(db, user, NotificationType.SECURITY_ALERT)

    assert emails_sent == []
    assert _stored(db, user) == 1


@pytest.mark.parametrize(
    "n_type", sorted(UNGATED, key=lambda t: t.value), ids=lambda t: t.value
)
def test_ungated_types_are_delivered_and_that_is_a_known_gap(
    db, make_recipient, n_type
):
    """
    There is no preference column for FOLLOW, so it is delivered. Pinning it
    means the day someone adds one, this test fails and points at the place to
    wire it up -- rather than the column being added and silently ignored,
    which is how this issue started.
    """
    user = make_recipient(messages=False, project_updates=False)

    _dispatch(db, user, n_type)

    assert _stored(db, user) == 1


# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------


def test_the_database_channel_switch_is_respected(db, make_recipient):
    user = make_recipient(database_enabled=False)

    _dispatch(db, user, NotificationType.MESSAGE)

    assert _stored(db, user) == 0


def test_an_explicit_channel_list_still_honours_preferences(
    db, make_recipient, emails_sent
):
    """
    Callers can name channels explicitly. That should narrow what is sent, not
    bypass the user's settings.
    """
    user = make_recipient(email_messages=False)

    _dispatch(db, user, NotificationType.MESSAGE, channels=["email"])

    assert emails_sent == []
    assert _stored(db, user) == 0


def test_a_user_with_no_preference_row_gets_defaults(db, make_recipient):
    """
    `_get_user_preferences` creates a row on first dispatch. Everything defaults
    to on, so a brand new user receives notifications.
    """
    user = User(
        id=uuid.uuid4(),
        email="nodefaults@example.com",
        username="nodefaults",
        first_name="No",
        last_name="Prefs",
        password_hash="x_hashed",
    )
    db.add(user)
    db.commit()

    _dispatch(db, user, NotificationType.MESSAGE)

    assert _stored(db, user) == 1
