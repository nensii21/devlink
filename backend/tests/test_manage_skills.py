import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.user import User
from app.models.skill import Skill
from app.core.security import create_access_token

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
    app.dependency_overrides[get_database] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def _create_user(db, email: str, username: str) -> User:
    user = User(
        email=email,
        username=username,
        first_name="Skill",
        last_name="Manager",
        password_hash="fakehash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_search_skills_autocomplete():
    client = TestClient(app)
    db = TestingSessionLocal()

    # Pre-seed skills
    s1 = Skill(
        name="TypeScript",
        slug="typescript",
        normalized_name="typescript",
        category="Languages",
    )
    s2 = Skill(
        name="Python", slug="python", normalized_name="python", category="Languages"
    )
    s3 = Skill(
        name="React", slug="react", normalized_name="react", category="Frameworks"
    )
    db.add_all([s1, s2, s3])
    db.commit()

    response = client.get("/api/skills/search/Type")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert any(r["name"] == "TypeScript" for r in results)


def test_manage_user_skill_matrix():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "skillsuser@example.com", "skillsuser")
    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Update skills (Add, Edit, Reorder, Deduplicate)
    skills_payload = {
        "skills": [
            {
                "name": "TypeScript",
                "category": "Languages",
                "level": "expert",
                "years_of_experience": 5,
            },
            {
                "name": "React",
                "category": "Frameworks",
                "level": "advanced",
                "years_of_experience": 4,
            },
            {
                "name": "FastAPI",
                "category": "Frameworks",
                "level": "intermediate",
                "years_of_experience": 2,
            },
            # Duplicate skill should be safely ignored
            {
                "name": "TypeScript",
                "category": "Languages",
                "level": "expert",
                "years_of_experience": 5,
            },
        ]
    }

    put_res = client.put("/api/skills-matrix/me", headers=headers, json=skills_payload)
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["total_skills"] == 3

    # Check languages category
    languages = data["skills_by_category"]["Languages"]
    assert len(languages) == 1
    assert languages[0]["name"] == "TypeScript"
    assert languages[0]["level"] == "Expert"
    assert languages[0]["years_of_experience"] == 5

    # Check frameworks category
    frameworks = data["skills_by_category"]["Frameworks"]
    assert len(frameworks) == 2
    f_names = [f["name"] for f in frameworks]
    assert "React" in f_names
    assert "FastAPI" in f_names

    # 2. Get my skill matrix
    get_res = client.get("/api/skills-matrix/me", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["total_skills"] == 3

    # 3. Delete a skill by updating with fewer skills
    updated_payload = {
        "skills": [
            {
                "name": "TypeScript",
                "category": "Languages",
                "level": "expert",
                "years_of_experience": 6,
            }
        ]
    }
    del_res = client.put("/api/skills-matrix/me", headers=headers, json=updated_payload)
    assert del_res.status_code == 200
    assert del_res.json()["total_skills"] == 1
