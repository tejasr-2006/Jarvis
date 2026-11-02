"""Authenticated memory APIs. Memory is local; no analytics/network calls here."""
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.config import settings
from app.security import require_jarvis_key
from app.memory.store import MemoryStore
from app.memory.context import relevant_memory_context
from app.conversation_context import ConversationContextStore

router = APIRouter(prefix="/memory", tags=["Memory"])
store = MemoryStore()


require_memory_key = require_jarvis_key

class FactCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=4000)
    category: str = Field(default="general", min_length=1, max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=20)


class FactUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=4000)
    category: str = Field(default="general", min_length=1, max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=20)


class ConversationCreate(BaseModel):
    user_message: str = Field(min_length=1, max_length=4000)
    assistant_message: str = Field(min_length=1, max_length=4000)


class MemoryPreferencesUpdate(BaseModel):
    context_enabled: bool | None = None
    cloud_context_enabled: bool | None = None
    conversation_storage_enabled: bool | None = None


class MemoryContextPreview(BaseModel):
    command: str = Field(min_length=1, max_length=2000)


class MemoryClearRequest(BaseModel):
    confirmation: str = Field(min_length=1, max_length=40)


@router.get("/status", dependencies=[Depends(require_memory_key)])
async def memory_status():
    return {
        "storage": "local_sqlite",
        "database_path": store.db_path,
        "conversation_storage_enabled": store.get_preferences()["conversation_storage_enabled"],
        "preferences": store.get_preferences(),
        "external_sync": False,
        "cloud_context_requires_opt_in": True,
        "raw_tool_payloads_saved": False,
    }


@router.get("/overview", dependencies=[Depends(require_memory_key)])
async def memory_overview():
    """Small control-center summary; never returns memory contents."""
    return {
        "storage": "local_sqlite",
        "counts": store.counts(),
        "preferences": store.get_preferences(),
        "cloud_context_default": bool(settings.MEMORY_CONTEXT_TO_CLOUD),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/preferences", dependencies=[Depends(require_memory_key)])
async def memory_preferences():
    return {"preferences": store.get_preferences()}


@router.put("/preferences", dependencies=[Depends(require_memory_key)])
async def update_memory_preferences(request: MemoryPreferencesUpdate):
    updates = request.model_dump(exclude_unset=True, exclude_none=True)
    if "cloud_context_enabled" in updates and updates["cloud_context_enabled"] is True:
        # This is a deliberate, explicit opt-in; no data is transmitted by this endpoint.
        pass
    return {"status": "saved_locally", "preferences": store.update_preferences(updates)}


@router.post("/context-preview", dependencies=[Depends(require_memory_key)])
async def preview_memory_context(request: MemoryContextPreview):
    """Preview the relevant saved facts JARVIS may use, without calling an AI provider."""
    preferences = store.get_preferences()
    if not preferences["context_enabled"]:
        return {"enabled": False, "items": [], "context": ""}
    context = relevant_memory_context(request.command, store)
    return {"enabled": True, "items": context.count("\n") + 1 if context else 0, "context": context}


@router.get("/export", dependencies=[Depends(require_memory_key)])
async def export_memory():
    """Export user-managed memory as JSON; caller decides where to save it."""
    return {
        "format": "jarvis-memory-export-v1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "preferences": store.get_preferences(),
        "facts": store.list_facts(limit=100000, offset=0),
        "saved_conversations": store.list_conversations(limit=100000, offset=0),
        "conversation_storage_included": True,
    }


@router.delete("/all", dependencies=[Depends(require_memory_key)])
async def clear_all_memory(request: MemoryClearRequest):
    """Irreversibly clear saved facts and conversation history after exact confirmation."""
    if request.confirmation != "CLEAR ALL MEMORY":
        raise HTTPException(status_code=400, detail='Confirmation must be exactly "CLEAR ALL MEMORY".')
    deleted_facts = store.delete_all_facts()
    deleted_conversations = store.delete_all_conversations()
    deleted_context_turns = ConversationContextStore().clear_all()
    return {
        "status": "cleared",
        "deleted": {
            "facts": deleted_facts,
            "saved_conversations": deleted_conversations,
            "conversation_context_turns": deleted_context_turns,
        },
    }


@router.post("/facts", dependencies=[Depends(require_memory_key)], status_code=201)
async def create_fact(request: FactCreate):
    return {"status": "stored_locally", "fact": store.create_fact(
        request.title, request.content, request.category, request.tags
    )}


@router.put("/facts/{fact_id}", dependencies=[Depends(require_memory_key)])
async def update_fact(fact_id: int, request: FactUpdate):
    if fact_id < 1:
        raise HTTPException(status_code=400, detail="Invalid memory ID")
    fact = store.update_fact(
        fact_id, request.title, request.content, request.category, request.tags
    )
    if fact is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "updated_locally", "fact": fact}


@router.get("/profile", dependencies=[Depends(require_memory_key)])
async def personal_profile():
    """Summarize explicitly saved preferences, goals, routines, and decisions."""
    items = store.list_facts(limit=200, offset=0)
    profile_categories = {"preference", "preferences", "goal", "goals", "routine", "routines", "decision", "decisions"}
    selected = [item for item in items if item["category"].lower() in profile_categories]
    grouped = {name: [] for name in ("preferences", "goals", "routines", "decisions")}
    category_map = {
        "preference": "preferences", "preferences": "preferences",
        "goal": "goals", "goals": "goals",
        "routine": "routines", "routines": "routines",
        "decision": "decisions", "decisions": "decisions",
    }
    for item in selected:
        grouped[category_map[item["category"].lower()]].append(item)
    return {"source": "explicitly_saved_local_memories", "count": len(selected), **grouped}


@router.get("/facts", dependencies=[Depends(require_memory_key)])
async def list_facts(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return {"items": store.list_facts(limit, offset), "limit": limit, "offset": offset}


@router.get("/search", dependencies=[Depends(require_memory_key)])
async def search_memory(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
):
    return {"query": q, "items": store.search_facts(q, limit)}


@router.delete("/facts/{fact_id}", dependencies=[Depends(require_memory_key)])
async def delete_fact(fact_id: int):
    if fact_id < 1:
        raise HTTPException(status_code=400, detail="Invalid memory ID")
    if not store.delete_fact(fact_id):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", "id": fact_id}


@router.delete("/facts", dependencies=[Depends(require_memory_key)])
async def delete_all_facts():
    return {"status": "deleted", "count": store.delete_all_facts()}


@router.post("/conversations", dependencies=[Depends(require_memory_key)], status_code=201)
async def save_conversation(request: ConversationCreate):
    if not store.get_preferences()["conversation_storage_enabled"]:
        raise HTTPException(
            status_code=403,
            detail="Conversation storage is disabled. Explicitly enable it at PUT /memory/preferences to opt in.",
        )
    return {"status": "stored_locally", "conversation": store.create_conversation(
        request.user_message, request.assistant_message
    )}


@router.get("/conversations", dependencies=[Depends(require_memory_key)])
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    # Turning storage off stops new writes but does not hide or delete existing history.
    return {"items": store.list_conversations(limit, offset), "limit": limit, "offset": offset}


@router.delete("/conversations", dependencies=[Depends(require_memory_key)])
async def delete_all_conversations():
    return {"status": "deleted", "count": store.delete_all_conversations()}
