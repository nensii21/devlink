from __future__ import annotations

"""
Business logic for project release notes (#1043).
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.activity import ActivityType
from app.models.project import Project
from app.models.project_member import MemberRole, ProjectMember
from app.models.project_release import ProjectRelease, ReleaseStatus
from app.models.user import User
from app.schemas.project_release import ReleaseCreate, ReleaseUpdate
from app.services.activity_service import ActivityService

logger = logging.getLogger(__name__)

MAINTAINER_ROLES = {
    MemberRole.OWNER,
    MemberRole.CO_OWNER,
    MemberRole.ADMIN,
    MemberRole.MAINTAINER,
}


class ProjectReleaseService:
    """Draft, publish, pin and list a project's changelog entries."""

    # ------------------------------------------------------------------
    # Lookups & authorization
    # ------------------------------------------------------------------

    @staticmethod
    def get_project_or_404(db: Session, project_id: uuid.UUID) -> Project:
        project = db.get(Project, project_id)
        if project is None or getattr(project, "deleted_at", None) is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return project

    @staticmethod
    def is_maintainer(db: Session, project: Project, user: User | None) -> bool:
        if user is None:
            return False
        if (
            getattr(user, "system_role", None) == "admin"
            or getattr(user, "role", None) == "admin"
        ):
            return True
        if project.owner_id == user.id:
            return True

        member = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user.id,
                ProjectMember.is_active.is_(True),
            )
        )
        return member is not None and member.role in MAINTAINER_ROLES

    @staticmethod
    def require_maintainer(db: Session, project: Project, user: User) -> None:
        if not ProjectReleaseService.is_maintainer(db, project, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners and maintainers can manage releases.",
            )

    @staticmethod
    def get_release_or_404(
        db: Session,
        project_id: uuid.UUID,
        release_id: uuid.UUID,
        viewer_is_maintainer: bool = False,
    ) -> ProjectRelease:
        release = db.scalar(
            select(ProjectRelease)
            .where(
                ProjectRelease.id == release_id, ProjectRelease.project_id == project_id
            )
            .options(selectinload(ProjectRelease.author))
        )
        if release is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Release not found",
            )

        # A draft is a 404, not a 403, for anyone who cannot see it. A 403
        # confirms the release exists, which leaks the fact that something
        # unannounced is in the pipeline -- and its id.
        if release.status == ReleaseStatus.DRAFT and not viewer_is_maintainer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Release not found",
            )
        return release

    # ------------------------------------------------------------------
    # Version uniqueness
    # ------------------------------------------------------------------

    @staticmethod
    def assert_version_available(
        db: Session,
        project_id: uuid.UUID,
        version: str,
        exclude_release_id: uuid.UUID | None = None,
    ) -> None:
        """
        Versions are unique per project, compared case-insensitively.

        ``V1.0.0`` and ``v1.0.0`` are the same release to every human reading
        the changelog, so treating them as distinct rows would produce a
        changelog with two entries nobody can tell apart.
        """
        stmt = select(ProjectRelease.id).where(
            ProjectRelease.project_id == project_id,
            func.lower(ProjectRelease.version) == version.strip().lower(),
        )
        if exclude_release_id is not None:
            stmt = stmt.where(ProjectRelease.id != exclude_release_id)

        if db.scalar(stmt) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Version '{version}' already exists for this project.",
            )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def create_release(
        db: Session,
        project_id: uuid.UUID,
        payload: ReleaseCreate,
        actor: User,
    ) -> ProjectRelease:
        project = ProjectReleaseService.get_project_or_404(db, project_id)
        ProjectReleaseService.require_maintainer(db, project, actor)
        ProjectReleaseService.assert_version_available(db, project_id, payload.version)

        now = datetime.now(timezone.utc)
        publishing = payload.status == ReleaseStatus.PUBLISHED

        release = ProjectRelease(
            id=uuid.uuid4(),
            project_id=project_id,
            author_id=actor.id,
            version=payload.version,
            title=payload.title,
            body=payload.body,
            highlights=payload.highlights,
            release_type=payload.release_type,
            status=payload.status,
            published_at=now if publishing else None,
            is_pinned=False,
            created_at=now,
            updated_at=now,
        )
        db.add(release)
        db.flush()

        if publishing:
            ProjectReleaseService._record_publish_activity(db, project, release, actor)

        db.commit()
        db.refresh(release)
        return release

    @staticmethod
    def update_release(
        db: Session,
        project_id: uuid.UUID,
        release_id: uuid.UUID,
        payload: ReleaseUpdate,
        actor: User,
    ) -> ProjectRelease:
        project = ProjectReleaseService.get_project_or_404(db, project_id)
        ProjectReleaseService.require_maintainer(db, project, actor)
        release = ProjectReleaseService.get_release_or_404(
            db, project_id, release_id, viewer_is_maintainer=True
        )

        data = payload.model_dump(exclude_unset=True)

        if "version" in data:
            ProjectReleaseService.assert_version_available(
                db, project_id, data["version"], exclude_release_id=release.id
            )

        for field, value in data.items():
            setattr(release, field, value)
        release.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(release)
        return release

    @staticmethod
    def delete_release(
        db: Session, project_id: uuid.UUID, release_id: uuid.UUID, actor: User
    ) -> None:
        project = ProjectReleaseService.get_project_or_404(db, project_id)
        ProjectReleaseService.require_maintainer(db, project, actor)
        release = ProjectReleaseService.get_release_or_404(
            db, project_id, release_id, viewer_is_maintainer=True
        )

        db.delete(release)
        db.commit()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @staticmethod
    def publish(
        db: Session,
        project_id: uuid.UUID,
        release_id: uuid.UUID,
        actor: User,
    ) -> ProjectRelease:
        """
        Publish a draft. Idempotent: re-publishing an already-published release
        is a no-op rather than moving ``published_at``, so a double-clicked
        button cannot rewrite the release date or fire a second announcement.
        """
        project = ProjectReleaseService.get_project_or_404(db, project_id)
        ProjectReleaseService.require_maintainer(db, project, actor)
        release = ProjectReleaseService.get_release_or_404(
            db, project_id, release_id, viewer_is_maintainer=True
        )

        if release.status == ReleaseStatus.PUBLISHED:
            return release

        now = datetime.now(timezone.utc)
        release.status = ReleaseStatus.PUBLISHED
        release.published_at = now
        release.updated_at = now
        db.flush()

        ProjectReleaseService._record_publish_activity(db, project, release, actor)

        db.commit()
        db.refresh(release)
        return release

    @staticmethod
    def pin(
        db: Session,
        project_id: uuid.UUID,
        release_id: uuid.UUID,
        actor: User,
    ) -> ProjectRelease:
        """Pin one release, un-pinning whichever was pinned before."""
        project = ProjectReleaseService.get_project_or_404(db, project_id)
        ProjectReleaseService.require_maintainer(db, project, actor)
        release = ProjectReleaseService.get_release_or_404(
            db, project_id, release_id, viewer_is_maintainer=True
        )

        if release.status != ReleaseStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only a published release can be pinned.",
            )

        currently_pinned = db.scalars(
            select(ProjectRelease).where(
                ProjectRelease.project_id == project_id,
                ProjectRelease.is_pinned.is_(True),
                ProjectRelease.id != release.id,
            )
        ).all()
        for other in currently_pinned:
            other.is_pinned = False

        release.is_pinned = True
        release.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(release)
        return release

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    @staticmethod
    def list_releases(
        db: Session,
        project_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        include_drafts: bool = False,
    ) -> tuple[list[ProjectRelease], int]:
        conditions = [ProjectRelease.project_id == project_id]
        if not include_drafts:
            conditions.append(ProjectRelease.status == ReleaseStatus.PUBLISHED)

        total = int(
            db.scalar(select(func.count(ProjectRelease.id)).where(*conditions)) or 0
        )

        stmt = (
            select(ProjectRelease)
            .where(*conditions)
            .options(selectinload(ProjectRelease.author))
            # Pinned first, then newest published. created_at is the tiebreak
            # so drafts (no published_at) still order deterministically.
            .order_by(
                ProjectRelease.is_pinned.desc(),
                ProjectRelease.published_at.desc().nullslast(),
                ProjectRelease.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(stmt).all()), total

    @staticmethod
    def get_latest(db: Session, project_id: uuid.UUID) -> ProjectRelease:
        release = db.scalar(
            select(ProjectRelease)
            .where(
                ProjectRelease.project_id == project_id,
                ProjectRelease.status == ReleaseStatus.PUBLISHED,
            )
            .options(selectinload(ProjectRelease.author))
            .order_by(
                ProjectRelease.published_at.desc(), ProjectRelease.created_at.desc()
            )
            .limit(1)
        )
        if release is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This project has no published releases yet.",
            )
        return release

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _record_publish_activity(
        db: Session,
        project: Project,
        release: ProjectRelease,
        actor: User,
    ) -> None:
        """
        Announce on publish, never on create. A draft is by definition not news
        yet, and pushing every work-in-progress into followers' feeds would
        make the feed useless.
        """
        try:
            ActivityService.record_activity(
                db,
                actor_id=actor.id,
                activity_type=ActivityType.PROJECT_ANNOUNCEMENT,
                title=f"{project.title} {release.version} released",
                description=release.title,
                target_id=release.id,
                target_type="project_release",
                metadata={
                    "project_id": str(project.id),
                    "release_id": str(release.id),
                    "version": release.version,
                    "release_type": release.release_type.value,
                },
                icon="rocket",
            )
        except Exception:  # pragma: no cover - feed failure must not lose the release
            # The release is the user's work; the feed entry is a side effect.
            # Losing the announcement is annoying, losing the release is not
            # acceptable, so this never propagates.
            logger.exception(
                "Failed to record release activity for release %s", release.id
            )


__all__ = ["ProjectReleaseService"]
