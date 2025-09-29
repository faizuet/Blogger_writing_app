from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional, Literal, List, Dict

from app.core.database import get_async_db
from app.core.security import get_current_user, get_current_user_optional as _get_current_user_optional
from app.schemas import (
    BlogCreate, BlogUpdate, BlogResponseV2,
    CommentCreate, CommentResponseV2,
    ReactionCreate, ReactionResponseV2,
    UserResponse, ReactionSummary, BulkReactionItem
)
from app.models import User, Blog, Comment, Reaction

router = APIRouter(prefix="/v2/blogs", tags=["Blogs V2"])

ALLOWED_REACTIONS = {128077, 10084, 128514, 128562, 128546, 128545}

# ---------------- Helper Dependencies ----------------
async def get_current_user_optional(current_user: Optional[User] = Depends(_get_current_user_optional)):
    return current_user

async def get_blog_or_404(blog_id: str, db: AsyncSession, current_user: Optional[User] = None) -> Blog:
    stmt = select(Blog).where(Blog.id == blog_id)
    if not current_user or current_user.role != "admin":
        stmt = stmt.where(Blog.deleted == False)
    result = await db.execute(stmt)
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return blog

# ---------------- Helper Functions ----------------
async def fetch_blog_counts(db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None):
    """Fetch comment counts, reaction summaries, and user reactions in bulk."""
    # Comment counts
    comments_stmt = select(Comment.blog_id, func.count(Comment.id)).where(
        Comment.blog_id.in_(blog_ids),
        Comment.deleted == False
    ).group_by(Comment.blog_id)
    comments_result = await db.execute(comments_stmt)
    comments_count_map = {bid: count for bid, count in comments_result.all()}

    # Reaction summaries
    reactions_stmt = select(Reaction.blog_id, Reaction.code, func.count(Reaction.id)).where(
        Reaction.blog_id.in_(blog_ids)
    ).group_by(Reaction.blog_id, Reaction.code)
    reactions_result = await db.execute(reactions_stmt)
    reactions_summary_map: Dict[str, List[ReactionSummary]] = {}
    for blog_id, code, count in reactions_result.all():
        reactions_summary_map.setdefault(blog_id, []).append(ReactionSummary(code=code, count=count))

    # Current user reactions
    user_reactions_map: Dict[str, int] = {}
    if current_user:
        user_reactions_stmt = select(Reaction.blog_id, Reaction.code).where(
            Reaction.blog_id.in_(blog_ids),
            Reaction.user_id == current_user.id
        )
        user_reactions_result = await db.execute(user_reactions_stmt)
        user_reactions_map = {bid: code for bid, code in user_reactions_result.all()}

    return comments_count_map, reactions_summary_map, user_reactions_map

async def fetch_comments(db: AsyncSession, blog_ids: List[str]):
    """Fetch all non-deleted comments for multiple blogs in bulk."""
    result = await db.execute(
        select(Comment).where(Comment.blog_id.in_(blog_ids), Comment.deleted == False)
    )
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

async def fetch_reactions(db: AsyncSession, blog_ids: List[str], current_user: Optional[User] = None):
    """Fetch all reactions and summaries for multiple blogs in bulk."""
    result = await db.execute(select(Reaction).where(Reaction.blog_id.in_(blog_ids)))
    reactions = result.scalars().all()
    reaction_map: Dict[str, List[ReactionResponseV2]] = {}
    for r in reactions:
        reaction_map.setdefault(r.blog_id, []).append(ReactionResponseV2.from_orm(r))

    summary_stmt = select(Reaction.blog_id, Reaction.code, func.count(Reaction.id)).where(
        Reaction.blog_id.in_(blog_ids)
    ).group_by(Reaction.blog_id, Reaction.code)
    summary_result = await db.execute(summary_stmt)
    summary_map: Dict[str, List[ReactionSummary]] = {}
    for blog_id, code, count in summary_result.all():
        summary_map.setdefault(blog_id, []).append(ReactionSummary(code=code, count=count))

    user_reactions_map: Dict[str, int] = {}
    if current_user:
        user_reactions_stmt = select(Reaction.blog_id, Reaction.code).where(
            Reaction.blog_id.in_(blog_ids),
            Reaction.user_id == current_user.id
        )
        user_reactions_result = await db.execute(user_reactions_stmt)
        user_reactions_map = {bid: code for bid, code in user_reactions_result.all()}

    return reaction_map, summary_map, user_reactions_map

