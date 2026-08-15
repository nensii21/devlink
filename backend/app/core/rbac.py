"""
RBAC (Role-Based Access Control) module for DevLink.

This module implements a comprehensive RBAC system with three layers:

1. **System-level roles** — assigned to every user via ``User.system_role``.
   Controls platform-wide actions like user management, content moderation,
   and system configuration.

2. **Organization-level roles** — assigned via ``OrganizationMember.role``.
   Controls actions within an organization (update settings, manage members,
   manage API tokens, delete org).

3. **Project-level roles** — assigned via ``ProjectMember.role``.
   Controls actions within a project (update, delete, invite, archive).

System Roles (issue #357):
    - ADMIN              — Full system access (also ``is_superuser=True``)
    - MAINTAINER         — System-wide read + content moderation
    - ORGANIZATION_OWNER — Can create/manage organizations
    - PROJECT_OWNER      — Can create/manage projects
    - CONTRIBUTOR        — Can contribute to projects (create issues, PRs)
    - USER               — Basic authenticated user (default)

Permission resolution order:
    1. If ``is_superuser`` → grant everything
    2. If system role has the permission → grant
    3. If org role has the permission (for org-scoped actions) → grant
    4. If project role has the permission (for project-scoped actions) → grant
    5. Deny
"""

from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrgMemberRole
from app.models.project import Project
from app.models.project_member import MemberRole, ProjectMember
from app.models.user import User

# ─── System-Level Roles ─────────────────────────────────────────────────────


class SystemRole(str, Enum):
    """Platform-wide roles assigned to every user.

    These control actions that are not scoped to a specific organization
    or project — e.g. user management, content moderation, system config.
    """

    ADMIN = "admin"
    MAINTAINER = "maintainer"
    ORGANIZATION_OWNER = "organization_owner"
    PROJECT_OWNER = "project_owner"
    CONTRIBUTOR = "contributor"
    USER = "user"


# Default role assigned to new users
DEFAULT_SYSTEM_ROLE = SystemRole.USER


# ─── System-Level Permissions ───────────────────────────────────────────────

SYSTEM_MANAGE_USERS = "system:manage_users"
SYSTEM_MANAGE_CONTENT = "system:manage_content"
SYSTEM_VIEW_ANALYTICS = "system:view_analytics"
SYSTEM_MANAGE_SYSTEM = "system:manage_system"
SYSTEM_CREATE_ORG = "system:create_org"
SYSTEM_CREATE_PROJECT = "system:create_project"
SYSTEM_CONTRIBUTE = "system:contribute"

SYSTEM_ROLE_PERMISSIONS: dict[SystemRole, frozenset[str]] = {
    SystemRole.ADMIN: frozenset(
        {
            SYSTEM_MANAGE_USERS,
            SYSTEM_MANAGE_CONTENT,
            SYSTEM_VIEW_ANALYTICS,
            SYSTEM_MANAGE_SYSTEM,
            SYSTEM_CREATE_ORG,
            SYSTEM_CREATE_PROJECT,
            SYSTEM_CONTRIBUTE,
        }
    ),
    SystemRole.MAINTAINER: frozenset(
        {
            SYSTEM_MANAGE_CONTENT,
            SYSTEM_VIEW_ANALYTICS,
            SYSTEM_CONTRIBUTE,
        }
    ),
    SystemRole.ORGANIZATION_OWNER: frozenset(
        {
            SYSTEM_CREATE_ORG,
            SYSTEM_VIEW_ANALYTICS,
            SYSTEM_CONTRIBUTE,
        }
    ),
    SystemRole.PROJECT_OWNER: frozenset(
        {
            SYSTEM_CREATE_PROJECT,
            SYSTEM_VIEW_ANALYTICS,
            SYSTEM_CONTRIBUTE,
        }
    ),
    SystemRole.CONTRIBUTOR: frozenset(
        {
            SYSTEM_CONTRIBUTE,
        }
    ),
    SystemRole.USER: frozenset(),
}

