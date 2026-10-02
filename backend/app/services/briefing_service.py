from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.models.reminder import Reminder
from app.schemas.briefing import DailyBriefingDeltaOut, DailyBriefingOut
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


def build_daily_briefing_delta(db: Session, user_id: str) -> DailyBriefingDeltaOut:
    now_local = datetime.now().astimezone()
    today_date = now_local.date()
    yesterday_date = today_date - timedelta(days=1)
    active_reminders = list(
        db.scalars(
            select(Reminder).where(
                Reminder.user_id == user_id,
                Reminder.status == "ACTIVE",
            )
        )
    )

    due_today_count = 0
    due_yesterday_count = 0
    new_reminders_created_count = 0
    for reminder in active_reminders:
        due_date = _to_local_date(reminder.due_at, now_local)
        if due_date == today_date:
            due_today_count += 1
        if due_date == yesterday_date:
            due_yesterday_count += 1

        created_date = _to_local_date(reminder.created_at, now_local)
        if created_date == today_date:
            new_reminders_created_count += 1

    active_memories = list(
        db.scalars(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.status == "ACTIVE",
            )
        )
    )
    new_active_memories_count = sum(1 for memory in active_memories if _to_local_date(memory.created_at, now_local) == today_date)

    return DailyBriefingDeltaOut(
        date=today_date,
        yesterday=yesterday_date,
        due_today_count=due_today_count,
        due_yesterday_count=due_yesterday_count,
        due_count_delta=due_today_count - due_yesterday_count,
        new_active_memories_count=new_active_memories_count,
        new_reminders_created_count=new_reminders_created_count,
    )


def build_daily_briefing_reply(db: Session, user_id: str) -> str:
    briefing = build_daily_briefing(db=db, user_id=user_id)
    lines = [f"Daily briefing for {briefing.date.isoformat()}"]

    if briefing.due_reminders_today:
        lines.append("Reminders due today:")
        for reminder in briefing.due_reminders_today:
            lines.append(f"- #{reminder.id} {reminder.title} at {reminder.due_at.isoformat()}")
    else:
        lines.append("Reminders due today: none")

    if briefing.top_active_memories:
        lines.append("Top active memories:")
        for memory in briefing.top_active_memories:
            lines.append(f"- #{memory.id} [{memory.type}] {memory.content}")
    else:
        lines.append("Top active memories: none")

    if briefing.routine_suggestions:
        lines.append("Routine suggestions:")
        for suggestion in briefing.routine_suggestions:
            lines.append(f"- {suggestion.title} (confidence {suggestion.confidence:.2f})")
    else:
        lines.append("Routine suggestions: none")

    return "\n".join(lines)


def build_daily_briefing_delta_reply(db: Session, user_id: str) -> str:
    delta = build_daily_briefing_delta(db=db, user_id=user_id)
    sign = "+" if delta.due_count_delta >= 0 else ""
    return "\n".join(
        [
            f"Daily delta for {delta.date.isoformat()} (vs {delta.yesterday.isoformat()})",
            f"- Due reminders today: {delta.due_today_count}",
            f"- Due reminders yesterday: {delta.due_yesterday_count}",
            f"- Due reminder delta: {sign}{delta.due_count_delta}",
            f"- New reminders created today: {delta.new_reminders_created_count}",
            f"- New active memories added today: {delta.new_active_memories_count}",
        ]
    )


def _to_local_date(value: datetime, local_now: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(local_now.tzinfo).date()

