"""Optional, tightly allow-listed Home Assistant REST API client."""
from __future__ import annotations

import httpx
from app.config import settings


class HomeAssistantNotConfigured(RuntimeError):
    pass


class HomeAssistantClient:
    """Only exposes state reads and explicitly allow-listed device actions."""

    ALLOWED_ACTIONS = {
        "turn_on": {"light": "turn_on", "switch": "turn_on", "fan": "turn_on"},
        "turn_off": {"light": "turn_off", "switch": "turn_off", "fan": "turn_off"},
        "toggle": {"light": "toggle", "switch": "toggle", "fan": "toggle"},
    }

    def __init__(self, base_url: str | None = None, token: str | None = None,
                 allowed_entities: set[str] | None = None, timeout: float = 8.0):
        self.base_url = (settings.HOME_ASSISTANT_BASE_URL if base_url is None else base_url).strip().rstrip("/")
        self.token = settings.HOME_ASSISTANT_TOKEN if token is None else token
        self.allowed_entities = (
            settings.HOME_ASSISTANT_ALLOWED_ENTITIES if allowed_entities is None else allowed_entities
        )
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.token)

    def _require_configured(self) -> None:
        if not self.configured:
            raise HomeAssistantNotConfigured("Home Assistant is not configured")

    def _headers(self) -> dict[str, str]:
        self._require_configured()
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    async def health(self) -> dict:
        self._require_configured()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/", headers=self._headers())
            response.raise_for_status()
            data = response.json()
        return {"status": "connected", "message": str(data.get("message", "API available"))[:160]}

    async def list_allowed_states(self) -> list[dict]:
        self._require_configured()
        if not self.allowed_entities:
            return []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/states", headers=self._headers())
            response.raise_for_status()
            states = response.json()
        result = []
        for item in states:
            entity_id = item.get("entity_id")
            if entity_id in self.allowed_entities:
                result.append({
                    "entity_id": entity_id,
                    "state": str(item.get("state", "unknown"))[:80],
                    "friendly_name": str(item.get("attributes", {}).get("friendly_name", entity_id))[:120],
                })
        return result

    def validate_action(self, entity_id: str, action: str) -> tuple[str, str]:
        if entity_id not in self.allowed_entities:
            raise ValueError("This entity is not in HOME_ASSISTANT_ALLOWED_ENTITIES")
        if "." not in entity_id:
            raise ValueError("Invalid Home Assistant entity ID")
        domain = entity_id.split(".", 1)[0]
        service = self.ALLOWED_ACTIONS.get(action, {}).get(domain)
        if not service:
            raise ValueError("Unsupported action for this entity domain")
        return domain, service

    async def execute_action(self, entity_id: str, action: str) -> dict:
        """Execute only after the API layer has checked explicit confirmation."""
        self._require_configured()
        domain, service = self.validate_action(entity_id, action)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                headers=self._headers(),
                json={"entity_id": entity_id},
            )
            response.raise_for_status()
            payload = response.json()
        # Do not return raw upstream response, which may contain excess device metadata.
        return {
            "status": "submitted",
            "entity_id": entity_id,
            "action": action,
            "service": f"{domain}.{service}",
            "affected_count": len(payload) if isinstance(payload, list) else None,
        }
