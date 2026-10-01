from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_mixins import TimestampMixin


class RoutineCandidate(Base, TimestampMixin):
    __tablename__ = "routine_candidates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, default="default-user")
    description: Mapped[str] = mapped_column(Text())
    confidence: Mapped[float] = mapped_column(Float, default=0.3)
    status: Mapped[str] = mapped_column(String(32), default="CANDIDATE", index=True)
    observation_count: Mapped[int] = mapped_column(default=1)

