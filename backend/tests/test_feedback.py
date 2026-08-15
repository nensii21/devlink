def test_submit_feedback_success(db, client, register_and_login):
    auth = register_and_login("fb1@example.com", "fbuser1")
    headers = auth["headers"]
    payload = {
        "category": "Bug Report",
        "title": "Navigation menu glitch on mobile",
        "description": "When opening the navigation menu on mobile devices, it occasionally glitches.",
    }
    response = client.post("/api/feedback", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "Bug Report"
    assert data["title"] == "Navigation menu glitch on mobile"
    assert data["status"] == "open"


def test_submit_feedback_invalid_category(db, client, register_and_login):
    auth = register_and_login("fb2@example.com", "fbuser2")
    headers = auth["headers"]
    payload = {
        "category": "NonExistentCategory",
        "title": "Some title text",
        "description": "Some detailed feedback content.",
    }
    response = client.post("/api/feedback", json=payload, headers=headers)
    assert response.status_code == 400


def test_get_my_feedbacks(db, client, register_and_login):
    auth = register_and_login("fb3@example.com", "fbuser3")
    headers = auth["headers"]
    client.post(
        "/api/feedback",
        json={
            "category": "Feature Request",
            "title": "Dark mode support for IDE",
            "description": "Please add high-contrast dark mode for code views.",
        },
        headers=headers,
    )
    response = client.get("/api/feedback/me", headers=headers)
    assert response.status_code == 200
    feedbacks = response.json()
    assert len(feedbacks) >= 1
