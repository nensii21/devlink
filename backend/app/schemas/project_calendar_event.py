import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CalendarEventBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    event_type: str = Field(..., description="e.g. sprint, meeting, hackathon, deadline, milestone")
    start_date: datetime
    end_date: Optional[datetime] = None

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class CalendarEventResponse(CalendarEventBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
