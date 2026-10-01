def test_get_memories_can_filter_by_status(client):
    create_active = client.post("/api/v1/memories", json={"type": "FACT", "content": "I own a bicycle."})
    assert create_active.status_code == 201
    create_other = client.post("/api/v1/memories", json={"type": "FACT", "content": "I own a scooter."})
    assert create_other.status_code == 201
    second_id = create_other.json()["id"]

    patch_response = client.patch(
        f"/api/v1/memories/{second_id}",
        json={"status": "SUPERSEDED", "reviewed_by": "user", "decision_reason": "outdated fact"},
    )
    assert patch_response.status_code == 200

    active_response = client.get("/api/v1/memories?status=ACTIVE")
    assert active_response.status_code == 200
    active_memories = active_response.json()
    assert len(active_memories) == 1
    assert active_memories[0]["content"] == "I own a bicycle."

    superseded_response = client.get("/api/v1/memories?status=SUPERSEDED")
    assert superseded_response.status_code == 200
    superseded_memories = superseded_response.json()
    assert len(superseded_memories) == 1
    assert superseded_memories[0]["content"] == "I own a scooter."


def test_patch_memory_preserves_manual_override_provenance(client):
    create_response = client.post("/api/v1/memories", json={"type": "PREFERENCE", "content": "I prefer loud alarms."})
    assert create_response.status_code == 201
    memory_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/api/v1/memories/{memory_id}",
        json={"status": "SUPERSEDED", "decision": "manual_override", "decision_reason": "user corrected preference"},
    )
    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["status"] == "SUPERSEDED"
    assert updated["provenance_json"]["decision"] == "manual_override"
    assert updated["provenance_json"]["decision_reason"] == "user corrected preference"
    assert updated["provenance_json"]["reviewed_by"] == "user"

