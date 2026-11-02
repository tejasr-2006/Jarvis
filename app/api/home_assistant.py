"""Phase 18 Home Assistant endpoints; every route requires the JARVIS API key."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import httpx

from app.security import require_jarvis_key
from app.integrations.home_assistant import (
    HomeAssistantClient, HomeAssistantNotConfigured
)

router = APIRouter(
    prefix="/integrations/home-assistant",
    tags=["Home Assistant"],
    dependencies=[Depends(require_jarvis_key)],
)


class DeviceActionRequest(BaseModel):
    entity_id: str = Field(min_length=3, max_length=128, pattern=r"^[a-z_]+\.[a-z0-9_]+$")
    action: str = Field(pattern=r"^(turn_on|turn_off|toggle)$")
    confirm: bool = False


@router.get("/health")
async def home_assistant_health():
    client = HomeAssistantClient()
    if not client.configured:
        return {"status": "not_configured", "configured": False}
    try:
        return {"status": "connected", "configured": True, "connection": await client.health()}
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Home Assistant is unavailable") from exc
    except HomeAssistantNotConfigured:
        return {"status": "not_configured", "configured": False}


@router.get("/states")
async def home_assistant_states():
    """Return state only for entities explicitly named in the allow-list."""
    client = HomeAssistantClient()
    if not client.configured:
        raise HTTPException(status_code=503, detail="Home Assistant is not configured")
    try:
        states = await client.list_allowed_states()
        return {"status": "success", "count": len(states), "entities": states}
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not retrieve Home Assistant states") from exc


@router.post("/action")
async def home_assistant_action(request: DeviceActionRequest):
    """Require an explicit confirm=true request and an allow-listed entity/action."""
    client = HomeAssistantClient()
    if not client.configured:
        raise HTTPException(status_code=503, detail="Home Assistant is not configured")
    try:
        domain, service = client.validate_action(request.entity_id, request.action)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if not request.confirm:
        return {
            "status": "confirmation_required",
            "message": "Review this proposed device action and submit it again with confirm=true.",
            "proposal": {
                "entity_id": request.entity_id,
                "action": request.action,
                "service": f"{domain}.{service}",
            },
        }

    try:
        result = await client.execute_action(request.entity_id, request.action)
        return {"status": "success", "result": result}
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Home Assistant action failed") from exc
