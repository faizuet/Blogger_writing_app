import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Index,
    Integer, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# -------- User Roles Enum --------
class UserRole(PyEnum):
    reader = "reader"
    writer = "writer"
    admin = "admin"


# -------- Friend Request Status Enum --------
class FriendRequestStatus(PyEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


# -------- User Model --------
class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        Enum(UserRole, name="user_roles"), default=UserRole.writer, nullable=False
    )

    # Relationships
    blogs = relationship(
        "Blog", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    comments = relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    reactions = relationship(
        "Reaction", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    sent_requests = relationship(
        "UserRequest",
        foreign_keys="UserRequest.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    received_requests = relationship(
        "UserRequest",
        foreign_keys="UserRequest.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# -------- Blog Model --------
class Blog(Base):
    __tablename__ = "blogs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    title = Column(String(200), index=True, nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="blogs", lazy="selectin")
    comments = relationship(
        "Comment", back_populates="blog", cascade="all, delete-orphan", lazy="selectin"
    )
    reactions = relationship(
        "Reaction", back_populates="blog", cascade="all, delete-orphan", lazy="selectin"
    )


# -------- Comment Model --------
class Comment(Base):
    __tablename__ = "comments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    content = Column(Text, nullable=False)
    blog_id = Column(
        UUID(as_uuid=True), ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blog = relationship("Blog", back_populates="comments", lazy="selectin")
    user = relationship("User", back_populates="comments", lazy="selectin")


# -------- Reaction Model --------
class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    code = Column(Integer, nullable=False)  # validated in schema (AllowedReactions)
    blog_id = Column(
        UUID(as_uuid=True), ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blog = relationship("Blog", back_populates="reactions", lazy="selectin")
    user = relationship("User", back_populates="reactions", lazy="selectin")


# -------- UserRequest Model (Friend Requests) --------
class UserRequest(Base):
    __tablename__ = "user_requests"
    __table_args__ = (
        UniqueConstraint("sender_id", "receiver_id", name="uq_sender_receiver"),
        Index("idx_receiver_status", "receiver_id", "status"),
        Index("idx_sender_status", "sender_id", "status"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    sender_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    receiver_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(
        Enum(FriendRequestStatus, name="request_status"),
        default=FriendRequestStatus.pending,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sender = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_requests", lazy="selectin"
    )
    receiver = relationship(
        "User", foreign_keys=[receiver_id], back_populates="received_requests", lazy="selectin"
    )

