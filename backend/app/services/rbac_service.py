"""
Role-Based Access Control (RBAC) service module.
Enforces granular policy evaluation, custom role definitions, hierarchical inheritance, and access auditing.
"""

from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import fnmatch


class PolicyEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class PolicyRule:
    rule_id: str
    effect: PolicyEffect
    actions: List[str]  # e.g., ["project:write", "issue:*"]
    resources: List[str]  # e.g., ["project:123", "org:*"]
    conditions: Dict[str, Any] = field(default_factory=dict)  # e.g., {"is_active": True}


@dataclass
class CustomRole:
    name: str
    project_id: str
    policies: List[PolicyRule] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)  # Names of other CustomRoles
    created_at: float = field(default_factory=time.time)


@dataclass
class AuditLogEntry:
    project_id: str
    user_id: str
    role_name: str
    action: str
    resource: str
    context: Dict[str, Any]
    granted: bool
    matched_rule_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class RBACService:
    """Manages role policies, evaluates access with explicit deny overrides, and records audit logs."""

    def __init__(self):
        self._custom_roles: Dict[str, CustomRole] = {}
        self._audit_logs: List[AuditLogEntry] = []

    def register_custom_role(self, role: CustomRole) -> None:
        """Registers or updates a custom project-specific role."""
        key = f"{role.project_id}:{role.name.lower()}"
        self._custom_roles[key] = role

    def get_role_policies(self, project_id: str, role_name: str) -> List[PolicyRule]:
        """Resolves all policies for a role, resolving the directed acyclic graph (DAG) of inheritance."""
        clean_name = role_name.lower()
        key = f"{project_id}:{clean_name}"

        if key not in self._custom_roles:
            return []

        resolved_policies = []
        visited = set()

        def dfs(current_role_name: str):
            current_key = f"{project_id}:{current_role_name.lower()}"
            if current_key in visited or current_key not in self._custom_roles:
                return
            
            visited.add(current_key)
            role = self._custom_roles[current_key]
            resolved_policies.extend(role.policies)
            
            for parent_role in role.inherits_from:
                dfs(parent_role)

        dfs(clean_name)
        return resolved_policies

    def _matches_pattern(self, requested: str, patterns: List[str]) -> bool:
        """Checks if a string matches any glob pattern in the list."""
        for pattern in patterns:
            if fnmatch.fnmatchcase(requested, pattern):
                return True
        return False

    def _evaluate_conditions(self, rule_conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluates if the execution context satisfies the rule's conditions."""
        for key, expected_value in rule_conditions.items():
            if context.get(key) != expected_value:
                return False
        return True

    def evaluate_access(
        self, project_id: str, user_role: str, action: str, resource: str, context: Optional[Dict[str, Any]] = None, user_id: str = "anonymous"
    ) -> bool:
        """Evaluates whether a given user role possesses the requested action on the resource. Explicit Deny overrides Allow."""
        context = context or {}
        policies = self.get_role_policies(project_id, user_role)
        
        is_allowed = False
        matched_rule = None

        for rule in policies:
            # Check Action and Resource scopes using glob matching
            if self._matches_pattern(action, rule.actions) and self._matches_pattern(resource, rule.resources):
                # Check contextual conditions
                if self._evaluate_conditions(rule.conditions, context):
                    if rule.effect == PolicyEffect.DENY:
                        # Explicit deny immediately halts evaluation
                        is_allowed = False
                        matched_rule = rule.rule_id
                        break
                    elif rule.effect == PolicyEffect.ALLOW:
                        # Allow can be overridden by a later DENY, but we record it for now
                        is_allowed = True
                        matched_rule = rule.rule_id

        # Always record the authorization decision
        self._audit_logs.append(
            AuditLogEntry(
                project_id=project_id,
                user_id=user_id,
                role_name=user_role,
                action=action,
                resource=resource,
                context=context,
                granted=is_allowed,
                matched_rule_id=matched_rule
            )
        )
        return is_allowed

    def get_audit_logs(self, project_id: Optional[str] = None) -> List[AuditLogEntry]:
        if project_id:
            return [l for l in self._audit_logs if l.project_id == project_id]
        return self._audit_logs


rbac_service = RBACService()
