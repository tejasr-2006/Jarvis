"""Conservative local heuristics over metadata-only JARVIS audit events."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings
from app.security_ops.audit import AuditStore


def summarize_threats(*, minutes: int = 60, store: AuditStore | None = None) -> dict:
    """Return advisory alerts; never block requests or claim attribution."""
    audit = store or AuditStore()
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    # Fetch a bounded recent window; audit.list caps at 200 by design.
    events = audit.list(limit=200, offset=0)
    recent = []
    for event in events:
        try:
            timestamp = datetime.fromisoformat(event["created_at"])
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            if timestamp >= cutoff:
                recent.append(event)
        except (KeyError, TypeError, ValueError):
            continue

    failed = [e for e in recent if e.get("status_code") in (401, 403)]
    server_errors = [e for e in recent if isinstance(e.get("status_code"), int) and e["status_code"] >= 500]
    by_route = Counter(e.get("route", "") for e in failed)
    alerts = []
    if len(failed) >= 5:
        alerts.append({
            "severity": "high" if len(failed) >= 15 else "medium",
            "type": "repeated_auth_failures",
            "count": len(failed),
            "message": "Multiple unauthorized/forbidden requests were recorded. Check access logs and rotate the API key if exposure is suspected.",
        })
    suspicious_routes = [
        route for route, count in by_route.items()
        if count >= 3 and any(token in route.lower() for token in ("/admin", "/.env", "/wp-", "/phpmyadmin", "/etc/"))
    ]
    if suspicious_routes:
        alerts.append({
            "severity": "medium",
            "type": "repeated_sensitive_path_probes",
            "count": sum(by_route[r] for r in suspicious_routes),
            "message": "Repeated requests to sensitive or unrelated paths were recorded. Confirm JARVIS is not exposed to untrusted networks.",
        })
    if len(server_errors) >= 10:
        alerts.append({
            "severity": "low",
            "type": "server_error_burst",
            "count": len(server_errors),
            "message": "A burst of server errors occurred. Review recent audit events and service health.",
        })
    return {
        "window_minutes": minutes,
        "events_reviewed": len(recent),
        "authentication_failures": len(failed),
        "server_errors": len(server_errors),
        "alerts": alerts,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "Heuristic advisory only: audit records contain route metadata, not source IPs or request bodies. This does not identify an attacker or automatically block traffic.",
    }
