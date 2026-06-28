from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import (
    Activity,
    ActivityType,
)
from app.schemas.activity import (
    ActivityCreate,
    ActivityUpdate,
)


class ActivityService:
    """
    Business logic for Activity operations.
    """

    @staticmethod
    def create_activity(
        db: Session,
        actor_id: uuid.UUID,
        activity: ActivityCreate,
    ) -> Activity:

        db_activity = Activity(
            actor_id=actor_id,
            activity_type=activity.activity_type,
            title=activity.title,
            description=activity.description,
            project_id=activity.project_id,
            organization_id=activity.organization_id,
            repository_id=activity.repository_id,
            application_id=activity.application_id,
            builder_flare_id=activity.builder_flare_id,
            icon=activity.icon,
            color=activity.color,
        )

        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)

        return db_activity

    @staticmethod
    def get_activity(
        db: Session,
        activity_id: uuid.UUID,
    ) -> Activity | None:

        return db.get(Activity, activity_id)

    @staticmethod
    def list_user_activities(
        db: Session,
        actor_id: uuid.UUID,
        limit: int = 50,
    ) -> list[Activity]:

        stmt = (
            select(Activity)
            .where(Activity.actor_id == actor_id)
            .order_by(Activity.created_at.desc())
            .limit(limit)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_project_activities(
        db: Session,
        project_id: uuid.UUID,
    ) -> list[Activity]:

        stmt = (
            select(Activity)
            .where(Activity.project_id == project_id)
            .order_by(Activity.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_organization_activities(
        db: Session,
        organization_id: uuid.UUID,
    ) -> list[Activity]:

        stmt = (
            select(Activity)
            .where(Activity.organization_id == organization_id)
            .order_by(Activity.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_repository_activities(
        db: Session,
        repository_id: uuid.UUID,
    ) -> list[Activity]:

        stmt = (
            select(Activity)
            .where(Activity.repository_id == repository_id)
            .order_by(Activity.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_recent_activities(
        db: Session,
        limit: int = 100,
    ) -> list[Activity]:

        stmt = (
            select(Activity)
            .order_by(Activity.created_at.desc())
            .limit(limit)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_by_type(
        db: Session,
        activity_type: ActivityType,
    ) -> list[Activity]:

        stmt = (
            select(Activity)
            .where(Activity.activity_type == activity_type)
            .order_by(Activity.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_activity(
        db: Session,
        db_activity: Activity,
        activity: ActivityUpdate,
    ) -> Activity:

        data = activity.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_activity, key, value)

        db.commit()
        db.refresh(db_activity)

        return db_activity

    @staticmethod
    def delete_activity(
        db: Session,
        db_activity: Activity,
    ) -> None:

        db.delete(db_activity)
        db.commit()