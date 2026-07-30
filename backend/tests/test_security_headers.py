import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    return TestClient(app)


def test_security_headers_present(client):
    """
    Test that recommended security headers are present in response.
    """
    response = client.get("/health")
    assert response.status_code == 200

    headers = response.headers

    # Mandatory Issue #579 HTTP Security Headers
    assert "Content-Security-Policy" in headers
    assert "Strict-Transport-Security" in headers
    assert "X-Frame-Options" in headers
    assert "Referrer-Policy" in headers
    assert "Permissions-Policy" in headers
    assert "X-Content-Type-Options" in headers


def test_security_headers_values(client):
    """
    Test that HTTP security headers have recommended default directive values.
    """
    response = client.get("/health")
    assert response.status_code == 200

    headers = response.headers

    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert "max-age=63072000" in headers["Strict-Transport-Security"]
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in headers["Permissions-Policy"]
    assert "microphone=()" in headers["Permissions-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"


def test_security_headers_on_api_v1(client):
    """
    Test that HTTP security headers are included on versioned API endpoints.
    """
    response = client.get("/api/v1/health/dashboard")

    headers = response.headers

    assert "Content-Security-Policy" in headers
    assert "Strict-Transport-Security" in headers
    assert "X-Frame-Options" in headers
    assert "Referrer-Policy" in headers
    assert "Permissions-Policy" in headers


def test_security_headers_toggle(client, monkeypatch):
    """
    Test that security headers can be conditionally disabled via settings flags.
    """
    monkeypatch.setattr(settings, "ENABLE_CSP", False)
    monkeypatch.setattr(settings, "ENABLE_HSTS", False)
    monkeypatch.setattr(settings, "ENABLE_X_FRAME_OPTIONS", False)

    response = client.get("/health")
    assert response.status_code == 200

    headers = response.headers

    assert "Content-Security-Policy" not in headers
    assert "Strict-Transport-Security" not in headers
    assert "X-Frame-Options" not in headers
