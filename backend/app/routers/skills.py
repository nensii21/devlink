from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_current_user
from app.middleware.rate_limit import limiter, SEARCH_LIMIT
from app.models.user import User
from app.schemas.skill import (
    SkillCreate,
    SkillResponse,
    SkillUpdate,
)
from app.services.skill_service import SkillService

router = APIRouter(
    prefix="/skills",
    tags=["Skills"],
)


@router.post(
    "/",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_skill(
    skill: SkillCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return SkillService.create_skill(db=db, skill=skill)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/{skill_id}",
    response_model=SkillResponse,
)
def get_skill(
    skill_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    skill = SkillService.get_skill(
        db,
        skill_id,
    )

    if skill is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    return skill


@router.get(
    "/slug/{slug}",
    response_model=SkillResponse,
)
def get_skill_by_slug(
    slug: str,
    db: Session = Depends(get_database),
):
    skill = SkillService.get_by_slug(
        db,
        slug,
    )

    if skill is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    return skill


@router.get(
    "/",
    response_model=list[SkillResponse],
)
@limiter.limit(SEARCH_LIMIT)
def list_skills(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_database),
):
    return SkillService.list_skills(
        db,
        skip,
        limit,
    )


@router.get(
    "/search/{keyword}",
    response_model=list[SkillResponse],
)
@limiter.limit(SEARCH_LIMIT)
def search_skills(
    request: Request,
    keyword: str,
    db: Session = Depends(get_database),
):
    return SkillService.search_skills(
        db,
        keyword,
    )


@router.put(
    "/{skill_id}",
    response_model=SkillResponse,
)
def update_skill(
    skill_id: uuid.UUID,
    skill: SkillUpdate,
    db: Session = Depends(get_database),
):
    db_skill = SkillService.get_skill(
        db,
        skill_id,
    )

    if db_skill is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    try:
        return SkillService.update_skill(db, db_skill, skill)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_skill(
    skill_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    db_skill = SkillService.get_skill(
        db,
        skill_id,
    )

    if db_skill is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    SkillService.delete_skill(
        db,
        db_skill,
    )
