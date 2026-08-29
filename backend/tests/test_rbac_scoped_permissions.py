"""
RBAC tests against a real database session.

Separate from ``tests/test_rbac.py``, which drives every check through a
``MagicMock`` session. That approach is part of why the escalation fixed here
survived: with a mocked ``db.get(User, ...)``, a check that returns ``True``
unconditionally looks exactly like a check that consulted a table. (Twenty-one
of those tests also fail on ``main`` today, for an unrelated SQLAlchemy/mock
interaction.)

Three things are pinned down here.

**The tables exist once and cover every role.** The project table used to be
written out twice, and the second binding silently discarded the first.

**Platform staff and org admins get what we decided to give them, not
everything.** Both ``has_org_permission`` and ``has_project_permission``
short-circuited on ``return True`` for a system MAINTAINER, so a content
moderator could delete any organization on the platform.

**A permission answer carries its scope.** ``get_user_permissions`` flattened
every membership into one ``set[str]``, so owning project A reported
``project:delete`` with nothing saying it did not apply to project B.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rbac import (
    ALL_ORG_PERMISSIONS,
    ALL_PROJECT_PERMISSIONS,
    ALL_SYSTEM_PERMISSIONS,
    ORG_DELETE,
    ORG_MANAGE_CONTENT,
    ORG_MANAGE_MEMBERS,
    ORG_ROLE_INHERITED_PROJECT_PERMISSIONS,
    ORG_ROLE_PERMISSIONS,
    ORG_UPDATE,
    ORG_VIEW_CONTENT,
    PROJECT_ARCHIVE,
    PROJECT_DELETE,
    PROJECT_EDIT_CONTENT,
    PROJECT_ROLE_PERMISSIONS,
    PROJECT_TRANSFER_OWNERSHIP,
    PROJECT_UPDATE,
    PROJECT_VIEW,
    SYSTEM_MANAGE_CONTENT,
    SYSTEM_ROLE_PERMISSIONS,
    SystemRole,
    get_scoped_permissions,
    get_user_permissions,
    get_user_system_role,
    has_org_permission,
    has_project_permission,
    has_system_permission,
    has_system_role,
)
from app.database.base import Base
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrgMemberRole
from app.models.project import Project
from app.models.project_member import MemberRole, ProjectMember
from app.models.user import User

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def make_user(
    db,
    username: str,
    *,
    system_role: str = SystemRole.USER.value,
    is_superuser: bool = False,
) -> User:
    user = User(
        email=f"{username}@example.com",
        username=username,
        first_name=username.capitalize(),
        last_name="Test",
        password_hash="hashed",
        is_active=True,
        is_superuser=is_superuser,
    )
    if hasattr(User, "system_role"):
        user.system_role = system_role

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_org(db, owner: User, name: str = "Acme") -> Organization:
    org = Organization(
        name=name,
        slug=name.lower().replace(" ", "-"),
        owner_id=owner.id,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


#: `Project` does not carry an `organization_id` column in every schema this
#: runs against, and `has_project_permission` reads it with `getattr` for that
#: reason. Where it is absent there is no org-to-project inheritance to test.
PROJECT_HAS_ORG = hasattr(Project, "organization_id")


def make_project(
    db, owner: User, title: str = "Thing", org: Organization | None = None
) -> Project:
    project = Project(
        title=title,
        slug=title.lower().replace(" ", "-"),
        description=f"{title} description",
        owner_id=owner.id,
    )
    if org is not None:
        project.organization_id = org.id

    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def add_org_member(db, org, user, role: OrgMemberRole) -> OrganizationMember:
    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=role,
        is_active=True,
    )
    db.add(member)
    db.commit()
    return member


def add_project_member(db, project, user, role: MemberRole) -> ProjectMember:
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=role,
        is_active=True,
    )
    db.add(member)
    db.commit()
    return member


# ---------------------------------------------------------------------------
# Table shape
# ---------------------------------------------------------------------------


def test_every_project_role_has_an_entry() -> None:
    """The dead copy of the table did not know about three of these."""
    assert set(PROJECT_ROLE_PERMISSIONS) == set(MemberRole)


def test_every_org_role_has_an_entry() -> None:
    assert set(ORG_ROLE_PERMISSIONS) == set(OrgMemberRole)


def test_every_system_role_has_an_entry() -> None:
    assert set(SYSTEM_ROLE_PERMISSIONS) == set(SystemRole)


def test_project_role_permissions_is_defined_once() -> None:
    """A second ``PROJECT_ROLE_PERMISSIONS = {...}`` silently replaced the
    first, leaving twenty-four lines of annotated table dead."""
    source = (Path(__file__).parent.parent / "app" / "core" / "rbac.py").read_text()

    bindings = re.findall(r"^PROJECT_ROLE_PERMISSIONS\b", source, re.MULTILINE)

    assert len(bindings) == 1, (
        f"PROJECT_ROLE_PERMISSIONS is bound {len(bindings)} times at module "
        "scope; the last one wins and the rest are dead."
    )


def test_the_derived_totals_cover_every_table() -> None:
    """A hardcoded 'all permissions' list is how the superuser branch drifted."""
    for perms in PROJECT_ROLE_PERMISSIONS.values():
        assert perms <= ALL_PROJECT_PERMISSIONS
    for perms in ORG_ROLE_PERMISSIONS.values():
        assert perms <= ALL_ORG_PERMISSIONS
    for perms in SYSTEM_ROLE_PERMISSIONS.values():
        assert perms <= ALL_SYSTEM_PERMISSIONS


def test_only_the_project_owner_can_delete_or_transfer() -> None:
    for role, perms in PROJECT_ROLE_PERMISSIONS.items():
        if role is MemberRole.OWNER:
            continue
        assert PROJECT_DELETE not in perms, role
        assert PROJECT_TRANSFER_OWNERSHIP not in perms, role


def test_only_the_org_owner_can_delete_the_org() -> None:
    for role, perms in ORG_ROLE_PERMISSIONS.items():
        if role is OrgMemberRole.OWNER:
            continue
        assert ORG_DELETE not in perms, role


def test_inherited_project_permissions_are_a_subset_of_the_real_ones() -> None:
    for role, perms in ORG_ROLE_INHERITED_PROJECT_PERMISSIONS.items():
        assert perms <= ALL_PROJECT_PERMISSIONS, role


# ---------------------------------------------------------------------------
# Platform staff
# ---------------------------------------------------------------------------


def test_a_maintainer_cannot_delete_an_organization(db) -> None:
    """The escalation. ``return True`` for any permission argument meant a
    content moderator could destroy any organization on the platform."""
    owner = make_user(db, "orgowner")
    maintainer = make_user(db, "mod", system_role=SystemRole.MAINTAINER.value)
    org = make_org(db, owner)

    assert has_org_permission(db, maintainer.id, org.id, ORG_DELETE) is False


def test_a_maintainer_cannot_update_or_manage_an_organization(db) -> None:
    owner = make_user(db, "orgowner")
    maintainer = make_user(db, "mod", system_role=SystemRole.MAINTAINER.value)
    org = make_org(db, owner)

    assert has_org_permission(db, maintainer.id, org.id, ORG_UPDATE) is False
    assert has_org_permission(db, maintainer.id, org.id, ORG_MANAGE_MEMBERS) is False


def test_a_maintainer_can_moderate_content_anywhere(db) -> None:
    """What the role is actually for."""
    owner = make_user(db, "orgowner")
    maintainer = make_user(db, "mod", system_role=SystemRole.MAINTAINER.value)
    org = make_org(db, owner)

    assert has_org_permission(db, maintainer.id, org.id, ORG_MANAGE_CONTENT) is True
    assert has_org_permission(db, maintainer.id, org.id, ORG_VIEW_CONTENT) is True


def test_a_maintainer_cannot_delete_archive_or_transfer_a_project(db) -> None:
    owner = make_user(db, "projowner")
    maintainer = make_user(db, "mod", system_role=SystemRole.MAINTAINER.value)
    project = make_project(db, owner)

    assert (
        has_project_permission(db, maintainer.id, project.id, PROJECT_DELETE) is False
    )
    assert (
        has_project_permission(db, maintainer.id, project.id, PROJECT_ARCHIVE) is False
    )
    assert (
        has_project_permission(
            db, maintainer.id, project.id, PROJECT_TRANSFER_OWNERSHIP
        )
        is False
    )


def test_a_maintainer_can_view_and_edit_project_content(db) -> None:
    owner = make_user(db, "projowner")
    maintainer = make_user(db, "mod", system_role=SystemRole.MAINTAINER.value)
    project = make_project(db, owner)

    assert has_project_permission(db, maintainer.id, project.id, PROJECT_VIEW) is True
    assert (
        has_project_permission(db, maintainer.id, project.id, PROJECT_EDIT_CONTENT)
        is True
    )


def test_a_system_admin_still_has_everything(db) -> None:
    owner = make_user(db, "orgowner")
    admin = make_user(db, "admin", system_role=SystemRole.ADMIN.value)
    org = make_org(db, owner)
    project = make_project(db, owner)

    for permission in ALL_ORG_PERMISSIONS:
        assert has_org_permission(db, admin.id, org.id, permission) is True, permission

    for permission in ALL_PROJECT_PERMISSIONS:
        assert (
            has_project_permission(db, admin.id, project.id, permission) is True
        ), permission


def test_a_superuser_still_has_everything(db) -> None:
    owner = make_user(db, "orgowner")
    root = make_user(db, "root", is_superuser=True)
    org = make_org(db, owner)
    project = make_project(db, owner)

    assert has_org_permission(db, root.id, org.id, ORG_DELETE) is True
    assert has_project_permission(db, root.id, project.id, PROJECT_DELETE) is True


def test_an_ordinary_user_gets_nothing_from_their_system_role(db) -> None:
    owner = make_user(db, "orgowner")
    stranger = make_user(db, "stranger")
    org = make_org(db, owner)
    project = make_project(db, owner)

    assert has_org_permission(db, stranger.id, org.id, ORG_VIEW_CONTENT) is False
    assert has_project_permission(db, stranger.id, project.id, PROJECT_VIEW) is False


# ---------------------------------------------------------------------------
# Ownership and membership
# ---------------------------------------------------------------------------


def test_an_org_owner_has_the_owner_role_permissions(db) -> None:
    owner = make_user(db, "orgowner")
    org = make_org(db, owner)

    assert has_org_permission(db, owner.id, org.id, ORG_DELETE) is True
    assert has_org_permission(db, owner.id, org.id, ORG_UPDATE) is True


def test_a_project_owner_has_the_owner_role_permissions(db) -> None:
    owner = make_user(db, "projowner")
    project = make_project(db, owner)

    assert has_project_permission(db, owner.id, project.id, PROJECT_DELETE) is True
    assert (
        has_project_permission(db, owner.id, project.id, PROJECT_TRANSFER_OWNERSHIP)
        is True
    )


@pytest.mark.parametrize("role", list(MemberRole))
def test_membership_grants_exactly_the_table(db, role: MemberRole) -> None:
    owner = make_user(db, "projowner")
    member = make_user(db, f"member_{role.value}")
    project = make_project(db, owner)
    add_project_member(db, project, member, role)

    expected = PROJECT_ROLE_PERMISSIONS[role]

    for permission in ALL_PROJECT_PERMISSIONS:
        assert has_project_permission(db, member.id, project.id, permission) is (
            permission in expected
        ), f"{role.value} / {permission}"


@pytest.mark.parametrize("role", list(OrgMemberRole))
def test_org_membership_grants_exactly_the_table(db, role: OrgMemberRole) -> None:
    owner = make_user(db, "orgowner")
    member = make_user(db, f"orgmember_{role.value}")
    org = make_org(db, owner)
    add_org_member(db, org, member, role)

    expected = ORG_ROLE_PERMISSIONS[role]

    for permission in ALL_ORG_PERMISSIONS:
        assert has_org_permission(db, member.id, org.id, permission) is (
            permission in expected
        ), f"{role.value} / {permission}"


def test_an_inactive_membership_grants_nothing(db) -> None:
    owner = make_user(db, "projowner")
    member = make_user(db, "former")
    project = make_project(db, owner)

    membership = add_project_member(db, project, member, MemberRole.ADMIN)
    membership.is_active = False
    db.commit()

    assert has_project_permission(db, member.id, project.id, PROJECT_UPDATE) is False


def test_an_unknown_user_gets_nothing(db) -> None:
    owner = make_user(db, "projowner")
    project = make_project(db, owner)

    assert has_project_permission(db, uuid.uuid4(), project.id, PROJECT_VIEW) is False


def test_a_missing_project_grants_nothing(db) -> None:
    user = make_user(db, "someone")

    assert has_project_permission(db, user.id, uuid.uuid4(), PROJECT_VIEW) is False


# ---------------------------------------------------------------------------
# Organization inheritance
# ---------------------------------------------------------------------------


def test_an_org_admin_cannot_transfer_ownership_of_an_org_project(db) -> None:
    """Org OWNER/ADMIN used to inherit *every* project permission."""
    founder = make_user(db, "founder")
    org_admin = make_user(db, "orgadmin")
    org = make_org(db, founder)
    add_org_member(db, org, org_admin, OrgMemberRole.ADMIN)
    project = make_project(db, founder, org=org)

    assert (
        has_project_permission(db, org_admin.id, project.id, PROJECT_TRANSFER_OWNERSHIP)
        is False
    )


def test_an_org_admin_cannot_delete_an_org_project(db) -> None:
    founder = make_user(db, "founder")
    org_admin = make_user(db, "orgadmin")
    org = make_org(db, founder)
    add_org_member(db, org, org_admin, OrgMemberRole.ADMIN)
    project = make_project(db, founder, org=org)

    assert has_project_permission(db, org_admin.id, project.id, PROJECT_DELETE) is False


def test_an_org_admin_can_manage_an_org_project(db) -> None:
    founder = make_user(db, "founder")
    org_admin = make_user(db, "orgadmin")
    org = make_org(db, founder)
    add_org_member(db, org, org_admin, OrgMemberRole.ADMIN)
    project = make_project(db, founder, org=org)

    assert has_project_permission(db, org_admin.id, project.id, PROJECT_UPDATE) is True
    assert has_project_permission(db, org_admin.id, project.id, PROJECT_VIEW) is True


def test_an_org_member_only_views_org_projects(db) -> None:
    founder = make_user(db, "founder")
    plain = make_user(db, "plainmember")
    org = make_org(db, founder)
    add_org_member(db, org, plain, OrgMemberRole.MEMBER)
    project = make_project(db, founder, org=org)

    assert has_project_permission(db, plain.id, project.id, PROJECT_VIEW) is True
    assert has_project_permission(db, plain.id, project.id, PROJECT_UPDATE) is False


def test_org_inheritance_does_not_reach_projects_outside_the_org(db) -> None:
    founder = make_user(db, "founder")
    org_admin = make_user(db, "orgadmin")
    outsider = make_user(db, "outsider")

    org = make_org(db, founder)
    add_org_member(db, org, org_admin, OrgMemberRole.ADMIN)

    unrelated = make_project(db, outsider, title="Unrelated")

    assert has_project_permission(db, org_admin.id, unrelated.id, PROJECT_VIEW) is False


# ---------------------------------------------------------------------------
# Scoped enumeration
# ---------------------------------------------------------------------------


def test_owning_one_project_does_not_grant_delete_on_another(db) -> None:
    """The flat-set bug, stated as directly as it can be.

    A user who owns project A and views project B got back a single set
    containing ``project:delete``, with nothing saying which project it
    applied to.
    """
    user = make_user(db, "mixed")
    other = make_user(db, "other")

    owned = make_project(db, user, title="Owned")
    viewed = make_project(db, other, title="Viewed")
    add_project_member(db, viewed, user, MemberRole.VIEWER)

    scoped = get_scoped_permissions(db, user.id)

    assert PROJECT_DELETE in scoped["projects"][str(owned.id)]
    assert PROJECT_DELETE not in scoped["projects"][str(viewed.id)]
    assert PROJECT_VIEW in scoped["projects"][str(viewed.id)]

    # And the enforcement path agrees with the report, which is the point.
    assert has_project_permission(db, user.id, owned.id, PROJECT_DELETE) is True
    assert has_project_permission(db, user.id, viewed.id, PROJECT_DELETE) is False


def test_scoped_permissions_reports_organizations_separately(db) -> None:
    user = make_user(db, "orgmixed")
    other = make_user(db, "otherowner")

    owned = make_org(db, user, name="Owned Org")
    joined = make_org(db, other, name="Joined Org")
    add_org_member(db, joined, user, OrgMemberRole.MEMBER)

    scoped = get_scoped_permissions(db, user.id)

    assert ORG_DELETE in scoped["organizations"][str(owned.id)]
    assert ORG_DELETE not in scoped["organizations"][str(joined.id)]


def test_scoped_permissions_for_an_unknown_user_is_empty(db) -> None:
    scoped = get_scoped_permissions(db, uuid.uuid4())

    assert scoped == {"system": [], "organizations": {}, "projects": {}}


def test_what_a_superuser_is_told_matches_what_is_enforced(db) -> None:
    """The superuser branch hardcoded six project permissions and omitted five
    that were actually allowed, so the UI hid actions that would have worked.
    """
    root = make_user(db, "root", is_superuser=True)
    owner = make_user(db, "owner")
    project = make_project(db, owner)

    # Give root a reason to have this project in its scope map at all.
    add_project_member(db, project, root, MemberRole.VIEWER)

    scoped = get_scoped_permissions(db, root.id)
    reported = set(scoped["projects"][str(project.id)])

    for permission in ALL_PROJECT_PERMISSIONS:
        enforced = has_project_permission(db, root.id, project.id, permission)
        assert (permission in reported) is enforced, permission


def test_scoped_permission_lists_are_sorted(db) -> None:
    """Stable output, so a client can diff two payloads."""
    user = make_user(db, "sorted")
    project = make_project(db, user)

    scoped = get_scoped_permissions(db, user.id)
    perms = scoped["projects"][str(project.id)]

    assert perms == sorted(perms)


def test_the_flat_helper_still_answers_its_narrow_question(db) -> None:
    user = make_user(db, "flat")
    make_project(db, user)

    flat = get_user_permissions(db, user.id)

    assert PROJECT_DELETE in flat
    assert isinstance(flat, set)


# ---------------------------------------------------------------------------
# System-level helpers
# ---------------------------------------------------------------------------


def test_has_system_permission_follows_the_table(db) -> None:
    maintainer = make_user(db, "mod", system_role=SystemRole.MAINTAINER.value)

    assert has_system_permission(db, maintainer.id, SYSTEM_MANAGE_CONTENT) is True
    assert has_system_permission(db, maintainer.id, "system:manage_system") is False


def test_has_system_role_treats_a_superuser_as_any_role(db) -> None:
    root = make_user(db, "root", is_superuser=True)

    assert has_system_role(db, root.id, SystemRole.MAINTAINER) is True


def test_an_unrecognised_system_role_falls_back_to_the_default(db) -> None:
    """Least privilege, not a 500."""
    if not hasattr(User, "system_role"):
        pytest.skip("User has no system_role column in this schema")

    user = make_user(db, "weird")
    user.system_role = "not-a-real-role"
    db.commit()

    assert get_user_system_role(db, user.id) is SystemRole.USER


def test_get_user_system_role_reports_admin_for_a_superuser(db) -> None:
    root = make_user(db, "root", is_superuser=True)

    assert get_user_system_role(db, root.id) is SystemRole.ADMIN


# ---------------------------------------------------------------------------
# Frontend / backend agreement
# ---------------------------------------------------------------------------


FRONTEND_HOOK = (
    Path(__file__).parent.parent.parent
    / "frontend"
    / "src"
    / "hooks"
    / "usePermissions.ts"
)


def _parse_frontend_table(source: str, name: str) -> dict[str, list[str]]:
    """Pull one ``Record<Role, readonly string[]>`` literal out of the hook.

    A regex over TypeScript is not something to be proud of. The alternative
    is a codegen step to make one authorization table readable from the other
    language, which is more machinery than this is worth; what matters is that
    a divergence fails *somewhere* instead of shipping.
    """
    match = re.search(
        rf"export const {name}: Record<[^=]+= \{{(.*?)\n\}};",
        source,
        re.DOTALL,
    )
    assert match, f"could not find {name} in {FRONTEND_HOOK}"

    body = match.group(1)
    table: dict[str, list[str]] = {}

    for role_match in re.finditer(r"(\w+):\s*\[(.*?)\]", body, re.DOTALL):
        role = role_match.group(1)
        perms = re.findall(r'"([^"]+)"', role_match.group(2))
        table[role] = sorted(perms)

    return table


@pytest.mark.skipif(
    not FRONTEND_HOOK.exists(), reason="frontend not present in this checkout"
)
def test_frontend_permission_tables_match_the_backend() -> None:
    """The frontend's copy of the tables must equal the backend's.

    They had drifted: the hook granted ``org:delete`` to org admins and
    ``project:delete`` to co-owners, so the UI rendered buttons the API
    answers 403 to. It also had no notion of the contributor, reviewer or
    viewer roles.

    If this fails, one side changed without the other. The backend is the
    source of truth for what is *allowed*.
    """
    source = FRONTEND_HOOK.read_text()

    frontend_org = _parse_frontend_table(source, "ORG_ROLE_PERMISSIONS")
    frontend_project = _parse_frontend_table(source, "PROJECT_ROLE_PERMISSIONS")

    backend_org = {
        role.value: sorted(perms) for role, perms in ORG_ROLE_PERMISSIONS.items()
    }
    backend_project = {
        role.value: sorted(perms) for role, perms in PROJECT_ROLE_PERMISSIONS.items()
    }

    assert (
        frontend_org == backend_org
    ), "frontend ORG_ROLE_PERMISSIONS disagrees with app/core/rbac.py:\n" + json.dumps(
        {"frontend": frontend_org, "backend": backend_org},
        indent=2,
        sort_keys=True,
    )

    assert frontend_project == backend_project, (
        "frontend PROJECT_ROLE_PERMISSIONS disagrees with app/core/rbac.py:\n"
        + json.dumps(
            {"frontend": frontend_project, "backend": backend_project},
            indent=2,
            sort_keys=True,
        )
    )


# ---------------------------------------------------------------------------
# The endpoint
# ---------------------------------------------------------------------------


def test_permissions_endpoint_requires_authentication(client) -> None:
    response = client.get("/api/v1/users/me/permissions")

    assert response.status_code in (401, 403)


def test_permissions_endpoint_returns_the_scoped_shape(
    client, register_and_login
) -> None:
    """The payload the UI consumes instead of hand-maintaining the rules."""
    _, token = register_and_login("perms@example.com", "permsuser")

    response = client.get(
        "/api/v1/users/me/permissions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    body = response.json()
    assert set(body) == {"system", "organizations", "projects"}
    assert isinstance(body["system"], list)
    assert isinstance(body["organizations"], dict)
    assert isinstance(body["projects"], dict)


def test_permissions_endpoint_scopes_a_created_project(
    client, register_and_login
) -> None:
    _, token = register_and_login("permsowner@example.com", "permsowner")
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/projects/",
        json={
            "title": "Perms Project",
            "slug": "perms-project",
            "description": "For checking the permissions payload.",
            "status": "active",
            "visibility": "public",
        },
        headers=headers,
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    body = client.get("/api/v1/users/me/permissions", headers=headers).json()

    assert project_id in body["projects"]
    assert PROJECT_DELETE in body["projects"][project_id]
