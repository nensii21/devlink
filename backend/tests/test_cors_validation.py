import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    return TestClient(app)


class TestCORSValidation:
    """Test CORS validation middleware behavior."""

    def test_request_without_origin_header_rejected(self, client):
        """Requests without Origin header should be rejected with 403."""
        response = client.get("/health")
        assert response.status_code == 403
        assert response.json()["detail"] == "Missing Origin header"

    def test_request_with_allowed_origin_accepted(self, client):
        """Requests with allowed Origin header should be accepted."""
        allowed_origin = settings.cors_origins[0]
        response = client.get("/health", headers={"origin": allowed_origin})
        assert response.status_code == 200

    def test_request_with_disallowed_origin_rejected(self, client):
        """Requests with disallowed Origin header should be rejected with 403."""
        response = client.get("/health", headers={"origin": "http://evil.com"})
        assert response.status_code == 403
        assert "not allowed" in response.json()["detail"]

    def test_all_allowed_origins_work(self, client):
        """All configured allowed origins should be accepted."""
        for origin in settings.cors_origins:
            response = client.get("/health", headers={"origin": origin})
            assert response.status_code == 200, f"Origin {origin} should be allowed"

    def test_cors_headers_present_for_allowed_origin(self, client):
        """CORS headers should be present for allowed origins."""
        allowed_origin = settings.cors_origins[0]
        response = client.get("/health", headers={"origin": allowed_origin})
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == allowed_origin

    def test_options_request_without_origin_rejected(self, client):
        """OPTIONS requests without Origin header should be rejected."""
        response = client.options("/health")
        assert response.status_code == 403
        assert response.json()["detail"] == "Missing Origin header"

    def test_options_request_with_allowed_origin_not_blocked_by_cors(self, client):
        """OPTIONS requests with allowed Origin should not be blocked by CORS validation (may return 405 for routing)."""
        allowed_origin = settings.cors_origins[0]
        response = client.options("/api/v1/health/dashboard", headers={"origin": allowed_origin})
        assert response.status_code != 403

    def test_post_request_without_origin_rejected(self, client):
        """POST requests without Origin header should be rejected."""
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 403
        assert response.json()["detail"] == "Missing Origin header"

    def test_post_request_with_allowed_origin_accepted(self, client):
        """POST requests with allowed Origin should be accepted (though may fail auth)."""
        allowed_origin = settings.cors_origins[0]
        response = client.post(
            "/api/auth/login",
            json={"email": "test@test.com", "password": "password"},
            headers={"origin": allowed_origin},
        )
        assert response.status_code != 403