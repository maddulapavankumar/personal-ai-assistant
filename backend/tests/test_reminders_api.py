from datetime import datetime, timedelta, timezone


def test_create_and_list_reminders(client):
    due_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    create_response = client.post(
        "/api/v1/reminders",
        json={"title": "Buy groceries", "notes": "Milk and eggs", "due_at": due_at, "recurrence_rule": None},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Buy groceries"
    assert created["status"] == "ACTIVE"

    list_response = client.get("/api/v1/reminders")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_update_and_delete_reminder(client):
    due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create_response = client.post("/api/v1/reminders", json={"title": "Pay electricity bill", "due_at": due_at})
    reminder_id = create_response.json()["id"]

    patch_response = client.patch(f"/api/v1/reminders/{reminder_id}", json={"status": "CANCELLED"})
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "CANCELLED"

    delete_response = client.delete(f"/api/v1/reminders/{reminder_id}")
    assert delete_response.status_code == 204

    list_response = client.get("/api/v1/reminders")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_patch_reminder_rejects_invalid_status_transition(client):
    due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create_response = client.post("/api/v1/reminders", json={"title": "Status transition item", "due_at": due_at})
    reminder_id = create_response.json()["id"]

    completed_response = client.patch(f"/api/v1/reminders/{reminder_id}", json={"status": "COMPLETED"})
    assert completed_response.status_code == 200
    assert completed_response.json()["status"] == "COMPLETED"

    invalid_response = client.patch(f"/api/v1/reminders/{reminder_id}", json={"status": "ACTIVE"})
    assert invalid_response.status_code == 409
    assert "Invalid reminder status transition: COMPLETED -> ACTIVE" in invalid_response.json()["detail"]


def test_patch_reminder_accepts_idempotent_status_update(client):
    due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create_response = client.post("/api/v1/reminders", json={"title": "Idempotent status item", "due_at": due_at})
    reminder_id = create_response.json()["id"]

    first_patch = client.patch(f"/api/v1/reminders/{reminder_id}", json={"status": "ACTIVE"})
    second_patch = client.patch(f"/api/v1/reminders/{reminder_id}", json={"status": "ACTIVE"})
    assert first_patch.status_code == 200
    assert second_patch.status_code == 200
    assert second_patch.json()["status"] == "ACTIVE"
