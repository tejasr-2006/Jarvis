"""Permission-controlled computer action endpoints."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.security import require_jarvis_key
from app.computer.service import ALLOWED_APPS, validate_action, execute_action
from app.computer.store import ComputerActionStore

router = APIRouter(prefix="/computer", tags=["Computer Control"], dependencies=[Depends(require_jarvis_key)])

class ActionProposal(BaseModel):
    action_type: Literal["open_url", "launch_app"]
    target: str = Field(min_length=1, max_length=2048)

class ExecuteConfirmation(BaseModel):
    confirm: bool = False

@router.get("/capabilities")
async def capabilities():
    return {
        "supported_actions": [
            {"action_type": "open_url", "description": "Open a validated HTTP(S) URL in the default browser"},
            {"action_type": "launch_app", "description": "Launch one of the allow-listed desktop applications"},
        ],
        "allowed_apps": [{"name": name, "description": description} for name, description in ALLOWED_APPS.items()],
        "safety": "No shell commands, arbitrary executables, keystroke injection, or unattended actions are supported.",
    }

@router.post("/actions/propose", status_code=201)
async def propose_action(request: ActionProposal):
    try:
        action_type, target = validate_action(request.action_type, request.target)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    action = ComputerActionStore().create(action_type, target)
    action["approval_required"] = True
    action["instructions"] = "Review the action, then call /computer/actions/{id}/execute with {confirm: true} to run it."
    return action

@router.get("/actions")
async def list_actions(limit: int = 50):
    return {"actions": ComputerActionStore().list(limit)}

@router.get("/actions/{action_id}")
async def get_action(action_id: str):
    action = ComputerActionStore().get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found.")
    return action

@router.post("/actions/{action_id}/execute")
async def execute_proposed_action(action_id: str, request: ExecuteConfirmation):
    store = ComputerActionStore()
    action = store.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found.")
    if action["status"] != "proposed":
        raise HTTPException(status_code=409, detail=f"Action cannot be executed from status '{action['status']}'.")
    if request.confirm is not True:
        raise HTTPException(status_code=400, detail="Explicit confirmation is required.")
    try:
        result = execute_action(action["action_type"], action["target"])
    except (ValueError, RuntimeError) as exc:
        store.update(action_id, "failed", {"error": str(exc)})
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    updated = store.update(action_id, "executed", result)
    return updated
