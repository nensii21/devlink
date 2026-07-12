from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.exc import IntegrityError
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    ApplicationStatus,
)
from app.models.notification import NotificationType
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
)
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService


class ApplicationService:
    """
    Business logic for project applications.
    """

    @staticmethod
    def create_application(
        db: Session,
        applicant_id: uuid.UUID,
        project_id: uuid.UUID,
        flare_id: uuid.UUID,
        application: ApplicationCreate,
    ) -> Application:
        existing_application = db.scalar(
            select(Application).where(
                Application.applicant_id == applicant_id,
                Application.project_id == project_id,
            )
        )

        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied to this project.",
            )
        db_application = Application(
            applicant_id=applicant_id,
            project_id=project_id,
            flare_id=flare_id,
            message=application.message,
            portfolio_url=application.portfolio_url,
            github_url=application.github_url,
            resume_url=application.resume_url,
        )

        db.add(db_application)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied to this project.",
       )
        db.refresh(db_application)
        return db_application    

    @staticmethod
    def get_application(
        db: Session,
        application_id: uuid.UUID,
    ) -> Application | None:

        return db.get(Application, application_id)

    @staticmethod
    def list_project_applications(
        db: Session,
        project_id: uuid.UUID,
    ) -> list[Application]:

        stmt = select(Application).where(Application.project_id == project_id)

        return list(db.scalars(stmt))

    @staticmethod
    def list_user_applications(
        db: Session,
        applicant_id: uuid.UUID,
    ) -> list[Application]:

        stmt = select(Application).where(Application.applicant_id == applicant_id)

        return list(db.scalars(stmt))

    @staticmethod
    def update_application(
        db: Session,
        db_application: Application,
        application: ApplicationUpdate,
    ) -> Application:

        data = application.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_application, key, value)

        db.commit()
        db.refresh(db_application)

        return db_application

    @staticmethod
    def accept_application(
        db: Session,
        db_application: Application,
    ) -> Application:

        db_application.status = ApplicationStatus.ACCEPTED

        db.commit()
        db.refresh(db_application)

        # Trigger notification
        project_title = db_application.project.title if db_application.project else "Project"
        owner_id = db_application.project.owner_id if db_application.project else None
        
        notification_data = NotificationCreate(
            recipient_id=db_application.applicant_id,
            type=NotificationType.APPLICATION_ACCEPTED,
            title="Application Accepted",
            message=f"Your application for project '{project_title}' has been accepted!",
            action_url=f"/projects/{db_application.project_id}",
            project_id=db_application.project_id,
            application_id=db_application.id
        )
        NotificationService.create_notification(
            db=db,
            recipient_id=db_application.applicant_id,
            sender_id=owner_id,
            notification=notification_data
        )

        return db_application

    @staticmethod
    def reject_application(
        db: Session,
        db_application: Application,
    ) -> Application:

        db_application.status = ApplicationStatus.REJECTED

        db.commit()
        db.refresh(db_application)

        # Trigger notification
        project_title = db_application.project.title if db_application.project else "Project"
        owner_id = db_application.project.owner_id if db_application.project else None
        
        notification_data = NotificationCreate(
            recipient_id=db_application.applicant_id,
            type=NotificationType.APPLICATION_REJECTED,
            title="Application Rejected",
            message=f"Your application for project '{project_title}' has been rejected.",
            action_url=f"/projects/{db_application.project_id}",
            project_id=db_application.project_id,
            application_id=db_application.id
        )
        NotificationService.create_notification(
            db=db,
            recipient_id=db_application.applicant_id,
            sender_id=owner_id,
            notification=notification_data
        )

        return db_application

    @staticmethod
    def withdraw_application(
        db: Session,
        db_application: Application,
    ) -> Application:

        db_application.status = ApplicationStatus.WITHDRAWN

        db.commit()
        db.refresh(db_application)

        return db_application

    @staticmethod
    def delete_application(
        db: Session,
        db_application: Application,
    ) -> None:

        db.delete(db_application)
        db.commit()
