import uuid
from typing import List
from sqlalchemy.orm import Session

from app.models.badge import Badge, UserBadge
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.follower import Follower
from app.models.feedback import UserFeedback
from app.schemas.badge import BadgeResponse, BadgeEvaluationResponse

DEFAULT_BADGES = [
    {
        "slug": "first-project",
        "name": "First Project",
        "description": "Created your first project on DevLink",
        "icon": "rocket",
        "category": "milestone",
        "points": 20,
    },
    {
        "slug": "first-collaboration",
        "name": "First Collaboration",
        "description": "Joined your first project team",
        "icon": "users",
        "category": "collaboration",
        "points": 20,
    },
    {
        "slug": "top-contributor",
        "name": "Top Contributor",
        "description": "Contributed to 5 or more projects on the platform",
        "icon": "award",
        "category": "achievement",
        "points": 50,
    },
    {
        "slug": "ai-builder",
        "name": "AI Builder",
        "description": "Created or contributed to an AI-powered project",
        "icon": "sparkles",
        "category": "specialty",
        "points": 30,
    },
    {
        "slug": "community-helper",
        "name": "Community Helper",
        "description": "Submitted feedback or helped resolve community issues",
        "icon": "heart-handshake",
        "category": "community",
        "points": 25,
    },
    {
        "slug": "100-followers",
        "name": "100 Followers",
        "description": "Reached 100 followers on your developer profile",
        "icon": "star",
        "category": "social",
        "points": 100,
    },
]


class BadgeService:
    @staticmethod
    def seed_badges(db: Session) -> None:
        """Seed default achievement badges into the database if not present."""
        for badge_data in DEFAULT_BADGES:
            existing = db.query(Badge).filter(Badge.slug == badge_data["slug"]).first()
            if not existing:
                new_badge = Badge(**badge_data)
                db.add(new_badge)
        db.commit()

    @staticmethod
    def get_all_badges(db: Session) -> List[Badge]:
        BadgeService.seed_badges(db)
        return db.query(Badge).all()

    @staticmethod
    def get_user_badges(db: Session, user_id: uuid.UUID) -> List[UserBadge]:
        return db.query(UserBadge).filter(UserBadge.user_id == user_id).all()

    @staticmethod
    def evaluate_user_badges(
        db: Session, user_id: uuid.UUID
    ) -> BadgeEvaluationResponse:
        BadgeService.seed_badges(db)

        # Fetch existing user badge IDs
        existing_user_badges = (
            db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
        )
        existing_badge_slugs = {
            ub.badge.slug for ub in existing_user_badges if ub.badge
        }

        # Gather user statistics for milestone evaluation
        created_projects_count = (
            db.query(Project).filter(Project.owner_id == user_id).count()
        )
        collaboration_count = (
            db.query(ProjectMember).filter(ProjectMember.user_id == user_id).count()
        )
        followers_count = (
            db.query(Follower).filter(Follower.following_id == user_id).count()
        )

        # AI projects check
        ai_projects = (
            db.query(Project)
            .filter(
                (Project.owner_id == user_id),
                (
                    Project.title.ilike("%ai%")
                    | Project.description.ilike("%ai%")
                    | Project.title.ilike("%machine learning%")
                ),
            )
            .count()
        )

        feedback_count = 0
        try:
            feedback_count = (
                db.query(UserFeedback).filter(UserFeedback.user_id == user_id).count()
            )
        except Exception:
            pass

        eligible_slugs = []
        if created_projects_count >= 1:
            eligible_slugs.append("first-project")
        if collaboration_count >= 1 or created_projects_count >= 1:
            eligible_slugs.append("first-collaboration")
        if (created_projects_count + collaboration_count) >= 5:
            eligible_slugs.append("top-contributor")
        if ai_projects >= 1:
            eligible_slugs.append("ai-builder")
        if feedback_count >= 1:
            eligible_slugs.append("community-helper")
        if followers_count >= 100:
            eligible_slugs.append("100-followers")

        newly_awarded_badges: List[Badge] = []
        for slug in eligible_slugs:
            if slug not in existing_badge_slugs:
                badge = db.query(Badge).filter(Badge.slug == slug).first()
                if badge:
                    ub = UserBadge(user_id=user_id, badge_id=badge.id)
                    db.add(ub)
                    newly_awarded_badges.append(badge)

        if newly_awarded_badges:
            db.commit()

        all_user_badges = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
        total_points = sum(ub.badge.points for ub in all_user_badges if ub.badge)

        return BadgeEvaluationResponse(
            user_id=user_id,
            newly_awarded=[
                BadgeResponse.model_validate(b) for b in newly_awarded_badges
            ],
            total_badges=len(all_user_badges),
            total_points=total_points,
        )
