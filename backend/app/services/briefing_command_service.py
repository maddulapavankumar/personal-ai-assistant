import re

from app.schemas.chat import ChatAction

BRIEFING_DAILY_RULE_ID = "chat_daily_briefing_v1"
BRIEFING_DAILY_DELTA_RULE_ID = "chat_daily_briefing_delta_v1"
REMINDER_COMPLETION_STATS_RULE_ID = "chat_reminder_completion_stats_v1"

BRIEFING_DAILY_PATTERN = re.compile(r"^\s*(brief me|show daily briefing)\s*$", re.IGNORECASE)
BRIEFING_DAILY_DELTA_PATTERN = re.compile(r"^\s*(what changed since yesterday|show daily delta)\s*$", re.IGNORECASE)
REMINDER_COMPLETION_STATS_PATTERN = re.compile(
    r"^\s*(show reminder completion stats|show reminder stats)\s*$", re.IGNORECASE
)


def maybe_process_briefing_command(message_text: str) -> ChatAction | None:
    if REMINDER_COMPLETION_STATS_PATTERN.match(message_text):
        return ChatAction(
            action="query_reminder_completion_stats",
            status="executed",
            rule_id=REMINDER_COMPLETION_STATS_RULE_ID,
        )
    if BRIEFING_DAILY_DELTA_PATTERN.match(message_text):
        return ChatAction(action="query_daily_briefing_delta", status="executed", rule_id=BRIEFING_DAILY_DELTA_RULE_ID)
    if BRIEFING_DAILY_PATTERN.match(message_text):
        return ChatAction(action="query_daily_briefing", status="executed", rule_id=BRIEFING_DAILY_RULE_ID)
    return None
