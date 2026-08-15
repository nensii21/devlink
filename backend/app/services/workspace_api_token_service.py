from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction
from app.models.workspace_api_token import WorkspaceApiToken
from app.schemas.workspace_api_token import WorkspaceApiTokenCreate
from app.services.audit_log_service import AuditLogService


class WorkspaceApiTokenService:
    """
    Business logic for Workspace API Tokens operations.
    """

    @staticmethod
    def create_token(
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        schema: WorkspaceApiTokenCreate,
    ) -> tuple[str, WorkspaceApiToken]:
        # Generate cryptographically secure random token secret
        # Token starts with "dl_tok_" for easy recognition
        secret_part = secrets.token_urlsafe(32)
        raw_token = f"dl_tok_{secret_part}"

        # Prefix is the first 12 characters (e.g. dl_tok_xxxx)
        prefix = raw_token[:12]

        # Compute SHA-256 hash to store securely
        # lgtm[py/weak-sensitive-data-hashing]
        hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        # Calculate expiration date
        expires_at = None
        if schema.expires_in_days is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=schema.expires_in_days
            )

        # Standardize scopes (comma-separated)
        scopes_str = ",".join(schema.scopes)

        # Create WorkspaceApiToken record
        db_token = WorkspaceApiToken(
            organization_id=organization_id,
            created_by_id=user_id,
            name=schema.name,
            hashed_token=hashed_token,
            prefix=prefix,
            scopes=scopes_str,
            expires_at=expires_at,
            is_active=True,
        )

        db.add(db_token)
        db.flush()
        db.refresh(db_token)

        # Log audit entry
        AuditLogService.create_log(
            db,
            user_id=user_id,
            action=AuditAction.API_TOKEN_CREATED,
            resource_type="workspace_api_token",
            resource_id=str(db_token.id),
            description=f"Created Workspace API Token '{db_token.name}' (Prefix: {db_token.prefix})",
        )
        db.commit()

        return raw_token, db_token

    @staticmethod
    def list_tokens(db: Session, organization_id: uuid.UUID) -> list[WorkspaceApiToken]:
        stmt = select(WorkspaceApiToken).where(
            WorkspaceApiToken.organization_id == organization_id,
            WorkspaceApiToken.is_active == True,
        )
        tokens = list(db.scalars(stmt))

        # Filter out expired tokens dynamically
        now = datetime.now(timezone.utc)
        active_tokens = []
        for t in tokens:
            if t.expires_at and t.expires_at < now:
                t.is_active = False
                db.flush()
            else:
                active_tokens.append(t)
        db.commit()

        return active_tokens

    @staticmethod
    def revoke_token(
        db: Session,
        organization_id: uuid.UUID,
        token_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        stmt = select(WorkspaceApiToken).where(
            WorkspaceApiToken.id == token_id,
            WorkspaceApiToken.organization_id == organization_id,
            WorkspaceApiToken.is_active == True,
        )
        token = db.scalar(stmt)
        if not token:
            return False

        token.is_active = False
        db.flush()

        # Log audit entry
        AuditLogService.create_log(
            db,
            user_id=user_id,
            action=AuditAction.API_TOKEN_REVOKED,
            resource_type="workspace_api_token",
            resource_id=str(token.id),
            description=f"Revoked Workspace API Token '{token.name}' (Prefix: {token.prefix})",
        )
        db.commit()

        return True

    @staticmethod
    def authenticate_api_token(db: Session, raw_token: str) -> WorkspaceApiToken | None:
        if not raw_token:
            return None

        # Compute SHA-256 hash of the incoming token
        # lgtm[py/weak-sensitive-data-hashing]
        hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        # Query active token
        stmt = select(WorkspaceApiToken).where(
            WorkspaceApiToken.hashed_token == hashed_token,
            WorkspaceApiToken.is_active == True,
        )
        token_info = db.scalar(stmt)
        if not token_info:
            return None

        # Check expiration
        if token_info.expires_at and token_info.expires_at < datetime.now(timezone.utc):
            token_info.is_active = False
            db.flush()
            db.commit()
            return None

        # Update last_used_at
        token_info.last_used_at = datetime.now(timezone.utc)
        db.flush()

        # Log audit entry (API access)
        AuditLogService.create_log(
            db,
            user_id=token_info.created_by_id,
            action=AuditAction.API_ACCESS,
            resource_type="workspace_api_token",
            resource_id=str(token_info.id),
            description=f"API access via token: {token_info.name}",
        )
        db.commit()

        return token_info
