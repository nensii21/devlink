from __future__ import annotations

import uuid
from datetime import datetime

# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status

# pyrefly: ignore [missing-import]
from sqlalchemy import select

# pyrefly: ignore [missing-import]
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

# pyrefly: ignore [missing-import]
from app.models.application import (
    Application,
    ApplicationStatus,
)
from app.models.project import Project
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.application import (
    ApplicationCreate,
    ApplicationPrefillResponse,
    ApplicationUpdate,
    OneClickApplicationCreate,
)
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService


class ApplicationService:
    """
    Business logic for project applications.
    """

    VALID_STATUS_TRANSITIONS = {
        ApplicationStatus.PENDING: {
            ApplicationStatus.ACCEPTED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.REVIEWING: {
            ApplicationStatus.INTERVIEWING,
            ApplicationStatus.ACCEPTED,
            ApplicationStatus.REJECTED,
        },
        ApplicationStatus.INTERVIEWING: {
            ApplicationStatus.ACCEPTED,
            ApplicationStatus.REJECTED,
        },
        ApplicationStatus.ACCEPTED: set(),
        ApplicationStatus.REJECTED: set(),
        ApplicationStatus.WITHDRAWN: set(),
    }

    @staticmethod
    def _validate_status_transition(
        current: ApplicationStatus,
        new: ApplicationStatus,
    ) -> None:
        if new not in ApplicationService.VALID_STATUS_TRANSITIONS[current]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot change application status "
                    f"from '{current.value}' to '{new.value}'."
                ),
            )

    @staticmethod
    def create_application(
        db: Session,
        applicant_id: uuid.UUID,
        project_id: uuid.UUID,
        flare_id: uuid.UUID,
        application: ApplicationCreate,
    ) -> Application:
        db_application = Application(
            applicant_id=applicant_id,
            project_id=project_id,
            flare_id=flare_id,
            message=application.message,
            portfolio_url=application.portfolio_url,
            github_url=application.github_url,
            resume_url=application.resume_url,
        )

        db.add(db_application)

        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied to this project with this status.",
            )
        db.refresh(db_application)
        return db_application

    @staticmethod
    def get_application_prefill(
        db: Session,
        user_id: uuid.UUID,
    ) -> ApplicationPrefillResponse:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
        skills = getattr(user, "skills", []) or []
        skills_str = ", ".join(skills[:4]) if skills else "software engineering"
        headline = getattr(user, "headline", None) or "Full Stack Developer"
        role = getattr(user, "role", None) or "Developer"

        suggested_cover_letter = (
            f"Hi! I'm {full_name}, a {headline} proficient in {skills_str}. "
            f"I would love to join your team as a {role} and bring scalable solutions to this project."
        )

        return ApplicationPrefillResponse(
            user_id=user.id,
            full_name=full_name,
            username=user.username,
            headline=headline,
            skills=skills,
            github_url=getattr(user, "github_url", None) or getattr(user, "githubUrl", None),
            portfolio_url=(
                getattr(user, "portfolio_url", None)
                or getattr(user, "portfolioUrl", None)
                or getattr(user, "website", None)
            ),
            resume_url=getattr(user, "resume_url", None) or getattr(user, "resumeUrl", None),
            role=role,
            suggested_cover_letter=suggested_cover_letter,
        )

    @staticmethod
    def one_click_apply(
        db: Session,
        applicant_id: uuid.UUID,
        payload: OneClickApplicationCreate,
    ) -> Application:
        user = db.get(User, applicant_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        project = db.get(Project, payload.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # Prevent owner from applying to own project
        if project.owner_id == applicant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot apply to your own project.",
            )

        # Check existing active application
        existing = db.scalars(
            select(Application).where(
                Application.applicant_id == applicant_id,
                Application.project_id == payload.project_id,
                Application.status.in_([
                    ApplicationStatus.PENDING,
                    ApplicationStatus.REVIEWING,
                    ApplicationStatus.INTERVIEWING,
                    ApplicationStatus.ACCEPTED,
                ])
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You have already applied to this project (Status: {existing.status.value}).",
            )

        # Resolve fields from profile if auto_use_profile or missing
        resume_url = payload.resume_url or (getattr(user, "resume_url", None) if payload.auto_use_profile else None)
        portfolio_url = payload.portfolio_url or (
            (getattr(user, "portfolio_url", None) or getattr(user, "website", None))
            if payload.auto_use_profile else None
        )
        github_url = payload.github_url or (getattr(user, "github_url", None) if payload.auto_use_profile else None)
        message = payload.cover_letter or payload.selected_role or "Applied via 1-Click DevLink Profile"

        db_application = Application(
            applicant_id=applicant_id,
            project_id=payload.project_id,
            flare_id=payload.flare_id or payload.project_id,
            message=message,
            portfolio_url=portfolio_url,
            github_url=github_url,
            resume_url=resume_url,
            status=ApplicationStatus.PENDING,
        )

        db.add(db_application)

        if hasattr(project, "applications_count"):
            project.applications_count = (project.applications_count or 0) + 1

        try:
            db.commit()
            db.refresh(db_application)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted an application to this project.",
            )

        return db_application

    @staticmethod
    def withdraw_application_by_applicant(
        db: Session,
        application_id: uuid.UUID,
        applicant_id: uuid.UUID,
    ) -> Application:
        db_application = db.get(Application, application_id)
        if not db_application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )

        if db_application.applicant_id != applicant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to withdraw this application",
            )

        if db_application.status not in (ApplicationStatus.PENDING, ApplicationStatus.REVIEWING):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending or reviewing applications can be withdrawn",
            )

        db_application.status = ApplicationStatus.WITHDRAWN
        db.commit()
        db.refresh(db_application)
        return db_application

    @staticmethod
    def get_application(
        db: Session,
        application_id: uuid.UUID,
    ) -> Application | None:

        return db.get(Application, application_id)

    @staticmethod
    def list_project_applications(
        db: Session,
        project_id: uuid.UUID,
    ) -> list[Application]:

        stmt = (
            select(Application)
            .options(
                selectinload(Application.applicant), selectinload(Application.project)
            )
            .where(Application.project_id == project_id)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_user_applications(
        db: Session,
        applicant_id: uuid.UUID,
    ) -> list[Application]:

        stmt = (
            select(Application)
            .options(
                selectinload(Application.applicant), selectinload(Application.project)
            )
            .where(Application.applicant_id == applicant_id)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_application(
        db: Session,
        db_application: Application,
        application: ApplicationUpdate,
    ) -> Application:

        data = application.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_application, key, value)

        db.flush()
        db.refresh(db_application)

        return db_application

    @staticmethod
    def accept_application(
        db: Session,
        db_application: Application,
    ) -> Application:

        ApplicationService._validate_status_transition(
            db_application.status,
            ApplicationStatus.ACCEPTED,
        )

        db_application.status = ApplicationStatus.ACCEPTED
        db.flush()
        db.refresh(db_application)

        project_title = (
            db_application.project.title if db_application.project else "Project"
        )
        owner_id = db_application.project.owner_id if db_application.project else None

        # Create ProjectMember record for applicant if not already present
        from app.models.project_member import MemberRole, ProjectMember

        existing_pm = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == db_application.project_id,
                ProjectMember.user_id == db_application.applicant_id,
            )
        )
        if not existing_pm:
            pm = ProjectMember(
                project_id=db_application.project_id,
                user_id=db_application.applicant_id,
                role=MemberRole.MEMBER,
                is_active=True,
            )
            db.add(pm)
        else:
            existing_pm.is_active = True

        db.commit()

        # Trigger notification
        notification_data = NotificationCreate(
            recipient_id=db_application.applicant_id,
            type=NotificationType.APPLICATION_ACCEPTED,
            title="Application Accepted",
            message=f"Your application for project '{project_title}' has been accepted!",
            action_url=f"/projects/{db_application.project_id}",
            project_id=db_application.project_id,
            application_id=db_application.id,
        )
        NotificationService.create_notification(
            db=db,
            recipient_id=db_application.applicant_id,
            sender_id=owner_id,
            notification=notification_data,
        )

        # Record activity for joining project
        from app.models.activity import ActivityType
        from app.services.activity_service import ActivityService

        ActivityService.record_activity(
            db=db,
            actor_id=db_application.applicant_id,
            activity_type=ActivityType.PROJECT_JOINED,
            title="Joined project",
            description=f"Joined project '{project_title}'",
            target_id=db_application.project_id,
            target_type="project",
            icon="user-check",
            color="success",
        )

        return db_application

    @staticmethod
    def reject_application(
        db: Session,
        db_application: Application,
    ) -> Application:

        ApplicationService._validate_status_transition(
            db_application.status,
            ApplicationStatus.REJECTED,
        )

        db_application.status = ApplicationStatus.REJECTED

        db.flush()
        db.refresh(db_application)

        # Trigger notification
        project_title = (
            db_application.project.title if db_application.project else "Project"
        )
        owner_id = db_application.project.owner_id if db_application.project else None

        notification_data = NotificationCreate(
            recipient_id=db_application.applicant_id,
            type=NotificationType.APPLICATION_REJECTED,
            title="Application Rejected",
            message=f"Your application for project '{project_title}' has been rejected.",
            action_url=f"/projects/{db_application.project_id}",
            project_id=db_application.project_id,
            application_id=db_application.id,
        )
        NotificationService.create_notification(
            db=db,
            recipient_id=db_application.applicant_id,
            sender_id=owner_id,
            notification=notification_data,
        )

        return db_application

    @staticmethod
    def schedule_interview(
        db: Session,
        db_application: Application,
        interview_scheduled_at: datetime,
        interview_link: str | None = None,
    ) -> Application:

        ApplicationService._validate_status_transition(
            db_application.status,
            ApplicationStatus.INTERVIEWING,
        )

        db_application.status = ApplicationStatus.INTERVIEWING
        db_application.interview_scheduled_at = interview_scheduled_at
        db_application.interview_link = interview_link

        db.flush()
        db.refresh(db_application)

        project_title = (
            db_application.project.title if db_application.project else "Project"
        )
        owner_id = db_application.project.owner_id if db_application.project else None

        notification_data = NotificationCreate(
            recipient_id=db_application.applicant_id,
            type=NotificationType.MESSAGE,
            title="Interview Scheduled",
            message=f"An interview for '{project_title}' has been scheduled.",
            action_url=f"/applications/{db_application.id}",
            project_id=db_application.project_id,
            application_id=db_application.id,
        )
        NotificationService.create_notification(
            db=db,
            recipient_id=db_application.applicant_id,
            sender_id=owner_id,
            notification=notification_data,
        )

        return db_application

    @staticmethod
    def shortlist_application(
        db: Session,
        db_application: Application,
        shortlisted: bool,
    ) -> Application:

        db_application.shortlisted = shortlisted

        if shortlisted and db_application.status == ApplicationStatus.PENDING:
            ApplicationService._validate_status_transition(
                db_application.status,
                ApplicationStatus.REVIEWING,
            )
            db_application.status = ApplicationStatus.REVIEWING

        db.flush()
        db.refresh(db_application)
        return db_application

    @staticmethod
    def add_notes(
        db: Session,
        db_application: Application,
        notes: str | None,
    ) -> Application:

        db_application.review_notes = notes
        db.flush()
        db.refresh(db_application)
        return db_application

    @staticmethod
    def withdraw_application(
        db: Session,
        db_application: Application,
    ) -> Application:
        if db_application.status != ApplicationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending applications can be withdrawn",
            )

        db_application.status = ApplicationStatus.WITHDRAWN
        db.flush()
        db.refresh(db_application)

        return db_application

    @staticmethod
    def delete_application(
        db: Session,
        db_application: Application,
    ) -> None:

        db.delete(db_application)
        db.flush()
