from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Attendance(Base):
    __tablename__ = "attendances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    customer_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="web", nullable=False)
    original_message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="received", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    classification: Mapped["Classification | None"] = relationship(
        back_populates="attendance", cascade="all, delete-orphan", uselist=False
    )
    routing: Mapped["Routing | None"] = relationship(
        back_populates="attendance", cascade="all, delete-orphan", uselist=False
    )
