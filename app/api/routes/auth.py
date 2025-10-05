from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import schemas
from app.api.routes.security_utils import (
    enforce_password_policy,
    hash_password,
    verify_password,
)
from app.core import security
from app.core.database import get_async_db
from app.models import User

# ---------------- Router setup ----------------
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------- Dependency ----------------
async def get_user_from_refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """Extract and validate a user from a refresh token."""
    payload = security.verify_token(refresh_token, token_type="refresh")
    user_id: str = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# ---------------- Routes ----------------
@router.post(
    "/signup",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_async_db)):
    """Register a new user."""
    email = user.email.lower()
    username = user.username.lower()

    enforce_password_policy(user.password)

    # Check for duplicate username or email
    if await db.scalar(select(User).where(User.username == username)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    if await db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {e}",
        )

    return new_user


@router.post("/login", response_model=schemas.TokenPairResponse)
async def login(user: schemas.UserLogin, db: AsyncSession = Depends(get_async_db)):
    """Authenticate user and return access + refresh tokens."""
    username = user.username.lower()

    db_user = await db.scalar(select(User).where(User.username == username))
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, access_exp = security.create_access_token(
        {"sub": str(db_user.id)}, with_exp=True
    )
    refresh_token, refresh_exp = security.create_refresh_token(
        {"sub": str(db_user.id)}, with_exp=True
    )

    return schemas.TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        access_expires_utc=datetime.fromtimestamp(access_exp, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        ),
        refresh_expires_utc=datetime.fromtimestamp(refresh_exp, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        ),
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_user_from_refresh_token),
):
    """Issue a new access token using a valid refresh token."""
    print(f"User {current_user.username} refreshed token from IP {request.client.host}")

    new_access_token, access_exp = security.create_access_token(
        {"sub": str(current_user.id)}, with_exp=True
    )

    return schemas.TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        access_expires_utc=datetime.fromtimestamp(access_exp, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        ),
    )

