from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Dict, Tuple

# pyrefly: ignore [missing-import]
from sqlalchemy import select

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session, selectinload

from app.models.message import Message
from app.models.conversation_member import ConversationMember
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
)
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService


class MessageService:
    """
    Business logic for chat messages.
    """

    @staticmethod
    def send_message(
        db: Session,
        conversation_id: uuid.UUID,
        sender_id: uuid.UUID,
        message: MessageCreate,
    ) -> Message:

        db_message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            parent_message_id=message.parent_message_id,
            type=message.type,
            content=message.content,
            attachment_url=message.attachment_url,
            attachment_name=message.attachment_name,
            attachment_size=message.attachment_size,
            mime_type=message.mime_type,
        )

        db.add(db_message)
        db.flush()
        db.refresh(db_message)

        # Trigger notifications for conversation members
        sender = db.get(User, sender_id)
        sender_name = f"{sender.first_name} {sender.last_name}" if sender else "Someone"

        member_stmt = select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id
        )
        members = db.scalars(member_stmt).all()

        content_hint = message.content[:50] if message.content else "sent an attachment"
        notification_message = f"{sender_name}: {content_hint}"

        for member in members:
            if member.user_id != sender_id:
                notification_data = NotificationCreate(
                    recipient_id=member.user_id,
                    type=NotificationType.MESSAGE,
                    title="New Message",
                    message=notification_message,
                    action_url=f"/messages/{conversation_id}",
                    conversation_id=conversation_id,
                    message_id=db_message.id,
                )
                NotificationService.create_notification(
                    db=db,
                    recipient_id=member.user_id,
                    sender_id=sender_id,
                    notification=notification_data,
                )

        return db_message

    @staticmethod
    def get_message(
        db: Session,
        message_id: uuid.UUID,
    ) -> Message | None:

        return db.get(Message, message_id)

    @staticmethod
    def list_conversation_messages(
        db: Session,
        conversation_id: uuid.UUID,
        limit: int = 100,
    ) -> list[Message]:

        stmt = (
            select(Message)
            .options(selectinload(Message.sender))
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_user_messages(
        db: Session,
        sender_id: uuid.UUID,
    ) -> list[Message]:

        stmt = (
            select(Message)
            .options(selectinload(Message.sender))
            .where(Message.sender_id == sender_id)
            .order_by(Message.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_message(
        db: Session,
        db_message: Message,
        message: MessageUpdate,
    ) -> Message:

        data = message.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_message, key, value)

        db_message.is_edited = True
        db_message.edited_at = datetime.utcnow()

        db.flush()
        db.refresh(db_message)

        return db_message

    @staticmethod
    def delete_message(
        db: Session,
        db_message: Message,
    ) -> Message:

        db_message.is_deleted = True
        db_message.deleted_at = datetime.utcnow()
        db_message.content = "[Message deleted]"

        db.flush()
        db.refresh(db_message)

        return db_message

    @staticmethod
    def restore_message(
        db: Session,
        db_message: Message,
    ) -> Message:

        db_message.is_deleted = False
        db_message.deleted_at = None

        db.flush()
        db.refresh(db_message)

        return db_message

    @staticmethod
    def search_messages(
        db: Session,
        conversation_id: uuid.UUID,
        keyword: str,
    ) -> list[Message]:

        stmt = (
            select(Message)
            .options(selectinload(Message.sender))
            .where(
                Message.conversation_id == conversation_id,
                Message.content.ilike(f"%{keyword}%"),
            )
            .order_by(Message.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def count_messages(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> int:

        stmt = select(Message).where(Message.conversation_id == conversation_id)

        return len(list(db.scalars(stmt)))

    # ==========================================================
    # Typing indicator
    # ----------------------------------------------------------
    # Issue #337: Display typing indicators in chat.
    #
    # Typing state is held in an ephemeral, process-local dict keyed by
    # (conversation_id, user_id) → monotonic timestamp. A short TTL (4s)
    # means a user is considered "typing" only while they keep sending
    # heartbeat POSTs from the client; if they stop, the indicator fades
    # automatically without needing an explicit "stopped typing" call.
    #
    # This is deliberately NOT persisted to the database:
    #   - typing state is intrinsically transient;
    #   - avoiding a new table means no migration, no schema change, and
    #     zero impact on existing tests / fixtures.
    # ==========================================================

    TYPING_TTL_SECONDS: float = 4.0
    _typing_store: Dict[Tuple[uuid.UUID, uuid.UUID], float] = {}

    @staticmethod
    def _now() -> float:
        # time.monotonic() is immune to wall-clock adjustments, which is
        # what we want for a TTL comparison.
        return time.monotonic()

    @classmethod
    def set_typing(
        cls,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Record that ``user_id`` is currently typing in ``conversation_id``.

        Idempotent — repeated heartbeats just refresh the timestamp.
        """
        cls._typing_store[(conversation_id, user_id)] = cls._now()

    @classmethod
    def clear_typing(
        cls,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Explicitly mark that ``user_id`` stopped typing.

        Optional — entries expire on their own via TTL. Called when the
        user sends a message or blurs the input so the indicator
        disappears immediately rather than waiting for the TTL.
        """
        cls._typing_store.pop((conversation_id, user_id), None)

    @classmethod
    def get_typing_users(
        cls,
        conversation_id: uuid.UUID,
        exclude_user_id: uuid.UUID | None = None,
    ) -> list[uuid.UUID]:
        """Return user IDs currently typing in ``conversation_id``.

        Stale entries (older than ``TYPING_TTL_SECONDS``) are pruned on
        read. The requesting user is excluded by default so a client
        never sees its own typing indicator echoed back.
        """
        now = cls._now()
        cutoff = now - cls.TYPING_TTL_SECONDS

        # Prune expired entries for this conversation (and any others that
        # happen to be checked in the same sweep). We iterate over a list
        # copy so we can mutate the dict safely.
        for key in list(cls._typing_store.keys()):
            if cls._typing_store[key] < cutoff:
                cls._typing_store.pop(key, None)

        typing = [
            uid
            for (cid, uid), ts in cls._typing_store.items()
            if cid == conversation_id and ts >= cutoff and uid != exclude_user_id
        ]
        return typing
