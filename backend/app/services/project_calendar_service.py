import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project_calendar_event import ProjectCalendarEvent
from app.models.milestone import Milestone
from app.models.project import Project
from app.models.user import User
from app.schemas.project_calendar_event import CalendarEventCreate, CalendarEventUpdate
from app.services.project_milestone_service import ProjectMilestoneService

class ProjectCalendarService:

    @staticmethod
    def get_events(db: Session, project_id: uuid.UUID) -> List[dict]:
        ProjectMilestoneService.get_project_or_404(db, project_id)
        
        # Get actual calendar events
        stmt = select(ProjectCalendarEvent).where(ProjectCalendarEvent.project_id == project_id)
        events = list(db.scalars(stmt).all())
        
        # Get milestones and treat them as calendar events
        milestone_stmt = select(Milestone).where(Milestone.project_id == project_id)
        milestones = list(db.scalars(milestone_stmt).all())
        
        unified_events = []
        for e in events:
            unified_events.append({
                "id": e.id,
                "project_id": e.project_id,
                "title": e.title,
                "description": e.description,
                "event_type": e.event_type,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "created_at": e.created_at,
                "updated_at": e.updated_at
            })
            
        for m in milestones:
            if m.due_date:
                unified_events.append({
                    "id": m.id,
                    "project_id": m.project_id,
                    "title": m.title,
                    "description": m.description,
                    "event_type": "milestone",
                    "start_date": m.due_date,
                    "end_date": m.due_date,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at
                })
                
        return unified_events

    @staticmethod
    def create_event(db: Session, project_id: uuid.UUID, event_in: CalendarEventCreate, actor: User) -> ProjectCalendarEvent:
        project = ProjectMilestoneService.get_project_or_404(db, project_id)
        ProjectMilestoneService.require_project_maintainer(db, project, actor)
        
        now = datetime.now(timezone.utc)
        event = ProjectCalendarEvent(
            id=uuid.uuid4(),
            project_id=project_id,
            title=event_in.title.strip(),
            description=event_in.description.strip() if event_in.description else None,
            event_type=event_in.event_type,
            start_date=event_in.start_date,
            end_date=event_in.end_date,
            created_at=now,
            updated_at=now
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def delete_event(db: Session, project_id: uuid.UUID, event_id: uuid.UUID, actor: User) -> None:
        project = ProjectMilestoneService.get_project_or_404(db, project_id)
        ProjectMilestoneService.require_project_maintainer(db, project, actor)
        
        event = db.get(ProjectCalendarEvent, event_id)
        if not event or event.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
            
        db.delete(event)
        db.commit()

