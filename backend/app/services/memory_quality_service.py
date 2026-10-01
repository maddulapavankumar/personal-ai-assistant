import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory


def normalize_memory_content(content: str) -> str:
    return re.sub(r"\s+", " ", content.strip().lower())


def find_active_duplicate_memory(
    db: Session,
    user_id: str,
    memory_type: str,
    content: str,
) -> Memory | None:
    normalized_candidate = normalize_memory_content(content)
    candidate_memories = db.scalars(
        select(Memory).where(
            Memory.user_id == user_id,
            Memory.type == memory_type,
            Memory.status.in_(["ACTIVE", "PENDING_REVIEW"]),
        )
    )
    for memory in candidate_memories:
        if normalize_memory_content(memory.content) == normalized_candidate:
            return memory
    return None


def build_decision_provenance(
    base_provenance: dict | None,
    decision: str,
    decision_reason: str,
    reviewed_by: str = "system",
    duplicate_of_memory_id: int | None = None,
) -> dict:
    updated = dict(base_provenance or {})
    updated["decision"] = decision
    updated["decision_reason"] = decision_reason
    updated["reviewed_by"] = reviewed_by
    updated["decision_at"] = datetime.now(timezone.utc).isoformat()
    if duplicate_of_memory_id is not None:
        updated["duplicate_of_memory_id"] = duplicate_of_memory_id
    return updated


def append_duplicate_suppression_event(
    memory: Memory,
    suppressed_candidate_provenance: dict | None,
) -> None:
    provenance = dict(memory.provenance_json or {})
    events = list(provenance.get("duplicate_suppressed_events", []))
    events.append(
        {
            "suppressed_at": datetime.now(timezone.utc).isoformat(),
            "candidate_provenance": suppressed_candidate_provenance or {},
        }
    )
    provenance["duplicate_suppressed_events"] = events
    provenance["duplicate_suppressed_count"] = len(events)
    memory.provenance_json = provenance
