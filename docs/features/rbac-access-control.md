# RBAC Access Control Service

DevLink relies on a robust Policy Evaluation Engine to ensure that resources are accessed securely and contextually. The Role-Based Access Control (RBAC) service resolves multi-level role hierarchies and enforces explicit Deny/Allow conditions globally.

## Core Concepts

### 1. Custom Roles & DAG Inheritance
Roles are defined by the `CustomRole` dataclass. Crucially, a role can inherit from any number of other CustomRoles. The evaluation engine resolves this inheritance dynamically via a Depth-First Search (DFS) algorithm, generating a directed acyclic graph (DAG) of privileges.
*Example: `admin` -> inherits from `manager` -> inherits from `member`.*

### 2. Policy Rules
Each role contains an array of `PolicyRule` objects determining exact constraints:
- **Effect**: `ALLOW` or `DENY`. Explicit `DENY` rules always override `ALLOW` rules, guaranteeing airtight security fail-safes.
- **Actions**: The operational intents. Supports wildcards (e.g. `project:*` vs `project:delete`).
- **Resources**: The precise target. Supports wildcards (e.g. `proj_3:folder/*`).
- **Conditions**: Context-specific requirements, such as requiring MFA to be active (`{"mfa_enabled": True}`).

### 3. Contextual Evaluation
During execution, authorization is checked using `evaluate_access(project_id, user_role, action, resource, context)`. The engine iterates through the fully unrolled policy tree and validates if the request context matches the `PolicyRule` conditions.

### 4. Audit Trail
Every authorization request routed through `evaluate_access()` is automatically recorded in the Audit Log, preserving the exact `matched_rule_id`, action, and granted state.

## Usage Example
```python
from app.services.rbac_service import rbac_service, CustomRole, PolicyRule, PolicyEffect

# Define a conditional role
contractor = CustomRole(
    name="contractor",
    project_id="proj_xyz",
    policies=[
        PolicyRule(
            rule_id="allow_write",
            effect=PolicyEffect.ALLOW,
            actions=["project:write"],
            resources=["proj_xyz:public/*"],
            conditions={"is_active": True}
        ),
        PolicyRule(
            rule_id="deny_delete",
            effect=PolicyEffect.DENY,
            actions=["*:delete"],
            resources=["*"]
        )
    ]
)
rbac_service.register_custom_role(contractor)

# Evaluate
is_allowed = rbac_service.evaluate_access(
    project_id="proj_xyz",
    user_role="contractor",
    action="project:write",
    resource="proj_xyz:public/doc.txt",
    context={"is_active": True}
)
# Returns True
```
