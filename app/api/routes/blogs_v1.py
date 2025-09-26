from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from app.core.database import get_async_db
from app.core.security import get_current_user
from app.schemas import (
    BlogCreate, BlogUpdate, BlogResponse,
    CommentCreate, CommentResponse,
    ReactionCreate, ReactionResponse,
)
from app.models import User, Blog, Comment, Reaction

# ---------------- Router Setup ----------------
router = APIRouter(prefix="/v1/blogs", tags=["Blogs V1"])

# Allowed emoji codes 👍 ❤️ 😂 😲 😢 😡
ALLOWED_REACTIONS = {128077, 10084, 128514, 128562, 128546, 128545}


# ---------------- Blog Routes ----------------
@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog: BlogCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Create a blog (writers only)."""
    if current_user.role != "writer":
        raise HTTPException(status_code=403, detail="Only writers can create blogs")

    new_blog = Blog(title=blog.title, content=blog.content, owner_id=current_user.id)
    db.add(new_blog)
    await db.commit()
    await db.refresh(new_blog)

    new_blog.comments, new_blog.reactions = [], []
    return new_blog


@router.get("/", response_model=list[BlogResponse])
async def list_blogs(
    db: AsyncSession = Depends(get_async_db),
    current_user: User | None = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    search: str | None = None,
    author: str | None = None,
):
    """Public: Get blogs with pagination, search & filter."""
    query = select(Blog)

    if not current_user or current_user.role != "admin":
        query = query.where(Blog.deleted == False)

    if search:
        query = query.where(
            or_(
                Blog.title.ilike(f"%{search}%"),
                Blog.content.ilike(f"%{search}%")
            )
        )
    if author:
        query = query.join(User).where(User.username == author)

    result = await db.execute(query.offset(skip).limit(limit))
    blogs = result.scalars().all()

    for blog in blogs:
        comments_result = await db.execute(
            select(Comment).where(
                Comment.blog_id == blog.id,
                (Comment.deleted == False) | (current_user and current_user.role == "admin")
            )
        )
        blog.comments = comments_result.scalars().all()

        reactions_result = await db.execute(
            select(Reaction).where(Reaction.blog_id == blog.id)
        )
        blog.reactions = reactions_result.scalars().all()

    return blogs


@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User | None = Depends(get_current_user),
):
    """Public: Get a single blog by ID with comments & reactions."""
    query = select(Blog).where(Blog.id == blog_id)
    if not current_user or current_user.role != "admin":
        query = query.where(Blog.deleted == False)

    result = await db.execute(query)
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    comments_result = await db.execute(
        select(Comment).where(
            Comment.blog_id == blog.id,
            (Comment.deleted == False) | (current_user and current_user.role == "admin")
        )
    )
    blog.comments = comments_result.scalars().all()

    reactions_result = await db.execute(
        select(Reaction).where(Reaction.blog_id == blog.id)
    )
    blog.reactions = reactions_result.scalars().all()

    return blog


@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: str,
    blog_data: BlogUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Update a blog (only owner or admin)."""
    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    blog = result.scalar_one_or_none()

    if not blog or blog.deleted:
        raise HTTPException(status_code=404, detail="Blog not found")
    if blog.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    if blog_data.title is not None:
        blog.title = blog_data.title
    if blog_data.content is not None:
        blog.content = blog_data.content

    await db.commit()
    await db.refresh(blog)

    comments_result = await db.execute(select(Comment).where(Comment.blog_id == blog.id))
    blog.comments = comments_result.scalars().all()

    reactions_result = await db.execute(select(Reaction).where(Reaction.blog_id == blog.id))
    blog.reactions = reactions_result.scalars().all()

    return blog


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a blog (only owner or admin)."""
    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    blog = result.scalar_one_or_none()

    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    if blog.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    blog.deleted = True
    await db.commit()
    return None


# ---------------- Comment Routes ----------------
@router.post("/{blog_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    blog_id: str,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment (any logged-in user)."""
    result = await db.execute(select(Blog).where(Blog.id == blog_id, Blog.deleted == False))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    new_comment = Comment(content=comment.content, blog_id=blog.id, user_id=current_user.id)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


@router.get("/{blog_id}/comments", response_model=list[CommentResponse])
async def get_comments(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User | None = Depends(get_current_user),
):
    """Public: Get all comments for a blog."""
    query = select(Comment).where(Comment.blog_id == blog_id)
    if not current_user or current_user.role != "admin":
        query = query.where(Comment.deleted == False)

    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/{blog_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    blog_id: str,
    comment_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a comment (owner or admin)."""
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.blog_id == blog_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    comment.deleted = True
    await db.commit()
    return None


# ---------------- Reaction Routes ----------------
@router.post("/{blog_id}/reactions", response_model=ReactionResponse, status_code=status.HTTP_201_CREATED)
async def add_or_update_reaction(
    blog_id: str,
    reaction: ReactionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Add or update a reaction (any logged-in user)."""
    result = await db.execute(select(Blog).where(Blog.id == blog_id, Blog.deleted == False))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    if reaction.code not in ALLOWED_REACTIONS:
        raise HTTPException(status_code=400, detail="Invalid reaction code")

    result = await db.execute(
        select(Reaction).where(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id)
    )
    existing_reaction = result.scalar_one_or_none()

    if existing_reaction:
        existing_reaction.code = reaction.code
        await db.commit()
        await db.refresh(existing_reaction)
        return existing_reaction

    new_reaction = Reaction(code=reaction.code, blog_id=blog.id, user_id=current_user.id)
    db.add(new_reaction)
    await db.commit()
    await db.refresh(new_reaction)
    return new_reaction


@router.get("/{blog_id}/reactions", response_model=list[ReactionResponse])
async def get_reactions(blog_id: str, db: AsyncSession = Depends(get_async_db)):
    """Public: Get all reactions for a blog."""
    result = await db.execute(select(Reaction).where(Reaction.blog_id == blog_id))
    return result.scalars().all()


@router.delete("/{blog_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    blog_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Remove your reaction (only your own)."""
    result = await db.execute(
        select(Reaction).where(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id)
    )
    reaction = result.scalar_one_or_none()
    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")

    await db.delete(reaction)
    await db.commit()
    return None

