from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import (
    BlogCreate, BlogUpdate, BlogResponseV2,
    CommentCreate, CommentResponseV2,
    ReactionCreate, ReactionResponseV2,
    UserResponse
)
from app.models import User, Blog, Comment, Reaction

router = APIRouter(prefix="/v2/blogs", tags=["Blogs V2"])

ALLOWED_REACTIONS = {128077, 10084, 128514, 128562, 128546, 128545}


# -------- Optional user dependency --------
def get_current_user_optional(current_user: Optional[User] = Depends(get_current_user)):
    """Return current user if authenticated, else None (used for public GET routes)."""
    return current_user


# -------- Helper Functions --------
def wrap_response(data):
    """Standardize API response format."""
    return {"status": "success", "data": data}


def get_blog_with_counts(db: Session, blog_id: str, current_user: User | None = None):
    """Fetch a blog along with comment count, reactions summary, and user's reaction if logged in."""
    blog = db.query(Blog).filter(Blog.id == blog_id, Blog.deleted == False).first()
    if not blog:
        return None

    comments_count = db.query(func.count(Comment.id))\
        .filter(Comment.blog_id == blog_id, Comment.deleted == False).scalar()

    reactions_data = (
        db.query(Reaction.code, func.count(Reaction.id))
        .filter(Reaction.blog_id == blog_id)
        .group_by(Reaction.code)
        .all()
    )
    reactions_summary = {code: count for code, count in reactions_data}

    current_user_reaction = None
    if current_user:
        user_reaction = db.query(Reaction)\
            .filter(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id).first()
        if user_reaction:
            current_user_reaction = user_reaction.code

    return BlogResponseV2(
        id=blog.id,
        title=blog.title,
        content=blog.content,
        owner=UserResponse.from_orm(blog.owner),
        created_at=blog.created_at.isoformat() if blog.created_at else None,
        updated_at=blog.updated_at.isoformat() if blog.updated_at else None,
        comments_count=comments_count,
        reactions_summary=reactions_summary,
        current_user_reaction=current_user_reaction
    )


# -------- Blog Routes --------
@router.post("/", response_model=BlogResponseV2, status_code=status.HTTP_201_CREATED)
def create_blog(blog: BlogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new blog post. Only users with role `writer` can create blogs."""
    if current_user.role != "writer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only writers can create blogs")

    new_blog = Blog(
        title=blog.title,
        content=blog.content,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return get_blog_with_counts(db, new_blog.id, current_user)


@router.get("/", response_model=list[BlogResponseV2])
def get_blogs(skip: int = 0, limit: int = 100, search: str | None = None,
              db: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    """Get a list of blogs. Publicly accessible. Supports pagination and search by title."""
    query = db.query(Blog).filter(Blog.deleted == False)
    if search:
        query = query.filter(Blog.title.ilike(f"%{search}%"))
    blogs = query.offset(skip).limit(limit).all()
    return [get_blog_with_counts(db, blog.id, current_user) for blog in blogs]


@router.get("/{blog_id}", response_model=BlogResponseV2)
def get_blog(blog_id: str, db: Session = Depends(get_db),
             current_user: User | None = Depends(get_current_user_optional)):
    """Get a single blog by ID. Publicly accessible."""
    blog = get_blog_with_counts(db, blog_id, current_user)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return blog


@router.put("/{blog_id}", response_model=BlogResponseV2)
def update_blog(blog_id: str, blog_data: BlogUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update a blog (only owner can update)."""
    blog = db.query(Blog).filter(Blog.id == blog_id, Blog.deleted == False).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    if blog.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this blog")

    if blog_data.title is not None:
        blog.title = blog_data.title
    if blog_data.content is not None:
        blog.content = blog_data.content
    blog.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(blog)
    return get_blog_with_counts(db, blog_id, current_user)


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(blog_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Soft delete a blog (only owner can delete)."""
    blog = db.query(Blog).filter(Blog.id == blog_id, Blog.deleted == False).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    if blog.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this blog")
    blog.deleted = True
    blog.updated_at = datetime.utcnow()
    db.commit()
    return wrap_response(None)


# -------- Comment Routes --------
@router.post("/comments/{blog_id}", response_model=CommentResponseV2, status_code=status.HTTP_201_CREATED)
def add_comment(blog_id: str, comment: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Add a comment to a blog. Requires authentication."""
    blog = db.query(Blog).filter(Blog.id == blog_id, Blog.deleted == False).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    new_comment = Comment(
        content=comment.content,
        blog_id=blog.id,
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted=False
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return CommentResponseV2(
        id=new_comment.id,
        content=new_comment.content,
        owner=UserResponse.from_orm(current_user),
        blog_id=blog.id,
        created_at=new_comment.created_at.isoformat(),
        updated_at=new_comment.updated_at.isoformat()
    )


@router.get("/comments/{blog_id}", response_model=list[CommentResponseV2])
def get_comments(blog_id: str, db: Session = Depends(get_db),
                 current_user: User | None = Depends(get_current_user_optional)):
    """Get all comments for a blog. Publicly accessible."""
    comments = db.query(Comment).filter(Comment.blog_id == blog_id, Comment.deleted == False).all()
    return [
        CommentResponseV2(
            id=c.id,
            content=c.content,
            owner=UserResponse.from_orm(c.user),
            blog_id=c.blog_id,
            created_at=c.created_at.isoformat() if c.created_at else None,
            updated_at=c.updated_at.isoformat() if c.updated_at else None
        )
        for c in comments
    ]


@router.delete("/comments/{blog_id}/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(blog_id: str, comment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a comment (only comment owner can delete)."""
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.blog_id == blog_id, Comment.deleted == False).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")
    comment.deleted = True
    comment.updated_at = datetime.utcnow()
    db.commit()
    return wrap_response(None)


# -------- Reaction Routes --------
@router.post("/reactions/{blog_id}", response_model=ReactionResponseV2, status_code=status.HTTP_201_CREATED)
def add_or_update_reaction(blog_id: str, reaction: ReactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Add or update a reaction to a blog. Requires authentication."""
    blog = db.query(Blog).filter(Blog.id == blog_id, Blog.deleted == False).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    if reaction.code not in ALLOWED_REACTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reaction code")

    existing_reaction = db.query(Reaction).filter(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id).first()
    if existing_reaction:
        existing_reaction.code = reaction.code
        existing_reaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_reaction)
        return ReactionResponseV2.from_orm(existing_reaction)
    else:
        new_reaction = Reaction(
            code=reaction.code,
            blog_id=blog.id,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_reaction)
        db.commit()
        db.refresh(new_reaction)
        return ReactionResponseV2.from_orm(new_reaction)


@router.get("/reactions/{blog_id}")
def get_reactions(blog_id: str, db: Session = Depends(get_db),
                  current_user: User | None = Depends(get_current_user_optional)):
    """Get all reactions for a blog. Publicly accessible."""
    reactions = db.query(Reaction).filter(Reaction.blog_id == blog_id).all()
    total_reactions = len(reactions)
    return wrap_response({
        "reactions": [ReactionResponseV2.from_orm(r) for r in reactions],
        "total_reactions": total_reactions
    })


@router.delete("/reactions/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_reaction(blog_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove a user's reaction from a blog. Requires authentication."""
    reaction = db.query(Reaction).filter(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id).first()
    if not reaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found")
    db.delete(reaction)
    db.commit()
    return wrap_response(None)

