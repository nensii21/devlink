from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.cache import cache_manager
from app.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_database,
)
from app.models.post import Post
from app.models.post_comment import PostComment
from app.models.post_like import PostLike
from app.models.user import User
from app.models.user_report import UserReport
from app.services.block_service import BlockService
from app.schemas.post import (
    PostAuthorResponse,
    PostCommentCreate,
    PostCommentResponse,
    PostCreate,
    PostEngagementResponse,
    PostResponse,
    PostUpdate,
)
from app.schemas.user_report import UserReportCreate, UserReportResponse

router = APIRouter(
    tags=["Posts"],
)

# Feed listings are paginated. `list_posts` used to end in `.all()` with no
# bound, so the response was every published post in the table.
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


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


def _author_response(author: User) -> PostAuthorResponse:
    return PostAuthorResponse(
        id=author.id,
        name=f"{author.first_name} {author.last_name}".strip() or author.username,
        handle=author.username,
        avatar=author.profile_image,
        verified=author.is_verified,
        premium=getattr(author, "premium", False),
    )


def map_db_to_response(db_post: Post, *, liked_by_me: bool = False) -> PostResponse:
    return PostResponse(
        id=db_post.id,
        author=_author_response(db_post.author),
        content=db_post.content,
        tags=list(db_post.tags) if db_post.tags else [],
        likes=db_post.likes_count,
        comments=db_post.comments_count,
        ago=get_ago_string(db_post.created_at),
        status=db_post.status,
        publish_at=db_post.publish_at,
        created_at=db_post.created_at,
        updated_at=db_post.updated_at,
        liked_by_me=liked_by_me,
    )


def _map_comment(comment: PostComment) -> PostCommentResponse:
    return PostCommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        author=_author_response(comment.author),
        content=comment.content,
        ago=get_ago_string(comment.created_at),
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        replies=[_map_comment(reply) for reply in getattr(comment, 'replies', [])]
    )


def _liked_post_ids(
    db: Session, user: User | None, post_ids: list[uuid.UUID]
) -> set[uuid.UUID]:
    """
    Which of ``post_ids`` the user has liked, in one query.

    One query for the page rather than one per post: the alternative is an
    N+1 on a feed listing, which is the shape the author relationship already
    had before the ``joinedload`` below.
    """
    if user is None or not post_ids:
        return set()
    rows = db.execute(
        select(PostLike.post_id).where(
            PostLike.user_id == user.id,
            PostLike.post_id.in_(post_ids),
        )
    ).all()
    return {row[0] for row in rows}


def _get_post_or_404(db: Session, post_id: uuid.UUID) -> Post:
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


def _recount(db: Session, db_post: Post) -> None:
    """
    Set both counters from the rows that back them.

    The previous handlers did `likes_count += 1` in Python, which is a
    read-modify-write: two concurrent likes both read *n* and both write
    *n + 1*. Counting in SQL means the counter is derived from the table that
    the unique constraint already protects, so it cannot drift from it.
    """
    db_post.likes_count = (
        db.execute(
            select(func.count())
            .select_from(PostLike)
            .where(PostLike.post_id == db_post.id)
        ).scalar_one()
        or 0
    )
    db_post.comments_count = (
        db.execute(
            select(func.count())
            .select_from(PostComment)
            .where(PostComment.post_id == db_post.id)
        ).scalar_one()
        or 0
    )


