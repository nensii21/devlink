def test_search_empty_query(client):
    response = client.get("/search/?q=xyz")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "projects" in data
    assert type(data["users"]) is list
    assert type(data["projects"]) is list
