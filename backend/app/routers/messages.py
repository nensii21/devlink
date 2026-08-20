from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

# pyrefly: ignore [missing-import]

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_current_user
from app.middleware.rate_limit import limiter, MESSAGE_LIMIT, SEARCH_LIMIT
from app.models.user import User
from app.schemas.message import (
    BulkReadRequest,
    BulkReadResponse,
    BulkDeliverRequest,
    BulkDeliverResponse,
    MessageCreate,
    MessageResponse,
    MessageUpdate,
)
from app.services.message_service import MessageService

# pyrefly: ignore [missing-import]
from sqlalchemy import func, select

from app.models.conversation_member import ConversationMember
from app.models.message import Message
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService

router = APIRouter(
    tags=["Messages"],
)


# ------------------------------------------------------------------
# Conversation membership  (issue #1234)
# ------------------------------------------------------------------
#
# Every route below addresses a conversation: by path parameter, through the
# body of the request, or indirectly through the message it names. None of
# them may act on a conversation the caller does not belong to.
#
# The read-receipt routes already got this right at the service layer
# (`MessageService.mark_as_read` and friends check `ConversationMember` before
# touching anything), so the shape below is deliberately the same check and
# the same 403 -- this is applying an existing convention to the routes that
# never adopted it, not inventing a second one.


