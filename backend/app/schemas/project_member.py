import uuid
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field, ConfigDict

from app.models.project_member import MemberRole


class UpdateProjectMemberRoleRequest(BaseModel):
    role: MemberRole = Field(
        ...,
        description="New project team role: owner, maintainer, contributor, reviewer, viewer",
    )


class TransferProjectOwnershipRequest(BaseModel):
    new_owner_id: uuid.UUID = Field(..., description="User ID of the new project owner")


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Union[uuid.UUID, str]
    project_id: Union[uuid.UUID, str]
    user_id: Union[uuid.UUID, str]
    role: MemberRole
    is_active: bool
    joined_at: datetime
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
