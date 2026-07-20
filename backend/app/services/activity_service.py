from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

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
            target_id=activity.target_id,
            target_type=activity.target_type,
            metadata_=activity.metadata_,
            icon=activity.icon,
            color=activity.color,
        )

        db.add(db_activity)
        db.flush()
        db.refresh(db_activity)

        return db_activity

    @staticmethod
    def log_activity(
        db: Session,
        actor_id: uuid.UUID,
        activity_type: ActivityType,
        title: str,
        description: str | None = None,
        target_id: uuid.UUID | None = None,
        target_type: str | None = None,
        metadata: dict[str, Any] | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> Activity:
        """
        Reusable helper to log an activity from other services.
        """
        db_activity = Activity(
            actor_id=actor_id,
            activity_type=activity_type,
            title=title,
            description=description,
            target_id=target_id,
            target_type=target_type,
            metadata_=metadata or {},
            icon=icon,
            color=color,
        )
        db.add(db_activity)
        db.flush()
        db.refresh(db_activity)
        return db_activity

    @staticmethod
    def get_activity(
        db: Session,
        activity_id: uuid.UUID,
    ) -> Activity | None:

        return db.get(Activity, activity_id)

    @staticmethod
    def list_activities(
        db: Session,
        limit: int = 50,
        cursor: datetime | None = None,
        actor_id: uuid.UUID | None = None,
        target_id: uuid.UUID | None = None,
        target_type: str | None = None,
        activity_types: list[ActivityType] | None = None,
    ) -> list[Activity]:
        """
        Unified method to list activities with cursor-based pagination and filtering.
        """
        stmt = select(Activity)

        if actor_id:
            stmt = stmt.where(Activity.actor_id == actor_id)
        if target_id:
            stmt = stmt.where(Activity.target_id == target_id)
        if target_type:
            stmt = stmt.where(Activity.target_type == target_type)
        if activity_types:
            stmt = stmt.where(Activity.activity_type.in_(activity_types))

        if cursor:
            # For cursor pagination, fetch items strictly older than the cursor
            stmt = stmt.where(Activity.created_at < cursor)

        stmt = stmt.order_by(Activity.created_at.desc()).limit(limit)

        return list(db.scalars(stmt))

    @staticmethod
    def list_user_activities(
        db: Session,
        actor_id: uuid.UUID,
        limit: int = 50,
    ) -> list[Activity]:
        return ActivityService.list_activities(db, limit=limit, actor_id=actor_id)

    @staticmethod
    def list_project_activities(
        db: Session,
        project_id: uuid.UUID,
    ) -> list[Activity]:
        return ActivityService.list_activities(db, target_id=project_id)

    @staticmethod
    def list_organization_activities(
        db: Session,
        organization_id: uuid.UUID,
    ) -> list[Activity]:
        return ActivityService.list_activities(db, target_id=organization_id)

    @staticmethod
    def list_repository_activities(
        db: Session,
        repository_id: uuid.UUID,
    ) -> list[Activity]:
        return ActivityService.list_activities(db, target_id=repository_id)

    @staticmethod
    def list_recent_activities(
        db: Session,
        limit: int = 100,
    ) -> list[Activity]:
        return ActivityService.list_activities(db, limit=limit)

    @staticmethod
    def list_by_type(
        db: Session,
        activity_type: ActivityType,
    ) -> list[Activity]:
        return ActivityService.list_activities(db, activity_types=[activity_type])

    @staticmethod
    def update_activity(
        db: Session,
        db_activity: Activity,
        activity: ActivityUpdate,
    ) -> Activity:

        data = activity.model_dump(exclude_unset=True)

        for key, value in data.items():
            if key == "metadata_":
                # Merge metadata if provided
                db_activity.metadata_ = {**db_activity.metadata_, **value}
            else:
                setattr(db_activity, key, value)

        db.flush()
        db.refresh(db_activity)

        return db_activity

    @staticmethod
    def delete_activity(
        db: Session,
        db_activity: Activity,
    ) -> None:

        db.delete(db_activity)
        db.flush()

