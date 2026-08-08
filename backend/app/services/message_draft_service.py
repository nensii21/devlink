from __future__ import annotations

import uuid
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models.message_draft import MessageDraft
from app.schemas.message_draft import MessageDraftSaveRequest


class MessageDraftService:
    """
    Business logic for managing saved message drafts per user and conversation.
    """

    @staticmethod
    def get_draft(
        db: Session, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> MessageDraft | None:
        stmt = select(MessageDraft).where(
            MessageDraft.user_id == user_id,
            MessageDraft.conversation_id == conversation_id,
        )
        return db.scalar(stmt)

    @staticmethod
    def get_all_user_drafts(db: Session, user_id: uuid.UUID) -> list[MessageDraft]:
        stmt = select(MessageDraft).where(MessageDraft.user_id == user_id)
        return list(db.scalars(stmt))

    @staticmethod
    def save_draft(
        db: Session, user_id: uuid.UUID, payload: MessageDraftSaveRequest
    ) -> MessageDraft:
        draft = MessageDraftService.get_draft(db, user_id, payload.conversation_id)
        if not payload.content.strip():
            if draft:
                db.delete(draft)
                db.flush()
            return None

        if draft:
            draft.content = payload.content
        else:
            draft = MessageDraft(
                user_id=user_id,
                conversation_id=payload.conversation_id,
                content=payload.content,
            )
            db.add(draft)

        db.flush()
        db.refresh(draft)
        return draft

    @staticmethod
    def delete_draft(db: Session, user_id: uuid.UUID, conversation_id: uuid.UUID) -> None:
        db.execute(
            delete(MessageDraft).where(
                MessageDraft.user_id == user_id,
                MessageDraft.conversation_id == conversation_id,
            )
        )
        db.flush()
