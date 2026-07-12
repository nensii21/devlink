from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.builder_flare import (
    BuilderFlareCreate,
    BuilderFlareResponse,
    BuilderFlareUpdate,
)
from app.services.builder_flare_service import BuilderFlareService

router = APIRouter(
    tags=["Builder Flares"],
)


@router.post(
    "/",
    response_model=BuilderFlareResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_builder_flare(
    flare: BuilderFlareCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    return BuilderFlareService.create_flare(
        db=db,
        user_id=current_user.id,
        project_id=flare.project_id,
        flare=flare,
    )


@router.get(
    "/{flare_id}",
    response_model=BuilderFlareResponse,
)
def get_builder_flare(
    flare_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    flare = BuilderFlareService.get_flare(
        db,
        flare_id,
    )

    if flare is None:
        raise HTTPException(
            status_code=404,
            detail="Builder Flare not found",
        )

    return flare


@router.get(
    "/open",
    response_model=list[BuilderFlareResponse],
)
def list_open_builder_flares(
    db: Session = Depends(get_database),
):

    return BuilderFlareService.list_open_flares(db)


@router.get(
    "/project/{project_id}",
    response_model=list[BuilderFlareResponse],
)
def list_project_builder_flares(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return BuilderFlareService.list_project_flares(
        db,
        project_id,
    )


@router.put(
    "/{flare_id}",
    response_model=BuilderFlareResponse,
)
def update_builder_flare(
    flare_id: uuid.UUID,
    flare: BuilderFlareUpdate,
    db: Session = Depends(get_database),
):

    db_flare = BuilderFlareService.get_flare(
        db,
        flare_id,
    )

    if db_flare is None:
        raise HTTPException(
            status_code=404,
            detail="Builder Flare not found",
        )

    return BuilderFlareService.update_flare(
        db,
        db_flare,
        flare,
    )


@router.patch(
    "/{flare_id}/close",
    response_model=BuilderFlareResponse,
)
def close_builder_flare(
    flare_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    db_flare = BuilderFlareService.get_flare(
        db,
        flare_id,
    )

    if db_flare is None:
        raise HTTPException(
            status_code=404,
            detail="Builder Flare not found",
        )

    return BuilderFlareService.close_flare(
        db,
        db_flare,
    )


@router.delete(
    "/{flare_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_builder_flare(
    flare_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    db_flare = BuilderFlareService.get_flare(
        db,
        flare_id,
    )

    if db_flare is None:
        raise HTTPException(
            status_code=404,
            detail="Builder Flare not found",
        )

    BuilderFlareService.delete_flare(
        db,
        db_flare,
    )
