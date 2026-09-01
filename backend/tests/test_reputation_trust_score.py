import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.dependencies import get_current_user
from app.main import app
from app.models.user import User
from app.schemas.reputation import ReputationAction
from app.services.reputation_service import ReputationService

# SQLite setup for tests
engine = create_engine(
    "sqlite://",
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
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

def _create_user(db, email: str, username: str, is_verified: bool = False) -> User:
    user = User(
        email=email,
        username=username,
        first_name="Dev",
        last_name="User",
        password_hash="fakehash",
        is_active=True,
        is_verified=is_verified,
        reputation_score=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_trust_score_breakdown_and_level():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, email="trust@devlink.io", username="trustdev", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user

    headers = {"Origin": "http://localhost:3000"}

    # Award reputation actions across categories
    ReputationService.award_reputation(db, user.id, ReputationAction.SUCCESSFUL_COLLABORATION.value, points_override=30)
    ReputationService.award_reputation(db, user.id, ReputationAction.MERGED_PULL_REQUEST.value, points_override=50)
    ReputationService.award_reputation(db, user.id, ReputationAction.COMPLETED_PROJECT.value, points_override=100)
    ReputationService.award_reputation(db, user.id, ReputationAction.COMMUNITY_FEEDBACK.value, points_override=20)

    response = client.get("/api/reputation/trust-score/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["reputation_score"] == 200
    assert data["is_verified"] is True
    assert data["trust_score"] == 40  # (200 / 500) * 100
    assert "Active Community Member" in data["trust_level"]
    
    breakdown = data["breakdown"]
    assert breakdown["collaborations_points"] == 30
    assert breakdown["pull_requests_points"] == 50
    assert breakdown["completed_projects_points"] == 100
    assert breakdown["feedback_points"] == 20
    assert breakdown["verification_points"] == 40

def test_peer_endorsement_success():
    client = TestClient(app)
    db = TestingSessionLocal()
    alice = _create_user(db, email="alice@devlink.io", username="alice")
    bob = _create_user(db, email="bob@devlink.io", username="bob")

    app.dependency_overrides[get_current_user] = lambda: alice
    headers = {"Origin": "http://localhost:3000"}

    payload = {
        "target_user_id": str(bob.id),
        "skill_or_reason": "React & Performance Optimization",
        "note": "Exceptional work refactoring components!",
    }

    response = client.post("/api/reputation/endorse", headers=headers, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == str(bob.id)
    assert data["points"] == 15
    assert "React & Performance Optimization" in data["description"]

    # Verify Bob's updated score
    bob_trust = client.get(f"/api/reputation/trust-score/{bob.id}", headers=headers).json()
    assert bob_trust["reputation_score"] == 15
    assert bob_trust["breakdown"]["endorsements_points"] == 15

def test_self_endorsement_rejected():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, email="self@devlink.io", username="selfuser")

    app.dependency_overrides[get_current_user] = lambda: user
    headers = {"Origin": "http://localhost:3000"}

    payload = {
        "target_user_id": str(user.id),
        "skill_or_reason": "Python FastAPI",
    }

    response = client.post("/api/reputation/endorse", headers=headers, json=payload)
    assert response.status_code == 400
    assert "cannot endorse yourself" in response.json()["detail"].lower()
