from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.routes.utils.blog_utils_v1 import (
    attach_comments_and_reactions,
    get_blog_or_404,
    validate_reaction_code,
)
from app.core.database import get_async_db
from app.core.security import get_current_user
from app.models import Blog, Comment, Reaction, User, UserRole
from app.schemas import (
    BlogCreate,
    BlogResponse,
    BlogUpdate,
    CommentCreate,
    CommentResponse,
    ReactionCreate,
    ReactionResponse,
)

# ---------------- Router Setup ----------------
router = APIRouter(prefix="/v1/blogs", tags=["Blogs V1"])

# ---------------- Blog Routes ----------------
@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog: BlogCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {UserRole.writer, UserRole.admin}:
        raise HTTPException(
            status_code=403, detail="Only writers or admins can create blogs"
        )

    new_blog = Blog(title=blog.title, content=blog.content, user_id=current_user.id)
    db.add(new_blog)
    await db.commit()
    await db.refresh(new_blog)
    new_blog.comments, new_blog.reactions = [], []
    return new_blog


@router.get("/", response_model=list[BlogResponse])
async def list_blogs(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    search: str | None = None,
    author: str | None = None,
):
    query = select(Blog).where(Blog.deleted.is_(False))
    if search:
        query = query.where(
            or_(Blog.title.ilike(f"%{search}%"), Blog.content.ilike(f"%{search}%"))
        )
    if author:
        query = query.join(User).where(User.username == author)

    result = await db.execute(query.offset(skip).limit(limit))
    blogs = result.scalars().unique().all()

    for blog in blogs:
        await attach_comments_and_reactions(db, blog, current_user=current_user)

    return blogs


@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(db, blog_id, current_user=current_user)
    return await attach_comments_and_reactions(db, blog, current_user=current_user)


@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: str,
    blog_data: BlogUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(db, blog_id, current_user=current_user)
    if blog.deleted:
        raise HTTPException(status_code=404, detail="Blog not found")

    # Only admin or owner can update
    if current_user.role != UserRole.admin and blog.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if blog_data.title is not None:
        blog.title = blog_data.title
    if blog_data.content is not None:
        blog.content = blog_data.content

    await db.commit()
    await db.refresh(blog)
    return await attach_comments_and_reactions(db, blog, current_user=current_user)


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(db, blog_id, current_user=current_user)
    if current_user.role != UserRole.admin and blog.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    blog.deleted = True
    await db.commit()

# ---------------- Comment Routes ----------------
@router.post(
    "/{blog_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    blog_id: str,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(db, blog_id, current_user=current_user)
    new_comment = Comment(
        content=comment.content, blog_id=blog.id, user_id=current_user.id
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


@router.get("/{blog_id}/comments", response_model=list[CommentResponse])
async def get_comments(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Comment).where(Comment.blog_id == blog_id, Comment.deleted.is_(False))
    )
    return result.scalars().all()


@router.delete(
    "/{blog_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_comment(
    blog_id: str,
    comment_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.blog_id == blog_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if current_user.role != UserRole.admin and comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    comment.deleted = True
    await db.commit()


# ---------------- Reaction Routes ----------------
@router.post(
    "/{blog_id}/reactions",
    response_model=ReactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_or_update_reaction(
    blog_id: str,
    reaction: ReactionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    blog = await get_blog_or_404(db, blog_id, current_user=current_user)
    validate_reaction_code(reaction.code)

    result = await db.execute(
        select(Reaction).where(
            Reaction.blog_id == blog_id, Reaction.user_id == current_user.id
        )
    )
    existing_reaction = result.scalar_one_or_none()

    if existing_reaction:
        existing_reaction.code = reaction.code
        await db.commit()
        await db.refresh(existing_reaction)
        return existing_reaction

    new_reaction = Reaction(
        code=reaction.code, blog_id=blog.id, user_id=current_user.id
    )
    db.add(new_reaction)
    await db.commit()
    await db.refresh(new_reaction)
    return new_reaction


@router.get("/{blog_id}/reactions", response_model=list[ReactionResponse])
async def get_reactions(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Reaction).where(Reaction.blog_id == blog_id))
    return result.scalars().all()


@router.delete("/{blog_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    blog_id: str,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Reaction).where(Reaction.blog_id == blog_id)
    if current_user.role == UserRole.admin and user_id:
        query = query.where(Reaction.user_id == user_id)
    else:
        query = query.where(Reaction.user_id == current_user.id)

    result = await db.execute(query)
    reaction = result.scalar_one_or_none()
    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")
    await db.delete(reaction)
    await db.commit()

