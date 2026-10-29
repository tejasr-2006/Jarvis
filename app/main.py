
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.integrations.email_manager import EmailManagerClient
from app.integrations.fitness_manager import FitnessManagerClient
from app.schemas.status import DashboardStatus
from app.services.ai_service import AIService
from app.services.command_executor import CommandExecutor

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting %s in %s environment",
        settings.APP_NAME,
        settings.APP_ENV,
    )

    try:
        yield
    finally:
        logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=f"{settings.APP_NAME} Personal AI Assistant",
    version="0.2.0",
    description="JARVIS personal AI assistant backend",
    lifespan=lifespan,
)


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
async def get_high_priority_emails():
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
# Main command processing
# ------------------------------------------------------------------

@app.post("/command", tags=["Commands"])
async def process_command(request: CommandRequest):
    command = request.command.strip()

    if not command:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Command cannot be empty",
        )

    try:
        # Step 1: Classify the user's natural-language command.
        ai = AIService()

        classification = await run_in_threadpool(
            ai.classify_command,
            command,
        )

        # Step 2: Execute the classified command.
        # CommandExecutor must validate permissions and confirmation
        # requirements before performing sensitive actions.
        executor = CommandExecutor()

        result = await executor.execute(classification)

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


# ------------------------------------------------------------------
# AI command understanding
# ------------------------------------------------------------------

@app.post("/ai/understand", tags=["AI"])
async def understand_command(request: AIRequest):
    command = request.command.strip()

    if not command:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Command cannot be empty",
        )

    try:
        ai = AIService()

        # Run the synchronous AI operation outside the event loop.
        result = await run_in_threadpool(
            ai.understand_command,
            command,
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
async def classify_command(request: AIRequest):
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
