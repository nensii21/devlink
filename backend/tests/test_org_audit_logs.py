import pytest
from uuid import uuid4

from app.models.user import User
from app.models.organization import Organization
from app.models.audit_log import AuditAction
from app.services.audit_log_service import AuditLogService
from app.core.security import create_access_token


@pytest.fixture
def test_user(db):
    user = User(
        id=uuid4(),
        first_name="OrgAdmin",
        last_name="Tester",
        username=f"org_admin_{uuid4().hex[:6]}",
        email=f"org_admin_{uuid4().hex[:6]}@example.com",
        password_hash="secret",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def target_user(db):
    user = User(
        id=uuid4(),
        first_name="Target",
        last_name="Member",
        username=f"target_user_{uuid4().hex[:6]}",
        email=f"target_{uuid4().hex[:6]}@example.com",
        password_hash="secret",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_org(db, test_user):
    org = Organization(
        id=uuid4(),
        owner_id=test_user.id,
        name="DevLink Audit Tech",
        slug=f"devlink-audit-{uuid4().hex[:4]}",
        description="Testing organization audit logging",
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(user_id=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


def test_create_and_get_org_audit_logs(
    client, db, test_org, test_user, target_user, auth_headers
):
    # Create audit log record
    log = AuditLogService.create_log(
        db,
        actor_id=test_user.id,
        target_user_id=target_user.id,
        action=AuditAction.MEMBER_INVITED,
        entity_type="organization_member",
        entity_id=str(target_user.id),
        organization_id=test_org.id,
        description="Invited new team member",
    )
    db.commit()

    # Query endpoint
    res = client.get(
        f"/api/v1/organizations/{test_org.id}/audit-logs",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "member_invited"
    assert data["items"][0]["actor_id"] == str(test_user.id)


def test_filter_org_audit_logs_by_user(
    client, db, test_org, test_user, target_user, auth_headers
):
    AuditLogService.create_log(
        db,
        actor_id=test_user.id,
        target_user_id=target_user.id,
        action=AuditAction.ROLE_UPDATED,
        entity_type="organization_member",
        organization_id=test_org.id,
        description="Updated role to Lead Developer",
    )
    db.commit()

    # Filter by target_user.id
    res = client.get(
        f"/api/v1/organizations/{test_org.id}/audit-logs?user_id={target_user.id}",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any(item["target_user_id"] == str(target_user.id) for item in data["items"])


def test_filter_org_audit_logs_by_event_type(
    client, db, test_org, test_user, auth_headers
):
    AuditLogService.create_log(
        db,
        actor_id=test_user.id,
        action=AuditAction.API_KEY_CREATED,
        entity_type="api_key",
        organization_id=test_org.id,
        description="Generated new production API token",
    )
    db.commit()

    res = client.get(
        f"/api/v1/organizations/{test_org.id}/audit-logs?event_type=api_key_created",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "api_key_created"


def test_org_audit_logs_pagination(client, db, test_org, test_user, auth_headers):
    for i in range(5):
        AuditLogService.create_log(
            db,
            actor_id=test_user.id,
            action=AuditAction.PROJECT_CREATED,
            entity_type="project",
            entity_id=f"proj_{i}",
            organization_id=test_org.id,
            description=f"Created project {i}",
        )
    db.commit()

    res = client.get(
        f"/api/v1/organizations/{test_org.id}/audit-logs?page=1&limit=2",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5
    assert data["pages"] >= 3


def test_export_org_audit_logs_csv(client, db, test_org, test_user, auth_headers):
    AuditLogService.create_log(
        db,
        actor_id=test_user.id,
        action=AuditAction.SETTINGS_CHANGED,
        entity_type="organization",
        organization_id=test_org.id,
        description="Updated security preferences",
    )
    db.commit()

    res = client.get(
        f"/api/v1/organizations/{test_org.id}/audit-logs/export",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "ID,Timestamp,Action" in res.text
    assert "settings_changed" in res.text
