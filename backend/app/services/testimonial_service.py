from __future__ import annotations

"""
Business logic for peer testimonials (#1044).

The rules in here *are* the feature. A testimonial system where the subject can
quietly rewrite what was said about them, or approve their own praise, is worth
less than no testimonials at all -- it looks like social proof while carrying
none.
"""

import logging
import uuid
from collections import Counter
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.project import Project
from app.models.testimonial import (
    MAX_FEATURED,
    Testimonial,
    TestimonialRelationship,
    TestimonialStatus,
)
from app.models.user import User
from app.schemas.testimonial import (
    RelationshipCount,
    TestimonialCreate,
    TestimonialSummary,
    TestimonialUpdate,
)
from app.services.block_service import BlockService

logger = logging.getLogger(__name__)


class TestimonialService:
    """Write, moderate and read peer testimonials."""

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    @staticmethod
    def get_user_or_404(db: Session, username: str) -> User:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    @staticmethod
    def get_subject_or_404(db: Session, subject_id: uuid.UUID) -> User:
        user = db.get(User, subject_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    @staticmethod
    def get_testimonial_or_404(db: Session, testimonial_id: uuid.UUID) -> Testimonial:
        testimonial = db.scalar(
            select(Testimonial)
            .where(Testimonial.id == testimonial_id)
            .options(
                selectinload(Testimonial.author), selectinload(Testimonial.subject)
            )
        )
        if testimonial is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Testimonial not found"
            )
        return testimonial

    # ------------------------------------------------------------------
    # Guards
    # ------------------------------------------------------------------

    @staticmethod
    def require_writable(db: Session, author: User, subject_id: uuid.UUID) -> None:
        if author.id == subject_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot write a testimonial about yourself.",
            )

        # is_blocked is bidirectional. Either direction is a hard no: a block
        # means these two have opted out of each other, and a testimonial is a
        # channel from one to the other's profile.
        if BlockService.is_blocked(db, author.id, subject_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot write a testimonial for this user.",
            )

    @staticmethod
    def require_author(testimonial: Testimonial, user: User) -> None:
        if testimonial.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can edit this testimonial.",
            )

    @staticmethod
    def require_subject(testimonial: Testimonial, user: User) -> None:
        """
        Moderation belongs to the subject alone. If the author could approve
        their own testimonial, approval would mean nothing.
        """
        if testimonial.subject_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the person a testimonial is about can moderate it.",
            )

    @staticmethod
    def can_view(testimonial: Testimonial, viewer: User | None) -> bool:
        if testimonial.status == TestimonialStatus.APPROVED:
            return True
        if viewer is None:
            return False
        return viewer.id in (testimonial.author_id, testimonial.subject_id)

    @staticmethod
    def validate_project(db: Session, project_id: uuid.UUID | None) -> None:
        if project_id is None:
            return
        if db.scalar(select(Project.id).where(Project.id == project_id)) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    @staticmethod
    def create(db: Session, author: User, payload: TestimonialCreate) -> Testimonial:
        TestimonialService.get_subject_or_404(db, payload.subject_id)
        TestimonialService.require_writable(db, author, payload.subject_id)
        TestimonialService.validate_project(db, payload.project_id)

        existing = db.scalar(
            select(Testimonial).where(
                Testimonial.author_id == author.id,
                Testimonial.subject_id == payload.subject_id,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already written a testimonial for this user. Edit it instead.",
            )

        now = datetime.now(timezone.utc)
        testimonial = Testimonial(
            id=uuid.uuid4(),
            subject_id=payload.subject_id,
            author_id=author.id,
            project_id=payload.project_id,
            relationship_type=payload.relationship,
            body=payload.body,
            status=TestimonialStatus.PENDING,
            is_featured=False,
            created_at=now,
            updated_at=now,
        )
        db.add(testimonial)
        db.commit()
        db.refresh(testimonial)
        return testimonial

    @staticmethod
    def update(
        db: Session,
        testimonial_id: uuid.UUID,
        author: User,
        payload: TestimonialUpdate,
    ) -> Testimonial:
        """
        Edit an existing testimonial.

        Editing an approved testimonial sends it back to ``pending`` and clears
        the feature flag. Without that, approval would be a rubber stamp on
        text the author can swap out afterwards -- get something bland
        approved, then rewrite it into anything at all.
        """
        testimonial = TestimonialService.get_testimonial_or_404(db, testimonial_id)
        TestimonialService.require_author(testimonial, author)

        if testimonial.status == TestimonialStatus.HIDDEN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This testimonial has been hidden and can no longer be edited.",
            )

        data = payload.model_dump(exclude_unset=True)
        if "project_id" in data:
            TestimonialService.validate_project(db, data["project_id"])

        content_changed = "body" in data or "relationship" in data

        if "relationship" in data:
            testimonial.relationship_type = data.pop("relationship")
        for field, value in data.items():
            setattr(testimonial, field, value)

        if content_changed and testimonial.status == TestimonialStatus.APPROVED:
            testimonial.status = TestimonialStatus.PENDING
            testimonial.is_featured = False
            testimonial.responded_at = None

        testimonial.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(testimonial)
        return testimonial

    @staticmethod
    def delete(db: Session, testimonial_id: uuid.UUID, user: User) -> None:
        """
        Only the author may delete. The subject can hide a testimonial but not
        erase it -- someone else's opinion is not theirs to destroy, and a
        subject who could delete would be curating rather than receiving.
        """
        testimonial = TestimonialService.get_testimonial_or_404(db, testimonial_id)
        TestimonialService.require_author(testimonial, user)

        db.delete(testimonial)
        db.commit()

    # ------------------------------------------------------------------
    # Moderation
    # ------------------------------------------------------------------

    @staticmethod
    def approve(db: Session, testimonial_id: uuid.UUID, subject: User) -> Testimonial:
        testimonial = TestimonialService.get_testimonial_or_404(db, testimonial_id)
        TestimonialService.require_subject(testimonial, subject)

        now = datetime.now(timezone.utc)
        testimonial.status = TestimonialStatus.APPROVED
        testimonial.responded_at = now
        testimonial.updated_at = now

        db.commit()
        db.refresh(testimonial)
        return testimonial

    @staticmethod
    def hide(db: Session, testimonial_id: uuid.UUID, subject: User) -> Testimonial:
        testimonial = TestimonialService.get_testimonial_or_404(db, testimonial_id)
        TestimonialService.require_subject(testimonial, subject)

        now = datetime.now(timezone.utc)
        testimonial.status = TestimonialStatus.HIDDEN
        # A hidden testimonial cannot stay featured, or hiding would only
        # remove it from the list while leaving it at the top of the profile.
        testimonial.is_featured = False
        testimonial.responded_at = now
        testimonial.updated_at = now

        db.commit()
        db.refresh(testimonial)
        return testimonial

    @staticmethod
    def set_featured(
        db: Session,
        testimonial_id: uuid.UUID,
        subject: User,
        featured: bool = True,
    ) -> Testimonial:
        testimonial = TestimonialService.get_testimonial_or_404(db, testimonial_id)
        TestimonialService.require_subject(testimonial, subject)

        if featured:
            if testimonial.status != TestimonialStatus.APPROVED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only an approved testimonial can be featured.",
                )

            already = int(
                db.scalar(
                    select(func.count(Testimonial.id)).where(
                        Testimonial.subject_id == subject.id,
                        Testimonial.is_featured.is_(True),
                        Testimonial.id != testimonial.id,
                    )
                )
                or 0
            )
            if already >= MAX_FEATURED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"You can feature at most {MAX_FEATURED} testimonials.",
                )

        testimonial.is_featured = featured
        testimonial.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(testimonial)
        return testimonial

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    @staticmethod
    def list_for_subject(
        db: Session,
        subject: User,
        viewer: User | None,
        status_filter: TestimonialStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Testimonial], int]:
        is_subject = viewer is not None and viewer.id == subject.id

        conditions = [Testimonial.subject_id == subject.id]
        if is_subject:
            # The subject may filter across their whole inbox; with no filter
            # they see everything, which is what a moderation queue needs.
            if status_filter is not None:
                conditions.append(Testimonial.status == status_filter)
        else:
            # Everyone else sees approved only, whatever they ask for.
            conditions.append(Testimonial.status == TestimonialStatus.APPROVED)

        total = int(
            db.scalar(select(func.count(Testimonial.id)).where(*conditions)) or 0
        )

        stmt = (
            select(Testimonial)
            .where(*conditions)
            .options(
                selectinload(Testimonial.author), selectinload(Testimonial.subject)
            )
            # Featured first, then newest.
            .order_by(Testimonial.is_featured.desc(), Testimonial.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(stmt).all()), total

    @staticmethod
    def list_written_by(
        db: Session,
        author: User,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Testimonial], int]:
        conditions = [Testimonial.author_id == author.id]
        total = int(
            db.scalar(select(func.count(Testimonial.id)).where(*conditions)) or 0
        )

        stmt = (
            select(Testimonial)
            .where(*conditions)
            .options(selectinload(Testimonial.subject))
            .order_by(Testimonial.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(stmt).all()), total

    @staticmethod
    def summarise(db: Session, subject: User) -> TestimonialSummary:
        approved = list(
            db.scalars(
                select(Testimonial)
                .where(
                    Testimonial.subject_id == subject.id,
                    Testimonial.status == TestimonialStatus.APPROVED,
                )
                .options(selectinload(Testimonial.author))
                .order_by(Testimonial.is_featured.desc(), Testimonial.created_at.desc())
            ).all()
        )

        counter: Counter[TestimonialRelationship] = Counter(
            item.relationship_type for item in approved
        )

        return TestimonialSummary(
            user_id=subject.id,
            username=subject.username,
            total_approved=len(approved),
            featured=[item for item in approved if item.is_featured][:MAX_FEATURED],
            by_relationship=[
                RelationshipCount(relationship=relationship, count=count)
                for relationship, count in sorted(
                    counter.items(), key=lambda pair: (-pair[1], pair[0].value)
                )
            ],
            max_featured=MAX_FEATURED,
        )


__all__ = ["TestimonialService", "MAX_FEATURED"]
