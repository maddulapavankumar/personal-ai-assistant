from sqlalchemy import Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_mixins import TimestampMixin


class Memory(Base, TimestampMixin):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, default="default-user")
    type: Mapped[str] = mapped_column(String(64), index=True)
    content: Mapped[str] = mapped_column(Text())
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    source: Mapped[str] = mapped_column(String(64), default="EXTRACTED")
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)

