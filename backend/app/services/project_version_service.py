from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.project_member import ProjectMember
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.services.audit_log_service import AuditLogService


class ProjectVersionService:
    """
    Business logic for Project Version History (#606)
    """

    @classmethod
    def _get_team_roles_snapshot(
        cls, db: Session, project_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Capture team roles snapshot for the version payload."""
        members = list(
            db.scalars(
                select(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.is_active.is_(True),
                )
            )
        )
        return [
            {
                "user_id": str(pm.user_id),
                "role": pm.role.value if hasattr(pm.role, "value") else str(pm.role),
                "joined_at": pm.joined_at.isoformat() if pm.joined_at else None,
            }
            for pm in members
        ]

    @classmethod
    def create_version(
        cls,
        db: Session,
        project: Project,
        actor_id: Optional[uuid.UUID] = None,
        change_summary: Optional[str] = None,
    ) -> ProjectVersion:
        """Create a new version record capturing current project state."""
        max_v = db.scalar(
            select(func.max(ProjectVersion.version_number)).where(
                ProjectVersion.project_id == project.id
            )
        )
        next_v = (max_v + 1) if isinstance(max_v, int) else 1

        team_roles = cls._get_team_roles_snapshot(db, project.id)

        stage_str = (
            project.stage.value
            if hasattr(project.stage, "value")
            else str(project.stage)
        )
        vis_str = (
            project.visibility.value
            if hasattr(project.visibility, "value")
            else str(project.visibility)
        )

        version = ProjectVersion(
            id=uuid.uuid4(),
            project_id=project.id,
            version_number=next_v,
            title=project.title,
            tagline=project.tagline,
            description=project.description,
            tech_stack=project.tech_stack,
            requirements=project.requirements,
            language=project.language,
            experience=project.experience,
            stage=stage_str,
            visibility=vis_str,
            team_roles=team_roles,
            change_summary=change_summary or f"Version {next_v} edit snapshot",
            created_by_id=actor_id or project.owner_id,
            created_at=datetime.now(timezone.utc),
        )

        db.add(version)
        db.flush()
        db.refresh(version)

        AuditLogService.create_log(
            db=db,
            actor_id=actor_id or project.owner_id,
            action=AuditAction.PROJECT_VERSION_CREATED,
            entity_type="project_version",
            entity_id=str(version.id),
            project_id=project.id,
            description=f"Created project version {next_v}",
            new_values={"version_number": next_v, "title": version.title},
        )

        return version

    @classmethod
    def list_versions(
        cls,
        db: Session,
        project_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """List version history for a project (ordered latest first)."""
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        stmt = (
            select(ProjectVersion)
            .where(ProjectVersion.project_id == project_id)
            .order_by(ProjectVersion.version_number.desc())
        )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        offset = (page - 1) * limit
        paginated_stmt = stmt.offset(offset).limit(limit)
        items = list(db.scalars(paginated_stmt))
        pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @classmethod
    def get_version(
        cls,
        db: Session,
        project_id: uuid.UUID,
        version_identifier: str,
    ) -> ProjectVersion:
        """Fetch version by version UUID or integer version_number."""
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        # Try parsing as UUID first
        try:
            v_uuid = uuid.UUID(version_identifier)
            version = db.scalar(
                select(ProjectVersion).where(
                    ProjectVersion.project_id == project_id,
                    ProjectVersion.id == v_uuid,
                )
            )
            if version:
                return version
        except ValueError:
            pass

        # Try parsing as integer version number
        try:
            v_num = int(version_identifier)
            version = db.scalar(
                select(ProjectVersion).where(
                    ProjectVersion.project_id == project_id,
                    ProjectVersion.version_number == v_num,
                )
            )
            if version:
                return version
        except ValueError:
            pass

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{version_identifier}' not found for project",
        )

    @classmethod
    def compare_versions(
        cls,
        db: Session,
        project_id: uuid.UUID,
        v1_identifier: str,
        v2_identifier: str = "current",
    ) -> Dict[str, Any]:
        """Compare version 1 with version 2 (or current state) and compute field diffs."""
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        v1_version = cls.get_version(db, project_id, v1_identifier)

        if v2_identifier.lower() == "current":
            team_roles_current = cls._get_team_roles_snapshot(db, project.id)
            v2_dict = {
                "version_number": "current",
                "title": project.title,
                "tagline": project.tagline,
                "description": project.description,
                "tech_stack": project.tech_stack,
                "requirements": project.requirements,
                "language": project.language,
                "experience": project.experience,
                "stage": (
                    project.stage.value
                    if hasattr(project.stage, "value")
                    else str(project.stage)
                ),
                "visibility": (
                    project.visibility.value
                    if hasattr(project.visibility, "value")
                    else str(project.visibility)
                ),
                "team_roles": team_roles_current,
            }
            v2_num = "current"
        else:
            v2_version = cls.get_version(db, project_id, v2_identifier)
            v2_dict = {
                "version_number": v2_version.version_number,
                "title": v2_version.title,
                "tagline": v2_version.tagline,
                "description": v2_version.description,
                "tech_stack": v2_version.tech_stack,
                "requirements": v2_version.requirements,
                "language": v2_version.language,
                "experience": v2_version.experience,
                "stage": v2_version.stage,
                "visibility": v2_version.visibility,
                "team_roles": v2_version.team_roles,
            }
            v2_num = v2_version.version_number

        diff: Dict[str, Dict[str, Any]] = {}
        tracked_fields = [
            "title",
            "tagline",
            "description",
            "tech_stack",
            "requirements",
            "language",
            "experience",
            "stage",
            "visibility",
            "team_roles",
        ]

        for field in tracked_fields:
            val1 = getattr(v1_version, field)
            val2 = v2_dict.get(field)
            if val1 != val2:
                diff[field] = {"old": val1, "new": val2}

        return {
            "project_id": project.id,
            "v1_version_number": v1_version.version_number,
            "v2_version_number": v2_num,
            "v1_snapshot": v1_version,
            "v2_snapshot": v2_dict,
            "diff": diff,
        }

    @classmethod
    def restore_version(
        cls,
        db: Session,
        project_id: uuid.UUID,
        version_identifier: str,
        actor_user: User,
    ) -> Project:
        """
        Restore a project to a previous version.
        Before restoring, creates a snapshot version of the current state.
        """
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        # Check permissions: owner or superuser or update permission
        if actor_user.id != project.owner_id and not actor_user.is_superuser:
            from app.core.rbac import has_project_permission

            if not has_project_permission(
                db, actor_user.id, project_id, "project:update"
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to restore project versions",
                )

        target_version = cls.get_version(db, project_id, version_identifier)

        # 1. Snapshot current state as new version before restoring
        cls.create_version(
            db=db,
            project=project,
            actor_id=actor_user.id,
            change_summary=f"Pre-restore backup before reverting to version {target_version.version_number}",
        )

        old_snapshot = {
            "title": project.title,
            "description": project.description,
            "tech_stack": project.tech_stack,
            "requirements": project.requirements,
            "stage": (
                project.stage.value
                if hasattr(project.stage, "value")
                else str(project.stage)
            ),
        }

        # 2. Revert project fields
        project.title = target_version.title
        project.tagline = target_version.tagline
        project.description = target_version.description
        project.tech_stack = target_version.tech_stack
        project.requirements = target_version.requirements
        project.language = target_version.language
        project.experience = target_version.experience

        try:
            project.stage = ProjectStage(target_version.stage)
        except ValueError:
            pass

        try:
            project.visibility = ProjectVisibility(target_version.visibility)
        except ValueError:
            pass

        project.updated_at = datetime.now(timezone.utc)
        db.add(project)
        db.commit()
        db.refresh(project)

        # 3. Snapshot new restored state
        restored_version = cls.create_version(
            db=db,
            project=project,
            actor_id=actor_user.id,
            change_summary=f"Restored from version {target_version.version_number}",
        )

        # 4. Audit Log
        AuditLogService.create_log(
            db=db,
            actor_id=actor_user.id,
            action=AuditAction.PROJECT_VERSION_RESTORED,
            entity_type="project",
            entity_id=str(project.id),
            project_id=project.id,
            old_values=old_snapshot,
            new_values={
                "restored_to_version": target_version.version_number,
                "new_version_number": restored_version.version_number,
                "title": project.title,
            },
            description=f"Restored project '{project.title}' to version {target_version.version_number}",
        )

        return project
