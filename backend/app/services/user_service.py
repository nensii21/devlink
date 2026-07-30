from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import ActivityType
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.activity_service import ActivityService
from app.models.application import Application, ApplicationStatus
from app.models.follower import Follower
from app.models.project import Project
from app.core.cache import cached
from app.schemas.user import UserStats
from app.models.user_report import UserReport
from app.schemas.user_report import UserReportCreate


class UserService:
    """
    Business logic for User operations.
    """

    @staticmethod
    def get_user(
        db: Session,
        user_id: uuid.UUID,
    ) -> User | None:
        stmt = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    @staticmethod
    def get_user_including_deleted(
        db: Session,
        user_id: uuid.UUID,
    ) -> User | None:
        """Retrieve a user regardless of soft-delete status (admin use)."""
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        stmt = select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    @staticmethod
    @cached(ttl=300, key_prefix="user")
    def get_by_username(db: Session, username: str) -> User | None:
        stmt = select(User).where(
            User.username == username,
            User.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    @staticmethod
    @cached(ttl=300, key_prefix="user")
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        stmt = select(User).where(User.deleted_at.is_(None)).offset(skip).limit(limit)
        return list(db.scalars(stmt))

    @staticmethod
    def create_user(
        db: Session,
        user: UserCreate,
        password_hash: str,
    ) -> User:

        db_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
            password_hash=password_hash,
        )

        db.add(db_user)
        db.flush()
        db.refresh(db_user)

        ActivityService.record_activity(
            db=db,
            actor_id=db_user.id,
            activity_type=ActivityType.USER_REGISTERED,
            title="Joined DevLink",
            description=f"{db_user.first_name} {db_user.last_name} joined DevLink.",
            icon="user-plus",
            color="success",
        )

        return db_user

    @staticmethod
    def update_user(
        db: Session,
        db_user: User,
        user: UserUpdate,
    ) -> User:

        data = user.model_dump(exclude_unset=True, mode="json")

        if "privacy_settings" in data:
            privacy_data = data.pop("privacy_settings")
            if privacy_data:
                current_settings = db_user.get_privacy_settings()
                current_settings.update(
                    {k: v for k, v in privacy_data.items() if v is not None}
                )
                db_user.privacy_settings = current_settings
        for key, value in data.items():
            setattr(db_user, key, value)
        db.flush()
        db.refresh(db_user)

        ActivityService.record_activity(
            db=db,
            actor_id=db_user.id,
            activity_type=ActivityType.PROFILE_UPDATED,
            title="Updated profile",
            description=f"{db_user.first_name} {db_user.last_name} updated their profile.",
            icon="user-round-pen",
            color="info",
        )

        return db_user

    @staticmethod
    def update_privacy_settings(
        db: Session,
        db_user: User,
        settings: dict | PrivacySettingsUpdate,
    ) -> User:
        current_settings = db_user.get_privacy_settings()
        if hasattr(settings, "model_dump"):
            update_data = settings.model_dump(exclude_unset=True)
        elif isinstance(settings, dict):
            update_data = settings
        else:
            update_data = {}
        for k, v in update_data.items():
            if v is not None:
                current_settings[k] = v.value if hasattr(v, "value") else str(v)
        db_user.privacy_settings = current_settings
        db.flush()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def apply_privacy_filters(
        db: Session,
        user: User,
        viewer: User | None = None,
    ) -> User:
        if not user:
            return user
        if viewer and (viewer.id == user.id or getattr(viewer, "is_superuser", False)):
            return user
        settings = user.get_privacy_settings()
        from app.services.follower_service import FollowerService

        is_follower = False
        if viewer:
            is_follower = FollowerService.is_following(
                db, follower_id=viewer.id, following_id=user.id
            )

        def is_visible(visibility_setting: str) -> bool:
            vis = str(visibility_setting).lower()
            if vis == "public":
                return True
            if vis == "authenticated" and viewer is not None:
                return True
            if vis == "followers" and (
                is_follower or (viewer and viewer.id == user.id)
            ):
                return True
            return False

        try:
            db.expunge(user)
        except Exception:
            pass
        if not is_visible(settings.get("email", "private")):
            user.public_email = None
        if not is_visible(settings.get("github", "public")):
            user.github_url = None
        if not is_visible(settings.get("resume", "public")):
            user.resume_url = None
        if not is_visible(settings.get("social_links", "public")):
            user.linkedin_url = None
            user.website = None
            user.portfolio_url = None
        if not is_visible(settings.get("availability", "public")):
            user.availability = []
        return user

    @staticmethod
    def soft_delete_user(
        db: Session,
        db_user: User,
        deleted_by_id: uuid.UUID,
    ) -> None:
        """Mark a user as deleted without removing the row."""
        db_user.deleted_at = func.now()
        db_user.deleted_by_id = deleted_by_id
        db.commit()

    @staticmethod
    def restore_user(
        db: Session,
        db_user: User,
    ) -> User:
        """Restore a soft-deleted user."""
        db_user.deleted_at = None
        db_user.deleted_by_id = None
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def hard_delete_user(
        db: Session,
        db_user: User,
    ) -> None:
        """Permanently remove a user from the database (admin only)."""
        db.delete(db_user)
        db.flush()

    @staticmethod
    def activate_user(
        db: Session,
        db_user: User,
    ) -> User:

        db_user.is_active = True

        db.flush()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def deactivate_user(
        db: Session,
        db_user: User,
    ) -> User:

        db_user.is_active = False

        db.flush()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def get_user_stats(
        db: Session,
        user_id: uuid.UUID,
    ) -> UserStats:
        projects = (
            db.scalar(
                select(func.count())
                .select_from(Project)
                .where(Project.owner_id == user_id)
            )
            or 0
        )

        followers = (
            db.scalar(
                select(func.count())
                .select_from(Follower)
                .where(Follower.following_id == user_id)
            )
            or 0
        )

        following = (
            db.scalar(
                select(func.count())
                .select_from(Follower)
                .where(Follower.follower_id == user_id)
            )
            or 0
        )

        applications = (
            db.scalar(
                select(func.count())
                .select_from(Application)
                .where(Application.applicant_id == user_id)
            )
            or 0
        )

        accepted = (
            db.scalar(
                select(func.count())
                .select_from(Application)
                .where(
                    Application.applicant_id == user_id,
                    Application.status == ApplicationStatus.ACCEPTED,
                )
            )
            or 0
        )

        stats = UserStats(
            projects=projects,
            followers=followers,
            following=following,
            applications=applications,
            accepted=accepted,
        )

        user = db.get(User, user_id)
        if user:
            UserService.update_user_badges(db, user, stats)
        return stats

    @staticmethod
    def update_user_badges(
        db: Session,
        user: User,
        stats: UserStats,
    ) -> None:
        new_badges = []
        if stats.accepted >= 5:
            new_badges.append("Top Contributor")
        elif stats.accepted >= 1:
            new_badges.append("Active Developer")
        if stats.projects >= 1:
            new_badges.append("Project Owner")
        if stats.followers >= 10:
            new_badges.append("Social Butterfly")
        if set(user.badges) != set(new_badges):
            user.badges = new_badges
            db.add(user)
            db.commit()

    @staticmethod
    def verify_email(
        db: Session,
        db_user: User,
    ) -> User:

        db_user.is_verified = True

        db.flush()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def get_profile_completion(
        db: Session,
        user: User,
    ) -> ProfileCompletionResponse:
        """
        Calculate profile completion percentage and list missing profile factors.

        Factors evaluated:
        - Avatar: profile_image
        - Bio: bio
        - Skills: UserSkill table entries count > 0
        - Experience: experience_level, role, or company
        - GitHub: github_url or github_id
        - Portfolio: portfolio_url or website
        - Location: location
        """
        from app.models.user_skill import UserSkill
        from app.schemas.user import ProfileCompletionResponse

        missing: list[str] = []

        # 1. Avatar

        if not (user.profile_image and user.profile_image.strip()):
            missing.append("Avatar")
        # 2. Bio

        if not (user.bio and user.bio.strip()):
            missing.append("Bio")
        # 3. Skills

        skills_count = (
            db.scalar(
                select(func.count())
                .select_from(UserSkill)
                .where(UserSkill.user_id == user.id)
            )
            or 0
        )
        if skills_count == 0:
            missing.append("Skills")
        # 4. Experience

        has_exp = bool(
            (user.experience_level and user.experience_level.strip())
            or (user.role and user.role.strip())
            or (user.company and user.company.strip())
        )
        if not has_exp:
            missing.append("Experience")
        # 5. GitHub

        has_github = bool(
            (user.github_url and str(user.github_url).strip())
            or (user.github_id and str(user.github_id).strip())
        )
        if not has_github:
            missing.append("GitHub")
        # 6. Portfolio

        has_portfolio = bool(
            (user.portfolio_url and str(user.portfolio_url).strip())
            or (user.website and str(user.website).strip())
        )
        if not has_portfolio:
            missing.append("Portfolio")
        # 7. Location

        if not (user.location and user.location.strip()):
            missing.append("Location")
        total_factors = 7
        completed_factors = total_factors - len(missing)
        completion_pct = round((completed_factors / total_factors) * 100)

        return ProfileCompletionResponse(
            completion=completion_pct,
            missing=missing,
        )

    def update_resume_url(
        db: Session,
        user: User,
        resume_url: str,
    ) -> User:
        user.resume_url = resume_url

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_profile_image(
        db: Session,
        user: User,
        profile_image_url: str,
    ) -> User:
        user.profile_image = profile_image_url

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def create_user_report(
        db: Session,
        reporter_id: uuid.UUID,
        reported_id: uuid.UUID,
        report: UserReportCreate,
    ) -> UserReport:
        db_report = UserReport(
            reporter_id=reporter_id,
            reported_id=reported_id,
            reason=report.reason,
            description=report.description,
            status="pending",
        )

        db.add(db_report)
        db.commit()
        db.refresh(db_report)

        return db_report
