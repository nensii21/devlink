from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_current_user
from app.middleware.rate_limit import limiter, MESSAGE_LIMIT, SEARCH_LIMIT
from app.models.user import User
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageUpdate,
)
from app.services.message_service import MessageService

# pyrefly: ignore [missing-import]
from sqlalchemy import select

from app.models.conversation_member import ConversationMember
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService

router = APIRouter(
    tags=["Messages"],
)


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
            NotificationService.enqueue(
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
def my_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return MessageService.list_user_messages(
        db,
        current_user.id,
    )


@router.get(
    "/search/{conversation_id}",
    response_model=list[MessageResponse],
)
def search_messages(
    conversation_id: uuid.UUID,
    keyword: str = Query(...),
    db: Session = Depends(get_database),
):

    return MessageService.search_messages(
        db,
        conversation_id,
        keyword,
    )


@router.get(
    "/conversation/{conversation_id}/count",
)
def count_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return {
        "count": MessageService.count_messages(
            db,
            conversation_id,
        )
    }


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
):

    return MessageService.list_conversation_messages(
        db,
        conversation_id,
        limit,
    )


@router.get(
    "/{message_id}",
    response_model=MessageResponse,
)
def get_message(
    message_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    message = MessageService.get_message(
        db,
        message_id,
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    return message


@router.put(
    "/{message_id}",
    response_model=MessageResponse,
)
@limiter.limit("20/minute")
def update_message(
    request: Request,
    message_id: uuid.UUID,
    message: MessageUpdate,
    db: Session = Depends(get_database),
):

    db_message = MessageService.get_message(
        db,
        message_id,
    )

    if db_message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    return MessageService.update_message(
        db,
        db_message,
        message,
    )


@router.patch(
    "/{message_id}/restore",
    response_model=MessageResponse,
)
@limiter.limit("10/minute")
def restore_message(
    request: Request,
    message_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    db_message = MessageService.get_message(
        db,
        message_id,
    )

    if db_message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

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
    db: Session = Depends(get_database),
):

    db_message = MessageService.get_message(
        db,
        message_id,
    )

    if db_message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    return MessageService.delete_message(
        db,
        db_message,
    )
