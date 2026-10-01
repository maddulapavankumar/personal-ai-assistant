def test_chat_extracts_preference_memory_with_provenance(client):
    response = client.post("/api/v1/chat", json={"message": "I prefer reminders with context."})
    assert response.status_code == 200
    conversation_id = response.json()["conversation_id"]

    memories_response = client.get("/api/v1/memories")
    assert memories_response.status_code == 200
    memories = memories_response.json()
    assert len(memories) == 1

    memory = memories[0]
    assert memory["type"] == "PREFERENCE"
    assert memory["source"] == "CHAT_RULE_EXTRACTOR_V1"
    assert memory["provenance_json"]["conversation_id"] == conversation_id
    assert memory["provenance_json"]["message_id"] > 0
    assert memory["provenance_json"]["rule_id"] == "pref_prefer_statement"
    assert memory["provenance_json"]["extractor_version"] == "memory-rule-extractor-v1"
    assert memory["provenance_json"]["decision"] == "accepted"
    assert memory["provenance_json"]["decision_reason"] == "new_extraction"
    assert memory["provenance_json"]["reviewed_by"] == "system"


def test_chat_extracts_fact_memory(client):
    response = client.post("/api/v1/chat", json={"message": "I own an Echo Show 5."})
    assert response.status_code == 200

    memories_response = client.get("/api/v1/memories")
    assert memories_response.status_code == 200
    memories = memories_response.json()
    assert len(memories) == 1
    assert memories[0]["type"] == "FACT"
    assert memories[0]["status"] == "PENDING_REVIEW"
    assert memories[0]["provenance_json"]["rule_id"] == "fact_ownership_statement"


def test_chat_extracts_dislike_preference_memory(client):
    response = client.post("/api/v1/chat", json={"message": "I don't like loud alarms."})
    assert response.status_code == 200

    memories_response = client.get("/api/v1/memories")
    assert memories_response.status_code == 200
    memories = memories_response.json()
    assert len(memories) == 1
    assert memories[0]["type"] == "PREFERENCE"
    assert memories[0]["provenance_json"]["rule_id"] == "pref_dislike_statement"


def test_chat_skips_non_ownership_i_have_phrases(client):
    response = client.post("/api/v1/chat", json={"message": "I have to go now."})
    assert response.status_code == 200

    memories_response = client.get("/api/v1/memories")
    assert memories_response.status_code == 200
    assert memories_response.json() == []


def test_chat_skips_memory_when_no_rule_matches(client):
    response = client.post("/api/v1/chat", json={"message": "Hello there."})
    assert response.status_code == 200

    memories_response = client.get("/api/v1/memories")
    assert memories_response.status_code == 200
    assert memories_response.json() == []


def test_chat_suppresses_duplicate_extracted_memories(client):
    first = client.post("/api/v1/chat", json={"message": "I own an Echo Show 5."})
    assert first.status_code == 200
    second = client.post("/api/v1/chat", json={"message": "I own an Echo Show 5."})
    assert second.status_code == 200

    memories_response = client.get("/api/v1/memories")
    assert memories_response.status_code == 200
    memories = memories_response.json()
    assert len(memories) == 1
    memory = memories[0]
    assert memory["status"] == "PENDING_REVIEW"
    assert memory["provenance_json"]["duplicate_suppressed_count"] == 1
    assert len(memory["provenance_json"]["duplicate_suppressed_events"]) == 1
