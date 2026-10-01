from sqlalchemy import ForeignKey, JSON, String, event
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_mixins import TimestampMixin


class MemoryReviewEvent(Base, TimestampMixin):
    __tablename__ = "memory_review_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    memory_id: Mapped[int] = mapped_column(ForeignKey("memories.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    conversation_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    message_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    decision: Mapped[str] = mapped_column(String(32), index=True)
    reason: Mapped[str] = mapped_column(String(255))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)


@event.listens_for(MemoryReviewEvent, "before_update")
def prevent_memory_review_event_update(*_args):
    raise ValueError("memory_review_events is append-only and cannot be updated")


@event.listens_for(MemoryReviewEvent, "before_delete")
def prevent_memory_review_event_delete(*_args):
    raise ValueError("memory_review_events is append-only and cannot be deleted")
