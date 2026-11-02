from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from app.security import require_jarvis_key
from app.reminders.store import ReminderStore

router = APIRouter(prefix="/reminders", tags=["Reminders"],
                   dependencies=[Depends(require_jarvis_key)])
store = ReminderStore()

class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_at: str = Field(min_length=10, max_length=40)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Reminder title cannot be blank")
        return value

    @field_validator("due_at")
    @classmethod
    def normalize_due_at(cls, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("due_at must be an ISO-8601 date/time with timezone") from exc
        if parsed.tzinfo is None:
            raise ValueError("due_at must include a timezone, e.g. +05:30 or Z")
        parsed = parsed.astimezone(timezone.utc)
        if parsed <= datetime.now(timezone.utc):
            raise ValueError("due_at must be in the future")
        return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")

@router.post("")
def create_reminder(body: ReminderCreate):
    return {"status": "scheduled", "reminder": store.create(body.title, body.due_at)}

@router.get("")
def list_reminders(status: str | None = Query(default=None, pattern="^(scheduled|fired|acknowledged)$"),
                   limit: int = Query(default=100, ge=1, le=200)):
    return {"reminders": store.list(status, limit)}

@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int):
    if not store.delete(reminder_id):
        raise HTTPException(status_code=404, detail="Scheduled reminder not found")
    return {"status": "deleted", "id": reminder_id}
