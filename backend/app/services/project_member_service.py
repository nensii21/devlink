from __future__ import annotations

import uuid
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project import Project
from app.models.project_member import ProjectMember, MemberRole
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService
from app.services.audit_log_service import AuditLogService
from app.models.audit_log import AuditAction
from app.core.rbac import (
    has_project_permission,
    PROJECT_MANAGE_ROLES,
    PROJECT_REMOVE_MEMBERS,
    PROJECT_VIEW,
)


class ProjectMemberService:
    @classmethod
    def get_membership(
        cls,
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ProjectMember | None:
        """Return the project membership row, or ``None`` if it does not exist."""
        return db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )

    @classmethod
    def require_membership(
        cls,
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ProjectMember:
        """Return the membership row, or 404 if it does not exist (#1310)."""
        membership = cls.get_membership(db, project_id, user_id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project membership not found",
            )
        return membership

    @classmethod
    def require_project_member_access(
        cls,
        db: Session,
        project: Project,
        actor_user: User,
        permission: str = PROJECT_VIEW,
        *,
        forbidden_detail: str = "You do not have access to this project's members",
    ) -> None:
        """403 unless the actor belongs to the project or holds ``permission``."""
        if actor_user.is_superuser or str(actor_user.id) == str(project.owner_id):
            return

        if not has_project_permission(db, actor_user.id, project.id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=forbidden_detail,
            )

    @classmethod
    def get_project_members(
        cls, db: Session, project_id: uuid.UUID, actor_user: User
    ) -> List[Dict[str, Any]]:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        cls.require_project_member_access(db, project, actor_user)

        stmt = (
            select(ProjectMember, User)
            .join(User, ProjectMember.user_id == User.id)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.is_active.is_(True),
            )
            .order_by(ProjectMember.joined_at.asc())
        )

        results = list(db.execute(stmt).all())
        members_list = []
        user_ids_seen = set()

        # Check if owner is already in members
        for pm, user in results:
            user_ids_seen.add(user.id)
            role_val = MemberRole.OWNER if user.id == project.owner_id else pm.role
            members_list.append(
                {
                    "id": str(pm.id),
                    "project_id": str(pm.project_id),
                    "user_id": str(pm.user_id),
                    "role": role_val,
                    "is_active": pm.is_active,
                    "joined_at": pm.joined_at,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "avatar_url": getattr(user, "avatar_url", None),
                }
            )

        # If project owner is not in project_members table, add owner entry
        if project.owner_id not in user_ids_seen:
            owner_user = db.get(User, project.owner_id)
            if owner_user:
                members_list.insert(
                    0,
                    {
                        "id": str(uuid.uuid4()),
                        "project_id": str(project.id),
                        "user_id": str(owner_user.id),
                        "role": MemberRole.OWNER,
                        "is_active": True,
                        "joined_at": project.created_at,
                        "username": owner_user.username,
                        "first_name": owner_user.first_name,
                        "last_name": owner_user.last_name,
                        "avatar_url": getattr(owner_user, "avatar_url", None),
                    },
                )

        return members_list

    @classmethod
    def update_member_role(
        cls,
        db: Session,
        project_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role: MemberRole,
        actor_user: User,
    ) -> ProjectMember:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        cls.require_project_member_access(
            db,
            project,
            actor_user,
            PROJECT_MANAGE_ROLES,
            forbidden_detail="Insufficient permissions to manage project roles",
        )

        # Cannot alter project owner role via normal update
        if target_user_id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change project owner role. Use transfer ownership instead.",
            )

        pm = cls.require_membership(db, project_id, target_user_id)
        pm.role = new_role
        pm.is_active = True

        db.commit()
        db.refresh(pm)

        # Notify target user
        try:
            notification = NotificationCreate(
                recipient_id=target_user_id,
                type=NotificationType.ROLE_CHANGE,
                title="Project Role Updated",
                message=f"Your role in project '{project.title}' was updated to {new_role.value.capitalize()}.",
                action_url=f"/projects/{project_id}",
                project_id=project_id,
            )
            NotificationService.create_notification(
                db=db,
                recipient_id=target_user_id,
                sender_id=actor_user.id,
                notification=notification,
            )
        except Exception:
            pass

        # Audit log
        AuditLogService.create_log(
            db=db,
            actor_id=actor_user.id,
            action=AuditAction.PROJECT_MEMBER_ROLE_UPDATED,
            entity_type="project_member",
            entity_id=str(pm.id),
            project_id=project_id,
            target_user_id=target_user_id,
            description=f"Updated member {target_user_id} role to {new_role.value}",
            new_values={"role": new_role.value},
        )

        return pm

    @classmethod
    def transfer_ownership(
        cls,
        db: Session,
        project_id: uuid.UUID,
        new_owner_id: uuid.UUID,
        current_owner: User,
    ) -> Project:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        if project.owner_id != current_owner.id and not current_owner.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the project owner can transfer project ownership",
            )

        if new_owner_id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target user is already the project owner",
            )

        new_owner = db.get(User, new_owner_id)
        if not new_owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="New owner user not found"
            )

        previous_owner_id = project.owner_id
        project.owner_id = new_owner_id

        # Update previous owner member record to MAINTAINER
        prev_pm = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == previous_owner_id,
            )
        )
        if prev_pm:
            prev_pm.role = MemberRole.MAINTAINER
        else:
            db.add(
                ProjectMember(
                    project_id=project_id,
                    user_id=previous_owner_id,
                    role=MemberRole.MAINTAINER,
                    is_active=True,
                )
            )

        # Update new owner member record to OWNER
        new_pm = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == new_owner_id,
            )
        )
        if new_pm:
            new_pm.role = MemberRole.OWNER
            new_pm.is_active = True
        else:
            db.add(
                ProjectMember(
                    project_id=project_id,
                    user_id=new_owner_id,
                    role=MemberRole.OWNER,
                    is_active=True,
                )
            )

        db.commit()
        db.refresh(project)

        # Notify new owner
        try:
            notification = NotificationCreate(
                recipient_id=new_owner_id,
                type=NotificationType.ROLE_CHANGE,
                title="Project Ownership Transferred",
                message=f"You are now the Project Owner of '{project.title}'.",
                action_url=f"/projects/{project_id}",
                project_id=project_id,
            )
            NotificationService.create_notification(
                db=db,
                recipient_id=new_owner_id,
                sender_id=current_owner.id,
                notification=notification,
            )
        except Exception:
            pass

        # Audit log
        AuditLogService.create_log(
            db=db,
            actor_id=current_owner.id,
            action=AuditAction.PROJECT_OWNERSHIP_TRANSFERRED,
            entity_type="project",
            entity_id=str(project_id),
            project_id=project_id,
            target_user_id=new_owner_id,
            description=f"Transferred project ownership to {new_owner.username}",
            old_values={"owner_id": str(previous_owner_id)},
            new_values={"owner_id": str(new_owner_id)},
        )

        return project

    @classmethod
    def remove_member(
        cls,
        db: Session,
        project_id: uuid.UUID,
        target_user_id: uuid.UUID,
        actor_user: User,
    ) -> None:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        if target_user_id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove project owner from team",
            )

        # Allow self-removal, otherwise require manage permissions
        if actor_user.id != target_user_id:
            cls.require_project_member_access(
                db,
                project,
                actor_user,
                PROJECT_REMOVE_MEMBERS,
                forbidden_detail="Insufficient permissions to remove team members",
            )

        pm = cls.require_membership(db, project_id, target_user_id)
        db.delete(pm)
        db.commit()

        # Audit log
        AuditLogService.create_log(
            db=db,
            actor_id=actor_user.id,
            action=AuditAction.PROJECT_MEMBER_REMOVED,
            entity_type="project_member",
            entity_id=str(target_user_id),
            project_id=project_id,
            target_user_id=target_user_id,
            description=f"Removed member {target_user_id} from project",
        )

    @classmethod
    def cancel_invitation(
        cls,
        db: Session,
        project_id: uuid.UUID,
        target_user_id: uuid.UUID,
        actor_user: User,
    ) -> None:
        """Cancel a pending project invitation.
        
        Only project owners and admins can cancel invitations.
        Active/accepted or non-pending memberships cannot be cancelled.
        """
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # 1. Authorization: Only project owner or members with role management / admin permissions
        is_owner = actor_user.id == project.owner_id
        is_admin_or_permitted = (
            actor_user.is_superuser
            or has_project_permission(db, actor_user.id, project_id, PROJECT_MANAGE_ROLES)
            or has_project_permission(db, actor_user.id, project_id, PROJECT_REMOVE_MEMBERS)
        )
        if not (is_owner or is_admin_or_permitted):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners and admins can cancel invitations",
            )

        # 2. Retrieve invitation record
        pm = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == target_user_id,
            )
        )
        if not pm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No invitation found for this user on the project",
            )

        # 3. State validation: Only pending (is_active is False) invitations can be cancelled
        if pm.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel invitation: User is already an active member of this project",
            )

        # 4. Remove pending invitation
        db.delete(pm)

        # 5. Clean up / mark pending invitation notifications
        try:
            from app.models.notification import Notification, NotificationType

            pending_notifications = (
                db.query(Notification)
                .filter(
                    Notification.recipient_id == target_user_id,
                    Notification.project_id == project_id,
                    Notification.type == NotificationType.PROJECT_INVITE,
                )
                .all()
            )
            for notif in pending_notifications:
                notif.read = True
        except Exception:
            pass

        db.commit()

        # 6. Emit audit log
        AuditLogService.create_log(
            db=db,
            actor_id=actor_user.id,
            action=AuditAction.INVITATION_REVOKED,
            entity_type="project_invitation",
            entity_id=str(target_user_id),
            project_id=project_id,
            target_user_id=target_user_id,
            description=f"Cancelled pending project invitation for user {target_user_id}",
        )

    @classmethod
    def add_member(
        cls,
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        role: MemberRole = MemberRole.MEMBER,
        is_active: bool = True,
        actor_user: User | None = None,
    ) -> ProjectMember:
        """Add a member to a project with strict duplicate prevention and integrity validation."""
        from sqlalchemy.exc import IntegrityError

        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # 1. Check if user is the project owner
        if user_id == project.owner_id and role != MemberRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already the owner of this project",
            )

        # 2. Service-level check for existing membership record
        existing = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        if existing:
            if existing.is_active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User is already an active member of this project",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already has a pending invitation for this project",
                )

        # 3. Create and persist member record with database integrity safeguard
        pm = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            is_active=is_active,
        )
        db.add(pm)
        try:
            db.commit()
            db.refresh(pm)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate membership: user is already a member of this project",
            )

        if actor_user:
            AuditLogService.create_log(
                db=db,
                actor_id=actor_user.id,
                action=AuditAction.PROJECT_MEMBER_ADDED,
                entity_type="project_member",
                entity_id=str(pm.id),
                project_id=project_id,
                target_user_id=user_id,
                description=f"Added member {user_id} with role {role.value}",
            )

        return pm

