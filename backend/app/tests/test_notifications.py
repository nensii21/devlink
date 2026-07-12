# pyrefly: ignore [missing-import]
import pytest
import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy import and_, select
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient

from app.database.base import Base
from app.dependencies import get_database
from app.dependencies import get_current_user
from app.main import app

# Import all models to register on Base.metadata
from app.models.user import User
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.follower import Follower  # noqa: F401
from app.models.conversation import Conversation, ConversationType
from app.models.conversation_member import ConversationMember
from app.models.message import Message, MessageType  # noqa: F401
from app.models.notification import Notification, NotificationType  # noqa: F401
from app.models.application import Application, ApplicationStatus  # noqa: F401
from app.models.builder_flare import BuilderFlare, FlareStatus
from app.models.project_member import ProjectMember, MemberRole

from app.services.follower_service import FollowerService
from app.services.message_service import MessageService
from app.services.application_service import ApplicationService
from app.services.notification_service import NotificationService
from app.schemas.message import MessageCreate
from app.schemas.application import ApplicationCreate

# pyrefly: ignore [missing-import]
from sqlalchemy.pool import StaticPool

# Setup in-memory SQLite database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



@pytest.fixture(scope="function")
def db():
    # Recreate schema for clean database per test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_database] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def create_test_user(db, email, username):
    user = User(
        first_name="Test",
        last_name="User",
        username=username,
        email=email,
        password_hash="hashed_password",
        is_active=True,
        is_verified=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_project(db, owner_id):
    project = Project(
        owner_id=owner_id,
        title="Test Project",
        slug=f"test-project-{uuid.uuid4().hex[:6]}",
        description="A cool test project",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def test_follow_notification(db):
    user1 = create_test_user(db, "user1@example.com", "user1")
    user2 = create_test_user(db, "user2@example.com", "user2")

    # User 1 follows User 2
    FollowerService.follow_user(db, follower_id=user1.id, following_id=user2.id)

    # Check notification triggered
    notifications = NotificationService.list_notifications(db, recipient_id=user2.id)
    assert len(notifications) == 1
    notification = notifications[0]
    assert notification.type == NotificationType.FOLLOW
    assert notification.recipient_id == user2.id
    assert notification.sender_id == user1.id
    assert "started following you" in notification.message

    # Test duplicate prevention (sending again should reuse/update instead of creating new row)
    # We delete follower relationship first to allow refollow if needed, or trigger manually
    from app.schemas.notification import NotificationCreate
    notification_data = NotificationCreate(
        recipient_id=user2.id,
        type=NotificationType.FOLLOW,
        title="New Follower",
        message="Test User started following you."
    )
    NotificationService.create_notification(db, recipient_id=user2.id, sender_id=user1.id, notification=notification_data)
    
    notifications = NotificationService.list_notifications(db, recipient_id=user2.id)
    # Still only 1 unread follow notification
    assert len(notifications) == 1

def test_message_notification(db):
    user1 = create_test_user(db, "user1@example.com", "user1")
    user2 = create_test_user(db, "user2@example.com", "user2")

    # Create conversation and add members
    conv = Conversation(type=ConversationType.DIRECT, created_by=user1.id)
    db.add(conv)
    db.commit()
    db.refresh(conv)

    member1 = ConversationMember(conversation_id=conv.id, user_id=user1.id)
    member2 = ConversationMember(conversation_id=conv.id, user_id=user2.id)
    db.add_all([member1, member2])
    db.commit()

    # User 1 sends message to conversation
    msg_create = MessageCreate(content="Hello there!", type=MessageType.TEXT)
    MessageService.send_message(db, conversation_id=conv.id, sender_id=user1.id, message=msg_create)

    # User 2 should get notification, User 1 should not
    notif_user2 = NotificationService.list_notifications(db, recipient_id=user2.id)
    assert len(notif_user2) == 1
    assert notif_user2[0].type == NotificationType.MESSAGE
    assert notif_user2[0].sender_id == user1.id

    notif_user1 = NotificationService.list_notifications(db, recipient_id=user1.id)
    assert len(notif_user1) == 0

def test_application_notifications(db):
    owner = create_test_user(db, "owner@example.com", "owner")
    applicant = create_test_user(db, "applicant@example.com", "applicant")
    project = create_test_project(db, owner.id)

    flare = BuilderFlare(
        project_id=project.id,
        created_by=owner.id,
        title="Frontend Developer",
        description="Looking for react developer",
        role="Frontend",
        status=FlareStatus.OPEN
    )
    db.add(flare)
    db.commit()
    db.refresh(flare)

    # Applicant submits application
    app_create = ApplicationCreate(message="I want to join")
    application = ApplicationService.create_application(
        db, applicant_id=applicant.id, project_id=project.id, flare_id=flare.id, application=app_create
    )

    # Accept application
    ApplicationService.accept_application(db, application)
    notifs = NotificationService.list_notifications(db, recipient_id=applicant.id)
    assert len(notifs) == 1
    assert notifs[0].type == NotificationType.APPLICATION_ACCEPTED
    assert notifs[0].sender_id == owner.id

    # Reset notifications and test reject
    db.delete(notifs[0])
    db.commit()

    ApplicationService.reject_application(db, application)
    notifs = NotificationService.list_notifications(db, recipient_id=applicant.id)
    assert len(notifs) == 1
    assert notifs[0].type == NotificationType.APPLICATION_REJECTED

def test_project_invite_endpoint_and_notification(db, client):
    owner = create_test_user(db, "owner@example.com", "owner")
    invitee = create_test_user(db, "invitee@example.com", "invitee")
    project = create_test_project(db, owner.id)

    try:
        app.dependency_overrides[get_current_user] = lambda: owner

        response = client.post(
            f"/api/projects/{project.id}/invite/{invitee.id}"
        )

    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 201
    assert response.json()["message"] == "User invited successfully"

    stmt = select(ProjectMember).where(
        and_(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == invitee.id,
        )
    )

    member = db.scalar(stmt)

    assert member is not None
    assert member.is_active is False
    assert member.role == MemberRole.MEMBER

    notifs = NotificationService.list_notifications(
        db,
        recipient_id=invitee.id,
    )

    assert len(notifs) == 1
    assert notifs[0].type == NotificationType.PROJECT_INVITE
    assert notifs[0].sender_id == owner.id
    assert "invited to join" in notifs[0].message