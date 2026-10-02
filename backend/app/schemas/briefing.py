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


class DailyBriefingDeltaOut(BaseModel):
    date: date
    yesterday: date
    due_today_count: int
    due_yesterday_count: int
    due_count_delta: int
    new_active_memories_count: int
    new_reminders_created_count: int
