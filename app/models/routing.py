from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Routing(Base):
    __tablename__ = "routings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    attendance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("attendances.id", ondelete="CASCADE"), unique=True, index=True
    )
    department: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True, nullable=False)
    execution_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attendance: Mapped["Attendance"] = relationship(back_populates="routing")
