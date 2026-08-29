import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.schemas.profile_view import (
    PaginatedProfileViewsResponse,
    ProfileViewPrivacySettings,
)
from app.services.profile_view_service import ProfileViewService

router = APIRouter(prefix="/profile-views", tags=["Profile Views"])


@router.post(
    "/{user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Record a profile view",
)
def record_profile_view(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Record that current_user visited target user_id's profile.
    Self-views are ignored.
    """
    view = ProfileViewService.record_view(
        db=db,
        viewed_user_id=user_id,
        viewer_id=current_user.id,
    )
    if not view:
        return {"message": "Self view ignored"}
    return {"status": "success", "view_id": str(view.id)}


@router.get(
    "/history",
    response_model=PaginatedProfileViewsResponse,
    summary="Get recent profile visitors",
)
def get_my_profile_views(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves paginated history of users who recently visited your profile.
    Anonymous viewers will have masked credentials.
    Feature is exclusive to premium members.
    """
    is_premium = (
        getattr(current_user, "premium", False)
        or getattr(current_user, "is_premium", False)
        or getattr(current_user, "is_superuser", False)
    )
    if not is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recent profile visitors feature is only available for premium members.",
        )

    return ProfileViewService.get_profile_views(
        db=db,
        user_id=current_user.id,
        page=page,
        size=size,
    )


@router.get(
    "/privacy",
    response_model=ProfileViewPrivacySettings,
    summary="Get profile view privacy setting",
)
def get_privacy_settings(
    current_user: User = Depends(get_current_user),
):
    """
    Check if your visits to other profiles are hidden/anonymous.
    """
    hide = getattr(current_user, "hide_profile_views", False)
    return ProfileViewPrivacySettings(hide_profile_views=hide)


@router.put(
    "/privacy",
    response_model=ProfileViewPrivacySettings,
    summary="Update profile view privacy setting",
)
def update_privacy_settings(
    settings: ProfileViewPrivacySettings,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle hide_profile_views to visit profiles anonymously.
    """
    setattr(current_user, "hide_profile_views", settings.hide_profile_views)
    db.commit()
    db.refresh(current_user)
    return ProfileViewPrivacySettings(
        hide_profile_views=current_user.hide_profile_views
    )
