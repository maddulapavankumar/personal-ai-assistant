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
    for key, value in update_values.items():
        setattr(reminder, key, value)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder
