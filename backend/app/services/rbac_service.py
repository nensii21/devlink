"""
Role-Based Access Control (RBAC) service module.
Enforces granular permission evaluation, custom role definitions, role inheritance, and access auditing.
"""

from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field
import time


DEFAULT_PERMISSIONS: Dict[str, Set[str]] = {
    "owner": {
        "project:admin", "project:write", "project:read", "project:delete",
        "member:manage", "code:merge", "code:review", "analytics:view", "analytics:export"
    },
    "admin": {
        "project:write", "project:read", "member:manage", "code:merge",
        "code:review", "analytics:view", "analytics:export"
    },
    "maintainer": {
        "project:write", "project:read", "code:merge", "code:review", "analytics:view"
    },
    "contributor": {
        "project:read", "code:review", "issue:create"
    },
    "viewer": {
        "project:read"
    }
}


@dataclass
class CustomRole:
    name: str
    project_id: str
    permissions: Set[str] = field(default_factory=set)
    inherits_from: Optional[str] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class AuditLogEntry:
    project_id: str
    user_id: str
    role_name: str
    permission: str
    granted: bool
    timestamp: float = field(default_factory=time.time)


class RBACService:
    """Manages role permissions, evaluates access policies, and records audit logs."""

    def __init__(self):
        self._custom_roles: Dict[str, CustomRole] = {}
        self._audit_logs: List[AuditLogEntry] = []

    def register_custom_role(self, role: CustomRole) -> None:
        """Registers or updates a custom project-specific role."""
        key = f"{role.project_id}:{role.name.lower()}"
        self._custom_roles[key] = role

    def get_role_permissions(self, project_id: str, role_name: str) -> Set[str]:
        """Resolves all permissions for a role, including inherited privileges."""
        clean_name = role_name.lower()
        key = f"{project_id}:{clean_name}"

        if key in self._custom_roles:
            role = self._custom_roles[key]
            perms = set(role.permissions)
            if role.inherits_from and role.inherits_from.lower() in DEFAULT_PERMISSIONS:
                perms.update(DEFAULT_PERMISSIONS[role.inherits_from.lower()])
            return perms

        return DEFAULT_PERMISSIONS.get(clean_name, set())

    def has_permission(
        self, project_id: str, user_role: str, required_permission: str, user_id: str = "anonymous"
    ) -> bool:
        """Evaluates whether a given user role possesses the requested permission."""
        permissions = self.get_role_permissions(project_id, user_role)
        granted = "project:admin" in permissions or required_permission in permissions

        self._audit_logs.append(
            AuditLogEntry(
                project_id=project_id,
                user_id=user_id,
                role_name=user_role,
                permission=required_permission,
                granted=granted
            )
        )
        return granted

    def get_audit_logs(self, project_id: Optional[str] = None) -> List[AuditLogEntry]:
        if project_id:
            return [l for l in self._audit_logs if l.project_id == project_id]
        return self._audit_logs


rbac_service = RBACService()
