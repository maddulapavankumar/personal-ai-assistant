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

