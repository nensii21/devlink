import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.project import ProjectStage, ProjectVisibility
from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService
from app.models.application import ApplicationStatus

from app.models.builder_flare import BuilderFlare

@pytest.fixture
def test_project(db: Session, register_and_login):
    owner_id, token = register_and_login("projowner@example.com", "projowner")
    project_in = ProjectCreate(
        title="Test Project App",
        slug="test-project-app",
        description="A project to test applications.",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )
    project = ProjectService.create_project(db, uuid.UUID(owner_id), project_in)
    
    flare = BuilderFlare(
        project_id=project.id,
        created_by=uuid.UUID(owner_id),
        title="Need a developer",
        description="Looking for someone to help.",
        role="Developer",
    )
    db.add(flare)
    db.commit()
    db.refresh(flare)

    return {"id": project.id, "owner_id": owner_id, "token": token, "flare_id": flare.id}

def test_create_application(client: TestClient, register_and_login, test_project):
    pid = test_project["id"]
    applicant_id, token = register_and_login("applicant@example.com", "applicant")

    response = client.post(
        "/applications/",
        json={
            "project_id": str(pid),
            "flare_id": str(test_project["flare_id"]),
            "message": "I would like to join!",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["message"] == "I would like to join!"
    assert response.json()["project_id"] == str(pid)

def test_create_application_invalid_payload(client: TestClient, register_and_login):
    applicant_id, token = register_and_login("appinvalid@example.com", "appinvalid")

    response = client.post(
        "/applications/",
        json={"message": "No project_id!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422

def test_get_application(client: TestClient, register_and_login, test_project):
    pid = test_project["id"]
    applicant_id, token = register_and_login("appget@example.com", "appget")

    c = client.post(
        "/applications/",
        json={"project_id": str(pid), "flare_id": str(test_project["flare_id"])},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert c.status_code == 201
    app_id = c.json()["id"]

    response = client.get(f"/applications/{app_id}")
    assert response.status_code == 200
    assert response.json()["project_id"] == str(pid)

def test_application_not_found(client: TestClient):
    response = client.get(f"/applications/{uuid.uuid4()}")
    assert response.status_code == 404

def test_my_applications(client: TestClient, register_and_login, test_project):
    pid = test_project["id"]
    applicant_id, token = register_and_login("myapps@example.com", "myapps")

    client.post(
        "/applications/",
        json={"project_id": str(pid), "flare_id": str(test_project["flare_id"])},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/applications/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_project_applications(client: TestClient, register_and_login, test_project):
    pid = test_project["id"]
    applicant_id, token = register_and_login("projapps@example.com", "projapps")

    client.post(
        "/applications/",
        json={"project_id": str(pid), "flare_id": str(test_project["flare_id"])},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(f"/applications/project/{pid}")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_update_application(client: TestClient, register_and_login, test_project):
    pid = test_project["id"]
    applicant_id, token = register_and_login("updapp@example.com", "updapp")

    c = client.post(
        "/applications/",
        json={"project_id": str(pid), "flare_id": str(test_project["flare_id"]), "message": "Original"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert c.status_code == 201
    app_id = c.json()["id"]

    response = client.put(
        f"/applications/{app_id}",
        json={"message": "Updated!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Updated!"

def test_accept_application(client: TestClient, register_and_login, test_project):
    pid = test_project["id"]
    owner_token = test_project["token"]
    applicant_id, applicant_token = register_and_login("accapp@example.com", "accapp")

    c = client.post(
        "/applications/",
        json={"project_id": str(pid), "flare_id": str(test_project["flare_id"])},
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert c.status_code == 201
    app_id = c.json()["id"]

    response = client.patch(
        f"/applications/{app_id}/accept",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

def test_reject_application(client: TestClient, register_and_login, test_project):
    pid = test_project["id"]
    owner_token = test_project["token"]
    applicant_id, applicant_token = register_and_login("rejapp@example.com", "rejapp")

    c = client.post(
        "/applications/",
        json={"project_id": str(pid), "flare_id": str(test_project["flare_id"])},
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert c.status_code == 201
    app_id = c.json()["id"]

    response = client.patch(
        f"/applications/{app_id}/reject",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

def test_withdraw_application(client: TestClient, register_and_login, test_project):
    pid = test_project["id"]
    applicant_id, applicant_token = register_and_login("withdrawapp@example.com", "withdrawapp")

    c = client.post(
        "/applications/",
        json={"project_id": str(pid), "flare_id": str(test_project["flare_id"])},
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert c.status_code == 201
    app_id = c.json()["id"]

    response = client.patch(
        f"/applications/{app_id}/withdraw",
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "withdrawn"

def test_delete_application(client: TestClient, register_and_login, test_project):
    pid = test_project["id"]
    applicant_id, applicant_token = register_and_login("delapp@example.com", "delapp")

    c = client.post(
        "/applications/",
        json={"project_id": str(pid), "flare_id": str(test_project["flare_id"])},
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert c.status_code == 201
    app_id = c.json()["id"]

    response = client.delete(
        f"/applications/{app_id}",
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert response.status_code == 204

    # Verify not found
    nf = client.get(f"/applications/{app_id}")
    assert nf.status_code == 404
