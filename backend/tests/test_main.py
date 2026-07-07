def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "DevLink API",
        "version": "1.0.0",
        "status": "running",
    }

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
