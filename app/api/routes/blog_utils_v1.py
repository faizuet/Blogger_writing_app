from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Blog, Comment, Reaction, User
from app.schemas import CommentResponseV2, ReactionResponseV2, ReactionSummary

# Allowed emoji codes (👍, ❤️, 😂, 😲, 😢, 😡)
ALLOWED_REACTIONS = {128077, 10084, 128514, 128562, 128546, 128545}


# ---------------- Blog Helpers ----------------
async def get_blog_or_404(
    db: AsyncSession, blog_id: str, current_user: Optional[User] = None
) -> Blog:
    """Fetch a blog by ID or raise 404. Admins can access deleted blogs."""
    stmt = select(Blog).where(Blog.id == blog_id)

    if not current_user or current_user.role != "admin":
        stmt = stmt.where(Blog.deleted.is_(False))

    result = await db.execute(stmt)
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    return blog


# ---------------- Comments + Reactions ----------------
async def attach_comments_and_reactions(
    db: AsyncSession, blog: Blog, current_user: Optional[User] = None
) -> Blog:
    """Attach comments and reactions to a single blog, respecting user roles."""

    # Comments
    comments_stmt = select(Comment).where(Comment.blog_id == blog.id)
    if not current_user or current_user.role != "admin":
        comments_stmt = comments_stmt.where(Comment.deleted.is_(False))

    comments_result = await db.execute(comments_stmt)
    blog.comments = comments_result.scalars().all()

    # Reactions
    reactions_result = await db.execute(select(Reaction).where(Reaction.blog_id == blog.id))
    reactions = reactions_result.scalars().all()

    blog.reactions = (
        reactions if (current_user and current_user.role == "admin") else [r for r in reactions if not r.deleted]
    )

    return blog


# ---------------- Reaction Validation ----------------
def validate_reaction_code(code: int) -> None:
    """Raise 400 if reaction code is invalid."""
    if code not in ALLOWED_REACTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reaction code")


# ---------------- Bulk Helpers ----------------
async def fetch_comments(
    db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None
) -> Dict[str, List[CommentResponseV2]]:
    """Fetch comments for multiple blogs, respecting user roles."""
    stmt = select(Comment).where(Comment.blog_id.in_(blog_ids))

    if not current_user or current_user.role != "admin":
        stmt = stmt.where(Comment.deleted.is_(False))

    result = await db.execute(stmt)
    comments = result.scalars().all()

    comment_map: Dict[str, List[CommentResponseV2]] = {}
    for c in comments:
        comment_map.setdefault(c.blog_id, []).append(
            CommentResponseV2(
                id=c.id,
                content=c.content,
                user=None,
                blog_id=c.blog_id,
                created_at=c.created_at.isoformat() if c.created_at else None,
                updated_at=c.updated_at.isoformat() if c.updated_at else None,
            )
        )

    return comment_map


from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Reaction, User
from app.schemas import ReactionResponseV2, ReactionSummary


async def fetch_reaction_data(
    db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None
) -> Tuple[
    Dict[str, List[ReactionResponseV2]],
    Dict[str, List[ReactionSummary]],
    Dict[str, int],
]:
    """
    Fetch reactions and summaries for multiple blogs, respecting roles.

    Returns:
        - reaction_map: blog_id -> list of individual reactions
        - summary_map: blog_id -> list of (reaction_code, count)
        - user_reactions_map: blog_id -> current user's reaction code
    """

    # --- Fetch reactions for response mapping ---
    stmt = select(Reaction).where(Reaction.blog_id.in_(blog_ids))
    if not (current_user and current_user.role == "admin"):
        stmt = stmt.where(Reaction.deleted.is_(False))

    reactions_result = await db.execute(stmt)
    reactions = reactions_result.scalars().all()

    reaction_map: Dict[str, List[ReactionResponseV2]] = {}
    user_reactions_map: Dict[str, int] = {}

    for r in reactions:
        reaction_map.setdefault(r.blog_id, []).append(ReactionResponseV2.from_orm(r))

        # Track current user’s reaction
        if current_user and r.user_id == current_user.id:
            user_reactions_map[r.blog_id] = r.code

    # --- Fetch aggregated reaction summaries ---
    summary_stmt = (
        select(Reaction.blog_id, Reaction.code, func.count().label("count"))
        .where(Reaction.blog_id.in_(blog_ids))
        .group_by(Reaction.blog_id, Reaction.code)
    )

    if not (current_user and current_user.role == "admin"):
        summary_stmt = summary_stmt.where(Reaction.deleted.is_(False))

    summary_result = await db.execute(summary_stmt)

    summary_map: Dict[str, List[ReactionSummary]] = {}
    for blog_id, code, count in summary_result.all():
        summary_map.setdefault(blog_id, []).append(ReactionSummary(code=code, count=count))

    return reaction_map, summary_map, user_reactions_map



