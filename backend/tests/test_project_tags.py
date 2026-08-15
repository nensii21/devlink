from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.project_tag_service import ProjectTagService


def test_get_predefined_tags_service():
    """Verify ProjectTagService returns predefined categories."""
    tags = ProjectTagService.get_predefined_tags()
    assert isinstance(tags, list)
    assert "AI" in tags
    assert "Web" in tags
    assert "Mobile" in tags
    assert "Open Source" in tags
    assert "Blockchain" in tags
    assert "Cybersecurity" in tags


def test_get_predefined_tags_endpoint():
    """Verify GET /api/project-tags/predefined returns predefined categories."""
    client = TestClient(app)
    r = client.get("/api/project-tags/predefined")
    assert r.status_code == 200
    body = r.json()
    assert "tags" in body
    tags = body["tags"]
    assert "AI" in tags
    assert "Web" in tags
    assert "Mobile" in tags
    assert "Open Source" in tags
    assert "Blockchain" in tags
    assert "Cybersecurity" in tags


def test_generate_default_tags_includes_predefined_category():
    """Verify default tag generator matches predefined keywords."""
    tags = ProjectTagService._get_default_tags(
        title="AI Chatbot",
        description="An open source mobile app using artificial intelligence and cybersecurity.",
    )
    names = [t["name"] for t in tags]
    assert "AI" in names
    assert "Mobile" in names
    assert "Cybersecurity" in names
    assert "Open Source" in names
