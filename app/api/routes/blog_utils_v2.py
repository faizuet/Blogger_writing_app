from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Blog, Comment, Reaction, User
from app.schemas import (
    BlogResponseV2, CommentResponseV2,
    ReactionResponseV2, ReactionSummary, UserResponse
)

# Allowed emoji codes 👍 ❤️ 😂 😲 😢 😡
ALLOWED_REACTIONS = {128077, 10084, 128514, 128562, 128546, 128545}


# ---------------- Blog Fetch ----------------
async def get_blog_or_404(
    blog_id: str, db: AsyncSession, current_user: Optional[User] = None
) -> Blog:
    """Fetch a blog by ID or raise 404.
    Admin can access deleted blogs, non-admins cannot."""
    stmt = select(Blog).where(Blog.id == blog_id)
    if not (current_user and current_user.role == "admin"):
        stmt = stmt.where(Blog.deleted == False)

    result = await db.execute(stmt)
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog not found"
        )
    return blog


# ---------------- Reactions ----------------
async def fetch_reaction_data(
    db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None
) -> Tuple[
    Dict[str, List[ReactionResponseV2]],
    Dict[str, List[ReactionSummary]],
    Dict[str, int],
]:
    """
    Fetch reactions, summaries, and current user reactions in bulk.
    - Non-admins: only non-deleted reactions.
    - Admins: include deleted ones.
    """
    # Raw reactions
    stmt = select(Reaction).where(Reaction.blog_id.in_(blog_ids))
    if not (current_user and current_user.role == "admin"):
        stmt = stmt.where(Reaction.deleted == False)
    reactions = (await db.execute(stmt)).scalars().all()

    # Map reactions
    reaction_map: Dict[str, List[ReactionResponseV2]] = {}
    for r in reactions:
        reaction_map.setdefault(r.blog_id, []).append(ReactionResponseV2.from_orm(r))

    # Summaries
    summary_stmt = (
        select(Reaction.blog_id, Reaction.code, func.count(Reaction.id))
        .where(Reaction.blog_id.in_(blog_ids))
        .group_by(Reaction.blog_id, Reaction.code)
    )
    if not (current_user and current_user.role == "admin"):
        summary_stmt = summary_stmt.where(Reaction.deleted == False)

    summary_result = await db.execute(summary_stmt)
    summary_map: Dict[str, List[ReactionSummary]] = {}
    for bid, code, count in summary_result.all():
        summary_map.setdefault(bid, []).append(ReactionSummary(code=code, count=count))

    # Current user reactions
    user_reactions_map: Dict[str, int] = {}
    if current_user:
        user_stmt = select(Reaction.blog_id, Reaction.code).where(
            Reaction.blog_id.in_(blog_ids),
            Reaction.user_id == current_user.id
        )
        if current_user.role != "admin":
            user_stmt = user_stmt.where(Reaction.deleted == False)
        user_reactions_map = {
            bid: code for bid, code in (await db.execute(user_stmt)).all()
        }

    return reaction_map, summary_map, user_reactions_map


# ---------------- Comments ----------------
async def fetch_comments(
    db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None
) -> Dict[str, List[CommentResponseV2]]:
    """Fetch comments for multiple blogs.
    Non-admins only see non-deleted comments."""
    stmt = select(Comment).where(Comment.blog_id.in_(blog_ids))
    if not (current_user and current_user.role == "admin"):
        stmt = stmt.where(Comment.deleted == False)

    comments = (await db.execute(stmt)).scalars().all()

    comment_map: Dict[str, List[CommentResponseV2]] = {}
    for c in comments:
        comment_map.setdefault(c.blog_id, []).append(
            CommentResponseV2(
                id=c.id,
                content=c.content,
                user=UserResponse.from_orm(c.user),
                blog_id=c.blog_id,
                created_at=c.created_at.isoformat() if c.created_at else None,
                updated_at=c.updated_at.isoformat() if c.updated_at else None,
            )
        )
    return comment_map


# ---------------- Blog Counts ----------------
async def fetch_blog_counts(
    db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None
) -> Tuple[Dict[str, int], Dict[str, List[ReactionSummary]], Dict[str, int]]:
    """Fetch comment counts, reaction summaries, and user reactions in bulk."""
    # Comment counts
    comments_stmt = (
        select(Comment.blog_id, func.count(Comment.id))
        .where(Comment.blog_id.in_(blog_ids))
        .group_by(Comment.blog_id)
    )
    if not (current_user and current_user.role == "admin"):
        comments_stmt = comments_stmt.where(Comment.deleted == False)

    comments_count_map = {
        bid: count for bid, count in (await db.execute(comments_stmt)).all()
    }

    _, reactions_summary_map, user_reactions_map = await fetch_reaction_data(
        db, blog_ids, current_user
    )
    return comments_count_map, reactions_summary_map, user_reactions_map


# ---------------- Response Mapping ----------------
def map_blog_response(
    blog: Blog,
    comments_count_map: Dict[str, int],
    reactions_summary_map: Dict[str, List[ReactionSummary]],
    user_reactions_map: Dict[str, int],
    current_user: Optional[User],
) -> BlogResponseV2:
    """Assemble final BlogResponseV2."""
    return BlogResponseV2(
        id=blog.id,
        title=blog.title,
        content=blog.content,
        user=UserResponse.from_orm(blog.user),
        created_at=blog.created_at.isoformat() if blog.created_at else None,
        updated_at=blog.updated_at.isoformat() if blog.updated_at else None,
        comments_count=comments_count_map.get(blog.id, 0),
        reactions_summary=reactions_summary_map.get(blog.id, []),
        current_user_reaction=user_reactions_map.get(blog.id),
        is_owner=bool(current_user and current_user.id == blog.user_id),
    )

