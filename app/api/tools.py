"""Authenticated discovery and execution endpoints for registered tools."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agent.executor import ToolExecutionError, ToolExecutor
from app.config import settings
from app.security import require_jarvis_key
from app.services.tool_registry import AGENT_TOOL_REGISTRY

router = APIRouter(prefix="/tools", tags=["Agent Tools"], dependencies=[Depends(require_jarvis_key)])
executor = ToolExecutor(
    AGENT_TOOL_REGISTRY,
    allow_writes=settings.AGENT_ALLOW_WRITES,
)


class ToolExecutionRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


@router.post("/{tool_name}/execute")
async def execute_registered_tool(tool_name: str, body: ToolExecutionRequest):
    """Execute a registered tool. Current integrations are read-only."""
    try:
        return await executor.execute(tool_name, body.arguments)
    except ToolExecutionError as exc:
        status_code = {
            "unknown_tool": 404,
            "invalid_arguments": 422,
            "approval_required": 403,
            "permission_denied": 403,
            "handler_unavailable": 503,
            "tool_timeout": 504,
            "upstream_error": 502,
        }.get(exc.code, 500)
        raise HTTPException(status_code=status_code, detail={"code": exc.code, "message": str(exc)}) from exc
