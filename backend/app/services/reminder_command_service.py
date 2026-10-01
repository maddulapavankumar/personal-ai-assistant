import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.reminder_audit_event import ReminderAuditEvent
from app.schemas.chat import ChatAction
from app.schemas.reminder import ReminderCreate
from app.services.reminder_service import create_reminder

REMINDER_RULE_ID = "chat_remind_me_iso_v1"
REMINDER_PATTERN = re.compile(r"^\s*remind me to (?P<title>.+?) at (?P<due_at>\S+)\s*$", re.IGNORECASE)


def maybe_process_reminder_command(
    db: Session,
    user_id: str,
    message_text: str,
    conversation_id: int,
    message_id: int,
) -> ChatAction | None:
    if not message_text.strip().lower().startswith("remind me to "):
        return None

    match = REMINDER_PATTERN.match(message_text)
    if not match:
        _create_audit_event(
            db=db,
            user_id=user_id,
            reminder_id=None,
            conversation_id=conversation_id,
            message_id=message_id,
            payload_json={
                "status": "invalid",
                "reason": "invalid_command_format",
                "message": message_text,
            },
        )
        return ChatAction(
            action="create_reminder",
            status="invalid",
            rule_id=REMINDER_RULE_ID,
            reminder_id=None,
        )

    title = match.group("title").strip()
    due_at_raw = match.group("due_at").strip()
    due_at = _parse_iso_datetime(due_at_raw)

    if not title or due_at is None:
        _create_audit_event(
            db=db,
            user_id=user_id,
            reminder_id=None,
            conversation_id=conversation_id,
            message_id=message_id,
            payload_json={
                "status": "invalid",
                "reason": "invalid_command_format",
                "message": message_text,
            },
        )
        return ChatAction(
            action="create_reminder",
            status="invalid",
            rule_id=REMINDER_RULE_ID,
            reminder_id=None,
        )

    reminder = create_reminder(
        db=db,
        user_id=user_id,
        payload=ReminderCreate(title=title, due_at=due_at),
    )
    _create_audit_event(
        db=db,
        user_id=user_id,
        reminder_id=reminder.id,
        conversation_id=conversation_id,
        message_id=message_id,
        payload_json={
            "status": "executed",
            "title": title,
            "due_at": due_at.isoformat(),
        },
    )
    return ChatAction(
        action="create_reminder",
        status="executed",
        rule_id=REMINDER_RULE_ID,
        reminder_id=reminder.id,
    )


def _parse_iso_datetime(value: str) -> datetime | None:
    if "T" not in value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _create_audit_event(
    db: Session,
    user_id: str,
    reminder_id: int | None,
    conversation_id: int,
    message_id: int,
    payload_json: dict,
) -> None:
    db.add(
        ReminderAuditEvent(
            user_id=user_id,
            reminder_id=reminder_id,
            conversation_id=conversation_id,
            message_id=message_id,
            rule_id=REMINDER_RULE_ID,
            payload_json=payload_json,
        )
    )
