from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.models import User, UserRequest
from app.schemas import (
    FriendRequestAction,
    FriendRequestActionType,
    FriendRequestCreate,
    FriendRequestResponse,
    FriendRequestStatus,
    UserResponse,
)

router = APIRouter(prefix="/friends", tags=["Friends"])

# ---------------- Helper Functions ----------------
async def get_user_by_id(user_id: UUID, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_request_by_id(request_id: UUID, db: AsyncSession) -> UserRequest | None:
    result = await db.execute(
        select(UserRequest)
        .options(selectinload(UserRequest.sender), selectinload(UserRequest.receiver))
        .where(UserRequest.id == request_id)
    )
    return result.scalar_one_or_none()

async def get_pending_request_between(
    user1_id: UUID, user2_id: UUID, db: AsyncSession
) -> UserRequest | None:
    """Check if a pending friend request exists between two users."""
    result = await db.execute(
        select(UserRequest)
        .where(
            and_(
                or_(
                    and_(
                        UserRequest.sender_id == user1_id,
                        UserRequest.receiver_id == user2_id,
                    ),
                    and_(
                        UserRequest.sender_id == user2_id,
                        UserRequest.receiver_id == user1_id,
                    ),
                ),
                UserRequest.status == FriendRequestStatus.pending.value,
            )
        )
        .options(selectinload(UserRequest.sender), selectinload(UserRequest.receiver))
    )
    return result.scalar_one_or_none()

async def are_friends(user1_id: UUID, user2_id: UUID, db: AsyncSession) -> bool:
    """Check if two users are already friends."""
    result = await db.execute(
        select(UserRequest).where(
            UserRequest.status == FriendRequestStatus.accepted.value,
            or_(
                and_(
                    UserRequest.sender_id == user1_id,
                    UserRequest.receiver_id == user2_id,
                ),
                and_(
                    UserRequest.sender_id == user2_id,
                    UserRequest.receiver_id == user1_id,
                ),
            ),
        )
    )
    return result.scalar_one_or_none() is not None

def to_friend_request_response(req: UserRequest) -> FriendRequestResponse:
    """Convert ORM object -> schema."""
    # Use the Enum, but safely handle string values from DB
    status = (
        req.status
        if isinstance(req.status, str)
        else req.status.value
    )
    return FriendRequestResponse(
        id=req.id,
        sender=UserResponse.model_validate(req.sender, from_attributes=True),
        receiver=UserResponse.model_validate(req.receiver, from_attributes=True),
        status=FriendRequestStatus(status),
        created_at=req.created_at,
        updated_at=req.updated_at,
    )

# ---------------- Send Friend Request ----------------
@router.post("/request", response_model=FriendRequestResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    request: FriendRequestCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    if request.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot send a friend request to yourself.")

    receiver = await get_user_by_id(request.receiver_id, db)
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found.")

    if await are_friends(current_user.id, request.receiver_id, db):
        raise HTTPException(status_code=400, detail="You are already friends.")

    existing_request = await get_pending_request_between(current_user.id, request.receiver_id, db)
    if existing_request:
        raise HTTPException(status_code=400, detail="A pending friend request already exists.")

    new_request = UserRequest(
        sender_id=current_user.id,
        receiver_id=request.receiver_id,
        status=FriendRequestStatus.pending.value,
    )
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)

    return to_friend_request_response(new_request)

# ---------------- Respond to Friend Request ----------------
@router.patch("/request/{request_id}/response", response_model=FriendRequestResponse)
async def respond_friend_request(
    request_id: UUID,
    body: FriendRequestAction,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    friend_request = await get_request_by_id(request_id, db)
    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found.")
    if friend_request.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to respond.")
    if friend_request.status != FriendRequestStatus.pending.value:
        raise HTTPException(status_code=400, detail=f"Request already {friend_request.status}.")

    friend_request.status = (
        FriendRequestStatus.accepted.value
        if body.action == FriendRequestActionType.accept
        else FriendRequestStatus.rejected.value
    )
    await db.commit()
    await db.refresh(friend_request)
    return to_friend_request_response(friend_request)

# ---------------- List Incoming Requests ----------------
@router.get("/incoming", response_model=List[FriendRequestResponse])
async def list_incoming_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    status_filter: FriendRequestStatus = Query(FriendRequestStatus.pending),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(UserRequest)
        .where(
            UserRequest.receiver_id == current_user.id,
            UserRequest.status == status_filter.value,
        )
        .order_by(desc(UserRequest.created_at))
        .offset(skip)
        .limit(limit)
        .options(selectinload(UserRequest.sender), selectinload(UserRequest.receiver))
    )
    requests = result.scalars().all()
    return [to_friend_request_response(r) for r in requests]

# ---------------- List Outgoing Requests ----------------
@router.get("/outgoing", response_model=List[FriendRequestResponse])
async def list_outgoing_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    status_filter: FriendRequestStatus = Query(FriendRequestStatus.pending),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(UserRequest)
        .where(
            UserRequest.sender_id == current_user.id,
            UserRequest.status == status_filter.value,
        )
        .order_by(desc(UserRequest.created_at))
        .offset(skip)
        .limit(limit)
        .options(selectinload(UserRequest.sender), selectinload(UserRequest.receiver))
    )
    requests = result.scalars().all()
    return [to_friend_request_response(r) for r in requests]

# ---------------- List Friends ----------------
@router.get("/", response_model=List[UserResponse])
async def list_friends(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(User)
        .join(
            UserRequest,
            or_(
                and_(
                    UserRequest.sender_id == User.id,
                    UserRequest.receiver_id == current_user.id,
                ),
                and_(
                    UserRequest.receiver_id == User.id,
                    UserRequest.sender_id == current_user.id,
                ),
            ),
        )
        .where(UserRequest.status == FriendRequestStatus.accepted.value)
        .order_by(User.username)
        .offset(skip)
        .limit(limit)
    )
    friends = result.scalars().all()
    return [UserResponse.model_validate(f, from_attributes=True) for f in friends]

# ---------------- Cancel Friend Request ----------------
@router.delete("/request/{request_id}/cancel", response_model=FriendRequestResponse)
async def cancel_friend_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    friend_request = await get_request_by_id(request_id, db)
    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found.")
    if friend_request.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to cancel.")
    if friend_request.status != FriendRequestStatus.pending.value:
        raise HTTPException(status_code=400, detail="Only pending requests can be cancelled.")

    friend_request.status = FriendRequestStatus.cancelled.value
    await db.commit()
    await db.refresh(friend_request)
    return to_friend_request_response(friend_request)

# ---------------- Unfriend ----------------
@router.delete("/{friend_id}/unfriend", status_code=status.HTTP_204_NO_CONTENT)
async def unfriend_user(
    friend_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(UserRequest).where(
            UserRequest.status == FriendRequestStatus.accepted.value,
            or_(
                and_(
                    UserRequest.sender_id == current_user.id,
                    UserRequest.receiver_id == friend_id,
                ),
                and_(
                    UserRequest.receiver_id == current_user.id,
                    UserRequest.sender_id == friend_id,
                ),
            ),
        )
    )
    friendship = result.scalar_one_or_none()
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found.")

    friendship.status = FriendRequestStatus.cancelled.value
    await db.commit()

