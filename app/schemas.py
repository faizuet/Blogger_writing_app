from pydantic import BaseModel, EmailStr, Field
from typing import Optional


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
    id: str  # UUID
    username: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


# -------- Blog Schemas --------
class BlogCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=1)


class BlogResponse(BaseModel):
    id: str  # UUID
    title: str
    content: str
    owner_id: str  # UUID

    class Config:
        from_attributes = True

