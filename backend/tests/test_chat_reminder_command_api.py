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
    assert events[0].payload_json["action"] == "create_reminder"
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
    assert events[0].payload_json["action"] == "create_reminder"
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


def test_chat_update_reminder_command_updates_existing_reminder_and_writes_audit(client, db_session):
    create_response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to pay rent at 2026-10-05T09:00:00Z"},
    )
    reminder_id = create_response.json()["actions"][0]["reminder_id"]

    update_response = client.post(
        "/api/v1/chat",
        json={"message": f"update reminder {reminder_id} title pay internet bill at 2026-10-06T08:30:00Z"},
    )
    assert update_response.status_code == 200
    body = update_response.json()
    assert body["actions"][0]["action"] == "update_reminder"
    assert body["actions"][0]["status"] == "executed"
    assert body["actions"][0]["rule_id"] == "chat_update_reminder_id_iso_v1"
    assert "Reminder updated" in body["reply"]

    reminder = db_session.query(Reminder).filter(Reminder.id == reminder_id).one()
    assert reminder.title == "pay internet bill"

    events = db_session.query(ReminderAuditEvent).order_by(ReminderAuditEvent.id.asc()).all()
    assert len(events) == 2
    assert events[1].rule_id == "chat_update_reminder_id_iso_v1"
    assert events[1].payload_json["action"] == "update_reminder"
    assert events[1].payload_json["status"] == "executed"


def test_chat_cancel_reminder_command_cancels_existing_reminder_and_writes_audit(client, db_session):
    create_response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to submit report at 2026-10-05T09:00:00Z"},
    )
    reminder_id = create_response.json()["actions"][0]["reminder_id"]

    cancel_response = client.post(
        "/api/v1/chat",
        json={"message": f"cancel reminder {reminder_id}"},
    )
    assert cancel_response.status_code == 200
    body = cancel_response.json()
    assert body["actions"][0]["action"] == "cancel_reminder"
    assert body["actions"][0]["status"] == "executed"
    assert body["actions"][0]["rule_id"] == "chat_cancel_reminder_id_v1"
    assert "Reminder cancelled" in body["reply"]

    reminder = db_session.query(Reminder).filter(Reminder.id == reminder_id).one()
    assert reminder.status == "CANCELLED"

    events = db_session.query(ReminderAuditEvent).order_by(ReminderAuditEvent.id.asc()).all()
    assert len(events) == 2
    assert events[1].rule_id == "chat_cancel_reminder_id_v1"
    assert events[1].payload_json["action"] == "cancel_reminder"
    assert events[1].payload_json["status"] == "executed"


def test_chat_update_reminder_command_returns_ignored_when_missing_reminder(client, db_session):
    response = client.post(
        "/api/v1/chat",
        json={"message": "update reminder 999 title pay bill at 2026-10-06T08:30:00Z"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["action"] == "update_reminder"
    assert body["actions"][0]["status"] == "ignored"
    assert body["actions"][0]["rule_id"] == "chat_update_reminder_id_iso_v1"
    assert "Reminder not found" in body["reply"]

    events = db_session.query(ReminderAuditEvent).all()
    assert len(events) == 1
    assert events[0].reminder_id is None
    assert events[0].payload_json["action"] == "update_reminder"
    assert events[0].payload_json["status"] == "ignored"
    assert events[0].payload_json["reason"] == "reminder_not_found"
    assert events[0].payload_json["requested_reminder_id"] == 999


def test_chat_cancel_reminder_command_returns_ignored_when_missing_reminder(client, db_session):
    response = client.post(
        "/api/v1/chat",
        json={"message": "cancel reminder 999"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["action"] == "cancel_reminder"
    assert body["actions"][0]["status"] == "ignored"
    assert body["actions"][0]["rule_id"] == "chat_cancel_reminder_id_v1"
    assert "Reminder not found" in body["reply"]

    events = db_session.query(ReminderAuditEvent).all()
    assert len(events) == 1
    assert events[0].reminder_id is None
    assert events[0].payload_json["action"] == "cancel_reminder"
    assert events[0].payload_json["status"] == "ignored"
    assert events[0].payload_json["reason"] == "reminder_not_found"
    assert events[0].payload_json["requested_reminder_id"] == 999


def test_chat_malformed_update_reminder_command_returns_invalid_action(client, db_session):
    response = client.post(
        "/api/v1/chat",
        json={"message": "update reminder 12 pay bill tomorrow"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["action"] == "update_reminder"
    assert body["actions"][0]["status"] == "invalid"
    assert "Invalid reminder command" in body["reply"]

    events = db_session.query(ReminderAuditEvent).all()
    assert len(events) == 1
    assert events[0].rule_id == "chat_update_reminder_id_iso_v1"
    assert events[0].payload_json["action"] == "update_reminder"
    assert events[0].payload_json["status"] == "invalid"


def test_chat_create_reminder_command_supports_title_with_at_phrase(client, db_session):
    response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to schedule meeting at office at 2026-10-05T09:00:00Z"},
    )
    assert response.status_code == 200
    action = response.json()["actions"][0]
    assert action["status"] == "executed"

    reminder = db_session.query(Reminder).one()
    assert reminder.title == "schedule meeting at office"


def test_chat_update_reminder_command_supports_title_with_at_phrase(client, db_session):
    create_response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to pay rent at 2026-10-05T09:00:00Z"},
    )
    reminder_id = create_response.json()["actions"][0]["reminder_id"]

    update_response = client.post(
        "/api/v1/chat",
        json={"message": f"update reminder {reminder_id} title pick up groceries at market at 2026-10-06T08:30:00Z"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["actions"][0]["status"] == "executed"

    reminder = db_session.query(Reminder).filter(Reminder.id == reminder_id).one()
    assert reminder.title == "pick up groceries at market"