def _assert_conversation_member(
    db: Session,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Raise 403 unless ``user_id`` belongs to ``conversation_id``.

    A count rather than a fetch: nothing here needs the membership row, only
    the yes/no, and the composite index on (conversation_id, user_id) answers
    it without loading anything.
    """
    is_member = db.scalar(
        select(func.count(ConversationMember.id)).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id,
        )
    )

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this conversation",
        )


def require_conversation_member(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency for routes with a ``conversation_id`` path parameter.

    Returns the caller, so a route declares
    ``current_user: User = Depends(require_conversation_member)`` and gets
    both the authentication and the membership check from one dependency --
    there is no way to take the user and forget the check.
    """
    _assert_conversation_member(db, conversation_id, current_user.id)
    return current_user


def _member_message_or_404(
    db: Session,
    message_id: uuid.UUID,
    current_user: User,
) -> Message:
    """Fetch a message the caller is entitled to see.

    For routes keyed on a ``message_id``, where the conversation is only
    reachable through the message itself.
    """
    db_message = MessageService.get_message(db, message_id)

    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    _assert_conversation_member(db, db_message.conversation_id, current_user.id)
    return db_message


@router.post(
    "/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(MESSAGE_LIMIT)
def send_message(
    request: Request,
    message: MessageCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    # The conversation id is in the body, out of reach of
    # `require_conversation_member`, so the check is explicit here -- and
    # before the write, not after it.
    _assert_conversation_member(db, message.conversation_id, current_user.id)

    sent = MessageService.send_message(
        db=db,
        conversation_id=message.conversation_id,
        sender_id=current_user.id,
        message=message,
    )

    try:
        recipient_ids = db.scalars(
            select(ConversationMember.user_id).where(
                ConversationMember.conversation_id == message.conversation_id,
                ConversationMember.user_id != current_user.id,
            )
        ).all()

        for recipient_id in recipient_ids:
            NotificationService.notify(
                db,
                recipient_id=recipient_id,
                sender_id=current_user.id,
                type=NotificationType.MESSAGE,
                title="New message",
                message=f"{current_user.username} sent you a message.",
                conversation_id=message.conversation_id,
                message_id=sent.id,
                action_url=f"/conversations/{message.conversation_id}",
            )
    except Exception:
        db.rollback()

    return sent


@router.get(
    "/me",
    response_model=list[MessageResponse],
)
@limiter.limit(MESSAGE_LIMIT)
def my_messages(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return MessageService.list_user_messages(
        db,
        current_user.id,
    )


@router.get(
    "/scheduled",
    response_model=list[MessageResponse],
)
@limiter.limit(MESSAGE_LIMIT)
def scheduled_messages(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """List the current user's not-yet-sent scheduled messages."""
    return MessageService.list_user_scheduled_messages(
        db,
        current_user.id,
    )


@router.delete(
    "/scheduled/{message_id}",
    response_model=MessageResponse,
)
@limiter.limit(MESSAGE_LIMIT)
def cancel_scheduled_message(
    request: Request,
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Cancel a scheduled message that has not been sent yet."""
    db_message = MessageService.get_message(db, message_id)
    if db_message is None or db_message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled message not found",
        )
    if db_message.is_sent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message has already been sent.",
        )
    return MessageService.cancel_scheduled_message(db, db_message)


@router.get(
    "/search",
    response_model=list[MessageResponse],
)
@limiter.limit(SEARCH_LIMIT)
def global_search_messages(
    request: Request,
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Global message search across every conversation the user belongs to."""
    return MessageService.search_all_messages(
        db,
        current_user.id,
        q,
    )


@router.get(
    "/search/{conversation_id}",
    response_model=list[MessageResponse],
)
@limiter.limit(SEARCH_LIMIT)
def search_messages(
    request: Request,
    conversation_id: uuid.UUID,
    keyword: str = Query(...),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_conversation_member),
):
    """Search one conversation the caller belongs to."""

    return MessageService.search_messages(
        db,
        conversation_id,
        keyword,
    )


@router.get(
    "/conversation/{conversation_id}/count",
)
@limiter.limit(MESSAGE_LIMIT)
def count_messages(
    request: Request,
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_conversation_member),
):
    """Count the messages in a conversation the caller belongs to."""

    return {
        "count": MessageService.count_messages(
            db,
            conversation_id,
        )
    }


@router.get(
    "/conversation/{conversation_id}/pinned",
    response_model=list[MessageResponse],
)
@limiter.limit(MESSAGE_LIMIT)
def pinned_messages(
    request: Request,
    conversation_id: uuid.UUID,
    current_user: User = Depends(require_conversation_member),
    db: Session = Depends(get_database),
):
    """List messages pinned in a conversation (issue #973)."""
    return MessageService.list_pinned_messages(db, conversation_id)


@router.get(
    "/conversation/{conversation_id}",
    response_model=list[MessageResponse],
)
@limiter.limit(SEARCH_LIMIT)
def list_conversation_messages(
    request: Request,
    conversation_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_conversation_member),
):
    """Read a conversation the caller belongs to."""

    return MessageService.list_conversation_messages(
        db,
        conversation_id,
        limit,
    )


# ------------------------------------------------------------------
# Typing indicator  (issue #337)
# ------------------------------------------------------------------


@router.post(
    "/conversation/{conversation_id}/typing",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("60/minute")
def set_typing(
    request: Request,
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_conversation_member),
):
    """Record that the current user is typing in a conversation.

    Clients should call this on a debounce (e.g. every 1–2s while the
    input has focus and is changing). The state expires automatically
    after ``MessageService.TYPING_TTL_SECONDS`` if no further heartbeats
    arrive, so there is no strict requirement to call the "stop" endpoint.
    """
    MessageService.set_typing(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    return None


@router.delete(
    "/conversation/{conversation_id}/typing",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("60/minute")
def stop_typing(
    request: Request,
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_conversation_member),
):
    """Explicitly clear the current user's typing state.

    Called when the user sends a message or blurs the input so the
    indicator disappears immediately rather than waiting for the TTL.
    """
    MessageService.clear_typing(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    return None


@router.get(
    "/conversation/{conversation_id}/typing",
)
@limiter.limit("60/minute")
def get_typing(
    request: Request,
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_conversation_member),
):
    """Return the list of user IDs currently typing in a conversation.

    The requesting user is excluded so a client never sees its own
    indicator echoed back.
    """
    typing_user_ids = MessageService.get_typing_users(
        conversation_id=conversation_id,
        exclude_user_id=current_user.id,
    )
    return {
        "conversation_id": str(conversation_id),
        "typing_user_ids": [str(uid) for uid in typing_user_ids],
    }


@router.get(
    "/{message_id}",
    response_model=MessageResponse,
)
@limiter.limit(MESSAGE_LIMIT)
def get_message(
    request: Request,
    message_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    return _member_message_or_404(db, message_id, current_user)


def _get_owned_message(
    db: Session,
    message_id: uuid.UUID,
    current_user: User,
) -> Message:
    """Fetch a message the caller wrote, in a conversation they are still in.

    Authorship alone is not enough. Someone removed from a conversation keeps
    their `sender_id` on every message they wrote there, so an ownership-only
    check let a removed member go on editing and deleting inside a thread they
    no longer belong to.
    """
    db_message = _member_message_or_404(db, message_id, current_user)

    if db_message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit or delete your own messages.",
        )

    return db_message


@router.put(
    "/{message_id}",
    response_model=MessageResponse,
)
@limiter.limit("20/minute")
def update_message(
    request: Request,
    message_id: uuid.UUID,
    message: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    db_message = _get_owned_message(db, message_id, current_user)

    return MessageService.update_message(
        db,
        db_message,
        message,
    )


@router.patch(
    "/{message_id}/pin",
    response_model=MessageResponse,
)
@limiter.limit("20/minute")
def pin_message(
    request: Request,
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Pin a message in its conversation (issue #973)."""
    db_message = _member_message_or_404(db, message_id, current_user)

    if db_message.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pin a deleted message.",
        )
    return MessageService.pin_message(db, db_message, current_user.id)


@router.patch(
    "/{message_id}/unpin",
    response_model=MessageResponse,
)
@limiter.limit("20/minute")
def unpin_message(
    request: Request,
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Unpin a message (issue #973)."""
    db_message = _member_message_or_404(db, message_id, current_user)

    return MessageService.unpin_message(db, db_message)


@router.patch(
    "/{message_id}/restore",
    response_model=MessageResponse,
)
@limiter.limit("10/minute")
def restore_message(
    request: Request,
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    db_message = _get_owned_message(db, message_id, current_user)

    return MessageService.restore_message(
        db,
        db_message,
    )


@router.delete(
    "/{message_id}",
    response_model=MessageResponse,
)
@limiter.limit("10/minute")
def delete_message(
    request: Request,
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    db_message = _get_owned_message(db, message_id, current_user)

    return MessageService.delete_message(
        db,
        db_message,
    )


@router.patch(
    "/{message_id}/read",
    response_model=MessageResponse,
)
@limiter.limit(MESSAGE_LIMIT)
def mark_message_as_read(
    request: Request,
    message_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Mark a single message as read by the current user."""
    return MessageService.mark_as_read(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
    )


@router.post(
    "/read/bulk",
    response_model=BulkReadResponse,
)
@limiter.limit(MESSAGE_LIMIT)
def bulk_mark_read(
    request: Request,
    body: BulkReadRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Bulk mark messages or an entire conversation as read by the current user."""
    if body.conversation_id:
        _assert_conversation_member(db, body.conversation_id, current_user.id)
        count, read_at = MessageService.mark_conversation_as_read(
            db=db,
            conversation_id=body.conversation_id,
            user_id=current_user.id,
        )
    elif body.message_ids:
        count, read_at = MessageService.bulk_mark_as_read(
            db=db,
            message_ids=body.message_ids,
            user_id=current_user.id,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either message_ids or conversation_id",
        )

    return BulkReadResponse(updated_count=count, read_at=read_at)


@router.post(
    "/conversation/{conversation_id}/read",
    response_model=BulkReadResponse,
)
@limiter.limit(MESSAGE_LIMIT)
def mark_conversation_as_read(
    request: Request,
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_conversation_member),
):
    """Mark all unread messages in a conversation as read by the current user."""
    count, read_at = MessageService.mark_conversation_as_read(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    return BulkReadResponse(updated_count=count, read_at=read_at)


@router.post(
    "/{message_id}/deliver",
    response_model=MessageResponse,
)
@limiter.limit(MESSAGE_LIMIT)
def mark_message_as_delivered(
    request: Request,
    message_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Mark a single message as delivered to the current user."""
    return MessageService.mark_as_delivered(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
    )


@router.post(
    "/bulk-deliver",
    response_model=BulkDeliverResponse,
)
@limiter.limit(MESSAGE_LIMIT)
def bulk_mark_as_delivered(
    request: Request,
    body: BulkDeliverRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Mark multiple messages or an entire conversation as delivered to the current user."""
    if body.conversation_id:
        _assert_conversation_member(db, body.conversation_id, current_user.id)
        count, delivered_at = MessageService.mark_conversation_as_delivered(
            db=db,
            conversation_id=body.conversation_id,
            user_id=current_user.id,
        )
    elif body.message_ids:
        count, delivered_at = MessageService.bulk_mark_as_delivered(
            db=db,
            message_ids=body.message_ids,
            user_id=current_user.id,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either message_ids or conversation_id",
        )

    return BulkDeliverResponse(updated_count=count, delivered_at=delivered_at)
