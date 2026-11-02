"""Backward-compatible tool metadata and trusted agent tool handlers."""
from dataclasses import dataclass
from app.config import settings
from app.agent.contracts import ToolSpec
from app.agent.registry import ToolRegistry
from app.tools.integration_tools import read_high_priority_emails, read_workouts, search_knowledge


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    mutating: bool = False


TOOL_DEFINITIONS = {
    "email.high_priority.read": ToolDefinition(
        "email.high_priority.read",
        "Read high-priority emails from the existing Email Manager API."
    ),
    "fitness.workouts.read": ToolDefinition(
        "fitness.workouts.read",
        "Read workout records from the existing Fitness Manager API."
    ),
    "knowledge.search": ToolDefinition(
        "knowledge.search",
        "Search local personal knowledge with hybrid ranking. Use when the request asks about stored documents, notes, or sources; narrow by source or update time when relevant. Results include source citations and nearby chunk context."
    ),
}


def enabled_tools() -> dict[str, ToolDefinition]:
    """Preserve the interface used by the existing command executor."""
    return {
        name: item for name, item in TOOL_DEFINITIONS.items()
        if name in settings.JARVIS_ENABLED_TOOLS
    }


def build_agent_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for name, definition in TOOL_DEFINITIONS.items():
        registry.register(ToolSpec(
            name=name,
            description=definition.description,
            handler={
                "email.high_priority.read": read_high_priority_emails,
                "fitness.workouts.read": read_workouts,
                "knowledge.search": search_knowledge,
            }[name],
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 500},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                    "source": {"type": "string", "maxLength": 300},
                    "updated_after": {"type": "string", "maxLength": 50},
                    "updated_before": {"type": "string", "maxLength": 50},
                } if name == "knowledge.search" else {},
                "required": ["query"] if name == "knowledge.search" else [],
                "additionalProperties": False,
            },
            permission="read",
            enabled=name in settings.JARVIS_ENABLED_TOOLS,
        ))
    return registry


AGENT_TOOL_REGISTRY = build_agent_registry()


def tool_status() -> list[dict[str, str | bool]]:
    return [
        {
            "name": item.name,
            "description": item.description,
            "permission": "enabled" if item.enabled else "disabled",
            "mutating": item.permission != "read",
            "requires_approval": item.requires_approval,
            "handler_configured": item.handler is not None,
        }
        for item in AGENT_TOOL_REGISTRY.list_tools(enabled_only=False)
    ]
