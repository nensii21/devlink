from __future__ import annotations

from app.models.user import User

from app.models.notification import NotificationType
from app.schemas.notification import NotificationCreate
from app.schemas.project import ProjectCreate
from app.models.project import ProjectStage, ProjectVisibility
from app.services.daily_digest_service import DailyDigestService
from app.services.notification_service import NotificationService
from app.services.project_service import ProjectService


def _create_user(db, email: str, username: str) -> User:
    user = User(
        email=email,
        username=username,
        first_name=username.capitalize(),
        last_name="Test",
        password_hash="fakehash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# reuse TestingSessionLocal and _create_user from this test file
def test_generate_empty_daily_digest(db):

    user = _create_user(db, "digest@example.com", "digestuser")

    digest = DailyDigestService.generate_daily_digest(
        db=db,
        recipient_id=user.id,
    )

    assert digest.new_projects == []
    assert digest.project_invitations == []
    assert digest.messages == []
    assert digest.notifications == []


def test_daily_digest_contains_new_project(db):

    owner = _create_user(db, "owner@example.com", "owner")

    from app.models.project import Project

    project = Project(
        owner_id=owner.id,
        title="Digest Project",
        slug="digest-project",
        description="Testing",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    digest = DailyDigestService.generate_daily_digest(
        db=db,
        recipient_id=owner.id,
    )

    assert len(digest.new_projects) == 1
    assert digest.new_projects[0].title == project.title


def test_daily_digest_contains_project_invitation(db):

    user = _create_user(db, "invite@example.com", "inviteuser")

    NotificationService.create_notification(
        db=db,
        recipient_id=user.id,
        sender_id=None,
        notification=NotificationCreate(
            recipient_id=user.id,
            type=NotificationType.PROJECT_INVITE,
            title="Invite",
            message="Join project",
        ),
    )

    digest = DailyDigestService.generate_daily_digest(
        db=db,
        recipient_id=user.id,
    )

    assert len(digest.project_invitations) == 1
    assert digest.project_invitations[0].title == "Invite"
    assert digest.messages == []


def test_daily_digest_handles_timezone_aware_created_at(db):
    """Regression: the digest crashed on Postgres for as long as it ran.

    `Notification.created_at` is declared `DateTime(timezone=True)`, so
    Postgres hands back an aware value. The cutoff was built with
    `datetime.utcnow()`, which is naive, and the comparison between the two
    raised:

        TypeError: can't compare offset-naive and offset-aware datetimes

    The existing tests never caught it because SQLite returns naive datetimes,
    so both sides happened to match. This test forces the aware case.
    """
    from datetime import datetime, timedelta, timezone

    user = _create_user(db, "aware@example.com", "awareuser")

    notification = NotificationService.create_notification(
        db=db,
        recipient_id=user.id,
        sender_id=None,
        notification=NotificationCreate(
            recipient_id=user.id,
            type=NotificationType.PROJECT_INVITE,
            title="Aware invite",
            message="Join project",
        ),
    )

    # What Postgres would have returned all along.
    notification.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.flush()

    digest = DailyDigestService.generate_daily_digest(
        db=db,
        recipient_id=user.id,
    )

    assert len(digest.project_invitations) == 1
    assert digest.project_invitations[0].title == "Aware invite"
