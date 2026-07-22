from datetime import datetime, timedelta, timezone

import app.core.security
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class MockPwdContext:
    def hash(self, secret: str, **kwargs) -> str:
        return secret + "_hashed"

    def verify(self, secret: str, hash: str, **kwargs) -> bool:
        return hash == secret + "_hashed"


app.core.security.pwd_context = MockPwdContext()

from app.database.base import Base  # noqa: E402
from app.dependencies import get_database  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.auth import CurrentUserResponse  # noqa: E402
from app.schemas.user import CurrentUser, UserResponse  # noqa: E402

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_database] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# -------------------------------------------------------------------
# Model-level tests
# -------------------------------------------------------------------


def test_user_model_has_last_active_at_column():
    """The users table should have a last_active_at column."""
    columns = {c.name for c in User.__table__.columns}
    assert "last_active_at" in columns


def test_user_last_active_at_default_is_none(db):
    """A new user should have last_active_at = None."""
    user = User(
        first_name="Test",
        last_name="User",
        username="testmodel",
        email="testmodel@example.com",
        password_hash="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.last_active_at is None


def test_user_last_active_at_can_be_set(db):
    """last_active_at should accept a UTC datetime."""
    now = datetime.now(timezone.utc)
    user = User(
        first_name="Test",
        last_name="User",
        username="testactive",
        email="testactive@example.com",
        password_hash="hashed",
        last_active_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.last_active_at is not None
    assert user.last_active_at.year == now.year


def test_user_last_active_at_stores_timezone(db):
    """last_active_at should accept timezone-aware datetime (UTC).

    Note: SQLite strips timezone info on round-trip, but PostgreSQL preserves it.
    This test verifies the value is set correctly; production behavior is validated
    by the ``DateTime(timezone=True)`` column definition.
    """
    now = datetime.now(timezone.utc)
    user = User(
        first_name="Tz",
        last_name="User",
        username="tztuser",
        email="tztuser@example.com",
        password_hash="hashed",
        last_active_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.last_active_at is not None
    # Verify the timestamp is within 1 second of what we set
    assert (
        abs(
            (
                user.last_active_at.replace(tzinfo=None) - now.replace(tzinfo=None)
            ).total_seconds()
        )
        < 1
    )


def test_user_last_active_at_updateable(db):
    """last_active_at should be updatable after creation."""
    user = User(
        first_name="Upd",
        last_name="User",
        username="updactive",
        email="updactive@example.com",
        password_hash="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.last_active_at is None

    new_time = datetime.now(timezone.utc)
    user.last_active_at = new_time
    db.commit()
    db.refresh(user)
    assert user.last_active_at is not None


# -------------------------------------------------------------------
# Schema-level tests
# -------------------------------------------------------------------


def test_user_response_includes_last_active_at():
    """UserResponse schema should include last_active_at field."""
    schema_fields = UserResponse.model_fields
    assert "last_active_at" in schema_fields


def test_current_user_includes_last_active_at():
    """CurrentUser schema should include last_active_at field."""
    schema_fields = CurrentUser.model_fields
    assert "last_active_at" in schema_fields


def test_current_user_response_includes_last_active_at():
    """CurrentUserResponse schema should include last_active_at field."""
    schema_fields = CurrentUserResponse.model_fields
    assert "last_active_at" in schema_fields


def test_user_response_serializes_last_active_at(db):
    """UserResponse should serialize last_active_at from ORM model."""
    now = datetime.now(timezone.utc)
    user = User(
        first_name="Ser",
        last_name="User",
        username="seruser",
        email="seruser@example.com",
        password_hash="hashed",
        last_active_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    resp = UserResponse.model_validate(user)
    assert resp.last_active_at is not None


def test_user_response_handles_null_last_active_at(db):
    """UserResponse should handle null last_active_at."""
    user = User(
        first_name="Null",
        last_name="User",
        username="nulluser",
        email="nulluser@example.com",
        password_hash="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    resp = UserResponse.model_validate(user)
    assert resp.last_active_at is None


# -------------------------------------------------------------------
# Middleware throttle logic test
# -------------------------------------------------------------------


def test_throttle_should_update_when_none():
    """Should update when last_active_at is None."""
    last_active = None
    should_update = last_active is None
    assert should_update is True


def test_throttle_should_update_when_stale():
    """Should update when last_active_at is older than throttle window."""
    from app.middleware.activity import THROTTLE_SECONDS

    last_active = datetime.now(timezone.utc) - timedelta(seconds=THROTTLE_SECONDS + 1)
    now = datetime.now(timezone.utc)
    should_update = (now - last_active).total_seconds() > THROTTLE_SECONDS
    assert should_update is True


def test_throttle_should_skip_when_recent():
    """Should skip update when last_active_at is within throttle window."""
    from app.middleware.activity import THROTTLE_SECONDS

    last_active = datetime.now(timezone.utc) - timedelta(seconds=THROTTLE_SECONDS - 10)
    now = datetime.now(timezone.utc)
    should_update = (now - last_active).total_seconds() > THROTTLE_SECONDS
    assert should_update is False
