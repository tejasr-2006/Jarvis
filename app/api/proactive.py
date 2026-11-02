"""Authenticated controls and read-only insight preview for proactive intelligence."""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.security import require_jarvis_key
from app.tasks.store import TaskStore
from app.reminders.store import ReminderStore
from app.reminders.notification_store import ProactiveNotificationStore
from app.services.proactive_intelligence import in_quiet_hours
from app.services.proactive_intelligence import (
    ProactiveIntelligenceSettings, build_insights, run_intelligence_cycle,
)

router = APIRouter(prefix="/proactive", tags=["Proactive Intelligence"], dependencies=[Depends(require_jarvis_key)])


class ProactivePreferences(BaseModel):
    enabled: bool = True
    quiet_start: str = Field(default="22:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    quiet_end: str = Field(default="07:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=80)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("timezone must be a valid IANA timezone, e.g. Asia/Kolkata") from exc
        return value


@router.get("/settings")
def get_preferences():
    return {"settings": ProactiveIntelligenceSettings().get()}


@router.put("/settings")
def update_preferences(body: ProactivePreferences):
    saved = ProactiveIntelligenceSettings().update(body.model_dump())
    return {"status": "updated", "settings": saved}


@router.get("/insights")
def get_insights():
    prefs = ProactiveIntelligenceSettings().get()
    if not prefs["enabled"]:
        return {"status": "disabled", "summary": {}, "insights": []}
    tasks = TaskStore().list(status="pending", limit=200)
    return {"status": "available", **build_insights(tasks, datetime.now().astimezone(), prefs["timezone"])}


@router.get("/briefing")
def proactive_briefing():
    """Build a concise local daily briefing from current tasks, reminders and alerts."""
    prefs = ProactiveIntelligenceSettings().get()
    now = datetime.now().astimezone()
    try:
        zone = ZoneInfo(prefs["timezone"])
        local_now = now.astimezone(zone)
        quiet = in_quiet_hours(local_now, prefs["quiet_start"], prefs["quiet_end"])
        tasks = TaskStore().list(limit=200)
        pending = [item for item in tasks if item.get("status") == "pending"]
        insights = build_insights(pending, now, prefs["timezone"])
        reminders = ReminderStore().list(status="scheduled", limit=100)
        fired_reminders = ReminderStore().list(status="fired", limit=100)
        alerts = ProactiveNotificationStore().list_unacknowledged(limit=50)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise HTTPException(status_code=422, detail="Invalid proactive intelligence timezone") from exc

    def due_value(item):
        raw = item.get("due_at")
        if not isinstance(raw, str):
            return ""
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed.isoformat() if parsed.tzinfo else raw
        except ValueError:
            return raw

    due_soon = []
    overdue = []
    for task in pending:
        due = due_value(task)
        if not due:
            continue
        try:
            parsed = datetime.fromisoformat(due.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                continue
            if parsed.astimezone().date() < local_now.date() or parsed < now:
                overdue.append(task)
            elif parsed.astimezone(zone).date() == local_now.date():
                due_soon.append(task)
        except ValueError:
            continue

    suggestions = []
    for insight in insights["insights"]:
        suggestions.append({
            "priority": insight["priority"],
            "title": insight["title"],
            "message": insight["message"],
            "kind": insight["kind"],
        })
    if alerts:
        suggestions.append({
            "priority": "normal",
            "title": f"{len(alerts)} notification(s) need review",
            "message": "Review and acknowledge the existing in-app alerts when appropriate.",
            "kind": "unacknowledged_notifications",
        })

    return {
        "status": "available" if prefs["enabled"] else "disabled",
        "generated_at": local_now.isoformat(timespec="seconds"),
        "timezone": prefs["timezone"],
        "quiet_hours": {"active": quiet, "start": prefs["quiet_start"], "end": prefs["quiet_end"]},
        "preferences": prefs,
        "summary": {
            "pending_tasks": len(pending),
            "overdue_tasks": insights["summary"]["overdue"],
            "due_today_tasks": insights["summary"]["due_today"],
            "high_priority_tasks": insights["summary"]["high_priority"],
            "scheduled_reminders": len(reminders),
            "fired_reminders": len(fired_reminders),
            "unacknowledged_notifications": len(alerts),
        },
        "top_tasks": pending[:8],
        "insights": insights["insights"],
        "suggestions": suggestions,
        "reminders": reminders[:10],
        "notifications": alerts[:10],
        "read_only": True,
        "note": "This briefing is assembled from local JARVIS data. Running the proactive cycle separately may create deduplicated in-app notifications; it does not send external messages or modify tasks.",
    }


@router.post("/run")
def run_now():
    """Evaluate now; creates local in-app notifications only, no external actions."""
    try:
        return run_intelligence_cycle()
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise HTTPException(status_code=422, detail="Invalid proactive intelligence timezone") from exc
