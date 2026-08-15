from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_dashboard_json():
    """Test GET /health/dashboard returns detailed JSON health status."""
    response = client.get("/health/dashboard")
    assert response.status_code in (200, 503)
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "environment" in data
    assert "uptime" in data
    assert "services" in data

    # Verify Uptime structure
    uptime = data["uptime"]
    assert "seconds" in uptime
    assert isinstance(uptime["seconds"], (int, float))
    assert "human" in uptime
    assert "started_at" in uptime

    # Verify Services structure (5 required services)
    services = data["services"]
    assert "database" in services
    assert "redis" in services
    assert "ai_service" in services
    assert "storage" in services
    assert "celery" in services

    # Verify database check structure
    db_status = services["database"]
    assert "status" in db_status

    # Verify redis check structure
    redis_status = services["redis"]
    assert "status" in redis_status

    # Verify AI service check structure
    ai_status = services["ai_service"]
    assert "status" in ai_status
    assert "provider" in ai_status
    assert "configured" in ai_status

    # Verify Storage check structure
    storage_status = services["storage"]
    assert "status" in storage_status
    assert "path" in storage_status
    assert "writable" in storage_status
    assert "free_space_mb" in storage_status


def test_health_dashboard_api_v1():
    """Test GET /api/v1/health/dashboard versioned endpoint."""
    response = client.get("/api/v1/health/dashboard")
    assert response.status_code in (200, 503)
    data = response.json()

    assert "status" in data
    assert "uptime" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "ai_service" in data["services"]
    assert "storage" in data["services"]


def test_health_dashboard_html_format():
    """Test GET /health/dashboard?format=html returns HTML dashboard view."""
    response = client.get("/health/dashboard?format=html")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in response.text
    assert "DevLink System Health Dashboard" in response.text
    assert "Service Status" in response.text


def test_health_ready_includes_uptime_and_services():
    """Test GET /health/ready includes uptime and component services."""
    response = client.get("/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()

    assert "status" in data
    assert "services" in data
    assert "uptime" in data
