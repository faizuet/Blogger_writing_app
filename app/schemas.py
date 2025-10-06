import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, RootModel, computed_field


# ---------------- User Roles Enum ----------------
class UserRole(str, Enum):
    reader = "reader"
    writer = "writer"
    admin = "admin"


# ---------------- User Schemas ----------------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: UserRole

    model_config = {"extra": "forbid"}


class UserLogin(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=50, description="Username only for login"
    )
    password: str

    model_config = {"extra": "forbid"}


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    role: UserRole

    model_config = {"from_attributes": True, "extra": "forbid"}


# ---------------- Token Schemas ----------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    access_expires_utc: Optional[str] = None

    model_config = {"extra": "forbid"}


class TokenPairResponse(TokenResponse):
    refresh_token: str
    refresh_expires_utc: Optional[str] = None

    model_config = {"extra": "forbid"}


# ---------------- Blog Schemas ----------------
class BlogBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=1)

    model_config = {"extra": "forbid"}


class BlogCreate(BlogBase):
    pass


class BlogUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = Field(None, min_length=1)

    model_config = {"extra": "forbid"}


class BlogResponse(BlogBase):
    id: uuid.UUID
    user: UserResponse
    comments: Optional[List["CommentResponse"]] = []
    reactions: Optional[List["ReactionResponse"]] = []

    model_config = {"from_attributes": True, "extra": "forbid"}


class ReactionSummary(BaseModel):
    code: int
    count: int

    @computed_field
    @property
    def emoji(self) -> str:
        return chr(self.code)


class BlogResponseV2(BlogBase):
    id: uuid.UUID
    user: UserResponse
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    comments_count: int = 0
    reactions_summary: List[ReactionSummary] = []
    current_user_reaction: Optional[int]
    is_owner: bool = False

    model_config = {"from_attributes": True, "extra": "forbid"}


# ---------------- Comment Schemas ----------------
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)

    model_config = {"extra": "forbid"}


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: uuid.UUID
    user: UserResponse
    blog_id: uuid.UUID

    model_config = {"from_attributes": True, "extra": "forbid"}


class CommentResponseV2(CommentBase):
    id: uuid.UUID
    user: UserResponse
    blog_id: uuid.UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True, "extra": "forbid"}


class BulkCommentsResponse(RootModel):
    root: Dict[uuid.UUID, List[CommentResponseV2]]


# ---------------- Reaction Schemas ----------------
AllowedReactions = Literal[128077, 10084, 128514, 128562, 128546, 128545]


class ReactionBase(BaseModel):
    code: AllowedReactions = Field(..., description="Allowed emoji code point")

    model_config = {"extra": "forbid"}


class ReactionCreate(ReactionBase):
    pass


class ReactionResponse(ReactionBase):
    id: uuid.UUID
    user: UserResponse
    blog_id: uuid.UUID

    model_config = {"from_attributes": True, "extra": "forbid"}

    @computed_field
    @property
    def emoji(self) -> str:
        return chr(self.code)


class ReactionResponseV2(ReactionBase):
    id: uuid.UUID
    user: UserResponse
    blog_id: uuid.UUID

    model_config = {"from_attributes": True, "extra": "forbid"}

    @computed_field
    @property
    def emoji(self) -> str:
        return chr(self.code)


class BulkReactionItem(BaseModel):
    reactions: List[ReactionResponseV2]
    summary: List[ReactionSummary]
    current_user_reaction: Optional[int]


class BulkReactionsResponse(RootModel):
    root: Dict[uuid.UUID, BulkReactionItem]


# ---------------- Friend Request Schemas ----------------
class FriendRequestStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class FriendRequestActionType(str, Enum):
    accept = "accept"
    reject = "reject"


class FriendRequestBase(BaseModel):
    receiver_id: uuid.UUID = Field(..., description="ID of the user to send request to")

    model_config = {"extra": "forbid"}


class FriendRequestCreate(FriendRequestBase):
    pass


class FriendRequestAction(BaseModel):
    action: FriendRequestActionType = Field(
        ..., description="Action to perform on a friend request"
    )

    model_config = {"extra": "forbid"}


class FriendRequestResponse(BaseModel):
    id: uuid.UUID
    sender: UserResponse
    receiver: UserResponse
    status: FriendRequestStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "forbid"}


# ---------------- Model Linking ----------------
BlogResponse.model_rebuild()
BlogResponseV2.model_rebuild()
CommentResponse.model_rebuild()
CommentResponseV2.model_rebuild()
ReactionResponse.model_rebuild()
ReactionResponseV2.model_rebuild()

