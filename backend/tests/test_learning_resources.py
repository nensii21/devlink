"""Tests for the Learning Resources feature."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    email = "learner@example.com"
    password = "TestPass123!"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": "learner",
            "password": password,
            "display_name": "Learner",
        },
    )
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    token = resp.json().get("access_token") or resp.json().get("token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project_id(client: TestClient, auth_headers: dict) -> str:
    resp = client.post(
        "/api/projects",
        headers=auth_headers,
        json={
            "title": "Learning Test Project",
            "description": "A project for testing learning resources",
            "visibility": "public",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]


RESOURCE_PAYLOAD = {
    "title": "FastAPI Official Docs",
    "url": "https://fastapi.tiangolo.com",
    "description": "The official FastAPI documentation",
    "category": "documentation",
    "language": "Python",
    "difficulty": "intermediate",
}


class TestCreateResource:
    def test_create_resource(self, client, auth_headers, project_id):
        resp = client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == RESOURCE_PAYLOAD["title"]
        assert data["category"] == "documentation"
        assert data["vote_score"] == 0

    def test_create_resource_invalid_project(self, client, auth_headers):
        import uuid
        resp = client.post(
            f"/api/learning-resources/project/{uuid.uuid4()}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        assert resp.status_code == 404

    def test_create_resource_no_auth(self, client, project_id):
        resp = client.post(
            f"/api/learning-resources/project/{project_id}",
            json=RESOURCE_PAYLOAD,
        )
        assert resp.status_code in (401, 403)


class TestListResources:
    def test_list_empty(self, client, auth_headers, project_id):
        resp = client.get(f"/api/learning-resources/project/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_with_resources(self, client, auth_headers, project_id):
        for i in range(3):
            client.post(
                f"/api/learning-resources/project/{project_id}",
                headers=auth_headers,
                json={**RESOURCE_PAYLOAD, "title": f"Resource {i}"},
            )
        resp = client.get(f"/api/learning-resources/project/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

    def test_filter_by_category(self, client, auth_headers, project_id):
        client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json={**RESOURCE_PAYLOAD, "title": "Video Guide", "category": "video", "url": "https://youtube.com/1"},
        )
        resp = client.get(
            f"/api/learning-resources/project/{project_id}?category=video"
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["category"] == "video"

    def test_filter_by_difficulty(self, client, auth_headers, project_id):
        client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        resp = client.get(
            f"/api/learning-resources/project/{project_id}?difficulty=beginner"
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_search(self, client, auth_headers, project_id):
        client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        resp = client.get(
            f"/api/learning-resources/project/{project_id}?search=FastAPI"
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


class TestGetResource:
    def test_get_resource(self, client, auth_headers, project_id):
        create_resp = client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        rid = create_resp.json()["id"]
        resp = client.get(f"/api/learning-resources/{rid}")
        assert resp.status_code == 200
        assert resp.json()["title"] == RESOURCE_PAYLOAD["title"]

    def test_get_nonexistent(self, client):
        resp = client.get("/api/learning-resources/nonexistent-id")
        assert resp.status_code == 404


class TestUpdateResource:
    def test_update_own_resource(self, client, auth_headers, project_id):
        create_resp = client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        rid = create_resp.json()["id"]
        resp = client.patch(
            f"/api/learning-resources/{rid}",
            headers=auth_headers,
            json={"title": "Updated Title", "difficulty": "advanced"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"
        assert resp.json()["difficulty"] == "advanced"


class TestDeleteResource:
    def test_delete_own_resource(self, client, auth_headers, project_id):
        create_resp = client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        rid = create_resp.json()["id"]
        resp = client.delete(f"/api/learning-resources/{rid}", headers=auth_headers)
        assert resp.status_code == 204
        get_resp = client.get(f"/api/learning-resources/{rid}")
        assert get_resp.status_code == 404


class TestVoting:
    def test_upvote(self, client, auth_headers, project_id):
        create_resp = client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        rid = create_resp.json()["id"]
        resp = client.post(
            f"/api/learning-resources/{rid}/vote",
            headers=auth_headers,
            json={"value": 1},
        )
        assert resp.status_code == 200
        assert resp.json()["vote_score"] == 1

    def test_toggle_vote_off(self, client, auth_headers, project_id):
        create_resp = client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        rid = create_resp.json()["id"]
        client.post(
            f"/api/learning-resources/{rid}/vote",
            headers=auth_headers,
            json={"value": 1},
        )
        resp = client.post(
            f"/api/learning-resources/{rid}/vote",
            headers=auth_headers,
            json={"value": 1},
        )
        assert resp.json()["vote_score"] == 0


class TestPin:
    def test_toggle_pin(self, client, auth_headers, project_id):
        create_resp = client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        rid = create_resp.json()["id"]
        resp = client.patch(
            f"/api/learning-resources/{rid}/pin", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["is_pinned"] is True


class TestStats:
    def test_stats_empty_project(self, client, project_id):
        resp = client.get(f"/api/learning-resources/project/{project_id}/stats")
        assert resp.status_code == 200
        assert resp.json()["total_resources"] == 0

    def test_stats_with_resources(self, client, auth_headers, project_id):
        client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json=RESOURCE_PAYLOAD,
        )
        client.post(
            f"/api/learning-resources/project/{project_id}",
            headers=auth_headers,
            json={**RESOURCE_PAYLOAD, "title": "Video", "category": "video", "url": "https://yt.com/v1"},
        )
        resp = client.get(f"/api/learning-resources/project/{project_id}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_resources"] == 2
        assert "documentation" in data["by_category"]
        assert "video" in data["by_category"]
