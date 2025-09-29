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
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def enforce_password_policy(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Password must be at least 8 characters long")
    if not any(c.isdigit() for c in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Password must contain at least one number")
    if not any(c.isalpha() for c in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Password must contain at least one letter")


# ---------------- Dependency ----------------
async def get_current_user_from_refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """Extract user from a refresh token (string ID safe)."""
    payload = security.verify_token(refresh_token, token_type="refresh")
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Use string ID directly (matches DB)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ---------------- Routes ----------------
@router.post("/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_async_db)):
    email = user.email.lower()
    enforce_password_policy(user.password)

    # Check duplicate username
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    # Check duplicate email
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    new_user = User(
        username=user.username,
        email=email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception:
        await db.rollback()
        raise

    return new_user


@router.post("/login", response_model=schemas.TokenPairResponse)
async def login(user: schemas.UserLogin, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid username or password",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token, access_exp = security.create_access_token({"sub": str(db_user.id)}, with_exp=True)
    refresh_token, refresh_exp = security.create_refresh_token({"sub": str(db_user.id)}, with_exp=True)

    return schemas.TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_exp,
        refresh_expires_in=refresh_exp
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user_from_refresh_token)
):
    print(f"User {current_user.username} refreshed token from IP {request.client.host}")

    new_access_token, access_exp = security.create_access_token(
        {"sub": str(current_user.id)},
        with_exp=True
    )
    return schemas.TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=access_exp
    )

