from __future__ import annotations

import logging
import re
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, selectinload

from app.core.rbac import ORG_MANAGE_PLUGINS, has_org_permission
from app.models.plugin import (
    Plugin,
    PluginInstallation,
    PluginStatus,
    PluginType,
)
from app.models.user import User
from app.schemas.plugin import (
    PluginCreate,
    PluginDispatchItem,
    PluginEventDispatchResult,
    PluginInstallationCreate,
    PluginInstallationUpdate,
    PluginUpdate,
)

logger = logging.getLogger(__name__)


class PluginService:
    """
    Business logic for DevLink Plugin & Extension System (#582).
    """

    @staticmethod
    def _slugify(text: str) -> str:
        s = text.lower().strip()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s_-]+", "-", s)
        return s.strip("-")

    @staticmethod
    def _generate_unique_slug(db: Session, base_name: str) -> str:
        base_slug = PluginService._slugify(base_name) or "plugin"
        slug = base_slug
        counter = 1
        while db.scalar(select(Plugin).where(Plugin.slug == slug)):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    # ------------------------------------------------------------------
    # Plugin Marketplace & Registry CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def create_plugin(db: Session, plugin_in: PluginCreate, author: User) -> Plugin:
        slug = (
            plugin_in.slug.strip()
            if plugin_in.slug
            else PluginService._generate_unique_slug(db, plugin_in.name)
        )

        existing = db.scalar(select(Plugin).where(Plugin.slug == slug))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin slug '{slug}' already exists.",
            )

        api_key_secret = f"devlink_plg_{secrets.token_urlsafe(32)}"
        now = datetime.now(timezone.utc)

        plugin = Plugin(
            id=uuid.uuid4(),
            name=plugin_in.name.strip(),
            slug=slug,
            description=plugin_in.description.strip(),
            version=plugin_in.version,
            author_id=author.id,
            plugin_type=plugin_in.plugin_type,
            status=PluginStatus.ACTIVE,
            manifest=plugin_in.manifest.model_dump(),
            api_key_hash=api_key_secret,
            is_verified=False,
            is_official=False,
            install_count=0,
            created_at=now,
            updated_at=now,
        )

        db.add(plugin)
        db.commit()
        db.refresh(plugin)
        return plugin

    @staticmethod
    def get_plugin_or_404(db: Session, plugin_id_or_slug: str | uuid.UUID) -> Plugin:
        if isinstance(plugin_id_or_slug, uuid.UUID):
            plugin = db.get(Plugin, plugin_id_or_slug)
        else:
            try:
                val = uuid.UUID(plugin_id_or_slug)
                plugin = db.get(Plugin, val)
            except ValueError:
                plugin = db.scalar(
                    select(Plugin).where(Plugin.slug == plugin_id_or_slug)
                )

        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plugin not found.",
            )
        return plugin

    @staticmethod
    def list_plugins(
        db: Session,
        *,
        plugin_type: PluginType | None = None,
        status_filter: PluginStatus | None = None,
        is_verified: bool | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[Plugin], int]:
        stmt = select(Plugin)

        if plugin_type:
            stmt = stmt.where(Plugin.plugin_type == plugin_type)
        if status_filter:
            stmt = stmt.where(Plugin.status == status_filter)
        else:
            stmt = stmt.where(Plugin.status != PluginStatus.DEPRECATED)

        if is_verified is not None:
            stmt = stmt.where(Plugin.is_verified.is_(is_verified))

        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Plugin.name).like(pattern),
                    func.lower(Plugin.slug).like(pattern),
                    func.lower(Plugin.description).like(pattern),
                )
            )

        total_cnt = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        offset = (page - 1) * limit
        stmt = (
            stmt.order_by(Plugin.install_count.desc(), Plugin.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        plugins = list(db.scalars(stmt).all())
        return plugins, total_cnt

    @staticmethod
    def update_plugin(
        db: Session,
        plugin_id: uuid.UUID,
        plugin_in: PluginUpdate,
        actor: User,
    ) -> Plugin:
        plugin = PluginService.get_plugin_or_404(db, plugin_id)

        # Check permission: Author or System Admin
        is_admin = (
            getattr(actor, "system_role", None) == "admin"
            or getattr(actor, "role", None) == "admin"
        )
        if plugin.author_id != actor.id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only plugin author or admin can update this plugin.",
            )

        now = datetime.now(timezone.utc)
        if plugin_in.name is not None:
            plugin.name = plugin_in.name.strip()
        if plugin_in.description is not None:
            plugin.description = plugin_in.description.strip()
        if plugin_in.version is not None:
            plugin.version = plugin_in.version.strip()
        if plugin_in.manifest is not None:
            plugin.manifest = plugin_in.manifest.model_dump()
        if plugin_in.status is not None and is_admin:
            plugin.status = plugin_in.status

        plugin.updated_at = now
        db.add(plugin)
        db.commit()
        db.refresh(plugin)
        return plugin

    @staticmethod
    def verify_plugin(
        db: Session,
        plugin_id: uuid.UUID,
        is_verified: bool = True,
        is_official: bool = False,
    ) -> Plugin:
        plugin = PluginService.get_plugin_or_404(db, plugin_id)
        plugin.is_verified = is_verified
        plugin.is_official = is_official
        plugin.updated_at = datetime.now(timezone.utc)
        db.add(plugin)
        db.commit()
        db.refresh(plugin)
        return plugin

    # ------------------------------------------------------------------
    # Installation & Uninstallation Management
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    @staticmethod
    def assert_can_manage_org_plugins(
        db: Session,
        user: User,
        organization_id: uuid.UUID,
    ) -> None:
        """Raise 403 unless ``user`` may manage plugins for that organization.

        ``organization_id`` arrives from the request -- in the body for
        install, as a query parameter for uninstall and list -- and was used
        unvalidated. Any logged-in user could therefore install a plugin into
        any organization, and since an installation is what ``dispatch_event``
        fans out over, that was also how an attacker attached a webhook
        destination of their choosing to somebody else's event stream.
        Uninstall was the mirror image: a one-request removal of an
        organization's integrations.
        """
        if not has_org_permission(db, user.id, organization_id, ORG_MANAGE_PLUGINS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage plugins for this organization.",
            )

    @staticmethod
    def can_manage_installation(
        db: Session,
        user: User,
        installation: PluginInstallation,
    ) -> bool:
        """Whether ``user`` may enable, disable or reconfigure an installation.

        Mirrors the two owner shapes on the row itself. The previous check was

            if installation.user_id != user.id and not is_admin:

        which is correct for a personal installation and wrong for an
        organization one: ``user_id`` is ``None`` there, so ``None != user.id``
        held for everybody -- including the organization's own admins, who were
        left with no way to disable a plugin somebody else had installed on
        them.
        """
        if getattr(user, "is_superuser", False):
            return True
        if getattr(user, "system_role", None) == "admin":
            return True

        if installation.user_id is not None:
            return installation.user_id == user.id

        if installation.organization_id is not None:
            return has_org_permission(
                db,
                user.id,
                installation.organization_id,
                ORG_MANAGE_PLUGINS,
            )

        return False

    @staticmethod
    def install_plugin(
        db: Session,
        plugin_id: uuid.UUID,
        user: User,
        install_in: PluginInstallationCreate,
    ) -> PluginInstallation:
        plugin = PluginService.get_plugin_or_404(db, plugin_id)

        if plugin.status == PluginStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot install suspended plugin.",
            )

        org_id = install_in.organization_id

        if org_id:
            PluginService.assert_can_manage_org_plugins(db, user, org_id)

        # Check existing installation
        if org_id:
            existing = db.scalar(
                select(PluginInstallation).where(
                    PluginInstallation.plugin_id == plugin.id,
                    PluginInstallation.organization_id == org_id,
                )
            )
        else:
            existing = db.scalar(
                select(PluginInstallation).where(
                    PluginInstallation.plugin_id == plugin.id,
                    PluginInstallation.user_id == user.id,
                    PluginInstallation.organization_id.is_(None),
                )
            )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plugin is already installed for this target.",
            )

        now = datetime.now(timezone.utc)
        installation = PluginInstallation(
            id=uuid.uuid4(),
            plugin_id=plugin.id,
            user_id=user.id if not org_id else None,
            organization_id=org_id,
            is_enabled=True,
            config=install_in.config or {},
            installed_at=now,
            updated_at=now,
        )

        plugin.install_count += 1
        db.add(installation)
        db.add(plugin)
        db.commit()

        # Reload with plugin relationship
        stmt = (
            select(PluginInstallation)
            .options(selectinload(PluginInstallation.plugin))
            .where(PluginInstallation.id == installation.id)
        )
        return db.scalar(stmt)

    @staticmethod
    def uninstall_plugin(
        db: Session,
        plugin_id: uuid.UUID,
        user: User,
        organization_id: Optional[uuid.UUID] = None,
    ) -> None:
        plugin = PluginService.get_plugin_or_404(db, plugin_id)

        if organization_id:
            PluginService.assert_can_manage_org_plugins(db, user, organization_id)

            installation = db.scalar(
                select(PluginInstallation).where(
                    PluginInstallation.plugin_id == plugin.id,
                    PluginInstallation.organization_id == organization_id,
                )
            )
        else:
            installation = db.scalar(
                select(PluginInstallation).where(
                    PluginInstallation.plugin_id == plugin.id,
                    PluginInstallation.user_id == user.id,
                    PluginInstallation.organization_id.is_(None),
                )
            )

        if not installation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plugin installation not found.",
            )

        if plugin.install_count > 0:
            plugin.install_count -= 1

        db.delete(installation)
        db.add(plugin)
        db.commit()

    @staticmethod
    def list_user_installations(
        db: Session,
        user: User,
        organization_id: Optional[uuid.UUID] = None,
    ) -> list[PluginInstallation]:
        stmt = select(PluginInstallation).options(
            selectinload(PluginInstallation.plugin)
        )

        if organization_id:
            # Listing an organization's installations discloses which
            # third-party integrations it runs and how they are configured, so
            # it needs the same permission as changing them.
            PluginService.assert_can_manage_org_plugins(db, user, organization_id)

            stmt = stmt.where(PluginInstallation.organization_id == organization_id)
        else:
            stmt = stmt.where(
                PluginInstallation.user_id == user.id,
                PluginInstallation.organization_id.is_(None),
            )

        return list(
            db.scalars(stmt.order_by(PluginInstallation.installed_at.desc())).all()
        )

    @staticmethod
    def update_installation(
        db: Session,
        installation_id: uuid.UUID,
        update_in: PluginInstallationUpdate,
        user: User,
    ) -> PluginInstallation:
        stmt = (
            select(PluginInstallation)
            .options(selectinload(PluginInstallation.plugin))
            .where(PluginInstallation.id == installation_id)
        )
        installation = db.scalar(stmt)
        if not installation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plugin installation not found.",
            )

        if not PluginService.can_manage_installation(db, user, installation):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this installation.",
            )

        now = datetime.now(timezone.utc)
        if update_in.is_enabled is not None:
            installation.is_enabled = update_in.is_enabled
        if update_in.config is not None:
            installation.config = update_in.config

        installation.updated_at = now
        db.add(installation)
        db.commit()
        db.refresh(installation)
        return installation

    # ------------------------------------------------------------------
    # Extension API & Workflow Execution Hooks
    # ------------------------------------------------------------------

    @staticmethod
    def dispatch_event(
        db: Session,
        event: str,
        payload: dict[str, Any],
    ) -> PluginEventDispatchResult:
        """
        Dispatches workflow/extension events to all matching active plugins.
        """
        stmt_plugins = select(Plugin).where(Plugin.status == PluginStatus.ACTIVE)
        active_plugins = list(db.scalars(stmt_plugins).all())

        matched_plugins: list[Plugin] = []
        for p in active_plugins:
            manifest_points = (
                p.manifest.get("extension_points", [])
                if isinstance(p.manifest, dict)
                else []
            )
            if event in manifest_points:
                matched_plugins.append(p)

        matched_ids = [p.id for p in matched_plugins]
        dispatches: list[PluginDispatchItem] = []
        dispatched_count = 0

        if matched_ids:
            stmt_inst = (
                select(PluginInstallation)
                .options(selectinload(PluginInstallation.plugin))
                .where(
                    PluginInstallation.plugin_id.in_(matched_ids),
                    PluginInstallation.is_enabled.is_(True),
                )
            )
            installations = list(db.scalars(stmt_inst).all())

            for inst in installations:
                webhook_url = (
                    inst.plugin.manifest.get("webhook_url")
                    if isinstance(inst.plugin.manifest, dict)
                    else None
                )
                dispatched_status = "queued" if webhook_url else "no_webhook"
                # The URL itself is deliberately not echoed back. An
                # integration webhook is a bearer credential in practice -- a
                # Slack or Discord hook URL is postable by anyone holding the
                # string -- and a dispatch result has no need to repeat the
                # destination to tell the caller what happened.
                dispatches.append(
                    PluginDispatchItem(
                        plugin_id=inst.plugin.id,
                        plugin_slug=inst.plugin.slug,
                        installation_id=inst.id,
                        has_webhook=bool(webhook_url),
                        status=dispatched_status,
                    )
                )
                if webhook_url:
                    dispatched_count += 1

        logger.info(
            "plugin_event_dispatched event=%s matched=%d dispatched=%d",
            event,
            len(matched_plugins),
            dispatched_count,
        )

        return PluginEventDispatchResult(
            event=event,
            matched_plugins_count=len(matched_plugins),
            dispatched_installations_count=dispatched_count,
            dispatches=dispatches,
        )
