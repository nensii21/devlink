"""
Mentorship and interactive learning platform service module.
Manages session scheduling, mentee progression, curriculum milestones, skill-based matching, and status transitions.
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
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
class StructuredFeedback:
    communication_score: int  # 1-5
    technical_accuracy_score: int  # 1-5
    helpfulness_score: int  # 1-5
    written_feedback: str


@dataclass
class TimeWindow:
    start_time: float
    end_time: float


@dataclass
class MentorProfile:
    mentor_id: str
    skills: List[str]
    availability_windows: List[TimeWindow] = field(default_factory=list)
    rating_score: float = 5.0
    total_sessions: int = 0


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
    feedback: Optional[StructuredFeedback] = None
    milestones: List[CurriculumMilestone] = field(default_factory=list)


class MentorshipService:
    """Handles booking, managing, and tracking mentorship sessions and curricula."""

    def __init__(self):
        self._sessions: Dict[str, MentorshipSession] = {}
        self._mentors: Dict[str, MentorProfile] = {}
        # Callback hooks for notifications
        self.on_session_status_changed: List[Callable[[MentorshipSession], None]] = []

    def register_mentor(self, mentor_id: str, skills: List[str], availability_windows: List[TimeWindow]) -> MentorProfile:
        profile = MentorProfile(mentor_id=mentor_id, skills=[s.lower() for s in skills], availability_windows=availability_windows)
        self._mentors[mentor_id] = profile
        return profile

    def find_matches(self, mentee_skills: List[str], required_expertise: List[str], limit: int = 5) -> List[Tuple[MentorProfile, float]]:
        """
        Skill-based matching algorithm using weighted similarity scoring.
        Prioritizes required_expertise overlap heavily, and general skill overlap secondarily.
        """
        matches = []
        required_set = set([s.lower() for s in required_expertise])
        mentee_set = set([s.lower() for s in mentee_skills])

        for profile in self._mentors.values():
            mentor_set = set(profile.skills)
            
            # Weighted intersection
            req_intersection = required_set.intersection(mentor_set)
            gen_intersection = mentee_set.intersection(mentor_set)
            
            # Score formula: 10 points per required skill, 2 points per general skill, + normalized rating
            score = (len(req_intersection) * 10.0) + (len(gen_intersection) * 2.0) + profile.rating_score
            
            if score > 0:
                matches.append((profile, score))
                
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]

    def _is_available(self, mentor_id: str, requested_start: float, duration_minutes: int) -> bool:
        """Validates if the mentor is available at the given time and there are no overlapping confirmed sessions."""
        mentor = self._mentors.get(mentor_id)
        if not mentor:
            return False
            
        requested_end = requested_start + (duration_minutes * 60)
        
        # Check standard availability windows
        within_window = False
        for window in mentor.availability_windows:
            if requested_start >= window.start_time and requested_end <= window.end_time:
                within_window = True
                break
                
        if not within_window:
            return False
            
        # Check for scheduling conflicts with existing CONFIRMED or IN_PROGRESS sessions
        for session in self._sessions.values():
            if session.mentor_id == mentor_id and session.status in [SessionStatus.CONFIRMED, SessionStatus.IN_PROGRESS]:
                session_start = session.scheduled_timestamp
                session_end = session_start + (session.duration_minutes * 60)
                # Overlap detection: max(start1, start2) < min(end1, end2)
                if max(requested_start, session_start) < min(requested_end, session_end):
                    return False # Conflict found
                    
        return True

    def book_session(
        self, mentor_id: str, mentee_id: str, topic: str, scheduled_timestamp: float, duration_minutes: int = 45
    ) -> MentorshipSession:
        """Creates a new requested mentorship session if the mentor is available."""
        if not self._is_available(mentor_id, scheduled_timestamp, duration_minutes):
            raise ValueError("Mentor is unavailable or has a scheduling conflict during this time.")
            
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
        self._notify_status_change(session)
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
        
        self._notify_status_change(session)
        return session

    def submit_feedback(
        self, session_id: str, feedback: StructuredFeedback
    ) -> Optional[MentorshipSession]:
        """Submits mentee/mentor structured feedback and updates the mentor's aggregate rating."""
        session = self._sessions.get(session_id)
        if not session:
            return None
            
        session.feedback = feedback
        
        # Aggregate feedback to mentor profile
        mentor = self._mentors.get(session.mentor_id)
        if mentor:
            avg_feedback_score = (feedback.communication_score + feedback.technical_accuracy_score + feedback.helpfulness_score) / 3.0
            # Simple moving average for rating updates
            mentor.rating_score = ((mentor.rating_score * mentor.total_sessions) + avg_feedback_score) / (mentor.total_sessions + 1)
            mentor.total_sessions += 1
            
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
        
    def _notify_status_change(self, session: MentorshipSession) -> None:
        """Triggers all registered notification callbacks for status changes."""
        for callback in self.on_session_status_changed:
            try:
                callback(session)
            except Exception as e:
                pass # Prevent notification failures from crashing core flow


mentorship_service = MentorshipService()
