"""Unified natural-language command endpoint."""
from fastapi import APIRouter, Depends, HTTPException
import re
import uuid
from pydantic import BaseModel, Field
from app.security import require_jarvis_key
from app.services.unified_assistant import UnifiedAssistant
from app.conversation_context import ConversationContextStore
from app.config import settings

router = APIRouter(prefix="/assistant", tags=["Unified Assistant"],
                   dependencies=[Depends(require_jarvis_key)])


class UnifiedCommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")


@router.get("/capabilities")
def capabilities():
    from app.services.unified_assistant import HELP
    return {"assistant": "JARVIS", "mode": "safe_read_only_dispatch",
            "capabilities": HELP,
            "note": "Commands that change data or devices are not executed through this endpoint."}


def _resolve_followup(command: str, recent: list[dict]) -> tuple[str, dict | None]:
    """Resolve only obvious elliptical follow-ups; never fabricate unsupported filters."""
    normalized = re.sub(r"\s+", " ", command.lower()).strip()
    if not recent:
        return command, None
    last = recent[-1]
    intent = last.get("intent", "unknown")
    temporal = re.search(r"\b(yesterday|today|last week|this week|last month|earlier|before)\b", normalized)
    elliptical = normalized in {
        "what about that", "what about it", "and that", "what about yesterday",
        "what about today", "and yesterday", "and today", "what about last week",
        "what about this week", "tell me more", "more details", "why", "how about that",
    }
    if temporal and intent in {"tasks.list", "routines.list", "notifications.list",
                              "email.high_priority.read", "fitness.workouts.read",
                              "calendar.status", "home_assistant.states"}:
        topic = {
            "tasks.list": "tasks", "routines.list": "routines",
            "notifications.list": "notifications and reminders",
            "email.high_priority.read": "high-priority emails",
            "fitness.workouts.read": "workouts", "calendar.status": "Google Calendar",
            "home_assistant.states": "smart-home devices",
        }[intent]
        return command, {
            "kind": "unsupported_temporal_filter", "topic": topic,
            "message": f"I understand you're asking about {topic} for that time period, but this command currently doesn't support historical date filtering. I haven't assumed or changed any data.",
        }
    if elliptical:
        if intent == "fitness.workouts.read":
            return "show my workouts", None
        if intent == "email.high_priority.read":
            return "show high priority emails", None
        if intent == "tasks.list":
            return "show my tasks", None
        if intent == "routines.list":
            return "show my routines", None
        if intent == "notifications.list":
            return "check notifications", None
        if intent == "home_assistant.states":
            return "show smart home devices", None
        if intent == "calendar.status":
            return "check calendar status", None
    # A follow-up that names a different module but omits the verb inherits the
    # last read verb only when that intent is known; no action is inferred.
    if re.fullmatch(r"(?:and )?(tasks|routines|notifications|reminders|emails|inbox|workouts|fitness|calendar|smart home|devices)(?:\?)?", normalized):
        mapping = {
            "tasks": "show my tasks", "routines": "show my routines",
            "notifications": "check notifications", "reminders": "show reminders",
            "emails": "show high priority emails", "inbox": "check my inbox",
            "workouts": "show my workouts", "fitness": "check fitness",
            "calendar": "check calendar status", "smart home": "show smart home devices",
            "devices": "show smart home devices",
        }
        return mapping[normalized.removeprefix("and ").removesuffix("?")], None
    return command, None


@router.post("/command")
async def unified_command(request: UnifiedCommandRequest):
    command = request.command.strip()
    if not command:
        raise HTTPException(status_code=422, detail="Command cannot be blank")
    if not settings.CONVERSATION_CONTEXT_ENABLED:
        session_id = request.session_id or uuid.uuid4().hex
        try:
            result = await UnifiedAssistant().handle(command)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Unified assistant failed to process the command") from exc
        return {**result, "session_id": session_id, "context_used": False,
                "context_note": "Conversation context is disabled in JARVIS settings."}

    session_id = request.session_id or uuid.uuid4().hex
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", session_id):
        raise HTTPException(status_code=422, detail="session_id must be 8-80 letters, numbers, underscores, or hyphens")
    store = ConversationContextStore()
    recent = store.recent(session_id)
    resolved_command, context_notice = _resolve_followup(command, recent)
    try:
        if context_notice:
            result = {"status": "context_limit", "intent": "followup.unsupported",
                      "message": context_notice["message"], "topic": context_notice["topic"]}
        else:
            result = await UnifiedAssistant().handle(resolved_command)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unified assistant failed to process the command") from exc

    intent = str(result.get("intent", "unknown"))
    status_value = str(result.get("status", "unknown"))
    summary = str(result.get("message", result.get("intent", "Command processed.")))
    store.add_turn(session_id, command, intent, status_value, summary)
    return {
        **result,
        "session_id": session_id,
        "context_used": bool(recent),
        "context": [{"command": item["user_command"], "intent": item["intent"],
                     "status": item["status"]} for item in recent[-4:]],
        "resolved_command": resolved_command if resolved_command != command else None,
        "context_note": "JARVIS stores recent command text and brief status summaries locally; tool result payloads are not stored.",
    }


@router.get("/context/{session_id}")
def get_context(session_id: str):
    if not settings.CONVERSATION_CONTEXT_ENABLED:
        return {"session_id": session_id, "enabled": False, "turns": []}
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", session_id):
        raise HTTPException(status_code=422, detail="Invalid session_id")
    return {"session_id": session_id, "enabled": True,
            "turns": ConversationContextStore().recent(session_id)}


@router.delete("/context/{session_id}")
def clear_context(session_id: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", session_id):
        raise HTTPException(status_code=422, detail="Invalid session_id")
    count = ConversationContextStore().clear(session_id)
    return {"status": "cleared", "session_id": session_id, "deleted_turns": count}


# Phase 3: LLM-driven tool planning and safe multi-tool execution.
from app.agent.orchestrator import AgentOrchestrator, AgentPlanningError
from app.agent.traces import AgentTraceStore
from app.services.tool_registry import AGENT_TOOL_REGISTRY
from app.services.ai_service import AIServiceError
from fastapi.concurrency import run_in_threadpool


class AgentChatRequest(BaseModel):
    command: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, min_length=8, max_length=80,
                                   pattern=r"^[a-zA-Z0-9_-]+$")
    max_tool_calls: int = Field(default=4, ge=1, le=5)


@router.post("/agent/chat")
async def agent_chat(request: AgentChatRequest):
    """Plan with the configured AI provider, execute allow-listed read tools, synthesize."""
    try:
        return await AgentOrchestrator(AGENT_TOOL_REGISTRY).run(
            request.command, session_id=request.session_id,
            max_tool_calls=request.max_tool_calls,
        )
    except AgentPlanningError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail="JARVIS AI provider is unavailable") from exc
    except ValueError as exc:
        # Includes missing provider configuration and invalid request-level settings.
        message = str(exc)
        status_code = 503 if "missing" in message.lower() or "not installed" in message.lower() else 422
        raise HTTPException(status_code=status_code, detail=message) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="JARVIS agent orchestration failed") from exc


@router.get("/agent/traces")
def agent_traces(limit: int = 20):
    """Return recent metadata-only traces; raw email/fitness payloads are not persisted."""
    return {"traces": AgentTraceStore().recent(limit)}
