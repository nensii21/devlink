from fastapi.testclient import TestClient


def test_get_developer_insights_unauthenticated(client: TestClient):
    response = client.get("/api/developer-insights")
    assert response.status_code == 401


def test_get_developer_insights_authenticated(client: TestClient, register_and_login):
    _, token = register_and_login("devinsightsuser1@example.com", "pass123456")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/developer-insights?range=30d", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "metrics" in data
    metrics = data["metrics"]
    assert "projects_created" in metrics
    assert "applications_submitted" in metrics
    assert "profile_views" in metrics
    assert "followers_gained" in metrics
    assert "messages_sent" in metrics
    assert "contribution_streak" in metrics
    assert "ai_match_success_rate" in metrics
    assert data["date_range"] == "30d"
    assert "activity_timeline" in data
