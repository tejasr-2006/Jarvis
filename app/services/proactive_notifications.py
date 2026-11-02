"""Create one-time local alerts for due-soon and overdue tasks."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import logging
from typing import Any
from app.config import settings
from app.tasks.store import TaskStore
from app.reminders.notification_store import ProactiveNotificationStore

logger = logging.getLogger(__name__)


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def generate_task_notifications(
    tasks: list[dict[str, Any]],
    store: ProactiveNotificationStore,
    now: datetime | None = None,
    due_soon_minutes: int = 30,
) -> int:
    """Create deduplicated alerts; safe to call repeatedly from a scheduler."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    created = 0
    for task in tasks:
        if task.get("status") != "pending":
            continue
        due = _parse_utc(task.get("due_at"))
        if due is None:
            continue
        task_id = task.get("id")
        title = str(task.get("title") or "Untitled task")
        if due <= now:
            key = f"task:{task_id}:overdue"
            created += int(store.create_once(key, f"Overdue task: {title}",
                f"This task was due at {due.isoformat(timespec='minutes')}. Review it or update its due date.",
                "task_overdue", "tasks"))
        elif due <= now + timedelta(minutes=max(1, due_soon_minutes)):
            key = f"task:{task_id}:due_soon"
            created += int(store.create_once(key, f"Task due soon: {title}",
                f"This task is due at {due.isoformat(timespec='minutes')}.",
                "task_due_soon", "tasks"))
    return created


def run_proactive_notification_cycle() -> int:
    """Run one local-only cycle. Errors are logged and never stop the API."""
    try:
        tasks = TaskStore().list(status="pending", limit=200)
        store = ProactiveNotificationStore()
        return generate_task_notifications(
            tasks, store,
            due_soon_minutes=max(1, min(settings.NOTIFY_TASK_DUE_SOON_MINUTES, 1440)),
        )
    except Exception:
        logger.exception("Proactive notification cycle failed")
        return 0
