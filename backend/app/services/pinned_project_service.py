from __future__ import annotations

"""
Business logic for pinned profile projects (#1042).
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.pinned_project import MAX_PINNED_PROJECTS, PinnedProject
from app.models.project import Project, ProjectVisibility
from app.models.project_member import ProjectMember
from app.models.user import User

logger = logging.getLogger(__name__)


class PinnedProjectService:
    """Pin, unpin and reorder the projects featured on a profile."""

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    @staticmethod
    def get_user_or_404(db: Session, username: str) -> User:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    @staticmethod
    def get_project_or_404(db: Session, project_id: uuid.UUID) -> Project:
        project = db.get(Project, project_id)
        if project is None or getattr(project, "deleted_at", None) is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return project

    # ------------------------------------------------------------------
    # Eligibility
    # ------------------------------------------------------------------

    @staticmethod
    def is_associated(db: Session, project: Project, user: User) -> bool:
        """Owner or active member. You cannot pin a project you had no part in."""
        if project.owner_id == user.id:
            return True
        member = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user.id,
                ProjectMember.is_active.is_(True),
            )
        )
        return member is not None

    @staticmethod
    def require_pinnable(db: Session, project: Project, user: User) -> None:
        """
        A pin is a public shop-window. The rules follow from that: the visitor
        who clicks one has to be able to open it, and the person pinning has to
        have actually been involved.
        """
        if not PinnedProjectService.is_associated(db, project, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only pin projects you own or are a member of.",
            )

        if getattr(project, "is_archived", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archived projects cannot be pinned.",
            )

        # A private project pinned by its owner is a dead link for everyone
        # else, so it does not belong in a shop-window at all.
        if project.visibility == ProjectVisibility.PRIVATE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Private projects cannot be pinned to a public profile.",
            )

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    @staticmethod
    def list_pins(db: Session, user_id: uuid.UUID) -> list[PinnedProject]:
        stmt = (
            select(PinnedProject)
            .where(PinnedProject.user_id == user_id)
            .options(selectinload(PinnedProject.project))
            .order_by(PinnedProject.position.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_pins(db: Session, user_id: uuid.UUID) -> int:
        return int(
            db.scalar(
                select(func.count(PinnedProject.id)).where(
                    PinnedProject.user_id == user_id
                )
            )
            or 0
        )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    @staticmethod
    def pin(db: Session, user: User, project_id: uuid.UUID) -> PinnedProject:
        project = PinnedProjectService.get_project_or_404(db, project_id)
        PinnedProjectService.require_pinnable(db, project, user)

        existing = db.scalar(
            select(PinnedProject).where(
                PinnedProject.user_id == user.id,
                PinnedProject.project_id == project_id,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This project is already pinned.",
            )

        current = PinnedProjectService.count_pins(db, user.id)
        if current >= MAX_PINNED_PROJECTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You can pin at most {MAX_PINNED_PROJECTS} projects. Unpin one first.",
            )

        pin = PinnedProject(
            id=uuid.uuid4(),
            user_id=user.id,
            project_id=project_id,
            position=current,
            created_at=datetime.now(timezone.utc),
        )
        db.add(pin)
        db.commit()
        db.refresh(pin)
        return pin

    @staticmethod
    def unpin(db: Session, user: User, project_id: uuid.UUID) -> None:
        pin = db.scalar(
            select(PinnedProject).where(
                PinnedProject.user_id == user.id,
                PinnedProject.project_id == project_id,
            )
        )
        if pin is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This project is not pinned.",
            )

        db.delete(pin)
        db.flush()
        # Close the gap so positions stay 0..n-1. A sparse sequence would leak
        # out through the API and force every client to renumber for itself.
        PinnedProjectService._compact_positions(db, user.id)
        db.commit()

    @staticmethod
    def replace(
        db: Session, user: User, project_ids: list[uuid.UUID]
    ) -> list[PinnedProject]:
        """
        Replace the entire pinned set in the given order.

        This is what a drag-and-drop UI wants: one call, one final state, no
        intermediate ordering the client has to reconstruct if a request fails.
        """
        if len(project_ids) > MAX_PINNED_PROJECTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You can pin at most {MAX_PINNED_PROJECTS} projects.",
            )

        seen: set[uuid.UUID] = set()
        for project_id in project_ids:
            if project_id in seen:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The same project appears more than once.",
                )
            seen.add(project_id)

        # Validate the whole batch before touching a single row. A partial
        # write here would leave the profile in a state the user never asked
        # for and cannot see to correct.
        for project_id in project_ids:
            project = PinnedProjectService.get_project_or_404(db, project_id)
            PinnedProjectService.require_pinnable(db, project, user)

        for pin in PinnedProjectService.list_pins(db, user.id):
            db.delete(pin)
        db.flush()

        now = datetime.now(timezone.utc)
        for position, project_id in enumerate(project_ids):
            db.add(
                PinnedProject(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    project_id=project_id,
                    position=position,
                    created_at=now,
                )
            )

        db.commit()
        return PinnedProjectService.list_pins(db, user.id)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _compact_positions(db: Session, user_id: uuid.UUID) -> None:
        pins = list(
            db.scalars(
                select(PinnedProject)
                .where(PinnedProject.user_id == user_id)
                .order_by(PinnedProject.position.asc(), PinnedProject.created_at.asc())
            ).all()
        )
        for index, pin in enumerate(pins):
            if pin.position != index:
                pin.position = index
        db.flush()


__all__ = ["PinnedProjectService", "MAX_PINNED_PROJECTS"]
