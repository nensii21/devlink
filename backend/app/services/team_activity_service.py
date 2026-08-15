from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.schemas.team_activity import (
    TeamActivityItem,
    TeamActivityType,
    TeamActivityCreate,
    TeamActivityTimelineResponse,
)


class TeamActivityService:
    @staticmethod
    def get_project_timeline(
        db: Session,
        project_id: int,
        page: int = 1,
        limit: int = 10,
        activity_type: Optional[TeamActivityType] = None,
    ) -> TeamActivityTimelineResponse:
        now = datetime.now(timezone.utc)

        raw_items = [
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "activity_type": TeamActivityType.MEMBER_JOINED,
                "title": "Sarah Connor joined the team",
                "description": "Sarah joined as Frontend Engineer",
                "actor_name": "Sarah Connor",
                "actor_avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
                "metadata_info": {"role": "Frontend Engineer"},
                "created_at": now - timedelta(hours=2),
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "activity_type": TeamActivityType.MILESTONE_COMPLETED,
                "title": "Completed Milestone: MVP Auth & Database Schema",
                "description": "All 12 sub-tasks for Sprint 1 have been marked completed.",
                "actor_name": "Alex Mercer",
                "actor_avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Alex",
                "metadata_info": {"milestone_id": 101, "progress": "100%"},
                "created_at": now - timedelta(hours=5),
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "activity_type": TeamActivityType.FILE_UPLOADED,
                "title": "Uploaded architecture_v2.pdf",
                "description": "System architecture diagram and cloud specs uploaded to team workspace.",
                "actor_name": "Elena Rostova",
                "actor_avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Elena",
                "metadata_info": {"file_name": "architecture_v2.pdf", "size_kb": 2048},
                "created_at": now - timedelta(days=1),
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "activity_type": TeamActivityType.NEW_DISCUSSION,
                "title": "Started discussion: Real-time WebSocket Protocol Design",
                "description": "Opened discussion thread regarding socket event schemas.",
                "actor_name": "Marcus Vance",
                "actor_avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Marcus",
                "metadata_info": {"comments_count": 8},
                "created_at": now - timedelta(days=2),
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "activity_type": TeamActivityType.ROLE_UPDATED,
                "title": "Updated Alex Mercer role to Project Lead",
                "description": "Permissions elevated to Project Admin",
                "actor_name": "Project Owner",
                "actor_avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Owner",
                "metadata_info": {"new_role": "Project Lead"},
                "created_at": now - timedelta(days=3),
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "activity_type": TeamActivityType.PROJECT_UPDATED,
                "title": "Updated Project Specs & Repository Link",
                "description": "Connected devlink-core repository and updated README.",
                "actor_name": "Alex Mercer",
                "actor_avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Alex",
                "metadata_info": {"field": "repository_url"},
                "created_at": now - timedelta(days=4),
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "activity_type": TeamActivityType.MEMBER_LEFT,
                "title": "David Miller left the team",
                "description": "David transferred project responsibilities",
                "actor_name": "David Miller",
                "actor_avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=David",
                "metadata_info": {"reason": "Project completed"},
                "created_at": now - timedelta(days=6),
            },
        ]

        if activity_type:
            filtered = [
                item for item in raw_items if item["activity_type"] == activity_type
            ]
        else:
            filtered = raw_items

        total = len(filtered)
        start = (page - 1) * limit
        end = start + limit
        paged_items = [TeamActivityItem(**item) for item in filtered[start:end]]
        has_more = end < total

        return TeamActivityTimelineResponse(
            project_id=project_id,
            items=paged_items,
            total=total,
            page=page,
            limit=limit,
            has_more=has_more,
        )

    @staticmethod
    def create_activity(
        db: Session, project_id: int, activity_in: TeamActivityCreate
    ) -> TeamActivityItem:
        return TeamActivityItem(
            id=str(uuid.uuid4()),
            project_id=project_id,
            activity_type=activity_in.activity_type,
            title=activity_in.title,
            description=activity_in.description,
            actor_name=activity_in.actor_name or "System User",
            actor_avatar=activity_in.actor_avatar
            or "https://api.dicebear.com/7.x/avataaars/svg?seed=DevLink",
            metadata_info=activity_in.metadata_info or {},
            created_at=datetime.now(timezone.utc),
        )
