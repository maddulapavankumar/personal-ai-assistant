import re

from app.schemas.chat import ChatAction

BRIEFING_DAILY_RULE_ID = "chat_daily_briefing_v1"
BRIEFING_DAILY_DELTA_RULE_ID = "chat_daily_briefing_delta_v1"

BRIEFING_DAILY_PATTERN = re.compile(r"^\s*(brief me|show daily briefing)\s*$", re.IGNORECASE)
BRIEFING_DAILY_DELTA_PATTERN = re.compile(r"^\s*(what changed since yesterday|show daily delta)\s*$", re.IGNORECASE)


def maybe_process_briefing_command(message_text: str) -> ChatAction | None:
    if BRIEFING_DAILY_DELTA_PATTERN.match(message_text):
        return ChatAction(action="query_daily_briefing_delta", status="executed", rule_id=BRIEFING_DAILY_DELTA_RULE_ID)
    if BRIEFING_DAILY_PATTERN.match(message_text):
        return ChatAction(action="query_daily_briefing", status="executed", rule_id=BRIEFING_DAILY_RULE_ID)
    return None
