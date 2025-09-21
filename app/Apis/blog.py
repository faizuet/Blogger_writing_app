from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schema, database, security
from app.models import User, Blog

router = APIRouter(prefix="/blogs", tags=["Blogs"])


# ---------- Create Blog ----------
@router.post("/", response_model=schema.BlogResponse, status_code=status.HTTP_201_CREATED)
def create_blog(
    blog: schema.BlogCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user),
):
    """Allow only writers to create blogs."""
    if current_user.role != "writer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only writers can create blogs")

    new_blog = Blog(title=blog.title, content=blog.content, owner_id=current_user.id)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog


# ---------- Get All Blogs ----------
@router.get("/", response_model=list[schema.BlogResponse])
def get_blogs(db: Session = Depends(database.get_db)):
    """Public endpoint: fetch all blogs (anyone can read)."""
    return db.query(Blog).all()


# ---------- Get Blog by ID ----------
@router.get("/{blog_id}", response_model=schema.BlogResponse)
def get_blog(blog_id: int, db: Session = Depends(database.get_db)):
    """Fetch a single blog by ID (anyone can read)."""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return blog

