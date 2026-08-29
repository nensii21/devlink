from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.main import app
from app.core.exceptions import (
    AppException,
    AuthException,
    DatabaseException,
    ValidationException,
)

# ------------------------------------------------------------------
# Add temporary test routes to the app instance for testing
# ------------------------------------------------------------------


@app.get("/test-error-handler/http-exception")
def route_http_exception():
    raise HTTPException(status_code=400, detail="Test Bad Request")


@app.get("/test-error-handler/app-exception")
def route_app_exception():
    raise AppException(
        message="Custom application error",
        status_code=400,
        code="CUSTOM_APP_ERROR",
        details={"foo": "bar"},
    )


@app.get("/test-error-handler/auth-exception")
def route_auth_exception():
    raise AuthException(
        message="Custom auth error", status_code=401, code="CUSTOM_AUTH_ERROR"
    )


@app.get("/test-error-handler/database-exception")
def route_database_exception():
    raise DatabaseException(
        message="Custom database error", status_code=500, code="CUSTOM_DB_ERROR"
    )


@app.get("/test-error-handler/validation-exception")
def route_validation_exception():
    raise ValidationException(
        message="Custom validation error", status_code=422, code="CUSTOM_VAL_ERROR"
    )


@app.get("/test-error-handler/sqlalchemy-error")
def route_sqlalchemy_error():
    raise SQLAlchemyError("Generic database failure")


@app.get("/test-error-handler/integrity-error")
def route_integrity_error():
    class MockOrigException:
        def __str__(self):
            return 'duplicate key value violates unique constraint "ix_users_email"\nDETAIL: Key (email)=(test@example.com) already exists.'

    raise IntegrityError("select 1", {}, MockOrigException())


@app.get("/test-error-handler/general-exception")
def route_general_exception():
    raise ValueError("Something went terribly wrong internally")


@pytest.fixture(name="client")
def fixture_client():
    return TestClient(app)


def test_http_exception_handling(client):
    response = client.get("/test-error-handler/http-exception")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "TEST_BAD_REQUEST"
    assert data["error"]["message"] == "Test Bad Request"
    assert "detail" in data
    assert data["detail"] == "Test Bad Request"


def test_app_exception_handling(client):
    response = client.get("/test-error-handler/app-exception")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "CUSTOM_APP_ERROR"
    assert data["error"]["message"] == "Custom application error"
    assert data["error"]["details"] == {"foo": "bar"}
    assert data["detail"] == "Custom application error"


def test_auth_exception_handling(client):
    response = client.get("/test-error-handler/auth-exception")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "CUSTOM_AUTH_ERROR"
    assert data["error"]["message"] == "Custom auth error"


def test_database_exception_handling(client):
    response = client.get("/test-error-handler/database-exception")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "CUSTOM_DB_ERROR"


def test_validation_exception_handling(client):
    response = client.get("/test-error-handler/validation-exception")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "CUSTOM_VAL_ERROR"
    assert data["error"]["message"] == "Custom validation error"


def test_generic_sqlalchemy_error_handling(client):
    response = client.get("/test-error-handler/sqlalchemy-error")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "DATABASE_ERROR"
    assert (
        data["error"]["message"] == "A database error occurred. Please try again later."
    )
    # Ensure raw DB failure message is NOT exposed to client
    assert "Generic database failure" not in str(data)


def test_integrity_error_handling_sanitization(client):
    response = client.get("/test-error-handler/integrity-error")
    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "CONFLICT"
    assert data["error"]["message"] == "The email provided is already in use."
    # Ensure details are sanitized/friendly and do NOT contain raw trace/SQL structures
    assert data["error"]["details"] == {"duplicate_field": "email"}
    assert "violates unique constraint" not in str(data)


def test_unhandled_value_error_handling(client):
    # `add_exception_handler(Exception, ...)` is installed on Starlette's
    # ServerErrorMiddleware, which builds the response and *then* re-raises so
    # the server still logs the fault. TestClient surfaces that re-raise unless
    # it is told not to, so the response is unreachable through the default
    # client. test_error_responses.py does the same thing for the same reason.
    client = TestClient(client.app, raise_server_exceptions=False)

    response = client.get("/test-error-handler/general-exception")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "An unexpected internal server error occurred."
    # Ensure traceback or specific python error details are NOT leaked to client
    assert "Something went terribly wrong internally" not in str(data)
