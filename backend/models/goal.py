from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    pressure_status: Mapped[str] = mapped_column(String(20), default="on_track", nullable=False)
    goal_type: Mapped[str] = mapped_column(String(20), default="mid_term", nullable=False)
    xp_awarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reflection_went_well: Mapped[str] = mapped_column(Text, nullable=True)
    reflection_didnt_go_well: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="goals")
    tasks = relationship("Task", back_populates="goal")
