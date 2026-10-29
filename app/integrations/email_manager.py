
import httpx
from app.config import settings


class EmailManagerClient:
    def __init__(self):
        self.base_url = settings.EMAIL_MANAGER_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(10.0)

    def _get_headers(self) -> dict:
        return {
            "X-API-Key": settings.EMAIL_MANAGER_API_KEY
        }

    async def health_check(self) -> dict:
        return await self._get("/healthz")

    async def get_high_priority_emails(self) -> dict:
        return await self._get("/emails/high-priority")

    async def _get(self, endpoint: str) -> dict:
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Email Manager returned HTTP "
                f"{exc.response.status_code}: "
                f"{exc.response.text}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Could not connect to Email Manager at {url}: {exc}"
            ) from exc
