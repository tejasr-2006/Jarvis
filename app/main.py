
import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.integrations.email_manager import EmailManagerClient
from app.integrations.fitness_manager import FitnessManagerClient
from app.schemas.status import DashboardStatus
from app.services.ai_service import AIService
from app.services.command_executor import CommandExecutor
from app.api.memory import router as memory_router
from app.security import require_jarvis_key
from app.memory.store import MemoryStore
from app.memory.context import relevant_memory_context
from app.services.tool_registry import tool_status
from app.api.reminders import router as reminders_router
from app.api.notifications import router as notifications_router
from app.api.tasks import router as tasks_router
from app.api.planner import router as planner_router
from app.api.calendar import router as calendar_router
from app.api.daily_planner import router as daily_planner_router
from app.api.email_assistant import router as email_assistant_router
from app.api.computer import router as computer_router
from app.api.operations import router as operations_router
from app.api.home_assistant import router as home_assistant_router
from app.api.routines import router as routines_router
from app.api.unified_assistant import router as unified_assistant_router
from app.api.proactive import router as proactive_router
from app.api.predictive_planning import router as predictive_planning_router
from app.api.personalization import router as personalization_router
from app.api.knowledge import router as knowledge_router
from app.api.email_calendar_intelligence import router as intelligence_router
from app.api.personal_finance_fitness import router as personal_finance_fitness_router
from app.api.multimodal import router as multimodal_router
from app.api.security import router as security_router
from app.api.agent import router as agent_router
from app.api.personalized_briefing import router as personalized_briefing_router
from app.api.smart_scheduling import router as smart_scheduling_router
from app.api.dashboard import router as dashboard_router
from app.api.tools import router as tools_router
from app.api.background_agents import router as background_agents_router
from app.routines_store import RoutineStore
from app.reminders.notification_store import ProactiveNotificationStore
from app.security_ops.audit import AuditStore
from app.tasks.store import TaskStore
from app.reminders.store import ReminderStore
from app.services.monitor import monitoring_loop
from app.services.proactive_notifications import run_proactive_notification_cycle
from app.services.background_agents import (
   BackgroundAgentStore,
   fire_due_routines,
   run_background_local_cycle,
   run_email_monitor_cycle,
)
from datetime import datetime, timezone
from fastapi.responses import FileResponse

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------

class CommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=2000)


class AIRequest(BaseModel):
    command: str = Field(min_length=1, max_length=2000)


# ------------------------------------------------------------------
# Application lifecycle
# ------------------------------------------------------------------

def run_due_routines(now: datetime | None = None) -> int:
    """Queue in-app notifications for due routines; never runs arbitrary actions."""
    return fire_due_routines(now)


async def _reminder_scheduler(stop_event: asyncio.Event) -> None:
    """Run reminders frequently and configurable background agents safely."""
    reminder_store = ReminderStore()
    agent_store = BackgroundAgentStore()
    last_agent_cycle = 0.0
    last_email_cycle = 0.0
    while not stop_event.is_set():
        try:
            reminder_store.mark_due()
        except Exception:
            logger.exception("Reminder scheduler failed")

        now_mono = time.monotonic()
        if now_mono - last_agent_cycle >= 60:
            try:
                await asyncio.to_thread(run_background_local_cycle, agent_store)
            except Exception:
                logger.exception("Local background-agent cycle failed")
            last_agent_cycle = now_mono

        try:
            preferences = agent_store.preferences()
            email_interval = max(60, min(preferences["email_monitor_interval_seconds"], 86400))
            if (preferences["enabled"] and preferences["email_monitor_enabled"]
                    and now_mono - last_email_cycle >= email_interval):
                await run_email_monitor_cycle(agent_store)
                last_email_cycle = now_mono
        except Exception:
            logger.exception("Email background-agent scheduler failed")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=5)
        except asyncio.TimeoutError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s environment", settings.APP_NAME, settings.APP_ENV)
    stop_event = asyncio.Event()
    scheduler = asyncio.create_task(_reminder_scheduler(stop_event))
    monitor = asyncio.create_task(monitoring_loop(stop_event, app.state))
    app.state.reminder_stop_event = stop_event
    app.state.monitor_snapshot = {
        "checked_at": None,
        "services": {
            "email_manager": {"status": "checking"},
            "fitness_manager": {"status": "checking"},
        },
    }
    try:
        yield
    finally:
        stop_event.set()
        scheduler.cancel()
        monitor.cancel()
        try:
            await scheduler
        except asyncio.CancelledError:
            pass
        try:
            await monitor
        except asyncio.CancelledError:
            pass
        logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=f"{settings.APP_NAME} Personal AI Assistant",
    version="0.41.0",
    description="JARVIS personal AI assistant backend",
    lifespan=lifespan,
)

