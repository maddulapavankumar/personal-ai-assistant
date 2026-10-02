from datetime import datetime, timedelta


def test_reminder_completion_stats_returns_zero_values_by_default(client):
    response = client.get("/api/v1/briefings/reminder-completion-stats")
    assert response.status_code == 200
    body = response.json()
    assert body["due_today_count"] == 0
    assert body["completed_due_today_count"] == 0
    assert body["completion_rate_today"] == 0.0
    assert body["due_this_week_count"] == 0
    assert body["completed_due_this_week_count"] == 0
    assert body["completion_rate_this_week"] == 0.0


def test_reminder_completion_stats_counts_completed_vs_due(client):
    now_local = datetime.now().astimezone()
    due_today = now_local.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    due_today_completed = now_local.replace(hour=11, minute=0, second=0, microsecond=0).isoformat()
    due_this_week_active = (now_local + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    due_cancelled = now_local.replace(hour=15, minute=0, second=0, microsecond=0).isoformat()

    client.post("/api/v1/reminders", json={"title": "Today active", "due_at": due_today})
    reminder_completed = client.post("/api/v1/reminders", json={"title": "Today done", "due_at": due_today_completed}).json()
    client.post("/api/v1/reminders", json={"title": "Week active", "due_at": due_this_week_active})
    reminder_cancelled = client.post("/api/v1/reminders", json={"title": "Cancelled item", "due_at": due_cancelled}).json()

    completed_patch = client.patch(f"/api/v1/reminders/{reminder_completed['id']}", json={"status": "COMPLETED"})
    cancelled_patch = client.patch(f"/api/v1/reminders/{reminder_cancelled['id']}", json={"status": "CANCELLED"})
    assert completed_patch.status_code == 200
    assert cancelled_patch.status_code == 200

    response = client.get("/api/v1/briefings/reminder-completion-stats")
    assert response.status_code == 200
    body = response.json()

    assert body["due_today_count"] == 2
    assert body["completed_due_today_count"] == 1
    assert body["completion_rate_today"] == 0.5
    assert body["due_this_week_count"] >= 3
    assert body["completed_due_this_week_count"] == 1
    assert body["completion_rate_this_week"] > 0.0
