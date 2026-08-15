from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


@patch("app.routers.projects.AIService.generate_project_description")
def test_generate_project_description_api(
    mock_generate, client: TestClient, register_and_login
):
    _, token = register_and_login("testai@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}

    mock_resp = MagicMock()
    mock_resp.description = "Generated Description"
    mock_generate.return_value = mock_resp

    response = client.post(
        "/api/v1/projects/generate-description",
        json={"prompt": "A cool project"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Generated Description"
