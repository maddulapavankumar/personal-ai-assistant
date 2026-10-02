import re

from app.schemas.chat import ChatAction

BRIEFING_DAILY_RULE_ID = "chat_daily_briefing_v1"
BRIEFING_DAILY_DELTA_RULE_ID = "chat_daily_briefing_delta_v1"
REMINDER_COMPLETION_STATS_RULE_ID = "chat_reminder_completion_stats_v1"
WEEKLY_BRIEFING_RULE_ID = "chat_weekly_briefing_v1"
NEXT_ACTIONS_RULE_ID = "chat_next_actions_v1"

BRIEFING_DAILY_PATTERN = re.compile(r"^\s*(brief me|show daily briefing)\s*$", re.IGNORECASE)
BRIEFING_DAILY_DELTA_PATTERN = re.compile(r"^\s*(what changed since yesterday|show daily delta)\s*$", re.IGNORECASE)
REMINDER_COMPLETION_STATS_PATTERN = re.compile(
    r"^\s*(show reminder completion stats|show reminder stats)\s*$", re.IGNORECASE
)
WEEKLY_BRIEFING_PATTERN = re.compile(r"^\s*(show weekly briefing|brief me this week)\s*$", re.IGNORECASE)
NEXT_ACTIONS_PATTERN = re.compile(r"^\s*(what should i do next|show next actions)\s*$", re.IGNORECASE)


def maybe_process_briefing_command(message_text: str) -> ChatAction | None:
    if NEXT_ACTIONS_PATTERN.match(message_text):
        return ChatAction(
            action="query_next_actions",
            status="executed",
            rule_id=NEXT_ACTIONS_RULE_ID,
        )
    if WEEKLY_BRIEFING_PATTERN.match(message_text):
        return ChatAction(
            action="query_weekly_briefing",
            status="executed",
            rule_id=WEEKLY_BRIEFING_RULE_ID,
        )
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
