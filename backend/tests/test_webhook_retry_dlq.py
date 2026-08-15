import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models.user import User
from app.models.webhook import (
    WebhookDelivery,
    WebhookDeadLetterQueue,
    WebhookDeliveryStatus,
)
from app.services.webhook_service import WebhookService, calculate_backoff_delay
from app.core.security import create_access_token


@pytest.fixture
def webhook_user(db):
    user = User(
        id=uuid4(),
        first_name="Webhook",
        last_name="Tester",
        username=f"webhook_{uuid4().hex[:6]}",
        email=f"webhook_{uuid4().hex[:6]}@example.com",
        password_hash="secret",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(webhook_user):
    token = create_access_token(user_id=str(webhook_user.id))
    return {"Authorization": f"Bearer {token}"}


def test_calculate_backoff_delay():
    assert calculate_backoff_delay(1) == 2
    assert calculate_backoff_delay(2) == 4
    assert calculate_backoff_delay(3) == 8
    assert calculate_backoff_delay(4) == 16
    assert calculate_backoff_delay(5) == 32


@patch.object(WebhookService, "_send_http_request")
def test_successful_webhook_dispatch(mock_post, client, db, auth_headers):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"success": true}'
    mock_post.return_value = mock_resp

    res = client.post(
        "/api/v1/webhooks/dispatch",
        json={
            "event_type": "project.created",
            "target_url": "https://api.example.com/webhook",
            "payload": {"project_id": "123", "name": "DevLink"},
            "max_retries": 3,
        },
        headers=auth_headers,
    )

    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "delivered"
    assert data["attempts"] == 1
    assert data["event_type"] == "project.created"


@patch.object(WebhookService, "_send_http_request")
def test_webhook_retry_and_dlq_exhaustion(mock_post, client, db, auth_headers):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_post.return_value = mock_resp

    # Dispatch with max_retries = 2
    deliv = WebhookService.dispatch_webhook(
        db=db,
        event_type="issue.closed",
        target_url="https://api.example.com/fail",
        payload={"issue_id": "456"},
        max_retries=2,
    )

    assert deliv.status == WebhookDeliveryStatus.FAILED
    assert deliv.attempts == 1
    assert deliv.next_retry_at is not None

    # Simulate 2nd attempt (reaching max retries)
    deliv.next_retry_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    res_retry = WebhookService.process_pending_retries(db=db)
    assert res_retry["processed"] >= 1

    db.refresh(deliv)
    assert deliv.status == WebhookDeliveryStatus.EXHAUSTED

    # Verify moved to Dead Letter Queue (DLQ)
    dlq_items = WebhookService.get_dlq_entries(db=db)["items"]
    assert len(dlq_items) >= 1
    assert dlq_items[0].event_type == "issue.closed"
    assert dlq_items[0].is_replayed is False


@patch.object(WebhookService, "_send_http_request")
def test_replay_dlq_entry_api(mock_post, client, db, webhook_user, auth_headers):
    # Setup exhausted DLQ entry
    deliv = WebhookDelivery(
        id=uuid4(),
        event_type="user.created",
        target_url="https://api.example.com/webhook",
        payload={"user_id": str(webhook_user.id)},
        status=WebhookDeliveryStatus.EXHAUSTED,
        attempts=3,
        max_retries=3,
    )
    db.add(deliv)
    db.commit()

    dlq_item = WebhookDeadLetterQueue(
        id=uuid4(),
        delivery_id=deliv.id,
        event_type=deliv.event_type,
        target_url=deliv.target_url,
        payload=deliv.payload,
        total_attempts=3,
        failure_reason="HTTP 500",
        is_replayed=False,
    )
    db.add(dlq_item)
    db.commit()

    # Mock successful replay
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"replayed": true}'
    mock_post.return_value = mock_resp

    res = client.post(
        f"/api/v1/webhooks/dlq/{dlq_item.id}/replay",
        headers=auth_headers,
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["replayed", "delivered"]

    db.refresh(dlq_item)
    assert dlq_item.is_replayed is True


@patch.object(WebhookService, "_send_http_request")
def test_replay_all_dlq_entries_api(mock_post, client, db, auth_headers):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"status": "ok"}'
    mock_post.return_value = mock_resp

    res = client.post(
        "/api/v1/webhooks/dlq/replay-all",
        headers=auth_headers,
    )

    assert res.status_code == 200
    data = res.json()
    assert "total_replayed" in data
    assert "successful" in data


def test_webhook_metrics_api(client, db, auth_headers):
    res = client.get(
        "/api/v1/webhooks/metrics",
        headers=auth_headers,
    )

    assert res.status_code == 200
    data = res.json()
    assert "total_deliveries" in data
    assert "successful_deliveries" in data
    assert "failed_deliveries" in data
    assert "dlq_count" in data
    assert "delivery_success_rate" in data
