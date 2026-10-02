from app.models.memory_review_event import MemoryReviewEvent
from app.models.reminder import Reminder
from app.models.reminder_audit_event import ReminderAuditEvent


def test_step10_smoke_journey_memory_review_and_reminder_lifecycle(client, db_session):
    chat_response = client.post("/api/v1/chat", json={"message": "I own an Echo Show 5."})
    assert chat_response.status_code == 200
    conversation_id = chat_response.json()["conversation_id"]

    queue_response = client.get("/api/v1/memories/review-queue")
    assert queue_response.status_code == 200
    queue = queue_response.json()
    assert len(queue) == 1
    pending_memory = queue[0]
    assert pending_memory["status"] == "PENDING_REVIEW"
    assert pending_memory["type"] == "FACT"
    assert pending_memory["provenance_json"]["rule_id"] == "fact_ownership_statement"

    memory_id = pending_memory["id"]
    approve_response = client.post(
        f"/api/v1/memories/{memory_id}/review",
        json={"decision": "approve", "reason": "smoke journey approved"},
    )
    assert approve_response.status_code == 200
    approved_memory = approve_response.json()
    assert approved_memory["status"] == "ACTIVE"
    assert approved_memory["provenance_json"]["decision"] == "approve"

    detail_response = client.get(f"/api/v1/memories/{memory_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "ACTIVE"

    create_reminder_response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to pay rent at 2026-10-05T09:00:00Z", "conversation_id": conversation_id},
    )
    assert create_reminder_response.status_code == 200
    create_action = create_reminder_response.json()["actions"][0]
    assert create_action["action"] == "create_reminder"
    assert create_action["status"] == "executed"
    assert create_action["rule_id"] == "chat_remind_me_iso_v1"
    reminder_id = create_action["reminder_id"]
    assert reminder_id is not None

    update_reminder_response = client.post(
        "/api/v1/chat",
        json={
            "message": f"update reminder {reminder_id} title pay internet bill at 2026-10-06T08:30:00Z",
            "conversation_id": conversation_id,
        },
    )
    assert update_reminder_response.status_code == 200
    update_action = update_reminder_response.json()["actions"][0]
    assert update_action["action"] == "update_reminder"
    assert update_action["status"] == "executed"
    assert update_action["rule_id"] == "chat_update_reminder_id_iso_v1"

    cancel_reminder_response = client.post(
        "/api/v1/chat",
        json={"message": f"cancel reminder {reminder_id}", "conversation_id": conversation_id},
    )
    assert cancel_reminder_response.status_code == 200
    cancel_action = cancel_reminder_response.json()["actions"][0]
    assert cancel_action["action"] == "cancel_reminder"
    assert cancel_action["status"] == "executed"
    assert cancel_action["rule_id"] == "chat_cancel_reminder_id_v1"

    reminders = db_session.query(Reminder).all()
    assert len(reminders) == 1
    assert reminders[0].id == reminder_id
    assert reminders[0].title == "pay internet bill"
    assert reminders[0].status == "CANCELLED"

    review_events = db_session.query(MemoryReviewEvent).all()
    assert len(review_events) == 1
    assert review_events[0].memory_id == memory_id
    assert review_events[0].decision == "approve"

    reminder_events = db_session.query(ReminderAuditEvent).order_by(ReminderAuditEvent.id.asc()).all()
    assert len(reminder_events) == 3
    assert [event.rule_id for event in reminder_events] == [
        "chat_remind_me_iso_v1",
        "chat_update_reminder_id_iso_v1",
        "chat_cancel_reminder_id_v1",
    ]
    assert [event.payload_json["status"] for event in reminder_events] == ["executed", "executed", "executed"]
