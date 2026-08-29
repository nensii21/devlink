from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Post status values the API accepts. The column is `String(20)` with no
# constraint, and `PostCreate.status` used to be a bare `str`, so any string
# was writable -- including one that no query filters on, which made the post
# invisible on every listing rather than rejected at the door.
POST_STATUSES = ("draft", "published", "scheduled")

MAX_POST_LENGTH = 5_000
MAX_COMMENT_LENGTH = 2_000
MAX_TAGS = 10
MAX_TAG_LENGTH = 40


class PostAuthorResponse(BaseModel):
    id: uuid.UUID
    name: str
    handle: str
    avatar: Optional[str] = None
    verified: bool = False
    premium: bool = False


def _validate_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if value not in POST_STATUSES:
        raise ValueError(
            f"status must be one of {', '.join(POST_STATUSES)}; got {value!r}"
        )
    return value


def _validate_tags(value: Optional[list[str]]) -> Optional[list[str]]:
    if value is None:
        return None
    cleaned: list[str] = []
    for tag in value:
        tag = tag.strip()
        if not tag:
            continue
        if len(tag) > MAX_TAG_LENGTH:
            raise ValueError(f"tag {tag!r} is longer than {MAX_TAG_LENGTH} characters")
        if tag not in cleaned:
            cleaned.append(tag)
    if len(cleaned) > MAX_TAGS:
        raise ValueError(f"a post may carry at most {MAX_TAGS} tags")
    return cleaned


class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=MAX_POST_LENGTH)
    status: str = "published"
    publish_at: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("status")
    @classmethod
    def _check_status(cls, value: str) -> str:
        return _validate_status(value)

    @field_validator("tags")
    @classmethod
    def _check_tags(cls, value: list[str]) -> list[str]:
        return _validate_tags(value) or []

    @field_validator("content")
    @classmethod
    def _strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content cannot be blank")
        return stripped


class PostUpdate(BaseModel):
    content: Optional[str] = Field(default=None, max_length=MAX_POST_LENGTH)
    status: Optional[str] = None
    publish_at: Optional[datetime] = None
    tags: Optional[list[str]] = None

    @field_validator("status")
    @classmethod
    def _check_status(cls, value: Optional[str]) -> Optional[str]:
        return _validate_status(value)

    @field_validator("tags")
    @classmethod
    def _check_tags(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        return _validate_tags(value)

    @field_validator("content")
    @classmethod
    def _strip_content(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("content cannot be blank")
        return stripped


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author: PostAuthorResponse
    content: str
    tags: list[str] = []
    likes: int = 0
    comments: int = 0
    ago: str = "just now"
    status: str = "published"
    publish_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Whether the caller has liked this post. The client used to guess from a
    # cache entry seeded with `{}`, so every post read as un-liked after a
    # reload and clicking the heart sent another like.
    liked_by_me: bool = False


class PostCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=MAX_COMMENT_LENGTH)

    @field_validator("comment")
    @classmethod
    def _strip_comment(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("comment cannot be blank")
        return stripped


class PostCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    author: PostAuthorResponse
    content: str
    ago: str = "just now"
    created_at: datetime
    updated_at: datetime


class PostEngagementResponse(BaseModel):
    """
    The state of one post's engagement after a like, unlike or comment.

    `liked_by_me` is returned alongside the count so the client never has to
    infer it, and `changed` says whether this request moved anything -- a
    second like is a success that changed nothing, not an error.
    """

    post_id: uuid.UUID
    likes: int
    comments: int
    liked_by_me: bool
    changed: bool