def map_blog_response(blog: Blog, comments_count_map, reactions_summary_map, user_reactions_map, current_user: Optional[User]):
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

# ---------------- Blog CRUD ----------------
@router.post("/", response_model=BlogResponseV2, status_code=status.HTTP_201_CREATED)
async def create_blog(blog: BlogCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in {"writer", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only writers or admins can create blogs")
    new_blog = Blog(
        title=blog.title,
        content=blog.content,
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_blog)
    await db.commit()
    await db.refresh(new_blog)
    return map_blog_response(new_blog, {}, {}, {}, current_user)

@router.get("/", response_model=List[BlogResponseV2])
async def get_blogs(
    skip: int = 0, limit: int = 100, search: Optional[str] = None,
    sort_by: Literal["newest", "most_commented", "most_reacted"] = "newest",
    db: AsyncSession = Depends(get_async_db), current_user: Optional[User] = Depends(get_current_user_optional)
):
    query = select(Blog)
    if not current_user or current_user.role != "admin":
        query = query.where(Blog.deleted == False)
    if search:
        query = query.where(Blog.title.ilike(f"%{search}%"))

    # Sorting
    if sort_by == "newest":
        query = query.order_by(Blog.created_at.desc())
    elif sort_by == "most_commented":
        comments_subq = select(
            Comment.blog_id,
            func.count(Comment.id).label("c_count")
        ).where(Comment.deleted == False).group_by(Comment.blog_id).subquery()
        query = query.outerjoin(comments_subq, Blog.id == comments_subq.c.blog_id).order_by(func.coalesce(comments_subq.c.c_count, 0).desc())
    elif sort_by == "most_reacted":
        reactions_subq = select(
            Reaction.blog_id,
            func.count(Reaction.id).label("r_count")
        ).group_by(Reaction.blog_id).subquery()
        query = query.outerjoin(reactions_subq, Blog.id == reactions_subq.c.blog_id).order_by(func.coalesce(reactions_subq.c.r_count, 0).desc())

    result = await db.execute(query.offset(skip).limit(limit))
    blogs = result.scalars().all()
    blog_ids = [b.id for b in blogs]
    if not blog_ids:
        return []

    comments_count_map, reactions_summary_map, user_reactions_map = await fetch_blog_counts(db, blog_ids, current_user)
    return [map_blog_response(b, comments_count_map, reactions_summary_map, user_reactions_map, current_user) for b in blogs]

@router.get("/{blog_id}", response_model=BlogResponseV2)
async def get_blog(blog_id: str, db: AsyncSession = Depends(get_async_db), current_user: Optional[User] = Depends(get_current_user_optional)):
    blog = await get_blog_or_404(blog_id, db, current_user)
    comments_count_map, reactions_summary_map, user_reactions_map = await fetch_blog_counts(db, [blog_id], current_user)
    return map_blog_response(blog, comments_count_map, reactions_summary_map, user_reactions_map, current_user)

@router.put("/{blog_id}", response_model=BlogResponseV2)
async def update_blog(blog_id: str, blog_data: BlogUpdate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    blog = await get_blog_or_404(blog_id, db, current_user)
    if blog.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this blog")
    if blog_data.title is not None:
        blog.title = blog_data.title
    if blog_data.content is not None:
        blog.content = blog_data.content
    blog.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(blog)
    comments_count_map, reactions_summary_map, user_reactions_map = await fetch_blog_counts(db, [blog_id], current_user)
    return map_blog_response(blog, comments_count_map, reactions_summary_map, user_reactions_map, current_user)

@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(blog_id: str, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    blog = await get_blog_or_404(blog_id, db, current_user)
    if blog.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this blog")
    blog.deleted = True
    blog.updated_at = datetime.utcnow()
    await db.commit()
    return None

# ---------------- Comment CRUD ----------------
@router.post("/{blog_id}/comments", response_model=CommentResponseV2, status_code=status.HTTP_201_CREATED)
async def add_comment(blog_id: str, comment: CommentCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    blog = await get_blog_or_404(blog_id, db, current_user)
    new_comment = Comment(
        content=comment.content,
        blog_id=blog.id,
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted=False
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return CommentResponseV2(
        id=new_comment.id,
        content=new_comment.content,
        user=UserResponse.from_orm(current_user),
        blog_id=blog.id,
        created_at=new_comment.created_at.isoformat(),
        updated_at=new_comment.updated_at.isoformat()
    )

@router.delete("/{blog_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(blog_id: str, comment_id: str, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    stmt = select(Comment).where(Comment.id == comment_id, Comment.blog_id == blog_id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if not comment or (comment.deleted and current_user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")
    comment.deleted = True
    comment.updated_at = datetime.utcnow()
    await db.commit()
    return None

# ---------------- Reaction CRUD ----------------
@router.post("/{blog_id}/reactions", response_model=ReactionResponseV2, status_code=status.HTTP_201_CREATED)
async def add_or_update_reaction(blog_id: str, reaction: ReactionCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    blog = await get_blog_or_404(blog_id, db, current_user)
    if reaction.code not in ALLOWED_REACTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reaction code")
    existing_result = await db.execute(select(Reaction).where(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id))
    existing_reaction = existing_result.scalar_one_or_none()
    if existing_reaction:
        existing_reaction.code = reaction.code
        existing_reaction.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_reaction)
        return ReactionResponseV2.from_orm(existing_reaction)
    new_reaction = Reaction(
        code=reaction.code,
        blog_id=blog.id,
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_reaction)
    await db.commit()
    await db.refresh(new_reaction)
    return ReactionResponseV2.from_orm(new_reaction)

@router.delete("/{blog_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reaction(blog_id: str, user_id: Optional[str] = None, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    blog = await get_blog_or_404(blog_id, db, current_user)
    stmt = select(Reaction).where(Reaction.blog_id == blog_id)
    if user_id:
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete other user reactions")
        stmt = stmt.where(Reaction.user_id == user_id)
    else:
        stmt = stmt.where(Reaction.user_id == current_user.id)
    result = await db.execute(stmt)
    reaction = result.scalar_one_or_none()
    if not reaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found")
    await db.delete(reaction)
    await db.commit()
    return None

# ---------------- Bulk Endpoints ----------------
@router.get("/bulk-comments", response_model=Dict[str, List[CommentResponseV2]])
async def get_bulk_comments(blog_ids: List[str] = Query(...), db: AsyncSession = Depends(get_async_db)):
    return await fetch_comments(db, blog_ids)

@router.get("/bulk-reactions", response_model=Dict[str, BulkReactionItem])
async def get_bulk_reactions(blog_ids: List[str] = Query(...), db: AsyncSession = Depends(get_async_db), current_user: Optional[User] = Depends(get_current_user_optional)):
    reaction_map, summary_map, user_reactions_map = await fetch_reactions(db, blog_ids, current_user)
    response: Dict[str, BulkReactionItem] = {}
    for bid in blog_ids:
        response[bid] = BulkReactionItem(
            reactions=reaction_map.get(bid, []),
            summary=summary_map.get(bid, []),
            current_user_reaction=user_reactions_map.get(bid)
        )
    return response

