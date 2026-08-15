from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog, AuditAction


def test_api_token_lifecycle_and_authentication(
    client: TestClient, register_and_login, db: Session
):
    owner_id, owner_token = register_and_login("owner@x.com", "owner")
    headers = {"Authorization": f"Bearer {owner_token}"}

    # 1. Create organization
    org_resp = client.post(
        "/organizations/",
        json={
            "name": "Acme Corp",
            "slug": "acme",
            "organization_type": "startup",
        },
        headers=headers,
    )
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    # 2. Create API token with org:read scope
    token_resp = client.post(
        f"/api/organizations/{org_id}/tokens/",
        json={
            "name": "Read Token",
            "scopes": ["org:read"],
        },
        headers=headers,
    )
    assert token_resp.status_code == 201
    token_data = token_resp.json()
    assert "token" in token_data
    assert token_data["name"] == "Read Token"
    assert token_data["scopes"] == ["org:read"]
    assert token_data["prefix"].startswith("dl_tok_")

    raw_token = token_data["token"]
    token_id = token_data["id"]

    # 3. List API tokens
    list_resp = client.get(
        f"/api/organizations/{org_id}/tokens/",
        headers=headers,
    )
    assert list_resp.status_code == 200
    tokens_list = list_resp.json()
    assert len(tokens_list) == 1
    assert tokens_list[0]["id"] == token_id
    assert "token" not in tokens_list[0]  # Secure! Raw token is not shown in list

    # 4. Authenticate a GET request via the API token
    token_headers = {"Authorization": f"Bearer {raw_token}"}
    get_org_resp = client.get(
        f"/organizations/{org_id}",
        headers=token_headers,
    )
    assert get_org_resp.status_code == 200
    assert get_org_resp.json()["name"] == "Acme Corp"

    # 5. Verify write action (PUT) is REJECTED with read-only token scope
    update_resp = client.put(
        f"/organizations/{org_id}",
        json={"description": "Nice description"},
        headers=token_headers,
    )
    assert update_resp.status_code == 403
    assert "Scope required" in update_resp.json()["error"]["message"]

    # 6. Generate a write-enabled token
    write_token_resp = client.post(
        f"/api/organizations/{org_id}/tokens/",
        json={
            "name": "Write Token",
            "scopes": ["org:read", "org:write"],
        },
        headers=headers,
    )
    assert write_token_resp.status_code == 201
    write_token = write_token_resp.json()["token"]

    # 7. Update org using write-enabled token
    write_headers = {"Authorization": f"Bearer {write_token}"}
    update_success_resp = client.put(
        f"/organizations/{org_id}",
        json={"description": "Nice description"},
        headers=write_headers,
    )
    assert update_success_resp.status_code == 200
    assert update_success_resp.json()["description"] == "Nice description"

    # 8. Revoke the read token
    revoke_resp = client.delete(
        f"/api/organizations/{org_id}/tokens/{token_id}",
        headers=headers,
    )
    assert revoke_resp.status_code == 204

    # 9. Verify revoked token is rejected
    get_org_after_revoke = client.put(
        f"/organizations/{org_id}",
        json={"description": "Nice description"},
        headers=token_headers,
    )
    assert get_org_after_revoke.status_code == 401

    # 10. Audit Logging check
    db.expire_all()
    audit_logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc())).all()
    actions = [a.action for a in audit_logs]
    assert AuditAction.API_TOKEN_CREATED in actions
    assert AuditAction.API_TOKEN_REVOKED in actions
    assert AuditAction.API_ACCESS in actions
