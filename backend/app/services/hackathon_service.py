from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cache import cached
from app.models.hackathon import Hackathon
from app.models.hackathon_judge import HackathonJudge
from app.models.hackathon_registration import HackathonRegistration, RegistrationStatus
from app.models.hackathon_score import HackathonScore
from app.models.hackathon_submission import HackathonSubmission
from app.models.hackathon_team import HackathonTeam, HackathonTeamMember, TeamMemberRole
from app.schemas.hackathon import (
    HackathonCreate,
    HackathonRegistrationCreate,
    HackathonSubmissionCreate,
    HackathonSubmissionUpdate,
    HackathonTeamCreate,
    HackathonUpdate,
)


class HackathonService:
    """
    Business logic for Hackathons.
    """

    # ==============================================================
    # Hackathon CRUD
    # ==============================================================

    @staticmethod
    def create_hackathon(
        db: Session,
        user_id: uuid.UUID,
        hackathon: HackathonCreate,
    ) -> Hackathon:
        db_hackathon = Hackathon(
            created_by=user_id,
            name=hackathon.name,
            description=hackathon.description,
            theme=hackathon.theme,
            registration_starts_at=hackathon.registration_starts_at,
            registration_ends_at=hackathon.registration_ends_at,
            starts_at=hackathon.starts_at,
            ends_at=hackathon.ends_at,
            min_team_size=hackathon.min_team_size,
            max_team_size=hackathon.max_team_size,
            prize=hackathon.prize,
            website_url=hackathon.website_url,
        )

        db.add(db_hackathon)
        db.flush()
        db.refresh(db_hackathon)

        return db_hackathon

    @staticmethod
    def get_hackathon(
        db: Session,
        hackathon_id: uuid.UUID,
    ) -> Hackathon | None:
        return db.get(Hackathon, hackathon_id)

    @staticmethod
    @cached(ttl=300, key_prefix="hackathon")
    def list_published_hackathons(
        db: Session,
    ) -> list[Hackathon]:
        stmt = select(Hackathon).where(Hackathon.is_published == True)
        return list(db.scalars(stmt))

    @staticmethod
    def update_hackathon(
        db: Session,
        db_hackathon: Hackathon,
        hackathon: HackathonUpdate,
    ) -> Hackathon:
        data = hackathon.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_hackathon, key, value)

        db.flush()
        db.refresh(db_hackathon)

        return db_hackathon

    @staticmethod
    def delete_hackathon(
        db: Session,
        db_hackathon: Hackathon,
    ) -> None:
        db.delete(db_hackathon)
        db.flush()

    # ==============================================================
    # Team Management
    # ==============================================================

    @staticmethod
    def create_team(
        db: Session,
        user_id: uuid.UUID,
        hackathon_id: uuid.UUID,
        team: HackathonTeamCreate,
    ) -> HackathonTeam:
        db_team = HackathonTeam(
            hackathon_id=hackathon_id,
            created_by=user_id,
            name=team.name,
            description=team.description,
        )

        db.add(db_team)
        db.flush()

        db_member = HackathonTeamMember(
            team_id=db_team.id,
            user_id=user_id,
            role=TeamMemberRole.LEADER,
        )
        db.add(db_member)
        db.flush()
        db.refresh(db_team)

        return db_team

    @staticmethod
    def get_team(
        db: Session,
        team_id: uuid.UUID,
    ) -> HackathonTeam | None:
        return db.get(HackathonTeam, team_id)

    @staticmethod
    def list_hackathon_teams(
        db: Session,
        hackathon_id: uuid.UUID,
    ) -> list[HackathonTeam]:
        stmt = select(HackathonTeam).where(HackathonTeam.hackathon_id == hackathon_id)
        return list(db.scalars(stmt))

    @staticmethod
    def join_team(
        db: Session,
        user_id: uuid.UUID,
        team_id: uuid.UUID,
    ) -> HackathonTeamMember:
        db_member = HackathonTeamMember(
            team_id=team_id,
            user_id=user_id,
            role=TeamMemberRole.MEMBER,
        )

        db.add(db_member)

        db_team = db.get(HackathonTeam, team_id)
        if db_team:
            db_team.member_count += 1

        db.flush()
        db.refresh(db_member)

        return db_member

    @staticmethod
    def leave_team(
        db: Session,
        user_id: uuid.UUID,
        team_id: uuid.UUID,
    ) -> None:
        stmt = select(HackathonTeamMember).where(
            HackathonTeamMember.team_id == team_id,
            HackathonTeamMember.user_id == user_id,
        )
        db_member = db.scalars(stmt).first()

        if db_member:
            db.delete(db_member)

            db_team = db.get(HackathonTeam, team_id)
            if db_team:
                db_team.member_count = max(0, db_team.member_count - 1)

            db.flush()

    # ==============================================================
    # Registration
    # ==============================================================

    @staticmethod
    def register_for_hackathon(
        db: Session,
        user_id: uuid.UUID,
        hackathon_id: uuid.UUID,
        registration: HackathonRegistrationCreate,
    ) -> HackathonRegistration:
        db_registration = HackathonRegistration(
            hackathon_id=hackathon_id,
            user_id=user_id,
            motivation=registration.motivation,
            experience_level=registration.experience_level,
        )

        db.add(db_registration)
        db.flush()
        db.refresh(db_registration)

        return db_registration

    @staticmethod
    def get_registration(
        db: Session,
        hackathon_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> HackathonRegistration | None:
        stmt = select(HackathonRegistration).where(
            HackathonRegistration.hackathon_id == hackathon_id,
            HackathonRegistration.user_id == user_id,
        )
        return db.scalars(stmt).first()

    @staticmethod
    def list_hackathon_registrations(
        db: Session,
        hackathon_id: uuid.UUID,
    ) -> list[HackathonRegistration]:
        stmt = select(HackathonRegistration).where(
            HackathonRegistration.hackathon_id == hackathon_id
        )
        return list(db.scalars(stmt))

    @staticmethod
    def cancel_registration(
        db: Session,
        db_registration: HackathonRegistration,
    ) -> HackathonRegistration:
        db_registration.status = RegistrationStatus.CANCELLED
        db.flush()
        db.refresh(db_registration)
        return db_registration

    # ==============================================================
    # Submission
    # ==============================================================

    @staticmethod
    def create_submission(
        db: Session,
        user_id: uuid.UUID,
        hackathon_id: uuid.UUID,
        submission: HackathonSubmissionCreate,
    ) -> HackathonSubmission:
        db_submission = HackathonSubmission(
            hackathon_id=hackathon_id,
            team_id=submission.team_id,
            submitted_by=user_id,
            title=submission.title,
            description=submission.description,
            repo_url=submission.repo_url,
            demo_url=submission.demo_url,
        )

        db.add(db_submission)
        db.flush()
        db.refresh(db_submission)

        return db_submission

    @staticmethod
    def get_submission(
        db: Session,
        submission_id: uuid.UUID,
    ) -> HackathonSubmission | None:
        return db.get(HackathonSubmission, submission_id)

    @staticmethod
    def list_hackathon_submissions(
        db: Session,
        hackathon_id: uuid.UUID,
    ) -> list[HackathonSubmission]:
        stmt = select(HackathonSubmission).where(
            HackathonSubmission.hackathon_id == hackathon_id
        )
        return list(db.scalars(stmt))

    @staticmethod
    def update_submission(
        db: Session,
        db_submission: HackathonSubmission,
        submission: HackathonSubmissionUpdate,
    ) -> HackathonSubmission:
        data = submission.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_submission, key, value)

        db.flush()
        db.refresh(db_submission)

        return db_submission

    # ==============================================================
    # Judges
    # ==============================================================

    @staticmethod
    def assign_judge(
        db: Session,
        hackathon_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> HackathonJudge:
        db_judge = HackathonJudge(
            hackathon_id=hackathon_id,
            user_id=user_id,
        )

        db.add(db_judge)
        db.flush()
        db.refresh(db_judge)

        return db_judge

    @staticmethod
    def is_judge(
        db: Session,
        hackathon_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        stmt = select(HackathonJudge).where(
            HackathonJudge.hackathon_id == hackathon_id,
            HackathonJudge.user_id == user_id,
        )
        return db.scalars(stmt).first() is not None

    @staticmethod
    def list_hackathon_judges(
        db: Session,
        hackathon_id: uuid.UUID,
    ) -> list[HackathonJudge]:
        stmt = select(HackathonJudge).where(HackathonJudge.hackathon_id == hackathon_id)
        return list(db.scalars(stmt))

    # ==============================================================
    # Scores & Leaderboard
    # ==============================================================

    @staticmethod
    def create_or_update_score(
        db: Session,
        submission_id: uuid.UUID,
        hackathon_id: uuid.UUID,
        judge_user_id: uuid.UUID,
        score: int,
        comments: str | None = None,
    ) -> HackathonScore:
        stmt_judge = select(HackathonJudge).where(
            HackathonJudge.hackathon_id == hackathon_id,
            HackathonJudge.user_id == judge_user_id,
        )
        db_judge = db.scalars(stmt_judge).first()

        if db_judge is None:
            raise ValueError("User is not an assigned judge")

        stmt = select(HackathonScore).where(
            HackathonScore.submission_id == submission_id,
            HackathonScore.judge_id == db_judge.id,
        )
        db_score = db.scalars(stmt).first()

        if db_score:
            db_score.score = score
            db_score.comments = comments
        else:
            db_score = HackathonScore(
                submission_id=submission_id,
                judge_id=db_judge.id,
                score=score,
                comments=comments,
            )
            db.add(db_score)

        db.flush()
        db.refresh(db_score)

        return db_score

    @staticmethod
    def get_leaderboard(
        db: Session,
        hackathon_id: uuid.UUID,
    ) -> list[dict]:
        from sqlalchemy import func as sqlfunc

        stmt = (
            select(
                HackathonTeam.id,
                HackathonTeam.name,
                HackathonSubmission.title.label("submission_title"),
                sqlfunc.avg(HackathonScore.score).label("avg_score"),
                sqlfunc.count(HackathonScore.id).label("judge_count"),
            )
            .join(HackathonSubmission, HackathonSubmission.team_id == HackathonTeam.id)
            .join(
                HackathonScore, HackathonScore.submission_id == HackathonSubmission.id
            )
            .where(HackathonTeam.hackathon_id == hackathon_id)
            .group_by(HackathonTeam.id, HackathonTeam.name, HackathonSubmission.title)
            .order_by(sqlfunc.avg(HackathonScore.score).desc())
        )

        results = db.execute(stmt).all()

        return [
            {
                "rank": idx + 1,
                "team_id": str(row.id),
                "team_name": row.name,
                "submission_title": row.submission_title or "",
                "avg_score": (
                    round(float(row.avg_score), 1) if row.avg_score is not None else 0.0
                ),
                "judge_count": row.judge_count,
            }
            for idx, row in enumerate(results)
        ]
