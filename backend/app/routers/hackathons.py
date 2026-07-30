from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.schemas.hackathon import (
    HackathonCreate,
    HackathonJudgeResponse,
    HackathonLeaderboardEntry,
    HackathonRegistrationCreate,
    HackathonRegistrationResponse,
    HackathonResponse,
    HackathonScoreCreate,
    HackathonScoreResponse,
    HackathonSubmissionCreate,
    HackathonSubmissionResponse,
    HackathonSubmissionUpdate,
    HackathonTeamCreate,
    HackathonTeamMemberResponse,
    HackathonTeamResponse,
    HackathonUpdate,
)
from app.services.hackathon_service import HackathonService

router = APIRouter(
    tags=["Hackathons"],
)


# ==============================================================
# Hackathon CRUD
# ==============================================================


@router.post(
    "/",
    response_model=HackathonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_hackathon(
    hackathon: HackathonCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    return HackathonService.create_hackathon(
        db=db,
        user_id=current_user.id,
        hackathon=hackathon,
    )


@router.get(
    "/",
    response_model=list[HackathonResponse],
)
def list_hackathons(
    db: Session = Depends(get_database),
):
    return HackathonService.list_published_hackathons(db)


@router.get(
    "/{hackathon_id}",
    response_model=HackathonResponse,
)
def get_hackathon(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    hackathon = HackathonService.get_hackathon(db, hackathon_id)

    if hackathon is None:
        raise HTTPException(
            status_code=404,
            detail="Hackathon not found",
        )

    return hackathon


@router.put(
    "/{hackathon_id}",
    response_model=HackathonResponse,
)
def update_hackathon(
    hackathon_id: uuid.UUID,
    hackathon: HackathonUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_hackathon = HackathonService.get_hackathon(db, hackathon_id)

    if db_hackathon is None:
        raise HTTPException(
            status_code=404,
            detail="Hackathon not found",
        )

    if db_hackathon.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the hackathon creator can update it",
        )

    return HackathonService.update_hackathon(db, db_hackathon, hackathon)


@router.delete(
    "/{hackathon_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_hackathon(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_hackathon = HackathonService.get_hackathon(db, hackathon_id)

    if db_hackathon is None:
        raise HTTPException(
            status_code=404,
            detail="Hackathon not found",
        )

    if db_hackathon.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the hackathon creator can delete it",
        )

    HackathonService.delete_hackathon(db, db_hackathon)


# ==============================================================
# Team Management
# ==============================================================


@router.post(
    "/{hackathon_id}/teams",
    response_model=HackathonTeamResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    hackathon_id: uuid.UUID,
    team: HackathonTeamCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_hackathon = HackathonService.get_hackathon(db, hackathon_id)

    if db_hackathon is None:
        raise HTTPException(
            status_code=404,
            detail="Hackathon not found",
        )

    return HackathonService.create_team(
        db=db,
        user_id=current_user.id,
        hackathon_id=hackathon_id,
        team=team,
    )


@router.get(
    "/{hackathon_id}/teams",
    response_model=list[HackathonTeamResponse],
)
def list_teams(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    return HackathonService.list_hackathon_teams(db, hackathon_id)


@router.post(
    "/teams/{team_id}/join",
    response_model=HackathonTeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def join_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_team = HackathonService.get_team(db, team_id)

    if db_team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found",
        )

    return HackathonService.join_team(
        db=db,
        user_id=current_user.id,
        team_id=team_id,
    )


@router.delete(
    "/teams/{team_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
)
def leave_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    HackathonService.leave_team(
        db=db,
        user_id=current_user.id,
        team_id=team_id,
    )


# ==============================================================
# Registration
# ==============================================================


@router.post(
    "/{hackathon_id}/registrations",
    response_model=HackathonRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_for_hackathon(
    hackathon_id: uuid.UUID,
    registration: HackathonRegistrationCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_hackathon = HackathonService.get_hackathon(db, hackathon_id)

    if db_hackathon is None:
        raise HTTPException(
            status_code=404,
            detail="Hackathon not found",
        )

    existing = HackathonService.get_registration(db, hackathon_id, current_user.id)

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already registered for this hackathon",
        )

    return HackathonService.register_for_hackathon(
        db=db,
        user_id=current_user.id,
        hackathon_id=hackathon_id,
        registration=registration,
    )


@router.get(
    "/{hackathon_id}/registrations",
    response_model=list[HackathonRegistrationResponse],
)
def list_registrations(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    return HackathonService.list_hackathon_registrations(db, hackathon_id)


@router.delete(
    "/{hackathon_id}/registrations",
    response_model=HackathonRegistrationResponse,
)
def cancel_registration(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_registration = HackathonService.get_registration(
        db, hackathon_id, current_user.id
    )

    if db_registration is None:
        raise HTTPException(
            status_code=404,
            detail="Registration not found",
        )

    return HackathonService.cancel_registration(db, db_registration)


# ==============================================================
# Submissions
# ==============================================================


@router.post(
    "/{hackathon_id}/submissions",
    response_model=HackathonSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_submission(
    hackathon_id: uuid.UUID,
    submission: HackathonSubmissionCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_hackathon = HackathonService.get_hackathon(db, hackathon_id)

    if db_hackathon is None:
        raise HTTPException(
            status_code=404,
            detail="Hackathon not found",
        )

    return HackathonService.create_submission(
        db=db,
        user_id=current_user.id,
        hackathon_id=hackathon_id,
        submission=submission,
    )


@router.get(
    "/{hackathon_id}/submissions",
    response_model=list[HackathonSubmissionResponse],
)
def list_submissions(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    return HackathonService.list_hackathon_submissions(db, hackathon_id)


@router.put(
    "/submissions/{submission_id}",
    response_model=HackathonSubmissionResponse,
)
def update_submission(
    submission_id: uuid.UUID,
    submission: HackathonSubmissionUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_submission = HackathonService.get_submission(db, submission_id)

    if db_submission is None:
        raise HTTPException(
            status_code=404,
            detail="Submission not found",
        )

    if db_submission.submitted_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the submission author can update it",
        )

    return HackathonService.update_submission(db, db_submission, submission)


# ==============================================================
# Judges & Scores
# ==============================================================


@router.post(
    "/{hackathon_id}/judges",
    response_model=HackathonJudgeResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_judge(
    hackathon_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_hackathon = HackathonService.get_hackathon(db, hackathon_id)

    if db_hackathon is None:
        raise HTTPException(
            status_code=404,
            detail="Hackathon not found",
        )

    if db_hackathon.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the hackathon creator can assign judges",
        )

    return HackathonService.assign_judge(db, hackathon_id, user_id)


@router.get(
    "/{hackathon_id}/judges",
    response_model=list[HackathonJudgeResponse],
)
def list_judges(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    return HackathonService.list_hackathon_judges(db, hackathon_id)


@router.post(
    "/scores",
    response_model=HackathonScoreResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_or_update_score(
    score: HackathonScoreCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_submission = HackathonService.get_submission(db, score.submission_id)

    if db_submission is None:
        raise HTTPException(
            status_code=404,
            detail="Submission not found",
        )

    if not HackathonService.is_judge(db, db_submission.hackathon_id, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Only assigned judges can score submissions",
        )

    try:
        return HackathonService.create_or_update_score(
            db=db,
            submission_id=score.submission_id,
            hackathon_id=db_submission.hackathon_id,
            judge_user_id=current_user.id,
            score=score.score,
            comments=score.comments,
        )
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="User is not an assigned judge",
        )


@router.get(
    "/{hackathon_id}/leaderboard",
    response_model=list[HackathonLeaderboardEntry],
)
def get_leaderboard(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    return HackathonService.get_leaderboard(db, hackathon_id)
