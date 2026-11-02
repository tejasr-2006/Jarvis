"""Authenticated configuration and manual controls for background agents."""
from __future__ import annotations

from datetime import datetime
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.security import require_jarvis_key
from app.services.background_agents import (
    BackgroundAgentStore, run_background_local_cycle, run_email_monitor_cycle,
)

router = APIRouter(prefix="/background-agents", tags=["Background Agents"],
                   dependencies=[Depends(require_jarvis_key)])


class BackgroundAgentPreferences(BaseModel):
    enabled: bool = True
    task_monitor_enabled: bool = True
    email_monitor_enabled: bool = False
    email_monitor_interval_seconds: int = Field(default=300, ge=60, le=86400)
    daily_briefing_time: str = Field(default="08:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")


@router.get("/status")
def status():
    store = BackgroundAgentStore()
    prefs = store.preferences()
    return {
        "status": "enabled" if prefs["enabled"] else "disabled",
        "preferences": prefs,
        "checkpoints": {
            "daily_briefing_date": store.checkpoint("daily_briefing_date"),
            "email_high_priority_count": store.checkpoint("email_high_priority_count"),
        },
        "safety": {
            "external_mutations": False,
            "email_monitor_stores_message_content": False,
            "notifications": "in-app only",
        },
    }


@router.put("/settings")
def update_settings(body: BackgroundAgentPreferences):
    saved = BackgroundAgentStore().update_preferences(body.model_dump())
    return {"status": "updated", "preferences": saved}


@router.post("/run")
async def run_now():
    store = BackgroundAgentStore()
    local_result = await __import__("asyncio").to_thread(run_background_local_cycle, store)
    email_result = await run_email_monitor_cycle(store)
    return {"status": "completed", "local_agents": local_result,
            "email_monitor": email_result,
            "note": "Only read-only checks and in-app notifications ran. No external messages were sent."}
