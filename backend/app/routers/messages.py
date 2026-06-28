from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageUpdate,
)
from app.services.message_service import MessageService

router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)

@router.post(
    "/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return MessageService.send_message(
        db=db,
        conversation_id=message.conversation_id,
        sender_id=current_user.id,
        message=message,
    )
    
@router.get(
    "/{message_id}",
    response_model=MessageResponse,
)
def get_message(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
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

@router.get(
    "/conversation/{conversation_id}",
    response_model=list[MessageResponse],
)
def list_conversation_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):

    return MessageService.list_conversation_messages(
        db,
        conversation_id,
        limit,
    )
    
@router.get(
    "/me",
    response_model=list[MessageResponse],
)
def my_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
):

    return MessageService.search_messages(
        db,
        conversation_id,
        keyword,
    )
    
@router.put(
    "/{message_id}",
    response_model=MessageResponse,
)
def update_message(
    message_id: uuid.UUID,
    message: MessageUpdate,
    db: Session = Depends(get_db),
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
def restore_message(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
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
def delete_message(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
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
    
@router.get(
    "/conversation/{conversation_id}/count",
)
def count_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    return {
        "count": MessageService.count_messages(
            db,
            conversation_id,
        )
    }