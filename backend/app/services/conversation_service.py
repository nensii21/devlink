"""
Business logic for conversations, and the membership rules that guard them.

Every route in ``app/routers/conversations.py`` that names a conversation used
to take a ``conversation_id`` and no caller, so the authorization decisions had
nowhere to live. They live here now, as four ``require_*`` helpers that the
router calls before it does anything else.

Two conventions worth stating, because the status codes are deliberate:

* A caller who is **not a member** gets ``404``, not ``403``. A private
  conversation they are not in should not be distinguishable from one that does
  not exist -- otherwise the routes become an oracle for "is this a real
  conversation id", which is exactly the enumeration step an attacker needs.
* A caller who **is** a member but lacks the role gets ``403``. They already
  know the conversation exists, so there is nothing left to hide, and ``403``
  is the answer that tells a client to stop retrying.
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationType
from app.models.conversation_member import ConversationMember, ConversationRole
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
)

#: Roles allowed to change a conversation or its membership.
#:
#: ``create_conversation`` has always stamped the creator ``OWNER`` and
#: ``add_member`` has always defaulted everyone else to ``MEMBER``; until now
#: nothing read either value back.
CONVERSATION_ADMIN_ROLES = frozenset(
    {ConversationRole.OWNER, ConversationRole.ADMIN}
)


class ConversationService:
    """
    Business logic for conversations.
    """

    # ------------------------------------------------------------------
    # Membership & authorization
    # ------------------------------------------------------------------

    @staticmethod
    def get_membership(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ConversationMember | None:
        """The caller's membership row, or ``None``.

        One query against the unique ``(conversation_id, user_id)`` index. The
        row itself is needed rather than a bare count because the role on it is
        what the next check reads.
        """
        return db.scalar(
            select(ConversationMember).where(
                and_(
                    ConversationMember.conversation_id == conversation_id,
                    ConversationMember.user_id == user_id,
                )
            )
        )

    @staticmethod
    def is_member(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        return (
            ConversationService.get_membership(db, conversation_id, user_id)
            is not None
        )

    @staticmethod
    def require_membership(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[Conversation, ConversationMember]:
        """Load a conversation the caller belongs to, or 404.

        The conversation is fetched *after* the membership check rather than
        before, so a caller who is not a member cannot tell an id that exists
        from one that does not: both paths raise the same 404 with the same
        detail.
        """
        member = ConversationService.get_membership(db, conversation_id, user_id)
        conversation = db.get(Conversation, conversation_id)

        if member is None or conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        return conversation, member

    @staticmethod
    def require_admin(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[Conversation, ConversationMember]:
        """Load a conversation the caller may administer.

        404 if they are not in it at all, 403 if they are in it as a plain
        member.
        """
        conversation, member = ConversationService.require_membership(
            db, conversation_id, user_id
        )

        if member.role not in CONVERSATION_ADMIN_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only a conversation owner or admin can do this.",
            )

        return conversation, member

    @staticmethod
    def require_owner(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[Conversation, ConversationMember]:
        """Load a conversation the caller owns.

        Reserved for deletion. ``delete_conversation`` is a hard ``db.delete``
        and both ``conversation_members`` and ``messages`` cascade from it, so
        it destroys the whole history irreversibly -- that is not something a
        promoted admin should be able to do to the person who started the
        thread.
        """
        conversation, member = ConversationService.require_membership(
            db, conversation_id, user_id
        )

        if member.role != ConversationRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the conversation owner can delete it.",
            )

        return conversation, member

    @staticmethod
    def create_conversation(
        db: Session,
        owner_id: uuid.UUID,
        conversation: ConversationCreate,
    ) -> Conversation:

        db_conversation = Conversation(
            title=conversation.title,
            type=conversation.type,
            project_id=conversation.project_id,
            created_by=owner_id,
        )

        db.add(db_conversation)
        db.flush()
        # Automatically add the owner/creator as a member of the conversation
        owner_member = ConversationMember(
            conversation_id=db_conversation.id,
            user_id=owner_id,
            role=ConversationRole.OWNER,
        )
        db.add(owner_member)
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
        """The one-to-one thread between two people, if it exists.

        This used to ``or_`` the two membership predicates, which matches any
        conversation where *either* of them is a member and then takes the
        first row. For anyone with more than one conversation that returned an
        arbitrary unrelated thread -- very often one ``user_b`` is not in at
        all.

        The predicate that actually expresses "both of them" is a restriction
        to the two ids followed by a ``HAVING`` on the distinct count, which
        also stays correct if a membership row is ever duplicated.
        """
        if user_a == user_b:
            return None

        stmt = (
            select(Conversation)
            .join(
                ConversationMember,
                Conversation.id == ConversationMember.conversation_id,
            )
            .where(
                Conversation.type == ConversationType.DIRECT,
                ConversationMember.user_id.in_([user_a, user_b]),
            )
            .group_by(Conversation.id)
            .having(func.count(func.distinct(ConversationMember.user_id)) == 2)
            .order_by(Conversation.created_at.asc())
        )

        return db.scalars(stmt).first()

    @staticmethod
    def add_member(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ConversationMember:

        # Fetch conversation
        conversation = db.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Prevent self-messaging in direct conversations
        if conversation.type == ConversationType.DIRECT:
            if user_id == conversation.created_by:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You cannot add yourself to a direct conversation",
                )

            # Direct conversations cannot have more than 2 members
            from sqlalchemy import func

            member_count = db.scalar(
                select(func.count(ConversationMember.id)).where(
                    ConversationMember.conversation_id == conversation_id
                )
            )
            if member_count >= 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Direct conversations cannot have more than 2 members",
                )

        # Check if user is already a member
        existing_member = db.scalar(
            select(ConversationMember).where(
                and_(
                    ConversationMember.conversation_id == conversation_id,
                    ConversationMember.user_id == user_id,
                )
            )
        )
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this conversation",
            )

        member = ConversationMember(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        db.add(member)
        db.flush()
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
            db.flush()

    @staticmethod
    def update_conversation(
        db: Session,
        db_conversation: Conversation,
        conversation: ConversationUpdate,
    ) -> Conversation:

        data = conversation.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_conversation, key, value)

        db.flush()
        db.refresh(db_conversation)

        return db_conversation

    @staticmethod
    def archive_conversation(
        db: Session,
        db_conversation: Conversation,
    ) -> Conversation:

        db_conversation.archived = True

        db.flush()
        db.refresh(db_conversation)

        return db_conversation

    @staticmethod
    def restore_conversation(
        db: Session,
        db_conversation: Conversation,
    ) -> Conversation:

        db_conversation.archived = False

        db.flush()
        db.refresh(db_conversation)

        return db_conversation

    @staticmethod
    def delete_conversation(
        db: Session,
        db_conversation: Conversation,
    ) -> None:

        db.delete(db_conversation)
        db.flush()
