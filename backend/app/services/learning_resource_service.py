import math
import uuid
from typing import Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.learning_resource import LearningResource, ResourceVote
from app.models.user import User
from app.schemas.learning_resource import (
    LearningResourceCreate,
    LearningResourceUpdate,
    VoteRequest,
)


class LearningResourceService:

    @staticmethod
    def create(
        db: Session,
        project_id: uuid.UUID,
        author_id: uuid.UUID,
        payload: LearningResourceCreate,
    ) -> LearningResource:
        resource = LearningResource(
            project_id=project_id,
            author_id=author_id,
            title=payload.title,
            url=payload.url,
            description=payload.description,
            category=payload.category,
            language=payload.language,
            difficulty=payload.difficulty,
            is_external=payload.is_external,
        )
        db.add(resource)
        db.commit()
        db.refresh(resource)
        return resource

    @staticmethod
    def get(db: Session, resource_id: str) -> Optional[LearningResource]:
        return db.query(LearningResource).filter(LearningResource.id == resource_id).first()

    @staticmethod
    def get_with_author(
        db: Session, resource_id: str
    ) -> Optional[dict]:
        resource = db.query(LearningResource).filter(LearningResource.id == resource_id).first()
        if not resource:
            return None
        author = db.query(User).filter(User.id == resource.author_id).first()
        return {
            "resource": resource,
            "author_name": author.display_name if author else None,
        }

    @staticmethod
    def list_resources(
        db: Session,
        project_id: uuid.UUID,
        *,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        language: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        query = db.query(LearningResource).filter(
            LearningResource.project_id == project_id
        )

        if category:
            query = query.filter(LearningResource.category == category)
        if difficulty:
            query = query.filter(LearningResource.difficulty == difficulty)
        if language:
            query = query.filter(LearningResource.language.ilike(f"%{language}%"))
        if search:
            query = query.filter(
                or_(
                    LearningResource.title.ilike(f"%{search}%"),
                    LearningResource.description.ilike(f"%{search}%"),
                )
            )

        total = query.count()

        if sort_by == "votes":
            query = query.order_by(
                LearningResource.is_pinned.desc(),
                LearningResource.vote_score.desc(),
            )
        elif sort_by == "popular":
            query = query.order_by(
                LearningResource.is_pinned.desc(),
                LearningResource.view_count.desc(),
            )
        else:  # newest
            query = query.order_by(
                LearningResource.is_pinned.desc(),
                LearningResource.created_at.desc(),
            )

        resources = query.offset((page - 1) * limit).limit(limit).all()

        author_ids = {r.author_id for r in resources}
        authors = {}
        if author_ids:
            user_rows = db.query(User).filter(User.id.in_(author_ids)).all()
            authors = {u.id: u.display_name for u in user_rows}

        result = []
        for r in resources:
            result.append({
                "id": r.id,
                "project_id": r.project_id,
                "author_id": r.author_id,
                "author_name": authors.get(r.author_id),
                "title": r.title,
                "url": r.url,
                "description": r.description,
                "category": r.category,
                "language": r.language,
                "difficulty": r.difficulty,
                "is_external": r.is_external,
                "is_pinned": r.is_pinned,
                "view_count": r.view_count,
                "vote_score": r.vote_score,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            })

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": max(1, math.ceil(total / limit)),
        }

    @staticmethod
    def update(
        db: Session,
        resource_id: str,
        author_id: uuid.UUID,
        payload: LearningResourceUpdate,
    ) -> Optional[LearningResource]:
        resource = db.query(LearningResource).filter(
            LearningResource.id == resource_id,
            LearningResource.author_id == author_id,
        ).first()
        if not resource:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(resource, field, value)
        db.commit()
        db.refresh(resource)
        return resource

    @staticmethod
    def delete(db: Session, resource_id: str, author_id: uuid.UUID) -> bool:
        resource = db.query(LearningResource).filter(
            LearningResource.id == resource_id,
            LearningResource.author_id == author_id,
        ).first()
        if not resource:
            return False
        db.delete(resource)
        db.commit()
        return True

    @staticmethod
    def increment_view(db: Session, resource_id: str) -> None:
        resource = db.query(LearningResource).filter(
            LearningResource.id == resource_id
        ).first()
        if resource:
            resource.view_count += 1
            db.commit()

    @staticmethod
    def vote(
        db: Session, resource_id: str, user_id: uuid.UUID, payload: VoteRequest
    ) -> Optional[dict]:
        resource = db.query(LearningResource).filter(
            LearningResource.id == resource_id
        ).first()
        if not resource:
            return None

        existing = db.query(ResourceVote).filter(
            ResourceVote.resource_id == resource_id,
            ResourceVote.user_id == user_id,
        ).first()

        if existing:
            if existing.value == payload.value:
                resource.vote_score -= payload.value
                db.delete(existing)
            else:
                resource.vote_score -= existing.value
                existing.value = payload.value
                resource.vote_score += payload.value
        else:
            new_vote = ResourceVote(
                resource_id=resource_id, user_id=user_id, value=payload.value
            )
            db.add(new_vote)
            resource.vote_score += payload.value

        db.commit()
        db.refresh(resource)
        return {
            "resource_id": resource_id,
            "vote_score": resource.vote_score,
            "user_vote": payload.value if not existing or existing.value != payload.value else 0,
        }

    @staticmethod
    def toggle_pin(db: Session, resource_id: str, author_id: uuid.UUID) -> Optional[LearningResource]:
        resource = db.query(LearningResource).filter(
            LearningResource.id == resource_id,
            LearningResource.author_id == author_id,
        ).first()
        if not resource:
            return None
        resource.is_pinned = not resource.is_pinned
        db.commit()
        db.refresh(resource)
        return resource

    @staticmethod
    def get_stats(db: Session, project_id: uuid.UUID) -> dict:
        resources = db.query(LearningResource).filter(
            LearningResource.project_id == project_id
        ).all()

        if not resources:
            return {
                "project_id": project_id,
                "total_resources": 0,
                "by_category": {},
                "by_difficulty": {},
                "total_votes": 0,
                "top_resources": [],
            }

        by_category = {}
        by_difficulty = {}
        total_votes = 0
        for r in resources:
            by_category[r.category] = by_category.get(r.category, 0) + 1
            by_difficulty[r.difficulty] = by_difficulty.get(r.difficulty, 0) + 1
            total_votes += abs(r.vote_score)

        top = sorted(resources, key=lambda x: x.vote_score, reverse=True)[:5]
        top_resources = [
            {
                "id": r.id,
                "title": r.title,
                "url": r.url,
                "category": r.category,
                "difficulty": r.difficulty,
                "vote_score": r.vote_score,
                "is_pinned": r.is_pinned,
                "created_at": r.created_at,
            }
            for r in top
        ]

        return {
            "project_id": project_id,
            "total_resources": len(resources),
            "by_category": by_category,
            "by_difficulty": by_difficulty,
            "total_votes": total_votes,
            "top_resources": top_resources,
        }
