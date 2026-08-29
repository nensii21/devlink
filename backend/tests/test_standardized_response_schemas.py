"""
Unit & Integration Tests for Standardized API Response Schemas (#1067)

Verifies:
1. Standard response envelope format {"success": true, "data": {...}, "message": "...", "meta": {...}}
2. Standard list paginated response format with offset metadata.
3. Standard cursor paginated response format with next_cursor / has_more metadata.
4. Standard error envelope format {"success": false, "error": {"code": "...", "message": "...", "details": [...]}}
5. FastAPI integration with typed response models, status codes, and OpenAPI schema generation.
"""

from __future__ import annotations

from typing import List, Optional
import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.schemas.response import (
    CursorPaginationMetadata,
    PaginationMetadata,
    ResponseMetadata,
    StandardCursorResponse,
    StandardErrorItem,
    StandardErrorResponse,
    StandardListResponse,
    StandardResponse,
    cursor_response,
    error_response,
    paginated_response,
    success_response,
)


class SampleUser(BaseModel):
    id: str
    username: str
    email: str


class SampleProject(BaseModel):
    id: str
    title: str
    stage: str


class TestStandardResponseSchema:
    def test_standard_response_with_dict(self):
        payload = {"user_id": "123", "name": "Alice"}
        resp = success_response(data=payload, message="User retrieved successfully")

        assert resp.success is True
        assert resp.data == payload
        assert resp.message == "User retrieved successfully"
        assert resp.meta is not None
        assert resp.meta.version == "v1"
        assert resp.meta.timestamp is not None

        dumped = resp.model_dump()
        assert dumped["success"] is True
        assert dumped["data"]["user_id"] == "123"
        assert dumped["message"] == "User retrieved successfully"

    def test_standard_response_with_pydantic_model(self):
        user = SampleUser(id="u-1", username="bob", email="bob@example.com")
        resp = StandardResponse[SampleUser](success=True, data=user, message="Found")

        assert resp.success is True
        assert resp.data.username == "bob"
        assert resp.data.email == "bob@example.com"

        dumped = resp.model_dump()
        assert dumped["data"]["id"] == "u-1"

    def test_standard_response_with_none_data(self):
        resp = success_response(data=None, message="Action performed")
        assert resp.success is True
        assert resp.data is None
        assert resp.message == "Action performed"

    def test_standard_response_custom_request_id(self):
        resp = success_response(data={"ok": True}, request_id="req-abc-999")
        assert resp.meta.request_id == "req-abc-999"


class TestStandardListResponseSchema:
    def test_paginated_response_calculation_first_page(self):
        items = [
            SampleProject(id="p-1", title="Alpha", stage="beta"),
            SampleProject(id="p-2", title="Beta", stage="launched"),
        ]
        resp = paginated_response(
            data=items,
            page=1,
            limit=2,
            total=10,
            message="Projects page 1",
            request_id="req-proj-1",
        )

        assert resp.success is True
        assert len(resp.data) == 2
        assert resp.pagination is not None
        assert resp.pagination.page == 1
        assert resp.pagination.limit == 2
        assert resp.pagination.total == 10
        assert resp.pagination.total_pages == 5
        assert resp.pagination.has_next is True
        assert resp.pagination.has_prev is False
        assert resp.meta.request_id == "req-proj-1"

    def test_paginated_response_last_page(self):
        items = [SampleProject(id="p-5", title="Epsilon", stage="idea")]
        resp = paginated_response(data=items, page=5, limit=2, total=9)

        assert resp.pagination.page == 5
        assert resp.pagination.total_pages == 5
        assert resp.pagination.has_next is False
        assert resp.pagination.has_prev is True

    def test_paginated_response_empty_results(self):
        resp = paginated_response(data=[], page=1, limit=10, total=0)
        assert resp.pagination.total == 0
        assert resp.pagination.total_pages == 0
        assert resp.pagination.has_next is False
        assert resp.pagination.has_prev is False


class TestStandardCursorResponseSchema:
    def test_cursor_response_with_next(self):
        items = ["item1", "item2", "item3"]
        resp = cursor_response(
            data=items,
            limit=3,
            next_cursor="cur_next_123",
            prev_cursor=None,
            has_more=True,
            message="Cursor batch",
        )

        assert resp.success is True
        assert len(resp.data) == 3
        assert resp.cursor.next_cursor == "cur_next_123"
        assert resp.cursor.prev_cursor is None
        assert resp.cursor.has_more is True

    def test_cursor_response_terminal(self):
        items = ["item4"]
        resp = cursor_response(
            data=items,
            limit=3,
            next_cursor=None,
            prev_cursor="cur_prev_999",
            has_more=False,
        )

        assert resp.cursor.next_cursor is None
        assert resp.cursor.prev_cursor == "cur_prev_999"
        assert resp.cursor.has_more is False


