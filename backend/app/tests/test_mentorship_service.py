"""
Comprehensive Unit tests for Interactive Learning & Mentorship Platform.
"""

import pytest
from app.services.mentorship_service import (
    MentorshipService,
    MentorshipSession,
    SessionStatus,
    mentorship_service
)


@pytest.fixture
def mentorship():
    return MentorshipService()


def test_book_session(mentorship):
    session = mentorship.book_session(
        mentor_id="mentor_100",
        mentee_id="mentee_200",
        topic="FastAPI Middleware Architecture",
        scheduled_timestamp=1724500000.0,
        duration_minutes=60
    )
    assert session.mentor_id == "mentor_100"
    assert session.mentee_id == "mentee_200"
    assert session.topic == "FastAPI Middleware Architecture"
    assert session.duration_minutes == 60
    assert session.status == SessionStatus.REQUESTED


def test_update_session_status_confirmed(mentorship):
    session = mentorship.book_session(
        mentor_id="mentor_2",
        mentee_id="mentee_2",
        topic="Open Source Git Flow",
        scheduled_timestamp=1724600000.0
    )
    updated = mentorship.update_session_status(
        session.session_id,
        SessionStatus.CONFIRMED,
        meeting_link="https://meet.devlink.io/session-123"
    )
    assert updated is not None
    assert updated.status == SessionStatus.CONFIRMED
    assert updated.meeting_link == "https://meet.devlink.io/session-123"


def test_submit_feedback_and_rating(mentorship):
    session = mentorship.book_session("m1", "me1", "Docker basics", 1724700000.0)
    mentorship.update_session_status(session.session_id, SessionStatus.COMPLETED)
    updated = mentorship.submit_feedback(session.session_id, rating=5, feedback="Outstanding mentor!")
    assert updated is not None
    assert updated.rating == 5
    assert updated.feedback == "Outstanding mentor!"


def test_curriculum_milestones(mentorship):
    session = mentorship.book_session("m1", "me1", "FullCourse", 1724800000.0)
    m = mentorship.add_milestone(session.session_id, "Build REST API", "Implement CRUD with auth")
    assert m is not None
    assert m.title == "Build REST API"
    assert len(session.milestones) == 1


def test_session_state_transitions(mentorship):
    session = mentorship.book_session("mentor_3", "mentee_3", "Rust Memory Safety", 1724900000.0)
    assert session.status == SessionStatus.REQUESTED

    mentorship.update_session_status(session.session_id, SessionStatus.CONFIRMED, "https://meet.devlink.io/rust")
    assert session.status == SessionStatus.CONFIRMED
    assert session.meeting_link == "https://meet.devlink.io/rust"

    mentorship.update_session_status(session.session_id, SessionStatus.IN_PROGRESS)
    assert session.status == SessionStatus.IN_PROGRESS

    mentorship.update_session_status(session.session_id, SessionStatus.COMPLETED)
    assert session.status == SessionStatus.COMPLETED


def test_rating_boundary_clamping(mentorship):
    session = mentorship.book_session("m_test", "me_test", "Unit testing", 1725000000.0)
    mentorship.submit_feedback(session.session_id, rating=10, feedback="Over 5 rating")
    assert session.rating == 5

    mentorship.submit_feedback(session.session_id, rating=-2, feedback="Negative rating")
    assert session.rating == 1


def test_multiple_milestones_addition(mentorship):
    session = mentorship.book_session("m_test", "me_test", "Full Course", 1725000000.0)
    m1 = mentorship.add_milestone(session.session_id, "Step 1", "Setup dev environment")
    m2 = mentorship.add_milestone(session.session_id, "Step 2", "Write first test")
    assert len(session.milestones) == 2
    assert m1.title == "Step 1"
    assert m2.title == "Step 2"
