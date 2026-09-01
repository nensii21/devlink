"""Tests for the Contribution Board feature.

Covers board CRUD, column management, task CRUD, drag-and-drop movement,
assignments, comments, activity logging, and board statistics.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Register and log in a user, return Authorization headers."""
    email = f"board-user-{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123!"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": password,
            "display_name": "Board Tester",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    token = resp.json().get("access_token") or resp.json().get("token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_auth_headers(client: TestClient) -> dict:
    """Register and log in a second user for assignment tests."""
    email = f"board-user2-{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123!"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": f"user2_{uuid.uuid4().hex[:8]}",
            "password": password,
            "display_name": "Board Tester 2",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    token = resp.json().get("access_token") or resp.json().get("token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project_id(client: TestClient, auth_headers: dict) -> str:
    """Create a project and return its ID."""
    resp = client.post(
        "/api/projects",
        headers=auth_headers,
        json={
            "title": f"Board Test Project {uuid.uuid4().hex[:6]}",
            "description": "A project for testing contribution boards",
            "visibility": "public",
        },
    )
    assert resp.status_code in (200, 201), f"Project creation failed: {resp.text}"
    return resp.json()["id"]


@pytest.fixture
def board_id(
    client: TestClient, auth_headers: dict, project_id: str
) -> str:
    """Create a contribution board and return its ID."""
    resp = client.post(
        f"/api/contribution-boards/{project_id}",
        headers=auth_headers,
        json={
            "title": "Sprint Board",
            "description": "Main sprint board for current iteration",
            "columns": [
                {"title": "Backlog", "position": 0, "color": "#6b7280"},
                {"title": "In Progress", "position": 1, "color": "#f59e0b"},
                {"title": "In Review", "position": 2, "color": "#8b5cf6"},
                {"title": "Done", "position": 3, "color": "#10b981"},
            ],
        },
    )
    assert resp.status_code == 201, f"Board creation failed: {resp.text}"
    return resp.json()["id"]


# ── Board CRUD Tests ──────────────────────────────────────────────────────────


class TestBoardCRUD:
    def test_create_board(self, client, auth_headers, project_id):
        resp = client.post(
            f"/api/contribution-boards/{project_id}",
            headers=auth_headers,
            json={
                "title": "My Board",
                "description": "Test board",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My Board"
        assert data["description"] == "Test board"
        assert data["project_id"] == project_id
        assert len(data["columns"]) == 5  # default columns

    def test_create_board_with_custom_columns(self, client, auth_headers, project_id):
        resp = client.post(
            f"/api/contribution-boards/{project_id}",
            headers=auth_headers,
            json={
                "title": "Custom Board",
                "columns": [
                    {"title": "To Do", "position": 0, "color": "#3b82f6"},
                    {"title": "Doing", "position": 1, "color": "#f59e0b"},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["columns"]) == 2
        assert data["columns"][0]["title"] == "To Do"
        assert data["columns"][1]["title"] == "Doing"

    def test_list_boards(self, client, auth_headers, project_id, board_id):
        resp = client.get(
            f"/api/contribution-boards/{project_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any(b["id"] == board_id for b in data["items"])

    def test_get_board(self, client, auth_headers, board_id):
        resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == board_id
        assert data["title"] == "Sprint Board"
        assert len(data["columns"]) == 4

    def test_update_board(self, client, auth_headers, board_id):
        resp = client.patch(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
            json={"title": "Updated Sprint Board"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Sprint Board"

    def test_delete_board(self, client, auth_headers, board_id):
        resp = client.delete(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

        # Verify deleted
        resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_get_nonexistent_board(self, client, auth_headers):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/contribution-boards/board/{fake_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_create_board_unauthorized(self, client, project_id):
        resp = client.post(
            f"/api/contribution-boards/{project_id}",
            json={"title": "No Auth Board"},
        )
        assert resp.status_code in (401, 403)

    def test_create_board_invalid_project(self, client, auth_headers):
        resp = client.post(
            f"/api/contribution-boards/{uuid.uuid4()}",
            headers=auth_headers,
            json={"title": "Bad Project Board"},
        )
        assert resp.status_code == 404


# ── Column Management Tests ───────────────────────────────────────────────────


class TestColumnManagement:
    def test_create_column(self, client, auth_headers, board_id):
        resp = client.post(
            f"/api/contribution-boards/board/{board_id}/columns",
            headers=auth_headers,
            json={"title": "Blocked", "color": "#da3633"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Blocked"
        assert data["color"] == "#da3633"

    def test_update_column(self, client, auth_headers, board_id):
        # Get first column
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        col_id = board_resp.json()["columns"][0]["id"]

        resp = client.patch(
            f"/api/contribution-boards/columns/{col_id}",
            headers=auth_headers,
            json={"title": "Icebox", "wip_limit": 5},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Icebox"
        assert resp.json()["wip_limit"] == 5

    def test_delete_column(self, client, auth_headers, board_id):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        col_id = board_resp.json()["columns"][-1]["id"]

        resp = client.delete(
            f"/api/contribution-boards/columns/{col_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    def test_reorder_columns(self, client, auth_headers, board_id):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        cols = board_resp.json()["columns"]
        col_ids = [c["id"] for c in reversed(cols)]

        resp = client.patch(
            f"/api/contribution-boards/board/{board_id}/columns/reorder",
            headers=auth_headers,
            json=col_ids,
        )
        assert resp.status_code == 200
        reordered = resp.json()
        assert reordered[0]["id"] == col_ids[0]


# ── Task CRUD Tests ───────────────────────────────────────────────────────────


class TestTaskCRUD:
    def _get_column_id(self, client, auth_headers, board_id, index=0):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        return board_resp.json()["columns"][index]["id"]

    def test_create_task(self, client, auth_headers, board_id):
        col_id = self._get_column_id(client, auth_headers, board_id)
        resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={
                "title": "Implement feature X",
                "description": "This is a detailed description",
                "column_id": col_id,
                "priority": "high",
                "estimated_hours": 8,
                "labels": "backend,api",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Implement feature X"
        assert data["priority"] == "high"
        assert data["estimated_hours"] == 8
        assert data["labels"] == "backend,api"

    def test_list_tasks(self, client, auth_headers, board_id):
        col_id = self._get_column_id(client, auth_headers, board_id)

        # Create a few tasks
        for i in range(3):
            client.post(
                f"/api/contribution-boards/board/{board_id}/tasks",
                headers=auth_headers,
                json={
                    "title": f"Task {i+1}",
                    "column_id": col_id,
                    "priority": "medium",
                },
            )

        resp = client.get(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 3

    def test_get_task(self, client, auth_headers, board_id):
        col_id = self._get_column_id(client, auth_headers, board_id)
        create_resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Get this task", "column_id": col_id},
        )
        task_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/contribution-boards/tasks/{task_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get this task"

    def test_update_task(self, client, auth_headers, board_id):
        col_id = self._get_column_id(client, auth_headers, board_id)
        create_resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Original title", "column_id": col_id},
        )
        task_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/contribution-boards/tasks/{task_id}",
            headers=auth_headers,
            json={
                "title": "Updated title",
                "priority": "critical",
                "estimated_hours": 16,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated title"
        assert data["priority"] == "critical"
        assert data["estimated_hours"] == 16

    def test_delete_task(self, client, auth_headers, board_id):
        col_id = self._get_column_id(client, auth_headers, board_id)
        create_resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Delete me", "column_id": col_id},
        )
        task_id = create_resp.json()["id"]

        resp = client.delete(
            f"/api/contribution-boards/tasks/{task_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

        resp = client.get(
            f"/api/contribution-boards/tasks/{task_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_filter_tasks_by_priority(self, client, auth_headers, board_id):
        col_id = self._get_column_id(client, auth_headers, board_id)

        client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Low task", "column_id": col_id, "priority": "low"},
        )
        client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "High task", "column_id": col_id, "priority": "high"},
        )

        resp = client.get(
            f"/api/contribution-boards/board/{board_id}/tasks?priority=high",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["priority"] == "high"

    def test_search_tasks(self, client, auth_headers, board_id):
        col_id = self._get_column_id(client, auth_headers, board_id)

        client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Fix login bug", "column_id": col_id},
        )
        client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Add dark mode", "column_id": col_id},
        )

        resp = client.get(
            f"/api/contribution-boards/board/{board_id}/tasks?search=login",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
        assert any("login" in item["title"].lower() for item in resp.json()["items"])


# ── Task Movement Tests ───────────────────────────────────────────────────────


class TestTaskMovement:
    def _create_task_in_column(self, client, auth_headers, board_id, col_index):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        col_id = board_resp.json()["columns"][col_index]["id"]
        resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": f"Moveable task", "column_id": col_id},
        )
        return resp.json()["id"], col_id

    def test_move_task_to_different_column(self, client, auth_headers, board_id):
        task_id, _ = self._create_task_in_column(client, auth_headers, board_id, 0)
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        target_col = board_resp.json()["columns"][1]["id"]

        resp = client.post(
            f"/api/contribution-boards/tasks/{task_id}/move",
            headers=auth_headers,
            json={"column_id": target_col, "position": 0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["column_id"] == target_col

    def test_move_task_reorders_positions(
        self, client, auth_headers, board_id
    ):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        col_id = board_resp.json()["columns"][0]["id"]

        # Create two tasks
        t1_resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "First", "column_id": col_id},
        )
        t2_resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Second", "column_id": col_id},
        )
        t1_id = t1_resp.json()["id"]

        # Move t1 to position 1 (push t2 to position 2)
        resp = client.post(
            f"/api/contribution-boards/tasks/{t1_id}/move",
            headers=auth_headers,
            json={"column_id": col_id, "position": 1},
        )
        assert resp.status_code == 200

    def test_move_nonexistent_task(self, client, auth_headers, board_id):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        col_id = board_resp.json()["columns"][0]["id"]

        resp = client.post(
            f"/api/contribution-boards/tasks/{uuid.uuid4()}/move",
            headers=auth_headers,
            json={"column_id": col_id, "position": 0},
        )
        assert resp.status_code == 404


# ── Assignment Tests ──────────────────────────────────────────────────────────


class TestAssignments:
    def _create_task(self, client, auth_headers, board_id):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        col_id = board_resp.json()["columns"][0]["id"]
        resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Assignable task", "column_id": col_id},
        )
        return resp.json()["id"]

    def _get_user_id(self, client, auth_headers):
        resp = client.get("/api/users/me", headers=auth_headers)
        return resp.json()["id"]

    def test_assign_user(self, client, auth_headers, second_auth_headers, board_id):
        task_id = self._create_task(client, auth_headers, board_id)
        user_id = self._get_user_id(client, second_auth_headers)

        resp = client.post(
            f"/api/contribution-boards/tasks/{task_id}/assign/{user_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 201

    def test_duplicate_assignment_conflict(
        self, client, auth_headers, second_auth_headers, board_id
    ):
        task_id = self._create_task(client, auth_headers, board_id)
        user_id = self._get_user_id(client, second_auth_headers)

        client.post(
            f"/api/contribution-boards/tasks/{task_id}/assign/{user_id}",
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/contribution-boards/tasks/{task_id}/assign/{user_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_unassign_user(self, client, auth_headers, second_auth_headers, board_id):
        task_id = self._create_task(client, auth_headers, board_id)
        user_id = self._get_user_id(client, second_auth_headers)

        client.post(
            f"/api/contribution-boards/tasks/{task_id}/assign/{user_id}",
            headers=auth_headers,
        )
        resp = client.delete(
            f"/api/contribution-boards/tasks/{task_id}/assign/{user_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204


# ── Comment Tests ─────────────────────────────────────────────────────────────


class TestComments:
    def _create_task(self, client, auth_headers, board_id):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        col_id = board_resp.json()["columns"][0]["id"]
        resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Commentable task", "column_id": col_id},
        )
        return resp.json()["id"]

    def test_add_comment(self, client, auth_headers, board_id):
        task_id = self._create_task(client, auth_headers, board_id)
        resp = client.post(
            f"/api/contribution-boards/tasks/{task_id}/comments",
            headers=auth_headers,
            json={"content": "This needs more work on the frontend side."},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "This needs more work on the frontend side."

    def test_list_comments(self, client, auth_headers, board_id):
        task_id = self._create_task(client, auth_headers, board_id)

        for i in range(3):
            client.post(
                f"/api/contribution-boards/tasks/{task_id}/comments",
                headers=auth_headers,
                json={"content": f"Comment {i+1}"},
            )

        resp = client.get(
            f"/api/contribution-boards/tasks/{task_id}/comments",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_add_reply_to_comment(self, client, auth_headers, board_id):
        task_id = self._create_task(client, auth_headers, board_id)

        parent_resp = client.post(
            f"/api/contribution-boards/tasks/{task_id}/comments",
            headers=auth_headers,
            json={"content": "Parent comment"},
        )
        parent_id = parent_resp.json()["id"]

        reply_resp = client.post(
            f"/api/contribution-boards/tasks/{task_id}/comments",
            headers=auth_headers,
            json={
                "content": "Reply to parent",
                "parent_comment_id": parent_id,
            },
        )
        assert reply_resp.status_code == 201
        assert reply_resp.json()["parent_comment_id"] == parent_id

    def test_delete_own_comment(self, client, auth_headers, board_id):
        task_id = self._create_task(client, auth_headers, board_id)

        comment_resp = client.post(
            f"/api/contribution-boards/tasks/{task_id}/comments",
            headers=auth_headers,
            json={"content": "Delete this comment"},
        )
        comment_id = comment_resp.json()["id"]

        resp = client.delete(
            f"/api/contribution-boards/comments/{comment_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204


# ── Activity Log Tests ────────────────────────────────────────────────────────


class TestActivityLog:
    def _create_task(self, client, auth_headers, board_id):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        col_id = board_resp.json()["columns"][0]["id"]
        resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Activity task", "column_id": col_id},
        )
        return resp.json()["id"]

    def test_activity_on_task_creation(self, client, auth_headers, board_id):
        task_id = self._create_task(client, auth_headers, board_id)
        resp = client.get(
            f"/api/contribution-boards/tasks/{task_id}/activity",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        activities = resp.json()
        assert len(activities) >= 1
        assert activities[0]["action"] == "created"

    def test_activity_on_task_update(self, client, auth_headers, board_id):
        task_id = self._create_task(client, auth_headers, board_id)

        client.patch(
            f"/api/contribution-boards/tasks/{task_id}",
            headers=auth_headers,
            json={"priority": "critical"},
        )

        resp = client.get(
            f"/api/contribution-boards/tasks/{task_id}/activity",
            headers=auth_headers,
        )
        activities = resp.json()
        update_actions = [a for a in activities if "updated" in a["action"]]
        assert len(update_actions) >= 1

    def test_activity_on_task_move(self, client, auth_headers, board_id):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        cols = board_resp.json()["columns"]

        resp = client.post(
            f"/api/contribution-boards/board/{board_id}/tasks",
            headers=auth_headers,
            json={"title": "Move activity task", "column_id": cols[0]["id"]},
        )
        task_id = resp.json()["id"]

        client.post(
            f"/api/contribution-boards/tasks/{task_id}/move",
            headers=auth_headers,
            json={"column_id": cols[1]["id"], "position": 0},
        )

        resp = client.get(
            f"/api/contribution-boards/tasks/{task_id}/activity",
            headers=auth_headers,
        )
        move_actions = [a for a in resp.json() if a["action"] == "moved"]
        assert len(move_actions) >= 1


# ── Board Statistics Tests ────────────────────────────────────────────────────


class TestBoardStatistics:
    def test_get_statistics(self, client, auth_headers, board_id):
        resp = client.get(
            f"/api/contribution-boards/board/{board_id}/statistics",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["board_id"] == board_id
        assert "total_tasks" in data
        assert "tasks_by_priority" in data
        assert "tasks_by_column" in data

    def test_statistics_reflect_tasks(self, client, auth_headers, board_id):
        board_resp = client.get(
            f"/api/contribution-boards/board/{board_id}",
            headers=auth_headers,
        )
        col_id = board_resp.json()["columns"][0]["id"]

        # Create some tasks
        for i in range(5):
            client.post(
                f"/api/contribution-boards/board/{board_id}/tasks",
                headers=auth_headers,
                json={"title": f"Stats task {i}", "column_id": col_id},
            )

        resp = client.get(
            f"/api/contribution-boards/board/{board_id}/statistics",
            headers=auth_headers,
        )
        data = resp.json()
        assert data["total_tasks"] >= 5

    def test_statistics_nonexistent_board(self, client, auth_headers):
        resp = client.get(
            f"/api/contribution-boards/board/{uuid.uuid4()}/statistics",
            headers=auth_headers,
        )
        assert resp.status_code == 404
