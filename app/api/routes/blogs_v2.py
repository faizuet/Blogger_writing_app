# app/routes/blogs_v2.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.schemas import (
    BlogCreate, BlogUpdate, BlogResponseV2,
    CommentCreate, CommentResponseV2,
    ReactionCreate, ReactionResponseV2,
    UserResponse, BulkReactionItem,
)
from app.models import User, Blog, Comment, Reaction
from app.api.routes.blog_utils_v2 import (
    get_blog_or_404,
    fetch_blog_counts,
    fetch_comments,
    fetch_reaction_data,
    map_blog_response,
)

router = APIRouter(prefix="/v2/blogs", tags=["Blogs V2"])

# ---------------- Blog CRUD ----------------
@router.post("/", response_model=BlogResponseV2, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog: BlogCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"writer", "admin"}:
        raise HTTPException(status_code=403, detail="Only writers or admins can create blogs")

    new_blog = Blog(
        title=blog.title,
        content=blog.content,
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_blog)
    await db.commit()
    await db.refresh(new_blog)

    return map_blog_response(new_blog, {}, {}, {}, current_user)

@router.get("/", response_model=list[BlogResponseV2])
async def get_blogs(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    sort_by: str = "newest",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Blog).where(Blog.deleted.is_(False))

    if search:
        query = query.where(Blog.title.ilike(f"%{search}%"))

    if sort_by == "newest":
        query = query.order_by(Blog.created_at.desc())
    elif sort_by == "most_commented":
        comments_subq = (
            select(Comment.blog_id, func.count(Comment.id).label("c_count"))
            .where(Comment.deleted.is_(False))
            .group_by(Comment.blog_id)
            .subquery()
        )
        query = query.outerjoin(comments_subq, Blog.id == comments_subq.c.blog_id)
        query = query.order_by(func.coalesce(comments_subq.c.c_count, 0).desc())
    elif sort_by == "most_reacted":
        reactions_subq = (
            select(Reaction.blog_id, func.count(Reaction.id).label("r_count"))
            .group_by(Reaction.blog_id)
            .subquery()
        )
        query = query.outerjoin(reactions_subq, Blog.id == reactions_subq.c.blog_id)
        query = query.order_by(func.coalesce(reactions_subq.c.r_count, 0).desc())

    result = await db.execute(query.offset(skip).limit(limit))
    blogs = result.scalars().all()

    if not blogs:
        return []

    blog_ids = [b.id for b in blogs]
    comments_map, reactions_map, user_reactions = await fetch_blog_counts(db, blog_ids, current_user)

    return [map_blog_response(b, comments_map, reactions_map, user_reactions, current_user) for b in blogs]

@router.get("/{blog_id}", response_model=BlogResponseV2)
async def get_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(blog_id, db, current_user)
    comments_map, reactions_map, user_reactions = await fetch_blog_counts(db, [blog_id], current_user)
    return map_blog_response(blog, comments_map, reactions_map, user_reactions, current_user)

@router.put("/{blog_id}", response_model=BlogResponseV2)
async def update_blog(
    blog_id: str,
    blog_data: BlogUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(blog_id, db, current_user)

    if blog.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    if blog_data.title is not None:
        blog.title = blog_data.title
    if blog_data.content is not None:
        blog.content = blog_data.content
    blog.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(blog)

    comments_map, reactions_map, user_reactions = await fetch_blog_counts(db, [blog_id], current_user)
    return map_blog_response(blog, comments_map, reactions_map, user_reactions, current_user)

@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(blog_id, db, current_user)

    if blog.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    blog.deleted = True
    blog.updated_at = datetime.utcnow()
    await db.commit()
    return None

# ---------------- Comment CRUD ----------------
@router.post("/{blog_id}/comments", response_model=CommentResponseV2, status_code=status.HTTP_201_CREATED)
async def add_comment(
    blog_id: str,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(blog_id, db, current_user)
    new_comment = Comment(
        content=comment.content,
        blog_id=blog.id,
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted=False,
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
        updated_at=new_comment.updated_at.isoformat(),
    )

@router.delete("/{blog_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    blog_id: str,
    comment_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id, Comment.blog_id == blog_id))
    comment = result.scalar_one_or_none()

    if not comment or (comment.deleted and current_user.role != "admin"):
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    comment.deleted = True
    comment.updated_at = datetime.utcnow()
    await db.commit()
    return None

# ---------------- Reaction CRUD ----------------
@router.post("/{blog_id}/reactions", response_model=ReactionResponseV2, status_code=status.HTTP_201_CREATED)
async def add_or_update_reaction(
    blog_id: str,
    reaction: ReactionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(blog_id, db, current_user)

    if reaction.code not in {128077, 10084, 128514, 128562, 128546, 128545}:
        raise HTTPException(status_code=400, detail="Invalid reaction code")

    result = await db.execute(select(Reaction).where(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id))
    existing_reaction = result.scalar_one_or_none()

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
        updated_at=datetime.utcnow(),
    )
    db.add(new_reaction)
    await db.commit()
    await db.refresh(new_reaction)
    return ReactionResponseV2.from_orm(new_reaction)

@router.delete("/{blog_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reaction(
    blog_id: str,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    await get_blog_or_404(blog_id, db, current_user)

    query = select(Reaction).where(Reaction.blog_id == blog_id)
    if user_id:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can delete other user reactions")
        query = query.where(Reaction.user_id == user_id)
    else:
        query = query.where(Reaction.user_id == current_user.id)

    result = await db.execute(query)
    reaction = result.scalar_one_or_none()
    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")

    await db.delete(reaction)
    await db.commit()
    return None

# ---------------- Bulk Endpoints ----------------
@router.get("/bulk-comments", response_model=dict[str, list[CommentResponseV2]])
async def get_bulk_comments(
    blog_ids: list[str] = Query(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await fetch_comments(db, blog_ids)

@router.get("/bulk-reactions", response_model=dict[str, BulkReactionItem])
async def get_bulk_reactions(
    blog_ids: list[str] = Query(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    reaction_map, summary_map, user_reactions = await fetch_reaction_data(db, blog_ids, current_user)

    return {
        bid: BulkReactionItem(
            reactions=reaction_map.get(bid, []),
            summary=summary_map.get(bid, []),
            current_user_reaction=user_reactions.get(bid),
        )
        for bid in blog_ids
    }

