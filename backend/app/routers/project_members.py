import uuid
from typing import List
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.schemas.project_member import (
    ProjectMemberResponse,
    UpdateProjectMemberRoleRequest,
    TransferProjectOwnershipRequest,
)
from app.schemas.project import ProjectResponse
from app.services.project_member_service import ProjectMemberService

router = APIRouter(
    prefix="/projects/{project_id}",
    tags=["Project Team Roles"],
)


@router.get(
    "/members",
    response_model=List[ProjectMemberResponse],
    summary="List project team members with assigned roles",
)
def get_project_members(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Retrieve all team members and their project roles."""
    return ProjectMemberService.get_project_members(db=db, project_id=project_id)


@router.put(
    "/members/{user_id}/role",
    response_model=ProjectMemberResponse,
    summary="Assign or change a project member's role",
)
def update_project_member_role(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: UpdateProjectMemberRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Assign or update team member role (Owner, Maintainer, Contributor, Reviewer, Viewer)."""
    return ProjectMemberService.update_member_role(
        db=db,
        project_id=project_id,
        target_user_id=user_id,
        new_role=payload.role,
        actor_user=current_user,
    )


@router.post(
    "/transfer-ownership",
    response_model=ProjectResponse,
    summary="Transfer project ownership to another member",
)
def transfer_project_ownership(
    project_id: uuid.UUID,
    payload: TransferProjectOwnershipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Transfer project ownership to a new team member."""
    return ProjectMemberService.transfer_ownership(
        db=db,
        project_id=project_id,
        new_owner_id=payload.new_owner_id,
        current_owner=current_user,
    )


@router.delete(
    "/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from the project team",
)
def remove_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Remove a user from the project team."""
    ProjectMemberService.remove_member(
        db=db,
        project_id=project_id,
        target_user_id=user_id,
        actor_user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