class TestStandardErrorResponseSchema:
    def test_error_response_basic(self):
        err = error_response(
            code="PROJECT_NOT_FOUND",
            message="The requested project was not found in the catalog.",
            request_id="trace-err-404",
        )

        assert err.success is False
        assert err.error.code == "PROJECT_NOT_FOUND"
        assert err.error.message == "The requested project was not found in the catalog."
        assert err.meta.request_id == "trace-err-404"

    def test_error_response_with_details_and_field(self):
        err = error_response(
            code="VALIDATION_ERROR",
            message="The payload failed schema validation.",
            details=[{"loc": ["body", "title"], "msg": "field required", "type": "value_error.missing"}],
            field="title",
        )

        assert err.success is False
        assert err.error.code == "VALIDATION_ERROR"
        assert err.error.field == "title"
        assert isinstance(err.error.details, list)
        assert len(err.error.details) == 1

    def test_error_response_serialization(self):
        err = error_response(code="UNAUTHORIZED", message="Token expired")
        dumped = err.model_dump()
        assert dumped["success"] is False
        assert dumped["error"]["code"] == "UNAUTHORIZED"
        assert dumped["error"]["message"] == "Token expired"


class TestFastAPIRouteIntegration:
    @pytest.fixture
    def test_app(self):
        app = FastAPI(title="Standardized API Test App")

        @app.get(
            "/api/users/{user_id}",
            response_model=StandardResponse[SampleUser],
            status_code=status.HTTP_200_OK,
        )
        async def get_user(user_id: str):
            if user_id == "not_found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User does not exist",
                )
            return success_response(
                data=SampleUser(id=user_id, username=f"user_{user_id}", email=f"{user_id}@devlink.io"),
                message="User fetched",
            )

        @app.get(
            "/api/projects",
            response_model=StandardListResponse[SampleProject],
            status_code=status.HTTP_200_OK,
        )
        async def list_projects(page: int = 1, limit: int = 10):
            mock_projects = [
                SampleProject(id=f"p-{i}", title=f"Project {i}", stage="launched")
                for i in range(1, 4)
            ]
            return paginated_response(
                data=mock_projects,
                page=page,
                limit=limit,
                total=25,
            )

        @app.get(
            "/api/feed",
            response_model=StandardCursorResponse[str],
            status_code=status.HTTP_200_OK,
        )
        async def get_feed(cursor: Optional[str] = None, limit: int = 5):
            items = ["activity_1", "activity_2", "activity_3"]
            return cursor_response(
                data=items,
                limit=limit,
                next_cursor="cur_act_4",
                has_more=True,
            )

        return app

    def test_get_single_resource_success(self, test_app):
        client = TestClient(test_app)
        res = client.get("/api/users/usr_42")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["success"] is True
        assert data["message"] == "User fetched"
        assert data["data"]["id"] == "usr_42"
        assert data["data"]["username"] == "user_usr_42"
        assert data["data"]["email"] == "usr_42@devlink.io"
        assert "timestamp" in data["meta"]

    def test_list_paginated_resource_success(self, test_app):
        client = TestClient(test_app)
        res = client.get("/api/projects?page=2&limit=5")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["success"] is True
        assert len(data["data"]) == 3
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["limit"] == 5
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["total_pages"] == 5
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_prev"] is True

    def test_cursor_feed_success(self, test_app):
        client = TestClient(test_app)
        res = client.get("/api/feed?limit=5")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["success"] is True
        assert len(data["data"]) == 3
        assert data["cursor"]["limit"] == 5
        assert data["cursor"]["next_cursor"] == "cur_act_4"
        assert data["cursor"]["has_more"] is True

    def test_openapi_schema_contains_standard_responses(self, test_app):
        client = TestClient(test_app)
        res = client.get("/openapi.json")

        assert res.status_code == status.HTTP_200_OK
        schema = res.json()

        # Verify components schemas contain StandardResponse models
        schemas = schema.get("components", {}).get("schemas", {})
        assert any("StandardResponse" in name for name in schemas.keys())
        assert any("StandardListResponse" in name for name in schemas.keys())
        assert any("StandardCursorResponse" in name for name in schemas.keys())
