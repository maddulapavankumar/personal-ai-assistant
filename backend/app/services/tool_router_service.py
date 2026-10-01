from sqlalchemy.orm import Session

from app.services.memory_extraction_service import extract_memory_candidates
from app.services.memory_service import create_extracted_memories


def maybe_extract_memories(
    db: Session,
    user_id: str,
    message_text: str,
    conversation_id: int,
    message_id: int,
    extraction_mode: str | None,
) -> int:
    resolved_mode = extraction_mode or "auto"
    if resolved_mode == "off":
        return 0

    candidates = extract_memory_candidates(
        message_text=message_text,
        conversation_id=conversation_id,
        message_id=message_id,
    )
    return create_extracted_memories(db=db, user_id=user_id, candidates=candidates)
