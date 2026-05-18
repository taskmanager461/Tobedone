from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class DailyScore(Base):
    __tablename__ = "daily_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user = relationship("User", back_populates="daily_scores")
