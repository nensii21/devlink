from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.oauth_linking import (
    OAuthProviderItem,
    OAuthProvidersListResponse,
)

VALID_PROVIDERS = {"github", "google", "gitlab", "linkedin"}


class OAuthLinkingService:
    @staticmethod
    def get_provider_column(provider: str):
        provider_lower = provider.lower()
        if provider_lower == "github":
            return User.github_id
        elif provider_lower == "google":
            return User.google_id
        elif provider_lower == "gitlab":
            return User.gitlab_id
        elif provider_lower == "linkedin":
            return User.linkedin_id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}. Supported providers: {', '.join(sorted(VALID_PROVIDERS))}",
            )

    @classmethod
    def get_linked_providers(
        cls, db: Session, user: User
    ) -> OAuthProvidersListResponse:
        has_password = bool(user.password_hash and len(user.password_hash) > 0)

        provider_map = [
            ("github", user.github_id),
            ("google", user.google_id),
            ("gitlab", user.gitlab_id),
            ("linkedin", user.linkedin_id),
        ]

        items = []
        linked_count = 0

        for name, pid in provider_map:
            is_linked = bool(pid and str(pid).strip())
            if is_linked:
                linked_count += 1
            items.append(
                OAuthProviderItem(
                    provider=name,
                    is_linked=is_linked,
                    provider_user_id=pid if is_linked else None,
                )
            )

        return OAuthProvidersListResponse(
            has_password=has_password,
            linked_count=linked_count,
            providers=items,
        )

    @classmethod
    def link_oauth_account(
        cls,
        db: Session,
        user: User,
        provider: str,
        provider_user_id: str,
    ) -> OAuthProvidersListResponse:
        provider_lower = provider.lower()
        if provider_lower not in VALID_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider '{provider}'. Must be one of: {', '.join(sorted(VALID_PROVIDERS))}",
            )

        column = cls.get_provider_column(provider_lower)

        # Check if provider account is already linked to ANOTHER user
        existing_owner = (
            db.query(User)
            .filter(column == provider_user_id, User.id != user.id)
            .first()
        )
        if existing_owner:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"This {provider_lower.capitalize()} account is already linked to another DevLink user.",
            )

        # Update user's provider ID
        setattr(user, f"{provider_lower}_id", provider_user_id)
        db.commit()
        db.refresh(user)

        return cls.get_linked_providers(db, user)

    @classmethod
    def unlink_oauth_account(
        cls,
        db: Session,
        user: User,
        provider: str,
    ) -> OAuthProvidersListResponse:
        provider_lower = provider.lower()
        if provider_lower not in VALID_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider '{provider}'. Must be one of: {', '.join(sorted(VALID_PROVIDERS))}",
            )

        current_linked_id = getattr(user, f"{provider_lower}_id", None)
        if not current_linked_id:
            # Already unlinked
            return cls.get_linked_providers(db, user)

        # Safety Check: ensure at least one authentication method remains
        has_password = bool(user.password_hash and len(user.password_hash) > 0)
        provider_map = [
            ("github", user.github_id),
            ("google", user.google_id),
            ("gitlab", user.gitlab_id),
            ("linkedin", user.linkedin_id),
        ]
        total_linked_oauth = sum(
            1 for name, pid in provider_map if pid and str(pid).strip()
        )

        if not has_password and total_linked_oauth <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unlink your only authentication method. Please set a password or link another OAuth provider first.",
            )

        # Unlink provider
        setattr(user, f"{provider_lower}_id", None)
        db.commit()
        db.refresh(user)

        return cls.get_linked_providers(db, user)
