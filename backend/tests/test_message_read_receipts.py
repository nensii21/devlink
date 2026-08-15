import uuid
import pytest
from app.models.conversation import Conversation
from app.models.conversation_member import ConversationMember
from app.models.message import Message, MessageType
from app.models.user import User
from app.services.message_service import MessageService
from app.services.user_service import UserService
from fastapi import HTTPException


def create_test_user(db, name_prefix):
    return UserService.create_user(
        db,
        User(
            email=f"{name_prefix}_{uuid.uuid4().hex[:6]}@example.com",
            username=f"{name_prefix}_{uuid.uuid4().hex[:6]}",
            first_name="Test",
            last_name="User",
        ),
        "password123",
    )


def test_mark_single_message_as_read(db):
    user1 = create_test_user(db, "sender")
    user2 = create_test_user(db, "recipient")

    conv = Conversation(created_by=user1.id, title="Read Receipt Test")
    db.add(conv)
    db.commit()
    db.refresh(conv)

    db.add_all(
        [
            ConversationMember(conversation_id=conv.id, user_id=user1.id),
            ConversationMember(conversation_id=conv.id, user_id=user2.id),
        ]
    )
    db.commit()

    msg = Message(
        conversation_id=conv.id,
        sender_id=user1.id,
        content="Hello world",
        type=MessageType.TEXT,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    assert msg.read_at is None

    # Mark as read by user2 (recipient)
    updated_msg = MessageService.mark_as_read(db, msg.id, user2.id)
    assert updated_msg.read_at is not None


def test_bulk_mark_messages_as_read(db):
    user1 = create_test_user(db, "bulk_sender")
    user2 = create_test_user(db, "bulk_recipient")

    conv = Conversation(created_by=user1.id, title="Bulk Read Test")
    db.add(conv)
    db.commit()
    db.refresh(conv)

    db.add_all(
        [
            ConversationMember(conversation_id=conv.id, user_id=user1.id),
            ConversationMember(conversation_id=conv.id, user_id=user2.id),
        ]
    )
    db.commit()

    m1 = Message(conversation_id=conv.id, sender_id=user1.id, content="Msg 1")
    m2 = Message(conversation_id=conv.id, sender_id=user1.id, content="Msg 2")
    db.add_all([m1, m2])
    db.commit()

    count, read_time = MessageService.bulk_mark_as_read(db, [m1.id, m2.id], user2.id)
    assert count == 2
    assert read_time is not None

    db.refresh(m1)
    db.refresh(m2)
    assert m1.read_at is not None
    assert m2.read_at is not None


def test_mark_conversation_as_read(db):
    user1 = create_test_user(db, "conv_sender")
    user2 = create_test_user(db, "conv_recipient")

    conv = Conversation(created_by=user1.id, title="Conv Read Test")
    db.add(conv)
    db.commit()
    db.refresh(conv)

    db.add_all(
        [
            ConversationMember(conversation_id=conv.id, user_id=user1.id),
            ConversationMember(conversation_id=conv.id, user_id=user2.id),
        ]
    )
    db.commit()

    m1 = Message(conversation_id=conv.id, sender_id=user1.id, content="Msg A")
    m2 = Message(conversation_id=conv.id, sender_id=user1.id, content="Msg B")
    m3 = Message(conversation_id=conv.id, sender_id=user2.id, content="My own Msg")
    db.add_all([m1, m2, m3])
    db.commit()

    count, read_time = MessageService.mark_conversation_as_read(db, conv.id, user2.id)
    # Only m1 and m2 should be marked as read, not m3 (own message)
    assert count == 2
    assert read_time is not None


def test_mark_read_forbidden_non_member(db):
    user1 = create_test_user(db, "member")
    user2 = create_test_user(db, "non_member")

    conv = Conversation(created_by=user1.id, title="Forbidden Test")
    db.add(conv)
    db.commit()

    db.add(ConversationMember(conversation_id=conv.id, user_id=user1.id))
    db.commit()

    msg = Message(conversation_id=conv.id, sender_id=user1.id, content="Private msg")
    db.add(msg)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        MessageService.mark_as_read(db, msg.id, user2.id)
    assert exc_info.value.status_code == 403
