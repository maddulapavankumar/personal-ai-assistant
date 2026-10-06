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
