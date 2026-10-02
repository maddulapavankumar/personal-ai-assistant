import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.reminder_audit_event import ReminderAuditEvent
from app.schemas.chat import ChatAction
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from app.services.reminder_service import create_reminder, get_reminder, update_reminder

REMINDER_CREATE_RULE_ID = "chat_remind_me_iso_v1"
REMINDER_UPDATE_RULE_ID = "chat_update_reminder_id_iso_v1"
REMINDER_CANCEL_RULE_ID = "chat_cancel_reminder_id_v1"
REMINDER_QUERY_ALL_RULE_ID = "chat_show_reminders_v1"
REMINDER_QUERY_DUE_TODAY_RULE_ID = "chat_show_reminders_due_today_v1"
REMINDER_QUERY_DUE_WEEK_RULE_ID = "chat_show_reminders_due_this_week_v1"
REMINDER_CREATE_PREFIX_PATTERN = re.compile(r"^\s*remind me to (?P<body>.+)\s*$", re.IGNORECASE)
REMINDER_UPDATE_PREFIX_PATTERN = re.compile(r"^\s*update reminder (?P<reminder_id>\d+) title (?P<body>.+)\s*$", re.IGNORECASE)
REMINDER_CANCEL_PATTERN = re.compile(r"^\s*cancel reminder (?P<reminder_id>\d+)\s*$", re.IGNORECASE)
REMINDER_QUERY_ALL_PATTERN = re.compile(r"^\s*show reminders\s*$", re.IGNORECASE)
REMINDER_QUERY_DUE_TODAY_PATTERN = re.compile(r"^\s*show reminders due today\s*$", re.IGNORECASE)
REMINDER_QUERY_DUE_WEEK_PATTERN = re.compile(r"^\s*show reminders due this week\s*$", re.IGNORECASE)


def maybe_process_reminder_command(
    db: Session,
    user_id: str,
    message_text: str,
    conversation_id: int,
    message_id: int,
) -> ChatAction | None:
    normalized = message_text.strip()
    lowered = normalized.lower()
    if not (
        lowered.startswith("remind me to ")
        or lowered.startswith("update reminder ")
        or lowered.startswith("cancel reminder ")
        or lowered.startswith("show reminders")
    ):
        return None

    if lowered.startswith("remind me to "):
        return _process_create_reminder_command(
            db=db,
            user_id=user_id,
            message_text=message_text,
            conversation_id=conversation_id,
            message_id=message_id,
        )
    if lowered.startswith("update reminder "):
        return _process_update_reminder_command(
            db=db,
            user_id=user_id,
            message_text=message_text,
            conversation_id=conversation_id,
            message_id=message_id,
        )
    if lowered.startswith("show reminders"):
        return _process_query_reminder_command(message_text=message_text)
    return _process_cancel_reminder_command(
        db=db,
        user_id=user_id,
        message_text=message_text,
        conversation_id=conversation_id,
        message_id=message_id,
    )


def _process_query_reminder_command(message_text: str) -> ChatAction:
    if REMINDER_QUERY_DUE_TODAY_PATTERN.match(message_text):
        return ChatAction(
            action="query_reminders",
            status="executed",
            rule_id=REMINDER_QUERY_DUE_TODAY_RULE_ID,
            reminder_id=None,
        )
    if REMINDER_QUERY_DUE_WEEK_PATTERN.match(message_text):
        return ChatAction(
            action="query_reminders",
            status="executed",
            rule_id=REMINDER_QUERY_DUE_WEEK_RULE_ID,
            reminder_id=None,
        )
    if REMINDER_QUERY_ALL_PATTERN.match(message_text):
        return ChatAction(
            action="query_reminders",
            status="executed",
            rule_id=REMINDER_QUERY_ALL_RULE_ID,
            reminder_id=None,
        )
    return ChatAction(
        action="query_reminders",
        status="invalid",
        rule_id=REMINDER_QUERY_ALL_RULE_ID,
        reminder_id=None,
    )


def _process_create_reminder_command(
    db: Session,
    user_id: str,
    message_text: str,
    conversation_id: int,
    message_id: int,
) -> ChatAction:
    match = REMINDER_CREATE_PREFIX_PATTERN.match(message_text)
    if not match:
        return _invalid_action_with_audit(
            db=db,
            user_id=user_id,
            action="create_reminder",
            rule_id=REMINDER_CREATE_RULE_ID,
            reminder_id=None,
            conversation_id=conversation_id,
            message_id=message_id,
            message_text=message_text,
        )

    split_result = _split_title_and_due_at(match.group("body"))
    if split_result is None:
        return _invalid_action_with_audit(
            db=db,
            user_id=user_id,
            action="create_reminder",
            rule_id=REMINDER_CREATE_RULE_ID,
            reminder_id=None,
            conversation_id=conversation_id,
            message_id=message_id,
            message_text=message_text,
        )
    title, due_at_raw = split_result
    due_at = _parse_iso_datetime(due_at_raw)
    if not title or due_at is None:
        return _invalid_action_with_audit(
            db=db,
            user_id=user_id,
            action="create_reminder",
            rule_id=REMINDER_CREATE_RULE_ID,
            reminder_id=None,
            conversation_id=conversation_id,
            message_id=message_id,
            message_text=message_text,
        )

    reminder = create_reminder(db=db, user_id=user_id, payload=ReminderCreate(title=title, due_at=due_at))
    _create_audit_event(
        db=db,
        user_id=user_id,
        rule_id=REMINDER_CREATE_RULE_ID,
        reminder_id=reminder.id,
        conversation_id=conversation_id,
        message_id=message_id,
        payload_json={"action": "create_reminder", "status": "executed", "title": title, "due_at": due_at.isoformat()},
    )
    return ChatAction(action="create_reminder", status="executed", rule_id=REMINDER_CREATE_RULE_ID, reminder_id=reminder.id)


def _process_update_reminder_command(
    db: Session,
    user_id: str,
    message_text: str,
    conversation_id: int,
    message_id: int,
) -> ChatAction:
    match = REMINDER_UPDATE_PREFIX_PATTERN.match(message_text)
    if not match:
        return _invalid_action_with_audit(
            db=db,
            user_id=user_id,
            action="update_reminder",
            rule_id=REMINDER_UPDATE_RULE_ID,
            reminder_id=None,
            conversation_id=conversation_id,
            message_id=message_id,
            message_text=message_text,
        )
    reminder_id = int(match.group("reminder_id"))
    split_result = _split_title_and_due_at(match.group("body"))
    if split_result is None:
        return _invalid_action_with_audit(
            db=db,
            user_id=user_id,
            action="update_reminder",
            rule_id=REMINDER_UPDATE_RULE_ID,
            reminder_id=None,
            requested_reminder_id=reminder_id,
            conversation_id=conversation_id,
            message_id=message_id,
            message_text=message_text,
        )
    title, due_at_raw = split_result
    due_at = _parse_iso_datetime(due_at_raw)
    if not title or due_at is None:
        return _invalid_action_with_audit(
            db=db,
            user_id=user_id,
            action="update_reminder",
            rule_id=REMINDER_UPDATE_RULE_ID,
            reminder_id=None,
            requested_reminder_id=reminder_id,
            conversation_id=conversation_id,
            message_id=message_id,
            message_text=message_text,
        )

    reminder = get_reminder(db=db, user_id=user_id, reminder_id=reminder_id)
    if not reminder:
        _create_audit_event(
            db=db,
            user_id=user_id,
            rule_id=REMINDER_UPDATE_RULE_ID,
            reminder_id=None,
            conversation_id=conversation_id,
            message_id=message_id,
            payload_json={
                "action": "update_reminder",
                "status": "ignored",
                "reason": "reminder_not_found",
                "requested_reminder_id": reminder_id,
            },
        )
        return ChatAction(action="update_reminder", status="ignored", rule_id=REMINDER_UPDATE_RULE_ID, reminder_id=reminder_id)

    updated = update_reminder(db=db, reminder=reminder, payload=ReminderUpdate(title=title, due_at=due_at))
    _create_audit_event(
        db=db,
        user_id=user_id,
        rule_id=REMINDER_UPDATE_RULE_ID,
        reminder_id=updated.id,
        conversation_id=conversation_id,
        message_id=message_id,
        payload_json={"action": "update_reminder", "status": "executed", "title": title, "due_at": due_at.isoformat()},
    )
    return ChatAction(action="update_reminder", status="executed", rule_id=REMINDER_UPDATE_RULE_ID, reminder_id=updated.id)


