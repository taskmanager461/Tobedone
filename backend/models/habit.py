from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    frequency_type: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)
    frequency_days: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preferred_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_tracked_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="habits")
    logs = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")
