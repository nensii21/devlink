from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import date
import uuid

class TimeSlot(BaseModel):
    start: str
    end: str

class AvailabilityBase(BaseModel):
    timezone: str = "UTC"
    working_hours: Dict[str, List[TimeSlot]] = Field(default_factory=dict)
    meeting_duration: int = 30
    vacation_mode: bool = False
    vacation_start: Optional[date] = None
    vacation_end: Optional[date] = None

class AvailabilityUpdate(AvailabilityBase):
    pass

class AvailabilityResponse(AvailabilityBase):
    id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        from_attributes = True
