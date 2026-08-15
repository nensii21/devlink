import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_user_registration_and_auth_workflow(client: TestClient, db: Session):
    # 1. Register a new user
    register_payload = {
        "first_name": "Integration",
        "last_name": "Tester",
        "email": "integration@example.com",
        "username": "integration_tester",
        "password": "SecurePassword123!"
    }
    r = client.post("/api/auth/register", json=register_payload)
    assert r.status_code == 201, r.json()
    
    # 2. Login
    login_payload = {
        "email": "integration@example.com",
        "password": "SecurePassword123!"
    }
    r = client.post("/api/auth/login", json=login_payload)
    assert r.status_code == 200, r.json()
    token = r.json()["access_token"]
    assert token is not None

    # 3. Fetch profile
    r = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.json()
    user_data = r.json()
    assert user_data["username"] == "integration_tester"
    assert user_data["email"] == "integration@example.com"

def test_project_creation_and_application_workflow(client: TestClient, db: Session, register_and_login):
    # 1. User A (Owner) registers and logs in
    owner_id, owner_token = register_and_login("owner@example.com", "owner_user")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # 2. User A creates a project
    project_payload = {
        "title": "Integration Test Project",
        "slug": "integration-test-project",
        "description": "This is a detailed description of the integration test project.",
    }
    r = client.post("/api/projects/", json=project_payload, headers=owner_headers)
    assert r.status_code == 201, r.json()
    project_id = r.json()["id"]

    # 3. User A creates a Builder Flare
    flare_payload = {
        "title": "Backend Developer Needed",
        "description": "We need a backend developer to write integration tests.",
        "role": "Backend Developer",
        "project_id": project_id
    }
    r = client.post("/api/flare/", json=flare_payload, headers=owner_headers)
    assert r.status_code == 201, r.json()
    flare_id = r.json()["id"]

    # 4. User B (Applicant) registers and logs in
    applicant_id, applicant_token = register_and_login("applicant@example.com", "applicant_user")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}

    # 5. User B applies to the project's flare
    application_payload = {
        "project_id": project_id,
        "flare_id": flare_id,
        "message": "I would love to join this project!"
    }
    r = client.post("/api/applications/", json=application_payload, headers=applicant_headers)
    assert r.status_code == 201, r.json()
    application_id = r.json()["id"]
    assert r.json()["status"] == "pending"

    # 6. User A checks notifications (should receive one for the application)
    r = client.get("/api/notifications/", headers=owner_headers)
    assert r.status_code == 200, r.json()
    notifications = r.json()
    
    assert len(notifications) > 0
    application_notification = next((n for n in notifications if n["type"] == "application" and n["project_id"] == project_id), None)
    assert application_notification is not None
    assert application_notification["sender_id"] == applicant_id

    # 7. User A accepts User B's application
    r = client.patch(f"/api/applications/{application_id}/accept", headers=owner_headers)
    assert r.status_code == 200, r.json()
    assert r.json()["status"] == "accepted"

    # 8. User B checks notifications (should receive one for the acceptance)
    r = client.get("/api/notifications/", headers=applicant_headers)
    assert r.status_code == 200, r.json()
    notifications = r.json()
    assert len(notifications) > 0
    acceptance_notification = next((n for n in notifications if n["type"] == "application_accepted" and n["project_id"] == project_id), None)
    assert acceptance_notification is not None
    assert acceptance_notification["sender_id"] == owner_id