app.include_router(memory_router)
app.include_router(reminders_router)
app.include_router(notifications_router)
app.include_router(tasks_router)
app.include_router(planner_router)
app.include_router(calendar_router)
app.include_router(daily_planner_router)
app.include_router(email_assistant_router)
app.include_router(computer_router)
app.include_router(operations_router)
app.include_router(home_assistant_router)
app.include_router(routines_router)
app.include_router(unified_assistant_router)
app.include_router(proactive_router)
app.include_router(predictive_planning_router)
app.include_router(personalization_router)
app.include_router(knowledge_router)
app.include_router(intelligence_router)
app.include_router(personal_finance_fitness_router)
app.include_router(multimodal_router)
app.include_router(security_router)
app.include_router(agent_router)
app.include_router(personalized_briefing_router)
app.include_router(smart_scheduling_router)
app.include_router(dashboard_router)
app.include_router(tools_router)
app.include_router(background_agents_router)


@app.get("/app", tags=["Interface"], include_in_schema=False)
async def unified_app():
    """Serve the unified responsive JARVIS application."""
    return FileResponse(
        Path(__file__).parent / "static" / "jarvis.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/workspace", tags=["Interface"], include_in_schema=False)
async def workspace_console():
    """Serve the organized, single-page JARVIS workspace."""
    return FileResponse(Path(__file__).parent / "static" / "workspace.html",
                        headers={"Cache-Control": "no-store"})


@app.get("/dashboard", include_in_schema=False)
def dashboard_page():
    """Serve the dashboard shell; data remains protected by API-key auth."""
    return FileResponse(Path(__file__).parent / "static" / "dashboard.html")


@app.middleware("http")
async def audit_http_requests(request, call_next):
    """Audit request metadata only; never store body, query string, or secret headers."""
    request_id = request.headers.get("X-Request-ID", "")[:64] or uuid.uuid4().hex
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path.startswith(("/security", "/operations", "/personal", "/memory", "/multimodal")):
            response.headers["Cache-Control"] = "no-store"
        return response
    finally:
        try:
            duration_ms = int((time.perf_counter() - started) * 1000)
            # Avoid logging high-volume static/health probes; log all operational API routes.
            if request.url.path.startswith(("/memory", "/tasks", "/planner", "/calendar",
                                            "/daily-planner", "/email-assistant", "/computer", "/assistant",
                                            "/notifications", "/reminders", "/operations", "/smart-scheduling", "/integrations/home-assistant", "/routines", "/proactive", "/predictive-planning", "/personalization", "/knowledge", "/multimodal", "/security", "/agent", "/assistant", "/background-agents",
                                            "/command", "/integrations/email/high-priority")):
                AuditStore().record(request.method, request.url.path, status_code,
                                    duration_ms, request_id)
        except Exception:
            logger.exception("Audit logging failed")


# ------------------------------------------------------------------
# Integration helpers
# ------------------------------------------------------------------

def get_integration_clients() -> dict[str, Any]:
    return {
        "email_manager": EmailManagerClient(),
        "fitness_manager": FitnessManagerClient(),
    }


async def check_integration(
    name: str,
    client: Any,
) -> dict[str, Any]:
    try:
        response = await client.health_check()
        return {
            "status": "connected",
            "response": response,
        }
    except Exception:
        logger.exception("Health check failed for %s", name)
        return {"status": "unavailable"}


async def get_service_health(
    name: str,
    client: Any,
) -> dict[str, Any]:
    try:
        response = await client.health_check()
        return {
            "service": name,
            "status": "connected",
            "response": response,
        }
    except Exception as exc:
        logger.exception("Health check failed for %s", name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{name} is unavailable",
        ) from exc


# ------------------------------------------------------------------
# General endpoints
# ------------------------------------------------------------------

@app.get("/voice", tags=["Interface"], include_in_schema=False)
async def voice_console():
    """Serve the local browser voice/text console."""
    return FileResponse(Path(__file__).parent / "static" / "voice.html")


@app.get("/computer-console", tags=["Interface"], include_in_schema=False)
async def computer_control_console():
    """Serve the local permission-controlled computer action console."""
    return FileResponse(
        Path(__file__).parent / "static" / "computer.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/dashboard", tags=["Interface"], include_in_schema=False)
