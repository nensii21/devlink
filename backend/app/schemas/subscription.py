import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tier: str
    status: str
    current_period_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SubscriptionUpgradeRequest(BaseModel):
    tier: str
