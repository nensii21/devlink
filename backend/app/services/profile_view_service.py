import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.profile_view import ProfileView
from app.models.user import User
from app.schemas.profile_view import ProfileViewResponse, PaginatedProfileViewsResponse


class ProfileViewService:
    """
    Business logic for recording profile visits and managing visitor privacy.
    """

    @staticmethod
    def record_view(
        db: Session,
        viewed_user_id: uuid.UUID,
        viewer_id: uuid.UUID,
        is_anonymous_override: Optional[bool] = None,
    ) -> Optional[ProfileView]:
        """
        Records a visit from viewer to viewed_user.
        Self-views are ignored. Updates timestamp and increments visit_count if visited recently.
        """
        if viewed_user_id == viewer_id:
            return None

        # Check viewer privacy preference or override
        viewer = db.get(User, viewer_id)
        is_anonymous = (
            is_anonymous_override
            if is_anonymous_override is not None
            else getattr(viewer, "hide_profile_views", False)
        )

        # Check existing recent view entry for deduplication/refresh
        stmt = (
            select(ProfileView)
            .where(
                and_(
                    ProfileView.viewed_user_id == viewed_user_id,
                    ProfileView.viewer_id == viewer_id,
                )
            )
            .order_by(ProfileView.created_at.desc())
            .limit(1)
        )

        existing_view = db.scalar(stmt)

        if existing_view:
            existing_view.created_at = datetime.now(timezone.utc)
            existing_view.is_anonymous = is_anonymous
            existing_view.visit_count = (getattr(existing_view, "visit_count", 1) or 1) + 1
            db.commit()
            db.refresh(existing_view)
            return existing_view

        view = ProfileView(
            viewed_user_id=viewed_user_id,
            viewer_id=viewer_id,
            is_anonymous=is_anonymous,
            visit_count=1,
            created_at=datetime.now(timezone.utc),
        )
        db.add(view)
        db.commit()
        db.refresh(view)
        return view

    @staticmethod
    def get_profile_views(
        db: Session,
        user_id: uuid.UUID,
        page: int = 1,
        size: int = 10,
    ) -> PaginatedProfileViewsResponse:
        """
        Retrieves recent profile visitors for a user with pagination.
        Masks details if viewer opted out / is anonymous.
        """
        offset = (page - 1) * size

        # Total count query
        count_stmt = (
            select(func.count())
            .select_from(ProfileView)
            .where(ProfileView.viewed_user_id == user_id)
        )
        total = db.scalar(count_stmt) or 0

        # Items query
        stmt = (
            select(ProfileView, User)
            .join(User, ProfileView.viewer_id == User.id)
            .where(ProfileView.viewed_user_id == user_id)
            .order_by(ProfileView.created_at.desc())
            .offset(offset)
            .limit(size)
        )

        results = db.execute(stmt).all()
        items: List[ProfileViewResponse] = []

        for view, viewer in results:
            visit_count = getattr(view, "visit_count", 1) or 1
            if view.is_anonymous:
                items.append(
                    ProfileViewResponse(
                        id=view.id,
                        viewer_id=None,
                        viewer_name="Anonymous Developer",
                        viewer_username="anonymous",
                        viewer_avatar=None,
                        viewed_at=view.created_at,
                        visit_count=visit_count,
                        is_anonymous=True,
                    )
                )
            else:
                items.append(
                    ProfileViewResponse(
                        id=view.id,
                        viewer_id=viewer.id,
                        viewer_name=f"{viewer.first_name} {viewer.last_name}".strip()
                        or viewer.username,
                        viewer_username=viewer.username,
                        viewer_avatar=getattr(viewer, "profile_image", None) or getattr(viewer, "avatar_url", None),
                        viewed_at=view.created_at,
                        visit_count=visit_count,
                        is_anonymous=False,
                    )
                )

        total_pages = (total + size - 1) // size if total > 0 else 1

        return PaginatedProfileViewsResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )
