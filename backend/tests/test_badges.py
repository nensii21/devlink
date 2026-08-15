from app.models.badge import Badge
from app.services.badge_service import BadgeService


def test_seed_badges(db):
    BadgeService.seed_badges(db)
    badges = db.query(Badge).all()
    assert len(badges) >= 6
    slugs = {b.slug for b in badges}
    assert "first-project" in slugs
    assert "100-followers" in slugs


def test_get_all_badges_api(client, register_and_login):
    response = client.get("/api/badges/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 6


def test_evaluate_badges(db, client, register_and_login):
    _, token = register_and_login("badge_user1@example.com", "badge_user1")
    headers = {"Authorization": f"Bearer {token}"}

    # Evaluate badges for current user
    response = client.post("/api/badges/evaluate", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_badges" in data
    assert "total_points" in data


def test_get_my_badges(client, register_and_login):
    _, token = register_and_login("badge_user2@example.com", "badge_user2")
    headers = {"Authorization": f"Bearer {token}"}

    # Trigger evaluate first
    client.post("/api/badges/evaluate", headers=headers)

    response = client.get("/api/badges/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
