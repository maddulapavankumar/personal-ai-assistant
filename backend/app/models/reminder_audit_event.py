from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_mixins import TimestampMixin


class ReminderAuditEvent(Base, TimestampMixin):
    __tablename__ = "reminder_audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    reminder_id: Mapped[int | None] = mapped_column(ForeignKey("reminders.id"), nullable=True, index=True)
    conversation_id: Mapped[int] = mapped_column(index=True)
    message_id: Mapped[int] = mapped_column(index=True)
    rule_id: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)

