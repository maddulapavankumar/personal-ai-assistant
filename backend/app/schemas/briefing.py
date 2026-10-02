from datetime import date

from pydantic import BaseModel

from app.schemas.memory import MemoryOut
from app.schemas.reminder import ReminderOut
from app.schemas.routine import RoutineSuggestionOut


class DailyBriefingOut(BaseModel):
    date: date
    due_reminders_today: list[ReminderOut]
    top_active_memories: list[MemoryOut]
    routine_suggestions: list[RoutineSuggestionOut]
