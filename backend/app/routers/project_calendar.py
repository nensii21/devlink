import uuid
from typing import List

from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_database
from app.models.user import User
from app.schemas.project_calendar_event import CalendarEventCreate, CalendarEventResponse
from app.services.project_calendar_service import ProjectCalendarService

router = APIRouter(
    prefix="/projects/{project_id}/calendar-events",
    tags=["Project Calendar"],
)

@router.get(
    "",
    response_model=List[CalendarEventResponse],
    summary="List calendar events",
)
def list_events(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    events = ProjectCalendarService.get_events(db, project_id=project_id)
    return events

@router.post(
    "",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create calendar event",
)
def create_event(
    project_id: uuid.UUID,
    event_in: CalendarEventCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
):
    event = ProjectCalendarService.create_event(
        db, project_id=project_id, event_in=event_in, actor=current_user
    )
    return event

@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete calendar event",
)
def delete_event(
    project_id: uuid.UUID,
    event_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
):
    ProjectCalendarService.delete_event(
        db, project_id=project_id, event_id=event_id, actor=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
