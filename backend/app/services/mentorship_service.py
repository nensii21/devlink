"""
Mentorship and interactive learning platform service module.
Manages session scheduling, mentee progression, curriculum milestones, and status transitions.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time


class SessionStatus(str, Enum):
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class CurriculumMilestone:
    milestone_id: str
    title: str
    description: str
    is_completed: bool = False
    completed_at: Optional[float] = None


@dataclass
class MentorshipSession:
    session_id: str
    mentor_id: str
    mentee_id: str
    topic: str
    scheduled_timestamp: float
    duration_minutes: int = 45
    status: SessionStatus = SessionStatus.REQUESTED
    meeting_link: Optional[str] = None
    notes: str = ""
    rating: Optional[int] = None
    feedback: str = ""
    milestones: List[CurriculumMilestone] = field(default_factory=list)


class MentorshipService:
    """Handles booking, managing, and tracking mentorship sessions and curricula."""

    def __init__(self):
        self._sessions: Dict[str, MentorshipSession] = {}

    def book_session(
        self, mentor_id: str, mentee_id: str, topic: str, scheduled_timestamp: float, duration_minutes: int = 45
    ) -> MentorshipSession:
        """Creates a new requested mentorship session."""
        session_id = f"session_{mentor_id[:6]}_{mentee_id[:6]}_{int(time.time())}"
        session = MentorshipSession(
            session_id=session_id,
            mentor_id=mentor_id,
            mentee_id=mentee_id,
            topic=topic,
            scheduled_timestamp=scheduled_timestamp,
            duration_minutes=duration_minutes,
            status=SessionStatus.REQUESTED
        )
        self._sessions[session_id] = session
        return session

    def update_session_status(
        self, session_id: str, status: SessionStatus, meeting_link: Optional[str] = None
    ) -> Optional[MentorshipSession]:
        """Transitions session status and sets meeting link if confirmed."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        session.status = status
        if meeting_link:
            session.meeting_link = meeting_link
        return session

    def submit_feedback(
        self, session_id: str, rating: int, feedback: str
    ) -> Optional[MentorshipSession]:
        """Submits mentee/mentor feedback and rating upon completion."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        session.rating = max(1, min(5, rating))
        session.feedback = feedback
        return session

    def add_milestone(
        self, session_id: str, title: str, description: str
    ) -> Optional[CurriculumMilestone]:
        """Attaches a learning roadmap milestone to a mentorship session."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        m_id = f"m_{len(session.milestones)+1}_{int(time.time())}"
        milestone = CurriculumMilestone(milestone_id=m_id, title=title, description=description)
        session.milestones.append(milestone)
        return milestone

    def get_session(self, session_id: str) -> Optional[MentorshipSession]:
        return self._sessions.get(session_id)


mentorship_service = MentorshipService()
