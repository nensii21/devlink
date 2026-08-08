"""Request and response schemas for project discussions (#930)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project_comment import MAX_BODY_LENGTH

# Shown in place of the body of a soft-deleted comment. The row is kept so the
# replies underneath it do not lose their parent, but the text is not returned.
DELETED_BODY_PLACEHOLDER = "[deleted]"


class CommentAuthor(BaseModel):
    """The subset of a user the thread needs.

    Deliberately narrow -- a comment list should not be a way to enumerate
    email addresses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    first_name: str | None = None
    last_name: str | None = None
    profile_image: str | None = None


class ProjectCommentBase(BaseModel):
    body: str = Field(
        ...,
        min_length=1,
        max_length=MAX_BODY_LENGTH,
        description="The comment text.",
    )

    @field_validator("body")
    @classmethod
    def body_must_not_be_blank(cls, value: str) -> str:
        """Reject whitespace-only bodies and normalise trailing space.

        `min_length=1` alone lets a single space through, which renders as an
        empty bubble in the thread.
        """
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Comment body cannot be empty or whitespace only.")

        return cleaned


class ProjectCommentCreate(ProjectCommentBase):
    parent_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "The comment being replied to. Omit for a top-level comment. "
            "Replies are one level deep, so this must name a top-level comment."
        ),
    )


class ProjectCommentUpdate(ProjectCommentBase):
    """Only the body is editable -- a reply cannot be moved to another parent."""


class ProjectCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    parent_id: uuid.UUID | None
    body: str
    author: CommentAuthor | None
    is_edited: bool
    edited_at: datetime | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class ProjectCommentThread(ProjectCommentResponse):
    """A top-level comment together with its replies."""

    replies: list[ProjectCommentResponse] = Field(default_factory=list)
    reply_count: int = 0


class ProjectCommentList(BaseModel):
    """A page of top-level comments.

    `total` counts top-level comments only. Counting replies here would make
    the number disagree with the page size in a way that is hard to explain in
    a paginator.
    """

    items: list[ProjectCommentThread]
    total: int
    limit: int
    offset: int
