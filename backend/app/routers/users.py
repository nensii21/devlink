from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from sqlalchemy.orm import Session
from app.dependencies import get_database
from app.dependencies import get_current_user
from app.middleware.rate_limit import limiter, SEARCH_LIMIT
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    CurrentUser,
    UserStats,
    UserUpdate,
    UsernameAvailabilityResponse,
)
from app.schemas.user_report import (
    UserReportCreate,
    UserReportResponse,
)
from app.models.user_report import UserReport
from app.core.security import hash_password
from app.services.user_service import UserService
from app.utils.validators import validate_username

router = APIRouter(
    tags=["Users"],
)


@router.get(
    "/check-username",
    response_model=UsernameAvailabilityResponse,
    summary="Check Username Availability",
)
def check_username(
    username: str = Query(..., description="The username to check availability for"),
    db: Session = Depends(get_database),
):
    """
    Check if a username is available for registration.
    """
    try:
        username = validate_username(username)
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    existing_user = UserService.get_by_username(db, username)
    if existing_user:
        return UsernameAvailabilityResponse(
            available=False,
            message="Username is already taken.",
        )
    return UsernameAvailabilityResponse(
        available=True,
        message="Username is available.",
    )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_database),
):

    if UserService.get_by_email(db, user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )
    if UserService.get_by_username(db, user.username):
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )
    password_hash = hash_password(
        user.password,
    )

    return UserService.create_user(
        db=db,
        user=user,
        password_hash=password_hash,
    )


@router.get(
    "/me",
    response_model=CurrentUser,
)
def get_me(
    online_threshold: int | None = Query(
        None, description="Online threshold in seconds"
    ),
    current_user: User = Depends(get_current_user),
):

    if online_threshold is not None:
        current_user._online_threshold = online_threshold
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: uuid.UUID,
    online_threshold: int | None = Query(
        None, description="Online threshold in seconds"
    ),
    db: Session = Depends(get_database),
):

    user = UserService.get_user(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    if online_threshold is not None:
        user._online_threshold = online_threshold
    return user


@router.get(
    "/",
    response_model=list[UserResponse],
)
@limiter.limit(SEARCH_LIMIT)
def list_users(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    online_threshold: int | None = Query(
        None, description="Online threshold in seconds"
    ),
    db: Session = Depends(get_database),
):

    users = UserService.list_users(
        db,
        skip,
        limit,
    )

    if online_threshold is not None:
        for u in users:
            u._online_threshold = online_threshold
    return users


@router.get(
    "/{user_id}/stats",
    response_model=UserStats,
)
def get_user_stats(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    if UserService.get_user(db, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserService.get_user_stats(db, user_id)


@router.put(
    "/me",
    response_model=CurrentUser,
)
def update_me(
    user: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return UserService.update_user(
        db,
        current_user,
        user,
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    UserService.delete_user(
        db,
        current_user,
    )


@router.patch(
    "/{user_id}/activate",
    response_model=UserResponse,
)
def activate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    user = UserService.get_user(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return UserService.activate_user(
        db,
        user,
    )


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
)
def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    user = UserService.get_user(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return UserService.deactivate_user(
        db,
        user,
    )


@router.patch(
    "/{user_id}/verify",
    response_model=UserResponse,
)
def verify_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    user = UserService.get_user(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return UserService.verify_email(
        db,
        user,
    )


@router.post(
    "/{user_id}/report",
    response_model=UserReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def report_user(
    user_id: uuid.UUID,
    report: UserReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    target_user = UserService.get_user(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.id == target_user.id:
        raise HTTPException(status_code=400, detail="You cannot report yourself")
    db_report = UserReport(
        reporter_id=current_user.id,
        reported_id=target_user.id,
        reason=report.reason,
        description=report.description,
        status="pending",
    )

    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    return db_report
