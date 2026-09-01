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
from typing import Dict, List, Optional, TypedDict

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrgMemberRole
from app.models.project import Project
from app.models.project_member import MemberRole, ProjectMember
from app.models.user import User


class ScopedPermissions(TypedDict):
    """Permissions grouped by the scope they apply in.

    ``organizations`` and ``projects`` are keyed by stringified UUID. A
    permission listed under a given id applies to *that* organization or
    project and to nothing else -- which is the whole point, and the thing the
    previous flat ``set[str]`` could not express.
    """

    system: List[str]
    organizations: Dict[str, List[str]]
    projects: Dict[str, List[str]]


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

#: Install, configure and remove plugins on behalf of an organization.
#:
#: Its own permission rather than a reuse of :data:`ORG_MANAGE_TOKENS`: a
#: plugin installation attaches a third-party webhook destination to the
#: organization's event stream, which is a different question from "may this
#: person mint an API key", even though the two often land on the same people.
ORG_MANAGE_PLUGINS = "org:manage_plugins"

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
            ORG_MANAGE_PLUGINS,
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
            ORG_MANAGE_PLUGINS,
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

#: Project-level grants, defined **once**.
#:
#: This table was previously written out twice, back to back: an annotated
#: ``dict[MemberRole, frozenset[str]]`` immediately followed by a plain ``dict``
#: literal that rebound the same name. The second won, so the first twenty-four
#: lines were dead -- never read, never executed, and never able to disagree
#: loudly enough for anyone to notice. They had already drifted: the dead table
#: gave MAINTAINER three permissions, the live one gave it seven, and the live
#: one added CONTRIBUTOR, REVIEWER and VIEWER, which the dead one did not know
#: about.
#:
#: The wider (live) set is kept, since that is what has actually been enforced.
PROJECT_ROLE_PERMISSIONS: dict[MemberRole, frozenset[str]] = {
    MemberRole.OWNER: frozenset(
        {
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
        }
    ),
    MemberRole.CO_OWNER: frozenset(
        {
            PROJECT_UPDATE,
            PROJECT_INVITE,
            PROJECT_ARCHIVE,
            PROJECT_RESTORE,
            PROJECT_VIEW,
            PROJECT_MANAGE_ROLES,
            PROJECT_REMOVE_MEMBERS,
            PROJECT_EDIT_CONTENT,
            PROJECT_REVIEW,
        }
    ),
    MemberRole.ADMIN: frozenset(
        {
            PROJECT_UPDATE,
            PROJECT_INVITE,
            PROJECT_VIEW,
            PROJECT_MANAGE_ROLES,
            PROJECT_REMOVE_MEMBERS,
            PROJECT_EDIT_CONTENT,
            PROJECT_REVIEW,
        }
    ),
    MemberRole.MAINTAINER: frozenset(
        {
            PROJECT_UPDATE,
            PROJECT_INVITE,
            PROJECT_VIEW,
            PROJECT_MANAGE_ROLES,
            PROJECT_REMOVE_MEMBERS,
            PROJECT_EDIT_CONTENT,
            PROJECT_REVIEW,
        }
    ),
    MemberRole.CONTRIBUTOR: frozenset(
        {
            PROJECT_VIEW,
            PROJECT_EDIT_CONTENT,
            PROJECT_REVIEW,
        }
    ),
    MemberRole.REVIEWER: frozenset(
        {
            PROJECT_VIEW,
            PROJECT_REVIEW,
        }
    ),
    MemberRole.VIEWER: frozenset({PROJECT_VIEW}),
    MemberRole.MEMBER: frozenset({PROJECT_VIEW}),
}

#: Every project permission, derived rather than restated. A hand-maintained
#: "all permissions" list is how the superuser branch of
#: :func:`get_user_permissions` ended up narrower than what is enforced.
ALL_PROJECT_PERMISSIONS: frozenset[str] = frozenset(
    perm for perms in PROJECT_ROLE_PERMISSIONS.values() for perm in perms
)

ALL_ORG_PERMISSIONS: frozenset[str] = frozenset(
    perm for perms in ORG_ROLE_PERMISSIONS.values() for perm in perms
)

ALL_SYSTEM_PERMISSIONS: frozenset[str] = frozenset(
    perm for perms in SYSTEM_ROLE_PERMISSIONS.values() for perm in perms
)


