"""Phase 28: read-only email and calendar triage. No autonomous changes."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.security import require_jarvis_key
from app.integrations.email_manager import EmailManagerClient
from app.calendar.service import GoogleCalendarService
from app.api.email_assistant import _email_items, categorize_email

router = APIRouter(prefix="/intelligence", tags=["Email & Calendar Intelligence"],
                   dependencies=[Depends(require_jarvis_key)])


def _event_start(event: dict) -> datetime | None:
    start = event.get("start") or {}
    raw = start.get("dateTime") if isinstance(start, dict) else start if isinstance(start, str) and "T" in start else None
    if not raw:
        return None  # All-day events are returned but not assigned a time.
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt if dt.tzinfo else None
    except (ValueError, TypeError):
        return None


def summarize(email_payload, events, now: datetime, hours: int) -> dict:
    emails = _email_items(email_payload)
    labeled = [{**categorize_email(e), "subject": str(e.get("subject", ""))[:300],
                "sender": str(e.get("from") or e.get("sender") or "")[:300],
                "id": str(e.get("id", ""))[:200]} for e in emails[:100]]
    urgent = [e for e in labeled if e["suggested_priority"] == "high"]
    reply = [e for e in labeled if e["needs_reply"]]
    end = now + timedelta(hours=hours)
    upcoming = []
    for event in events[:250]:
        start = _event_start(event)
        if start and now <= start <= end:
            upcoming.append({"id": str(event.get("id", ""))[:200],
                             "summary": str(event.get("summary", "Untitled"))[:300],
                             "start_at": start.isoformat()})
    upcoming.sort(key=lambda e: e["start_at"])
    return {"window_hours": hours, "email_count": len(emails),
            "urgent_email_count": len(urgent), "reply_suggested_count": len(reply),
            "urgent_emails": urgent[:20], "reply_suggestions": reply[:20],
            "upcoming_event_count": len(upcoming), "upcoming_events": upcoming[:30],
            "suggestions": [
                *([f"Review {len(urgent)} potentially urgent email(s)."] if urgent else []),
                *([f"Review {len(reply)} email(s) that may need replies."] if reply else []),
                *([f"Prepare for {len(upcoming)} upcoming event(s)."] if upcoming else []),
            ],
            "read_only": True, "heuristic": True}


@router.get("/briefing")
async def intelligence_briefing(hours: int = Query(24, ge=1, le=168)):
    """Combine available sources without failing the entire briefing when one is offline."""
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=hours)
    async def email_read():
        return await EmailManagerClient().get_high_priority_emails()
    async def calendar_read():
        return await asyncio.to_thread(
            GoogleCalendarService().list_events,
            now.isoformat(), end.isoformat(), 250,
        )
    email_result, calendar_result = await asyncio.gather(
        email_read(), calendar_read(), return_exceptions=True
    )
    email_ok = not isinstance(email_result, BaseException)
    calendar_ok = not isinstance(calendar_result, BaseException)
    if not email_ok and not calendar_ok:
        raise HTTPException(status_code=503, detail="Both Email Manager and Calendar are unavailable.")
    events = calendar_result if calendar_ok and isinstance(calendar_result, list) else []
    result = summarize(email_result if email_ok else {}, events, now, hours)
    result["sources"] = {
        "email_manager": "connected" if email_ok else "unavailable",
        "calendar": "connected" if calendar_ok else "unavailable",
    }
    result["partial"] = not (email_ok and calendar_ok)
    result["note"] = "Only high-priority emails are requested. Suggestions are rules-based, not AI-verified. No emails are sent and no calendar events are changed."
    return result
