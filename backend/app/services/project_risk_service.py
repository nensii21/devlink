from typing import List
from app.schemas.project_risk import ProjectRiskInput, ProjectRiskReport, RiskItem

class ProjectRiskService:
    @staticmethod
    def analyze_project(payload: ProjectRiskInput) -> ProjectRiskReport:
        risks: List[RiskItem] = []

        # 1. Check Unrealistic Timeline
        if payload.timeline_days and payload.timeline_days < 7:
            risks.append(RiskItem(
                category="Timeline",
                severity="High",
                message=f"Timeline of {payload.timeline_days} days is extremely short for project delivery.",
                suggestion="Extend the timeline to at least 14-30 days to account for standard development cycles."
            ))

        # 2. Check Missing Required Roles
        if not payload.required_roles or len(payload.required_roles) == 0:
            risks.append(RiskItem(
                category="Roles",
                severity="Medium",
                message="No required contributor roles specified.",
                suggestion="Specify key roles (e.g., Frontend Developer, Backend Developer) to attract qualified contributors."
            ))

        # 3. Check Incomplete Requirements / Description
        if len(payload.description.strip()) < 50:
            risks.append(RiskItem(
                category="Requirements",
                severity="High",
                message="Project description is too short or lacks detailed requirements.",
                suggestion="Expand the description to include technical architecture, goals, and core deliverables."
            ))

        # 4. Check Undefined Scope
        if not payload.scope or len(payload.scope.strip()) < 10:
            risks.append(RiskItem(
                category="Scope",
                severity="Medium",
                message="Project scope is undefined or vague.",
                suggestion="Clearly outline what is included and excluded in the initial release."
            ))

        # Calculate risk score & publishable status
        risk_score = min(100.0, len(risks) * 25.0)
        is_publishable = len([r for r in risks if r.severity in ["High", "Critical"]]) == 0

        return ProjectRiskReport(
            is_publishable=is_publishable,
            risk_score=risk_score,
            risks=risks
        )
    