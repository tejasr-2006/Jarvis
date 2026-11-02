"""Safe execution of registered JARVIS tools."""
from __future__ import annotations

import asyncio
import inspect
from typing import Any

from app.agent.policies import evaluate_tool_policy
from app.agent.registry import ToolRegistry, validate_arguments


class ToolExecutionError(RuntimeError):
    def __init__(self, message: str, *, code: str = "tool_execution_failed") -> None:
        super().__init__(message)
        self.code = code


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        allow_writes: bool = False,
        allow_system_tools: bool = False,
    ) -> None:
        self.registry = registry
        self.allow_writes = allow_writes
        self.allow_system_tools = allow_system_tools

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        *,
        approved: bool = False,
    ) -> dict[str, Any]:
        try:
            tool = self.registry.get(name)
        except KeyError as exc:
            raise ToolExecutionError(str(exc), code="unknown_tool") from exc

        try:
            clean_arguments = validate_arguments(tool.input_schema, arguments or {})
        except ValueError as exc:
            raise ToolExecutionError(str(exc), code="invalid_arguments") from exc

        decision = evaluate_tool_policy(
            tool,
            approved=approved,
            allow_writes=self.allow_writes,
            allow_system_tools=self.allow_system_tools,
        )
        if not decision.allowed:
            code = "approval_required" if decision.requires_approval else "permission_denied"
            raise ToolExecutionError(decision.reason, code=code)
        if tool.handler is None:
            raise ToolExecutionError(
                f"Tool '{name}' has no configured handler",
                code="handler_unavailable",
            )

        timeout = tool.timeout_seconds
        try:
            result = tool.handler(**clean_arguments)
            if inspect.isawaitable(result):
                result = await asyncio.wait_for(result, timeout=timeout)
            return {
                "status": "success",
                "tool": name,
                "result": result,
            }
        except asyncio.TimeoutError as exc:
            raise ToolExecutionError(
                f"Tool '{name}' exceeded its {timeout:g}-second timeout",
                code="tool_timeout",
            ) from exc
        except ToolExecutionError:
            raise
        except Exception as exc:
            # Keep raw upstream exception details out of the public API response.
            raise ToolExecutionError(
                f"Tool '{name}' failed. Check the JARVIS server logs.",
                code="upstream_error",
            ) from exc