SYSTEM_ADMIN_ROLES = frozenset({SystemRole.ADMIN})
SYSTEM_STAFF_ROLES = frozenset({SystemRole.ADMIN, SystemRole.MAINTAINER})
SYSTEM_OWNER_ROLES = frozenset(
    {SystemRole.ADMIN, SystemRole.ORGANIZATION_OWNER, SystemRole.PROJECT_OWNER}
)


# ─── Org-Level Permissions ──────────────────────────────────────────────────

ORG_UPDATE = "org:update"
ORG_DELETE = "org:delete"
ORG_MANAGE_MEMBERS = "org:manage_members"
ORG_MANAGE_TOKENS = "org:manage_tokens"
ORG_MANAGE_ROLES = "org:manage_roles"
ORG_MANAGE_JOBS = "org:manage_jobs"
ORG_MANAGE_CANDIDATES = "org:manage_candidates"
ORG_MANAGE_CONTENT = "org:manage_content"
ORG_VIEW_CONTENT = "org:view_content"

ORG_ROLE_PERMISSIONS: dict[OrgMemberRole, frozenset[str]] = {
    OrgMemberRole.OWNER: frozenset(
        {
            ORG_UPDATE,
            ORG_DELETE,
            ORG_MANAGE_MEMBERS,
            ORG_MANAGE_TOKENS,
            ORG_MANAGE_ROLES,
            ORG_MANAGE_JOBS,
            ORG_MANAGE_CANDIDATES,
            ORG_MANAGE_CONTENT,
            ORG_VIEW_CONTENT,
        }
    ),
    OrgMemberRole.ADMIN: frozenset(
        {
            ORG_UPDATE,
            ORG_MANAGE_MEMBERS,
            ORG_MANAGE_TOKENS,
            ORG_MANAGE_ROLES,
            ORG_MANAGE_JOBS,
            ORG_MANAGE_CANDIDATES,
            ORG_MANAGE_CONTENT,
            ORG_VIEW_CONTENT,
        }
    ),
    OrgMemberRole.RECRUITER: frozenset(
        {ORG_MANAGE_JOBS, ORG_MANAGE_CANDIDATES, ORG_VIEW_CONTENT}
    ),
    OrgMemberRole.MAINTAINER: frozenset(
        {ORG_UPDATE, ORG_MANAGE_CONTENT, ORG_VIEW_CONTENT}
    ),
    OrgMemberRole.MEMBER: frozenset({ORG_VIEW_CONTENT}),
}


# ─── Project-Level Permissions ──────────────────────────────────────────────

PROJECT_UPDATE = "project:update"
PROJECT_DELETE = "project:delete"
PROJECT_INVITE = "project:invite"
PROJECT_ARCHIVE = "project:archive"
PROJECT_RESTORE = "project:restore"
PROJECT_VIEW = "project:view"
PROJECT_MANAGE_ROLES = "project:manage_roles"
PROJECT_TRANSFER_OWNERSHIP = "project:transfer_ownership"
PROJECT_REMOVE_MEMBERS = "project:remove_members"
PROJECT_EDIT_CONTENT = "project:edit_content"
PROJECT_REVIEW = "project:review"

PROJECT_ROLE_PERMISSIONS: dict[MemberRole, frozenset[str]] = {
    MemberRole.OWNER: frozenset(
        {
            PROJECT_UPDATE,
            PROJECT_DELETE,
            PROJECT_INVITE,
            PROJECT_ARCHIVE,
            PROJECT_RESTORE,
            PROJECT_VIEW,
        }
    ),
    MemberRole.CO_OWNER: frozenset(
        {
            PROJECT_UPDATE,
            PROJECT_INVITE,
            PROJECT_ARCHIVE,
            PROJECT_RESTORE,
            PROJECT_VIEW,
        }
    ),
    MemberRole.ADMIN: frozenset({PROJECT_UPDATE, PROJECT_INVITE, PROJECT_VIEW}),
    MemberRole.MAINTAINER: frozenset({PROJECT_UPDATE, PROJECT_INVITE, PROJECT_VIEW}),
    MemberRole.MEMBER: frozenset({PROJECT_VIEW}),
}