async def dashboard_console():
    """Serve the local JARVIS monitoring dashboard."""
    return FileResponse(Path(__file__).parent / "static" / "dashboard.html")


@app.get("/mobile", tags=["Interface"], include_in_schema=False)
async def mobile_console():
    """Serve the responsive mobile control panel."""
    return FileResponse(Path(__file__).parent / "static" / "mobile.html", headers={"Cache-Control": "no-store"})


@app.get("/mobile/manifest.webmanifest", tags=["Interface"], include_in_schema=False)
async def mobile_manifest():
    return FileResponse(Path(__file__).parent / "static" / "mobile-manifest.webmanifest",
                        media_type="application/manifest+json", headers={"Cache-Control": "no-cache"})


@app.get("/mobile/icon.svg", tags=["Interface"], include_in_schema=False)
async def mobile_icon():
    return FileResponse(Path(__file__).parent / "static" / "mobile-icon.svg", media_type="image/svg+xml")


@app.get("/mobile/service-worker.js", tags=["Interface"], include_in_schema=False)
async def mobile_service_worker():
    return FileResponse(Path(__file__).parent / "static" / "mobile-sw.js",
                        media_type="application/javascript", headers={"Cache-Control": "no-cache"})


@app.get("/", tags=["General"])
async def root():
    return {
        "app": settings.APP_NAME,
        "message": "JARVIS is online",
    }


@app.get("/health", tags=["General"])
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


# ------------------------------------------------------------------
# Fitness integration
# ------------------------------------------------------------------

@app.get("/integrations/fitness/health", tags=["Integrations"])
async def fitness_health():
    return await get_service_health(
        "fitness_manager",
        FitnessManagerClient(),
    )


# ------------------------------------------------------------------
# Email integration
# ------------------------------------------------------------------

@app.get("/integrations/email/health", tags=["Integrations"])
async def email_health():
    return await get_service_health(
        "email_manager",
        EmailManagerClient(),
    )


@app.get(
    "/integrations/email/high-priority",
    tags=["Integrations"],
)
async def get_high_priority_emails(_auth: None = Depends(require_jarvis_key)):
    try:
        emails = await EmailManagerClient().get_high_priority_emails()

        return {
            "service": "email_manager",
            "status": "success",
            "emails": emails,
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Failed to retrieve high-priority emails")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not retrieve high-priority emails",
        ) from exc


# ------------------------------------------------------------------
# Combined integration health
# ------------------------------------------------------------------

@app.get("/integrations/health", tags=["Integrations"])
async def integrations_health():
    clients = get_integration_clients()

    results = await asyncio.gather(
        *(
            check_integration(name, client)
            for name, client in clients.items()
        )
    )

    return dict(zip(clients.keys(), results))


@app.get(
    "/dashboard/status",
    response_model=DashboardStatus,
    tags=["Dashboard"],
)
async def dashboard_status():
    results = await integrations_health()

    email_status = results["email_manager"]["status"]
    fitness_status = results["fitness_manager"]["status"]

    overall_status = (
        "healthy"
        if email_status == "connected"
        and fitness_status == "connected"
        else "degraded"
    )

    return {
        "app": settings.APP_NAME,
        "status": overall_status,
        "services": [
            {
                "name": "Email Manager",
                "status": email_status,
                "url": settings.EMAIL_MANAGER_BASE_URL,
            },
            {
                "name": "Fitness Manager",
                "status": fitness_status,
                "url": settings.FITNESS_MANAGER_BASE_URL,
            },
        ],
    }


# ------------------------------------------------------------------
# Phase 5: monitoring and daily briefing
# ------------------------------------------------------------------

@app.get("/monitor/status", tags=["Monitoring"], dependencies=[Depends(require_jarvis_key)])
async def monitor_status():
    """Return the latest background health snapshot, not personal data."""
    return getattr(app.state, "monitor_snapshot", {
        "checked_at": None,
        "services": {
            "email_manager": {"status": "checking"},
            "fitness_manager": {"status": "checking"},
        },
    })


