from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
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
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
):

    UserService.soft_delete_user(
        db,
        current_user,
        deleted_by_id=current_user.id,
    )


@router.patch(
    "/{user_id}/restore",
    response_model=UserResponse,
)
def restore_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only admins can restore users",
        )

    user = UserService.get_user_including_deleted(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.deleted_at is None:
        raise HTTPException(
            status_code=400,
            detail="User is not deleted",
        )

    return UserService.restore_user(
        db,
        user,
    )


@router.delete(
    "/{user_id}/hard",
    status_code=status.HTTP_204_NO_CONTENT,
)
def hard_delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only admins can permanently delete users",
        )

    user = UserService.get_user_including_deleted(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    UserService.hard_delete_user(
        db,
        user,
    )


@router.patch(
    "/{user_id}/activate",
    response_model=UserResponse,
)
def activate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
