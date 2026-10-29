
import httpx

from app.config import settings


class FitnessManagerClient:
    def __init__(self) -> None:
        self.base_url = settings.FITNESS_MANAGER_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(10.0)

    async def health_check(self) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/health"
            )
            response.raise_for_status()
            return response.json()


    async def get_workouts(self, token: str) -> list:
        headers = {
            "Authorization": f"Bearer {token}"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/workouts",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
