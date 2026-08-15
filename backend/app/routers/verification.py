from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.models.user import User
from app.models.verification_request import VerificationRequest
from app.schemas.verification import (
    VerificationRequestCreate,
    VerificationRequestResponse,
    VerificationReview,
    VerificationStatusResponse,
)
from app.dependencies import get_current_user_id

router = APIRouter(tags=["Verification"])


@router.post(
    "/verification/request",
    response_model=VerificationRequestResponse,
    summary="Submit developer verification request",
)
def submit_verification_request(
    payload: VerificationRequestCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(VerificationRequest)
        .filter(
            VerificationRequest.user_id == user_id,
            VerificationRequest.status == "pending",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You already have a pending verification request.",
        )

    request = VerificationRequest(
        user_id=user_id,
        method=payload.method,
        evidence=payload.evidence,
        status="pending",
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.get(
    "/verification/status",
    response_model=VerificationStatusResponse,
    summary="Get verification status",
)
def get_verification_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return VerificationStatusResponse(
        status=user.verification_status,
        verified_at=user.verified_at,
    )


@router.get(
    "/admin/verification/requests",
    response_model=list[VerificationRequestResponse],
    summary="List all verification requests",
)
def list_verification_requests(
    status_filter: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = db.query(VerificationRequest)
    if status_filter:
        query = query.filter(VerificationRequest.status == status_filter)
    return query.order_by(VerificationRequest.id.desc()).all()


@router.post(
    "/admin/verification/requests/{request_id}/review",
    response_model=VerificationRequestResponse,
    summary="Review a verification request",
)
def review_verification_request(
    request_id: str,
    payload: VerificationReview,
    admin_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):
    admin = db.query(User).filter(User.id == admin_id).first()
    if not admin or not admin.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    if payload.status not in ("approved", "rejected"):
        raise HTTPException(
            status_code=400, detail="Status must be 'approved' or 'rejected'"
        )

    request = (
        db.query(VerificationRequest)
        .filter(VerificationRequest.id == request_id)
        .first()
    )
    if not request:
        raise HTTPException(status_code=404, detail="Verification request not found")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request has already been reviewed")

    request.status = payload.status
    request.reviewed_by = admin_id
    request.reviewed_at = datetime.now(timezone.utc)
    request.review_notes = payload.review_notes

    if payload.status == "approved":
        user = db.query(User).filter(User.id == request.user_id).first()
        if user:
            user.verification_status = "verified"
            user.verified_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(request)
    return request
