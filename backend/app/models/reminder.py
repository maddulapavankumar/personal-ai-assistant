from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_mixins import TimestampMixin


class Reminder(Base, TimestampMixin):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, default="default-user")
    title: Mapped[str] = mapped_column(String(255), index=True)
    notes: Mapped[str] = mapped_column(Text(), default="")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    recurrence_rule: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)

