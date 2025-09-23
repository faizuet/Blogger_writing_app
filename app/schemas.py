from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from __main__ import CommentResponse, ReactionResponse


# -------- User Schemas --------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[str] = "reader"


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: str

    model_config = {"from_attributes": True}


# -------- Blog Schemas --------
class BlogBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=1)


class BlogCreate(BlogBase):
    pass


class BlogUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = Field(None, min_length=1)


class BlogResponse(BlogBase):
    id: str
    owner: UserResponse
    comments: Optional[List["CommentResponse"]] = []
    reactions: Optional[List["ReactionResponse"]] = []

    model_config = {"from_attributes": True}


# -------- Comment Schemas --------
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: str
    user: UserResponse
    blog_id: str

    model_config = {"from_attributes": True}


# -------- Reaction Enum & Schemas --------
class ReactionType(str, Enum):
    like = "like"
    love = "love"
    haha = "haha"
    wow = "wow"
    sad = "sad"
    angry = "angry"


class ReactionBase(BaseModel):
    type: ReactionType


class ReactionCreate(ReactionBase):
    pass


class ReactionResponse(ReactionBase):
    id: str
    user: UserResponse
    blog_id: str

    model_config = {"from_attributes": True}


# Forward references for nested models
BlogResponse.model_rebuild()

