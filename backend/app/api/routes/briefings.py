from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.schemas.briefing import DailyBriefingDeltaOut, DailyBriefingOut, ReminderCompletionStatsOut
from app.services.briefing_service import (
    build_daily_briefing,
    build_daily_briefing_delta,
    build_reminder_completion_stats,
)

router = APIRouter(prefix="/api/v1/briefings", tags=["briefings"])


@router.get("/daily", response_model=DailyBriefingOut)
def get_daily_briefing(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return build_daily_briefing(db=db, user_id=user_id)


@router.get("/daily-delta", response_model=DailyBriefingDeltaOut)
def get_daily_briefing_delta(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return build_daily_briefing_delta(db=db, user_id=user_id)


@router.get("/reminder-completion-stats", response_model=ReminderCompletionStatsOut)
def get_reminder_completion_stats(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return build_reminder_completion_stats(db=db, user_id=user_id)
