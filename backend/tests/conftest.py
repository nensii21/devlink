import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.security


class MockPwdContext:
    def hash(self, secret: str, **kwargs) -> str:
        print("MOCK HASH CALLED!")
        return secret + "_hashed"

    def verify(self, secret: str, hash: str, **kwargs) -> bool:
        print("MOCK VERIFY CALLED!")
        return hash == secret + "_hashed"


app.core.security.pwd_context = MockPwdContext()
app.core.security.hash_password = lambda p: p + "_hashed"
app.core.security.verify_password = lambda p, h: h == p + "_hashed"

from app.database.base import Base
from app.dependencies import get_database
from app.main import app

app.state.limiter.enabled = False

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
        print("EXECUTING COMMIT IN OVERRIDE_GET_DB!")
        db.commit()
    except Exception as e:
        print(f"EXCEPTION IN OVERRIDE_GET_DB: {e}")
        db.rollback()
        raise
    finally:
        print("CLOSING DB IN OVERRIDE_GET_DB!")
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    import app.database.session

    app.database.session.SessionLocal = TestingSessionLocal
    app.database.session.get_db = override_get_db
    import app.database.database

    app.database.database.engine = engine
    from app.main import app

    app.dependency_overrides[get_database] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db():
    # Return the db session for tests that need it directly
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="function")
def register_and_login(client: TestClient):
    """
    Returns a factory function that registers and logs in a user.
    """

    def _register_and_login_func(
        email: str, username: str, password: str = "Passw0rd!"
    ) -> tuple[str, str]:
        # Register
        client.post(
            "/api/auth/register",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": email,
                "username": username,
                "password": password,
            },
        )
        # Login
        r = client.post("/api/auth/login", json={"email": email, "password": password})
        token = r.json().get("access_token")
        if not token:
            raise RuntimeError(f"Login failed: {r.json()}")

        me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        return me.json()["id"], token

    return _register_and_login_func
