"""Central policy checks for tool execution."""
from dataclasses import dataclass
from app.agent.contracts import ToolSpec


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str


def evaluate_tool_policy(
    tool: ToolSpec,
    *,
    approved: bool = False,
    allow_writes: bool = False,
    allow_system_tools: bool = False,
) -> PolicyDecision:
    if not tool.enabled:
        return PolicyDecision(False, False, "Tool is disabled")
    if tool.permission == "read":
        return PolicyDecision(True, False, "Read-only tool allowed")
    if tool.permission == "write" and not allow_writes:
        return PolicyDecision(False, True, "Write operations are disabled by policy")
    if tool.permission == "system" and not allow_system_tools:
        return PolicyDecision(False, True, "System operations are disabled by policy")
    needs_approval = tool.requires_approval or tool.permission in {"write", "destructive", "system"}
    if needs_approval and not approved:
        return PolicyDecision(False, True, "Explicit user approval is required")
    return PolicyDecision(True, False, "Policy checks passed")
