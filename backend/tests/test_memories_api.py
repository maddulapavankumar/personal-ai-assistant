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


def test_get_memory_by_id(client):
    create_response = client.post(
        "/api/v1/memories",
        json={"type": "FACT", "content": "My thermostat is in the hall.", "confidence": 0.8, "importance": 0.5},
    )
    memory_id = create_response.json()["id"]

    detail_response = client.get(f"/api/v1/memories/{memory_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == memory_id
    assert detail["content"] == "My thermostat is in the hall."


def test_get_memory_by_id_returns_404_for_missing_memory(client):
    response = client.get("/api/v1/memories/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Memory not found"


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


def test_patch_memory_rejects_invalid_status_transition(client):
    create_response = client.post(
        "/api/v1/memories",
        json={"type": "FACT", "content": "I prefer bright lights.", "confidence": 0.8, "importance": 0.6},
    )
    memory_id = create_response.json()["id"]

    patch_response = client.patch(f"/api/v1/memories/{memory_id}", json={"status": "PENDING_REVIEW"})
    assert patch_response.status_code == 409
    assert "Invalid status transition: ACTIVE -> PENDING_REVIEW" in patch_response.json()["detail"]


def test_patch_memory_with_same_status_does_not_mutate_provenance(client):
    create_response = client.post(
        "/api/v1/memories",
        json={"type": "FACT", "content": "I use a standing desk.", "confidence": 0.8, "importance": 0.6},
    )
    memory_id = create_response.json()["id"]

    patch_response = client.patch(f"/api/v1/memories/{memory_id}", json={"status": "ACTIVE"})
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "ACTIVE"
    assert patch_response.json()["provenance_json"] == {}
