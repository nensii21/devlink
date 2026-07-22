from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.conversation_starter import (
    ConversationStarterRequest,
    ConversationStarterResponse,
)
from app.services.conversation_starter_service import ConversationStarterService

router = APIRouter(
    tags=["Conversation Starters"],
)

CONVERSATION_STARTER_LIMIT = "10/minute"


@router.post(
    "/conversation-starters",
    response_model=ConversationStarterResponse,
)
@limiter.limit(CONVERSATION_STARTER_LIMIT)
def generate_conversation_starters(
    request: Request,
    body: ConversationStarterRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Generate AI-powered conversation starters for messaging a user.
    
    Returns 3-5 context-aware suggestions based on both users' profiles,
    skills, and interests.
    """
    # Prevent generating starters for yourself
    if current_user.id == body.target_user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate conversation starters for yourself",
        )

    # Verify target user exists
    target_user = db.get(User, body.target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="Target user not found",
        )

    # Generate starters
    suggestions = ConversationStarterService.generate_conversation_starters(
        db=db,
        current_user_id=str(current_user.id),
        target_user_id=str(body.target_user_id),
    )

    return ConversationStarterResponse(
        suggestions=suggestions,
        target_user_id=target_user.id,
        target_user_name=f"{target_user.first_name} {target_user.last_name}",
    )