PROJECT_ROLE_PERMISSIONS = {
    MemberRole.OWNER: {
        PROJECT_UPDATE,
        PROJECT_DELETE,
        PROJECT_INVITE,
        PROJECT_ARCHIVE,
        PROJECT_RESTORE,
        PROJECT_VIEW,
        PROJECT_MANAGE_ROLES,
        PROJECT_TRANSFER_OWNERSHIP,
        PROJECT_REMOVE_MEMBERS,
        PROJECT_EDIT_CONTENT,
        PROJECT_REVIEW,
    },
    MemberRole.CO_OWNER: {
        PROJECT_UPDATE,
        PROJECT_INVITE,
        PROJECT_ARCHIVE,
        PROJECT_RESTORE,
        PROJECT_VIEW,
        PROJECT_MANAGE_ROLES,
        PROJECT_REMOVE_MEMBERS,
        PROJECT_EDIT_CONTENT,
        PROJECT_REVIEW,
    },
    MemberRole.ADMIN: {
        PROJECT_UPDATE,
        PROJECT_INVITE,
        PROJECT_VIEW,
        PROJECT_MANAGE_ROLES,
        PROJECT_REMOVE_MEMBERS,
        PROJECT_EDIT_CONTENT,
        PROJECT_REVIEW,
    },
    MemberRole.MAINTAINER: {
        PROJECT_UPDATE,
        PROJECT_INVITE,
        PROJECT_VIEW,
        PROJECT_MANAGE_ROLES,
        PROJECT_REMOVE_MEMBERS,
        PROJECT_EDIT_CONTENT,
        PROJECT_REVIEW,
    },
    MemberRole.CONTRIBUTOR: {
        PROJECT_VIEW,
        PROJECT_EDIT_CONTENT,
        PROJECT_REVIEW,
    },
    MemberRole.REVIEWER: {
        PROJECT_VIEW,
        PROJECT_REVIEW,
    },
    MemberRole.VIEWER: {
        PROJECT_VIEW,
    },
    MemberRole.MEMBER: {
        PROJECT_VIEW,
    },
}

# ─── Permission Check Functions ─────────────────────────────────────────────