# ─── Platform-Staff Grants ──────────────────────────────────────────────────
#
# `has_org_permission` and `has_project_permission` both used to short-circuit
# on:
#
#     if has_system_role(db, user_id, SystemRole.ADMIN, SystemRole.MAINTAINER):
#         return True
#
# `return True` -- for *any* permission argument. The system table says a
# MAINTAINER holds exactly {manage_content, view_analytics, contribute}, but
# because these functions never consulted it, a maintainer could pass
# ORG_DELETE or PROJECT_DELETE and be granted. The docstring described the
# intent as "platform staff can manage any org"; what was implemented was
# "platform staff can delete any org".
#
# Staff grants are now tables like every other grant, so what a maintainer can
# do is written down and testable.

#: Org permissions a system role carries into *every* organization.
SYSTEM_ROLE_ORG_PERMISSIONS: dict[SystemRole, frozenset[str]] = {
    SystemRole.ADMIN: ALL_ORG_PERMISSIONS,
    # Moderation and visibility, deliberately not ORG_DELETE, ORG_UPDATE,
    # ORG_MANAGE_MEMBERS, ORG_MANAGE_ROLES or ORG_MANAGE_TOKENS.
    SystemRole.MAINTAINER: frozenset({ORG_VIEW_CONTENT, ORG_MANAGE_CONTENT}),
}

#: Project permissions a system role carries into *every* project.
SYSTEM_ROLE_PROJECT_PERMISSIONS: dict[SystemRole, frozenset[str]] = {
    SystemRole.ADMIN: ALL_PROJECT_PERMISSIONS,
    # A content moderator can see a project and edit its content. It cannot
    # delete the project, archive it, or change who owns it.
    SystemRole.MAINTAINER: frozenset({PROJECT_VIEW, PROJECT_EDIT_CONTENT}),
}

#: Project permissions an organization role inherits on the org's projects.
#:
#: Previously org OWNER and ADMIN inherited *every* project permission,
#: including PROJECT_TRANSFER_OWNERSHIP on a project they do not own.
ORG_ROLE_INHERITED_PROJECT_PERMISSIONS: dict[OrgMemberRole, frozenset[str]] = {
    OrgMemberRole.OWNER: frozenset(
        {
            PROJECT_VIEW,
            PROJECT_UPDATE,
            PROJECT_INVITE,
            PROJECT_ARCHIVE,
            PROJECT_RESTORE,
            PROJECT_MANAGE_ROLES,
            PROJECT_REMOVE_MEMBERS,
            PROJECT_EDIT_CONTENT,
            PROJECT_REVIEW,
            PROJECT_DELETE,
        }
    ),
    OrgMemberRole.ADMIN: frozenset(
        {
            PROJECT_VIEW,
            PROJECT_UPDATE,
            PROJECT_INVITE,
            PROJECT_ARCHIVE,
            PROJECT_RESTORE,
            PROJECT_MANAGE_ROLES,
            PROJECT_REMOVE_MEMBERS,
            PROJECT_EDIT_CONTENT,
            PROJECT_REVIEW,
        }
    ),
    OrgMemberRole.MAINTAINER: frozenset(
        {PROJECT_VIEW, PROJECT_EDIT_CONTENT, PROJECT_REVIEW}
    ),
    OrgMemberRole.MEMBER: frozenset({PROJECT_VIEW}),
    OrgMemberRole.RECRUITER: frozenset({PROJECT_VIEW}),
}

# ─── Role Resolution ────────────────────────────────────────────────────────


def _coerce_system_role(raw: object) -> SystemRole:
    """A ``system_role`` column value as a :class:`SystemRole`.

    Tolerant of a plain string, an already-coerced enum, ``None``, and a value
    that is no longer a role we recognise -- the last of which falls back to
    the default rather than raising, because an unreadable role should mean
    "least privilege", not "500".
    """
    if isinstance(raw, SystemRole):
        return raw

    if not raw:
        return DEFAULT_SYSTEM_ROLE

    try:
        return SystemRole(raw)
    except ValueError:
        return DEFAULT_SYSTEM_ROLE


def _system_role_of(user: User) -> SystemRole:
    """The effective system role of an already-loaded user."""
    if user.is_superuser:
        return SystemRole.ADMIN

    return _coerce_system_role(getattr(user, "system_role", None))