def _process_cancel_reminder_command(
    db: Session,
    user_id: str,
    message_text: str,
    conversation_id: int,
    message_id: int,
) -> ChatAction:
    match = REMINDER_CANCEL_PATTERN.match(message_text)
    if not match:
        return _invalid_action_with_audit(
            db=db,
            user_id=user_id,
            action="cancel_reminder",
            rule_id=REMINDER_CANCEL_RULE_ID,
            reminder_id=None,
            conversation_id=conversation_id,
            message_id=message_id,
            message_text=message_text,
        )
    reminder_id = int(match.group("reminder_id"))
    reminder = get_reminder(db=db, user_id=user_id, reminder_id=reminder_id)
    if not reminder:
        _create_audit_event(
            db=db,
            user_id=user_id,
            rule_id=REMINDER_CANCEL_RULE_ID,
            reminder_id=None,
            conversation_id=conversation_id,
            message_id=message_id,
            payload_json={
                "action": "cancel_reminder",
                "status": "ignored",
                "reason": "reminder_not_found",
                "requested_reminder_id": reminder_id,
            },
        )
        return ChatAction(action="cancel_reminder", status="ignored", rule_id=REMINDER_CANCEL_RULE_ID, reminder_id=reminder_id)

    updated = update_reminder(db=db, reminder=reminder, payload=ReminderUpdate(status="CANCELLED"))
    _create_audit_event(
        db=db,
        user_id=user_id,
        rule_id=REMINDER_CANCEL_RULE_ID,
        reminder_id=updated.id,
        conversation_id=conversation_id,
        message_id=message_id,
        payload_json={"action": "cancel_reminder", "status": "executed"},
    )
    return ChatAction(action="cancel_reminder", status="executed", rule_id=REMINDER_CANCEL_RULE_ID, reminder_id=updated.id)


def _parse_iso_datetime(value: str) -> datetime | None:
    if "T" not in value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _split_title_and_due_at(body: str) -> tuple[str, str] | None:
    title_part, separator, due_at_part = body.rpartition(" at ")
    if not separator:
        return None
    title = title_part.strip()
    due_at_raw = due_at_part.strip()
    if not title or not due_at_raw:
        return None
    return (title, due_at_raw)


def _invalid_action_with_audit(
    db: Session,
    user_id: str,
    action: str,
    rule_id: str,
    reminder_id: int | None,
    conversation_id: int,
    message_id: int,
    message_text: str,
    requested_reminder_id: int | None = None,
) -> ChatAction:
    payload_json = {"action": action, "status": "invalid", "reason": "invalid_command_format", "message": message_text}
    if requested_reminder_id is not None:
        payload_json["requested_reminder_id"] = requested_reminder_id
    _create_audit_event(
        db=db,
        user_id=user_id,
        rule_id=rule_id,
        reminder_id=reminder_id,
        conversation_id=conversation_id,
        message_id=message_id,
        payload_json=payload_json,
    )
    return ChatAction(action=action, status="invalid", rule_id=rule_id, reminder_id=reminder_id)


def _create_audit_event(
    db: Session,
    user_id: str,
    rule_id: str,
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
            rule_id=rule_id,
            payload_json=payload_json,
        )
    )
