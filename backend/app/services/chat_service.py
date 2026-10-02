import re

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse, MemoryContextItem
from app.services.briefing_command_service import (
    BRIEFING_DAILY_DELTA_RULE_ID,
    BRIEFING_DAILY_RULE_ID,
    REMINDER_COMPLETION_STATS_RULE_ID,
)
from app.services.briefing_service import (
    build_daily_briefing_delta_reply,
    build_daily_briefing_reply,
    build_reminder_completion_stats_reply,
)
from app.services.memory_service import list_memories
from app.services.reminder_command_service import (
    REMINDER_QUERY_ALL_RULE_ID,
    REMINDER_QUERY_DUE_TODAY_RULE_ID,
    REMINDER_QUERY_DUE_WEEK_RULE_ID,
)
from app.services.reminder_service import list_reminders_for_query
from app.services.tool_router_service import maybe_extract_memories, maybe_route_chat_actions

MAX_MEMORY_CONTEXT_ITEMS = 3
MIN_TOKEN_OVERLAP_FOR_MATCH = 2
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

    actions = maybe_route_chat_actions(
        db=db,
        user_id=user_id,
        message_text=payload.message,
        conversation_id=conversation.id,
        message_id=user_message.id,
    )

    reply = "MVP assistant is running. Next milestone will integrate tool-calling and memory extraction."
    if actions:
        action = actions[0]
        if action.status == "executed" and action.action == "create_reminder":
            reply = "Reminder created from your chat command."
        elif action.status == "executed" and action.action == "update_reminder":
            reply = "Reminder updated from your chat command."
        elif action.status == "executed" and action.action == "cancel_reminder":
            reply = "Reminder cancelled from your chat command."
        elif action.status == "ignored":
            reply = "Reminder not found for that command."
        elif action.status == "executed" and action.action == "query_reminders":
            reply = _build_reminder_query_reply(
                db=db,
                user_id=user_id,
                rule_id=action.rule_id,
            )
        elif action.status == "executed" and action.action == "query_daily_briefing":
            reply = build_daily_briefing_reply(db=db, user_id=user_id)
        elif action.status == "executed" and action.action == "query_daily_briefing_delta":
            reply = build_daily_briefing_delta_reply(db=db, user_id=user_id)
        elif action.status == "executed" and action.action == "query_reminder_completion_stats":
            reply = build_reminder_completion_stats_reply(db=db, user_id=user_id)
        elif action.status == "invalid" and action.action == "query_reminders":
            reply = "Invalid reminder query command. Use: show reminders; show reminders due today; show reminders due this week"
        elif action.status == "invalid" and action.rule_id in {
            BRIEFING_DAILY_RULE_ID,
            BRIEFING_DAILY_DELTA_RULE_ID,
            REMINDER_COMPLETION_STATS_RULE_ID,
        }:
            reply = (
                "Invalid briefing command. Use: brief me; show daily briefing; "
                "what changed since yesterday; show daily delta; show reminder completion stats; show reminder stats"
            )
        elif action.status == "invalid":
            reply = (
                "Invalid reminder command. Use: remind me to <title> at <ISO-8601 datetime>; "
                "update reminder <id> title <text> at <ISO-8601 datetime>; cancel reminder <id>"
            )

    assistant_message = Message(conversation_id=conversation.id, role="assistant", content=reply)
    db.add(assistant_message)

    memory_context = _build_memory_context(
        db=db,
        user_id=user_id,
        message_text=payload.message,
    )

    db.commit()
    db.refresh(conversation)
    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply,
        actions=actions,
        memory_context=memory_context or None,
    )


def _build_memory_context(db: Session, user_id: str, message_text: str) -> list[MemoryContextItem]:
    active_memories = list_memories(db=db, user_id=user_id, status="ACTIVE")
    message_tokens = _tokenize_for_matching(message_text)
    if not active_memories or not message_tokens:
        return []

    matched: list[MemoryContextItem] = []
    for memory in active_memories:
        memory_tokens = _tokenize_for_matching(memory.content)
        if len(message_tokens.intersection(memory_tokens)) >= MIN_TOKEN_OVERLAP_FOR_MATCH:
            matched.append(
                MemoryContextItem(
                    id=memory.id,
                    type=memory.type,
                    content=memory.content,
                    importance=memory.importance,
                )
            )
        if len(matched) >= MAX_MEMORY_CONTEXT_ITEMS:
            break
    return matched


def _tokenize_for_matching(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    return {token for token in tokens if len(token) >= 3 and token not in GENERIC_TOKENS}


def _build_reminder_query_reply(db: Session, user_id: str, rule_id: str) -> str:
    scope_by_rule = {
        REMINDER_QUERY_ALL_RULE_ID: "all",
        REMINDER_QUERY_DUE_TODAY_RULE_ID: "today",
        REMINDER_QUERY_DUE_WEEK_RULE_ID: "this_week",
    }
    scope = scope_by_rule.get(rule_id)
    if scope is None:
        return "Invalid reminder query command. Use: show reminders; show reminders due today; show reminders due this week"

    reminders = list_reminders_for_query(db=db, user_id=user_id, query_scope=scope)
    if not reminders:
        if scope == "all":
            return "No active reminders found."
        if scope == "today":
            return "No active reminders due today."
        return "No active reminders due this week."

    title = "Active reminders:"
    if scope == "today":
        title = "Active reminders due today:"
    elif scope == "this_week":
        title = "Active reminders due this week:"

    lines = [title]
    for reminder in reminders:
        lines.append(f"- #{reminder.id} {reminder.title} at {reminder.due_at.isoformat()}")
    return "\n".join(lines)
