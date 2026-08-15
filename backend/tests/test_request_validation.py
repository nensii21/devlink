import pytest
from fastapi import FastAPI, Query
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.error_handlers import validation_exception_handler
from app.middleware.request_validation import (
    RequestValidationMiddleware,
    validate_query_param,
    validate_path_param,
)

# Test App setup
dummy_app = FastAPI()
dummy_app.add_middleware(RequestValidationMiddleware)
dummy_app.add_exception_handler(RequestValidationError, validation_exception_handler)


class SampleRequestBody(BaseModel):
    title: str = Field(..., min_length=3)
    age: int = Field(..., ge=18, le=100)


@dummy_app.post("/sample/body")
def sample_body_handler(payload: SampleRequestBody):
    return {"message": "Success", "title": payload.title}


@dummy_app.get("/sample/query")
def sample_query_handler(
    page: int = Query(..., ge=1),
    limit: int = Query(..., le=50),
):
    return {"page": page, "limit": limit}


client = TestClient(dummy_app)


def test_valid_request_body():
    response = client.post("/sample/body", json={"title": "DevLink", "age": 25})
    assert response.status_code == 200
    assert response.json() == {"message": "Success", "title": "DevLink"}


def test_invalid_request_body_standardized_error():
    response = client.post("/sample/body", json={"title": "a", "age": 12})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_invalid_query_parameters():
    response = client.get("/sample/query?page=0&limit=100")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_validate_query_param_utility():
    with pytest.raises(Exception):
        validate_query_param(value=0, param_name="page", min_val=1)


def test_validate_path_param_utility():
    with pytest.raises(Exception):
        validate_path_param(value="", param_name="user_id")
