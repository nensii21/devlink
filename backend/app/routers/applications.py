from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
)
from app.services.application_service import ApplicationService

router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ApplicationService.create_application(
        db=db,
        applicant_id=current_user.id,
        project_id=application.project_id,
        flare_id=application.flare_id,
        application=application,
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
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
    "/me",
    response_model=list[ApplicationResponse],
)
def my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return ApplicationService.list_user_applications(
        db,
        current_user.id,
    )


@router.get(
    "/project/{project_id}",
    response_model=list[ApplicationResponse],
)
def project_applications(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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

    return ApplicationService.accept_application(
        db,
        db_application,
    )


@router.patch(
    "/{application_id}/reject",
    response_model=ApplicationResponse,
)
def reject_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
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

    return ApplicationService.reject_application(
        db,
        db_application,
    )


@router.patch(
    "/{application_id}/withdraw",
    response_model=ApplicationResponse,
)
def withdraw_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
