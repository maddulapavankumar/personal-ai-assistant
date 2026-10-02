from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate, ReminderUpdate


def list_reminders(db: Session, user_id: str) -> list[Reminder]:
    return list(db.scalars(select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.due_at.asc())))


def get_reminder(db: Session, user_id: str, reminder_id: int) -> Reminder | None:
    reminder = db.get(Reminder, reminder_id)
    if not reminder or reminder.user_id != user_id:
        return None
    return reminder


def create_reminder(db: Session, user_id: str, payload: ReminderCreate) -> Reminder:
    reminder = Reminder(user_id=user_id, **payload.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def update_reminder(db: Session, reminder: Reminder, payload: ReminderUpdate) -> Reminder:
    update_values = payload.model_dump(exclude_unset=True)
    target_status = update_values.get("status")
    if target_status is not None:
        validate_reminder_status_transition(current_status=reminder.status, new_status=target_status)
    for key, value in update_values.items():
        setattr(reminder, key, value)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def list_reminders_for_query(db: Session, user_id: str, query_scope: str) -> list[Reminder]:
    reminders = list_reminders(db=db, user_id=user_id)
    active_reminders = [reminder for reminder in reminders if reminder.status == "ACTIVE"]
    if query_scope == "all":
        return active_reminders

    now_local = datetime.now().astimezone()
    local_due_date_by_id = {reminder.id: _to_local_due_date(reminder_due_at=reminder.due_at, local_now=now_local) for reminder in active_reminders}
    if query_scope == "today":
        return [reminder for reminder in active_reminders if local_due_date_by_id[reminder.id] == now_local.date()]

    week_start_date = (now_local - timedelta(days=now_local.weekday())).date()
    week_end_date = week_start_date + timedelta(days=6)
    return [
        reminder
        for reminder in active_reminders
        if week_start_date <= local_due_date_by_id[reminder.id] <= week_end_date
    ]


def _to_local_due_date(reminder_due_at: datetime, local_now: datetime):
    if reminder_due_at.tzinfo is None:
        reminder_due_at = reminder_due_at.replace(tzinfo=timezone.utc)
    return reminder_due_at.astimezone(local_now.tzinfo).date()


def validate_reminder_status_transition(current_status: str, new_status: str) -> None:
    if current_status == new_status:
        return
    allowed_transitions = {
        "ACTIVE": {"COMPLETED", "CANCELLED"},
        "COMPLETED": set(),
        "CANCELLED": set(),
    }
    allowed = allowed_transitions.get(current_status)
    if allowed is None or new_status not in allowed:
        raise ValueError(f"Invalid reminder status transition: {current_status} -> {new_status}")
