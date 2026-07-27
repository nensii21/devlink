from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

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
