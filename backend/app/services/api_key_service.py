from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.api_key import (
    ALL_ALLOWED_SCOPES,
    ApiKeyCreateRequest,
    ApiKeyUpdateRequest,
)
from app.services.audit_log_service import AuditLogService


class ApiKeyService:
    """
    Business logic for API Key Management (#605)
    """

    @staticmethod
    def generate_raw_key() -> Tuple[str, str, str]:
        """Generate prefix, raw token secret, and SHA-256 hash."""
        secret = secrets.token_urlsafe(32)
        raw_key = f"dlk_live_{secret}"
        prefix = raw_key[:14]  # e.g., 'dlk_live_XXXXX'
        # lgtm[py/weak-sensitive-data-hashing]
        hashed_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return raw_key, prefix, hashed_key

    @classmethod
    def validate_scopes(cls, scopes: List[str]) -> List[str]:
        """Validate that provided scope strings are recognized."""
        cleaned = [s.strip().lower() for s in scopes if s and s.strip()]
        for s in cleaned:
            if s not in ALL_ALLOWED_SCOPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid scope '{s}'. Allowed scopes are: {sorted(list(ALL_ALLOWED_SCOPES))}",
                )
        return cleaned

    @classmethod
    def create_api_key(
        cls,
        db: Session,
        actor: User,
        payload: ApiKeyCreateRequest,
    ) -> Tuple[str, ApiKey]:
        """
        Create a new secure API Key for user or organization.
        Returns (raw_key, api_key_orm).
        """
        validated_scopes = cls.validate_scopes(payload.scopes)
        raw_key, prefix, hashed_key = cls.generate_raw_key()

        # Calculate expiration
        expires_at = payload.expires_at
        if payload.expires_in_days is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=payload.expires_in_days
            )

        api_key = ApiKey(
            id=uuid.uuid4(),
            user_id=actor.id if not payload.organization_id else None,
            organization_id=payload.organization_id,
            created_by_id=actor.id,
            name=payload.name,
            prefix=prefix,
            hashed_key=hashed_key,
            scopes=validated_scopes,
            expires_at=expires_at,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

        db.add(api_key)
        db.flush()
        db.refresh(api_key)

        # Audit log
        AuditLogService.create_log(
            db=db,
            actor_id=actor.id,
            action=AuditAction.API_KEY_CREATED,
            entity_type="api_key",
            entity_id=str(api_key.id),
            organization_id=payload.organization_id,
            description=f"Created API Key '{api_key.name}' (Prefix: {prefix})",
            new_values={
                "name": api_key.name,
                "prefix": prefix,
                "scopes": validated_scopes,
            },
        )
        db.commit()

        return raw_key, api_key

    @classmethod
    def list_api_keys(
        cls,
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """List API keys for user or organization."""
        stmt = select(ApiKey)

        if organization_id:
            stmt = stmt.where(ApiKey.organization_id == organization_id)
        elif user_id:
            stmt = stmt.where(ApiKey.user_id == user_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide user_id or organization_id",
            )

        # Exclude revoked/deleted keys or order active first
        stmt = stmt.order_by(ApiKey.created_at.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        offset = (page - 1) * limit
        items = list(db.scalars(stmt.offset(offset).limit(limit)))
        pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @classmethod
    def get_api_key(cls, db: Session, key_id: uuid.UUID) -> ApiKey:
        key = db.get(ApiKey, key_id)
        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found"
            )
        return key

    @classmethod
    def update_api_key(
        cls,
        db: Session,
        key_id: uuid.UUID,
        payload: ApiKeyUpdateRequest,
        actor: User,
    ) -> ApiKey:
        key = cls.get_api_key(db, key_id)

        # Authorization check
        if key.user_id and key.user_id != actor.id and not actor.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        if payload.name is not None:
            key.name = payload.name
        if payload.scopes is not None:
            key.scopes = cls.validate_scopes(payload.scopes)
        if payload.expires_at is not None:
            key.expires_at = payload.expires_at
        if payload.is_active is not None:
            key.is_active = payload.is_active

        key.updated_at = datetime.now(timezone.utc)
        db.add(key)
        db.commit()
        db.refresh(key)

        AuditLogService.create_log(
            db=db,
            actor_id=actor.id,
            action=AuditAction.API_KEY_UPDATED,
            entity_type="api_key",
            entity_id=str(key.id),
            organization_id=key.organization_id,
            description=f"Updated API Key '{key.name}'",
        )

        return key

    @classmethod
    def regenerate_api_key(
        cls,
        db: Session,
        key_id: uuid.UUID,
        actor: User,
    ) -> Tuple[str, ApiKey]:
        """
        Regenerates token secret for an existing key.
        Invalidates old key hash and returns new raw_key once.
        """
        key = cls.get_api_key(db, key_id)

        if key.user_id and key.user_id != actor.id and not actor.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        raw_key, prefix, hashed_key = cls.generate_raw_key()
        key.prefix = prefix
        key.hashed_key = hashed_key
        key.last_used_at = None
        key.is_active = True
        key.updated_at = datetime.now(timezone.utc)

        db.add(key)
        db.commit()
        db.refresh(key)

        AuditLogService.create_log(
            db=db,
            actor_id=actor.id,
            action=AuditAction.API_KEY_REGENERATED,
            entity_type="api_key",
            entity_id=str(key.id),
            organization_id=key.organization_id,
            description=f"Regenerated API Key secret for '{key.name}' (New Prefix: {prefix})",
        )

        return raw_key, key

    @classmethod
    def revoke_api_key(
        cls,
        db: Session,
        key_id: uuid.UUID,
        actor: User,
    ) -> ApiKey:
        """Revoke API Key immediately."""
        key = cls.get_api_key(db, key_id)

        if key.user_id and key.user_id != actor.id and not actor.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        key.is_active = False
        key.updated_at = datetime.now(timezone.utc)
        db.add(key)
        db.commit()
        db.refresh(key)

        AuditLogService.create_log(
            db=db,
            actor_id=actor.id,
            action=AuditAction.API_KEY_REVOKED,
            entity_type="api_key",
            entity_id=str(key.id),
            organization_id=key.organization_id,
            description=f"Revoked API Key '{key.name}' (Prefix: {key.prefix})",
        )

        return key

    @classmethod
    def authenticate_api_key(
        cls,
        db: Session,
        raw_key: str,
        required_scope: Optional[str] = None,
    ) -> ApiKey:
        """
        Authenticate an incoming raw API key string, check expiration & active status,
        enforce required scope, and update last_used_at timestamp.
        """
        if not raw_key or not raw_key.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API Key header",
            )

        # lgtm[py/weak-sensitive-data-hashing]
        hashed_input = hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()

        key = db.scalar(
            select(ApiKey).where(
                ApiKey.hashed_key == hashed_input,
                ApiKey.is_active.is_(True),
            )
        )

        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked API Key",
            )

        # Expiration Check
        if key.expires_at and key.expires_at < datetime.now(timezone.utc):
            key.is_active = False
            db.add(key)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key has expired",
            )

        # Scope Validation
        if required_scope:
            scopes = key.scopes or []
            if "full_access" not in scopes and required_scope not in scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API Key lacks required scope '{required_scope}'",
                )

        # Update last_used_at
        key.last_used_at = datetime.now(timezone.utc)
        db.add(key)
        db.commit()

        return key
