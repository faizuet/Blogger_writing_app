from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app import schema, database, security
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- Helpers ----------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------- Routes ----------
@router.post("/signup", response_model=schema.UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: schema.UserCreate, db: Session = Depends(database.get_db)):
    """Register a new user with role (writer or reader)."""
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(user: schema.UserLogin, db: Session = Depends(database.get_db)):
    """Authenticate user and return JWT token."""
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = security.create_access_token({"sub": db_user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "role": db_user.role,
        }
    }

