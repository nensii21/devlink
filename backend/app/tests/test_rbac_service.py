"""
Comprehensive Unit tests for Advanced Role-Based Access Control (RBAC).
"""

import pytest
from app.services.rbac_service import (
    RBACService,
    CustomRole,
    DEFAULT_PERMISSIONS,
    rbac_service
)


@pytest.fixture
def rbac():
    return RBACService()


def test_default_permissions_owner(rbac):
    perms = rbac.get_role_permissions("proj_1", "owner")
    assert "project:admin" in perms
    assert rbac.has_permission("proj_1", "owner", "project:write")
    assert rbac.has_permission("proj_1", "owner", "any:arbitrary:perm")


def test_default_permissions_contributor(rbac):
    perms = rbac.get_role_permissions("proj_1", "contributor")
    assert "project:read" in perms
    assert "code:review" in perms
    assert "project:admin" not in perms
    assert not rbac.has_permission("proj_1", "contributor", "project:admin")
    assert not rbac.has_permission("proj_1", "contributor", "code:merge")


def test_custom_role_registration_and_evaluation(rbac):
    custom = CustomRole(
        name="triage",
        project_id="proj_100",
        permissions={"issue:label", "issue:close", "project:read"}
    )
    rbac.register_custom_role(custom)
    assert rbac.has_permission("proj_100", "triage", "issue:label")
    assert rbac.has_permission("proj_100", "triage", "issue:close")
    assert not rbac.has_permission("proj_100", "triage", "code:merge")


def test_custom_role_inheritance(rbac):
    custom = CustomRole(
        name="lead_reviewer",
        project_id="proj_200",
        permissions={"code:approve", "code:bypass_rules"},
        inherits_from="contributor"
    )
    rbac.register_custom_role(custom)
    assert rbac.has_permission("proj_200", "lead_reviewer", "code:approve")
    assert rbac.has_permission("proj_200", "lead_reviewer", "code:review")  # inherited
    assert rbac.has_permission("proj_200", "lead_reviewer", "project:read")  # inherited
    assert not rbac.has_permission("proj_200", "lead_reviewer", "project:admin")


def test_audit_log_recording(rbac):
    rbac.has_permission("proj_500", "viewer", "code:merge", user_id="user_123")
    rbac.has_permission("proj_500", "owner", "code:merge", user_id="user_admin")

    logs = rbac.get_audit_logs("proj_500")
    assert len(logs) == 2
    assert logs[0].granted is False
    assert logs[0].user_id == "user_123"
    assert logs[1].granted is True
    assert logs[1].user_id == "user_admin"


def test_has_permission_case_insensitivity(rbac):
    assert rbac.has_permission("proj_1", "OWNER", "project:write")
    assert rbac.has_permission("proj_1", "Maintainer", "code:merge")


def test_custom_role_unknown_role_fallback(rbac):
    perms = rbac.get_role_permissions("proj_1", "completely_unknown_role")
    assert perms == set()
    assert not rbac.has_permission("proj_1", "completely_unknown_role", "project:read")


def test_circular_inheritance_safety(rbac):
    role_a = CustomRole(name="role_a", project_id="proj_circ", permissions={"perm:a"}, inherits_from="viewer")
    rbac.register_custom_role(role_a)
    assert rbac.has_permission("proj_circ", "role_a", "perm:a")
    assert rbac.has_permission("proj_circ", "role_a", "project:read")
