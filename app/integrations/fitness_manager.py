"""Authenticated HTTP adapter for the standalone Fitness Manager service."""
from __future__ import annotations

import asyncio
import time

import httpx

from app.config import settings


class FitnessManagerClient:
    """Uses the Fitness Manager's own login endpoint; credentials stay server-side.

    The token is cached briefly (five minutes) and refreshed once after a 401.
    This deliberately refreshes well before the service's configured expiry.
    """

    def __init__(self) -> None:
        self.base_url = settings.FITNESS_MANAGER_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(15.0)
        self._access_token: str | None = None
        self._token_cached_at = 0.0
        self._token_lock = asyncio.Lock()
        self._token_cache_seconds = 300

    async def health_check(self) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

    async def _login(self, client: httpx.AsyncClient, *, force: bool = False) -> str:
        if not settings.FITNESS_MANAGER_EMAIL or not settings.FITNESS_MANAGER_PASSWORD:
            raise RuntimeError(
                "Fitness Manager login is not configured. Set FITNESS_MANAGER_EMAIL "
                "and FITNESS_MANAGER_PASSWORD in the JARVIS environment."
            )

        async with self._token_lock:
            token_is_fresh = (
                self._access_token
                and time.monotonic() - self._token_cached_at < self._token_cache_seconds
            )
            if token_is_fresh and not force:
                return self._access_token  # type: ignore[return-value]

            try:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json={
                        "email": settings.FITNESS_MANAGER_EMAIL,
                        "password": settings.FITNESS_MANAGER_PASSWORD,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                token = payload.get("access_token") if isinstance(payload, dict) else None
                if not isinstance(token, str) or not token:
                    raise RuntimeError("Fitness Manager login returned no access token")
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"Fitness Manager login failed with HTTP {exc.response.status_code}"
                ) from exc
            except httpx.RequestError as exc:
                raise RuntimeError("Could not connect to Fitness Manager login endpoint") from exc

            self._access_token = token
            self._token_cached_at = time.monotonic()
            return token

    async def get_workouts(self, token: str | None = None) -> list:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Optional static token remains for backwards compatibility; new setups
            # should use the dedicated service login credentials.
            token = token or await self._login(client)
            response = await client.get(
                f"{self.base_url}/workouts",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 401:
                token = await self._login(client, force=True)
                response = await client.get(
                    f"{self.base_url}/workouts",
                    headers={"Authorization": f"Bearer {token}"},
                )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"Fitness Manager returned HTTP {exc.response.status_code} for workouts"
                ) from exc
            data = response.json()
            if not isinstance(data, list):
                raise RuntimeError("Fitness Manager returned an unexpected workouts response")
            return data
