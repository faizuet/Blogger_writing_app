from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import (
    BlogCreate, BlogUpdate, BlogResponse,
    CommentCreate, CommentResponse,
    ReactionCreate, ReactionResponse
)
from app.models import User, Blog, Comment, Reaction

# Versioned router
router = APIRouter(prefix="/v1/blogs", tags=["Blogs V1"])

ALLOWED_REACTIONS = {128077, 10084, 128514, 128562, 128546, 128545}


# -------- Blog Routes --------
@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
def create_blog(
    blog: BlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ Create a blog (writers only, login required)."""
    if current_user.role != "writer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only writers can create blogs",
        )

    new_blog = Blog(title=blog.title, content=blog.content, owner_id=current_user.id)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)

    # Include empty comments & reactions
    new_blog.comments = []
    new_blog.reactions = []

    return new_blog


@router.get("/", response_model=list[BlogResponse])
def get_blogs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """ Public: Get all blogs with comments and reactions."""
    blogs = db.query(Blog).offset(skip).limit(limit).all()
    for blog in blogs:
        blog.comments = db.query(Comment).filter(Comment.blog_id == blog.id).all()
        blog.reactions = db.query(Reaction).filter(Reaction.blog_id == blog.id).all()
    return blogs


@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(blog_id: str, db: Session = Depends(get_db)):
    """ Public: Get a single blog by ID with comments and reactions."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    blog.comments = db.query(Comment).filter(Comment.blog_id == blog.id).all()
    blog.reactions = db.query(Reaction).filter(Reaction.blog_id == blog.id).all()
    return blog


@router.put("/{blog_id}", response_model=BlogResponse)
def update_blog(
    blog_id: str,
    blog_data: BlogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ Update a blog (only owner, login required)."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    if blog.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this blog")

    if blog_data.title is not None:
        blog.title = blog_data.title
    if blog_data.content is not None:
        blog.content = blog_data.content

    db.commit()
    db.refresh(blog)

    # Attach comments & reactions
    blog.comments = db.query(Comment).filter(Comment.blog_id == blog.id).all()
    blog.reactions = db.query(Reaction).filter(Reaction.blog_id == blog.id).all()
    return blog


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ Delete a blog (only owner, login required)."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    if blog.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this blog")

    db.delete(blog)
    db.commit()
    return None


# -------- Comment Routes --------
@router.post("/comments/{blog_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    blog_id: str,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ Add a comment (readers & writers, login required)."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    new_comment = Comment(content=comment.content, blog_id=blog.id, user_id=current_user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


@router.get("/comments/{blog_id}", response_model=list[CommentResponse])
def get_comments(blog_id: str, db: Session = Depends(get_db)):
    """🌍 Public: Get all comments for a blog (no login required)."""
    return db.query(Comment).filter(Comment.blog_id == blog_id).all()


@router.delete("/comments/{blog_id}/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    blog_id: str,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ Delete a comment (only the comment owner, login required)."""
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.blog_id == blog_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")

    db.delete(comment)
    db.commit()
    return None


# -------- Reaction Routes --------
@router.post("/reactions/{blog_id}", response_model=ReactionResponse, status_code=status.HTTP_201_CREATED)
def add_or_update_reaction(
    blog_id: str,
    reaction: ReactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ Add or update a reaction (readers & writers, login required)."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    if reaction.code not in ALLOWED_REACTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reaction code")

    existing_reaction = db.query(Reaction).filter(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id).first()
    if existing_reaction:
        existing_reaction.code = reaction.code
        db.commit()
        db.refresh(existing_reaction)
        return existing_reaction

    new_reaction = Reaction(code=reaction.code, blog_id=blog.id, user_id=current_user.id)
    db.add(new_reaction)
    db.commit()
    db.refresh(new_reaction)
    return new_reaction


@router.get("/reactions/{blog_id}", response_model=list[ReactionResponse])
def get_reactions(blog_id: str, db: Session = Depends(get_db)):
    """ Public: Get all reactions for a blog (no login required)."""
    return db.query(Reaction).filter(Reaction.blog_id == blog_id).all()


@router.delete("/reactions/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_reaction(
    blog_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ Remove your reaction (only your own, login required)."""
    reaction = db.query(Reaction).filter(Reaction.blog_id == blog_id, Reaction.user_id == current_user.id).first()
    if not reaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found")

    db.delete(reaction)
    db.commit()
    return None

