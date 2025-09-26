from pydantic import BaseModel, EmailStr, Field, computed_field
from typing import Optional, List, Literal


# ---------------- User Schemas ----------------
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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = {"extra": "forbid"}


class TokenPairResponse(TokenResponse):
    refresh_token: str

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
    id: str
    owner: UserResponse
    comments: Optional[List["CommentResponse"]] = []
    reactions: Optional[List["ReactionResponse"]] = []

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }


# ---- V2 Enhanced ----
class ReactionSummary(BaseModel):
    code: int
    count: int

    @computed_field
    @property
    def emoji(self) -> str:
        return chr(self.code)


class BlogResponseV2(BlogBase):
    id: str
    owner: UserResponse
    created_at: Optional[str]
    updated_at: Optional[str]

    comments_count: int = 0
    reactions_summary: List[ReactionSummary] = []
    current_user_reaction: Optional[int] = None
    is_owner: bool = False  # new field

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }


# ---------------- Comment Schemas ----------------
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)

    model_config = {"extra": "forbid"}


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: str
    owner: UserResponse
    blog_id: str

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }


class CommentResponseV2(CommentBase):
    id: str
    owner: UserResponse
    blog_id: str
    created_at: Optional[str]
    updated_at: Optional[str]

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }


# ---------------- Reaction Schemas ----------------
AllowedReactions = Literal[128077, 10084, 128514, 128562, 128546, 128545]


class ReactionBase(BaseModel):
    code: AllowedReactions = Field(..., description="Allowed emoji code point")

    model_config = {"extra": "forbid"}


class ReactionCreate(ReactionBase):
    pass


class ReactionResponse(ReactionBase):
    id: str
    owner: UserResponse
    blog_id: str

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }

    @computed_field
    @property
    def emoji(self) -> str:
        return chr(self.code)


class ReactionResponseV2(ReactionBase):
    id: str
    owner: UserResponse
    blog_id: str

    model_config = {
        "from_attributes": True,
        "extra": "forbid"
    }

    @computed_field
    @property
    def emoji(self) -> str:
        return chr(self.code)


# ---------------- Model Linking ----------------
BlogResponse.model_rebuild()
BlogResponseV2.model_rebuild()
CommentResponse.model_rebuild()
CommentResponseV2.model_rebuild()
ReactionResponse.model_rebuild()
ReactionResponseV2.model_rebuild()

