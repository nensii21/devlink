import pytest
from datetime import datetime, timedelta

def test_get_active_announcements(client, register_and_login):
    res = client.get("/api/announcements/active")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_admin_announcement_crud(client, register_and_login, db):
    from app.models.user import User, UserRole
    admin_id, token = register_and_login("admin_ann@example.com", "admin_ann")

    import uuid
    # Set user role to admin in db
    user = db.get(User, uuid.UUID(str(admin_id)))
    user.role = UserRole.ADMIN
    db.commit()

    headers = {"Authorization": f"Bearer {token}"}

    # Create announcement
    payload = {
        "title": "System Maintenance",
        "content": "Scheduled maintenance on Sunday at 2 AM UTC",
        "severity": "warning",
        "target_audience": "all",
        "is_active": True
    }
    res = client.post("/api/announcements/admin", json=payload, headers=headers)
    assert res.status_code == 201
    created = res.json()
    assert created["title"] == "System Maintenance"
    assert created["severity"] == "warning"
    ann_id = created["id"]

    # List admin announcements
    res = client.get("/api/announcements/admin/all", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Update announcement
    update_payload = {"title": "Updated System Maintenance", "severity": "critical"}
    res = client.put(f"/api/announcements/admin/{ann_id}", json=update_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Updated System Maintenance"
    assert res.json()["severity"] == "critical"

    # Verify active list includes it
    res = client.get("/api/announcements/active")
    assert res.status_code == 200
    titles = [a["title"] for a in res.json()]
    assert "Updated System Maintenance" in titles

    # Delete announcement
    res = client.delete(f"/api/announcements/admin/{ann_id}", headers=headers)
    assert res.status_code == 204
