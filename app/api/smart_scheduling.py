"""Propose and confirm local schedules without touching external calendars."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from app.security import require_jarvis_key
from app.services.predictive_planning import rank_tasks
from app.services.proactive_intelligence import ProactiveIntelligenceSettings
from app.scheduling.store import ScheduleProposalStore
from app.scheduling.calendar_sync_store import CalendarSyncStore
from app.calendar.service import CalendarNotConfigured, GoogleCalendarService
from app.tasks.store import TaskStore

router = APIRouter(prefix="/smart-scheduling", tags=["Smart Scheduling"],
                   dependencies=[Depends(require_jarvis_key)])
store = ScheduleProposalStore()
sync_store = CalendarSyncStore()
calendar_service = GoogleCalendarService()


class ScheduleRequest(BaseModel):
    plan_date: date | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=80)
    workday_start: str = "09:00"
    workday_end: str = "18:00"
    break_minutes: int = Field(default=10, ge=0, le=60)
    max_tasks: int = Field(default=8, ge=1, le=30)
    focus_mode: str = Field(default="balanced", pattern="^(balanced|deadline_first|quick_wins|deep_work)$")
    duration_overrides: dict[int, int] = Field(default_factory=dict)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        if value is not None:
            try:
                ZoneInfo(value)
            except (ZoneInfoNotFoundError, ValueError) as exc:
                raise ValueError("timezone must be a valid IANA timezone") from exc
        return value

    @field_validator("workday_start", "workday_end")
    @classmethod
    def valid_clock(cls, value):
        try:
            parsed = time.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Use 24-hour HH:MM time") from exc
        if parsed.second or parsed.microsecond or len(value) != 5:
            raise ValueError("Use 24-hour HH:MM time")
        return value

    @field_validator("duration_overrides")
    @classmethod
    def valid_overrides(cls, value):
        if len(value) > 200 or any(k < 1 for k in value):
            raise ValueError("At most 200 positive task IDs may be overridden")
        if any(not isinstance(v, int) or v < 5 or v > 480 for v in value.values()):
            raise ValueError("Task duration overrides must be 5–480 minutes")
        return value

    @model_validator(mode="after")
    def validate_window(self):
        if self.workday_end <= self.workday_start:
            raise ValueError("workday_end must be later than workday_start")
        return self


class DecisionRequest(BaseModel):
    confirm: bool = True


def _build_schedule(body: ScheduleRequest, tasks: list[dict], timezone_name: str):
    zone = ZoneInfo(timezone_name)
    plan_date = body.plan_date or datetime.now(zone).date()
    start_clock = time.fromisoformat(body.workday_start)
    end_clock = time.fromisoformat(body.workday_end)
    start = datetime.combine(plan_date, start_clock, tzinfo=zone)
    end = datetime.combine(plan_date, end_clock, tzinfo=zone)
    now = datetime.now(zone)
    # If planning for today, do not propose time slots that have already passed.
    cursor = max(start, now) if plan_date == now.date() else start
    if cursor >= end:
        return {
            "plan_date": plan_date.isoformat(), "workday_start": start.isoformat(),
            "workday_end": end.isoformat(), "focus_mode": body.focus_mode,
            "scheduled_tasks": [], "deferred_tasks": [
                {"id": int(t.get("id", 0)), "title": str(t.get("title", "Untitled task")),
                 "estimated_minutes": body.duration_overrides.get(int(t.get("id", 0)), 30),
                 "reason": "Workday has ended in the selected timezone."}
                for t in tasks[:body.max_tasks]
            ], "planned_minutes": 0, "available_minutes": 0,
            "note": "Proposal only; no task status or calendar data was changed.",
        }
    ranked = rank_tasks(tasks, now, timezone_name, body.focus_mode, body.duration_overrides)
    available = max(0, int((end-cursor).total_seconds() // 60))
    scheduled, deferred = [], []
    remaining = available
    for item in ranked[:body.max_tasks]:
        duration = item["estimated_minutes"]
        if duration <= remaining:
            slot_start = cursor
            slot_end = slot_start + timedelta(minutes=duration)
            scheduled.append({
                **item, "start_at": slot_start.isoformat(timespec="minutes"),
                "end_at": slot_end.isoformat(timespec="minutes"),
                "date": plan_date.isoformat(),
            })
            remaining -= duration
            cursor = slot_end + timedelta(minutes=body.break_minutes)
            # Break time is accounted for between tasks, not after the final task.
            if len(scheduled) < min(len(ranked), body.max_tasks) and body.break_minutes:
                remaining = max(0, remaining - body.break_minutes)
        else:
            deferred.append({**item, "reason": "Estimated duration does not fit in the remaining workday."})
    deferred.extend({**item, "reason": "Outside the selected task limit."} for item in ranked[body.max_tasks:])
    planned = sum(item["estimated_minutes"] for item in scheduled)
    return {
        "plan_date": plan_date.isoformat(), "workday_start": start.isoformat(timespec="minutes"),
        "workday_end": end.isoformat(timespec="minutes"), "timezone": timezone_name,
        "focus_mode": body.focus_mode, "break_minutes": body.break_minutes,
        "available_minutes": available, "planned_minutes": planned,
        "scheduled_tasks": scheduled, "deferred_tasks": deferred,
        "note": "Proposal only. Confirming saves this local schedule proposal; it does not create calendar events or change task records.",
    }


@router.post("/proposals", status_code=201)
def propose_schedule(body: ScheduleRequest):
    prefs = ProactiveIntelligenceSettings().get()
    timezone_name = body.timezone or prefs.get("timezone", "Asia/Kolkata")
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Invalid planning timezone") from exc
    tasks = TaskStore().list(status="pending", limit=200)
    plan = _build_schedule(body, tasks, timezone_name)
    saved = store.create(plan["plan_date"], timezone_name, plan)
    return {
        "status": "pending_approval", "proposal": saved,
        "message": "Review the schedule and explicitly confirm or reject it. No calendar or task changes have occurred.",
    }


@router.get("/proposals")
def list_proposals(limit: int = 50):
    return {"proposals": store.list(limit)}


@router.get("/proposals/{proposal_id}")
def get_proposal(proposal_id: int):
    item = store.get(proposal_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule proposal not found")
    return {"proposal": item}


@router.post("/proposals/{proposal_id}/confirm")
def confirm_proposal(proposal_id: int, body: DecisionRequest):
    if not body.confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to confirm this local schedule")
    item = store.decide(proposal_id, "confirmed")
    if not item:
        existing = store.get(proposal_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Schedule proposal not found")
        raise HTTPException(status_code=409, detail=f"Schedule proposal is already {existing['status']}")
    return {"status": "confirmed", "proposal": item,
            "note": "Confirmed locally only; no external calendar event or task change was made."}


@router.post("/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: int):
    item = store.decide(proposal_id, "rejected")
    if not item:
        existing = store.get(proposal_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Schedule proposal not found")
        raise HTTPException(status_code=409, detail=f"Schedule proposal is already {existing['status']}")
    return {"status": "rejected", "proposal": item}



class CalendarSyncRequest(BaseModel):
    confirm: bool = False
    allow_conflicts: bool = False


def _schedule_slots(proposal):
    plan = proposal["plan"]
    slots = []
    for item in plan.get("scheduled_tasks", []):
        start_at, end_at = item.get("start_at"), item.get("end_at")
        if not start_at or not end_at:
            continue
        slots.append({
            "task_id": item.get("id"),
            "summary": str(item.get("title") or "JARVIS task")[:200],
            "start_at": start_at,
            "end_at": end_at,
            "description": f"Created from JARVIS schedule proposal #{proposal['id']}. Estimated duration: {item.get('estimated_minutes', 'unknown')} minutes.",
        })
    return slots


def _calendar_preview(proposal):
    slots = _schedule_slots(proposal)
    if not slots:
        return {"proposal_id": proposal["id"], "status": "no_events", "events_to_create": 0,
                "conflict_count": 0, "conflicts": [], "slots": [],
                "note": "No scheduled task slots were present; no calendar changes were made."}
    starts = [GoogleCalendarService._parse(slot["start_at"]) for slot in slots]
    ends = [GoogleCalendarService._parse(slot["end_at"]) for slot in slots]
    time_min = min(starts).isoformat()
    time_max = max(ends).isoformat()
    existing = calendar_service.list_events(time_min, time_max, limit=250)
    conflicts = []
    for slot in slots:
        slot_start = GoogleCalendarService._parse(slot["start_at"])
        slot_end = GoogleCalendarService._parse(slot["end_at"])
        overlaps = []
        for event in existing:
            try:
                raw_start, raw_end = event.get("start"), event.get("end")
                # All-day event dates are treated as occupied for their full local day.
                if isinstance(raw_start, str) and len(raw_start) == 10:
                    from datetime import date as date_type, datetime as datetime_type, time as time_type
                    event_start = datetime_type.combine(date_type.fromisoformat(raw_start), time_type.min, tzinfo=slot_start.tzinfo)
                    event_end = datetime_type.combine(date_type.fromisoformat(raw_end), time_type.min, tzinfo=slot_start.tzinfo)
                else:
                    event_start = GoogleCalendarService._parse(raw_start)
                    event_end = GoogleCalendarService._parse(raw_end)
            except (ValueError, TypeError):
                # Unknown event bounds are conservatively reported as a conflict.
                overlaps.append(event)
                continue
            if slot_start < event_end and slot_end > event_start:
                overlaps.append(event)
        if overlaps:
            conflicts.append({"slot": slot, "events": overlaps})
    return {
        "proposal_id": proposal["id"], "status": "conflicts_found" if conflicts else "clear",
        "events_to_create": len(slots), "conflict_count": len(conflicts),
        "conflicts": conflicts, "slots": slots,
        "calendar_id": "configured Google Calendar",
        "note": "Preview is read-only. Sync is blocked if conflicts exist unless allow_conflicts=true is explicitly confirmed.",
    }


@router.post("/proposals/{proposal_id}/calendar-preview")
def preview_calendar_sync(proposal_id: int):
    proposal = store.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Schedule proposal not found")
    if proposal["status"] != "confirmed":
        raise HTTPException(status_code=409, detail="Confirm the local schedule proposal before previewing calendar sync")
    prior = sync_store.get(proposal_id)
    if prior:
        return {"status": "already_attempted", "sync": prior,
                "note": "A calendar sync attempt already exists for this proposal; create a new proposal to avoid duplicate events."}
    try:
        return _calendar_preview(proposal)
    except CalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Schedule contains an invalid calendar time") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not inspect Google Calendar. No events were created.") from exc


@router.post("/proposals/{proposal_id}/calendar-sync")
def sync_schedule_to_calendar(proposal_id: int, body: CalendarSyncRequest):
    if not body.confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to explicitly approve creating Google Calendar events")
    proposal = store.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Schedule proposal not found")
    if proposal["status"] != "confirmed":
        raise HTTPException(status_code=409, detail="Confirm the local schedule proposal before syncing to Google Calendar")
    prior = sync_store.get(proposal_id)
    if prior:
        raise HTTPException(status_code=409, detail=f"Calendar sync already attempted with status {prior['status']}; create a new proposal to prevent duplicate events")
    try:
        preview = _calendar_preview(proposal)
    except CalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Schedule contains an invalid calendar time") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not check Google Calendar conflicts. No events were created.") from exc
    if preview["conflict_count"] and not body.allow_conflicts:
        raise HTTPException(status_code=409, detail={
            "message": "Calendar conflicts were found; no events were created.",
            "conflict_count": preview["conflict_count"],
            "conflicts": preview["conflicts"],
            "next_step": "Review the conflicts. If you deliberately want to proceed, retry with confirm=true and allow_conflicts=true.",
        })
    attempt = sync_store.begin(proposal_id)
    if not attempt:
        raise HTTPException(status_code=409, detail="A calendar sync attempt already exists for this proposal")
    created_ids, created_events, errors = [], [], []
    slots = preview["slots"]
    for index, slot in enumerate(slots):
        try:
            result = calendar_service.create_event(
                summary=slot["summary"], start_at=slot["start_at"], end_at=slot["end_at"],
                description=slot["description"], location="", allow_conflicts=body.allow_conflicts,
            )
            if not result.get("created"):
                errors.append({"slot": slot, "status": "conflict", "conflicts": result.get("conflicts", [])})
                break
            event = result.get("event") or {}
            event_id = event.get("id")
            if event_id:
                created_ids.append(str(event_id))
            created_events.append({"task_id": slot.get("task_id"), "event": event})
        except Exception as exc:
            errors.append({"slot": slot, "error_type": type(exc).__name__,
                           "message": "Calendar creation failed; inspect Google Calendar before retrying."})
            break
    if errors:
        state = "partial" if created_events else "failed"
    else:
        state = "synced"
    result_payload = {
        "proposal_id": proposal_id, "status": state, "created_count": len(created_events),
        "events": created_events, "errors": errors,
        "note": "Task records were not changed. Check Google Calendar for any events already created before taking further action.",
    }
    saved = sync_store.update(proposal_id, state, created_ids, result_payload)
    if errors:
        return {"status": state, "sync": saved,
                "warning": "This attempt will not be repeated automatically because calendar writes may have partially succeeded."}
    return {"status": "synced", "sync": saved}
