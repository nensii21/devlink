import pytest
from app.services.rbac_service import (
    RBACService,
    CustomRole,
    PolicyRule,
    PolicyEffect,
    rbac_service
)


@pytest.fixture
def rbac():
    return RBACService()


def test_hierarchical_inheritance(rbac):
    # Setup DAG: admin -> manager -> member
    member = CustomRole(
        name="member",
        project_id="proj_1",
        policies=[
            PolicyRule(rule_id="r1", effect=PolicyEffect.ALLOW, actions=["project:read"], resources=["proj_1:*"])
        ]
    )
    manager = CustomRole(
        name="manager",
        project_id="proj_1",
        inherits_from=["member"],
        policies=[
            PolicyRule(rule_id="r2", effect=PolicyEffect.ALLOW, actions=["project:write"], resources=["proj_1:*"])
        ]
    )
    admin = CustomRole(
        name="admin",
        project_id="proj_1",
        inherits_from=["manager"],
        policies=[
            PolicyRule(rule_id="r3", effect=PolicyEffect.ALLOW, actions=["project:delete"], resources=["proj_1:*"])
        ]
    )
    
    rbac.register_custom_role(member)
    rbac.register_custom_role(manager)
    rbac.register_custom_role(admin)
    
    # Member access
    assert rbac.evaluate_access("proj_1", "member", "project:read", "proj_1:resource_a") is True
    assert rbac.evaluate_access("proj_1", "member", "project:write", "proj_1:resource_a") is False
    
    # Manager access
    assert rbac.evaluate_access("proj_1", "manager", "project:read", "proj_1:resource_a") is True
    assert rbac.evaluate_access("proj_1", "manager", "project:write", "proj_1:resource_a") is True
    assert rbac.evaluate_access("proj_1", "manager", "project:delete", "proj_1:resource_a") is False
    
    # Admin access
    assert rbac.evaluate_access("proj_1", "admin", "project:read", "proj_1:resource_a") is True
    assert rbac.evaluate_access("proj_1", "admin", "project:write", "proj_1:resource_a") is True
    assert rbac.evaluate_access("proj_1", "admin", "project:delete", "proj_1:resource_a") is True


def test_explicit_deny_overrides_allow(rbac):
    role = CustomRole(
        name="contractor",
        project_id="proj_2",
        policies=[
            PolicyRule(rule_id="allow_all", effect=PolicyEffect.ALLOW, actions=["*"], resources=["*"]),
            PolicyRule(rule_id="deny_delete", effect=PolicyEffect.DENY, actions=["*:delete"], resources=["*"])
        ]
    )
    rbac.register_custom_role(role)
    
    assert rbac.evaluate_access("proj_2", "contractor", "project:write", "proj_2:res1") is True
    assert rbac.evaluate_access("proj_2", "contractor", "project:delete", "proj_2:res1") is False


def test_resource_scoping(rbac):
    role = CustomRole(
        name="scoped_user",
        project_id="proj_3",
        policies=[
            PolicyRule(rule_id="r1", effect=PolicyEffect.ALLOW, actions=["project:write"], resources=["proj_3:folder1/*"])
        ]
    )
    rbac.register_custom_role(role)
    
    # Granted in folder1
    assert rbac.evaluate_access("proj_3", "scoped_user", "project:write", "proj_3:folder1/file.txt") is True
    # Denied in folder2
    assert rbac.evaluate_access("proj_3", "scoped_user", "project:write", "proj_3:folder2/file.txt") is False


def test_conditional_evaluation(rbac):
    role = CustomRole(
        name="conditional_user",
        project_id="proj_4",
        policies=[
            PolicyRule(
                rule_id="r1", 
                effect=PolicyEffect.ALLOW, 
                actions=["project:write"], 
                resources=["*"],
                conditions={"is_active": True, "mfa_enabled": True}
            )
        ]
    )
    rbac.register_custom_role(role)
    
    # Fails due to missing context
    assert rbac.evaluate_access("proj_4", "conditional_user", "project:write", "res1") is False
    
    # Fails due to incorrect context
    assert rbac.evaluate_access("proj_4", "conditional_user", "project:write", "res1", context={"is_active": True, "mfa_enabled": False}) is False
    
    # Passes with correct context
    assert rbac.evaluate_access("proj_4", "conditional_user", "project:write", "res1", context={"is_active": True, "mfa_enabled": True}) is True


def test_audit_logs(rbac):
    role = CustomRole(
        name="audited_user",
        project_id="proj_5",
        policies=[
            PolicyRule(rule_id="r1", effect=PolicyEffect.ALLOW, actions=["read"], resources=["res1"])
        ]
    )
    rbac.register_custom_role(role)
    
    rbac.evaluate_access("proj_5", "audited_user", "read", "res1", user_id="u1")
    rbac.evaluate_access("proj_5", "audited_user", "write", "res1", user_id="u1")
    
    logs = rbac.get_audit_logs("proj_5")
    assert len(logs) == 2
    assert logs[0].granted is True
    assert logs[0].matched_rule_id == "r1"
    assert logs[1].granted is False
    assert logs[1].matched_rule_id is None
