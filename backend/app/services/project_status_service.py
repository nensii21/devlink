"""
Project Status Transition Validation Service (#232)
"""

from __future__ import annotations

from typing import Dict, Set

from fastapi import HTTPException, status

from app.models.project import ProjectStatus

# State Machine Transition Rules Matrix
ALLOWED_PROJECT_STATUS_TRANSITIONS: Dict[ProjectStatus, Set[ProjectStatus]] = {
    ProjectStatus.DRAFT: {
        ProjectStatus.RECRUITING,
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.RECRUITING: {
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.PAUSED,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.IN_PROGRESS: {
        ProjectStatus.COMPLETED,
        ProjectStatus.PAUSED,
        ProjectStatus.RECRUITING,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.PAUSED: {
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.RECRUITING,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.COMPLETED: {
        ProjectStatus.ARCHIVED,
        ProjectStatus.IN_PROGRESS,
    },
    ProjectStatus.ARCHIVED: {
        ProjectStatus.DRAFT,
    },
}

STATUS_ALIASES = {
    "active": ProjectStatus.IN_PROGRESS,
    "open": ProjectStatus.RECRUITING,
    "closed": ProjectStatus.COMPLETED,
}


def _parse_status_enum(val: ProjectStatus | str) -> ProjectStatus:
    if isinstance(val, ProjectStatus):
        return val
    raw = (val.value if hasattr(val, "value") else str(val)).lower()
    if "." in raw:
        raw = raw.split(".")[-1]
    if raw in STATUS_ALIASES:
        return STATUS_ALIASES[raw]
    return ProjectStatus(raw)


class ProjectStatusService:
    @staticmethod
    def get_allowed_next_statuses(current_status: ProjectStatus | str) -> list[str]:
        """
        Returns list of allowed destination statuses from current_status.
        """
        try:
            curr_enum = _parse_status_enum(current_status)
        except ValueError:
            return []

        allowed = ALLOWED_PROJECT_STATUS_TRANSITIONS.get(curr_enum, set())
        return sorted([s.value for s in allowed])

    @staticmethod
    def validate_status_transition(
        current_status: ProjectStatus | str,
        new_status: ProjectStatus | str,
    ) -> None:
        """
        Validates if transitioning from current_status to new_status is permitted.
        Raises HTTPException 400 Bad Request if the transition is invalid.
        """
        try:
            curr_enum = _parse_status_enum(current_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid current project status '{current_status}'.",
            )

        try:
            new_enum = _parse_status_enum(new_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target project status '{new_status}'.",
            )

        # Self-transition is a valid no-op
        if curr_enum == new_enum:
            return

        allowed = ALLOWED_PROJECT_STATUS_TRANSITIONS.get(curr_enum, set())
        if new_enum not in allowed:
            allowed_list = sorted([s.value for s in allowed])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid project status transition from '{curr_enum.value}' to '{new_enum.value}'. "
                    f"Allowed target status(es) from '{curr_enum.value}': {allowed_list}"
                ),
            )
