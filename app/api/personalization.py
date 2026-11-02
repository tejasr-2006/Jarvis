"""Authenticated controls for optional adaptive personalization."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.security import require_jarvis_key
from app.tasks.store import TaskStore
from app.services.proactive_intelligence import ProactiveIntelligenceSettings
from app.services.adaptation_store import AdaptationStore
from app.services.adaptive_planning import personalized_plan

router = APIRouter(prefix="/personalization", tags=["Adaptive Personalization"],
                   dependencies=[Depends(require_jarvis_key)])


class PreferencesUpdate(BaseModel):
    enabled: bool | None = None
    focus_mode: str | None = Field(default=None, pattern="^(balanced|deadline_first|quick_wins|deep_work)$")
    default_available_minutes: int | None = Field(default=None, ge=15, le=960)
    prefer_deadline_first: bool | None = None
    collect_feedback: bool | None = None


class FeedbackRequest(BaseModel):
    task_id: int | None = Field(default=None, ge=1)
    event: str = Field(pattern="^(completed|deferred|dismissed|plan_accepted|plan_rejected)$")
    planned_minutes: int | None = Field(default=None, ge=1, le=960)
    actual_minutes: int | None = Field(default=None, ge=1, le=1440)
    priority: str | None = Field(default=None, pattern="^(low|normal|high)$")


class PersonalizedPlanRequest(BaseModel):
    available_minutes: int | None = Field(default=None, ge=15, le=960)
    focus_mode: str | None = Field(default=None, pattern="^(balanced|deadline_first|quick_wins|deep_work)$")
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


@router.get("/preferences")
def get_preferences():
    return {"preferences": AdaptationStore().preferences()}


@router.put("/preferences")
def update_preferences(body: PreferencesUpdate):
    values = {key: value for key, value in body.model_dump().items() if value is not None}
    saved = AdaptationStore().update_preferences(values)
    return {"status": "updated", "preferences": saved}


@router.post("/plan")
def adaptive_plan(body: PersonalizedPlanRequest):
    prefs = ProactiveIntelligenceSettings().get()
    tz = body.timezone or prefs.get("timezone", "Asia/Kolkata")
    tasks = TaskStore().list(status="pending", limit=200)
    return personalized_plan(tasks, body.available_minutes, body.focus_mode, tz,
                             body.duration_overrides)


@router.post("/feedback")
def add_feedback(body: FeedbackRequest):
    store = AdaptationStore()
    try:
        item = store.record_feedback(body.task_id, body.event, body.planned_minutes,
                                     body.actual_minutes, body.priority)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail="Feedback collection is disabled in preferences") from exc
    return {"status": "recorded", "feedback": item}


@router.get("/feedback")
def list_feedback(limit: int = 50):
    return {"feedback": AdaptationStore().list_feedback(max(1, min(limit, 200)))}


@router.delete("/feedback")
def clear_feedback():
    deleted = AdaptationStore().clear_feedback()
    return {"status": "cleared", "deleted": deleted}
