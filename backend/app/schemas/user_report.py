from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class UserReportBase(BaseModel):
    reason: str = Field(..., max_length=100)
    description: str | None = None
    post_id: UUID | None = None


class UserReportCreate(UserReportBase):
    pass


class UserReportResponse(UserReportBase):
    id: UUID
    reporter_id: UUID
    reported_id: UUID
    post_id: UUID | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
