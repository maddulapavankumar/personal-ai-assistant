def test_chat_returns_memory_context_for_matching_active_memories(client):
    first_memory = client.post(
        "/api/v1/memories",
        json={"type": "FACT", "content": "I own an Echo Show 5.", "confidence": 0.9, "importance": 0.6},
    )
    second_memory = client.post(
        "/api/v1/memories",
        json={"type": "PREFERENCE", "content": "I prefer rent reminders in the morning.", "confidence": 0.9, "importance": 0.8},
    )
    assert first_memory.status_code == 201
    assert second_memory.status_code == 201

    response = client.post("/api/v1/chat", json={"message": "Please set morning rent reminders for my Echo Show."})
    assert response.status_code == 200
    body = response.json()

    memory_context = body["memory_context"]
    assert memory_context is not None
    assert len(memory_context) == 2
    assert memory_context[0]["id"] == second_memory.json()["id"]
    assert memory_context[1]["id"] == first_memory.json()["id"]
    assert memory_context[0]["type"] == "PREFERENCE"
    assert memory_context[1]["type"] == "FACT"


def test_chat_returns_null_memory_context_when_no_active_memory_matches(client):
    create_pending = client.post("/api/v1/chat", json={"message": "I own an Echo Show 5."})
    assert create_pending.status_code == 200

    response = client.post("/api/v1/chat", json={"message": "Please suggest a workout plan."})
    assert response.status_code == 200
    assert response.json()["memory_context"] is None


def test_chat_preserves_reminder_reply_and_includes_matching_memory_context(client):
    memory_response = client.post(
        "/api/v1/memories",
        json={"type": "FACT", "content": "I pay rent monthly.", "confidence": 0.9, "importance": 0.9},
    )
    assert memory_response.status_code == 201

    response = client.post(
        "/api/v1/chat",
        json={"message": "remind me to pay rent at 2026-10-05T09:00:00Z"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Reminder created from your chat command."
    assert body["actions"][0]["action"] == "create_reminder"
    assert body["actions"][0]["status"] == "executed"
    assert body["memory_context"] is not None
    assert len(body["memory_context"]) == 1
    assert body["memory_context"][0]["id"] == memory_response.json()["id"]


def test_chat_does_not_match_memory_on_single_generic_token_overlap(client):
    memory_response = client.post(
        "/api/v1/memories",
        json={"type": "PREFERENCE", "content": "I like weekly meal plan prep.", "confidence": 0.9, "importance": 0.5},
    )
    assert memory_response.status_code == 201

    response = client.post("/api/v1/chat", json={"message": "Can you plan my vacation itinerary?"})
    assert response.status_code == 200
    assert response.json()["memory_context"] is None


def test_chat_memory_context_caps_results_to_three_items(client):
    payloads = [
        {"type": "FACT", "content": "I track rent reminders in October.", "confidence": 0.9, "importance": 0.6},
        {"type": "PREFERENCE", "content": "I prefer morning rent reminders.", "confidence": 0.9, "importance": 0.7},
        {"type": "FACT", "content": "I set monthly rent reminders.", "confidence": 0.9, "importance": 0.8},
        {"type": "FACT", "content": "I keep rent reminder notes.", "confidence": 0.9, "importance": 0.9},
    ]
    created_ids = []
    for payload in payloads:
        create_response = client.post("/api/v1/memories", json=payload)
        assert create_response.status_code == 201
        created_ids.append(create_response.json()["id"])

    response = client.post("/api/v1/chat", json={"message": "Show my monthly morning rent reminders and notes."})
    assert response.status_code == 200
    memory_context = response.json()["memory_context"]
    assert memory_context is not None
    assert len(memory_context) == 3
    returned_ids = [item["id"] for item in memory_context]
    assert returned_ids == [created_ids[3], created_ids[2], created_ids[1]]
