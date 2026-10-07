def test_dashboard_page_loads(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "Personal AI Assistant Dashboard" in body
    assert "/api/v1/briefings/daily" in body
    assert "/api/v1/briefings/weekly" in body
    assert "/api/v1/briefings/reminder-completion-stats" in body
    assert "/api/v1/routines/next-actions" in body
    assert "/api/v1/memories/review-queue" in body
    assert "/api/v1/chat" in body
    assert "/api/v1/reminders/" in body
    assert "Chat Assistant" in body
    assert "Memory Review Queue" in body
    assert "show weekly briefing" in body
    assert "show reminders" in body
    assert "show reminders due today" in body
    assert "show reminders due tomorrow" in body
    assert "show reminders overdue" in body
    assert "show reminders due next 7 days" in body
    assert "show reminders due this week" in body
    assert "Approve" in body
    assert "Reject" in body
    assert "Complete" in body
    assert "Cancel" in body
