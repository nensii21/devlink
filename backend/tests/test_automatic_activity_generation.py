import uuid
from app.models.activity import Activity, ActivityType
from app.models.application import Application, ApplicationStatus
from app.models.user import User
from app.schemas.organization import OrganizationCreate
from app.schemas.project import ProjectCreate
from app.schemas.user import UserUpdate
from app.services.application_service import ApplicationService
from app.services.follower_service import FollowerService
from app.services.organization_service import OrganizationService
from app.services.project_service import ProjectService
from app.services.user_service import UserService


def test_automatic_activity_project_creation(db):
    user = UserService.create_user(
        db,
        User(
            email=f"creator_{uuid.uuid4().hex[:6]}@example.com",
            username=f"creator_{uuid.uuid4().hex[:6]}",
            first_name="Project",
            last_name="Creator",
        ),
        "secret_hash_123",
    )
    project_data = ProjectCreate(
        title=f"Test Project {uuid.uuid4().hex[:6]}",
        slug=f"test-project-{uuid.uuid4().hex[:6]}",
        description="A cool project description for automatic activity feed.",
    )
    project = ProjectService.create_project(db, user.id, project_data)

    activity = (
        db.query(Activity)
        .filter(
            Activity.actor_id == user.id,
            Activity.activity_type == ActivityType.PROJECT_CREATED,
        )
        .first()
    )
    assert activity is not None
    assert activity.target_id == project.id
    assert activity.target_type == "project"
    assert activity.title == "Created project"


def test_automatic_activity_project_joined(db):
    owner = UserService.create_user(
        db,
        User(
            email=f"owner_{uuid.uuid4().hex[:6]}@example.com",
            username=f"owner_{uuid.uuid4().hex[:6]}",
            first_name="Project",
            last_name="Owner",
        ),
        "secret_hash_123",
    )
    applicant = UserService.create_user(
        db,
        User(
            email=f"applicant_{uuid.uuid4().hex[:6]}@example.com",
            username=f"applicant_{uuid.uuid4().hex[:6]}",
            first_name="Project",
            last_name="Applicant",
        ),
        "secret_hash_123",
    )
    project = ProjectService.create_project(
        db,
        owner.id,
        ProjectCreate(
            title=f"Join Project {uuid.uuid4().hex[:6]}",
            slug=f"join-project-{uuid.uuid4().hex[:6]}",
            description="Project to join and trigger activity.",
        ),
    )

    from app.models.builder_flare import BuilderFlare

    flare = BuilderFlare(
        project_id=project.id,
        created_by=owner.id,
        title="Python Dev",
        role="Developer",
        description="Looking for Python developer",
    )
    db.add(flare)
    db.commit()
    db.refresh(flare)

    app = Application(
        project_id=project.id,
        applicant_id=applicant.id,
        flare_id=flare.id,
        message="I want to contribute!",
        status=ApplicationStatus.PENDING,
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    ApplicationService.accept_application(db, app)

    activity = (
        db.query(Activity)
        .filter(
            Activity.actor_id == applicant.id,
            Activity.activity_type == ActivityType.PROJECT_JOINED,
        )
        .first()
    )
    assert activity is not None
    assert activity.target_id == project.id
    assert activity.target_type == "project"
    assert activity.title == "Joined project"


def test_automatic_activity_user_follow(db):
    user1 = UserService.create_user(
        db,
        User(
            email=f"follower_{uuid.uuid4().hex[:6]}@example.com",
            username=f"follower_{uuid.uuid4().hex[:6]}",
            first_name="User",
            last_name="One",
        ),
        "secret_hash_123",
    )
    user2 = UserService.create_user(
        db,
        User(
            email=f"following_{uuid.uuid4().hex[:6]}@example.com",
            username=f"following_{uuid.uuid4().hex[:6]}",
            first_name="User",
            last_name="Two",
        ),
        "secret_hash_123",
    )

    FollowerService.follow_user(db, user1.id, user2.id)

    activity = (
        db.query(Activity)
        .filter(
            Activity.actor_id == user1.id,
            Activity.activity_type == ActivityType.FOLLOWED_USER,
        )
        .first()
    )
    assert activity is not None
    assert activity.target_id == user2.id
    assert activity.target_type == "user"
    assert activity.title == "Followed a builder"


def test_automatic_activity_profile_update(db):
    user = UserService.create_user(
        db,
        User(
            email=f"profile_{uuid.uuid4().hex[:6]}@example.com",
            username=f"profile_{uuid.uuid4().hex[:6]}",
            first_name="Profile",
            last_name="User",
        ),
        "secret_hash_123",
    )

    UserService.update_user(
        db,
        user,
        UserUpdate(first_name="UpdatedFirstName", bio="Updated bio description"),
    )

    activity = (
        db.query(Activity)
        .filter(
            Activity.actor_id == user.id,
            Activity.activity_type == ActivityType.PROFILE_UPDATED,
        )
        .first()
    )
    assert activity is not None
    assert activity.target_id == user.id
    assert activity.target_type == "user"
    assert activity.title == "Updated profile"


def test_automatic_activity_organization_creation(db):
    owner = UserService.create_user(
        db,
        User(
            email=f"org_owner_{uuid.uuid4().hex[:6]}@example.com",
            username=f"org_owner_{uuid.uuid4().hex[:6]}",
            first_name="Org",
            last_name="Owner",
        ),
        "secret_hash_123",
    )

    org_data = OrganizationCreate(
        name=f"Test Org {uuid.uuid4().hex[:6]}",
        description="Organization description for activity feed testing.",
    )

    org = OrganizationService.create_organization(db, owner.id, org_data)

    activity = (
        db.query(Activity)
        .filter(
            Activity.actor_id == owner.id,
            Activity.activity_type == ActivityType.ORGANIZATION_CREATED,
        )
        .first()
    )
    assert activity is not None
    assert activity.target_id == org.id
    assert activity.target_type == "organization"
    assert activity.title == "Created organization"
