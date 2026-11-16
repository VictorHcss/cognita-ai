from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


def test_health_returns_ok_and_providers() -> None:
    # Ignora o .env local: o teste não deve depender da configuração da máquina.
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    try:
        response = TestClient(app).get("/api/health")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "fake"
    assert body["embedding_provider"] == "fake"