def _engagement(db_post: Post, *, liked_by_me: bool, changed: bool):
    return PostEngagementResponse(
        post_id=db_post.id,
        likes=db_post.likes_count,
        comments=db_post.comments_count,
        liked_by_me=liked_by_me,
        changed=changed,
    )


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[PostResponse])
def list_posts(
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_current_user_optional),
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    """
    The published feed.

    No longer wrapped in ``@cached``. The response now carries
    ``liked_by_me``, which makes it caller-dependent, and the cache key
    ``@cached`` builds only includes the caller when ``current_user`` arrives
    as a keyword argument (#1170). Caching a per-user field behind a key that
    may not name the user is how one account's liked state gets served to
    another, so the decorator comes off until that is fixed.
    """
    now = datetime.now(timezone.utc)
    query = (
        db.query(Post)
        .options(joinedload(Post.author))
        .filter(
            Post.status == "published",
            (Post.publish_at.is_(None)) | (Post.publish_at <= now),
        )
    )

    if current_user:
        blocked_ids = BlockService.get_blocked_and_blocking_user_ids(db, current_user.id)
        if blocked_ids:
            query = query.filter(~Post.author_id.in_(blocked_ids))

    db_posts = (
        query
        .order_by(Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    liked = _liked_post_ids(db, current_user, [p.id for p in db_posts])
    return [map_db_to_response(p, liked_by_me=p.id in liked) for p in db_posts]


@router.get("/drafts", response_model=list[PostResponse])
def list_drafts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    db_posts = (
        db.query(Post)
        .options(joinedload(Post.author))
        .filter(
            Post.author_id == current_user.id, Post.status.in_(["draft", "scheduled"])
        )
        .order_by(Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    liked = _liked_post_ids(db, current_user, [p.id for p in db_posts])
    return [map_db_to_response(p, liked_by_me=p.id in liked) for p in db_posts]


# ---------------------------------------------------------------------------
# Authoring
# ---------------------------------------------------------------------------


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
        # An explicit draft stays a draft. Previously any `publish_at` forced
        # the status to published or scheduled, so scheduling a draft was not
        # expressible: setting a date published it.
        if status_val != "draft":
            status_val = (
                "scheduled" if publish_at > datetime.now(timezone.utc) else "published"
            )

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
    db_post = _get_post_or_404(db, post_id)
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

    # Same rule as create: a post the author has put back into `draft` stays
    # there. The old code recomputed the status from `publish_at`
    # unconditionally, so once a post had a publish date it could never be
    # unpublished -- `{"status": "draft"}` was overwritten on the next line.
    if db_post.publish_at and db_post.status != "draft":
        pub_time = db_post.publish_at
        if pub_time.tzinfo is None:
            pub_time = pub_time.replace(tzinfo=timezone.utc)
        db_post.status = (
            "scheduled" if pub_time > datetime.now(timezone.utc) else "published"
        )

    db.commit()
    db.refresh(db_post)
    cache_manager.delete_pattern("post_*")

    liked = _liked_post_ids(db, current_user, [db_post.id])
    return map_db_to_response(db_post, liked_by_me=db_post.id in liked)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    db_post = _get_post_or_404(db, post_id)
    if db_post.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this post"
        )

    db.delete(db_post)
    db.commit()
    cache_manager.delete_pattern("post_*")
    return


# ---------------------------------------------------------------------------
# Likes
# ---------------------------------------------------------------------------


@router.post("/{post_id}/like", response_model=PostEngagementResponse)
def like_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Like a post. Idempotent: liking twice leaves one like.

    The insert is attempted and the unique constraint decides, rather than a
    SELECT deciding and the insert following. Two concurrent requests both
    pass a SELECT; only one wins the constraint.
    """
    db_post = _get_post_or_404(db, post_id)

    changed = True
    db.add(PostLike(post_id=db_post.id, user_id=current_user.id))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        db_post = _get_post_or_404(db, post_id)
        changed = False

    _recount(db, db_post)
    db.commit()
    db.refresh(db_post)
    cache_manager.delete_pattern("post_*")

    return _engagement(db_post, liked_by_me=True, changed=changed)


@router.delete("/{post_id}/like", response_model=PostEngagementResponse)
def unlike_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Remove the caller's like, if they had one.

    The old handler decremented unconditionally, so any authenticated user
    could take a post's count down one request at a time without ever having
    liked it. Removing a like you do not have now changes nothing.
    """
    db_post = _get_post_or_404(db, post_id)

    like = (
        db.query(PostLike)
        .filter(PostLike.post_id == db_post.id, PostLike.user_id == current_user.id)
        .first()
    )
    changed = like is not None
    if like is not None:
        db.delete(like)
        db.flush()

    _recount(db, db_post)
    db.commit()
    db.refresh(db_post)
    cache_manager.delete_pattern("post_*")

    return _engagement(db_post, liked_by_me=False, changed=changed)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


@router.get("/{post_id}/comments", response_model=list[PostCommentResponse])
def list_comments(
    post_id: uuid.UUID,
    db: Session = Depends(get_database),
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    """Read a post's comments. Returns top-level comments and their nested replies."""
    _get_post_or_404(db, post_id)

    comments = (
        db.query(PostComment)
        .options(
            joinedload(PostComment.author),
        )
        .filter(PostComment.post_id == post_id, PostComment.parent_id.is_(None))
        .order_by(PostComment.created_at.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return [_map_comment(c) for c in comments]


@router.post(
    "/{post_id}/comment",
    response_model=PostCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def comment_post(
    post_id: uuid.UUID,
    payload: PostCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Comment on a post.

    The body used to be validated and then discarded -- only
    ``comments_count`` moved. It is stored now, and the created comment is
    returned so the client can render it without a refetch.
    """
    db_post = _get_post_or_404(db, post_id)
    
    if payload.parent_id:
        parent_comment = db.query(PostComment).filter(PostComment.id == payload.parent_id).first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        if parent_comment.post_id != db_post.id:
            raise HTTPException(status_code=400, detail="Parent comment does not belong to this post")

    comment = PostComment(
        post_id=db_post.id,
        author_id=current_user.id,
        content=payload.comment,
        parent_id=payload.parent_id,
    )
    db.add(comment)
    db.flush()

    _recount(db, db_post)
    db.commit()
    db.refresh(comment)
    cache_manager.delete_pattern("post_*")

    return _map_comment(comment)


@router.delete(
    "/{post_id}/comment/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Delete a comment.

    Allowed for the comment's author and for the post's author, who is
    responsible for what sits under their post.
    """
    db_post = _get_post_or_404(db, post_id)

    comment = (
        db.query(PostComment)
        .filter(PostComment.id == comment_id, PostComment.post_id == post_id)
        .first()
    )
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")

    if current_user.id not in (comment.author_id, db_post.author_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this comment"
        )

    db.delete(comment)
    db.flush()
    _recount(db, db_post)
    db.commit()
    cache_manager.delete_pattern("post_*")
    return


@router.post(
    "/{post_id}/report",
    response_model=UserReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a post",
)
def report_post(
    post_id: uuid.UUID,
    report: UserReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    post = _get_post_or_404(db, post_id)
    if post.author_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot report your own post")

    db_report = UserReport(
        reporter_id=current_user.id,
        reported_id=post.author_id,
        post_id=post.id,
        reason=report.reason,
        description=report.description,
        status="pending",
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report
