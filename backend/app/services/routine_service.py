from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.routine import RoutineCandidate


def list_routine_candidates(db: Session, user_id: str) -> list[RoutineCandidate]:
    return list(
        db.scalars(
            select(RoutineCandidate)
            .where(RoutineCandidate.user_id == user_id)
            .order_by(RoutineCandidate.updated_at.desc())
        )
    )

