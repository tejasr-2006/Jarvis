from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "app": "JARVIS",
        "message": "JARVIS is online",
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "app": "JARVIS",
        "environment": "development",
    }


def test_ai_provider_status_does_not_expose_secrets():
    response = client.get("/ai/provider")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] in {"gemini", "ollama"}
    assert "api_key" not in body
    assert "GEMINI_API_KEY" not in body


def test_command_rejects_blank(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "JARVIS_API_KEY", "test-secret")
    response = client.post("/command", json={"command": "   "},
                           headers={"X-JARVIS-API-Key": "test-secret"})
    assert response.status_code == 422


def test_executor_requires_confirmation_even_if_model_says_false(monkeypatch):
    import asyncio
    from app.services.command_executor import CommandExecutor

    result = asyncio.run(
        CommandExecutor().execute(
            {
                "service": "email_manager",
                "intent": "send an email",
                "requires_confirmation": False,
            },
            "send an email to my professor",
        )
    )
    assert result["status"] == "confirmation_required"


def test_executor_rejects_unknown_service():
    import asyncio
    from app.services.command_executor import CommandExecutor

    result = asyncio.run(
        CommandExecutor().execute(
            {
                "service": "arbitrary_service",
                "intent": "do something",
                "requires_confirmation": False,
            },
            "do something",
        )
    )
    assert result["status"] == "rejected"
