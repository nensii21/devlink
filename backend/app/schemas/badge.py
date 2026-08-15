import uuid
from datetime import datetime
from typing import List
from pydantic import BaseModel


class BadgeBase(BaseModel):
    slug: str
    name: str
    description: str
    icon: str
    category: str = "achievement"
    points: int = 10


class BadgeCreate(BadgeBase):
    pass


class BadgeResponse(BadgeBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserBadgeResponse(BaseModel):
    id: str
    user_id: uuid.UUID
    badge: BadgeResponse
    awarded_at: datetime

    class Config:
        from_attributes = True


class BadgeEvaluationResponse(BaseModel):
    user_id: uuid.UUID
    newly_awarded: List[BadgeResponse]
    total_badges: int
    total_points: int
