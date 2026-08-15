import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.main import app
from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.services.search_service import search_users

# Setup in-memory SQLite database for tests
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="test_client")
def fixture_test_client(db_session):
    # Setup mock current user
    mock_user = User(
        first_name="Alice",
        last_name="Developer",
        username="alice_dev",
        email="alice@devlink.io",
        is_active=True,
        is_verified=True,
        premium=False,
    )
    db_session.add(mock_user)
    db_session.commit()
    db_session.refresh(mock_user)

    def override_get_database():
        return db_session

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


def test_toggle_premium_status(test_client, db_session):
    # Initially user is not premium
    user = db_session.query(User).filter(User.username == "alice_dev").first()
    assert user.premium is False

    # Toggle premium status to True
    response = test_client.put("/api/users/me/premium?premium=true")
    assert response.status_code == 200
    data = response.json()
    assert data["premium"] is True

    # Re-verify DB state
    db_session.refresh(user)
    assert user.premium is True

    # Toggle back to False
    response = test_client.put("/api/users/me/premium?premium=false")
    assert response.status_code == 200
    data = response.json()
    assert data["premium"] is False
    db_session.refresh(user)
    assert user.premium is False


def test_search_prioritization(db_session):
    # Create users with different verification and premium states:
    # 1. Unverified, Free (Lowest rank)
    # 2. Verified, Free (Medium rank)
    # 3. Verified, Premium (Highest rank)
    # 4. Unverified, Premium (Low-Medium rank)
    u1 = User(
        first_name="Bobby",
        last_name="Free",
        username="bobby_free",
        email="bobby@devlink.io",
        role="Developer",
        is_active=True,
        is_verified=False,
        premium=False,
    )
    u2 = User(
        first_name="Charlie",
        last_name="Verified",
        username="charlie_ver",
        email="charlie@devlink.io",
        role="Developer",
        is_active=True,
        is_verified=True,
        premium=False,
    )
    u3 = User(
        first_name="David",
        last_name="Premium",
        username="david_prem",
        email="david@devlink.io",
        role="Developer",
        is_active=True,
        is_verified=True,
        premium=True,
    )
    u4 = User(
        first_name="Eva",
        last_name="PremUnver",
        username="eva_unver",
        email="eva@devlink.io",
        role="Developer",
        is_active=True,
        is_verified=False,
        premium=True,
    )

    db_session.add_all([u1, u2, u3, u4])
    db_session.commit()

    # Search for "Developer"
    results = search_users(db_session, "Developer")
    assert len(results) >= 4

    # Order should rank:
    # 1. Verified + Premium (David) -> matches is_verified=True, premium=True
    # 2. Verified + Free (Charlie) -> matches is_verified=True, premium=False
    # 3. Unverified + Premium (Eva) -> matches is_verified=False, premium=True
    # 4. Unverified + Free (Bobby) -> matches is_verified=False, premium=False
    usernames = [u.username for u in results]

    # We find indices of each user in search results to verify they are in correct priority order
    idx_david = usernames.index("david_prem")
    idx_charlie = usernames.index("charlie_ver")
    idx_eva = usernames.index("eva_unver")
    idx_bobby = usernames.index("bobby_free")

    assert idx_david < idx_charlie
    assert idx_charlie < idx_eva
    assert idx_eva < idx_bobby
