from app.models.centralized_analytics import (
    AnalyticsEventType,
)
from app.services.centralized_analytics_service import CentralizedAnalyticsService


def test_track_event_service(db):
    event = CentralizedAnalyticsService.track_event(
        db,
        event_type=AnalyticsEventType.PROJECT_CREATION.value,
        properties={"project_title": "Test Project"},
    )
    assert event.id is not None
    assert event.event_type == "project_creation"
    assert event.properties["project_title"] == "Test Project"


def test_centralized_analytics_api_track(client):
    payload = {
        "event_type": "user_registration",
        "properties": {"source": "github_oauth"},
        "session_id": "test_session_123",
    }
    response = client.post("/api/centralized-analytics/track", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "user_registration"
    assert data["session_id"] == "test_session_123"


def test_centralized_analytics_api_metrics(client, db):
    CentralizedAnalyticsService.track_event(
        db,
        event_type=AnalyticsEventType.SEARCH_PERFORMED.value,
        properties={"query": "react"},
    )

    response = client.get("/api/centralized-analytics/metrics?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "total_events" in data
    assert "event_counts" in data
    assert data["total_events"] >= 1


def test_centralized_analytics_api_list_events(client, db):
    CentralizedAnalyticsService.track_event(
        db,
        event_type=AnalyticsEventType.MESSAGE_SENT.value,
        properties={"chat": "dev_group"},
    )

    response = client.get(
        "/api/centralized-analytics/events?limit=10&event_type=message_sent"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["event_type"] == "message_sent"
