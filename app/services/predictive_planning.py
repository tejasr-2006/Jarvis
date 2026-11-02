"""Deterministic, explainable task prioritization and time-budget planning."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

PRIORITY_SCORE = {"high": 30, "normal": 20, "low": 10}
DEFAULT_MINUTES = {"high": 45, "normal": 30, "low": 20}


def _parse_due(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def rank_tasks(
    tasks: list[dict[str, Any]],
    now: datetime | None = None,
    timezone_name: str = "Asia/Kolkata",
    focus_mode: str = "balanced",
    duration_overrides: dict[int, int] | None = None,
) -> list[dict[str, Any]]:
    """Rank pending tasks. Reasons are rule-based, not model predictions."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    local_today = current.astimezone(ZoneInfo(timezone_name)).date()
    overrides = duration_overrides or {}
    ranked = []
    for task in tasks:
        if task.get("status", "pending") != "pending":
            continue
        priority = task.get("priority", "normal")
        if priority not in PRIORITY_SCORE:
            priority = "normal"
        task_id = int(task.get("id", 0))
        minutes = int(overrides.get(task_id, DEFAULT_MINUTES[priority]))
        due = _parse_due(task.get("due_at"))
        score = PRIORITY_SCORE[priority]
        reasons = [f"{priority.title()} priority"]
        due_bucket = "unscheduled"
        if due is not None:
            local_due = due.astimezone(ZoneInfo(timezone_name))
            if due < current:
                score += 100
                due_bucket = "overdue"
                reasons.insert(0, "Overdue")
            elif local_due.date() == local_today:
                score += 70
                due_bucket = "due_today"
                reasons.insert(0, "Due today")
            else:
                hours = (due - current).total_seconds() / 3600
                if hours <= 48:
                    score += 45
                    due_bucket = "due_soon"
                    reasons.insert(0, "Due within 48 hours")
                else:
                    due_bucket = "scheduled"
        if focus_mode == "deadline_first" and due is not None:
            score += max(0, 48 - min(48, int((due-current).total_seconds()/3600)))
        elif focus_mode == "quick_wins":
            score += max(0, 40 - minutes)
        elif focus_mode == "deep_work":
            score += 15 if priority == "high" else 0
        ranked.append({
            "id": task_id,
            "title": str(task.get("title", "Untitled task")),
            "priority": priority,
            "due_at": task.get("due_at"),
            "estimated_minutes": minutes,
            "score": score,
            "due_bucket": due_bucket,
            "reasons": reasons,
        })
    # Stable tie-breaking: score, due date, priority, then id.
    ranked.sort(key=lambda item: (
        -item["score"],
        _parse_due(item["due_at"]) or datetime.max.replace(tzinfo=timezone.utc),
        item["id"],
    ))
    return ranked


def build_day_plan(
    tasks: list[dict[str, Any]],
    available_minutes: int = 120,
    now: datetime | None = None,
    timezone_name: str = "Asia/Kolkata",
    focus_mode: str = "balanced",
    duration_overrides: dict[int, int] | None = None,
) -> dict[str, Any]:
    ranked = rank_tasks(tasks, now, timezone_name, focus_mode, duration_overrides)
    remaining = available_minutes
    scheduled = []
    deferred = []
    for task in ranked:
        if task["estimated_minutes"] <= remaining:
            scheduled.append({**task, "start_after_minutes": available_minutes - remaining})
            remaining -= task["estimated_minutes"]
        else:
            deferred.append(task)
    return {
        "status": "proposal",
        "available_minutes": available_minutes,
        "planned_minutes": available_minutes - remaining,
        "unused_minutes": remaining,
        "focus_mode": focus_mode,
        "duration_estimation": "Heuristic defaults by priority (high 45m, normal 30m, low 20m); per-task overrides are accepted.",
        "scheduled_tasks": scheduled,
        "deferred_tasks": deferred,
        "note": "This is a read-only proposal. JARVIS has not changed task status or created calendar events.",
    }
