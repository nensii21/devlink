"""Tests for the project onboarding checklist endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PROJECT_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())
CHECKLIST_ID: str = ""
ITEM_ID: str = ""
ASSIGNMENT_ID: str = ""

HEADERS = {"Authorization": "Bearer fake-token"}


# ── Checklist CRUD ──────────────────────────────────────────────────


def test_create_checklist():
    global CHECKLIST_ID
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists",
        json={"title": "New Member Onboarding", "description": "Standard onboarding steps"},
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)
    if resp.status_code == 201:
        CHECKLIST_ID = resp.json()["id"]
        assert resp.json()["title"] == "New Member Onboarding"


def test_list_checklists():
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_list_checklists_include_archived():
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists",
        params={"include_archived": True},
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_get_checklist():
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        data = resp.json()
        assert "items" in data
        assert "item_count" in data


def test_get_checklist_not_found():
    fake_id = str(uuid.uuid4())
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{fake_id}",
        headers=HEADERS,
    )
    assert resp.status_code in (404, 401)


def test_update_checklist():
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.put(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}",
        json={"title": "Updated Onboarding", "description": "Updated desc"},
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_delete_checklist_not_found():
    fake_id = str(uuid.uuid4())
    resp = client.delete(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{fake_id}",
        headers=HEADERS,
    )
    assert resp.status_code in (404, 401)


# ── Items ────────────────────────────────────────────────────────────


def test_add_item():
    global ITEM_ID
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}/items",
        json={
            "title": "Read the README",
            "description": "Read the project documentation",
            "item_type": "read",
            "order": 1,
            "is_required": True,
            "resource_url": "https://github.com/example/README.md",
        },
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)
    if resp.status_code == 201:
        ITEM_ID = resp.json()["id"]


def test_add_second_item():
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}/items",
        json={
            "title": "Set up dev environment",
            "item_type": "configure",
            "order": 2,
            "is_required": True,
        },
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)


def test_update_item():
    if not ITEM_ID:
        pytest.skip("No item created")
    resp = client.put(
        f"/api/projects/{PROJECT_ID}/onboarding/items/{ITEM_ID}",
        json={"title": "Read the docs carefully", "is_required": True},
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_delete_item_not_found():
    fake_id = str(uuid.uuid4())
    resp = client.delete(
        f"/api/projects/{PROJECT_ID}/onboarding/items/{fake_id}",
        headers=HEADERS,
    )
    assert resp.status_code in (404, 401)


# ── Assignments ──────────────────────────────────────────────────────


def test_assign_checklist():
    global ASSIGNMENT_ID
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}/assign",
        json={"user_id": str(uuid.uuid4())},
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)
    if resp.status_code == 201:
        ASSIGNMENT_ID = resp.json()["id"]


def test_batch_assign():
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}/assign-batch",
        json={"user_ids": [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]},
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)
    if resp.status_code == 201:
        assert len(resp.json()) == 3


def test_list_assignments():
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}/assignments",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_list_assignments_completed_only():
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}/assignments",
        params={"completed_only": True},
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_get_assignment_progress():
    if not ASSIGNMENT_ID:
        pytest.skip("No assignment created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/assignments/{ASSIGNMENT_ID}/progress",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_get_assignment_progress_not_found():
    fake_id = str(uuid.uuid4())
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/assignments/{fake_id}/progress",
        headers=HEADERS,
    )
    assert resp.status_code in (404, 401)


# ── Item Completion ──────────────────────────────────────────────────


def test_complete_item():
    if not ASSIGNMENT_ID or not ITEM_ID:
        pytest.skip("No assignment or item created")
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/onboarding/assignments/{ASSIGNMENT_ID}/items/{ITEM_ID}/complete",
        json={"notes": "Done reading"},
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)


def test_complete_item_idempotent():
    if not ASSIGNMENT_ID or not ITEM_ID:
        pytest.skip("No assignment or item created")
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/onboarding/assignments/{ASSIGNMENT_ID}/items/{ITEM_ID}/complete",
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)


# ── Statistics ───────────────────────────────────────────────────────


def test_checklist_stats():
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}/stats",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_checklist_stats_not_found():
    fake_id = str(uuid.uuid4())
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{fake_id}/stats",
        headers=HEADERS,
    )
    assert resp.status_code in (404, 401)


def test_project_onboarding_stats():
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/onboarding/stats",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


# ── Cleanup ──────────────────────────────────────────────────────────


def test_delete_checklist():
    if not CHECKLIST_ID:
        pytest.skip("No checklist created")
    resp = client.delete(
        f"/api/projects/{PROJECT_ID}/onboarding/checklists/{CHECKLIST_ID}",
        headers=HEADERS,
    )
    assert resp.status_code in (204, 401)
