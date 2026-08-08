from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from limits import parse as parse_limit
from pydantic import BaseModel, Field, field_validator
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_handlers import (
    generate_error_code,
    global_exception_handler,
    http_exception_handler,
    rate_limit_exception_handler,
    validation_exception_handler,
)


@pytest.fixture
def test_app():
    app = FastAPI()

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    class DummyPayload(BaseModel):
        name: str = Field(..., min_length=2)

    @app.get("/test/not-found")
    def trigger_not_found():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    @app.get("/test/unauthorized")
    def trigger_unauthorized():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        )

    @app.get("/test/custom-dict")
    def trigger_custom_dict():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CUSTOM_ERROR_CODE", "message": "Custom error message."},
        )

    @app.post("/test/validation")
    def trigger_validation(payload: DummyPayload):
        return {"success": True}

    class DummyLimit:
        error_message = "Rate limit exceeded"

    @app.get("/test/rate-limit")
    def trigger_rate_limit():
        raise RateLimitExceeded(DummyLimit())

    @app.get("/test/server-error")
    def trigger_server_error():
        raise RuntimeError("Something exploded")

    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


def test_generate_error_code_helper():
    assert generate_error_code(404, "Project not found.") == "PROJECT_NOT_FOUND"
    assert (
        generate_error_code(401, "Invalid authentication credentials.")
        == "INVALID_AUTHENTICATION_CREDENTIALS"
    )
    assert generate_error_code(400, "Bad Request") == "BAD_REQUEST"
    assert generate_error_code(404, None) == "NOT_FOUND"


def test_http_exception_404_format(client):
    response = client.get("/test/not-found")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PROJECT_NOT_FOUND"
    assert data["error"]["message"] == "Project not found."


def test_http_exception_401_format(client):
    response = client.get("/test/unauthorized")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_AUTHENTICATION_CREDENTIALS"
    assert data["error"]["message"] == "Invalid authentication credentials."


def test_http_exception_custom_dict_format(client):
    response = client.get("/test/custom-dict")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "CUSTOM_ERROR_CODE"
    assert data["error"]["message"] == "Custom error message."


def test_validation_error_format(client):
    response = client.post("/test/validation", json={})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "Validation error" in data["error"]["message"]
    assert "details" in data["error"]


def test_rate_limit_error_format(client):
    response = client.get("/test/rate-limit")
    assert response.status_code == 429
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Rate limit exceeded" in data["error"]["message"]


def test_server_error_format(client):
    # TestClient re-raises unhandled exceptions unless raise_server_exceptions is False
    client_no_raise = TestClient(client.app, raise_server_exceptions=False)
    response = client_no_raise.get("/test/server-error")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "unexpected internal server error" in data["error"]["message"]


# ---------------------------------------------------------------------------
# Custom validators (regression, #930)
# ---------------------------------------------------------------------------


class BlankRejectingPayload(BaseModel):
    """Defined at module level so `from __future__ import annotations` can
    still resolve it -- FastAPI reads the annotation via get_type_hints, which
    cannot see a class defined inside a test function."""

    name: str

    @field_validator("name")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        return value


# The route is built at module scope with a concrete annotation. Under
# `from __future__ import annotations` every annotation is a string, and
# FastAPI resolves them with get_type_hints against the module globals -- so a
# model (or a parameterised helper) defined inside a test function resolves to
# nothing and the body is misread as a query parameter.
_validator_app = FastAPI()
_validator_app.add_exception_handler(
    RequestValidationError, validation_exception_handler
)


@_validator_app.post("/custom-validator")
def _custom_validator_endpoint(
    payload: BlankRejectingPayload,
):  # pragma: no cover - exercised via client
    return {"name": payload.name}


_validator_client = TestClient(_validator_app)


def test_custom_validator_error_returns_422_not_a_crash():
    """A `field_validator` raising ValueError must still render a 422.

    Pydantic v2 puts the exception *object* into the error entry's `ctx`:

        {'type': 'value_error', ..., 'ctx': {'error': ValueError('...')}}

    Passing that straight to JSONResponse raised

        TypeError: Object of type ValueError is not JSON serializable

    while rendering the response, so the handler crashed instead of answering.
    Every endpoint whose schema uses a custom validator was affected.
    """
    response = _validator_client.post("/custom-validator", json={"name": "   "})

    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "name cannot be blank" in data["error"]["message"]


def test_custom_validator_error_details_are_serialisable():
    """The `ctx` survives sanitising as a string rather than being lost."""
    response = _validator_client.post("/custom-validator", json={"name": ""})
    details = response.json()["error"]["details"]

    assert response.status_code == 422
    assert isinstance(details, list) and details
    assert details[0]["type"] == "value_error"
    assert isinstance(details[0]["loc"], list)
    assert isinstance(details[0].get("ctx", {}).get("error", ""), str)
