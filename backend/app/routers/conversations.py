from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from app.services.conversation_service import ConversationService

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)

@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ConversationService.create_conversation(
        db=db,
        owner_id=current_user.id,
        conversation=conversation,
    )
@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ConversationService.create_conversation(
        db=db,
        owner_id=current_user.id,
        conversation=conversation,
    )
    
@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ConversationService.create_conversation(
        db=db,
        owner_id=current_user.id,
        conversation=conversation,
    )
    
@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    conversation = ConversationService.get_conversation(
        db,
        conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation

@router.get(
    "/",
    response_model=list[ConversationResponse],
)
def list_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return ConversationService.list_user_conversations(
        db,
        current_user.id,
    )
    
@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def update_conversation(
    conversation_id: uuid.UUID,
    conversation: ConversationUpdate,
    db: Session = Depends(get_db),
):

    db_conversation = ConversationService.get_conversation(
        db,
        conversation_id,
    )

    if db_conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return ConversationService.update_conversation(
        db,
        db_conversation,
        conversation,
    )
    
@router.post(
    "/{conversation_id}/members/{user_id}",
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    return ConversationService.add_member(
        db,
        conversation_id,
        user_id,
    )
    
@router.delete(
    "/{conversation_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    ConversationService.remove_member(
        db,
        conversation_id,
        user_id,
    )
    
@router.patch(
    "/{conversation_id}/archive",
    response_model=ConversationResponse,
)
def archive_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    conversation = ConversationService.get_conversation(
        db,
        conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return ConversationService.archive_conversation(
        db,
        conversation,
    )
    
@router.patch(
    "/{conversation_id}/restore",
    response_model=ConversationResponse,
)
def restore_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    conversation = ConversationService.get_conversation(
        db,
        conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return ConversationService.restore_conversation(
        db,
        conversation,
    )
    
@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    conversation = ConversationService.get_conversation(
        db,
        conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    ConversationService.delete_conversation(
        db,
        conversation,
    )