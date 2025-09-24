from pydantic import BaseModel, EmailStr, Field, computed_field
from typing import Optional, List, TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from __main__ import CommentResponse, ReactionResponse


# -------- Auth Schemas --------
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (usually 'bearer')")

    model_config = {"extra": "forbid"}


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[str] = "reader"

    model_config = {"extra": "forbid"}


class UserLogin(BaseModel):
    username: str
    password: str

    model_config = {"extra": "forbid"}


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: str

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }


# -------- Blog Schemas --------
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
    id: str
    owner: UserResponse
    comments: Optional[List["CommentResponse"]] = []
    reactions: Optional[List["ReactionResponse"]] = []

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }


# -------- Comment Schemas --------
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)

    model_config = {"extra": "forbid"}


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: str
    user: UserResponse
    blog_id: str

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }


# -------- Reaction Schemas --------
AllowedReactions = Literal[128077, 10084, 128514, 128558, 128546, 128545]
# 👍, ❤️, 😂, 😮, 😢, 😡


class ReactionBase(BaseModel):
    code: AllowedReactions = Field(
        ...,
        description="Unicode code point of allowed emoji reaction"
    )

    model_config = {"extra": "forbid"}


class ReactionCreate(ReactionBase):
    pass


class ReactionResponse(ReactionBase):
    id: str
    user: UserResponse
    blog_id: str

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }

    @computed_field
    @property
    def emoji(self) -> str:
        """Return the actual emoji character from its Unicode code point."""
        return chr(self.code)


# Forward references for nested models
BlogResponse.model_rebuild()

