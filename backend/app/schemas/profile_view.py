import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProfileViewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    viewer_id: Optional[uuid.UUID] = None
    viewer_name: str
    viewer_username: str
    viewer_avatar: Optional[str] = None
    viewed_at: datetime
    visit_count: int = 1
    is_anonymous: bool


class ProfileViewPrivacySettings(BaseModel):
    hide_profile_views: bool = Field(
        default=False,
        description="If True, your visits to other profiles will be recorded anonymously and hidden.",
    )


class PaginatedProfileViewsResponse(BaseModel):
    items: List[ProfileViewResponse]
    total: int
    page: int
    size: int
    total_pages: int
