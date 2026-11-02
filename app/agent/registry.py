"""In-process allow-list registry for trusted JARVIS tools."""
from __future__ import annotations

from typing import Any
from app.agent.contracts import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def replace(self, tool: ToolSpec) -> None:
        """Explicit replacement for controlled startup/configuration use."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list_tools(self, *, enabled_only: bool = True) -> list[ToolSpec]:
        tools = self._tools.values()
        if enabled_only:
            tools = (tool for tool in tools if tool.enabled)
        return sorted(tools, key=lambda tool: tool.name)

    def describe(self) -> list[dict[str, Any]]:
        return [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
            "permission": tool.permission,
            "requires_approval": tool.requires_approval,
            "enabled": tool.enabled,
        } for tool in self.list_tools(enabled_only=False)]

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)


def validate_arguments(schema: dict[str, Any], arguments: Any) -> dict[str, Any]:
    """Validate the safe JSON Schema subset used by tool contracts.

    Supports object properties, required, additionalProperties, primitive types,
    enum, and basic string/numeric/array bounds. Unknown schema keywords are
    ignored; tool handlers must still validate business-specific constraints.
    """
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object")
    if schema.get("type", "object") != "object":
        raise ValueError("Only object tool schemas are supported")

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if not isinstance(properties, dict) or not isinstance(required, list):
        raise ValueError("Invalid tool schema definition")

    missing = [key for key in required if key not in arguments]
    if missing:
        raise ValueError(f"Missing required argument(s): {', '.join(missing)}")
    if schema.get("additionalProperties", False) is False:
        unknown = set(arguments) - set(properties)
        if unknown:
            raise ValueError(f"Unexpected argument(s): {', '.join(sorted(unknown))}")

    type_map = {
        "object": dict, "array": list, "string": str,
        "integer": int, "number": (int, float), "boolean": bool,
    }
    for key, value in arguments.items():
        rule = properties.get(key)
        if rule is None:
            continue
        expected = rule.get("type")
        if expected in type_map:
            valid_type = isinstance(value, type_map[expected])
            if expected in {"integer", "number"} and isinstance(value, bool):
                valid_type = False
            if not valid_type:
                raise ValueError(f"Argument '{key}' must be {expected}")
        if "enum" in rule and value not in rule["enum"]:
            raise ValueError(f"Argument '{key}' must be one of: {rule['enum']}")
        if isinstance(value, str):
            if len(value) < rule.get("minLength", 0):
                raise ValueError(f"Argument '{key}' is too short")
            if len(value) > rule.get("maxLength", 100_000):
                raise ValueError(f"Argument '{key}' is too long")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if value < rule.get("minimum", float("-inf")):
                raise ValueError(f"Argument '{key}' is below minimum")
            if value > rule.get("maximum", float("inf")):
                raise ValueError(f"Argument '{key}' exceeds maximum")
        if isinstance(value, list):
            if len(value) < rule.get("minItems", 0) or len(value) > rule.get("maxItems", 100_000):
                raise ValueError(f"Argument '{key}' has an invalid number of items")
    return arguments
