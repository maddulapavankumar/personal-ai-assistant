import re

from app.schemas.memory import MemoryCreate

EXTRACTOR_VERSION = "memory-rule-extractor-v1"
EXTRACTION_SOURCE = "CHAT_RULE_EXTRACTOR_V1"


def extract_memory_candidates(message_text: str, conversation_id: int, message_id: int) -> list[MemoryCreate]:
    content = message_text.strip()
    if not content:
        return []

    lower_content = content.lower()
    candidates: list[MemoryCreate] = []

    if re.search(r"\bi prefer\b", lower_content):
        candidates.append(
            _build_candidate(
                memory_type="PREFERENCE",
                content=content,
                confidence=0.85,
                importance=0.7,
                conversation_id=conversation_id,
                message_id=message_id,
                rule_id="pref_prefer_statement",
            )
        )

    if re.search(r"\bi (do not|don't) like\b", lower_content):
        candidates.append(
            _build_candidate(
                memory_type="PREFERENCE",
                content=content,
                confidence=0.8,
                importance=0.7,
                conversation_id=conversation_id,
                message_id=message_id,
                rule_id="pref_dislike_statement",
            )
        )

    if re.search(r"\bi own\b|\bi have (a|an|the|my)\b", lower_content):
        candidates.append(
            _build_candidate(
                memory_type="FACT",
                content=content,
                confidence=0.75,
                importance=0.6,
                conversation_id=conversation_id,
                message_id=message_id,
                rule_id="fact_ownership_statement",
            )
        )

    return candidates


def _build_candidate(
    memory_type: str,
    content: str,
    confidence: float,
    importance: float,
    conversation_id: int,
    message_id: int,
    rule_id: str,
) -> MemoryCreate:
    return MemoryCreate(
        type=memory_type,
        content=content,
        confidence=confidence,
        importance=importance,
        source=EXTRACTION_SOURCE,
        provenance_json={
            "conversation_id": conversation_id,
            "message_id": message_id,
            "rule_id": rule_id,
            "extractor_version": EXTRACTOR_VERSION,
        },
    )
