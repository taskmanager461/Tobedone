from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Integer, String, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class UserSocialProfile(Base):
    __tablename__ = "user_social_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    public_profile: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_level: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_streak: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_xp: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="social_profile")


class Friendship(Base):
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[FriendshipStatus] = mapped_column(SQLEnum(FriendshipStatus), default=FriendshipStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    friend = relationship("User", foreign_keys=[friend_id])
