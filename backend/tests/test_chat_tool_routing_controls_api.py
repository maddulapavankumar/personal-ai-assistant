def test_chat_with_extraction_off_does_not_create_memories(client):
    response = client.post(
        "/api/v1/chat",
        json={"message": "I prefer reminders with context.", "extraction_mode": "off"},
    )
    assert response.status_code == 200

    memories_response = client.get("/api/v1/memories")
    assert memories_response.status_code == 200
    assert memories_response.json() == []


def test_chat_with_extraction_auto_creates_memories(client):
    response = client.post(
        "/api/v1/chat",
        json={"message": "I own an Echo Show 5.", "extraction_mode": "auto"},
    )
    assert response.status_code == 200

    memories_response = client.get("/api/v1/memories")
    assert memories_response.status_code == 200
    memories = memories_response.json()
    assert len(memories) == 1
    assert memories[0]["type"] == "FACT"
