from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query, status
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(
    tags=["Users"],
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

    password_hash = AuthService.hash_password(
        user.password,
    )

    return UserService.create_user(
        db=db,
        user=user,
        password_hash=password_hash,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):

    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
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

    return user


@router.get(
    "/",
    response_model=list[UserResponse],
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_database),
):

    return UserService.list_users(
        db,
        skip,
        limit,
    )


@router.put(
    "/me",
    response_model=UserResponse,
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
