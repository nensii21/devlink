def test_notification_delivery_analytics(client, register_and_login):
    user_id, token = register_and_login(
        "notif_analytics@example.com", "notif_analytics"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Create notification
    create_payload = {
        "recipient_id": user_id,
        "type": "system",
        "title": "Analytics Test Notification",
        "message": "Testing notification delivery analytics",
    }
    res = client.post("/api/notifications/", json=create_payload, headers=headers)
    assert res.status_code == 201
    notif = res.json()
    notif_id = notif["id"]

    # Track delivered
    res = client.post(f"/api/notifications/{notif_id}/delivered", headers=headers)
    assert res.status_code == 200
    assert res.json()["delivered_at"] is not None

    # Track clicked
    res = client.post(f"/api/notifications/{notif_id}/click", headers=headers)
    assert res.status_code == 200
    assert res.json()["clicked_at"] is not None
    assert res.json()["is_read"] is True

    # Get Analytics Dashboard response
    res = client.get("/api/notifications/analytics/delivery", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "rates" in data
    assert data["metrics"]["clicked"] >= 1
    assert data["metrics"]["delivered"] >= 1
