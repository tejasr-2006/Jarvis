"""Authenticated security posture and local threat summary endpoints."""
from fastapi import APIRouter, Depends, Query

from app.config import settings
from app.security import require_jarvis_key
from app.security_ops.audit import AuditStore
from app.security_ops.threat_detection import summarize_threats

router = APIRouter(prefix="/security", tags=["Advanced Security"],
                   dependencies=[Depends(require_jarvis_key)])


@router.get("/policy")
def security_policy():
    return {
        "api_key_configured": bool(settings.JARVIS_API_KEY) and settings.JARVIS_API_KEY != "replace-with-a-long-random-secret",
        "api_key_transport": "X-JARVIS-API-Key header",
        "audit_storage": "local SQLite metadata only",
        "automatic_blocking": False,
        "recommended_exposure": "localhost or private VPN; do not port-forward directly to the public internet",
        "recommendations": [
            "Use a unique, long random JARVIS_API_KEY and keep it out of source control.",
            "Keep .env, OAuth credentials, and tokens private; rotate any secret that may have been exposed.",
            "Use localhost or a trusted private VPN; add HTTPS before any trusted remote access.",
            "Keep JARVIS, Python dependencies, and connected services updated.",
            "Review audit events and threat summaries after unexpected access or errors.",
            "Back up ~/.jarvis securely and restrict OS account access.",
        ],
    }


@router.get("/threats")
def threat_summary(minutes: int = Query(default=60, ge=5, le=1440)):
    return summarize_threats(minutes=minutes)


@router.get("/audit")
def security_audit(limit: int = Query(default=100, ge=1, le=200),
                   offset: int = Query(default=0, ge=0)):
    return {"items": AuditStore().list(limit, offset), "limit": limit, "offset": offset,
            "note": "Metadata only; request bodies, query strings, headers, and source IPs are not stored."}
