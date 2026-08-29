import pytest
from fastapi.testclient import TestClient

from app.schemas.email_template import EmailTemplateType


def test_list_email_templates(client: TestClient, register_and_login):
    _, token = register_and_login("emailuser1@example.com", "pass123456")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/email-templates", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7

    types_found = {t["template_type"] for t in data}
    for expected_type in EmailTemplateType:
        assert expected_type.value in types_found


def test_render_all_email_templates(client: TestClient, register_and_login):
    _, token = register_and_login("emailuser2@example.com", "pass123456")
    headers = {"Authorization": f"Bearer {token}"}

    for t_type in EmailTemplateType:
        payload = {
            "template_type": t_type.value,
            "context": {"user_name": "Test Developer", "project_name": "Test Project"},
        }
        response = client.post(
            "/api/email-templates/render", json=payload, headers=headers
        )
        assert response.status_code == 200
        res = response.json()
        assert res["template_type"] == t_type.value
        assert len(res["subject"]) > 0
        assert (
            "Test Developer" in res["html_content"]
            or "Test Project" in res["html_content"]
            or "DevLink" in res["html_content"]
        )
        assert len(res["text_content"]) > 0
