"""Conservative preference-aware planning; no opaque ML model or cloud training."""
from __future__ import annotations
from typing import Any
from app.services.adaptation_store import AdaptationStore
from app.services.predictive_planning import build_day_plan


def personalized_plan(tasks: list[dict[str, Any]], available_minutes: int | None = None,
                      focus_mode: str | None = None, timezone_name: str = "Asia/Kolkata",
                      duration_overrides: dict[int, int] | None = None,
                      store: AdaptationStore | None = None) -> dict[str, Any]:
    store = store or AdaptationStore()
    prefs = store.preferences()
    enabled = prefs["enabled"]
    effective_minutes = available_minutes if available_minutes is not None else prefs["default_available_minutes"]
    if focus_mode:
        effective_mode = focus_mode
    elif enabled and prefs["prefer_deadline_first"]:
        effective_mode = "deadline_first"
    elif enabled:
        effective_mode = prefs["focus_mode"]
    else:
        effective_mode = "balanced"
    result = build_day_plan(tasks, effective_minutes, timezone_name=timezone_name,
                            focus_mode=effective_mode, duration_overrides=duration_overrides)
    result["personalization"] = {
        "enabled": enabled,
        "applied": enabled and (focus_mode is None or focus_mode == effective_mode),
        "focus_mode": effective_mode,
        "available_minutes": effective_minutes,
        "source": "explicit request" if focus_mode or available_minutes is not None else (
            "saved preferences" if enabled else "safe defaults; personalization disabled"),
    }
    result["note"] += " Personalization is based only on locally saved preferences and optional explicit feedback."
    return result
