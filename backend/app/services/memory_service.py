from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryUpdate
from app.services.memory_quality_service import (
    append_duplicate_suppression_event,
    build_decision_provenance,
    find_active_duplicate_memory,
)


def list_memories(db: Session, user_id: str, status: str | None = None) -> list[Memory]:
    query = select(Memory).where(Memory.user_id == user_id)
    if status:
        query = query.where(Memory.status == status)
    return list(db.scalars(query.order_by(Memory.updated_at.desc())))


def create_memory(db: Session, user_id: str, payload: MemoryCreate) -> Memory:
    memory = Memory(user_id=user_id, **payload.model_dump())
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def create_extracted_memories(db: Session, user_id: str, candidates: list[MemoryCreate]) -> int:
    accepted_count = 0
    for candidate in candidates:
        duplicate = find_active_duplicate_memory(
            db=db,
            user_id=user_id,
            memory_type=candidate.type,
            content=candidate.content,
        )
        if duplicate:
            append_duplicate_suppression_event(duplicate, suppressed_candidate_provenance=candidate.provenance_json)
            db.add(duplicate)
            continue

        candidate_data = candidate.model_dump()
        candidate_data["provenance_json"] = build_decision_provenance(
            base_provenance=candidate.provenance_json,
            decision="accepted",
            decision_reason="new_extraction",
            reviewed_by="system",
        )
        db.add(Memory(user_id=user_id, **candidate_data))
        accepted_count += 1
    return accepted_count


def update_memory(db: Session, memory: Memory, payload: MemoryUpdate) -> Memory:
    update_values = payload.model_dump(exclude_unset=True)
    reviewed_by = update_values.pop("reviewed_by", None)
    decision = update_values.pop("decision", None)
    decision_reason = update_values.pop("decision_reason", None)
    provenance_json = update_values.pop("provenance_json", None)

    for key, value in update_values.items():
        setattr(memory, key, value)

    if provenance_json is not None:
        memory.provenance_json = provenance_json

    if "status" in update_values or reviewed_by is not None or decision is not None or decision_reason is not None:
        memory.provenance_json = build_decision_provenance(
            base_provenance=memory.provenance_json,
            decision=decision or "manual_override",
            decision_reason=decision_reason or "manual_status_or_metadata_update",
            reviewed_by=reviewed_by or "user",
        )

    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory
