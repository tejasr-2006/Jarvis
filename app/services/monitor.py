"""Low-risk background health monitor for connected JARVIS services."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any

from app.integrations.email_manager import EmailManagerClient
from app.integrations.fitness_manager import FitnessManagerClient
from app.config import settings

logger = logging.getLogger(__name__)


async def collect_service_status() -> dict[str, Any]:
    """Check only service health endpoints; never fetch personal records."""
    clients = {
        "email_manager": EmailManagerClient(),
        "fitness_manager": FitnessManagerClient(),
    }

    async def check(name: str, client: Any) -> tuple[str, dict[str, Any]]:
        try:
            await client.health_check()
            return name, {"status": "connected"}
        except Exception as exc:
            logger.info("Background health check failed for %s: %s", name, type(exc).__name__)
            return name, {"status": "unavailable"}

    checked = await asyncio.gather(*(check(name, client) for name, client in clients.items()))
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "services": dict(checked),
    }


async def monitoring_loop(stop_event: asyncio.Event, state: Any) -> None:
    """Refresh a small in-memory health snapshot until the app shuts down."""
    interval = max(15, min(int(settings.MONITOR_INTERVAL_SECONDS), 3600))
    while not stop_event.is_set():
        try:
            state.monitor_snapshot = await collect_service_status()
        except Exception:
            logger.exception("Background monitoring cycle failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
