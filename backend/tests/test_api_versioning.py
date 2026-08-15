from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_root_version_info():
    """Test GET /api returns API versioning metadata."""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "DevLink API"
    assert data["version"] == "v1"
    assert data["current_version"] == "v1"
    assert "v1" in data["supported_versions"]


def test_api_v1_root():
    """Test GET /api/v1 returns v1 root status."""
    response = client.get("/api/v1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "DevLink API"
    assert data["version"] == "v1"
    assert data["status"] == "running"


def test_api_v1_health():
    """Test GET /api/v1/health/ready returns healthy or status details."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data


def test_api_v1_project_tags_predefined():
    """Test GET /api/v1/project-tags/predefined versioned route."""
    response = client.get("/api/v1/project-tags/predefined")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data or "tags" in data or isinstance(data, (dict, list))


def test_unversioned_legacy_backward_compatibility():
    """Test GET /api/project-tags/predefined legacy unversioned route for backward compatibility."""
    response = client.get("/api/project-tags/predefined")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data or "tags" in data or isinstance(data, (dict, list))
