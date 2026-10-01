from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.schemas.routine import RoutineCandidateOut
from app.services.routine_service import list_routine_candidates

router = APIRouter(prefix="/api/v1/routines", tags=["routines"])


@router.get("", response_model=list[RoutineCandidateOut])
def get_routines(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return list_routine_candidates(db, user_id=user_id)

