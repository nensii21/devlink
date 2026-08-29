"""
Request bodies for the administrative account-state routes.

Each of ``/activate``, ``/deactivate`` and ``/verify`` accepts an optional
reason. It is optional so the routes stay callable with an empty body -- they
took no body at all before -- but when it is supplied it lands on the audit row,
which is the difference between a log that records *what* happened and one that
records why.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AccountStateChangeRequest(BaseModel):
    """Optional context an administrator can attach to a state transition."""

    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description=(
            "Why this transition is being applied. Stored on the audit log "
            "entry; not shown to the affected user."
        ),
        examples=["Spam reports from three separate projects (see ticket 4412)"],
    )

    @field_validator("reason")
    @classmethod
    def _blank_is_absent(cls, value: Optional[str]) -> Optional[str]:
        """Treat a whitespace-only reason as no reason.

        Otherwise a client that always sends the field ends up writing
        ``{"reason": "  "}`` onto every audit row, which reads as "a reason was
        given" to anything scanning the log.
        """
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class AccountStateResponse(BaseModel):
    """Minimal projection of the flags a transition touches.

    Not currently used by the routes -- they return the full ``UserResponse``
    for backwards compatibility -- but it is what an admin console wants when
    it only needs to reconcile the two booleans it just changed.
    """

    id: str
    username: str
    is_active: bool
    is_verified: bool
