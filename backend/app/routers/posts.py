from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.cache import cache_manager, cached
from app.dependencies import get_current_user, get_database
from app.models.post import Post
from app.models.user import User
from app.schemas.post import (
    PostCreate,
    PostResponse,
    PostUpdate,
    PostAuthorResponse,
)

router = APIRouter(
    tags=["Posts"],
)


def get_ago_string(created_at: datetime) -> str:
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    diff = now - created_at
    if diff.days > 0:
        return f"{diff.days}d ago"
    seconds = diff.seconds
    if seconds >= 3600:
        return f"{seconds // 3600}h ago"
    if seconds >= 60:
        return f"{seconds // 60}m ago"
    return "just now"


def map_db_to_response(db_post: Post) -> PostResponse:
    author_obj = PostAuthorResponse(
        id=db_post.author.id,
        name=f"{db_post.author.first_name} {db_post.author.last_name}".strip(),
        handle=db_post.author.username,
        avatar=db_post.author.profile_image,
        verified=db_post.author.is_verified,
        premium=getattr(db_post.author, "premium", False),
    )
    return PostResponse(
        id=db_post.id,
        author=author_obj,
        content=db_post.content,
        tags=list(db_post.tags) if db_post.tags else [],
        likes=db_post.likes_count,
        comments=db_post.comments_count,
        ago=get_ago_string(db_post.created_at),
        status=db_post.status,
        publish_at=db_post.publish_at,
        created_at=db_post.created_at,
        updated_at=db_post.updated_at,
    )


@router.get("/", response_model=list[PostResponse])
@cached(ttl=120, key_prefix="post_list")
def list_posts(
    db: Session = Depends(get_database),
):
    now = datetime.now(timezone.utc)
    db_posts = (
        db.query(Post)
        .filter(
            Post.status == "published",
            (Post.publish_at.is_(None)) | (Post.publish_at <= now),
        )
        .order_by(Post.created_at.desc())
        .all()
    )
    return [map_db_to_response(p) for p in db_posts]


@router.get("/drafts", response_model=list[PostResponse])
@cached(ttl=120, key_prefix="post_drafts")
def list_drafts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    db_posts = (
        db.query(Post)
        .filter(
            Post.author_id == current_user.id, Post.status.in_(["draft", "scheduled"])
        )
        .order_by(Post.created_at.desc())
        .all()
    )
    return [map_db_to_response(p) for p in db_posts]


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    status_val = payload.status
    publish_at = payload.publish_at

    if publish_at:
        if publish_at.tzinfo is None:
            publish_at = publish_at.replace(tzinfo=timezone.utc)
        if publish_at > datetime.now(timezone.utc):
            status_val = "scheduled"
        else:
            status_val = "published"

    new_post = Post(
        author_id=current_user.id,
        content=payload.content,
        status=status_val,
        publish_at=publish_at,
        tags=payload.tags,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    cache_manager.delete_pattern("post_*")
    return map_db_to_response(new_post)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: uuid.UUID,
    payload: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")

    if payload.content is not None:
        db_post.content = payload.content
    if payload.tags is not None:
        db_post.tags = payload.tags
    if payload.publish_at is not None:
        db_post.publish_at = payload.publish_at
    if payload.status is not None:
        db_post.status = payload.status

    if db_post.publish_at:
        pub_time = db_post.publish_at
        if pub_time.tzinfo is None:
            pub_time = pub_time.replace(tzinfo=timezone.utc)
        if pub_time > datetime.now(timezone.utc):
            db_post.status = "scheduled"
        else:
            db_post.status = "published"

    db.commit()
    db.refresh(db_post)
    cache_manager.delete_pattern("post_*")
    return map_db_to_response(db_post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this post"
        )

    db.delete(db_post)
    db.commit()
    cache_manager.delete_pattern("post_*")
    return


@router.post("/{post_id}/like")
def like_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.likes_count += 1
    db.commit()
    cache_manager.delete_pattern("post_*")
    return {"likes": db_post.likes_count}


@router.delete("/{post_id}/like")
def unlike_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.likes_count = max(0, db_post.likes_count - 1)
    db.commit()
    cache_manager.delete_pattern("post_*")
    return {"likes": db_post.likes_count}


class CommentRequest(BaseModel):
    comment: str


@router.post("/{post_id}/comment")
def comment_post(
    post_id: uuid.UUID,
    payload: CommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.comments_count += 1
    db.commit()
    cache_manager.delete_pattern("post_*")
    return {"comments": db_post.comments_count}
