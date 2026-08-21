import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.user import User
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
        first_name="Widget",
        last_name="User",
        password_hash="fakehash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_dashboard_layout_crud():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "widgetuser@example.com", "widgetuser")
    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initial state -> uncustomized
    get_res = client.get("/api/users/me/dashboard-layout", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["is_customized"] is False
    assert len(get_res.json()["widgets"]) == 0

    # 2. Save custom layout
    custom_layout = {
        "widgets": [
            {
                "id": "current-projects",
                "order": 0,
                "pinned": True,
                "visible": True,
                "column": 1,
            },
            {
                "id": "stats",
                "order": 1,
                "pinned": False,
                "visible": True,
                "column": 1,
            },
            {
                "id": "upgrade-plan",
                "order": 2,
                "pinned": False,
                "visible": False,
                "column": 2,
            },
        ]
    }

    put_res = client.put(
        "/api/users/me/dashboard-layout", headers=headers, json=custom_layout
    )
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["is_customized"] is True
    assert len(data["widgets"]) == 3
    assert data["widgets"][0]["id"] == "current-projects"
    assert data["widgets"][0]["pinned"] is True
    assert data["widgets"][2]["visible"] is False

    # 3. Retrieve saved layout
    get_saved = client.get("/api/users/me/dashboard-layout", headers=headers)
    assert get_saved.status_code == 200
    saved_data = get_saved.json()
    assert saved_data["is_customized"] is True
    assert len(saved_data["widgets"]) == 3

    # 4. Reset layout to default
    del_res = client.delete("/api/users/me/dashboard-layout", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["is_customized"] is False
    assert len(del_res.json()["widgets"]) == 0

    # 5. Verify reset state
    get_after_del = client.get("/api/users/me/dashboard-layout", headers=headers)
    assert get_after_del.status_code == 200
    assert get_after_del.json()["is_customized"] is False
