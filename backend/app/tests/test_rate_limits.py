import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)


@pytest.fixture(autouse=True)
def enable_rate_limiter_for_tests(monkeypatch):
    """
    Ensure the rate limiter is enabled during these tests.
    """
    # SlowAPI uses the limiter instance attached to app.state
    # We will override the config values directly.
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", True)

    # Since limits might be high (like 100/minute), we clear the storage before and after
    from app.middleware.rate_limit import limiter

    limiter.reset()
    yield limiter
    limiter.reset()


def test_rate_limit_headers_present():
    """
    Test that standard rate-limit headers are present when headers_enabled=True.
    """
    response = client.get("/health")
    assert response.status_code == 200

    # SlowAPI adds these headers by default when headers_enabled is True
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_rate_limit_exceeded(enable_rate_limiter_for_tests, monkeypatch):
    """
    Test that exceeding the rate limit returns a 429 status code.
    We mock the get_remote_address to use a specific IP so we don't interfere with other tests.
    """
    # Temporarily set a very low limit for the health endpoint to test 429
    limiter = enable_rate_limiter_for_tests

    # The default limit is 100/minute.
    # We will hit the /health endpoint 100 times, which shouldn't hit the DB.

    for _ in range(100):
        response = client.get("/health")
        assert response.status_code == 200

    # The 101st request should fail with 429 Too Many Requests
    response = client.get("/health")
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert "Rate limit exceeded" in response.text
