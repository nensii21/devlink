from fastapi.testclient import TestClient

def test_register_success(client: TestClient):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "StrongPassword1!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert "id" in data
    assert data["is_active"] is True
    assert data["is_verified"] is False

def test_register_duplicate_email(client: TestClient):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser2",
        "email": "testuser@example.com",
        "password": "StrongPassword1!"
    }
    # Register first
    client.post("/api/auth/register", json={**payload, "username": "firstuser"})
    
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists."

def test_register_duplicate_username(client: TestClient):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "email": "testuser2@example.com",
        "password": "StrongPassword1!"
    }
    # Register first
    client.post("/api/auth/register", json={**payload, "email": "firstuser@example.com"})
    
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already exists."

def test_login_success(client: TestClient):
    payload = {
        "email": "testuser@example.com",
        "password": "StrongPassword1!"
    }
    # Register first
    client.post("/api/auth/register", json={
        "first_name": "Test", "last_name": "User", 
        "username": "testuser", **payload
    })
    
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "testuser@example.com"

def test_login_invalid_password(client: TestClient):
    payload = {
        "email": "testuser@example.com",
        "password": "WrongPassword1!"
    }
    # Register first
    client.post("/api/auth/register", json={
        "first_name": "Test", "last_name": "User", 
        "username": "testuser", "email": "testuser@example.com", "password": "StrongPassword1!"
    })
    
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."

def test_login_invalid_email(client: TestClient):
    payload = {
        "email": "notfound@example.com",
        "password": "StrongPassword1!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."

def test_protected_route_me(client: TestClient):
    # Get token first
    login_payload = {
        "email": "testuser@example.com",
        "password": "StrongPassword1!"
    }
    # Register first
    client.post("/api/auth/register", json={
        "first_name": "Test", "last_name": "User", 
        "username": "testuser", **login_payload
    })
    
    login_response = client.post("/api/auth/login", json=login_payload)
    token = login_response.json()["access_token"]
    
    # Access protected route
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["username"] == "testuser"

def test_protected_route_invalid_token(client: TestClient):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials."

def test_protected_route_no_token(client: TestClient):
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_refresh_token(client: TestClient):
    login_payload = {
        "email": "testuser@example.com",
        "password": "StrongPassword1!"
    }
    client.post("/api/auth/register", json={
        "first_name": "Test", "last_name": "User", 
        "username": "testuser", **login_payload
    })
    login_response = client.post("/api/auth/login", json=login_payload)
    refresh_token = login_response.json()["refresh_token"]
    
    refresh_payload = {
        "refresh_token": refresh_token
    }
    response = client.post("/api/auth/refresh", json=refresh_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"]

def test_refresh_invalid_token(client: TestClient):
    refresh_payload = {
        "refresh_token": "invalid.refresh.token"
    }
    response = client.post("/api/auth/refresh", json=refresh_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token."

def test_change_password(client: TestClient):
    # Login to get token
    login_payload = {
        "email": "testuser@example.com",
        "password": "StrongPassword1!"
    }
    client.post("/api/auth/register", json={
        "first_name": "Test", "last_name": "User", 
        "username": "testuser", **login_payload
    })
    login_response = client.post("/api/auth/login", json=login_payload)
    token = login_response.json()["access_token"]
    
    # Change password
    change_payload = {
        "current_password": "StrongPassword1!",
        "new_password": "NewStrongPassword2@"
    }
    response = client.patch(
        "/api/auth/change-password",
        json=change_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Login with new password
    login_payload["password"] = "NewStrongPassword2@"
    login_response = client.post("/api/auth/login", json=login_payload)
    assert login_response.status_code == 200
    
def test_logout(client: TestClient):
    login_payload = {
        "email": "testuser@example.com",
        "password": "NewStrongPassword2@"
    }
    client.post("/api/auth/register", json={
        "first_name": "Test", "last_name": "User", 
        "username": "testuser", **login_payload
    })
    login_response = client.post("/api/auth/login", json=login_payload)
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_verify_email(client: TestClient):
    from app.core.security import _create_token
    from datetime import timedelta
    # Create a verification token manually for testing since SMTP isn't implemented
    # We need the user ID
    login_payload = {
        "email": "testuser@example.com",
        "password": "NewStrongPassword2@"
    }
    client.post("/api/auth/register", json={
        "first_name": "Test", "last_name": "User", 
        "username": "testuser", **login_payload
    })
    login_response = client.post("/api/auth/login", json=login_payload)
    user_id = login_response.json()["user"]["id"]
    
    token = _create_token(
        subject=user_id,
        expires_delta=timedelta(hours=24),
        token_type="verification"
    )
    
    response = client.post("/api/auth/verify-email", json={"token": token})
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Check that user is verified
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"}
    )
    assert me_response.json()["is_verified"] is True
