from fastapi import status

from app.models.user import User


def create_test_user(db, username):
    user = User(
        first_name="Test",
        last_name="User",
        username=username,
        email=f"{username}@example.com",
        password_hash="hashed_password",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_check_username_available(client):
    response = client.get(
        "/api/users/check-username", params={"username": "free_username"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["available"] is True
    assert response.json()["message"] == "Username is available."


def test_check_username_taken(client, db):
    create_test_user(db, "taken_username")

    response = client.get(
        "/api/users/check-username", params={"username": "taken_username"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["available"] is False
    assert response.json()["message"] == "Username is already taken."


def test_check_username_invalid_format(client):
    # Too short
    response = client.get("/api/users/check-username", params={"username": "ab"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username may contain only letters" in response.json()["detail"]

    # Invalid characters
    response = client.get("/api/users/check-username", params={"username": "user*name"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username may contain only letters" in response.json()["detail"]
