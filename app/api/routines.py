"""Authenticated API for safe, notification-based daily routines."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from app.security import require_jarvis_key
from app.routines_store import RoutineStore

router = APIRouter(prefix="/routines", tags=["Routines"],
                   dependencies=[Depends(require_jarvis_key)])


class RoutineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=1000)
    time_local: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    weekdays: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6], min_length=1, max_length=7)

    @field_validator("name", "message")
    @classmethod
    def no_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank")
        return value.strip()

    @field_validator("weekdays")
    @classmethod
    def valid_unique_weekdays(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("Weekdays use 0=Monday through 6=Sunday")
        if len(set(value)) != len(value):
            raise ValueError("Weekdays must be unique")
        return sorted(value)


class RoutineEnabled(BaseModel):
    enabled: bool


@router.get("")
def list_routines(include_disabled: bool = Query(default=True)):
    return {"routines": RoutineStore().list(include_disabled=include_disabled)}


@router.post("", status_code=201)
def create_routine(request: RoutineCreate):
    routine = RoutineStore().create(request.name, request.message, request.time_local, request.weekdays)
    return {"status": "created", "routine": routine}


@router.patch("/{routine_id}")
def set_routine_enabled(routine_id: int, request: RoutineEnabled):
    routine = RoutineStore().set_enabled(routine_id, request.enabled)
    if routine is None:
        raise HTTPException(status_code=404, detail="Routine not found")
    return {"status": "updated", "routine": routine}


@router.delete("/{routine_id}")
def delete_routine(routine_id: int):
    if not RoutineStore().delete(routine_id):
        raise HTTPException(status_code=404, detail="Routine not found")
    return {"status": "deleted", "id": routine_id}
