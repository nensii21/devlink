"""
Administrative account-state transitions.

``is_active`` and ``is_verified`` are the two flags that decide whether a person
can sign in and what the platform is willing to vouch for about them. Both used
to be flipped by ``UserService`` setters that took a ``User`` and set an
attribute -- no actor, no record, and nothing to stop a caller from applying a
transition that had already been applied.

Everything an administrator can do to somebody else's account now goes through
this module, so that three things are true of every transition:

* an actor is named, and the transition refuses to run without one;
* the transition is recorded in the audit log with both parties on it;
* the side effects that make the state change *mean* something happen in the
  same unit of work as the flag.

That last point is the one worth spelling out. Clearing ``is_active`` stops
:meth:`AuthService.login` from issuing new tokens, but it does nothing to the
tokens already out there: ``POST /api/auth/refresh`` reads the refresh-token row
and the JWT, neither of which consults ``users.is_active``. A "disabled" account
therefore went on minting access tokens for the remaining lifetime of its
refresh token. Deactivation revokes them here.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction
from app.models.user import User
from app.services.audit_log_service import AuditLogService
from app.services.refresh_token_service import RefreshTokenService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequestContext:
    """Where a transition came from.

    Optional throughout -- a transition driven by a management command has no
    request behind it -- but when the router has these they belong on the audit
    row, because "an admin deactivated this account" is a much weaker record
    than "an admin deactivated this account from this address at this time".
    """

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None

    @classmethod
    def from_request(cls, request) -> "RequestContext":
        if request is None:
            return cls()
        client = getattr(request, "client", None)
        return cls(
            ip_address=getattr(client, "host", None) if client else None,
            user_agent=request.headers.get("user-agent"),
            request_method=request.method,
            request_path=str(request.url.path),
        )


class AccountStateService:
    """Activate, deactivate and verify accounts on an administrator's behalf."""

    # ------------------------------------------------------------------
    # Guards
    # ------------------------------------------------------------------

    @staticmethod
    def assert_not_self(actor: User, target: User, operation: str) -> None:
        """Refuse a transition an administrator applies to their own account.

        Deactivating yourself is the interesting case: it takes effect
        immediately, ``get_current_active_user`` then rejects your own token,
        and you cannot call ``/activate`` to undo it. Without a second admin
        that is an unrecoverable state, reached by a single mis-pasted id.

        The other two transitions are harmless in themselves, but an admin
        self-verifying is precisely the audit-log entry a reviewer wants to be
        impossible rather than merely visible.
        """
        if actor.id == target.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You cannot {operation} your own account.",
            )

    @staticmethod
    def assert_not_deleted(target: User) -> None:
        """A soft-deleted account is not a thing to activate or verify.

        ``UserService.get_user`` already filters ``deleted_at``, so a caller
        that went through it cannot get here. Callers that used
        ``get_user_including_deleted`` can, and restoring is
        ``POST /{user_id}/restore``'s job, not a side effect of activation.
        """
        if getattr(target, "deleted_at", None) is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account is deleted. Restore it before changing its state.",
            )

    # ------------------------------------------------------------------
    # Transitions
    # ------------------------------------------------------------------

    @classmethod
    def activate(
        cls,
        db: Session,
        *,
        actor: User,
        target: User,
        reason: Optional[str] = None,
        context: Optional[RequestContext] = None,
    ) -> User:
        """Re-enable a disabled account.

        Idempotent by design: re-activating an already-active account is a
        no-op that still returns the user, because the caller's intent
        ("this account should be usable") is satisfied either way. It does not
        write an audit row in that case -- a log full of transitions that
        changed nothing is a log nobody reads.
        """
        cls.assert_not_deleted(target)

        if target.is_active:
            return target

        target.is_active = True
        db.add(target)
        db.flush()

        cls._record(
            db,
            actor=actor,
            target=target,
            action=AuditAction.USER_ACTIVATED,
            description=f"Activated account '{target.username}'",
            old_values={"is_active": False},
            new_values={"is_active": True},
            reason=reason,
            context=context,
        )

        db.commit()
        db.refresh(target)

        logger.info(
            "account_activated target=%s actor=%s",
            target.id,
            actor.id,
        )
        return target

    @classmethod
    def deactivate(
        cls,
        db: Session,
        *,
        actor: User,
        target: User,
        reason: Optional[str] = None,
        context: Optional[RequestContext] = None,
    ) -> User:
        """Disable an account and cut its live sessions.

        The token revocation is the part that makes this a real suspension
        rather than a flag. It runs even when the account was already inactive,
        because an account can be marked inactive by one code path and still
        hold valid refresh tokens issued before it -- re-running the
        revocation is cheap and closes that window.
        """
        cls.assert_not_self(actor, target, "deactivate")
        cls.assert_not_deleted(target)

        was_active = target.is_active
        target.is_active = False
        db.add(target)
        db.flush()

        RefreshTokenService.revoke_all_tokens(db, target.id)

        if was_active:
            cls._record(
                db,
                actor=actor,
                target=target,
                action=AuditAction.USER_SUSPENDED,
                description=f"Deactivated account '{target.username}'",
                old_values={"is_active": True},
                new_values={"is_active": False},
                reason=reason,
                context=context,
            )

        db.commit()
        db.refresh(target)

        logger.info(
            "account_deactivated target=%s actor=%s was_active=%s",
            target.id,
            actor.id,
            was_active,
        )
        return target

    @classmethod
    def mark_email_verified(
        cls,
        db: Session,
        *,
        actor: User,
        target: User,
        reason: Optional[str] = None,
        context: Optional[RequestContext] = None,
    ) -> User:
        """Mark an address verified without the confirmation email.

        This exists for support: somebody whose mail provider silently drops
        the confirmation link needs a way through. It is not the normal path --
        that is ``POST /api/auth/verify-email`` with a token -- and the audit
        row says which one was used, because ``is_verified`` is what renders
        the badge on every post the account writes.
        """
        cls.assert_not_self(actor, target, "verify")
        cls.assert_not_deleted(target)

        if target.is_verified:
            return target

        target.is_verified = True
        db.add(target)
        db.flush()

        cls._record(
            db,
            actor=actor,
            target=target,
            action=AuditAction.USER_EMAIL_VERIFIED,
            description=(
                f"Marked '{target.username}' email-verified without a confirmation token"
            ),
            old_values={"is_verified": False},
            new_values={"is_verified": True},
            reason=reason,
            context=context,
        )

        db.commit()
        db.refresh(target)

        logger.info(
            "account_email_verified_by_admin target=%s actor=%s",
            target.id,
            actor.id,
        )
        return target

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _record(
        db: Session,
        *,
        actor: User,
        target: User,
        action: AuditAction,
        description: str,
        old_values: dict,
        new_values: dict,
        reason: Optional[str],
        context: Optional[RequestContext],
    ) -> None:
        """Write the audit row for a transition.

        Deliberately not wrapped in a ``try``: if the audit write fails the
        transition should fail with it. A state change that silently did not
        get recorded is worse than one that did not happen.
        """
        ctx = context or RequestContext()
        AuditLogService.create_log(
            db=db,
            actor_id=actor.id,
            action=action,
            entity_type="user",
            entity_id=str(target.id),
            target_user_id=target.id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata_info={"reason": reason} if reason else None,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            request_method=ctx.request_method,
            request_path=ctx.request_path,
        )


def resolve_target_user(db: Session, user_id: uuid.UUID) -> User:
    """Load the subject of a transition, or 404.

    Goes through ``db.get`` rather than ``UserService.get_user`` on purpose:
    that one is decorated with ``@cached``, and reading an account's flags from
    a cache immediately before writing them is how you get a transition applied
    to a stale copy.
    """
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
