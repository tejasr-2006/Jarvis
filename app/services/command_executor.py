import re
from typing import Any
from app.config import settings
from app.integrations.email_manager import EmailManagerClient
from app.integrations.fitness_manager import FitnessManagerClient
from app.services.tool_registry import enabled_tools

_MUTATING_ACTION = re.compile(
    r"\b(send|forward|reply|delete|remove|modify|edit|update|change|create|"
    r"cancel|archive|move|mark\s+as\s+(?:read|unread|important)|purchase|buy|"
    r"submit|share|publish|schedule|log|record|add|set|reset)\b", re.IGNORECASE
)
_EMAIL_READ = re.compile(
    r"\b(high[- ]priority|priority|important|urgent)\b.*\b(email|emails|inbox|mail)\b"
    r"|\b(email|emails|inbox|mail)\b.*\b(high[- ]priority|priority|important|urgent)\b",
    re.IGNORECASE
)
_FITNESS_READ = re.compile(
    r"\b(workout|workouts|exercise|exercises|training session|training sessions)\b",
    re.IGNORECASE
)

class CommandExecutor:
    """Only executes explicitly registered read-only tools in Phase 3."""
    async def execute(self, classification: dict[str, Any],
                      original_command: str = "") -> dict[str, Any]:
        service = classification.get("service")
        intent = classification.get("intent")
        model_confirmation = classification.get("requires_confirmation", False)
        if service not in {"email_manager", "fitness_manager", "jarvis"}:
            return {"status": "rejected", "message": "Unsupported service."}
        if not isinstance(intent, str) or not intent.strip() or len(intent) > 500:
            return {"status": "rejected", "message": "Invalid command intent."}
        if _MUTATING_ACTION.search(original_command) or model_confirmation:
            return {
                "status": "confirmation_required",
                "message": "This request may change data. Phase 3 only supports read-only tools; no action was taken.",
                "service": service,
            }

        tools = enabled_tools()
        if service == "email_manager":
            if not _EMAIL_READ.search(original_command):
                return {"status": "not_implemented", "service": service,
                        "intent": intent,
                        "message": "Only read-only high-priority email retrieval is enabled."}
            if "email.high_priority.read" not in tools:
                return {"status": "permission_denied", "message": "Email read tool is disabled."}
            if not settings.EMAIL_MANAGER_API_KEY:
                return {"status": "authentication_required", "service": service,
                        "message": "Configure EMAIL_MANAGER_API_KEY before reading email."}
            try:
                result = await EmailManagerClient().get_high_priority_emails()
                return {"status": "success", "service": service,
                        "tool": "email.high_priority.read", "data": result}
            except Exception as exc:
                return {"status": "failed", "service": service,
                        "message": "Could not retrieve high-priority emails. Check service availability and authentication.",
                        "error_type": type(exc).__name__}

        if service == "fitness_manager":
            if not _FITNESS_READ.search(original_command):
                return {"status": "not_implemented", "service": service,
                        "intent": intent,
                        "message": "Only read-only workout retrieval is enabled."}
            if "fitness.workouts.read" not in tools:
                return {"status": "permission_denied", "message": "Fitness read tool is disabled."}
            has_login = bool(
                settings.FITNESS_MANAGER_EMAIL and settings.FITNESS_MANAGER_PASSWORD
            )
            if not has_login and not settings.FITNESS_MANAGER_API_TOKEN:
                return {"status": "authentication_required", "service": service,
                        "message": "Configure FITNESS_MANAGER_EMAIL and FITNESS_MANAGER_PASSWORD (or the legacy FITNESS_MANAGER_API_TOKEN) to read personal workouts."}
            try:
                result = await FitnessManagerClient().get_workouts(
                    token=settings.FITNESS_MANAGER_API_TOKEN or None
                )
                return {"status": "success", "service": service,
                        "tool": "fitness.workouts.read", "data": result}
            except Exception as exc:
                return {"status": "failed", "service": service,
                        "message": "Could not retrieve workouts. Check service availability and authentication.",
                        "error_type": type(exc).__name__}

        return {"status": "understood",
                "message": f"JARVIS understood your request: {intent}",
                "service": "jarvis", "intent": intent}
