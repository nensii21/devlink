from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.schemas.message_draft import MessageDraftResponse, MessageDraftSaveRequest
from app.services.message_draft_service import MessageDraftService

router = APIRouter(
    prefix="/messages/drafts",
    tags=["Message Drafts"],
)


@router.get(
    "/",
    response_model=list[MessageDraftResponse],
    summary="List all message drafts for current user across conversations",
)
def list_my_drafts(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    return MessageDraftService.get_all_user_drafts(db, current_user.id)


@router.get(
    "/{conversation_id}",
    response_model=MessageDraftResponse | None,
    summary="Get saved draft for a specific conversation",
)
def get_draft(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    draft = MessageDraftService.get_draft(db, current_user.id, conversation_id)
    return draft


@router.post(
    "/",
    response_model=MessageDraftResponse | None,
    summary="Save or update draft (auto-save while typing)",
)
def save_draft(
    payload: MessageDraftSaveRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    return MessageDraftService.save_draft(db, current_user.id, payload)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Explicitly delete draft for conversation",
)
def delete_draft(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    MessageDraftService.delete_draft(db, current_user.id, conversation_id)
