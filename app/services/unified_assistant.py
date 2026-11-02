"""Unified, predictable command router for JARVIS' existing modules.

This layer uses deterministic intent matching for supported read-only commands.
Unknown or mutating requests are not executed; the user is directed to the relevant API.
"""
from __future__ import annotations

import re
from typing import Any

from app.config import settings
from app.tasks.store import TaskStore
from app.routines_store import RoutineStore
from app.reminders.store import ReminderStore
from app.reminders.notification_store import ProactiveNotificationStore
from app.integrations.email_manager import EmailManagerClient
from app.integrations.fitness_manager import FitnessManagerClient
from app.services.tool_registry import enabled_tools
from app.calendar.service import GoogleCalendarService, CalendarNotConfigured
from app.integrations.home_assistant import HomeAssistantClient, HomeAssistantNotConfigured


HELP = [
    {"examples": ["show my tasks", "what tasks are pending"], "capability": "tasks"},
    {"examples": ["show my routines", "list daily routines"], "capability": "routines"},
    {"examples": ["check notifications", "show reminders"], "capability": "notifications"},
    {"examples": ["show high priority emails", "check my inbox"], "capability": "email"},
    {"examples": ["show my workouts", "check fitness"], "capability": "fitness"},
    {"examples": ["calendar status", "is my calendar connected"], "capability": "calendar"},
    {"examples": ["show smart home devices", "check home assistant"], "capability": "smart_home"},
]


