from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.models.reminder import Reminder
from app.schemas.briefing import DailyBriefingDeltaOut, DailyBriefingOut, ReminderCompletionStatsOut, WeeklyBriefingOut
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


def build_weekly_briefing(db: Session, user_id: str) -> WeeklyBriefingOut:
    now_local = datetime.now().astimezone()
    week_start = (now_local - timedelta(days=now_local.weekday())).date()
    week_end = week_start + timedelta(days=6)

    reminders = list(db.scalars(select(Reminder).where(Reminder.user_id == user_id)))
    due_this_week_reminders: list[Reminder] = []
    due_this_week_count = 0
    completed_due_this_week_count = 0
    for reminder in reminders:
        due_date = _to_local_date(reminder.due_at, now_local)
        if not (week_start <= due_date <= week_end):
            continue
        if reminder.status == "CANCELLED":
            continue

        due_this_week_count += 1
        if reminder.status == "COMPLETED":
            completed_due_this_week_count += 1
        if reminder.status == "ACTIVE":
            due_this_week_reminders.append(reminder)

    due_this_week_reminders = sorted(due_this_week_reminders, key=lambda item: (item.due_at, item.id))
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
    completion_rate_this_week = (
        round((completed_due_this_week_count / due_this_week_count), 4) if due_this_week_count else 0.0
    )

    return WeeklyBriefingOut(
        date=now_local.date(),
        week_start=week_start,
        week_end=week_end,
        due_this_week_reminders=[ReminderOut.model_validate(reminder) for reminder in due_this_week_reminders],
        due_this_week_count=due_this_week_count,
        completed_due_this_week_count=completed_due_this_week_count,
        completion_rate_this_week=completion_rate_this_week,
        top_active_memories=[MemoryOut.model_validate(memory) for memory in top_memories],
        routine_suggestions=suggestions,
    )


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


def build_weekly_briefing_reply(db: Session, user_id: str) -> str:
    briefing = build_weekly_briefing(db=db, user_id=user_id)
    lines = [f"Weekly briefing for {briefing.week_start.isoformat()} to {briefing.week_end.isoformat()}"]

    if briefing.due_this_week_reminders:
        lines.append("Active reminders due this week:")
        for reminder in briefing.due_this_week_reminders:
            lines.append(f"- #{reminder.id} {reminder.title} at {reminder.due_at.isoformat()}")
    else:
        lines.append("Active reminders due this week: none")

    lines.append(
        "Completion this week: "
        f"{briefing.completed_due_this_week_count}/{briefing.due_this_week_count} ({briefing.completion_rate_this_week:.2%})"
    )

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


def _to_local_date(value: datetime, local_now: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(local_now.tzinfo).date()


def build_reminder_completion_stats(db: Session, user_id: str) -> ReminderCompletionStatsOut:
    now_local = datetime.now().astimezone()
    today_date = now_local.date()
    week_start = (now_local - timedelta(days=now_local.weekday())).date()
    week_end = week_start + timedelta(days=6)

    reminders = list(db.scalars(select(Reminder).where(Reminder.user_id == user_id)))
    due_today_count = 0
    completed_due_today_count = 0
    due_this_week_count = 0
    completed_due_this_week_count = 0

    for reminder in reminders:
        if reminder.status == "CANCELLED":
            continue
        due_date = _to_local_date(reminder.due_at, now_local)

        if due_date == today_date:
            due_today_count += 1
            if reminder.status == "COMPLETED":
                completed_due_today_count += 1

        if week_start <= due_date <= week_end:
            due_this_week_count += 1
            if reminder.status == "COMPLETED":
                completed_due_this_week_count += 1

    completion_rate_today = round((completed_due_today_count / due_today_count), 4) if due_today_count else 0.0
    completion_rate_this_week = (
        round((completed_due_this_week_count / due_this_week_count), 4) if due_this_week_count else 0.0
    )

    return ReminderCompletionStatsOut(
        date=today_date,
        week_start=week_start,
        week_end=week_end,
        due_today_count=due_today_count,
        completed_due_today_count=completed_due_today_count,
        completion_rate_today=completion_rate_today,
        due_this_week_count=due_this_week_count,
        completed_due_this_week_count=completed_due_this_week_count,
        completion_rate_this_week=completion_rate_this_week,
    )


def build_reminder_completion_stats_reply(db: Session, user_id: str) -> str:
    stats = build_reminder_completion_stats(db=db, user_id=user_id)
    return "\n".join(
        [
            f"Reminder completion stats for {stats.date.isoformat()}",
            f"- Due today: {stats.due_today_count}",
            f"- Completed due today: {stats.completed_due_today_count}",
            f"- Completion rate today: {stats.completion_rate_today:.2%}",
            f"- Due this week: {stats.due_this_week_count}",
            f"- Completed due this week: {stats.completed_due_this_week_count}",
            f"- Completion rate this week: {stats.completion_rate_this_week:.2%}",
        ]
    )
