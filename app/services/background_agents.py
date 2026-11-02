"""Permission-safe background agents for JARVIS.

Agents only read local task/routine state and, when explicitly enabled, the
Email Manager's high-priority count. They create in-app notifications only.
They never send messages or mutate external services.
"""
from __future__ import annotations

import hashlib
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings
from app.reminders.notification_store import ProactiveNotificationStore
from app.services.proactive_intelligence import (
    ProactiveIntelligenceSettings, in_quiet_hours, run_intelligence_cycle,
)
from app.services.proactive_notifications import run_proactive_notification_cycle
from app.routines_store import RoutineStore
from app.integrations.email_manager import EmailManagerClient

logger = logging.getLogger(__name__)


class BackgroundAgentStore:
    """Persistent preferences and checkpoints for background agents."""

    DEFAULTS = {
        "enabled": "true",
        "task_monitor_enabled": "true",
        "email_monitor_enabled": "false",
        "email_monitor_interval_seconds": "300",
        "daily_briefing_time": "08:00",
    }

    def __init__(self, db_path: str | None = None):
        folder = Path(settings.JARVIS_DATA_DIR).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or str(folder / "background_agents.db")
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS checkpoints (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")

    def preferences(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            values = dict(conn.execute("SELECT key,value FROM preferences").fetchall())
        result = dict(self.DEFAULTS)
        result.update(values)
        result["enabled"] = result["enabled"] == "true"
        result["task_monitor_enabled"] = result["task_monitor_enabled"] == "true"
        result["email_monitor_enabled"] = result["email_monitor_enabled"] == "true"
        result["email_monitor_interval_seconds"] = int(result["email_monitor_interval_seconds"])
        return result

    def update_preferences(self, values: dict[str, Any]) -> dict[str, Any]:
        normalized = []
        for key, value in values.items():
            if key not in self.DEFAULTS:
                raise ValueError(f"Unsupported background-agent setting: {key}")
            normalized.append((key, str(value).lower() if isinstance(value, bool) else str(value)))
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.executemany(
                "INSERT INTO preferences(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value", normalized
            )
        return self.preferences()

    def checkpoint(self, key: str) -> str | None:
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            row = conn.execute("SELECT value FROM checkpoints WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def set_checkpoint(self, key: str, value: str) -> None:
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute(
                "INSERT INTO checkpoints(key,value,updated_at) VALUES(?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
                (key, value),
            )


def _record_count(payload: Any) -> int:
    """Count email records without retaining message bodies or subjects."""
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("emails", "items", "results", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
        count = payload.get("count", payload.get("total"))
        if isinstance(count, int) and count >= 0:
            return count
    raise ValueError("Email Manager returned an unsupported high-priority response")


async def run_email_monitor_cycle(
    store: BackgroundAgentStore | None = None,
    client: Any | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    store = store or BackgroundAgentStore()
    prefs = store.preferences()
    if not prefs["enabled"] or not prefs["email_monitor_enabled"]:
        return {"status": "disabled"}
    proactive = ProactiveIntelligenceSettings().get()
    current = now or datetime.now().astimezone()
    local_now = current.astimezone(ZoneInfo(proactive["timezone"]))
    if in_quiet_hours(local_now, proactive["quiet_start"], proactive["quiet_end"]):
        return {"status": "quiet_hours"}
    try:
        client = client or EmailManagerClient()
        payload = await client.get_high_priority_emails()
        count = _record_count(payload)
        previous = store.checkpoint("email_high_priority_count")
        store.set_checkpoint("email_high_priority_count", str(count))
        if previous is None:
            return {"status": "baseline_saved", "high_priority_count": count}
        old_count = int(previous)
        if count > old_count:
            digest = hashlib.sha256(f"{local_now.date()}:{old_count}:{count}".encode()).hexdigest()[:16]
            ProactiveNotificationStore().create_once(
                f"email:high_priority:{digest}",
                f"{count - old_count} new high-priority email(s)",
                f"Your high-priority email count increased from {old_count} to {count}. Review your inbox.",
                "email_priority", "email_monitor",
            )
        return {"status": "checked", "high_priority_count": count, "previous_count": old_count}
    except Exception as exc:
        logger.warning("Email background monitor failed: %s", type(exc).__name__)
        return {"status": "unavailable", "reason": type(exc).__name__}


def fire_due_routines(now: datetime | None = None) -> int:
    current = now or datetime.now().astimezone()
    routines = RoutineStore()
    notifications = ProactiveNotificationStore()
    fired = 0
    for routine in routines.due(current):
        local_date = current.date().isoformat()
        event_key = f"routine:{routine['id']}:{local_date}"
        notifications.create_once(
            event_key=event_key,
            title=f"Routine: {routine['name']}",
            message=routine["message"],
            kind="routine",
            source=f"routine:{routine['id']}",
        )
        if routines.mark_fired(routine["id"], local_date):
            fired += 1
    return fired


def _run_due_routines(now: datetime | None = None) -> int:
    """Backward-compatible alias for the shared local routine scheduler."""
    return fire_due_routines(now)


def run_daily_briefing_if_due(
    store: BackgroundAgentStore | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    store = store or BackgroundAgentStore()
    prefs = store.preferences()
    if not prefs["enabled"]:
        return {"status": "disabled"}
    proactive = ProactiveIntelligenceSettings().get()
    current = now or datetime.now().astimezone()
    local_now = current.astimezone(ZoneInfo(proactive["timezone"]))
    if in_quiet_hours(local_now, proactive["quiet_start"], proactive["quiet_end"]):
        return {"status": "quiet_hours"}
    target_hour, target_minute = map(int, prefs["daily_briefing_time"].split(":"))
    if (local_now.hour, local_now.minute) < (target_hour, target_minute):
        return {"status": "not_due"}
    day_key = local_now.date().isoformat()
    if store.checkpoint("daily_briefing_date") == day_key:
        return {"status": "already_run"}
    result = run_intelligence_cycle(current)
    if result.get("status") == "completed":
        store.set_checkpoint("daily_briefing_date", day_key)
    return {"status": result.get("status", "not_completed"), "created": result.get("created", 0)}


def run_background_local_cycle(
    store: BackgroundAgentStore | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run local read-only monitors; external email polling is async and separate."""
    store = store or BackgroundAgentStore()
    prefs = store.preferences()
    if not prefs["enabled"]:
        return {"status": "disabled"}
    results: dict[str, Any] = {}
    if prefs["task_monitor_enabled"]:
        results["task_notifications_created"] = run_proactive_notification_cycle()
        try:
            results["routines_fired"] = fire_due_routines(now)
        except Exception:
            logger.exception("Routine background agent failed")
            results["routines_fired"] = 0
    results["daily_briefing"] = run_daily_briefing_if_due(store, now)
    return {"status": "completed", "agents": results}
