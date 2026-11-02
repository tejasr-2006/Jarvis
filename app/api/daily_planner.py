"""Personalized daily schedule assembled from local tasks and optional connected services.

This endpoint only reads data and returns a proposal. It does not create calendar events,
modify tasks, send email, or change workout records.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from app.calendar.service import CalendarNotConfigured, GoogleCalendarService
from app.integrations.email_manager import EmailManagerClient
from app.integrations.fitness_manager import FitnessManagerClient
from app.security import require_jarvis_key
from app.tasks.store import TaskStore

router = APIRouter(prefix="/daily-planner", tags=["Daily Planner"], dependencies=[Depends(require_jarvis_key)])
tasks_store = TaskStore()
calendar_service = GoogleCalendarService()


class RoutineBlock(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    start_time: str = Field(description="Local HH:MM time, e.g. 07:30")
    end_time: str = Field(description="Local HH:MM time, e.g. 08:00")

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Routine title cannot be blank")
        return value

    @field_validator("start_time", "end_time")
    @classmethod
    def valid_clock_time(cls, value: str) -> str:
        try:
            parsed = time.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Use 24-hour HH:MM time") from exc
        if parsed.second or parsed.microsecond or len(value) != 5:
            raise ValueError("Use 24-hour HH:MM time")
        return value

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("Routine end_time must be after start_time and within the same day")
        return self


class DailyPlanRequest(BaseModel):
    plan_date: date | None = None
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=80)
    workday_start: str = "09:00"
    workday_end: str = "18:00"
    break_minutes: int = Field(default=10, ge=0, le=60)
    max_tasks: int = Field(default=8, ge=1, le=30)
    routines: list[RoutineBlock] = Field(default_factory=list, max_length=20)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("timezone must be a valid IANA timezone, e.g. Asia/Kolkata") from exc
        return value

    @field_validator("workday_start", "workday_end")
    @classmethod
    def valid_clock_time(cls, value: str) -> str:
        try:
            parsed = time.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Use 24-hour HH:MM time") from exc
        if parsed.second or parsed.microsecond or len(value) != 5:
            raise ValueError("Use 24-hour HH:MM time")
        return value

    @model_validator(mode="after")
    def valid_workday(self):
        if self.workday_end <= self.workday_start:
            raise ValueError("workday_end must be after workday_start and within the same day")
        return self


def _dt(value: Any, tz: ZoneInfo) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(tz)
    except ValueError:
        return None


def _minutes_for_task(task: dict[str, Any]) -> int:
    text = f"{task.get('title', '')} {task.get('description', '')}".lower()
    if any(word in text for word in ("exam", "study", "revision", "assignment", "project", "report")):
        return 60
    if any(word in text for word in ("email", "reply", "call", "message")):
        return 20
    return 30


def build_schedule(day: date, tz: ZoneInfo, start_clock: str, end_clock: str,
                   fixed_blocks: list[dict[str, Any]], tasks: list[dict[str, Any]],
                   break_minutes: int, max_tasks: int) -> dict[str, Any]:
    """Place fixed blocks first, then priority-sorted tasks into available gaps."""
    start = datetime.combine(day, time.fromisoformat(start_clock), tzinfo=tz)
    end = datetime.combine(day, time.fromisoformat(end_clock), tzinfo=tz)
    blocks: list[dict[str, Any]] = []
    for block in fixed_blocks:
        bs, be = block.get("start_dt"), block.get("end_dt")
        if not isinstance(bs, datetime) or not isinstance(be, datetime) or be <= bs:
            continue
        # User-supplied routines can be outside working hours (e.g. morning exercise).
        # Calendar events are fetched only for the workday and are clipped to its bounds.
        if block.get("type") == "calendar_event":
            if be <= start or bs >= end:
                continue
            bs, be = max(bs, start), min(be, end)
        blocks.append({"title": block["title"], "type": block["type"], "start": bs.isoformat(), "end": be.isoformat(), "duration_minutes": int((be-bs).total_seconds() // 60), "source": block.get("source", "local")})
    blocks.sort(key=lambda b: b["start"])
    # Preserve all fixed blocks, but report overlaps rather than silently moving calendar events.
    conflicts = []
    for previous, current in zip(blocks, blocks[1:]):
        if datetime.fromisoformat(current["start"]) < datetime.fromisoformat(previous["end"]):
            conflicts.append({"first": previous["title"], "second": current["title"]})

    ordered_tasks = sorted(
        [t for t in tasks if t.get("status", "pending") == "pending"],
        key=lambda t: (0 if t.get("priority") == "high" else 1 if t.get("priority") == "normal" else 2,
                       t.get("due_at") is None, t.get("due_at") or "", t.get("id", 0)),
    )[:max_tasks]
    unscheduled = []
    cursor = start
    occupied = sorted([(datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])) for b in blocks])
    planned_tasks = []
    for task in ordered_tasks:
        duration = _minutes_for_task(task)
        candidate = cursor
        placed = False
        while candidate + timedelta(minutes=duration) <= end:
            overlap = next(((bs, be) for bs, be in occupied if candidate < be and candidate + timedelta(minutes=duration) > bs), None)
            if overlap:
                candidate = overlap[1] + timedelta(minutes=break_minutes)
                continue
            task_block = {"title": task.get("title", "Untitled task"), "type": "task", "priority": task.get("priority", "normal"), "task_id": task.get("id"), "start": candidate.isoformat(), "end": (candidate + timedelta(minutes=duration)).isoformat(), "duration_minutes": duration, "source": "tasks"}
            planned_tasks.append(task_block)
            occupied.append((candidate, candidate + timedelta(minutes=duration)))
            occupied.sort()
            cursor = candidate + timedelta(minutes=duration + break_minutes)
            placed = True
            break
        if not placed:
            unscheduled.append({"id": task.get("id"), "title": task.get("title", "Untitled task"), "priority": task.get("priority", "normal"), "reason": "No free slot remains within the selected workday"})
    combined = blocks + planned_tasks
    combined.sort(key=lambda b: b["start"])
    return {"date": day.isoformat(), "timezone": str(tz), "workday": {"start": start.isoformat(), "end": end.isoformat()}, "schedule": combined, "unscheduled_tasks": unscheduled, "fixed_block_conflicts": conflicts, "scheduled_task_count": len(planned_tasks)}


@router.post("/plan")
async def create_daily_plan(body: DailyPlanRequest):
    """Build a read-only daily schedule from tasks, calendar events, emails, workouts, and routines."""
    tz = ZoneInfo(body.timezone)
    local_today = datetime.now(tz).date()
    day = body.plan_date or local_today
    start = datetime.combine(day, time.fromisoformat(body.workday_start), tzinfo=tz)
    end = datetime.combine(day, time.fromisoformat(body.workday_end), tzinfo=tz)
    start_utc, end_utc = start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    # Local tasks are authoritative and always included.
    tasks = tasks_store.list(status="pending", limit=200)
    fixed_blocks: list[dict[str, Any]] = []
    for routine in body.routines:
        rs = datetime.combine(day, time.fromisoformat(routine.start_time), tzinfo=tz)
        re = datetime.combine(day, time.fromisoformat(routine.end_time), tzinfo=tz)
        fixed_blocks.append({"title": routine.title, "type": "routine", "start_dt": rs, "end_dt": re, "source": "request"})

    sources: dict[str, Any] = {"tasks": {"status": "available", "count": len(tasks)}, "calendar": {"status": "not_configured", "count": 0}, "email": {"status": "not_checked", "high_priority_count": None}, "fitness": {"status": "not_checked", "workout_count": None}}

    try:
        events = await asyncio.to_thread(calendar_service.list_events, start_utc.isoformat(), end_utc.isoformat(), 250)
        for event in events:
            es, ee = _dt(event.get("start"), tz), _dt(event.get("end"), tz)
            # All-day events are represented as dates; block that whole local day conservatively.
            if es is None and isinstance(event.get("start"), str):
                try:
                    es = datetime.combine(date.fromisoformat(event["start"]), time.min, tzinfo=tz)
                except ValueError:
                    pass
            if ee is None and isinstance(event.get("end"), str):
                try:
                    ee = datetime.combine(date.fromisoformat(event["end"]), time.min, tzinfo=tz)
                except ValueError:
                    pass
            if es and ee and ee > es:
                fixed_blocks.append({"title": event.get("summary") or "Calendar event", "type": "calendar_event", "start_dt": es, "end_dt": ee, "source": "google_calendar", "event_id": event.get("id")})
        sources["calendar"] = {"status": "connected", "count": len(events)}
    except CalendarNotConfigured:
        sources["calendar"] = {"status": "not_configured", "count": 0}
    except Exception:
        sources["calendar"] = {"status": "unavailable", "count": 0}

    # Optional integrations are read-only; their failure must not prevent the daily plan.
    try:
        emails = await EmailManagerClient().get_high_priority_emails()
        if isinstance(emails, dict):
            email_items = emails.get("emails", emails.get("data", []))
        else:
            email_items = emails
        count = len(email_items) if isinstance(email_items, list) else None
        sources["email"] = {"status": "connected", "high_priority_count": count, "items": email_items[:10] if isinstance(email_items, list) else []}
    except Exception:
        sources["email"] = {"status": "unavailable", "high_priority_count": None, "items": []}

    try:
        workouts = await FitnessManagerClient().get_workouts()
        workout_items = workouts if isinstance(workouts, list) else (workouts.get("workouts", []) if isinstance(workouts, dict) else [])
        sources["fitness"] = {"status": "connected", "workout_count": len(workout_items) if isinstance(workout_items, list) else None, "items": workout_items[:10] if isinstance(workout_items, list) else []}
    except Exception:
        sources["fitness"] = {"status": "unavailable", "workout_count": None, "items": []}

    result = build_schedule(day, tz, body.workday_start, body.workday_end, fixed_blocks, tasks, body.break_minutes, body.max_tasks)
    result["sources"] = sources
    result["notes"] = [
        "This is a proposed schedule; no tasks, emails, workouts, or calendar events were changed.",
        "Calendar, email, or fitness data may be unavailable if an integration is not configured or online.",
        "Routine blocks are supplied in this request and are not saved as recurring routines.",
    ]
    return result
