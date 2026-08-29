"""
Conversation routes.

Every route below that names a ``conversation_id`` requires an authenticated
caller who is a member of that conversation. That was not previously true: the
create and list routes took ``current_user``, and the seven that read, mutated
or destroyed a named conversation took only ``get_database``.

The membership check is not cosmetic. ``POST /{id}/members/{user_id}`` grants
exactly the predicate that ``app/routers/messages.py`` uses to authorise
reads -- so an open add-member route meant anyone could join a private thread
and then read all of it through the correctly-guarded messages API.
"""

from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database
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
    db: Session = Depends(get_database),
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
    summary="Get a conversation you are a member of",
)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    conversation, _ = ConversationService.require_membership(
        db,
        conversation_id,
        current_user.id,
    )

    return conversation


@router.get(
    "/",
    response_model=list[ConversationResponse],
)
def list_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return ConversationService.list_user_conversations(
        db,
        current_user.id,
    )


@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Rename or reconfigure a conversation (owner or admin)",
)
def update_conversation(
    conversation_id: uuid.UUID,
    conversation: ConversationUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    db_conversation, _ = ConversationService.require_admin(
        db,
        conversation_id,
        current_user.id,
    )

    return ConversationService.update_conversation(
        db,
        db_conversation,
        conversation,
    )


@router.post(
    "/{conversation_id}/members/{user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Add someone to a conversation (owner or admin)",
    description=(
        "Membership is what the messages API checks before returning a "
        "thread, so this route hands out read access to everything already "
        "said in it. Restricted to the conversation's owner and admins."
    ),
)
def add_member(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    ConversationService.require_admin(
        db,
        conversation_id,
        current_user.id,
    )

    return ConversationService.add_member(
        db,
        conversation_id,
        user_id,
    )


@router.delete(
    "/{conversation_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member, or leave the conversation yourself",
)
def remove_member(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    # Leaving is not an administrative act. Requiring an admin role to remove
    # yourself would trap a plain member in a thread they want no part of,
    # with no route out of it.
    if user_id == current_user.id:
        ConversationService.require_membership(
            db,
            conversation_id,
            current_user.id,
        )
    else:
        ConversationService.require_admin(
            db,
            conversation_id,
            current_user.id,
        )

    ConversationService.remove_member(
        db,
        conversation_id,
        user_id,
    )


@router.patch(
    "/{conversation_id}/archive",
    response_model=ConversationResponse,
    summary="Archive a conversation (owner or admin)",
)
def archive_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    conversation, _ = ConversationService.require_admin(
        db,
        conversation_id,
        current_user.id,
    )

    return ConversationService.archive_conversation(
        db,
        conversation,
    )


@router.patch(
    "/{conversation_id}/restore",
    response_model=ConversationResponse,
    summary="Restore an archived conversation (owner or admin)",
)
def restore_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    conversation, _ = ConversationService.require_admin(
        db,
        conversation_id,
        current_user.id,
    )

    return ConversationService.restore_conversation(
        db,
        conversation,
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation (owner only)",
    description=(
        "Irreversible. `conversation_members` and `messages` both cascade "
        "from the conversation row, so this destroys the whole history."
    ),
)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    conversation, _ = ConversationService.require_owner(
        db,
        conversation_id,
        current_user.id,
    )

    ConversationService.delete_conversation(
        db,
        conversation,
    )
