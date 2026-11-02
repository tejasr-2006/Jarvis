"""Authenticated, read-only predictive planning endpoints."""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.security import require_jarvis_key
from app.tasks.store import TaskStore
from app.services.proactive_intelligence import ProactiveIntelligenceSettings
from app.services.predictive_planning import build_day_plan, rank_tasks

router = APIRouter(prefix="/predictive-planning", tags=["Predictive Planning"],
                   dependencies=[Depends(require_jarvis_key)])


class DayPlanRequest(BaseModel):
    available_minutes: int = Field(default=120, ge=15, le=960)
    focus_mode: str = Field(default="balanced", pattern="^(balanced|deadline_first|quick_wins|deep_work)$")
    timezone: str | None = Field(default=None, min_length=1, max_length=80)
    duration_overrides: dict[int, int] = Field(default_factory=dict)

    @field_validator("duration_overrides")
    @classmethod
    def validate_durations(cls, value):
        if len(value) > 200:
            raise ValueError("at most 200 task duration overrides are allowed")
        if any(task_id < 1 for task_id in value):
            raise ValueError("task IDs must be positive")
        if any(minutes < 5 or minutes > 480 for minutes in value.values()):
            raise ValueError("task durations must be between 5 and 480 minutes")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value):
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return value


def _context(timezone_name: str | None):
    prefs = ProactiveIntelligenceSettings().get()
    tz = timezone_name or prefs.get("timezone", "Asia/Kolkata")
    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Invalid planning timezone") from exc
    tasks = TaskStore().list(status="pending", limit=200)
    return tasks, tz


@router.get("/recommendations")
def recommendations(focus_mode: str = "balanced", timezone: str | None = None):
    if focus_mode not in {"balanced", "deadline_first", "quick_wins", "deep_work"}:
        raise HTTPException(status_code=422, detail="Unsupported focus_mode")
    tasks, tz = _context(timezone)
    ranked = rank_tasks(tasks, datetime.now().astimezone(), tz, focus_mode)
    return {
        "status": "available",
        "focus_mode": focus_mode,
        "count": len(ranked),
        "recommendations": ranked,
        "note": "Rule-based ranking from priority and due dates; not a guarantee of task completion.",
    }


@router.post("/day-plan")
def day_plan(body: DayPlanRequest):
    tasks, tz = _context(body.timezone)
    return build_day_plan(
        tasks=tasks,
        available_minutes=body.available_minutes,
        now=datetime.now().astimezone(),
        timezone_name=tz,
        focus_mode=body.focus_mode,
        duration_overrides=body.duration_overrides,
    )