def has_system_permission(db: Session, user_id: uuid.UUID, permission: str) -> bool:
    """Check if a user has a specific system-level permission.

    Superusers (``is_superuser=True``) automatically have all permissions.
    Otherwise, the user's ``system_role`` is checked against
    ``SYSTEM_ROLE_PERMISSIONS``.
    """
    user = db.get(User, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    role_str = getattr(user, "system_role", None) or DEFAULT_SYSTEM_ROLE.value
    try:
        role = SystemRole(role_str) if isinstance(role_str, str) else role_str
    except ValueError:
        role = DEFAULT_SYSTEM_ROLE

    allowed = SYSTEM_ROLE_PERMISSIONS.get(role, frozenset())
    return permission in allowed


def has_system_role(
    db: Session, user_id: uuid.UUID, *allowed_roles: SystemRole
) -> bool:
    """Check if a user has one of the specified system roles.

    Superusers are always considered to have every role.
    """
    user = db.get(User, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    role_str = getattr(user, "system_role", None) or DEFAULT_SYSTEM_ROLE.value
    try:
        role = SystemRole(role_str) if isinstance(role_str, str) else role_str
    except ValueError:
        role = DEFAULT_SYSTEM_ROLE

    return role in allowed_roles


def has_org_permission(
    db: Session,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    permission: str,
) -> bool:
    """Check if a user has a specific permission within an organization.

    Resolution order:
    1. Superuser → grant
    2. System ADMIN/MAINTAINER → grant (platform staff can manage any org)
    3. Direct org ownership → grant
    4. Org membership role has permission → grant
    5. Deny
    """
    user = db.get(User, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    if has_system_role(db, user_id, SystemRole.ADMIN, SystemRole.MAINTAINER):
        return True

    stmt = select(OrganizationMember).where(
        and_(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active == True,  # noqa: E712
        )
    )
    member = db.scalar(stmt)
    if not member:
        org = db.get(Organization, org_id)
        if org and org.owner_id == user_id:
            return True
        return False

    allowed_permissions = ORG_ROLE_PERMISSIONS.get(member.role, frozenset())
    return permission in allowed_permissions


def has_project_permission(
    db: Session,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    permission: str,
) -> bool:
    """Check if a user has a specific permission within a project.

    Resolution order:
    1. Superuser → grant
    2. System ADMIN/MAINTAINER → grant
    3. Direct project ownership → grant
    4. Project membership role has permission → grant
    5. If project belongs to an org, org owners/admins inherit → grant
    6. Deny
    """
    user = db.get(User, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    if has_system_role(db, user_id, SystemRole.ADMIN, SystemRole.MAINTAINER):
        return True

    project = db.get(Project, project_id)
    if not project:
        return False

    if project.owner_id == user_id:
        return True

    stmt = select(ProjectMember).where(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True,  # noqa: E712
        )
    )
    member = db.scalar(stmt)
    if member:
        allowed_permissions = PROJECT_ROLE_PERMISSIONS.get(member.role, frozenset())
        if permission in allowed_permissions:
            return True

    org_id = getattr(project, "organization_id", None)
    if org_id is not None:
        org_role_stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
                OrganizationMember.is_active == True,  # noqa: E712
            )
        )
        org_member = db.scalar(org_role_stmt)
        if org_member and org_member.role in (
            OrgMemberRole.OWNER,
            OrgMemberRole.ADMIN,
        ):
            return True

    return False


def get_user_system_role(db: Session, user_id: uuid.UUID) -> SystemRole:
    """Return the user's system role, defaulting to ``SystemRole.USER``."""
    user = db.get(User, user_id)
    if not user:
        return DEFAULT_SYSTEM_ROLE

    if user.is_superuser:
        return SystemRole.ADMIN

    role_str = getattr(user, "system_role", None) or DEFAULT_SYSTEM_ROLE.value
    try:
        return SystemRole(role_str) if isinstance(role_str, str) else role_str
    except ValueError:
        return DEFAULT_SYSTEM_ROLE


def get_user_permissions(db: Session, user_id: uuid.UUID) -> set[str]:
    """Return ALL permissions a user has across all three RBAC layers."""
    user = db.get(User, user_id)
    if not user:
        return set()

    permissions: set[str] = set()

    if user.is_superuser:
        for perms in SYSTEM_ROLE_PERMISSIONS.values():
            permissions.update(perms)
        permissions.update(
            {
                ORG_UPDATE,
                ORG_DELETE,
                ORG_MANAGE_MEMBERS,
                ORG_MANAGE_TOKENS,
                ORG_MANAGE_ROLES,
                ORG_MANAGE_JOBS,
                ORG_MANAGE_CANDIDATES,
                ORG_MANAGE_CONTENT,
                ORG_VIEW_CONTENT,
            }
        )
        permissions.update(
            {
                PROJECT_UPDATE,
                PROJECT_DELETE,
                PROJECT_INVITE,
                PROJECT_ARCHIVE,
                PROJECT_RESTORE,
                PROJECT_VIEW,
            }
        )
        return permissions

    system_role = get_user_system_role(db, user_id)
    permissions.update(SYSTEM_ROLE_PERMISSIONS.get(system_role, frozenset()))

    org_members = db.scalars(
        select(OrganizationMember).where(
            and_(
                OrganizationMember.user_id == user_id,
                OrganizationMember.is_active == True,  # noqa: E712
            )
        )
    ).all()
    for om in org_members:
        permissions.update(ORG_ROLE_PERMISSIONS.get(om.role, frozenset()))

    project_members = db.scalars(
        select(ProjectMember).where(
            and_(
                ProjectMember.user_id == user_id,
                ProjectMember.is_active == True,  # noqa: E712
            )
        )
    ).all()
    for pm in project_members:
        permissions.update(PROJECT_ROLE_PERMISSIONS.get(pm.role, frozenset()))

    return permissions
