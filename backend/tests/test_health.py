from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok_and_providers() -> None:
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "fake"
    assert body["embedding_provider"] == "fake"
