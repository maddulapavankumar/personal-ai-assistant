from app.models.memory_review_event import MemoryReviewEvent


def test_review_queue_returns_pending_memories(client):
    response = client.post("/api/v1/chat", json={"message": "I own an Echo Show 5."})
    assert response.status_code == 200

    queue_response = client.get("/api/v1/memories/review-queue")
    assert queue_response.status_code == 200
    queue = queue_response.json()
    assert len(queue) == 1
    assert queue[0]["status"] == "PENDING_REVIEW"
    assert queue[0]["type"] == "FACT"


def test_review_endpoint_approves_pending_memory_and_writes_event(client, db_session):
    create_response = client.post("/api/v1/chat", json={"message": "I own an Echo Show 5."})
    assert create_response.status_code == 200

    queue_response = client.get("/api/v1/memories/review-queue")
    memory_id = queue_response.json()[0]["id"]

    review_response = client.post(
        f"/api/v1/memories/{memory_id}/review",
        json={"decision": "approve", "reason": "confirmed ownership"},
    )
    assert review_response.status_code == 200
    reviewed = review_response.json()
    assert reviewed["status"] == "ACTIVE"
    assert reviewed["provenance_json"]["decision"] == "approve"
    assert reviewed["provenance_json"]["decision_reason"] == "confirmed ownership"
    assert reviewed["provenance_json"]["reviewed_by"] == "user"

    events = db_session.query(MemoryReviewEvent).all()
    assert len(events) == 1
    assert events[0].memory_id == memory_id
    assert events[0].decision == "approve"
    assert events[0].reason == "confirmed ownership"


def test_review_endpoint_rejects_pending_memory(client):
    create_response = client.post("/api/v1/chat", json={"message": "I own an Echo Show 5."})
    assert create_response.status_code == 200

    queue_response = client.get("/api/v1/memories/review-queue")
    memory_id = queue_response.json()[0]["id"]

    review_response = client.post(
        f"/api/v1/memories/{memory_id}/review",
        json={"decision": "reject", "reason": "not relevant"},
    )
    assert review_response.status_code == 200
    reviewed = review_response.json()
    assert reviewed["status"] == "REJECTED"
    assert reviewed["provenance_json"]["decision"] == "reject"


def test_review_endpoint_rejects_non_pending_memory(client):
    chat_response = client.post("/api/v1/chat", json={"message": "I own an Echo Show 5."})
    assert chat_response.status_code == 200
    queue_response = client.get("/api/v1/memories/review-queue")
    memory_id = queue_response.json()[0]["id"]

    first_review = client.post(
        f"/api/v1/memories/{memory_id}/review",
        json={"decision": "approve", "reason": "confirmed"},
    )
    assert first_review.status_code == 200

    review_response = client.post(
        f"/api/v1/memories/{memory_id}/review",
        json={"decision": "approve", "reason": "already reviewed"},
    )
    assert review_response.status_code == 409
    assert "Only PENDING_REVIEW memories can be reviewed" in review_response.json()["detail"]
