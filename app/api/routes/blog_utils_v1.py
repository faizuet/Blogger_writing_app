from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Tuple

from app.models import Blog, Comment, Reaction, User
from app.schemas import CommentResponseV2, ReactionResponseV2, ReactionSummary

ALLOWED_REACTIONS = {128077, 10084, 128514, 128562, 128546, 128545}

# ---------------- Blog Helper ----------------
async def get_blog_or_404(db: AsyncSession, blog_id: str, current_user: Optional[User] = None) -> Blog:
    """Fetch a blog by ID or raise 404. Admin can access deleted blogs."""
    stmt = select(Blog).where(Blog.id == blog_id)
    if not current_user or current_user.role != "admin":
        stmt = stmt.where(Blog.deleted == False)

    result = await db.execute(stmt)
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return blog


# ---------------- Comments + Reactions ----------------
async def attach_comments_and_reactions(db: AsyncSession, blog: Blog, current_user: Optional[User] = None):
    """Attach comments and reactions to a blog respecting user roles."""

    # Comments
    comments_query = select(Comment).where(Comment.blog_id == blog.id)
    if not current_user or current_user.role != "admin":
        # Only non-deleted comments for writers and readers
        comments_query = comments_query.where(Comment.deleted == False)

    comments_result = await db.execute(comments_query)
    blog.comments = comments_result.scalars().all()

    # Reactions
    reactions_result = await db.execute(select(Reaction).where(Reaction.blog_id == blog.id))
    all_reactions = reactions_result.scalars().all()

    # Admin sees all; others see only non-deleted reactions
    if current_user and current_user.role == "admin":
        blog.reactions = all_reactions
    else:
        blog.reactions = [r for r in all_reactions if not r.deleted]

    return blog


# ---------------- Reaction Validation ----------------
def validate_reaction_code(code: int):
    """Validate reaction code."""
    if code not in ALLOWED_REACTIONS:
        raise HTTPException(status_code=400, detail="Invalid reaction code")


# ---------------- Bulk Helpers ----------------
async def fetch_comments(db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None) -> Dict[str, List[CommentResponseV2]]:
    """Fetch comments for multiple blogs respecting roles."""
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
                user=None,
                blog_id=c.blog_id,
                created_at=c.created_at.isoformat() if c.created_at else None,
                updated_at=c.updated_at.isoformat() if c.updated_at else None,
            )
        )
    return comment_map


async def fetch_reaction_data(
    db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None
) -> Tuple[Dict[str, List[ReactionResponseV2]], Dict[str, List[ReactionSummary]], Dict[str, int]]:
    """Fetch reactions and summaries for multiple blogs respecting roles."""
    result = await db.execute(select(Reaction).where(Reaction.blog_id.in_(blog_ids)))
    reactions = result.scalars().all()

    reaction_map: Dict[str, List[ReactionResponseV2]] = {}
    summary_map: Dict[str, List[ReactionSummary]] = {}
    user_reactions_map: Dict[str, int] = {}

    for r in reactions:
        # Admin sees all reactions, others only non-deleted
        if not r.deleted or (current_user and current_user.role == "admin"):
            reaction_map.setdefault(r.blog_id, []).append(ReactionResponseV2.from_orm(r))
            summary_map.setdefault(r.blog_id, []).append(ReactionSummary(code=r.code, count=1))

        # Track reactions of the current user
        if current_user and r.user_id == current_user.id:
            user_reactions_map[r.blog_id] = r.code

    return reaction_map, summary_map, user_reactions_map

