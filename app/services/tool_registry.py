"""Backward-compatible tool metadata backed by the new agent registry.

The existing command executor still consumes enabled_tools(); the new agent
runtime can consume AGENT_TOOL_REGISTRY and its typed contracts. Actual service
handlers are attached in the integration phase, not guessed here.
"""
from dataclasses import dataclass
from app.config import settings
from app.agent.contracts import ToolSpec
from app.agent.registry import ToolRegistry
from app.tools.integration_tools import read_high_priority_emails, read_workouts


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
            }[name],
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
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
