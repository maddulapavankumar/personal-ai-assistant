from datetime import datetime, timedelta


def test_daily_briefing_returns_empty_collections_by_default(client):
    response = client.get("/api/v1/briefings/daily")
    assert response.status_code == 200
    body = response.json()
    assert body["due_reminders_today"] == []
    assert body["top_active_memories"] == []
    assert body["routine_suggestions"] == []


def test_daily_briefing_includes_due_today_memories_and_suggestions(client):
    now_local = datetime.now().astimezone()
    due_today = now_local.replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    due_tomorrow = (now_local + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0).isoformat()

    reminder_today = client.post("/api/v1/reminders", json={"title": "Pay rent monthly", "due_at": due_today})
    reminder_tomorrow = client.post("/api/v1/reminders", json={"title": "Next day task", "due_at": due_tomorrow})
    assert reminder_today.status_code == 201
    assert reminder_tomorrow.status_code == 201

    memory_high = client.post(
        "/api/v1/memories",
        json={"type": "PREFERENCE", "content": "I prefer monthly rent tracking.", "confidence": 0.9, "importance": 0.9},
    )
    memory_mid = client.post(
        "/api/v1/memories",
        json={"type": "FACT", "content": "I review reminders in the morning.", "confidence": 0.8, "importance": 0.7},
    )
    memory_low = client.post(
        "/api/v1/memories",
        json={"type": "FACT", "content": "I write quick notes.", "confidence": 0.6, "importance": 0.4},
    )
    assert memory_high.status_code == 201
    assert memory_mid.status_code == 201
    assert memory_low.status_code == 201

    response = client.get("/api/v1/briefings/daily")
    assert response.status_code == 200
    body = response.json()

    assert len(body["due_reminders_today"]) == 1
    assert body["due_reminders_today"][0]["title"] == "Pay rent monthly"
    assert body["due_reminders_today"][0]["id"] == reminder_today.json()["id"]

    memory_ids = [item["id"] for item in body["top_active_memories"]]
    assert memory_ids == [memory_high.json()["id"], memory_mid.json()["id"], memory_low.json()["id"]]

    suggestion_titles = [item["title"] for item in body["routine_suggestions"]]
    assert "Daily reminder check-in" in suggestion_titles
    assert "Memory-informed planning review" in suggestion_titles
    assert "Align reminders with known preferences" in suggestion_titles


def test_daily_briefing_limits_top_active_memories_to_three(client):
    payloads = [
        {"type": "FACT", "content": "Memory one details.", "confidence": 0.5, "importance": 0.1},
        {"type": "FACT", "content": "Memory two details.", "confidence": 0.6, "importance": 0.2},
        {"type": "FACT", "content": "Memory three details.", "confidence": 0.7, "importance": 0.3},
        {"type": "FACT", "content": "Memory four details.", "confidence": 0.8, "importance": 0.4},
    ]
    for payload in payloads:
        create_response = client.post("/api/v1/memories", json=payload)
        assert create_response.status_code == 201

    response = client.get("/api/v1/briefings/daily")
    assert response.status_code == 200
    assert len(response.json()["top_active_memories"]) == 3
