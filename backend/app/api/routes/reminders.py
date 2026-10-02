from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate, ReminderOut, ReminderUpdate
from app.services.reminder_service import create_reminder, list_reminders, update_reminder

router = APIRouter(prefix="/api/v1/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderOut])
def get_reminders(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return list_reminders(db, user_id=user_id)


@router.post("", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
def post_reminder(payload: ReminderCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return create_reminder(db, user_id=user_id, payload=payload)


@router.patch("/{reminder_id}", response_model=ReminderOut)
def patch_reminder(
    reminder_id: int, payload: ReminderUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)
):
    reminder = db.get(Reminder, reminder_id)
    if not reminder or reminder.user_id != user_id:
        raise HTTPException(status_code=404, detail="Reminder not found")
    try:
        return update_reminder(db, reminder, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    reminder = db.get(Reminder, reminder_id)
    if not reminder or reminder.user_id != user_id:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(reminder)
    db.commit()
    return None
