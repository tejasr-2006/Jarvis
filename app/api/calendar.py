from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from app.security import require_jarvis_key
from app.calendar.service import GoogleCalendarService, CalendarNotConfigured

router = APIRouter(prefix="/calendar", tags=["Calendar"], dependencies=[Depends(require_jarvis_key)])
service = GoogleCalendarService()

class EventCreate(BaseModel):
    summary: str = Field(min_length=1, max_length=200)
    start_at: str = Field(description="ISO-8601 datetime with timezone offset")
    end_at: str = Field(description="ISO-8601 datetime with timezone offset")
    description: str = Field(default="", max_length=4000)
    location: str = Field(default="", max_length=500)
    allow_conflicts: bool = False

    @field_validator("start_at", "end_at")
    @classmethod
    def timezone_required(cls, value: str) -> str:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Use ISO-8601 datetime format") from exc
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("Datetime must include a timezone offset")
        return value

@router.get("/status")
def calendar_status():
    return service.status()

@router.get("/events")
def calendar_events(time_min: str = Query(...), time_max: str = Query(...), limit: int = Query(100, ge=1, le=250)):
    try:
        events = service.list_events(time_min, time_max, limit)
        return {"count": len(events), "events": events}
    except CalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Google Calendar request failed. Check configuration and connectivity.") from exc

@router.post("/events")
def create_calendar_event(payload: EventCreate):
    try:
        result = service.create_event(**payload.model_dump())
        if result.get("conflict_detected") and not result.get("created"):
            return result
        return result
    except CalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not create calendar event. Check Google Calendar configuration.") from exc
