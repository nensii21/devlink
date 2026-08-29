import pytest
from app.models.user import UserRole


def test_feature_announcements_crud_and_read(client, register_and_login, db):
    reg_user = register_and_login()
    token = reg_user["access_token"]
    user_id = reg_user["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Promote to admin
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    user.role = UserRole.ADMIN
    db.commit()

    # 1. Admin creates a feature announcement
    payload = {
        "title": "New Platform Feature Center",
        "summary": "Discover latest release notes, changelog and roadmap.",
        "content": "Full detailed markdown description of the announcement center.",
        "category": "feature",
        "version": "v1.2.0",
        "badge_label": "New Hub",
        "is_featured": True,
        "is_published": True,
    }
    create_res = client.post(
        "/api/feature-announcements/admin",
        json=payload,
        headers=headers,
    )
    assert create_res.status_code == 201, create_res.text
    ann_data = create_res.json()
    ann_id = ann_data["id"]
    assert ann_data["title"] == "New Platform Feature Center"
    assert ann_data["category"] == "feature"
    assert ann_data["is_featured"] is True

    # 2. Public / Authenticated list
    list_res = client.get("/api/feature-announcements", headers=headers)
    assert list_res.status_code == 200
    list_json = list_res.json()
    assert list_json["total"] >= 1
    assert list_json["unread_count"] >= 1
    assert any(item["id"] == ann_id for item in list_json["items"])

    # 3. Filter by category
    filter_res = client.get(
        "/api/feature-announcements?category=feature", headers=headers
    )
    assert filter_res.status_code == 200
    assert len(filter_res.json()["items"]) >= 1

    # 4. Search query
    search_res = client.get("/api/feature-announcements?q=roadmap", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()["items"]) >= 1

    # 5. Get detail & auto-read
    detail_res = client.get(f"/api/feature-announcements/{ann_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["is_read"] is True

    # 6. Mark read endpoint
    read_res = client.post(f"/api/feature-announcements/{ann_id}/read", headers=headers)
    assert read_res.status_code == 200

    # 7. Update announcement
    update_res = client.put(
        f"/api/feature-announcements/admin/{ann_id}",
        json={"title": "Updated Feature Center Title"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Feature Center Title"

    # 8. Delete announcement
    del_res = client.delete(
        f"/api/feature-announcements/admin/{ann_id}",
        headers=headers,
    )
    assert del_res.status_code == 204
