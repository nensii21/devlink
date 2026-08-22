"""
Which stored preference gates which notification.

`notification_preferences` has seventeen columns. The dispatcher used to read
four of them with an `if` chain, and everything the chain did not name fell
through to `return True` -- so nine of the fifteen notification types were
undeniable, and turning off "email me about messages" did nothing at all
(#1247).

The `if` chain was not the problem so much as its default. A type that nobody
remembered to add was silently delivered, and there was no place where the
omission was visible. This module is that place: every `NotificationType` has
a row in `CATEGORY_BY_TYPE`, and a type without one raises in the tests rather
than quietly defaulting to "send it".

Three buckets, because "gated by a preference" is not the only honest answer:

* **gated** -- the type belongs to a category the user can switch off;
* **always delivered** -- password resets and security alerts, which are not
  marketing and should not be suppressible by a checkbox;
* **ungated** -- there is no column for it. Currently just ``FOLLOW``. Adding
  one means a migration and a settings row, so it is recorded here as a known
  gap instead of being mapped to whichever category looks closest.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.notification import NotificationType


@dataclass(frozen=True)
class Category:
    """
    One row of the notification settings page.

    ``enabled_field`` is the master switch for the category and
    ``email_field`` is its per-channel one. ``legacy_fields`` are older columns
    that mean the same thing and are still set on rows written before #586 --
    see :func:`category_enabled` for how they combine.
    """

    name: str
    enabled_field: str
    email_field: str | None = None
    legacy_fields: tuple[str, ...] = ()


MESSAGES = Category("messages", "messages", "email_messages")
MENTIONS = Category("mentions", "mentions", "email_mentions")
TEAM_INVITATIONS = Category(
    "team_invitations",
    "team_invitations",
    "email_team_invitations",
    legacy_fields=("invitations",),
)
PROJECT_UPDATES = Category(
    "project_updates", "project_updates", "email_project_updates"
)
SYSTEM_ANNOUNCEMENTS = Category(
    "system_announcements",
    "system_announcements",
    "email_system_announcements",
    legacy_fields=("system_alerts",),
)
ROLE_CHANGES = Category("role_changes", "role_changes")

#: Every notification type that a preference can switch off.
#:
#: The enum has fifteen members and the model has six categories, so some of
#: these are judgement calls rather than obvious pairings -- application
#: outcomes and builder flares are filed under project activity, and the AI
#: notifications under system announcements. Named explicitly so they can be
#: argued with.
CATEGORY_BY_TYPE: dict[NotificationType, Category] = {
    NotificationType.MESSAGE: MESSAGES,
    NotificationType.MENTION: MENTIONS,
    NotificationType.PROJECT_INVITE: TEAM_INVITATIONS,
    NotificationType.PROJECT_UPDATE: PROJECT_UPDATES,
    NotificationType.APPLICATION: PROJECT_UPDATES,
    NotificationType.APPLICATION_ACCEPTED: PROJECT_UPDATES,
    NotificationType.APPLICATION_REJECTED: PROJECT_UPDATES,
    NotificationType.BUILDER_FLARE: PROJECT_UPDATES,
    NotificationType.ROLE_CHANGE: ROLE_CHANGES,
    NotificationType.SYSTEM: SYSTEM_ANNOUNCEMENTS,
    NotificationType.WELCOME: SYSTEM_ANNOUNCEMENTS,
    NotificationType.AI: SYSTEM_ANNOUNCEMENTS,
}

#: Delivered whatever the preferences say.
#:
#: `PASSWORD_RESET` used to sit under `system_alerts`, which meant a user who
#: switched off system alerts stopped being told their password had been reset.
#: That is the notification you least want suppressed, and the same goes for
#: `SECURITY_ALERT`.
ALWAYS_DELIVERED: frozenset[NotificationType] = frozenset(
    {
        NotificationType.PASSWORD_RESET,
        NotificationType.SECURITY_ALERT,
    }
)

#: Types with no matching column. A known gap, not a decision.
#:
#: `FOLLOW` has no preference anywhere in the model, so there is nothing to
#: read. Mapping it to a neighbouring category would mean somebody's "project
#: updates" switch silently also controls follows. It stays ungated, and this
#: set is what makes that visible.
UNGATED: frozenset[NotificationType] = frozenset({NotificationType.FOLLOW})


def _flag(prefs, field: str, default: bool = True) -> bool:
    """Read a boolean column, tolerating a preference row that predates it."""
    value = getattr(prefs, field, None)
    return default if value is None else bool(value)


def category_for(notification_type: NotificationType) -> Category | None:
    """The category gating this type, or ``None`` if it is not gated."""
    return CATEGORY_BY_TYPE.get(notification_type)


def category_enabled(category: Category, prefs) -> bool:
    """
    Whether the user wants this category at all.

    A category is on only if its own field **and** every legacy alias are on.

    That is an ``and``, deliberately, and it is the opposite of what the old
    code did -- it joined `project_updates` and `invitations` with ``or``, so
    neither switch did anything on its own and the pair was off only when both
    were. Two rows in Settings that only worked as one.

    Every column defaults to ``True``, so a row written before #586 that opted
    out via `invitations` still has `team_invitations=True`. Honouring the
    legacy opt-out therefore means treating any ``False`` as a no.
    """
    if not _flag(prefs, category.enabled_field):
        return False
    return all(_flag(prefs, field) for field in category.legacy_fields)


def should_deliver(notification_type: NotificationType, prefs) -> bool:
    """Whether this notification should be delivered on any channel."""
    if notification_type in ALWAYS_DELIVERED or notification_type in UNGATED:
        return True

    category = category_for(notification_type)
    if category is None:
        # Fail open. A type nobody mapped is a bug, and dropping a user's
        # notifications is a worse way to find out about it than delivering
        # one too many -- `test_every_notification_type_is_accounted_for`
        # turns it red in CI instead.
        return True

    return category_enabled(category, prefs)


def should_deliver_by_email(notification_type: NotificationType, prefs) -> bool:
    """
    Whether the *email* channel should carry this notification.

    Assumes :func:`should_deliver` has already passed; this is the second,
    per-channel gate that the dispatcher never had. `email_enabled` is the
    master switch and stays with the dispatcher's channel check -- what is new
    here is the per-category one underneath it.
    """
    if notification_type in ALWAYS_DELIVERED:
        return True

    category = category_for(notification_type)
    if category is None or category.email_field is None:
        # `role_changes` genuinely has no email column; it follows the global
        # email switch alone.
        return True

    return _flag(prefs, category.email_field)
