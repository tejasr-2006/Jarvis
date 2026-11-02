import asyncio

from app.config import settings
from app.services.unified_assistant import UnifiedAssistant


class FitnessManagerStub:
    async def get_workouts(self):
        return [{"id": 7, "name": "Morning run"}]


def test_unified_assistant_accepts_fitness_manager_login_credentials(monkeypatch):
    monkeypatch.setattr(settings, "JARVIS_ENABLED_TOOLS", {"fitness.workouts.read"})
    monkeypatch.setattr(settings, "FITNESS_MANAGER_EMAIL", "user@example.test")
    monkeypatch.setattr(settings, "FITNESS_MANAGER_PASSWORD", "test-password")
    monkeypatch.setattr(settings, "FITNESS_MANAGER_API_TOKEN", "")
    monkeypatch.setattr(
        "app.services.unified_assistant.FitnessManagerClient",
        FitnessManagerStub,
    )

    result = asyncio.run(UnifiedAssistant().handle("show my workouts"))

    assert result["status"] == "success"
    assert result["intent"] == "fitness.workouts.read"
    assert result["data"] == [{"id": 7, "name": "Morning run"}]


def test_unified_assistant_still_requires_fitness_credentials(monkeypatch):
    monkeypatch.setattr(settings, "JARVIS_ENABLED_TOOLS", {"fitness.workouts.read"})
    monkeypatch.setattr(settings, "FITNESS_MANAGER_EMAIL", "")
    monkeypatch.setattr(settings, "FITNESS_MANAGER_PASSWORD", "")
    monkeypatch.setattr(settings, "FITNESS_MANAGER_API_TOKEN", "")

    result = asyncio.run(UnifiedAssistant().handle("show my workouts"))

    assert result["status"] == "authentication_required"
