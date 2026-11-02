"""Server-to-server HTTP adapter for the standalone Email Manager."""
from __future__ import annotations

import httpx

from app.config import settings


class EmailManagerClient:
    def __init__(self) -> None:
        self.base_url = settings.EMAIL_MANAGER_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(15.0)

    def _get_headers(self) -> dict[str, str]:
        if not settings.EMAIL_MANAGER_API_KEY:
            raise RuntimeError(
                "Email Manager API key is not configured. Set EMAIL_MANAGER_API_KEY "
                "in JARVIS and the matching API_KEY in Email Manager."
            )
        return {"X-API-Key": settings.EMAIL_MANAGER_API_KEY}

    async def health_check(self) -> dict:
        return await self._get("/healthz", authenticated=False)

    async def get_high_priority_emails(self) -> list | dict:
        return await self._get("/emails/high-priority")

    async def get_action_required_emails(self) -> list | dict:
        return await self._get("/emails/action-required")

    async def _get(self, endpoint: str, *, authenticated: bool = True) -> dict | list:
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers() if authenticated else {}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Email Manager returned HTTP {exc.response.status_code} for {endpoint}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Could not connect to Email Manager at {url}") from exc
