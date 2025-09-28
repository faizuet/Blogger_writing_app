from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from app import schemas
from app.core.database import get_async_db
from app.core import security
from app.models import User

# ---------------- Router setup ----------------
router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------- Helper functions ----------------
def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------- Dependency to get user from refresh token ----------------
async def get_current_user_from_refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Extract user from a refresh token.
    Can be used as a dependency to inject `current_user` in endpoints.
    """
    payload = security.verify_token(refresh_token, token_type="refresh")
    username: str = payload.get("sub")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ---------------- Routes ----------------
@router.post("/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_async_db)):
    """Create a new user account."""
    # Check duplicate username
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    # Check duplicate email
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.TokenPairResponse)
async def login(user: schemas.UserLogin, db: AsyncSession = Depends(get_async_db)):
    """Authenticate user and return access + refresh tokens."""
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token({"sub": db_user.username})
    refresh_token = security.create_refresh_token({"sub": db_user.username})

    return schemas.TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user_from_refresh_token)
):
    """
    Refresh access token using a refresh token.
    `current_user` is injected from refresh token like other endpoints.
    """
    # Optional: log activity
    print(f"User {current_user.username} refreshed token from IP {request.client.host}")

    new_access_token = security.create_access_token({"sub": current_user.username})
    return schemas.TokenResponse(access_token=new_access_token, token_type="bearer")

