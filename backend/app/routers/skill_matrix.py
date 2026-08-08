from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.schemas.skill_matrix import SkillMatrixResponse, SkillMatrixUpdateRequest
from app.services.skill_matrix_service import SkillMatrixService

router = APIRouter(
    prefix="/skills-matrix",
    tags=["Skill Matrix"],
)


@router.get(
    "/me",
    response_model=SkillMatrixResponse,
    summary="Get current user's skill matrix",
)
def get_my_skill_matrix(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    return SkillMatrixService.get_user_skill_matrix(db, current_user.id)


@router.get(
    "/user/{user_id}",
    response_model=SkillMatrixResponse,
    summary="Get specified user's skill matrix",
)
def get_user_skill_matrix(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    return SkillMatrixService.get_user_skill_matrix(db, user_id)


@router.put(
    "/me",
    response_model=SkillMatrixResponse,
    summary="Update current user's skill matrix",
)
def update_my_skill_matrix(
    body: SkillMatrixUpdateRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    skills_data = [s.model_dump() for s in body.skills]
    return SkillMatrixService.update_user_skill_matrix(db, current_user.id, skills_data)
