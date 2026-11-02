"""Typed contracts for the JARVIS tool/agent runtime.

Tools are metadata plus an optional trusted Python handler. AI-generated content
may select a registered tool, but can never provide executable code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal

Permission = Literal["read", "write", "destructive", "system"]
ToolHandler = Callable[..., Any | Awaitable[Any]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    handler: ToolHandler | None = field(default=None, repr=False, compare=False)
    input_schema: dict[str, Any] = field(default_factory=lambda: {
        "type": "object", "properties": {}, "additionalProperties": False
    })
    permission: Permission = "read"
    requires_approval: bool = False
    enabled: bool = True
    timeout_seconds: float = 15.0

    def __post_init__(self) -> None:
        if not self.name or len(self.name) > 128:
            raise ValueError("Tool name must contain 1-128 characters")
        if not self.description.strip():
            raise ValueError("Tool description cannot be empty")
        if self.permission not in {"read", "write", "destructive", "system"}:
            raise ValueError(f"Unsupported permission: {self.permission}")
        if self.timeout_seconds <= 0 or self.timeout_seconds > 300:
            raise ValueError("timeout_seconds must be greater than 0 and at most 300")
        if self.requires_approval is False and self.permission in {"destructive", "system"}:
            raise ValueError("Destructive and system tools must require approval")
        if self.input_schema.get("type", "object") != "object":
            raise ValueError("Tool input_schema must describe a JSON object")
