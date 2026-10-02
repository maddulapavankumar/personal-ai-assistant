from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.schemas.routine import RoutineCandidateOut, RoutineSuggestionOut
from app.services.routine_service import build_routine_suggestions, list_routine_candidates

router = APIRouter(prefix="/api/v1/routines", tags=["routines"])


@router.get("", response_model=list[RoutineCandidateOut])
def get_routines(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return list_routine_candidates(db, user_id=user_id)


@router.get("/suggestions", response_model=list[RoutineSuggestionOut])
def get_routine_suggestions(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return build_routine_suggestions(db=db, user_id=user_id)
