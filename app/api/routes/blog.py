from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import (
    BlogCreate, BlogResponse,
    CommentCreate, CommentResponse,
    ReactionCreate, ReactionResponse, ReactionType
)
from app.models import User, Blog, Comment, Reaction

router = APIRouter(prefix="/blogs", tags=["Blogs"])


# -------- Blog Routes --------
@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
def create_blog(
    blog: BlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a blog (writers only)."""
    if current_user.role != "writer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only writers can create blogs",
        )

    new_blog = Blog(title=blog.title, content=blog.content, owner_id=current_user.id)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog


@router.get("/", response_model=list[BlogResponse])
def get_blogs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all blogs with optional pagination."""
    return db.query(Blog).offset(skip).limit(limit).all()


@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(blog_id: str, db: Session = Depends(get_db)):
    """Get a blog by ID."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return blog


@router.put("/{blog_id}", response_model=BlogResponse)
def update_blog(
    blog_id: str,
    blog_data: BlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a blog (only owner can update)."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    if blog.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this blog")

    blog.title = blog_data.title
    blog.content = blog_data.content
    db.commit()
    db.refresh(blog)
    return blog


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a blog (only owner can delete)."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    if blog.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this blog")

    db.delete(blog)
    db.commit()
    return None


# -------- Comment Routes --------
@router.post("/{blog_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    blog_id: str,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to a blog (readers & writers)."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    new_comment = Comment(content=comment.content, blog_id=blog.id, user_id=current_user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


@router.get("/{blog_id}/comments", response_model=list[CommentResponse])
def get_comments(blog_id: str, db: Session = Depends(get_db)):
    """Get all comments for a blog."""
    return db.query(Comment).filter(Comment.blog_id == blog_id).all()


@router.delete("/{blog_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    blog_id: str,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a comment (only the comment owner can delete)."""
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.blog_id == blog_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")

    db.delete(comment)
    db.commit()
    return None


# -------- Reaction Routes --------
@router.post("/{blog_id}/reactions", response_model=ReactionResponse, status_code=status.HTTP_201_CREATED)
def add_or_update_reaction(
    blog_id: str,
    reaction: ReactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add or update a reaction on a blog (readers & writers)."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    # Validate the reaction type
    if reaction.type not in ReactionType.__members__.values():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reaction type")

    existing_reaction = (
        db.query(Reaction).filter(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id).first()
    )

    if existing_reaction:
        existing_reaction.type = reaction.type
        db.commit()
        db.refresh(existing_reaction)
        return existing_reaction
    else:
        new_reaction = Reaction(type=reaction.type, blog_id=blog.id, user_id=current_user.id)
        db.add(new_reaction)
        db.commit()
        db.refresh(new_reaction)
        return new_reaction


@router.get("/{blog_id}/reactions", response_model=list[ReactionResponse])
def get_reactions(blog_id: str, db: Session = Depends(get_db)):
    """Get all reactions for a blog."""
    return db.query(Reaction).filter(Reaction.blog_id == blog_id).all()


@router.delete("/{blog_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
def remove_reaction(
    blog_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a user's reaction from a blog."""
    reaction = db.query(Reaction).filter(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id).first()
    if not reaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found")

    db.delete(reaction)
    db.commit()
    return None

