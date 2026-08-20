"""The shape of the error envelope itself.

`tests/test_error_responses.py` and `tests/test_global_error_handler.py`
already check that each handler produces the right code for the right
situation. What neither of them checked is the thing that actually broke: the
*name* of the field carrying that code.

The envelope was emitted with `error_code` while the docstring, the input side
of `http_exception_handler` and every assertion in the suite used `code`. Both
halves were individually consistent, so nothing pointed at the seam. These
tests hold the seam.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_handlers import (
    DEPRECATED_ERROR_CODE_KEY,
    ERROR_CODE_KEY,
    app_exception_handler,
    global_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    rate_limit_exception_handler,
    sqlalchemy_error_handler,
    validation_exception_handler,
)
from app.core.exceptions import AppException, AuthException, ValidationException


@pytest.fixture(name="client")
def fixture_client() -> TestClient:
    """An app wired with the real handlers and nothing else.

    Deliberately not `app.main:app` -- these tests are about the envelope, and
    a route that exists only to raise is clearer than hunting for a real
    endpoint that happens to fail the right way.
    """
    app = FastAPI()

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    class Payload(BaseModel):
        name: str = Field(..., min_length=2)

    @app.get("/string-detail")
    def string_detail():
        raise HTTPException(status_code=404, detail="Project not found.")

    @app.get("/structured-detail")
    def structured_detail():
        # The `code` spelling here is the input contract, and it is what made
        # the mismatch absurd: the handler reads `code` out and used to write
        # `error_code` back.
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PROJECT_FORBIDDEN",
                "message": "You cannot touch this project.",
                "details": {"project_id": "abc"},
            },
        )

    @app.get("/typed-auth")
    def typed_auth():
        raise AuthException(message="Nope.", status_code=401, code="TOKEN_EXPIRED")

    @app.get("/typed-validation")
    def typed_validation():
        raise ValidationException(
            message="Slug is taken.",
            status_code=422,
            code="SLUG_TAKEN",
            details={"field": "slug"},
        )

    @app.post("/validated")
    def validated(payload: Payload):
        return payload

    @app.get("/rate-limited")
    def rate_limited():
        raise RateLimitExceeded(_DummyLimit())

    @app.get("/integrity")
    def integrity():
        raise IntegrityError("INSERT INTO users ...", {}, _DuplicateEmail())

    @app.get("/db-error")
    def db_error():
        raise SQLAlchemyError("connection to server at 10.0.0.4 failed: password auth")

    @app.get("/boom")
    def boom():
        raise ValueError("secret internal state: token=abc123")

    return TestClient(app, raise_server_exceptions=False)


class _DummyLimit:
    """Minimal stand-in for a SlowAPI limit object."""

    error_message = "1 per second"
    limit = "1 per second"

    def __str__(self) -> str:  # pragma: no cover - only for repr in failures
        return self.limit


class _DuplicateEmail:
    """Stands in for the psycopg error `IntegrityError` wraps."""

    def __str__(self) -> str:
        return (
            'duplicate key value violates unique constraint "ix_users_email"\n'
            "DETAIL:  Key (email)=(victim@example.com) already exists."
        )


ALL_ERROR_PATHS = [
    ("/string-detail", 404),
    ("/structured-detail", 403),
    ("/typed-auth", 401),
    ("/typed-validation", 422),
    ("/rate-limited", 429),
    ("/integrity", 409),
    ("/db-error", 500),
    ("/boom", 500),
]


@pytest.mark.parametrize("path,expected_status", ALL_ERROR_PATHS)
def test_every_handler_emits_the_canonical_code_key(
    client: TestClient, path: str, expected_status: int
) -> None:
    """`error.code` is present on every path out of the application.

    Parametrised over every registered handler rather than spot-checked,
    because the previous break was one handler's worth of inconsistency and a
    spot check is exactly what missed it.
    """
    response = client.get(path)

    assert response.status_code == expected_status
    error = response.json()["error"]

    assert ERROR_CODE_KEY in error, f"{path} has no {ERROR_CODE_KEY!r}"
    assert isinstance(error[ERROR_CODE_KEY], str)
    assert error[ERROR_CODE_KEY], f"{path} has an empty code"


@pytest.mark.parametrize("path,expected_status", ALL_ERROR_PATHS)
def test_deprecated_alias_matches_the_canonical_key(
    client: TestClient, path: str, expected_status: int
) -> None:
    """`error_code` still ships, and always agrees with `code`.

    Nothing in this repository reads it, but responses carried it for long
    enough that something outside might. Two keys that can disagree would be
    worse than one wrong key, so they are asserted equal rather than merely
    both present.
    """
    error = client.get(path).json()["error"]

    assert DEPRECATED_ERROR_CODE_KEY in error
    assert error[DEPRECATED_ERROR_CODE_KEY] == error[ERROR_CODE_KEY]


@pytest.mark.parametrize("path,expected_status", ALL_ERROR_PATHS)
def test_envelope_always_carries_message_timestamp_and_request_id(
    client: TestClient, path: str, expected_status: int
) -> None:
    """The rest of the envelope is not optional either."""
    body = client.get(path).json()
    error = body["error"]

    assert error["message"]
    assert error["timestamp"]
    assert error["request_id"]
    assert body["detail"] == error["message"], "detail must mirror the human message"


def test_structured_detail_code_survives_the_round_trip(client: TestClient) -> None:
    """What a route writes as `code` is what the caller reads as `code`."""
    error = client.get("/structured-detail").json()["error"]

    assert error[ERROR_CODE_KEY] == "PROJECT_FORBIDDEN"
    assert error["message"] == "You cannot touch this project."
    assert error["details"] == {"project_id": "abc"}


def test_string_detail_is_derived_into_a_code(client: TestClient) -> None:
    """A plain string detail still gets a machine-readable code."""
    error = client.get("/string-detail").json()["error"]

    assert error[ERROR_CODE_KEY] == "PROJECT_NOT_FOUND"


def test_typed_exceptions_keep_their_status_and_code(client: TestClient) -> None:
    """`AppException` subclasses are no longer flattened into a 500.

    Without a handler these fell through to `global_exception_handler`, so a
    401 `TOKEN_EXPIRED` reached the client as a 500 `INTERNAL_SERVER_ERROR`
    and the caller had no way to tell "log in again" from "we are broken".
    """
    auth = client.get("/typed-auth")
    assert auth.status_code == 401
    assert auth.json()["error"][ERROR_CODE_KEY] == "TOKEN_EXPIRED"

    validation = client.get("/typed-validation")
    assert validation.status_code == 422
    body = validation.json()["error"]
    assert body[ERROR_CODE_KEY] == "SLUG_TAKEN"
    assert body["details"] == {"field": "slug"}


def test_validation_errors_use_the_same_envelope(client: TestClient) -> None:
    """422s from Pydantic are not a special case."""
    response = client.post("/validated", json={"name": "x"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error[ERROR_CODE_KEY] == "VALIDATION_ERROR"
    assert isinstance(error["details"], list)
    assert error["details"], "validation errors should say which field failed"


def test_integrity_error_names_the_field_without_echoing_the_value(
    client: TestClient,
) -> None:
    """A duplicate-key 409 must not read the row back to the caller.

    `details` used to be the raw driver string, which contains both the
    physical index name and the colliding value. On a signup form that meant
    replying to "this email is taken" with the email on the existing account.
    """
    response = client.get("/integrity")
    body = response.text
    error = response.json()["error"]

    assert response.status_code == 409
    assert error[ERROR_CODE_KEY] == "CONFLICT"
    assert error["details"] == {"duplicate_field": "email"}

    assert "victim@example.com" not in body
    assert "ix_users_email" not in body
    assert "violates unique constraint" not in body


def test_database_errors_do_not_leak_the_driver_message(client: TestClient) -> None:
    """Connection strings and bound parameters stay in the log."""
    response = client.get("/db-error")

    assert response.status_code == 500
    assert response.json()["error"][ERROR_CODE_KEY] == "DATABASE_ERROR"
    assert "10.0.0.4" not in response.text
    assert "password auth" not in response.text


def test_unhandled_errors_do_not_leak_internal_state(client: TestClient) -> None:
    """The catch-all says nothing about what actually went wrong."""
    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json()["error"][ERROR_CODE_KEY] == "INTERNAL_SERVER_ERROR"
    assert "token=abc123" not in response.text
