def test_create_and_list_memories(client):
    create_payload = {
        "type": "FACT",
        "content": "I own an Echo Show 5.",
        "confidence": 0.7,
        "importance": 0.8,
        "source": "USER_MESSAGE",
        "provenance_json": {"message_id": "abc-123"},
    }
    create_response = client.post("/api/v1/memories", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["type"] == "FACT"
    assert created["content"] == "I own an Echo Show 5."

    list_response = client.get("/api/v1/memories")
    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data) == 1
    assert data[0]["source"] == "USER_MESSAGE"


def test_update_and_delete_memory(client):
    create_response = client.post(
        "/api/v1/memories",
        json={"type": "PREFERENCE", "content": "I prefer contextual reminders.", "confidence": 0.6, "importance": 0.7},
    )
    memory_id = create_response.json()["id"]

    patch_response = client.patch(f"/api/v1/memories/{memory_id}", json={"status": "SUPERSEDED", "confidence": 0.4})
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "SUPERSEDED"
    assert patch_response.json()["confidence"] == 0.4

    delete_response = client.delete(f"/api/v1/memories/{memory_id}")
    assert delete_response.status_code == 204

    list_response = client.get("/api/v1/memories")
    assert list_response.status_code == 200
    assert list_response.json() == []

