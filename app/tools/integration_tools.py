"""Trusted handlers for local knowledge and standalone integration services."""
import asyncio
from datetime import datetime, timezone
from typing import Any

from app.integrations.email_manager import EmailManagerClient
from app.integrations.fitness_manager import FitnessManagerClient
from app.knowledge.store import KnowledgeStore


_email_client = EmailManagerClient()
_fitness_client = FitnessManagerClient()
_knowledge_store = KnowledgeStore()


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Search time filters must be ISO 8601 timestamps") from exc
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


async def read_high_priority_emails() -> list | dict:
    return await _email_client.get_high_priority_emails()


async def read_workouts() -> list:
    return await _fitness_client.get_workouts()


async def search_knowledge(
    query: str,
    limit: int = 10,
    source: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("Search query cannot be blank")
    after = _parse_datetime(updated_after)
    before = _parse_datetime(updated_before)
    if after is not None and before is not None and after > before:
        raise ValueError("updated_after must be earlier than or equal to updated_before")
    return await asyncio.to_thread(
        _knowledge_store.search,
        query,
        limit,
        source=source,
        updated_after=after,
        updated_before=before,
    )