@app.get("/briefing", tags=["Briefing"], dependencies=[Depends(require_jarvis_key)])
async def daily_briefing():
    """Build a concise briefing from service health and local reminders."""
    monitor = await monitor_status()
    reminder_store = ReminderStore()
    upcoming = reminder_store.list(status="scheduled", limit=5)
    notifications = reminder_store.list(status="fired", limit=20)
    task_store = TaskStore()
    pending_tasks = task_store.list(status="pending", limit=10)
    services = monitor.get("services", {})
    connected = sum(1 for item in services.values() if item.get("status") == "connected")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_status": "healthy" if connected == 2 else ("degraded" if connected else "checking"),
        "services": services,
        "upcoming_reminders": upcoming,
        "pending_notifications": notifications,
        "pending_tasks": pending_tasks,
        "summary": (
            f"{connected} of 2 connected services are healthy; "
            f"{len(upcoming)} upcoming reminders and "
            f"{len(notifications)} pending notifications and "
            f"{len(pending_tasks)} pending tasks."
        ),
    }


# ------------------------------------------------------------------
# Main command processing
# ------------------------------------------------------------------

@app.post("/command", tags=["Commands"])
async def process_command(request: CommandRequest, _auth: None = Depends(require_jarvis_key)):
    command = request.command.strip()

    if not command:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Command cannot be empty",
        )

    try:
        # Step 1: Classify the user's natural-language command.
        ai = AIService()

        memory_context = await run_in_threadpool(_get_memory_context_for_ai, command, ai.provider)
        classification = await run_in_threadpool(
            ai.classify_command,
            command,
            memory_context,
        )

        # Step 2: Execute the classified command.
        # CommandExecutor must validate permissions and confirmation
        # requirements before performing sensitive actions.
        executor = CommandExecutor()

        result = await executor.execute(classification, original_command=command)

        # Step 3: Return the classification and execution result.
        return {
            "app": settings.APP_NAME,
            "command": command,
            "classification": classification,
            "result": result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Command processing failed")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to process command",
        ) from exc



def _get_memory_context_for_ai(command: str, provider: str) -> str:
    """Only expose saved facts to local AI by default; cloud sharing is opt-in."""
    try:
        memory_store = MemoryStore()
        preferences = memory_store.get_preferences()
        if not preferences["context_enabled"]:
            return ""
        is_local = provider == "ollama" and settings.OLLAMA_BASE_URL.startswith(
            ("http://127.0.0.1", "http://localhost", "http://[::1]")
        )
        if not is_local and not preferences["cloud_context_enabled"]:
            return ""
        return relevant_memory_context(command, memory_store)
    except Exception:
        logger.warning("Memory context unavailable; continuing without saved memory")
        return ""


@app.get("/tools", tags=["Tools"], dependencies=[Depends(require_jarvis_key)])
async def list_available_tools():
    """List explicitly enabled tools without exposing credentials."""
    return {"tools": tool_status(), "mode": "read_only"}


@app.get("/ai/provider", tags=["AI"])
async def ai_provider_status():
    """Return configured provider metadata without exposing credentials."""
    from app.config import settings

    if settings.AI_PROVIDER == "gemini":
        model = settings.GEMINI_MODEL
    elif settings.AI_PROVIDER == "ollama":
        model = settings.OLLAMA_MODEL
    else:
        model = "unknown"

    return {
        "provider": settings.AI_PROVIDER,
        "model": model,
        "local_inference": settings.AI_PROVIDER == "ollama"
            and settings.OLLAMA_BASE_URL.startswith(
                ("http://127.0.0.1", "http://localhost", "http://[::1]")
            ),
    }


# ------------------------------------------------------------------
# AI command understanding
# ------------------------------------------------------------------

@app.post("/ai/understand", tags=["AI"])
async def understand_command(request: AIRequest, _auth: None = Depends(require_jarvis_key)):
    command = request.command.strip()

    if not command:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Command cannot be empty",
        )

    try:
        ai = AIService()

        # Run the synchronous AI operation outside the event loop.
        memory_context = await run_in_threadpool(_get_memory_context_for_ai, command, ai.provider)
        result = await run_in_threadpool(
            ai.understand_command,
            command,
            memory_context,
        )

        return {
            "app": settings.APP_NAME,
            "command": command,
            "understanding": result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "JARVIS AI command understanding failed"
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI request failed. Check the JARVIS backend logs.",
        ) from exc


# ------------------------------------------------------------------
# AI command classification
# ------------------------------------------------------------------

@app.post("/ai/classify", tags=["AI"])
async def classify_command(request: AIRequest, _auth: None = Depends(require_jarvis_key)):
    command = request.command.strip()

    if not command:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Command cannot be empty",
        )

    try:
        ai = AIService()

        result = await run_in_threadpool(
            ai.classify_command,
            command,
        )

        return {
            "app": settings.APP_NAME,
            "command": command,
            "classification": result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("JARVIS command classification failed")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Command classification failed. Check the JARVIS backend logs.",
        ) from exc
