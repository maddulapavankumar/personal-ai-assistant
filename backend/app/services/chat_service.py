from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.tool_router_service import maybe_extract_memories


def handle_chat_turn(db: Session, user_id: str, payload: ChatRequest) -> ChatResponse:
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
    db.flush()

    maybe_extract_memories(
        db=db,
        user_id=user_id,
        message_text=payload.message,
        conversation_id=conversation.id,
        message_id=user_message.id,
        extraction_mode=payload.extraction_mode,
    )

    reply = "MVP assistant is running. Next milestone will integrate tool-calling and memory extraction."
    assistant_message = Message(conversation_id=conversation.id, role="assistant", content=reply)
    db.add(assistant_message)

    db.commit()
    db.refresh(conversation)
    return ChatResponse(conversation_id=conversation.id, reply=reply)

