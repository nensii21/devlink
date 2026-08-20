from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)

# pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.cache import cache_manager, cached
from app.dependencies import get_current_user, get_database, get_optional_current_user
from app.middleware.rate_limit import SEARCH_LIMIT, limiter
from app.models.user import User
from app.services.block_service import BlockService
from app.schemas.user import (
    CollaborationStatus,
    CurrentUser,
    PrivacySettings,
    PrivacySettingsUpdate,
    ProfileCompletionResponse,
    ResumeParseResponse,
    UserCreate,
    UsernameAvailabilityResponse,
    UserResponse,
    UserStats,
    UserUpdate,
)
from app.schemas.user_report import (
    UserReportCreate,
    UserReportResponse,
)
from app.services.user_service import UserService
from app.utils.uploads import (
    save_image_upload,
    save_resume_upload,
    save_video_introduction_upload,
    save_voice_introduction_upload,
    validate_image_upload,
    validate_resume_upload,
    validate_video_introduction_upload,
    validate_voice_introduction_upload,
)
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
@cached(ttl=300, key_prefix="user")
def get_me(
    online_threshold: int | None = Query(
        None, description="Online threshold in seconds"
    ),
    current_user: User = Depends(get_current_user),
):

    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if online_threshold is not None:
        current_user._online_threshold = online_threshold
    return current_user


@router.get(
    "/me/privacy",
    response_model=PrivacySettings,
    summary="Get Privacy Settings",
)
def get_my_privacy_settings(
    current_user: User = Depends(get_current_user),
):
    """
    Get profile privacy controls for the current user.
    """
    return current_user.get_privacy_settings()


