from app.models.reminder import Reminder
from app.models.reminder_audit_event import ReminderAuditEvent


def test_chat_reminder_command_creates_reminder_and_audit_event(client, db_session):
    response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to pay rent at 2026-10-05T09:00:00Z"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"]
    action = body["actions"][0]
    assert action["action"] == "create_reminder"
    assert action["status"] == "executed"
    assert action["rule_id"] == "chat_remind_me_iso_v1"
    assert action["reminder_id"] is not None

    reminders = db_session.query(Reminder).all()
    assert len(reminders) == 1
    assert reminders[0].title == "pay rent"

    events = db_session.query(ReminderAuditEvent).all()
    assert len(events) == 1
    assert events[0].reminder_id == reminders[0].id
    assert events[0].rule_id == "chat_remind_me_iso_v1"
    assert events[0].payload_json["status"] == "executed"


def test_chat_reminder_command_with_invalid_datetime_creates_no_reminder(client, db_session):
    response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to pay rent at 2026-10-05"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"]
    action = body["actions"][0]
    assert action["status"] == "invalid"
    assert action["reminder_id"] is None
    assert "Invalid reminder command" in body["reply"]

    reminders = db_session.query(Reminder).all()
    assert reminders == []

    events = db_session.query(ReminderAuditEvent).all()
    assert len(events) == 1
    assert events[0].reminder_id is None
    assert events[0].payload_json["status"] == "invalid"


def test_chat_malformed_reminder_command_returns_invalid_action(client, db_session):
    response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to pay rent tomorrow"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"]
    assert body["actions"][0]["status"] == "invalid"
    assert "Invalid reminder command" in body["reply"]

    reminders = db_session.query(Reminder).all()
    assert reminders == []
    events = db_session.query(ReminderAuditEvent).all()
    assert len(events) == 1
    assert events[0].payload_json["reason"] == "invalid_command_format"
