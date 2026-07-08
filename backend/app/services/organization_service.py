from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)


class OrganizationService:
    """
    Business logic for Organization operations.
    """

    @staticmethod
    def create_organization(
        db: Session,
        owner_id: uuid.UUID,
        organization: OrganizationCreate,
    ) -> Organization:

        db_organization = Organization(
            owner_id=owner_id,
            name=organization.name,
            slug=organization.slug,
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
        db.commit()
        db.refresh(db_organization)

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
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Organization | None:

        stmt = select(Organization).where(
            Organization.slug == slug,
            Organization.deleted_at.is_(None),
        )

        return db.scalar(stmt)

    @staticmethod
    def list_organizations(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Organization]:

        stmt = (
            select(Organization)
            .where(Organization.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_owner_organizations(
        db: Session,
        owner_id: uuid.UUID,
    ) -> list[Organization]:

        stmt = select(Organization).where(
            Organization.owner_id == owner_id,
            Organization.deleted_at.is_(None),
        )

        return list(db.scalars(stmt))

    @staticmethod
    def search_organizations(
        db: Session,
        keyword: str,
    ) -> list[Organization]:

        stmt = select(Organization).where(
            Organization.name.ilike(f"%{keyword}%"),
            Organization.deleted_at.is_(None),
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_organization(
        db: Session,
        db_organization: Organization,
        organization: OrganizationUpdate,
    ) -> Organization:

        data = organization.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_organization, key, value)

        db.commit()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def verify_organization(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.verified = True

        db.commit()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def enable_hiring(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.hiring = True

        db.commit()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def disable_hiring(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.hiring = False

        db.commit()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def deactivate_organization(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.active = False

        db.commit()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def activate_organization(
        db: Session,
        db_organization: Organization,
    ) -> Organization:

        db_organization.active = True

        db.commit()
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
        db.delete(db_organization)
        db.commit()
