from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat_turn

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return handle_chat_turn(db=db, user_id=user_id, payload=payload)
