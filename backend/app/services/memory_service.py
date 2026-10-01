from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.models.memory_review_event import MemoryReviewEvent
from app.schemas.memory import MemoryCreate, MemoryReviewRequest, MemoryUpdate
from app.services.memory_quality_service import (
    append_duplicate_suppression_event,
    build_decision_provenance,
    find_active_duplicate_memory,
    validate_status_transition,
)

REVIEW_THRESHOLD = 0.80


def list_memories(db: Session, user_id: str, status: str | None = None) -> list[Memory]:
    query = select(Memory).where(Memory.user_id == user_id)
    if status:
        query = query.where(Memory.status == status)
    return list(db.scalars(query.order_by(Memory.updated_at.desc())))


def get_memory(db: Session, user_id: str, memory_id: int) -> Memory | None:
    memory = db.get(Memory, memory_id)
    if not memory or memory.user_id != user_id:
        return None
    return memory


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
        if candidate.confidence < REVIEW_THRESHOLD:
            candidate_data["status"] = "PENDING_REVIEW"
            candidate_data["provenance_json"] = build_decision_provenance(
                base_provenance=candidate.provenance_json,
                decision="pending_review",
                decision_reason="confidence_below_threshold",
                reviewed_by="system",
            )
        else:
            candidate_data["status"] = "ACTIVE"
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
    target_status = update_values.get("status")
    status_changed = target_status is not None and target_status != memory.status

    if target_status is not None:
        validate_status_transition(current_status=memory.status, new_status=target_status)

    for key, value in update_values.items():
        setattr(memory, key, value)

    if provenance_json is not None:
        memory.provenance_json = provenance_json

    if status_changed or reviewed_by is not None or decision is not None or decision_reason is not None:
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


def list_review_queue(db: Session, user_id: str) -> list[Memory]:
    return list_review_queue_with_filters(db=db, user_id=user_id)


def list_review_queue_with_filters(
    db: Session,
    user_id: str,
    status: str | None = "PENDING_REVIEW",
    memory_type: str | None = None,
    sort_by: str = "updated_at",
    order: str = "desc",
) -> list[Memory]:
    sort_column_lookup = {
        "created_at": Memory.created_at,
        "updated_at": Memory.updated_at,
        "confidence": Memory.confidence,
        "importance": Memory.importance,
    }
    query = select(Memory).where(Memory.user_id == user_id)
    if status is not None:
        query = query.where(Memory.status == status)
    if memory_type is not None:
        query = query.where(Memory.type == memory_type)

    sort_column = sort_column_lookup[sort_by]
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    return list(db.scalars(query))


def review_memory(db: Session, memory: Memory, payload: MemoryReviewRequest, user_id: str) -> Memory:
    if memory.status != "PENDING_REVIEW":
        raise ValueError("Only PENDING_REVIEW memories can be reviewed")

    decision_to_status = {"approve": "ACTIVE", "reject": "REJECTED"}
    target_status = decision_to_status[payload.decision]
    validate_status_transition(current_status=memory.status, new_status=target_status)
    memory.status = target_status
    memory.provenance_json = build_decision_provenance(
        base_provenance=memory.provenance_json,
        decision=payload.decision,
        decision_reason=payload.reason,
        reviewed_by="user",
    )
    db.add(memory)

    provenance = memory.provenance_json or {}
    db.add(
        MemoryReviewEvent(
            memory_id=memory.id,
            user_id=user_id,
            conversation_id=provenance.get("conversation_id"),
            message_id=provenance.get("message_id"),
            decision=payload.decision,
            reason=payload.reason,
            payload_json={"provenance": provenance},
        )
    )
    db.commit()
    db.refresh(memory)
    return memory