@router.put(
    "/me/privacy",
    response_model=CurrentUser,
    summary="Update Privacy Settings",
)
def update_my_privacy_settings(
    settings: PrivacySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Update profile privacy controls for email, GitHub, resume, social links, and availability.
    """
    return UserService.update_privacy_settings(db, current_user, settings)


@router.get(
    "/me/completion",
    response_model=ProfileCompletionResponse,
    summary="Get Current User Profile Completion",
)
def get_my_profile_completion(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Get profile completion percentage and missing factors for current user.
    """
    return UserService.get_profile_completion(db, current_user)


@router.get(
    "/{user_id}/completion",
    response_model=ProfileCompletionResponse,
    summary="Get User Profile Completion by ID",
)
def get_user_profile_completion(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """
    Get profile completion percentage and missing factors for a specific user.
    """
    user = UserService.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserService.get_profile_completion(db, user)


@router.get(
    "/by-username/{username}",
    response_model=UserResponse,
    summary="Get User Profile by Username",
)
def get_user_by_username(
    username: str,
    online_threshold: int | None = Query(
        None, description="Online threshold in seconds"
    ),
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
):
    user = UserService.get_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Check private profile and blocking restrictions
    if user.is_private:
        if not current_user or (
            current_user.id != user.id
            and BlockService.is_blocked(db, user.id, current_user.id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this private profile.",
            )

    if online_threshold is not None:
        user._online_threshold = online_threshold

    user = UserService.apply_privacy_filters(db, user, current_user)
    return user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
@cached(ttl=300, key_prefix="user")
def get_user(
    user_id: uuid.UUID,
    online_threshold: int | None = Query(
        None, description="Online threshold in seconds"
    ),
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
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

    # Check private profile and blocking restrictions
    if user.is_private:
        if not current_user or (
            current_user.id != user_id
            and BlockService.is_blocked(db, user_id, current_user.id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this private profile.",
            )

    if online_threshold is not None:
        user._online_threshold = online_threshold

    user = UserService.apply_privacy_filters(db, user, current_user)
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
    current_user: User | None = Depends(get_optional_current_user),
):

    users = UserService.list_users(
        db,
        skip,
        limit,
    )

    filtered_users = []
    for u in users:
        fu = UserService.apply_privacy_filters(db, u, current_user)
        if online_threshold is not None:
            fu._online_threshold = online_threshold
        filtered_users.append(fu)

    return filtered_users


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
    from app.models.audit_log import AuditAction
    from app.services.audit_log_service import AuditLogService

    # Extract old values for fields that are being updated
    old_values = {}
    for key in user.model_dump(exclude_unset=True).keys():
        old_values[key] = getattr(current_user, key, None)

    updated_user = UserService.update_user(
        db,
        current_user,
        user,
    )

    new_values = user.model_dump(exclude_unset=True)

    AuditLogService.create_log(
        db=db,
        actor_id=updated_user.id,
        action=AuditAction.PROFILE_UPDATED,
        entity_type="user",
        entity_id=str(updated_user.id),
        target_user_id=updated_user.id,
        old_values=old_values,
        new_values=new_values,
        description="User updated their profile",
    )

    cache_manager.delete_pattern(f"user:*{updated_user.id}*")

    return updated_user


@router.get(
    "/me/collaboration-status",
    response_model=dict,
    summary="Get live collaboration presence status",
)
def get_collaboration_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get the current user's live collaboration presence status
    (coding, reviewing_pr, in_meeting, looking_for_project, available).
    """
    return {
        "user_id": str(current_user.id),
        "status": current_user.collaboration_status,
    }


@router.put(
    "/me/collaboration-status",
    response_model=dict,
    summary="Set live collaboration presence status",
)
def set_collaboration_status(
    status_val: CollaborationStatus = Query(
        ...,
        description="One of: coding, reviewing_pr, in_meeting, looking_for_project, available",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Set the current user's live collaboration presence status and broadcast the
    change to all connected WebSocket clients.
    """
    current_user.collaboration_status = status_val.value
    db.commit()
    db.refresh(current_user)

    try:
        from app.routers.websockets import manager

        manager.set_collaboration_status(str(current_user.id), status_val.value)
    except Exception:
        # WebSocket manager is in-memory; a failure to broadcast should not
        # fail the persistence of the status update.
        pass

    return {"user_id": str(current_user.id), "status": status_val.value}


@router.put(
    "/me/premium",
    response_model=UserResponse,
    summary="Toggle user premium status",
)
def update_premium_status(
    premium: bool = Query(True, description="Enable or disable premium status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    current_user.premium = premium
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post(
    "/me/resume",
    response_model=UserResponse,
)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    try:
        validate_resume_upload(file.filename, file.content_type, len(contents))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    resume_url = save_resume_upload(contents, file.filename, current_user.id)
    full_resume_url = str(request.base_url).rstrip("/") + resume_url

    return UserService.update_resume_url(db, current_user, full_resume_url)


@router.post(
    "/me/resume/parse",
    response_model=ResumeParseResponse,
    summary="Upload and parse resume",
)
async def parse_resume(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    from app.services.resume_parser_service import ResumeParserService

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    try:
        validate_resume_upload(file.filename, file.content_type, len(contents))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ResumeParserService.parse_resume(contents, file.filename)


@router.post(
    "/me/avatar",
    response_model=UserResponse,
    summary="Upload and optimize user profile avatar",
)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    try:
        validate_image_upload(file.filename, file.content_type, len(contents))
        saved = save_image_upload(
            contents=contents,
            filename=file.filename,
            subfolder="avatars",
            user_id=current_user.id,
            max_dimensions=(400, 400),
            thumb_dimensions=(150, 150),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    full_avatar_url = str(request.base_url).rstrip("/") + str(saved["image_url"])
    result = UserService.update_profile_image(db, current_user, full_avatar_url)
    cache_manager.delete_pattern(f"user:*{current_user.id}*")
    return result


@router.post(
    "/me/voice-introduction",
    response_model=UserResponse,
    summary="Upload user voice introduction",
)
async def upload_voice_introduction(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()

    try:
        validate_voice_introduction_upload(
            file.filename,
            file.content_type,
            len(contents),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    voice_url = save_voice_introduction_upload(
        contents,
        file.filename,
        current_user.id,
    )

    full_voice_url = str(request.base_url).rstrip("/") + voice_url

    result = UserService.update_voice_introduction_url(
        db,
        current_user,
        full_voice_url,
    )
    cache_manager.delete_pattern(f"user:*{current_user.id}*")
    return result


@router.post(
    "/me/video-introduction",
    response_model=UserResponse,
    summary="Upload user video introduction",
)
async def upload_video_introduction(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()

    try:
        validate_video_introduction_upload(
            file.filename,
            file.content_type,
            len(contents),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    video_url = save_video_introduction_upload(
        contents,
        file.filename,
        current_user.id,
    )

    full_video_url = str(request.base_url).rstrip("/") + video_url

    result = UserService.update_video_introduction_url(
        db,
        current_user,
        full_video_url,
    )
    cache_manager.delete_pattern(f"user:*{current_user.id}*")
    return result


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    UserService.soft_delete_user(
        db,
        current_user,
        deleted_by_id=current_user.id,
    )
    cache_manager.delete_pattern(f"user:*{current_user.id}*")


@router.patch(
    "/{user_id}/restore",
    response_model=UserResponse,
)
def restore_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
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
    db: Session = Depends(get_database),
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

    user = UserService.get_user(db, user_id)

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

    return UserService.create_user_report(db, current_user.id, target_user.id, report)
