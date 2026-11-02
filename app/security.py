"""Shared-secret authentication for local JARVIS control endpoints."""
import secrets
from typing import Annotated
from fastapi import Header, HTTPException, status
from app.config import settings

async def require_jarvis_key(
    x_jarvis_api_key: Annotated[str | None, Header()] = None,
) -> None:
    configured = settings.JARVIS_API_KEY
    if not configured or configured == "replace-with-a-long-random-secret":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JARVIS control API is locked. Configure a private JARVIS_API_KEY.",
        )
    if not x_jarvis_api_key or not secrets.compare_digest(x_jarvis_api_key, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing JARVIS API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
