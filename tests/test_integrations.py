import asyncio

import httpx

from app.config import settings
from app.integrations.fitness_manager import FitnessManagerClient
from app.integrations.home_assistant import HomeAssistantClient


class FakeFitnessHTTPClient:
    def __init__(self):
        self.login_count = 0
        self.workout_headers = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, url, *, json):
        self.login_count += 1
        return httpx.Response(
            200,
            json={"access_token": f"fitness-token-{self.login_count}"},
            request=httpx.Request("POST", url),
        )

    async def get(self, url, *, headers):
        self.workout_headers.append(headers)
        status_code = 401 if len(self.workout_headers) == 1 else 200
        return httpx.Response(
            status_code,
            json=[],
            request=httpx.Request("GET", url),
        )


def test_fitness_manager_uses_bearer_token_and_refreshes_after_unauthorized(monkeypatch):
    fake_client = FakeFitnessHTTPClient()
    monkeypatch.setattr(settings, "FITNESS_MANAGER_EMAIL", "user@example.test")
    monkeypatch.setattr(settings, "FITNESS_MANAGER_PASSWORD", "test-password")
    monkeypatch.setattr(
        "app.integrations.fitness_manager.httpx.AsyncClient",
        lambda **kwargs: fake_client,
    )
    client = FitnessManagerClient()

    workouts = asyncio.run(client.get_workouts())

    assert workouts == []
    assert fake_client.login_count == 2
    assert fake_client.workout_headers == [
        {"Authorization": "Bearer fitness-token-1"},
        {"Authorization": "Bearer fitness-token-2"},
    ]


def test_home_assistant_uses_bearer_token():
    client = HomeAssistantClient(
        base_url="http://home-assistant.test",
        token="home-assistant-token",
    )

    assert client._headers() == {
        "Authorization": "Bearer home-assistant-token",
        "Content-Type": "application/json",
    }
