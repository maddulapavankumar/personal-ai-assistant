from datetime import datetime, timedelta

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


def test_chat_complete_reminder_command_completes_existing_reminder_and_writes_audit(client, db_session):
    create_response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to submit report at 2026-10-05T09:00:00Z"},
    )
    reminder_id = create_response.json()["actions"][0]["reminder_id"]

    complete_response = client.post(
        "/api/v1/chat",
        json={"message": f"complete reminder {reminder_id}"},
    )
    assert complete_response.status_code == 200
    body = complete_response.json()
    assert body["actions"][0]["action"] == "complete_reminder"
    assert body["actions"][0]["status"] == "executed"
    assert body["actions"][0]["rule_id"] == "chat_complete_reminder_id_v1"
    assert "Reminder marked completed" in body["reply"]

    reminder = db_session.query(Reminder).filter(Reminder.id == reminder_id).one()
    assert reminder.status == "COMPLETED"

    events = db_session.query(ReminderAuditEvent).order_by(ReminderAuditEvent.id.asc()).all()
    assert len(events) == 2
    assert events[1].rule_id == "chat_complete_reminder_id_v1"
    assert events[1].payload_json["action"] == "complete_reminder"
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


def test_chat_complete_reminder_command_returns_ignored_when_missing_reminder(client, db_session):
    response = client.post(
        "/api/v1/chat",
        json={"message": "complete reminder 999"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["action"] == "complete_reminder"
    assert body["actions"][0]["status"] == "ignored"
    assert body["actions"][0]["rule_id"] == "chat_complete_reminder_id_v1"
    assert "Reminder not found" in body["reply"]

    events = db_session.query(ReminderAuditEvent).all()
    assert len(events) == 1
    assert events[0].reminder_id is None
    assert events[0].payload_json["action"] == "complete_reminder"
    assert events[0].payload_json["status"] == "ignored"
    assert events[0].payload_json["reason"] == "reminder_not_found"
    assert events[0].payload_json["requested_reminder_id"] == 999


def test_chat_cancel_after_complete_returns_invalid_status_transition(client, db_session):
    create_response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to final task at 2026-10-05T09:00:00Z"},
    )
    reminder_id = create_response.json()["actions"][0]["reminder_id"]
    complete_response = client.post("/api/v1/chat", json={"message": f"complete reminder {reminder_id}"})
    assert complete_response.status_code == 200

    cancel_response = client.post("/api/v1/chat", json={"message": f"cancel reminder {reminder_id}"})
    assert cancel_response.status_code == 200
    body = cancel_response.json()
    assert body["actions"][0]["action"] == "cancel_reminder"
    assert body["actions"][0]["status"] == "invalid"
    assert body["reply"] == "Invalid reminder status transition for that command."


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


def test_chat_show_reminders_returns_active_reminders(client, db_session):
    now_local = datetime.now().astimezone()
    first_due = (now_local + timedelta(hours=1)).isoformat()
    second_due = (now_local + timedelta(hours=2)).isoformat()
    client.post("/api/v1/reminders", json={"title": "Pay rent", "due_at": second_due})
    client.post("/api/v1/reminders", json={"title": "Call bank", "due_at": first_due})

    response = client.post("/api/v1/chat", json={"message": "show reminders"})
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["action"] == "query_reminders"
    assert body["actions"][0]["status"] == "executed"
    assert body["actions"][0]["rule_id"] == "chat_show_reminders_v1"
    assert "Active reminders:" in body["reply"]
    assert "- #" in body["reply"]
    assert body["reply"].index("Call bank") < body["reply"].index("Pay rent")
    assert db_session.query(ReminderAuditEvent).count() == 0


def test_chat_show_reminders_due_today_filters_by_local_day(client):
    now_local = datetime.now().astimezone()
    today_due = now_local.replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    tomorrow_due = (now_local + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    client.post("/api/v1/reminders", json={"title": "Today reminder", "due_at": today_due})
    client.post("/api/v1/reminders", json={"title": "Tomorrow reminder", "due_at": tomorrow_due})

    response = client.post("/api/v1/chat", json={"message": "show reminders due today"})
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["rule_id"] == "chat_show_reminders_due_today_v1"
    assert "Active reminders due today:" in body["reply"]
    assert "Today reminder" in body["reply"]
    assert "Tomorrow reminder" not in body["reply"]


def test_chat_show_reminders_due_tomorrow_filters_by_local_day(client):
    now_local = datetime.now().astimezone()
    today_due = now_local.replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    tomorrow_due = (now_local + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    next_day_due = (now_local + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    client.post("/api/v1/reminders", json={"title": "Today reminder", "due_at": today_due})
    client.post("/api/v1/reminders", json={"title": "Tomorrow reminder", "due_at": tomorrow_due})
    client.post("/api/v1/reminders", json={"title": "Next day reminder", "due_at": next_day_due})

    response = client.post("/api/v1/chat", json={"message": "show reminders due tomorrow"})
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["rule_id"] == "chat_show_reminders_due_tomorrow_v1"
    assert "Active reminders due tomorrow:" in body["reply"]
    assert "Tomorrow reminder" in body["reply"]
    assert "Today reminder" not in body["reply"]
    assert "Next day reminder" not in body["reply"]


def test_chat_show_reminders_due_this_week_filters_by_local_week(client):
    now_local = datetime.now().astimezone()
    start_of_week = now_local - timedelta(days=now_local.weekday())
    this_week_due = (start_of_week + timedelta(days=2, hours=1)).isoformat()
    next_week_due = (start_of_week + timedelta(days=8, hours=1)).isoformat()
    client.post("/api/v1/reminders", json={"title": "This week reminder", "due_at": this_week_due})
    client.post("/api/v1/reminders", json={"title": "Next week reminder", "due_at": next_week_due})

    response = client.post("/api/v1/chat", json={"message": "show reminders due this week"})
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["rule_id"] == "chat_show_reminders_due_this_week_v1"
    assert "Active reminders due this week:" in body["reply"]
    assert "This week reminder" in body["reply"]
    assert "Next week reminder" not in body["reply"]


def test_chat_show_reminders_due_this_week_handles_naive_due_at_without_error(client, db_session):
    now_local = datetime.now().astimezone()
    start_of_week = now_local - timedelta(days=now_local.weekday())
    reminder = Reminder(
        user_id="default-user",
        title="Naive local reminder",
        notes="",
        due_at=(start_of_week + timedelta(days=3, hours=2)).replace(tzinfo=None),
        recurrence_rule=None,
        status="ACTIVE",
    )
    db_session.add(reminder)
    db_session.commit()

    response = client.post("/api/v1/chat", json={"message": "show reminders due this week"})
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["status"] == "executed"
    assert "Naive local reminder" in body["reply"]


def test_chat_invalid_show_reminders_command_returns_invalid(client):
    response = client.post("/api/v1/chat", json={"message": "show reminders tomorrow"})
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["action"] == "query_reminders"
    assert body["actions"][0]["status"] == "invalid"
    assert "Invalid reminder query command." in body["reply"]
