"""Business logic for project discussions (#930)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.project import Project, ProjectVisibility
from app.models.project_comment import ProjectComment
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project_comment import (
    ProjectCommentCreate,
    ProjectCommentUpdate,
)

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


def _utcnow() -> datetime:
    """Timezone-aware UTC.

    The timestamp columns here are `DateTime(timezone=True)`, so a naive value
    would either fail to compare or be silently reinterpreted in the session
    time zone.
    """
    return datetime.now(timezone.utc)


class ProjectCommentService:
    # ------------------------------------------------------------------
    # Lookups and permissions
    # ------------------------------------------------------------------

    @staticmethod
    def get_project_or_404(db: Session, project_id: uuid.UUID) -> Project:
        project = db.get(Project, project_id)

        if project is None or project.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        return project

    @staticmethod
    def is_project_member(db: Session, project: Project, user_id: uuid.UUID) -> bool:
        if project.owner_id == user_id:
            return True

        member = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user_id,
                ProjectMember.is_active.is_(True),
            )
        )

        return member is not None

    @staticmethod
    def can_view_project(db: Session, project: Project, user: User | None) -> bool:
        """Comment visibility follows the project's own visibility.

        A public project's discussion is public, including to signed-out
        visitors -- that is the point of having it in the open. A private
        project's discussion is limited to people who can already see the
        project.
        """
        if project.visibility == ProjectVisibility.PUBLIC:
            return True

        if user is None:
            return False

        if getattr(user, "system_role", None) == "admin":
            return True

        return ProjectCommentService.is_project_member(db, project, user.id)

    @staticmethod
    def require_can_view(db: Session, project: Project, user: User | None) -> None:
        if not ProjectCommentService.can_view_project(db, project, user):
            # 404 rather than 403: telling an outsider that a private project
            # exists is itself a disclosure.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

    @staticmethod
    def get_comment_or_404(
        db: Session,
        project_id: uuid.UUID,
        comment_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> ProjectComment:
        comment = db.get(ProjectComment, comment_id)

        # The project_id check keeps a comment id from one project being used
        # to reach into another.
        if comment is None or comment.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found",
            )

        if comment.deleted_at is not None and not include_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found",
            )

        return comment

    @staticmethod
    def require_can_edit(comment: ProjectComment, user: User) -> None:
        """Only the author may edit. Not the project owner, not an admin.

        Editing someone else's words under their name is a different thing
        from removing them, so the delete path below is more permissive than
        this one deliberately.
        """
        if comment.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own comments.",
            )

    @staticmethod
    def require_can_delete(
        db: Session, project: Project, comment: ProjectComment, user: User
    ) -> None:
        """The author, the project owner, or an admin -- moderation needs it."""
        if comment.author_id == user.id:
            return

        if project.owner_id == user.id:
            return

        if getattr(user, "system_role", None) == "admin":
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only delete your own comments, or comments on a "
                "project you own."
            ),
        )

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    @staticmethod
    def list_thread(
        db: Session,
        project_id: uuid.UUID,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> tuple[list[ProjectComment], int]:
        """Return one page of top-level comments plus the total.

        Replies are eager-loaded via `selectinload`, which costs one extra
        query for the whole page rather than one per comment.
        """
        limit = max(1, min(limit, MAX_PAGE_SIZE))
        offset = max(0, offset)

        base = select(ProjectComment).where(
            ProjectComment.project_id == project_id,
            ProjectComment.parent_id.is_(None),
        )

        total = db.scalar(select(func.count()).select_from(base.subquery()))

        comments = list(
            db.scalars(
                base.options(
                    selectinload(ProjectComment.author),
                    selectinload(ProjectComment.replies).selectinload(
                        ProjectComment.author
                    ),
                )
                .order_by(ProjectComment.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )

        return comments, int(total or 0)

    @staticmethod
    def visible_replies(comment: ProjectComment) -> list[ProjectComment]:
        """Replies, oldest first, with deleted ones dropped.

        A deleted *top-level* comment is tombstoned and stays in the listing so
        its replies keep their context. A deleted *reply* has nothing hanging
        off it, so it just disappears.
        """
        return [
            reply
            for reply in sorted(comment.replies, key=lambda r: r.created_at)
            if reply.deleted_at is None
        ]

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    @staticmethod
    def create_comment(
        db: Session,
        project: Project,
        payload: ProjectCommentCreate,
        author: User,
    ) -> ProjectComment:
        parent_id = payload.parent_id

        if parent_id is not None:
            parent = ProjectCommentService.get_comment_or_404(db, project.id, parent_id)

            # One level only. Replying to a reply attaches to that reply's
            # parent instead of erroring, which is what the user meant and
            # keeps the thread flat.
            if parent.parent_id is not None:
                parent_id = parent.parent_id

        comment = ProjectComment(
            project_id=project.id,
            author_id=author.id,
            parent_id=parent_id,
            body=payload.body,
        )

        db.add(comment)
        db.flush()
        db.refresh(comment)

        return comment

    @staticmethod
    def update_comment(
        db: Session,
        comment: ProjectComment,
        payload: ProjectCommentUpdate,
    ) -> ProjectComment:
        # Editing to the same text should not light up the "edited" marker.
        if payload.body != comment.body:
            comment.body = payload.body
            comment.is_edited = True
            comment.edited_at = _utcnow()

            db.flush()
            db.refresh(comment)

        return comment

    @staticmethod
    def delete_comment(
        db: Session,
        comment: ProjectComment,
        actor: User,
    ) -> ProjectComment:
        """Soft delete, so replies underneath keep their parent."""
        if comment.deleted_at is None:
            comment.deleted_at = _utcnow()
            comment.deleted_by_id = actor.id

            db.flush()
            db.refresh(comment)

        return comment

    # ------------------------------------------------------------------
    # Counts
    # ------------------------------------------------------------------

    @staticmethod
    def count_comments(db: Session, project_id: uuid.UUID) -> int:
        """Every live comment on the project, replies included.

        This is the number a "12 comments" badge on a project card wants,
        which is why it counts differently from the `total` in a listing page.
        """
        return int(
            db.scalar(
                select(func.count())
                .select_from(ProjectComment)
                .where(
                    ProjectComment.project_id == project_id,
                    ProjectComment.deleted_at.is_(None),
                )
            )
            or 0
        )
