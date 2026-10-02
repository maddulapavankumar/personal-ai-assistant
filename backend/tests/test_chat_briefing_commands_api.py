from datetime import datetime, timedelta


def test_chat_brief_me_returns_daily_briefing(client):
    now_local = datetime.now().astimezone()
    due_today = now_local.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    client.post("/api/v1/reminders", json={"title": "Standup prep", "due_at": due_today})
    memory_response = client.post(
        "/api/v1/memories",
        json={"type": "PREFERENCE", "content": "I prioritize morning planning.", "confidence": 0.9, "importance": 0.9},
    )
    assert memory_response.status_code == 201

    response = client.post("/api/v1/chat", json={"message": "brief me"})
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["action"] == "query_daily_briefing"
    assert body["actions"][0]["rule_id"] == "chat_daily_briefing_v1"
    assert f"Daily briefing for {now_local.date().isoformat()}" in body["reply"]
    assert "Reminders due today:" in body["reply"]
    assert "Top active memories:" in body["reply"]
    assert "Routine suggestions:" in body["reply"]


def test_chat_daily_delta_command_returns_delta_summary(client):
    now_local = datetime.now().astimezone()
    due_today = now_local.replace(hour=11, minute=0, second=0, microsecond=0).isoformat()
    due_yesterday = (now_local - timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0).isoformat()
    client.post("/api/v1/reminders", json={"title": "Today task", "due_at": due_today})
    client.post("/api/v1/reminders", json={"title": "Yesterday task", "due_at": due_yesterday})

    response = client.post("/api/v1/chat", json={"message": "what changed since yesterday"})
    assert response.status_code == 200
    body = response.json()
    assert body["actions"][0]["action"] == "query_daily_briefing_delta"
    assert body["actions"][0]["rule_id"] == "chat_daily_briefing_delta_v1"
    assert f"Daily delta for {now_local.date().isoformat()}" in body["reply"]
    assert "Due reminders today:" in body["reply"]
    assert "Due reminders yesterday:" in body["reply"]
    assert "Due reminder delta:" in body["reply"]
