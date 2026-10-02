import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.models.reminder import Reminder
from app.models.routine import RoutineCandidate
from app.schemas.routine import NextActionOut, RoutineSuggestionOut

GENERIC_TOKENS = {
    "about",
    "assistant",
    "can",
    "could",
    "for",
    "from",
    "have",
    "help",
    "into",
    "just",
    "like",
    "need",
    "plan",
    "please",
    "reminder",
    "reminders",
    "that",
    "the",
    "this",
    "with",
    "would",
    "your",
}


def list_routine_candidates(db: Session, user_id: str) -> list[RoutineCandidate]:
    return list(
        db.scalars(
            select(RoutineCandidate)
            .where(RoutineCandidate.user_id == user_id)
            .order_by(RoutineCandidate.updated_at.desc())
        )
    )


def build_routine_suggestions(db: Session, user_id: str) -> list[RoutineSuggestionOut]:
    active_reminders = list(
        db.scalars(
            select(Reminder)
            .where(
                Reminder.user_id == user_id,
                Reminder.status == "ACTIVE",
            )
            .order_by(Reminder.due_at.asc(), Reminder.id.asc())
        )
    )
    active_memories = list(
        db.scalars(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.status == "ACTIVE",
            )
            .order_by(Memory.updated_at.desc(), Memory.id.asc())
        )
    )

    suggestions: list[RoutineSuggestionOut] = []
    if active_reminders:
        first_due = active_reminders[0]
        suggestions.append(
            RoutineSuggestionOut(
                title="Daily reminder check-in",
                description=(
                    f"Start with your next reminder ({first_due.title}) at {first_due.due_at.isoformat()} "
                    f"and review {len(active_reminders)} active reminder(s)."
                ),
                confidence=0.75,
                source_memory_ids=[],
                source_reminder_ids=[reminder.id for reminder in active_reminders[:3]],
            )
        )

    if active_memories:
        suggestions.append(
            RoutineSuggestionOut(
                title="Memory-informed planning review",
                description=f"Review your {len(active_memories)} active memory item(s) before planning the day.",
                confidence=0.65,
                source_memory_ids=[memory.id for memory in active_memories[:3]],
                source_reminder_ids=[],
            )
        )

    overlap_memory_ids, overlap_reminder_ids = _find_memory_reminder_overlap(active_memories, active_reminders)
    if overlap_memory_ids and overlap_reminder_ids:
        suggestions.append(
            RoutineSuggestionOut(
                title="Align reminders with known preferences",
                description="Combine memory cues with active reminders to tighten routine consistency.",
                confidence=0.7,
                source_memory_ids=overlap_memory_ids[:3],
                source_reminder_ids=overlap_reminder_ids[:3],
            )
        )

    return sorted(suggestions, key=lambda item: (-item.confidence, item.title))


def build_next_actions(db: Session, user_id: str) -> list[NextActionOut]:
    actions: list[NextActionOut] = []
    active_reminders = list(
        db.scalars(
            select(Reminder)
            .where(
                Reminder.user_id == user_id,
                Reminder.status == "ACTIVE",
            )
            .order_by(Reminder.due_at.asc(), Reminder.id.asc())
        )
    )
    pending_review_memories = list(
        db.scalars(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.status == "PENDING_REVIEW",
            )
            .order_by(Memory.updated_at.desc(), Memory.id.asc())
        )
    )
    active_memories = list(
        db.scalars(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.status == "ACTIVE",
            )
            .order_by(Memory.updated_at.desc(), Memory.id.asc())
        )
    )

    if active_reminders:
        next_reminder = active_reminders[0]
        actions.append(
            NextActionOut(
                priority=1,
                title="Complete next due reminder",
                description=f"Complete reminder #{next_reminder.id} ({next_reminder.title}) due at {next_reminder.due_at.isoformat()}.",
                source_reminder_id=next_reminder.id,
                source_memory_id=None,
            )
        )

    if pending_review_memories:
        actions.append(
            NextActionOut(
                priority=2,
                title="Review pending memories",
                description=f"Review {len(pending_review_memories)} memory item(s) in the review queue.",
                source_reminder_id=None,
                source_memory_id=pending_review_memories[0].id,
            )
        )

    if active_memories:
        actions.append(
            NextActionOut(
                priority=3,
                title="Run memory-informed planning review",
                description="Use your active memories to shape today's reminder priorities.",
                source_reminder_id=None,
                source_memory_id=active_memories[0].id,
            )
        )

    if not actions:
        actions.append(
            NextActionOut(
                priority=1,
                title="Create your first reminder",
                description="Add one reminder to start generating actionable assistant routines.",
                source_reminder_id=None,
                source_memory_id=None,
            )
        )

    return sorted(actions, key=lambda item: (item.priority, item.title))[:3]


def build_next_actions_reply(db: Session, user_id: str) -> str:
    next_actions = build_next_actions(db=db, user_id=user_id)
    lines = ["Next best actions:"]
    for action in next_actions:
        lines.append(f"- ({action.priority}) {action.title}: {action.description}")
    return "\n".join(lines)


def _find_memory_reminder_overlap(memories: list[Memory], reminders: list[Reminder]) -> tuple[list[int], list[int]]:
    overlap_memory_ids: list[int] = []
    overlap_reminder_ids: list[int] = []
    for memory in memories:
        memory_tokens = _tokenize(memory.content)
        if not memory_tokens:
            continue
        for reminder in reminders:
            reminder_tokens = _tokenize(reminder.title)
            if len(memory_tokens.intersection(reminder_tokens)) >= 2:
                if memory.id not in overlap_memory_ids:
                    overlap_memory_ids.append(memory.id)
                if reminder.id not in overlap_reminder_ids:
                    overlap_reminder_ids.append(reminder.id)
    return overlap_memory_ids, overlap_reminder_ids


def _tokenize(value: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", value.lower()))
    return {token for token in tokens if len(token) >= 3 and token not in GENERIC_TOKENS}
