from __future__ import annotations

import uuid
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization_member import OrganizationMember, OrgMemberRole
from app.models.project_member import ProjectMember, MemberRole
from app.models.organization import Organization
from app.models.project import Project

# Define permission system actions
# Org permissions
ORG_UPDATE = "org:update"
ORG_DELETE = "org:delete"
ORG_MANAGE_MEMBERS = "org:manage_members"

# Project permissions
PROJECT_UPDATE = "project:update"
PROJECT_DELETE = "project:delete"
PROJECT_INVITE = "project:invite"
PROJECT_ARCHIVE = "project:archive"
PROJECT_RESTORE = "project:restore"
PROJECT_VIEW = "project:view"

# Mapping roles to exact permissions list
ORG_ROLE_PERMISSIONS = {
    OrgMemberRole.OWNER: {ORG_UPDATE, ORG_DELETE, ORG_MANAGE_MEMBERS},
    OrgMemberRole.ADMIN: {ORG_UPDATE, ORG_MANAGE_MEMBERS},
    OrgMemberRole.MEMBER: set(),
}

PROJECT_ROLE_PERMISSIONS = {
    MemberRole.OWNER: {
        PROJECT_UPDATE,
        PROJECT_DELETE,
        PROJECT_INVITE,
        PROJECT_ARCHIVE,
        PROJECT_RESTORE,
        PROJECT_VIEW,
    },
    MemberRole.CO_OWNER: {
        PROJECT_UPDATE,
        PROJECT_INVITE,
        PROJECT_ARCHIVE,
        PROJECT_RESTORE,
        PROJECT_VIEW,
    },
    MemberRole.ADMIN: {PROJECT_UPDATE, PROJECT_INVITE, PROJECT_VIEW},
    MemberRole.MAINTAINER: {PROJECT_UPDATE, PROJECT_INVITE, PROJECT_VIEW},
    MemberRole.MEMBER: {PROJECT_VIEW},
}


def has_org_permission(
    db: Session,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    permission: str,
) -> bool:
    """
    Checks if a user has a specific permission within an organization.
    Superusers automatically have all permissions.
    """
    user = db.get(User, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    # Get the organization member record
    stmt = select(OrganizationMember).where(
        and_(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active == True,
        )
    )
    member = db.scalar(stmt)
    if not member:
        # Fallback check: is user the owner direct?
        org = db.get(Organization, org_id)
        if org and org.owner_id == user_id:
            return True
        return False

    allowed_permissions = ORG_ROLE_PERMISSIONS.get(member.role, set())
    return permission in allowed_permissions


def has_project_permission(
    db: Session,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    permission: str,
) -> bool:
    """
    Checks if a user has a specific permission within a project.
    If the project belongs to an organization, the organization Owner/Admin permissions propagate.
    Superusers automatically have all permissions.
    """
    user = db.get(User, user_id)
    if not user:
        return False

    if user.is_superuser:
        return True

    # Get project
    project = db.get(Project, project_id)
    if not project:
        return False

    # Direct project ownership check
    if project.owner_id == user_id:
        return True

    # Check project membership
    stmt = select(ProjectMember).where(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True,
        )
    )
    member = db.scalar(stmt)
    if member:
        allowed_permissions = PROJECT_ROLE_PERMISSIONS.get(member.role, set())
        if permission in allowed_permissions:
            return True

    return False
