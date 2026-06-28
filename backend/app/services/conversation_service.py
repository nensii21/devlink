from __future__ import annotations

import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.conversation_member import ConversationMember
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
)


class ConversationService:
    """
    Business logic for conversations.
    """

    @staticmethod
    def create_conversation(
        db: Session,
        owner_id: uuid.UUID,
        conversation: ConversationCreate,
    ) -> Conversation:

        db_conversation = Conversation(
            title=conversation.title,
            type=conversation.type,
            description=conversation.description,
            project_id=conversation.project_id,
            created_by=owner_id,
        )

        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)

        return db_conversation

    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:

        return db.get(Conversation, conversation_id)

    @staticmethod
    def list_user_conversations(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[Conversation]:

        stmt = (
            select(Conversation)
            .join(
                ConversationMember,
                Conversation.id == ConversationMember.conversation_id,
            )
            .where(
                ConversationMember.user_id == user_id,
            )
        )

        return list(db.scalars(stmt))

    @staticmethod
    def get_direct_conversation(
        db: Session,
        user_a: uuid.UUID,
        user_b: uuid.UUID,
    ) -> Conversation | None:

        stmt = (
            select(Conversation)
            .join(
                ConversationMember,
                Conversation.id == ConversationMember.conversation_id,
            )
            .where(
                or_(
                    ConversationMember.user_id == user_a,
                    ConversationMember.user_id == user_b,
                )
            )
        )

        return db.scalar(stmt)

    @staticmethod
    def add_member(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ConversationMember:

        member = ConversationMember(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        db.add(member)
        db.commit()
        db.refresh(member)

        return member

    @staticmethod
    def remove_member(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:

        stmt = select(ConversationMember).where(
            and_(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
        )

        member = db.scalar(stmt)

        if member:
            db.delete(member)
            db.commit()

    @staticmethod
    def update_conversation(
        db: Session,
        db_conversation: Conversation,
        conversation: ConversationUpdate,
    ) -> Conversation:

        data = conversation.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_conversation, key, value)

        db.commit()
        db.refresh(db_conversation)

        return db_conversation

    @staticmethod
    def archive_conversation(
        db: Session,
        db_conversation: Conversation,
    ) -> Conversation:

        db_conversation.archived = True

        db.commit()
        db.refresh(db_conversation)

        return db_conversation

    @staticmethod
    def restore_conversation(
        db: Session,
        db_conversation: Conversation,
    ) -> Conversation:

        db_conversation.archived = False

        db.commit()
        db.refresh(db_conversation)

        return db_conversation

    @staticmethod
    def delete_conversation(
        db: Session,
        db_conversation: Conversation,
    ) -> None:

        db.delete(db_conversation)
        db.commit()
