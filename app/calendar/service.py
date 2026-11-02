"""Optional Google Calendar adapter. Google credentials are stored locally, never in source."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar.events", "https://www.googleapis.com/auth/calendar.readonly"]

class CalendarNotConfigured(RuntimeError):
    pass

class GoogleCalendarService:
    def __init__(self, service: Any | None = None):
        self._service = service

    def _client(self):
        if self._service is not None:
            return self._service
        credentials_path = Path(settings.GOOGLE_CALENDAR_CREDENTIALS).expanduser()
        token_path = Path(settings.GOOGLE_CALENDAR_TOKEN).expanduser()
        if not credentials_path.is_file():
            raise CalendarNotConfigured("Google Calendar is not configured. Add an OAuth Desktop credentials JSON and run python -m app.calendar.auth.")
        if not token_path.is_file():
            raise CalendarNotConfigured("Google Calendar authorization is incomplete. Run python -m app.calendar.auth.")
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise CalendarNotConfigured("Install optional dependencies with: pip install -r requirements-calendar.txt") from exc
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json(), encoding="utf-8")
        if not creds.valid:
            raise CalendarNotConfigured("Google Calendar token is invalid. Re-run python -m app.calendar.auth.")
        self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return self._service

    @staticmethod
    def _parse(value: str) -> datetime:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("Datetime must include a timezone offset, e.g. 2026-10-29T09:00:00+05:30")
        return dt

    def status(self) -> dict[str, Any]:
        try:
            client = self._client()
            info = client.calendarList().get(calendarId=settings.GOOGLE_CALENDAR_ID).execute()
            return {"configured": True, "status": "connected", "calendar_id": settings.GOOGLE_CALENDAR_ID, "summary": info.get("summary", "")}
        except CalendarNotConfigured as exc:
            return {"configured": False, "status": "not_configured", "detail": str(exc)}
        except Exception:
            return {"configured": True, "status": "unavailable", "detail": "Could not verify Google Calendar. Check credentials and network access."}

    def list_events(self, time_min: str, time_max: str, limit: int = 100) -> list[dict[str, Any]]:
        start, end = self._parse(time_min), self._parse(time_max)
        if end <= start:
            raise ValueError("time_max must be after time_min")
        if (end - start).days > 31:
            raise ValueError("Calendar range cannot exceed 31 days")
        result = self._client().events().list(calendarId=settings.GOOGLE_CALENDAR_ID, timeMin=start.isoformat(), timeMax=end.isoformat(), maxResults=max(1, min(limit, 250)), singleEvents=True, orderBy="startTime").execute()
        return [self._normalize(e) for e in result.get("items", [])]

    @staticmethod
    def _normalize(event: dict[str, Any]) -> dict[str, Any]:
        return {"id": event.get("id"), "summary": event.get("summary", "(untitled)"), "description": event.get("description", ""), "start": event.get("start", {}).get("dateTime", event.get("start", {}).get("date")), "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date")), "html_link": event.get("htmlLink"), "status": event.get("status", "confirmed")}

    def create_event(self, summary: str, start_at: str, end_at: str, description: str = "", location: str = "", allow_conflicts: bool = False) -> dict[str, Any]:
        start, end = self._parse(start_at), self._parse(end_at)
        if end <= start:
            raise ValueError("end_at must be after start_at")
        existing = self.list_events(start.isoformat(), end.isoformat(), limit=100)
        conflicts = []
        for event in existing:
            try:
                es, ee = self._parse(event["start"]), self._parse(event["end"])
            except (ValueError, TypeError):
                # All-day events are conservatively treated as conflicts for their date.
                conflicts.append(event)
                continue
            if start < ee and end > es:
                conflicts.append(event)
        if conflicts and not allow_conflicts:
            return {"created": False, "conflict_detected": True, "conflicts": conflicts, "message": "Review the conflicts. To explicitly override, submit the request again with allow_conflicts=true."}
        body = {"summary": summary.strip(), "description": description.strip(), "location": location.strip(), "start": {"dateTime": start.isoformat()}, "end": {"dateTime": end.isoformat()}}
        created = self._client().events().insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=body).execute()
        return {"created": True, "conflict_detected": bool(conflicts), "event": self._normalize(created)}
