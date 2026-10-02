from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.schemas.briefing import DailyBriefingOut
from app.services.briefing_service import build_daily_briefing

router = APIRouter(prefix="/api/v1/briefings", tags=["briefings"])


@router.get("/daily", response_model=DailyBriefingOut)
def get_daily_briefing(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return build_daily_briefing(db=db, user_id=user_id)
