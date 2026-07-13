from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.message import Message
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
)


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
        db.commit()
        db.refresh(db_message)

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

        db.commit()
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

        db.commit()
        db.refresh(db_message)

        return db_message

    @staticmethod
    def restore_message(
        db: Session,
        db_message: Message,
    ) -> Message:

        db_message.is_deleted = False
        db_message.deleted_at = None

        db.commit()
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
