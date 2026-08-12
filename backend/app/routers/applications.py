from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.middleware.idempotency import IdempotentRoute
from app.models.notification import NotificationType
from app.models.project import Project
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
)
from app.services.application_service import ApplicationService
from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
    route_class=IdempotentRoute,
)


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    from app.models.user_subscription import UserSubscription
    from sqlalchemy import select, func
    from app.models.application import Application

    stmt = select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    sub = db.scalar(stmt)
    is_pro = sub and sub.tier == "pro" and sub.status == "active"

    if not is_pro:
        # Check limit of 3
        count_stmt = select(func.count(Application.id)).where(Application.applicant_id == current_user.id)
        count = db.scalar(count_stmt) or 0
        if count >= 3:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free plan limit reached. Upgrade to Pro for unlimited project applications.",
            )

    created = ApplicationService.create_application(
        db=db,
        applicant_id=current_user.id,
        project_id=application.project_id,
        flare_id=application.flare_id,
        application=application,
    )

    try:
        project = db.get(Project, created.project_id)
        if project is not None:
            NotificationService.notify(
                db,
                recipient_id=project.owner_id,
                sender_id=current_user.id,
                type=NotificationType.APPLICATION,
                title="New application",
                message=f"{current_user.username} applied to your project.",
                project_id=created.project_id,
                application_id=created.id,
                action_url=f"/applications/{created.id}",
            )
    except Exception:
        db.rollback()

    return created


@router.get(
    "/me",
    response_model=list[ApplicationResponse],
)
def my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return ApplicationService.list_user_applications(
        db,
        current_user.id,
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    db_application = ApplicationService.get_application(
        db,
        application_id,
    )

    if db_application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return db_application


@router.get(
    "/project/{project_id}",
    response_model=list[ApplicationResponse],
)
def project_applications(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return ApplicationService.list_project_applications(
        db,
        project_id,
    )


@router.put(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def update_application(
    application_id: uuid.UUID,
    application: ApplicationUpdate,
    db: Session = Depends(get_database),
):

    db_application = ApplicationService.get_application(
        db,
        application_id,
    )

    if db_application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return ApplicationService.update_application(
        db,
        db_application,
        application,
    )


@router.patch(
    "/{application_id}/accept",
    response_model=ApplicationResponse,
)
def accept_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    db_application = ApplicationService.get_application(
        db,
        application_id,
    )

    if db_application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    accepted = ApplicationService.accept_application(
        db,
        db_application,
    )

    try:
        NotificationService.notify(
            db,
            recipient_id=db_application.applicant_id,
            sender_id=current_user.id,
            type=NotificationType.APPLICATION_ACCEPTED,
            title="Application accepted",
            message="Your application was accepted. 🎉",
            project_id=db_application.project_id,
            application_id=db_application.id,
            action_url=f"/applications/{db_application.id}",
        )
    except Exception:
        db.rollback()

    return accepted


@router.patch(
    "/{application_id}/reject",
    response_model=ApplicationResponse,
)
def reject_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    db_application = ApplicationService.get_application(
        db,
        application_id,
    )

    if db_application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    rejected = ApplicationService.reject_application(
        db,
        db_application,
    )

    try:
        NotificationService.notify(
            db,
            recipient_id=db_application.applicant_id,
            sender_id=current_user.id,
            type=NotificationType.APPLICATION_REJECTED,
            title="Application rejected",
            message="Your application was not accepted this time.",
            project_id=db_application.project_id,
            application_id=db_application.id,
            action_url=f"/applications/{db_application.id}",
        )
    except Exception:
        db.rollback()

    return rejected


@router.patch(
    "/{application_id}/withdraw",
    response_model=ApplicationResponse,
)
def withdraw_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    db_application = ApplicationService.get_application(
        db,
        application_id,
    )

    if db_application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return ApplicationService.withdraw_application(
        db,
        db_application,
    )


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    db_application = ApplicationService.get_application(
        db,
        application_id,
    )

    if db_application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    ApplicationService.delete_application(
        db,
        db_application,
    )
