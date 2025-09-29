import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Text,
    Integer,
    Boolean,
    DateTime,
    Enum,
)
from sqlalchemy.orm import relationship
from app.core.database import Base

# -------- User Roles --------
USER_ROLES = ("reader", "writer", "admin")


# -------- User Model --------
class User(Base):
    __tablename__ = "users"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
        nullable=False,
    )
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Only allow roles from USER_ROLES
    role = Column(
        Enum(*USER_ROLES, name="user_roles"),
        default="writer",
        nullable=False,
    )

    blogs = relationship(
        "Blog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    comments = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reactions = relationship(
        "Reaction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# -------- Blog Model --------
class Blog(Base):
    __tablename__ = "blogs"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
        nullable=False,
    )
    title = Column(String(200), index=True, nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # v2 fields
    deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship(
        "User",
        back_populates="blogs",
        lazy="selectin",
    )
    comments = relationship(
        "Comment",
        back_populates="blog",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reactions = relationship(
        "Reaction",
        back_populates="blog",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# -------- Comment Model --------
class Comment(Base):
    __tablename__ = "comments"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
        nullable=False,
    )
    content = Column(Text, nullable=False)
    blog_id = Column(String(36), ForeignKey("blogs.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # v2 fields
    deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blog = relationship(
        "Blog",
        back_populates="comments",
        lazy="selectin",
    )
    user = relationship(
        "User",
        back_populates="comments",
        lazy="selectin",
    )


# -------- Reaction Model --------
class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
        nullable=False,
    )
    code = Column(Integer, nullable=False)
    blog_id = Column(String(36), ForeignKey("blogs.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # v2 fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blog = relationship(
        "Blog",
        back_populates="reactions",
        lazy="selectin",
    )
    user = relationship(
        "User",
        back_populates="reactions",
        lazy="selectin",
    )

