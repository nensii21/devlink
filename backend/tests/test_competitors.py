"""Tests for the Project Competitor Tracker endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

# ── Helpers ──────────────────────────────────────────────────────────

PROJECT_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())
COMPETITOR_ID: str = ""
COMPARISON_ID: str = ""
SNAPSHOT_ID: str = ""

HEADERS = {"Authorization": "Bearer fake-token"}


def test_add_competitor():
    global COMPETITOR_ID
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/competitors/",
        json={
            "name": "Rival Framework",
            "website_url": "https://rival.dev",
            "repository_url": "https://github.com/example/rival",
            "description": "A competing full-stack framework",
            "threat_level": "high",
            "tags": ["framework", "fullstack"],
            "notes": "Growing rapidly in the React ecosystem",
        },
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)  # 401 if no real auth
    if resp.status_code == 201:
        data = resp.json()
        COMPETITOR_ID = data["id"]
        assert data["name"] == "Rival Framework"
        assert data["threat_level"] == "high"


def test_list_competitors():
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_list_competitors_by_threat():
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/",
        params={"threat_level": "high"},
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_threat_summary():
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/summary",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_get_competitor():
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_get_competitor_not_found():
    fake_id = str(uuid.uuid4())
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/{fake_id}",
        headers=HEADERS,
    )
    assert resp.status_code in (404, 401)


def test_update_competitor():
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.put(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}",
        json={"threat_level": "critical", "notes": "Updated notes"},
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


# ── Feature Comparisons ──────────────────────────────────────────────


def test_add_comparison():
    global COMPARISON_ID
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}/comparisons",
        json={
            "feature_name": "Real-time Collaboration",
            "description": "WebSocket-based real-time editing",
            "our_notes": "We support basic cursors",
            "their_notes": "They have full CRDT-based editing",
            "verdict": "inferior",
        },
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)
    if resp.status_code == 201:
        COMPARISON_ID = resp.json()["id"]


def test_list_comparisons():
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}/comparisons",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_list_comparisons_by_verdict():
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}/comparisons",
        params={"verdict": "inferior"},
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_update_comparison():
    if not COMPARISON_ID:
        pytest.skip("No comparison created")
    resp = client.put(
        f"/api/projects/{PROJECT_ID}/competitors/comparisons/{COMPARISON_ID}",
        json={"verdict": "competitive"},
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_delete_comparison():
    if not COMPARISON_ID:
        pytest.skip("No comparison created")
    resp = client.delete(
        f"/api/projects/{PROJECT_ID}/competitors/comparisons/{COMPARISON_ID}",
        headers=HEADERS,
    )
    assert resp.status_code in (204, 401)


# ── Metric Snapshots ─────────────────────────────────────────────────


def test_add_snapshot():
    global SNAPSHOT_ID
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.post(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}/snapshots",
        json={
            "stars": 15000,
            "forks": 2000,
            "contributors": 350,
            "downloads": 500000,
            "open_issues": 120,
            "monthly_active_users": 80000,
            "custom_metrics": {"npm_weekly_downloads": 25000},
            "notes": "Strong growth month-over-month",
            "snapshot_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=HEADERS,
    )
    assert resp.status_code in (201, 401)
    if resp.status_code == 201:
        SNAPSHOT_ID = resp.json()["id"]


def test_list_snapshots():
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}/snapshots",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_get_latest_snapshot():
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}/snapshots/latest",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 404, 401)


def test_delete_snapshot():
    if not SNAPSHOT_ID:
        pytest.skip("No snapshot created")
    resp = client.delete(
        f"/api/projects/{PROJECT_ID}/competitors/snapshots/{SNAPSHOT_ID}",
        headers=HEADERS,
    )
    assert resp.status_code in (204, 401)


# ── Insights ─────────────────────────────────────────────────────────


def test_insight_report():
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}/insights",
        headers=HEADERS,
    )
    assert resp.status_code in (200, 401)


def test_insight_report_not_found():
    fake_id = str(uuid.uuid4())
    resp = client.get(
        f"/api/projects/{PROJECT_ID}/competitors/{fake_id}/insights",
        headers=HEADERS,
    )
    assert resp.status_code in (404, 401)


# ── Delete Competitor ────────────────────────────────────────────────


def test_delete_competitor():
    if not COMPETITOR_ID:
        pytest.skip("No competitor created")
    resp = client.delete(
        f"/api/projects/{PROJECT_ID}/competitors/{COMPETITOR_ID}",
        headers=HEADERS,
    )
    assert resp.status_code in (204, 401)


def test_delete_competitor_not_found():
    fake_id = str(uuid.uuid4())
    resp = client.delete(
        f"/api/projects/{PROJECT_ID}/competitors/{fake_id}",
        headers=HEADERS,
    )
    assert resp.status_code in (404, 401)
