from datetime import datetime, timedelta


def test_chat_endpoint_creates_conversation(client):
    response = client.post("/api/v1/chat", json={"message": "Hello assistant"})
    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] > 0
    assert "MVP assistant is running" in body["reply"]


def test_list_routines_empty_by_default(client):
    response = client.get("/api/v1/routines")
    assert response.status_code == 200
    assert response.json() == []


def test_routine_suggestions_empty_when_no_active_inputs(client):
    response = client.get("/api/v1/routines/suggestions")
    assert response.status_code == 200
    assert response.json() == []


def test_routine_suggestions_include_reminder_and_memory_based_suggestions(client):
    now_local = datetime.now().astimezone()
    client.post(
        "/api/v1/reminders",
        json={"title": "Pay rent monthly", "due_at": (now_local + timedelta(hours=2)).isoformat()},
    )
    client.post(
        "/api/v1/reminders",
        json={"title": "Rent budget review", "due_at": (now_local + timedelta(hours=3)).isoformat()},
    )
    client.post(
        "/api/v1/memories",
        json={"type": "PREFERENCE", "content": "I prefer monthly rent tracking.", "confidence": 0.9, "importance": 0.8},
    )

    response = client.get("/api/v1/routines/suggestions")
    assert response.status_code == 200
    suggestions = response.json()
    assert len(suggestions) == 3
    assert suggestions[0]["title"] == "Daily reminder check-in"
    assert suggestions[1]["title"] == "Align reminders with known preferences"
    assert suggestions[2]["title"] == "Memory-informed planning review"
    assert suggestions[0]["source_reminder_ids"]
    assert suggestions[2]["source_memory_ids"]


def test_routine_suggestions_avoid_generic_token_false_overlap(client):
    now_local = datetime.now().astimezone()
    client.post(
        "/api/v1/reminders",
        json={"title": "Plan vacation itinerary", "due_at": (now_local + timedelta(hours=4)).isoformat()},
    )
    client.post(
        "/api/v1/memories",
        json={"type": "PREFERENCE", "content": "I like weekly meal plan prep.", "confidence": 0.9, "importance": 0.6},
    )

    response = client.get("/api/v1/routines/suggestions")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert "Align reminders with known preferences" not in titles


def test_next_actions_returns_fallback_when_no_inputs(client):
    response = client.get("/api/v1/routines/next-actions")
    assert response.status_code == 200
    actions = response.json()
    assert len(actions) == 1
    assert actions[0]["title"] == "Create your first reminder"


def test_next_actions_prioritizes_due_reminder_and_memory_review(client):
    now_local = datetime.now().astimezone()
    client.post("/api/v1/reminders", json={"title": "First due", "due_at": (now_local + timedelta(hours=1)).isoformat()})
    client.post("/api/v1/memories", json={"type": "FACT", "content": "I plan meetings at 9am.", "confidence": 0.5, "importance": 0.6})

    response = client.get("/api/v1/routines/next-actions")
    assert response.status_code == 200
    actions = response.json()
    assert actions[0]["title"] == "Complete next due reminder"
    assert actions[1]["title"] == "Run memory-informed planning review"
