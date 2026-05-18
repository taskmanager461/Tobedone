from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    goal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("goals.id"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    recurring: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    xp_awarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=True)
    time: Mapped[str] = mapped_column(String(10), nullable=True) # HH:MM format
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user = relationship("User", back_populates="tasks")
    goal = relationship("Goal", back_populates="tasks")
