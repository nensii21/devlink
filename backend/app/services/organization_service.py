from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.core.cache import cached
from app.models.activity import ActivityType
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)
from app.services.activity_service import ActivityService
from app.utils.validators import slugify


class OrganizationService:
    """
    Business logic for Organization operations.
    """

    @staticmethod
    def generate_unique_slug(
        db: Session,
        name: str,
        exclude_org_id: uuid.UUID | None = None,
    ) -> str:
        """
        Generate a unique, human-readable slug from organization name or text.
        Handles collisions by appending numeric increments (-1, -2, etc.).
        """
        base_slug = slugify(name)
        if not base_slug:
            base_slug = "organization"

        slug = base_slug
        counter = 1

        while True:
            stmt = select(Organization).where(
                Organization.slug == slug,
                Organization.deleted_at.is_(None),
            )
            if exclude_org_id:
                stmt = stmt.where(Organization.id != exclude_org_id)

            existing = db.scalar(stmt)
            if not existing:
                return slug

            slug = f"{base_slug}-{counter}"
            counter += 1

    @staticmethod
    def create_organization(
        db: Session,
        owner_id: uuid.UUID,
        organization: OrganizationCreate,
    ) -> Organization:

        if organization.slug and organization.slug.strip():
            slug = OrganizationService.generate_unique_slug(db, organization.slug)
        else:
            slug = OrganizationService.generate_unique_slug(db, organization.name)

        db_organization = Organization(
            owner_id=owner_id,
            name=organization.name,
            slug=slug,
            description=organization.description,
            organization_type=organization.organization_type,
            website=organization.website,
            email=organization.email,
            phone=organization.phone,
            logo_url=organization.logo_url,
            banner_url=organization.banner_url,
            location=organization.location,
            github_url=organization.github_url,
            linkedin_url=organization.linkedin_url,
            twitter_url=organization.twitter_url,
            hiring=organization.hiring,
        )

        db.add(db_organization)
        db.flush()
        db.refresh(db_organization)

        # Create OrganizationMember record for owner
        from app.models.organization_member import OrganizationMember, OrgMemberRole

        member = OrganizationMember(
            organization_id=db_organization.id,
            user_id=owner_id,
            role=OrgMemberRole.OWNER,
            is_active=True,
        )
        db.add(member)
        db.commit()
        ActivityService.record_activity(
            db=db,
            actor_id=owner_id,
            activity_type=ActivityType.ORGANIZATION_CREATED,
            title="Created organization",
            description=db_organization.name,
            target_id=db_organization.id,
            target_type="organization",
            icon="building-2",
            color="primary",
        )

        return db_organization

    @staticmethod
    def get_organization(
        db: Session,
        organization_id: uuid.UUID,
    ) -> Organization | None:

        stmt = select(Organization).where(
            Organization.id == organization_id,
            Organization.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    @staticmethod
    def get_organization_including_deleted(
        db: Session,
        organization_id: uuid.UUID,
    ) -> Organization | None:
        """Retrieve an organization regardless of soft-delete status (admin use)."""
        return db.get(Organization, organization_id)

    @staticmethod
    @cached(ttl=300, key_prefix="org")
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Organization | None:

        stmt = (
            select(Organization)
            .options(selectinload(Organization.owner))
            .where(
                Organization.slug == slug,
                Organization.deleted_at.is_(None),
            )
        )

        return db.scalar(stmt)

    @staticmethod
    @cached(ttl=300, key_prefix="org")
    def list_organizations(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Organization]:

        stmt = (
            select(Organization)
            .where(Organization.deleted_at.is_(None))
            .options(selectinload(Organization.owner))
            .offset(skip)
            .limit(limit)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_owner_organizations(
        db: Session,
        owner_id: uuid.UUID,
    ) -> list[Organization]:

        stmt = (
            select(Organization)
            .options(selectinload(Organization.owner))
            .where(
                Organization.owner_id == owner_id,
                Organization.deleted_at.is_(None),
            )
        )

        return list(db.scalars(stmt))

    @staticmethod
    def search_organizations(
        db: Session,
        keyword: str,
    ) -> list[Organization]:

        stmt = (
            select(Organization)
            .options(selectinload(Organization.owner))
            .where(
                Organization.name.ilike(f"%{keyword}%"),
                Organization.deleted_at.is_(None),
            )
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_organization(
        db: Session,
        db_organization: Organization,
        organization: OrganizationUpdate,
    ) -> Organization:

        data = organization.model_dump(exclude_unset=True)

        if "slug" in data and data["slug"]:
            data["slug"] = OrganizationService.generate_unique_slug(
                db, data["slug"], exclude_org_id=db_organization.id
            )

        for key, value in data.items():
            setattr(db_organization, key, value)

        db.flush()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def verify_organization(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.verified = True

        db.flush()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def enable_hiring(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.hiring = True

        db.flush()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def disable_hiring(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.hiring = False

        db.flush()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def deactivate_organization(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.active = False

        db.flush()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def activate_organization(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.active = True

        db.flush()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def soft_delete_organization(
        db: Session,
        db_organization: Organization,
        deleted_by_id: uuid.UUID,
    ) -> None:
        """Mark an organization as deleted without removing the row."""
        db_organization.deleted_at = func.now()
        db_organization.deleted_by_id = deleted_by_id
        db.commit()

    @staticmethod
    def restore_soft_deleted_organization(
        db: Session,
        db_organization: Organization,
    ) -> Organization:
        """Restore a soft-deleted organization."""
        db_organization.deleted_at = None
        db_organization.deleted_by_id = None
        db.commit()
        db.refresh(db_organization)
        return db_organization

    @staticmethod
    def hard_delete_organization(
        db: Session,
        db_organization: Organization,
    ) -> None:
        """Permanently remove an organization from the database (admin only)."""
        from app.models.organization_member import OrganizationMember

        # Explicitly delete member rows first to avoid SQLAlchemy FK nullification
        db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == db_organization.id
        ).delete(synchronize_session=False)
        db.delete(db_organization)
        db.flush()

    @staticmethod
    def list_members(
        db: Session,
        organization_id: uuid.UUID,
    ):
        from app.models.organization_member import OrganizationMember

        stmt = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == organization_id)
        )
        return list(db.scalars(stmt))

    @staticmethod
    def can_manage_role(actor_role, target_current_role, target_new_role) -> bool:
        from app.models.organization_member import OrgMemberRole

        if actor_role == OrgMemberRole.OWNER:
            return True

        if actor_role == OrgMemberRole.ADMIN:
            if target_current_role == OrgMemberRole.OWNER:
                return False
            if target_new_role == OrgMemberRole.OWNER:
                return False
            return True

        return False

    @staticmethod
    def update_member_role(
        db: Session,
        organization_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role,
        actor_id: uuid.UUID,
    ):
        from app.models.organization_member import OrganizationMember, OrgMemberRole

        # Get actor
        actor = db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == actor_id,
            )
        )
        if not actor:
            raise ValueError("Actor is not a member of the organization")

        # Get target member
        target = db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == target_user_id,
            )
        )
        if not target:
            raise ValueError("Target user is not a member of the organization")

        if target.role == new_role:
            return target

        # Check permission
        if not OrganizationService.can_manage_role(actor.role, target.role, new_role):
            raise ValueError("You do not have permission to perform this role change")

        # Owner protection (last owner cannot be demoted)
        if target.role == OrgMemberRole.OWNER and new_role != OrgMemberRole.OWNER:
            owner_count = db.scalar(
                select(func.count())
                .select_from(OrganizationMember)
                .where(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.role == OrgMemberRole.OWNER,
                )
            )
            if owner_count <= 1:
                raise ValueError("Cannot demote the last owner of the organization")

        target.role = new_role
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def remove_member(
        db: Session,
        organization_id: uuid.UUID,
        target_user_id: uuid.UUID,
        actor_id: uuid.UUID,
    ):
        from app.models.organization_member import OrganizationMember, OrgMemberRole

        actor = db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == actor_id,
            )
        )
        if not actor:
            raise ValueError("Actor is not a member of the organization")

        target = db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == target_user_id,
            )
        )
        if not target:
            raise ValueError("Target user is not a member of the organization")

        # Self-leave is allowed for non-owners (or owners if not the last one)
        if actor_id != target_user_id:
            if not OrganizationService.can_manage_role(actor.role, target.role, None):
                raise ValueError("You do not have permission to remove this member")

        # Owner protection
        if target.role == OrgMemberRole.OWNER:
            owner_count = db.scalar(
                select(func.count())
                .select_from(OrganizationMember)
                .where(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.role == OrgMemberRole.OWNER,
                )
            )
            if owner_count <= 1:
                raise ValueError("Cannot remove the last owner of the organization")

        db.delete(target)
        db.commit()
