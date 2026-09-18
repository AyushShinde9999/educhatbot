import pytest

def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "vector_store" in data

def test_security_headers(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"

def test_public_faqs_route(client):
    response = client.get("/api/faqs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_public_notices_route(client):
    response = client.get("/api/notices")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_chat_endpoint_valid_question(client):
    response = client.post("/api/chat", json={
        "question": "What are the college timings?",
        "session_id": "test_session_123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "fallback_used" in data
