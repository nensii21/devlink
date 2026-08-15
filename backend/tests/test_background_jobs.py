import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.background_job import BackgroundJob, JobStatus
from app.tasks.notification_tasks import send_notification_task
from app.models.notification import NotificationType
from app.core.celery_app import celery_app

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True


@pytest.fixture(autouse=True)
def mock_task_db():
    import app.tasks.notification_tasks as nt
    from tests.conftest import TestingSessionLocal

    original_session = nt.SessionLocal
    nt.SessionLocal = TestingSessionLocal
    yield
    nt.SessionLocal = original_session


def test_background_job_lifecycle(db: Session):
    from app.models.user import User

    user = User(
        first_name="Lifecycle",
        last_name="Test",
        email="lifecycle@test.com",
        username="lifecycle_test",
        password_hash="secret_hashed",
    )
    db.add(user)
    db.commit()

    recipient_id = user.id
    sender_id = user.id

    payload = {
        "recipient_id": str(recipient_id),
        "sender_id": str(sender_id),
        "type": NotificationType.FOLLOW.value,
        "title": "New follower",
        "message": "someone followed you",
        "action_url": None,
        "image_url": None,
        "project_id": None,
        "conversation_id": None,
        "message_id": None,
        "application_id": None,
    }

    res = send_notification_task.apply(args=[payload])
    task_id = res.id

    job = db.get(BackgroundJob, task_id)
    assert job is not None
    assert job.task_name == "notifications.send"
    assert job.status == JobStatus.COMPLETED
    assert job.payload is not None
    assert job.processing_time is not None
    assert job.processing_time >= 0.0


def test_background_jobs_api_admin_only(client: TestClient):
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Standard",
            "last_name": "User",
            "email": "user@test.com",
            "username": "stduser",
            "password": "Passw0rd!",
        },
    )
    r = client.post(
        "/api/auth/login", json={"email": "user@test.com", "password": "Passw0rd!"}
    )
    token = r.json()["access_token"]

    r = client.get(
        "/api/admin/background-jobs/stats", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 403
    assert "Admin access required" in r.json()["detail"]


def test_background_jobs_api_success(client: TestClient, db: Session):
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Admin",
            "last_name": "User",
            "email": "admin@test.com",
            "username": "adminuser",
            "password": "Passw0rd!",
        },
    )

    from app.models.user import User

    admin_user = db.scalar(select(User).where(User.email == "admin@test.com"))
    assert admin_user is not None
    admin_user.role = "admin"
    db.commit()

    r = client.post(
        "/api/auth/login", json={"email": "admin@test.com", "password": "Passw0rd!"}
    )
    token = r.json()["access_token"]

    user_id = str(admin_user.id)
    job1 = BackgroundJob(
        id="job-1",
        task_name="notifications.send",
        status=JobStatus.COMPLETED,
        payload={
            "args": [
                {
                    "recipient_id": user_id,
                    "sender_id": user_id,
                    "type": "follow",
                    "title": "a",
                    "message": "b",
                }
            ],
            "kwargs": {},
        },
        processing_time=0.123,
    )
    job2 = BackgroundJob(
        id="job-2",
        task_name="notifications.send",
        status=JobStatus.FAILED,
        payload={
            "args": [
                {
                    "recipient_id": user_id,
                    "sender_id": user_id,
                    "type": "follow",
                    "title": "a",
                    "message": "b",
                }
            ],
            "kwargs": {},
        },
        error="Exception: Something went wrong",
    )
    db.add_all([job1, job2])
    db.commit()

    r = client.get(
        "/api/admin/background-jobs/stats", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 2
    assert data["completed"] >= 1
    assert data["failed"] >= 1

    r = client.get(
        "/api/admin/background-jobs/", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["jobs"]) >= 2

    r = client.get(
        "/api/admin/background-jobs/?status=failed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert all(j["status"] == "failed" for j in data["jobs"])

    r = client.get(
        "/api/admin/background-jobs/?search=job-1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["id"] == "job-1"

    r = client.post(
        "/api/admin/background-jobs/job-2/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "retrying"

    db.refresh(job2)
    assert job2.status in (JobStatus.PENDING, JobStatus.COMPLETED)
