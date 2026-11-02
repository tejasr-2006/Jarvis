"""Authenticated unified JARVIS dashboard data aggregator."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query

from app.security import require_jarvis_key
from app.tasks.store import TaskStore
from app.reminders.store import ReminderStore
from app.reminders.notification_store import ProactiveNotificationStore
from app.routines_store import RoutineStore
from app.finance.store import FinanceStore
from app.integrations.email_manager import EmailManagerClient
from app.integrations.fitness_manager import FitnessManagerClient
from app.calendar.service import GoogleCalendarService

router = APIRouter(prefix="/dashboard", tags=["Unified Dashboard"],
                   dependencies=[Depends(require_jarvis_key)])


def _safe_local_data(month: str):
    now = datetime.now(timezone.utc)
    tasks = TaskStore().list(limit=200)
    pending = [t for t in tasks if t.get("status") == "pending"]
    reminders = ReminderStore().list(limit=100)
    notifications = ProactiveNotificationStore().list_unacknowledged(limit=50)
    routines = RoutineStore().list(include_disabled=False)
    finance = FinanceStore().summary(month, "INR")
    due_today = overdue = 0
    for task in pending:
        raw = task.get("due_at")
        if not raw:
            continue
        try:
            due = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if due.tzinfo is None:
                continue
            due = due.astimezone(timezone.utc)
            if due.date() == now.date():
                due_today += 1
            elif due < now:
                overdue += 1
        except ValueError:
            continue
    return {
        "tasks": {"total": len(tasks), "pending": len(pending),
                  "completed": sum(1 for t in tasks if t.get("status") == "completed"),
                  "due_today": due_today, "overdue": overdue, "items": pending[:10]},
        "reminders": {"scheduled_count": sum(1 for r in reminders if r.get("status") == "scheduled"),
                      "items": reminders[:10]},
        "notifications": {"unacknowledged_count": len(notifications), "items": notifications[:10]},
        "routines": {"enabled_count": len(routines), "items": routines[:10]},
        "finance": finance,
    }


@router.get("/overview")
async def dashboard_overview(month: str = Query(default_factory=lambda: date.today().strftime("%Y-%m"),
                                                pattern=r"^\d{4}-(0[1-9]|1[0-2])$")):
    """Read-only overview; each remote integration can fail independently."""
    local = await asyncio.to_thread(_safe_local_data, month)
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=7)

    async def email_check():
        return await EmailManagerClient().get_high_priority_emails()

    async def fitness_check():
        return await FitnessManagerClient().get_workouts()

    async def calendar_check():
        return await asyncio.to_thread(GoogleCalendarService().list_events,
                                       now.isoformat(), end.isoformat(), 250)

    results = await asyncio.gather(email_check(), fitness_check(), calendar_check(),
                                   return_exceptions=True)
    email_result, fitness_result, calendar_result = results

    def is_ok(value):
        return not isinstance(value, BaseException)

    if is_ok(email_result):
        payload = email_result
        if isinstance(payload, list):
            emails = payload
        elif isinstance(payload, dict):
            emails = next((payload[k] for k in ("emails", "items", "data", "results") if isinstance(payload.get(k), list)), [])
        else:
            emails = []
        email_data = {"status": "connected", "high_priority_count": len(emails),
                      "items": [{"subject": str(e.get("subject", ""))[:200],
                                 "sender": str(e.get("from") or e.get("sender") or "")[:200],
                                 "id": str(e.get("id", ""))[:160]} for e in emails[:8] if isinstance(e, dict)]}
    else:
        email_data = {"status": "unavailable", "high_priority_count": None, "items": []}

    if is_ok(fitness_result):
        if isinstance(fitness_result, list):
            workouts = fitness_result
        elif isinstance(fitness_result, dict):
            workouts = next((fitness_result[k] for k in ("workouts", "items", "data", "results") if isinstance(fitness_result.get(k), list)), [])
        else:
            workouts = []
        fitness_data = {"status": "connected", "workout_count": len(workouts),
                        "recent_workouts": workouts[:5]}
    else:
        fitness_data = {"status": "unavailable", "workout_count": None, "recent_workouts": []}

    if is_ok(calendar_result):
        events = calendar_result if isinstance(calendar_result, list) else []
        calendar_data = {"status": "connected", "upcoming_count": len(events),
                         "events": events[:10]}
    else:
        calendar_data = {"status": "unavailable", "upcoming_count": None, "events": []}

    connected = sum(1 for section in (email_data, fitness_data, calendar_data) if section["status"] == "connected")
    return {
        "status": "available" if connected == 3 else "partial",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "month": month,
        "summary": {
            "pending_tasks": local["tasks"]["pending"],
            "overdue_tasks": local["tasks"]["overdue"],
            "due_today_tasks": local["tasks"]["due_today"],
            "unacknowledged_notifications": local["notifications"]["unacknowledged_count"],
            "high_priority_emails": email_data["high_priority_count"],
            "upcoming_calendar_events": calendar_data["upcoming_count"],
            "workouts_returned": fitness_data["workout_count"],
            "monthly_expenses_inr": local["finance"]["expenses"],
            "monthly_net_inr": local["finance"]["net"],
        },
        **local,
        "email": email_data,
        "fitness": fitness_data,
        "calendar": calendar_data,
        "integrations": {
            "email_manager": email_data["status"],
            "fitness_manager": fitness_data["status"],
            "google_calendar": calendar_data["status"],
            "connected_remote_sources": connected,
            "remote_source_count": 3,
        },
        "read_only": True,
        "note": "Unified overview only. It does not send email, create or edit calendar events, change tasks, or perform financial transactions. Finance is a manual local ledger; fitness data comes from the configured Fitness Manager.",
    }
