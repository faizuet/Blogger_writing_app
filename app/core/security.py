import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from dotenv import load_dotenv
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_async_db
from app import models

# ---------------- Load Config ----------------
load_dotenv()

SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback_secret_key")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# OAuth2 scheme for FastAPI (for access tokens only)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------- Token Helpers ----------------
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    with_exp: bool = False
) -> str | Tuple[str, int]:
    """Generate a short-lived JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    if with_exp:
        return token, int(expire.timestamp())
    return token


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    with_exp: bool = False
) -> str | Tuple[str, int]:
    """Generate a long-lived JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    if with_exp:
        return token, int(expire.timestamp())
    return token


def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}.",
            )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{token_type.capitalize()} token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid {token_type} token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------- Dependencies ----------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
):
    """Fetch the current authenticated user using access token."""
    payload = verify_token(token, token_type="access")
    user_id: str = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
):
    """Optional user dependency (returns None if no token)."""
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None