class UnifiedAssistant:
    """Dispatch safe read operations to the app's existing local services."""

    def __init__(self):
        self.tasks = TaskStore()
        self.routines = RoutineStore()
        self.reminders = ReminderStore()
        self.notifications = ProactiveNotificationStore()

    async def handle(self, command: str) -> dict[str, Any]:
        original = command.strip()
        normalized = re.sub(r"\s+", " ", original.lower()).strip()
        if not normalized:
            return {"status": "invalid", "message": "Please enter a command."}

        if normalized in {"help", "what can you do", "what can jarvis do", "show commands"}:
            return {"status": "success", "intent": "help", "message": "Here are commands I currently support.", "capabilities": HELP}

        # Refuse mixed/read-write requests before dispatching any read operation.
        if re.search(r"\b(create|add|make|complete|finish|delete|remove|send|reply|forward|book|schedule|turn on|turn off|switch on|switch off|unlock|lock|open|close|change|update|edit|cancel|start|stop)\b", normalized):
            return {"status": "confirmation_required", "intent": "action.not_executed",
                    "message": "I haven't changed anything. Use the relevant module in /docs and review its confirmation requirements.",
                    "suggested_routes": ["/tasks", "/reminders", "/calendar/events", "/email-assistant/drafts", "/integrations/home-assistant/action"]}

        # Read-only commands are checked before general fallback.
        if re.search(r"\b(task|tasks|to[- ]dos|todo list)\b", normalized) and re.search(r"\b(show|list|view|check|what|display|pending)\b", normalized):
            items = self.tasks.list(status="pending", limit=50)
            return {"status": "success", "intent": "tasks.list", "count": len(items),
                    "message": f"You have {len(items)} pending task(s).", "data": items}

        if re.search(r"\b(routine|routines|daily routine|daily routines)\b", normalized) and re.search(r"\b(show|list|view|check|what|display)\b", normalized):
            items = self.routines.list(include_disabled=False)
            return {"status": "success", "intent": "routines.list", "count": len(items),
                    "message": f"You have {len(items)} enabled routine(s).", "data": items}

        if re.search(r"\b(notification|notifications|reminder|reminders|alerts)\b", normalized) and re.search(r"\b(show|list|check|view|what|display|pending)\b", normalized):
            reminder_items = self.reminders.list(status="fired", limit=50)
            proactive = self.notifications.list_unacknowledged(limit=50)
            items = reminder_items + [
                {"id": -int(item["id"]), "title": item["title"], "message": item["message"],
                 "kind": item["kind"], "created_at": item["created_at"], "status": "fired"}
                for item in proactive
            ]
            items.sort(key=lambda item: str(item.get("fired_at") or item.get("created_at") or ""), reverse=True)
            return {"status": "success", "intent": "notifications.list", "count": len(items),
                    "message": f"You have {len(items)} pending notification(s).", "data": items[:50]}

        if re.search(r"\b(email|emails|inbox|mail)\b", normalized) and re.search(r"\b(show|list|check|read|view|high[- ]priority|important|urgent)\b", normalized):
            if "email.high_priority.read" not in enabled_tools():
                return {"status": "permission_denied", "intent": "email.read",
                        "message": "Email reading is disabled in JARVIS tool permissions."}
            if not settings.EMAIL_MANAGER_API_KEY:
                return {"status": "authentication_required", "intent": "email.read",
                        "message": "Configure EMAIL_MANAGER_API_KEY in JARVIS .env first."}
            try:
                data = await EmailManagerClient().get_high_priority_emails()
                return {"status": "success", "intent": "email.high_priority.read",
                        "message": "Retrieved high-priority email data.", "data": data}
            except Exception as exc:
                return {"status": "failed", "intent": "email.high_priority.read",
                        "message": "Email Manager could not be reached or rejected authentication.",
                        "error_type": type(exc).__name__}

        if re.search(r"\b(workout|workouts|fitness|exercise|exercises|training)\b", normalized) and re.search(r"\b(show|list|check|view|what|display|my)\b", normalized):
            if "fitness.workouts.read" not in enabled_tools():
                return {"status": "permission_denied", "intent": "fitness.workouts.read",
                        "message": "Fitness reading is disabled in JARVIS tool permissions."}
            has_login = bool(
                settings.FITNESS_MANAGER_EMAIL and settings.FITNESS_MANAGER_PASSWORD
            )
            if not has_login and not settings.FITNESS_MANAGER_API_TOKEN:
                return {"status": "authentication_required", "intent": "fitness.workouts.read",
                        "message": "Configure FITNESS_MANAGER_EMAIL and FITNESS_MANAGER_PASSWORD (or the legacy FITNESS_MANAGER_API_TOKEN) in JARVIS .env first."}
            try:
                data = await FitnessManagerClient().get_workouts()
                return {"status": "success", "intent": "fitness.workouts.read",
                        "message": "Retrieved workout data.", "data": data}
            except Exception as exc:
                return {"status": "failed", "intent": "fitness.workouts.read",
                        "message": "Fitness Manager could not be reached or rejected authentication.",
                        "error_type": type(exc).__name__}

        if "calendar" in normalized and re.search(r"\b(status|connected|connection|health|working)\b", normalized):
            try:
                return {"status": "success", "intent": "calendar.status",
                        "message": "Google Calendar connection status.", "data": GoogleCalendarService().status()}
            except Exception:
                return {"status": "unavailable", "intent": "calendar.status",
                        "message": "Could not check Google Calendar status."}

        if re.search(r"\b(smart home|home assistant|devices|lights|light|switches|fan|fans)\b", normalized) and re.search(r"\b(show|list|check|status|state|view|what)\b", normalized):
            client = HomeAssistantClient()
            if not client.configured:
                return {"status": "not_configured", "intent": "home_assistant.states",
                        "message": "Home Assistant is not configured. Set its URL, token, and allowed entity IDs in .env."}
            try:
                states = await client.list_allowed_states()
                return {"status": "success", "intent": "home_assistant.states",
                        "count": len(states), "message": f"Found {len(states)} allow-listed device(s).", "data": states}
            except Exception as exc:
                return {"status": "failed", "intent": "home_assistant.states",
                        "message": "Could not retrieve allow-listed Home Assistant states.",
                        "error_type": type(exc).__name__}

        # Detect likely state changes and refuse to run them through natural language.
        if re.search(r"\b(create|add|make|complete|finish|delete|remove|send|reply|forward|book|schedule|turn on|turn off|switch on|switch off|unlock|lock|open|close|change|update|edit|cancel|start|stop)\b", normalized):
            return {"status": "confirmation_required", "intent": "action.not_executed",
                    "message": "I haven't changed anything. Use the relevant module in /docs and review its confirmation requirements.",
                    "suggested_routes": ["/tasks", "/reminders", "/calendar/events", "/email-assistant/drafts", "/integrations/home-assistant/action"]}

        return {"status": "not_understood", "intent": "unknown",
                "message": "I couldn't match that to a supported command. Say 'help' to see examples, or use the AI command endpoint for general understanding."}
