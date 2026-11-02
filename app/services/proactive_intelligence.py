"""Local, deduplicated proactive insights; never performs external mutations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings
from app.tasks.store import TaskStore
from app.routines_store import RoutineStore
from app.reminders.notification_store import ProactiveNotificationStore


def _due(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            return None
        return result.astimezone(timezone.utc)
    except ValueError:
        return None


def in_quiet_hours(now: datetime, start: str, end: str) -> bool:
    """Supports normal and overnight quiet-hour windows; equal means disabled."""
    clock = now.strftime("%H:%M")
    if start == end:
        return False
    if start < end:
        return start <= clock < end
    return clock >= start or clock < end


def build_insights(tasks: list[dict[str, Any]], now: datetime | None = None,
                   timezone_name: str = "Asia/Kolkata") -> dict[str, Any]:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    local_now = current.astimezone(ZoneInfo(timezone_name))
    today = local_now.date()
    pending = [t for t in tasks if t.get("status") == "pending"]
    overdue, due_today, high_priority = [], [], []
    for task in pending:
        due = _due(task.get("due_at"))
        if due:
            local_due = due.astimezone(ZoneInfo(timezone_name))
            if due < current.astimezone(timezone.utc):
                overdue.append(task)
            elif local_due.date() == today:
                due_today.append(task)
        if task.get("priority") == "high":
            high_priority.append(task)
    insights: list[dict[str, Any]] = []
    if overdue:
        insights.append({"kind": "overdue_summary", "priority": "high", "title": f"Review {len(overdue)} overdue task{'s' if len(overdue) != 1 else ''}", "message": "Choose what to finish first, or update due dates that are no longer realistic.", "task_ids": [t.get("id") for t in overdue]})
    if due_today:
        insights.append({"kind": "due_today_summary", "priority": "high", "title": f"{len(due_today)} task{'s' if len(due_today) != 1 else ''} due today", "message": "Review today's deadlines and reserve time for the most important task.", "task_ids": [t.get("id") for t in due_today]})
    if len(high_priority) >= 3:
        insights.append({"kind": "high_priority_load", "priority": "normal", "title": "Several high-priority tasks are pending", "message": f"There are {len(high_priority)} high-priority tasks. Pick one next action instead of trying to tackle all at once.", "task_ids": [t.get("id") for t in high_priority]})
    if not pending:
        insights.append({"kind": "clear_tasks", "priority": "low", "title": "Your task list is clear", "message": "No pending tasks are currently recorded in JARVIS.", "task_ids": []})
    return {"generated_at": local_now.isoformat(timespec="seconds"), "timezone": timezone_name,
            "summary": {"pending": len(pending), "overdue": len(overdue), "due_today": len(due_today), "high_priority": len(high_priority)},
            "insights": insights}


def run_intelligence_cycle(now: datetime | None = None) -> dict[str, Any]:
    """Create one daily briefing notification and deduplicated insight alerts."""
    config = ProactiveIntelligenceSettings()
    prefs = config.get()
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    local_now = current.astimezone(ZoneInfo(prefs["timezone"]))
    if not prefs["enabled"]:
        return {"status": "disabled", "created": 0, "reason": "Proactive intelligence is disabled"}
    if in_quiet_hours(local_now, prefs["quiet_start"], prefs["quiet_end"]):
        return {"status": "quiet_hours", "created": 0, "reason": "Notifications are paused during quiet hours"}
    tasks = TaskStore().list(status="pending", limit=200)
    result = build_insights(tasks, current, prefs["timezone"])
    notification_store = ProactiveNotificationStore()
    date_key = local_now.date().isoformat()
    summary = result["summary"]
    created = 0
    if summary["pending"]:
        message = (f"{summary['pending']} pending; {summary['overdue']} overdue; "
                   f"{summary['due_today']} due today; {summary['high_priority']} high priority.")
        created += int(notification_store.create_once(
            f"proactive:daily_briefing:{date_key}", "Your JARVIS daily briefing", message,
            "daily_briefing", "proactive_intelligence"))
    for insight in result["insights"]:
        if insight["kind"] == "clear_tasks":
            continue
        created += int(notification_store.create_once(
            f"proactive:insight:{date_key}:{insight['kind']}", insight["title"], insight["message"],
            "proactive_insight", "proactive_intelligence"))
    return {"status": "completed", "created": created, **result}


class ProactiveIntelligenceSettings:
    """Small local SQLite preference store; values are validated by the API schema."""
    def __init__(self, db_path: str | None = None):
        import sqlite3
        from pathlib import Path
        folder = Path(settings.JARVIS_DATA_DIR).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or str(folder / "proactive_intelligence.db")
        self._sqlite3 = sqlite3
        with self._sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

    def get(self) -> dict[str, Any]:
        with self._sqlite3.connect(self.db_path, timeout=10) as conn:
            rows = dict(conn.execute("SELECT key,value FROM preferences").fetchall())
        return {"enabled": rows.get("enabled", "true") == "true",
                "quiet_start": rows.get("quiet_start", "22:00"),
                "quiet_end": rows.get("quiet_end", "07:00"),
                "timezone": rows.get("timezone", "Asia/Kolkata")}

    def update(self, values: dict[str, Any]) -> dict[str, Any]:
        with self._sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.executemany("INSERT INTO preferences(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                             [(key, str(value).lower() if isinstance(value, bool) else str(value)) for key, value in values.items()])
        return self.get()
