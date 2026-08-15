def test_portfolio_export_markdown(db, client, register_and_login):
    headers = register_and_login("export_user@example.com", "exportuser")["headers"]
    response = client.get(
        "/api/users/me/portfolio/export?format=markdown", headers=headers
    )
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    assert response.text.startswith("# ")


def test_portfolio_export_pdf_html(db, client, register_and_login):
    headers = register_and_login("export_user@example.com", "exportuser")["headers"]
    response = client.get("/api/users/me/portfolio/export?format=pdf", headers=headers)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<!DOCTYPE html>" in response.text


def test_portfolio_export_json(db, client, register_and_login):
    headers = register_and_login("export_user@example.com", "exportuser")["headers"]
    response = client.get("/api/users/me/portfolio/export?format=json", headers=headers)
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert "profile" in data
    assert "skills" in data
    assert "projects" in data
