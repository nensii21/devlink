from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.builder_flare import BuilderFlare
from app.schemas.builder_flare import (
    BuilderFlareCreate,
    BuilderFlareUpdate,
)


class BuilderFlareService:
    """
    Business logic for Builder Flares.
    """

    @staticmethod
    def create_flare(
        db: Session,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        flare: BuilderFlareCreate,
    ) -> BuilderFlare:

        db_flare = BuilderFlare(
            created_by=user_id,
            project_id=project_id,
            title=flare.title,
            description=flare.description,
            role=flare.role,
            location=flare.location,
            commitment=flare.commitment,
            experience_level=flare.experience_level,
            openings=flare.openings,
            remote=flare.remote,
        )

        db.add(db_flare)
        db.commit()
        db.refresh(db_flare)

        return db_flare

    @staticmethod
    def get_flare(
        db: Session,
        flare_id: uuid.UUID,
    ) -> BuilderFlare | None:

        return db.get(BuilderFlare, flare_id)

    @staticmethod
    def list_open_flares(
        db: Session,
    ) -> list[BuilderFlare]:

        stmt = (
            select(BuilderFlare)
            .where(BuilderFlare.status == "open")
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_project_flares(
        db: Session,
        project_id: uuid.UUID,
    ) -> list[BuilderFlare]:

        stmt = (
            select(BuilderFlare)
            .where(BuilderFlare.project_id == project_id)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_flare(
        db: Session,
        db_flare: BuilderFlare,
        flare: BuilderFlareUpdate,
    ) -> BuilderFlare:

        data = flare.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_flare, key, value)

        db.commit()
        db.refresh(db_flare)

        return db_flare

    @staticmethod
    def close_flare(
        db: Session,
        db_flare: BuilderFlare,
    ) -> BuilderFlare:

        db_flare.status = "closed"

        db.commit()
        db.refresh(db_flare)

        return db_flare

    @staticmethod
    def delete_flare(
        db: Session,
        db_flare: BuilderFlare,
    ) -> None:

        db.delete(db_flare)
        db.commit()