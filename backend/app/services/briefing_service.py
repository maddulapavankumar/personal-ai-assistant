from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.schemas.briefing import DailyBriefingOut
from app.schemas.memory import MemoryOut
from app.schemas.reminder import ReminderOut
from app.services.reminder_service import list_reminders_for_query
from app.services.routine_service import build_routine_suggestions


def build_daily_briefing(db: Session, user_id: str) -> DailyBriefingOut:
    now_local = datetime.now().astimezone()
    due_reminders = list_reminders_for_query(db=db, user_id=user_id, query_scope="today")
    top_memories = list(
        db.scalars(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.status == "ACTIVE",
            )
            .order_by(
                Memory.importance.desc(),
                Memory.confidence.desc(),
                Memory.updated_at.desc(),
                Memory.id.asc(),
            )
            .limit(3)
        )
    )
    suggestions = build_routine_suggestions(db=db, user_id=user_id)

    return DailyBriefingOut(
        date=now_local.date(),
        due_reminders_today=[ReminderOut.model_validate(reminder) for reminder in due_reminders],
        top_active_memories=[MemoryOut.model_validate(memory) for memory in top_memories],
        routine_suggestions=suggestions,
    )
