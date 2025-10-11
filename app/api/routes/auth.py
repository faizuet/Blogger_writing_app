import uuid
import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import schemas
from app.api.routes.utils.security_utils import (
    enforce_password_policy,
    hash_password,
    verify_password,
)
from app.core import security
from app.core.database import get_async_db
from app.models import User
from celery_tasks import send_verification_email

# ---------------- Router & Logger Setup ----------------
router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

# ---------------- Base URL ----------------
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


# ---------------- Helpers ----------------
async def get_user_from_refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """Extract and validate user from refresh token."""
    try:
        payload = security.verify_token(refresh_token, token_type="refresh")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ---------------- Signup ----------------
@router.post("/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_async_db)):
    """Register new user and send verification email."""
    email = user.email.lower()
    username = user.username.lower()
    enforce_password_policy(user.password)

    if await db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=409, detail="Username already exists")

    if await db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")

    verification_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(user.password),
        role=user.role,
        verification_token=verification_token,
        verification_token_expires=expires_at,
        is_verified=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    try:
        send_verification_email.delay(new_user.email, verification_token)
        logger.info(f"Verification email queued for {new_user.email}")
    except Exception as e:
        logger.exception(f"Failed to queue verification email for {new_user.email}: {e}")

    return new_user


# ---------------- Verify Email ----------------
@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_async_db)):
    """Verify user's email using a token."""
    user = await db.scalar(select(User).where(User.verification_token == token))

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if user.is_verified:
        return {"message": "Email already verified"}

    if not user.verification_token_expires or user.verification_token_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification token expired")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None

    await db.commit()

    logger.info(f"User {user.email} verified successfully")
    return {"message": "Email verified successfully"}


# ---------------- Login ----------------
@router.post("/login", response_model=schemas.TokenPairResponse)
async def login(user: schemas.UserLogin, db: AsyncSession = Depends(get_async_db)):
    """Authenticate user and return access + refresh tokens."""
    username = user.username.lower()
    db_user = await db.scalar(select(User).where(User.username == username))

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not db_user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

    access_token, access_exp = security.create_access_token({"sub": str(db_user.id)}, with_exp=True)
    refresh_token, refresh_exp = security.create_refresh_token({"sub": str(db_user.id)}, with_exp=True)

    return schemas.TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        access_expires_utc=datetime.fromtimestamp(access_exp, tz=timezone.utc).isoformat(),
        refresh_expires_utc=datetime.fromtimestamp(refresh_exp, tz=timezone.utc).isoformat(),
    )


# ---------------- Refresh Token ----------------
@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(request: Request, current_user: User = Depends(get_user_from_refresh_token)):
    """Issue new access token using refresh token."""
    logger.info(f"User {current_user.username} refreshed token from {request.client.host}")

    new_access_token, access_exp = security.create_access_token({"sub": str(current_user.id)}, with_exp=True)

    return schemas.TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        access_expires_utc=datetime.fromtimestamp(access_exp, tz=timezone.utc).isoformat(),
    )

