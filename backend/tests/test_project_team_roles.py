import pytest
from uuid import uuid4

from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember, MemberRole
from app.services.project_member_service import ProjectMemberService
from app.core.rbac import (
    has_project_permission,
    PROJECT_MANAGE_ROLES,
    PROJECT_TRANSFER_OWNERSHIP,
    PROJECT_EDIT_CONTENT,
)
from app.core.security import create_access_token


@pytest.fixture
def owner_user(db):
    user = User(
        id=uuid4(),
        first_name="ProjOwner",
        last_name="Leader",
        username=f"owner_{uuid4().hex[:6]}",
        email=f"owner_{uuid4().hex[:6]}@example.com",
        password_hash="secret",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def member_user(db):
    user = User(
        id=uuid4(),
        first_name="Team",
        last_name="Member",
        username=f"member_{uuid4().hex[:6]}",
        email=f"member_{uuid4().hex[:6]}@example.com",
        password_hash="secret",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_project(db, owner_user):
    proj = Project(
        id=uuid4(),
        owner_id=owner_user.id,
        title="Role Managed Project",
        slug=f"role-proj-{uuid4().hex[:4]}",
        description="Testing Team Roles within Projects",
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


@pytest.fixture
def owner_auth_headers(owner_user):
    token = create_access_token(user_id=str(owner_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_auth_headers(member_user):
    token = create_access_token(user_id=str(member_user.id))
    return {"Authorization": f"Bearer {token}"}


def test_get_project_members(client, db, test_project, owner_user, member_user):
    # Add member_user as contributor
    pm = ProjectMember(
        id=uuid4(),
        project_id=test_project.id,
        user_id=member_user.id,
        role=MemberRole.CONTRIBUTOR,
        is_active=True,
    )
    db.add(pm)
    db.commit()

    members = ProjectMemberService.get_project_members(
        db=db, project_id=test_project.id
    )
    assert len(members) >= 2
    roles = {m["role"] for m in members}
    assert MemberRole.OWNER in roles
    assert MemberRole.CONTRIBUTOR in roles


def test_update_member_role_success(
    client, db, test_project, owner_user, member_user, owner_auth_headers
):
    # Update role to MAINTAINER
    res = client.put(
        f"/api/v1/projects/{test_project.id}/members/{member_user.id}/role",
        json={"role": "maintainer"},
        headers=owner_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "maintainer"


def test_update_member_role_unauthorized(
    client, db, test_project, owner_user, member_user, member_auth_headers
):
    # Viewer/member attempting to change roles should fail with 403
    res = client.put(
        f"/api/v1/projects/{test_project.id}/members/{owner_user.id}/role",
        json={"role": "viewer"},
        headers=member_auth_headers,
    )
    assert res.status_code == 403


def test_cannot_demote_project_owner(
    client, db, test_project, owner_user, owner_auth_headers
):
    res = client.put(
        f"/api/v1/projects/{test_project.id}/members/{owner_user.id}/role",
        json={"role": "viewer"},
        headers=owner_auth_headers,
    )
    assert res.status_code == 400
    assert "Cannot change project owner role" in res.json()["detail"]


def test_transfer_project_ownership(
    client, db, test_project, owner_user, member_user, owner_auth_headers
):
    res = client.post(
        f"/api/v1/projects/{test_project.id}/transfer-ownership",
        json={"new_owner_id": str(member_user.id)},
        headers=owner_auth_headers,
    )
    assert res.status_code == 200

    db.refresh(test_project)
    assert test_project.owner_id == member_user.id

    # Verify old owner is now MAINTAINER and new owner is OWNER
    members = ProjectMemberService.get_project_members(
        db=db, project_id=test_project.id
    )
    member_roles = {m["user_id"]: m["role"] for m in members}
    assert member_roles[str(member_user.id)] == MemberRole.OWNER
    assert member_roles[str(owner_user.id)] == MemberRole.MAINTAINER


def test_remove_project_member(
    client, db, test_project, owner_user, member_user, owner_auth_headers
):
    # Add member
    ProjectMemberService.update_member_role(
        db=db,
        project_id=test_project.id,
        target_user_id=member_user.id,
        new_role=MemberRole.REVIEWER,
        actor_user=owner_user,
    )

    res = client.delete(
        f"/api/v1/projects/{test_project.id}/members/{member_user.id}",
        headers=owner_auth_headers,
    )
    assert res.status_code in [200, 204]

    members = ProjectMemberService.get_project_members(
        db=db, project_id=test_project.id
    )
    assert not any(m["user_id"] == str(member_user.id) for m in members)


def test_cannot_remove_project_owner(
    client, db, test_project, owner_user, owner_auth_headers
):
    res = client.delete(
        f"/api/v1/projects/{test_project.id}/members/{owner_user.id}",
        headers=owner_auth_headers,
    )
    assert res.status_code == 400


def test_rbac_permission_checks(db, test_project, owner_user, member_user):
    # Owner has all permissions
    assert (
        has_project_permission(
            db, owner_user.id, test_project.id, PROJECT_TRANSFER_OWNERSHIP
        )
        is True
    )
    assert (
        has_project_permission(db, owner_user.id, test_project.id, PROJECT_MANAGE_ROLES)
        is True
    )

    # Set member_user as CONTRIBUTOR
    ProjectMemberService.update_member_role(
        db=db,
        project_id=test_project.id,
        target_user_id=member_user.id,
        new_role=MemberRole.CONTRIBUTOR,
        actor_user=owner_user,
    )

    assert (
        has_project_permission(
            db, member_user.id, test_project.id, PROJECT_EDIT_CONTENT
        )
        is True
    )
    assert (
        has_project_permission(
            db, member_user.id, test_project.id, PROJECT_TRANSFER_OWNERSHIP
        )
        is False
    )
