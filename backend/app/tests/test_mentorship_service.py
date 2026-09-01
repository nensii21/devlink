import pytest
import time
from app.services.mentorship_service import (
    MentorshipService,
    SessionStatus,
    TimeWindow,
    StructuredFeedback
)

@pytest.fixture
def mentorship_service():
    return MentorshipService()

def test_register_and_match(mentorship_service):
    # Register mentors
    mentorship_service.register_mentor(
        mentor_id="mentor_1",
        skills=["python", "django", "aws"],
        availability_windows=[]
    )
    mentorship_service.register_mentor(
        mentor_id="mentor_2",
        skills=["python", "react", "fastapi"],
        availability_windows=[]
    )
    
    # Mentee needs react and python
    matches = mentorship_service.find_matches(
        mentee_skills=["javascript"], 
        required_expertise=["react", "python"]
    )
    
    assert len(matches) > 0
    best_match = matches[0][0]
    assert best_match.mentor_id == "mentor_2"

def test_availability_and_scheduling(mentorship_service):
    now = time.time()
    
    # Register mentor with a window of 2 hours starting now
    mentorship_service.register_mentor(
        mentor_id="mentor_avail",
        skills=["python"],
        availability_windows=[TimeWindow(start_time=now, end_time=now + 7200)]
    )
    
    # Successfully book a session within the window
    session1 = mentorship_service.book_session(
        mentor_id="mentor_avail",
        mentee_id="mentee_1",
        topic="Help with Python",
        scheduled_timestamp=now,
        duration_minutes=60
    )
    assert session1 is not None
    assert session1.status == SessionStatus.REQUESTED
    
    # Confirm it to trigger conflict logic
    mentorship_service.update_session_status(session1.session_id, SessionStatus.CONFIRMED)
    
    # Try to double-book in the same window (should fail)
    with pytest.raises(ValueError, match="scheduling conflict"):
        mentorship_service.book_session(
            mentor_id="mentor_avail",
            mentee_id="mentee_2",
            topic="Double Book",
            scheduled_timestamp=now + 1800, # Starts halfway through session1
            duration_minutes=30
        )
        
    # Try to book outside window (should fail)
    with pytest.raises(ValueError, match="unavailable"):
        mentorship_service.book_session(
            mentor_id="mentor_avail",
            mentee_id="mentee_3",
            topic="Outside Window",
            scheduled_timestamp=now + 10000,
            duration_minutes=60
        )

def test_structured_feedback_aggregation(mentorship_service):
    now = time.time()
    mentor = mentorship_service.register_mentor(
        mentor_id="mentor_fb",
        skills=["aws"],
        availability_windows=[TimeWindow(start_time=now, end_time=now + 3600)]
    )
    
    session = mentorship_service.book_session("mentor_fb", "m1", "AWS setup", now, 30)
    mentorship_service.update_session_status(session.session_id, SessionStatus.COMPLETED)
    
    feedback = StructuredFeedback(
        communication_score=5,
        technical_accuracy_score=4,
        helpfulness_score=5,
        written_feedback="Great session!"
    )
    
    mentorship_service.submit_feedback(session.session_id, feedback)
    
    # Expected avg = (5+4+5)/3 = 4.666...
    # Previous rating = 5.0, total sessions = 0
    # New avg = (0 + 4.666) / 1 = 4.666...
    assert 4.6 <= mentor.rating_score <= 4.7
    assert mentor.total_sessions == 1

def test_notification_hooks(mentorship_service):
    now = time.time()
    mentorship_service.register_mentor("m1", ["test"], [TimeWindow(start_time=now, end_time=now + 3600)])
    
    notified_status = []
    
    def on_status_change(session):
        notified_status.append(session.status)
        
    mentorship_service.on_session_status_changed.append(on_status_change)
    
    # Booking creates REQUESTED status
    session = mentorship_service.book_session("m1", "me1", "topic", now, 30)
    assert SessionStatus.REQUESTED in notified_status
    
    # Update to CONFIRMED
    mentorship_service.update_session_status(session.session_id, SessionStatus.CONFIRMED)
    assert SessionStatus.CONFIRMED in notified_status
