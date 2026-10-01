from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    conversation = None
    if payload.conversation_id:
        conversation = db.get(Conversation, payload.conversation_id)
        if conversation and conversation.user_id != user_id:
            conversation = None
    if not conversation:
        conversation = Conversation(user_id=user_id, title="MVP conversation")
        db.add(conversation)
        db.flush()

    user_message = Message(conversation_id=conversation.id, role="user", content=payload.message)
    db.add(user_message)

    reply = "MVP assistant is running. Next milestone will integrate tool-calling and memory extraction."
    assistant_message = Message(conversation_id=conversation.id, role="assistant", content=reply)
    db.add(assistant_message)

    db.commit()
    db.refresh(conversation)
    return ChatResponse(conversation_id=conversation.id, reply=reply)