def _load_user(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Load the user once.

    Each check used to call ``db.get(User, ...)`` and then call another
    function that called ``db.get(User, ...)`` again. The identity map made
    that cheap in practice, which is exactly why it went unnoticed -- the
    shape is still wrong, and it hid how many queries a permission check
    costs.
    """
    return db.get(User, user_id)


# ─── Permission Check Functions ─────────────────────────────────────────────


def has_system_permission(db: Session, user_id: uuid.UUID, permission: str) -> bool:
    """Whether a user holds a system-level permission.

    Superusers hold everything. Otherwise the user's ``system_role`` is looked
    up in :data:`SYSTEM_ROLE_PERMISSIONS`.
    """
    user = _load_user(db, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    role = _system_role_of(user)

    return permission in SYSTEM_ROLE_PERMISSIONS.get(role, frozenset())


def has_system_role(
    db: Session, user_id: uuid.UUID, *allowed_roles: SystemRole
) -> bool:
    """Whether a user has one of ``allowed_roles``.

    Superusers satisfy any role. This is a role *identity* check and is not
    used to answer permission questions any more -- see
    :func:`has_org_permission` and :func:`has_project_permission`.
    """
    user = _load_user(db, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    return _system_role_of(user) in allowed_roles


def has_org_permission(
    db: Session,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    permission: str,
) -> bool:
    """Whether a user holds ``permission`` within one organization.

    Resolution order, first grant wins:

    1. Superuser
    2. The user's system role, via :data:`SYSTEM_ROLE_ORG_PERMISSIONS`
    3. Direct ownership of the organization
    4. Their organization membership role

    Step 2 used to be an unconditional ``return True`` for platform staff,
    which let a MAINTAINER -- whose whole job is content moderation -- delete
    any organization on the platform.
    """
    user = _load_user(db, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    system_role = _system_role_of(user)
    if permission in SYSTEM_ROLE_ORG_PERMISSIONS.get(system_role, frozenset()):
        return True

    stmt = select(OrganizationMember).where(
        and_(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active.is_(True),
        )
    )
    member = db.scalar(stmt)

    if member is not None:
        if permission in ORG_ROLE_PERMISSIONS.get(member.role, frozenset()):
            return True

    # An owner who is not also carrying a membership row still owns the org.
    org = db.get(Organization, org_id)
    if org is not None and org.owner_id == user_id:
        return permission in ORG_ROLE_PERMISSIONS[OrgMemberRole.OWNER]

    return False


def has_project_permission(
    db: Session,
    user_id: uuid.UUID | str,
    project_id: uuid.UUID | str,
    permission: str,
) -> bool:
    """Whether a user holds ``permission`` within one project.

    Resolution order, first grant wins:

    1. Superuser
    2. The user's system role, via :data:`SYSTEM_ROLE_PROJECT_PERMISSIONS`
    3. Direct ownership of the project
    4. Their project membership role
    5. Their organization role on the project's organization, via
       :data:`ORG_ROLE_INHERITED_PROJECT_PERMISSIONS`

    Steps 2 and 5 were both unconditional ``return True``. Step 5 in
    particular meant an org admin could transfer ownership of a project they
    do not own.
    """
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            pass

    if isinstance(project_id, str):
        try:
            project_id = uuid.UUID(project_id)
        except ValueError:
            pass

    user = _load_user(db, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    system_role = _system_role_of(user)
    if permission in SYSTEM_ROLE_PROJECT_PERMISSIONS.get(system_role, frozenset()):
        return True

    project = db.get(Project, project_id)
    if not project:
        return False

    if str(project.owner_id) == str(user_id):
        return permission in PROJECT_ROLE_PERMISSIONS[MemberRole.OWNER]

    stmt = select(ProjectMember).where(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active.is_(True),
        )
    )
    member = db.scalar(stmt)
    if member is not None:
        role_enum = MemberRole(member.role) if isinstance(member.role, str) else member.role
        if permission in PROJECT_ROLE_PERMISSIONS.get(role_enum, frozenset()):
            return True

    org_id = getattr(project, "organization_id", None)
    if org_id is not None:
        org_member = db.scalar(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == user_id,
                    OrganizationMember.is_active.is_(True),
                )
            )
        )
        if org_member is not None:
            inherited = ORG_ROLE_INHERITED_PROJECT_PERMISSIONS.get(
                org_member.role, frozenset()
            )
            if permission in inherited:
                return True

    return False


def get_user_system_role(db: Session, user_id: uuid.UUID) -> SystemRole:
    """The user's system role, defaulting to :data:`DEFAULT_SYSTEM_ROLE`."""
    user = _load_user(db, user_id)
    if not user:
        return DEFAULT_SYSTEM_ROLE

    return _system_role_of(user)


# ─── Permission Enumeration ─────────────────────────────────────────────────


def get_scoped_permissions(db: Session, user_id: uuid.UUID) -> ScopedPermissions:
    """Every permission a user holds, grouped by the scope it applies in.

    A permission answer is meaningless without its scope, and the previous
    version returned one flat ``set[str]`` unioned across every membership. A
    user who owned project A and was a viewer on project B got back a set
    containing ``project:delete`` with nothing saying *which* project, so any
    consumer asking "can they delete this project?" by testing membership in
    that set got ``True`` for project B.

    The returned mapping is::

        {
            "system": [...],
            "organizations": {"<org uuid>": [...]},
            "projects": {"<project uuid>": [...]},
        }

    Every value is derived from the same tables the enforcement path uses, so
    what this reports cannot drift from what is allowed. The superuser branch
    in particular used to restate a hardcoded list of six project permissions
    and omitted five that were actually enforced.
    """
    empty: ScopedPermissions = {"system": [], "organizations": {}, "projects": {}}

    user = _load_user(db, user_id)
    if not user:
        return empty

    system_role = _system_role_of(user)
    is_admin = user.is_superuser or system_role is SystemRole.ADMIN

    system_permissions = (
        ALL_SYSTEM_PERMISSIONS
        if is_admin
        else SYSTEM_ROLE_PERMISSIONS.get(system_role, frozenset())
    )

    baseline_org = (
        ALL_ORG_PERMISSIONS
        if is_admin
        else SYSTEM_ROLE_ORG_PERMISSIONS.get(system_role, frozenset())
    )
    baseline_project = (
        ALL_PROJECT_PERMISSIONS
        if is_admin
        else SYSTEM_ROLE_PROJECT_PERMISSIONS.get(system_role, frozenset())
    )

    organizations: dict[str, set[str]] = {}
    projects: dict[str, set[str]] = {}

    # Organizations the user owns outright.
    for org in db.scalars(
        select(Organization).where(Organization.owner_id == user_id)
    ).all():
        organizations.setdefault(str(org.id), set()).update(
            ORG_ROLE_PERMISSIONS[OrgMemberRole.OWNER]
        )

    org_members = db.scalars(
        select(OrganizationMember).where(
            and_(
                OrganizationMember.user_id == user_id,
                OrganizationMember.is_active.is_(True),
            )
        )
    ).all()

    for om in org_members:
        organizations.setdefault(str(om.organization_id), set()).update(
            ORG_ROLE_PERMISSIONS.get(om.role, frozenset())
        )

    for project in db.scalars(select(Project).where(Project.owner_id == user_id)).all():
        projects.setdefault(str(project.id), set()).update(
            PROJECT_ROLE_PERMISSIONS[MemberRole.OWNER]
        )

    project_members = db.scalars(
        select(ProjectMember).where(
            and_(
                ProjectMember.user_id == user_id,
                ProjectMember.is_active.is_(True),
            )
        )
    ).all()

    for pm in project_members:
        projects.setdefault(str(pm.project_id), set()).update(
            PROJECT_ROLE_PERMISSIONS.get(pm.role, frozenset())
        )

    # Projects reached only through an organization membership.
    #
    # `Project.organization_id` is not present in every schema this runs
    # against -- `has_project_permission` reads it with `getattr(project, ...)`
    # for the same reason -- so the class-level query is guarded rather than
    # assumed. Where the column is absent there is simply no inheritance to
    # report, which matches what the enforcement path does.
    if org_members and hasattr(Project, "organization_id"):
        org_role_by_id = {str(om.organization_id): om.role for om in org_members}

        org_projects = db.scalars(
            select(Project).where(
                Project.organization_id.in_([om.organization_id for om in org_members])
            )
        ).all()

        for project in org_projects:
            inherited = ORG_ROLE_INHERITED_PROJECT_PERMISSIONS.get(
                org_role_by_id.get(str(project.organization_id)), frozenset()
            )
            if inherited:
                projects.setdefault(str(project.id), set()).update(inherited)

    # The platform-staff baseline applies everywhere the user can see.
    if baseline_org:
        for perms in organizations.values():
            perms.update(baseline_org)
    if baseline_project:
        for perms in projects.values():
            perms.update(baseline_project)

    return {
        "system": sorted(system_permissions),
        "organizations": {k: sorted(v) for k, v in organizations.items()},
        "projects": {k: sorted(v) for k, v in projects.items()},
    }


def get_user_permissions(db: Session, user_id: uuid.UUID) -> set[str]:
    """Every permission a user holds anywhere, flattened.

    .. deprecated::
        Kept for callers that only need "could this user ever do X". The
        result carries no scope, so it must not be used to answer a question
        about a *specific* organization or project -- use
        :func:`has_org_permission` / :func:`has_project_permission`, or
        :func:`get_scoped_permissions` if you need the whole picture.
    """
    scoped = get_scoped_permissions(db, user_id)

    flattened: set[str] = set(scoped["system"])
    for perms in scoped["organizations"].values():
        flattened.update(perms)
    for perms in scoped["projects"].values():
        flattened.update(perms)

    return flattened
