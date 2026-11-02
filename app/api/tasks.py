from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from app.security import require_jarvis_key
from app.tasks.store import TaskStore

router = APIRouter(prefix="/tasks", tags=["Tasks"], dependencies=[Depends(require_jarvis_key)])
store = TaskStore()

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: str = "normal"
    due_at: str | None = Field(default=None, max_length=40)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Task title cannot be blank")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"low", "normal", "high"}:
            raise ValueError("priority must be low, normal, or high")
        return value

    @field_validator("due_at")
    @classmethod
    def normalize_due_at(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("due_at must be an ISO-8601 date/time with timezone") from exc
        if parsed.tzinfo is None:
            raise ValueError("due_at must include a timezone, e.g. +05:30 or Z")
        return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

@router.post("")
def create_task(body: TaskCreate):
    task = store.create(body.title, body.description, body.priority, body.due_at)
    return {"status": "created", "task": task}

@router.get("")
def list_tasks(status: str | None = Query(default=None, pattern="^(pending|completed)$"), limit: int = Query(default=100, ge=1, le=200)):
    return {"tasks": store.list(status, limit)}

@router.post("/{task_id}/complete")
def complete_task(task_id: int):
    task = store.complete(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": task["status"], "task": task}

@router.delete("/{task_id}")
def delete_task(task_id: int):
    if not store.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted", "id": task_id}
