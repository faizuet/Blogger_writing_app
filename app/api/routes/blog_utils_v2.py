from typing import Optional, List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models import Blog, Comment, Reaction, User
from app.schemas import (
    CommentResponseV2, ReactionResponseV2,
    UserResponse, ReactionSummary, BlogResponseV2
)

# Allowed emoji codes 👍 ❤️ 😂 😲 😢 😡
ALLOWED_REACTIONS = {128077, 10084, 128514, 128562, 128546, 128545}


# ---------------- Helper Dependencies ----------------
async def get_blog_or_404(blog_id: str, db: AsyncSession, current_user: Optional[User] = None) -> Blog:
    stmt = select(Blog).where(Blog.id == blog_id)
    if not current_user or current_user.role != "admin":
        stmt = stmt.where(Blog.deleted == False)
    result = await db.execute(stmt)
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return blog


# ---------------- Reaction + Counts Helper ----------------
async def fetch_reaction_data(
    db: AsyncSession,
    blog_ids: List[str],
    current_user: Optional[User] = None
) -> Tuple[Dict[str, List[ReactionResponseV2]], Dict[str, List[ReactionSummary]], Dict[str, int]]:
    """
    Fetch reactions, summaries, and current user reactions in bulk.
    - Non-admins: ignore deleted reactions in both lists and summaries.
    - Admins: see all reactions including deleted.
    """
    # Fetch all reactions (filtered for non-admins)
    stmt = select(Reaction).where(Reaction.blog_id.in_(blog_ids))
    if not current_user or current_user.role != "admin":
        stmt = stmt.where(Reaction.deleted == False)
    result = await db.execute(stmt)
    reactions = result.scalars().all()

    # Map reactions for response
    reaction_map: Dict[str, List[ReactionResponseV2]] = {}
    for r in reactions:
        reaction_map.setdefault(r.blog_id, []).append(ReactionResponseV2.from_orm(r))

    # Reaction summaries (grouped by code, excluding deleted for non-admins)
    summary_stmt = select(
        Reaction.blog_id, Reaction.code, func.count(Reaction.id)
    ).where(
        Reaction.blog_id.in_(blog_ids)
    )
    if not current_user or current_user.role != "admin":
        summary_stmt = summary_stmt.where(Reaction.deleted == False)
    summary_stmt = summary_stmt.group_by(Reaction.blog_id, Reaction.code)

    summary_result = await db.execute(summary_stmt)
    summary_map: Dict[str, List[ReactionSummary]] = {}
    for blog_id, code, count in summary_result.all():
        summary_map.setdefault(blog_id, []).append(ReactionSummary(code=code, count=count))

    # Current user reactions
    user_reactions_map: Dict[str, int] = {}
    if current_user:
        user_stmt = select(Reaction.blog_id, Reaction.code).where(
            Reaction.blog_id.in_(blog_ids),
            Reaction.user_id == current_user.id
        )
        if not current_user.role == "admin":
            user_stmt = user_stmt.where(Reaction.deleted == False)
        user_result = await db.execute(user_stmt)
        user_reactions_map = {bid: code for bid, code in user_result.all()}

    return reaction_map, summary_map, user_reactions_map

# ---------------- Comments Helper ----------------
async def fetch_comments(db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None) -> Dict[str, List[CommentResponseV2]]:
    """Fetch all non-deleted comments for multiple blogs in bulk. Admin sees all."""
    stmt = select(Comment).where(Comment.blog_id.in_(blog_ids))
    if not current_user or current_user.role != "admin":
        stmt = stmt.where(Comment.deleted == False)

    result = await db.execute(stmt)
    comments = result.scalars().all()

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


# ---------------- Counts Helper ----------------
async def fetch_blog_counts(db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None):
    """Fetch comment counts, reaction summaries, and user reactions in bulk."""
    # Comment counts
    comments_stmt = select(Comment.blog_id, func.count(Comment.id)).where(
        Comment.blog_id.in_(blog_ids)
    )
    if not current_user or current_user.role != "admin":
        comments_stmt = comments_stmt.where(Comment.deleted == False)
    comments_stmt = comments_stmt.group_by(Comment.blog_id)
    comments_result = await db.execute(comments_stmt)
    comments_count_map = {bid: count for bid, count in comments_result.all()}

    _, reactions_summary_map, user_reactions_map = await fetch_reaction_data(db, blog_ids, current_user)

    return comments_count_map, reactions_summary_map, user_reactions_map


# ---------------- Mapping ----------------
def map_blog_response(
    blog: Blog,
    comments_count_map,
    reactions_summary_map,
    user_reactions_map,
    current_user: Optional[User]
) -> BlogResponseV2:
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
        is_owner=(current_user.id == blog.user_id) if current_user else False,
    )

