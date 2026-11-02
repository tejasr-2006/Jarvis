"""Personalized daily briefing with explainable, read-only recommendations."""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agent.learning import AgentLearningStore
from app.security import require_jarvis_key
from app.services.proactive_intelligence import ProactiveIntelligenceSettings, build_insights
from app.services.predictive_planning import rank_tasks
from app.tasks.store import TaskStore

router = APIRouter(
    prefix="/personalized-briefing",
    tags=["Personalized Daily Briefing"],
    dependencies=[Depends(require_jarvis_key)],
)


@router.get("/today")
def today_briefing(
    timezone: str | None = Query(default=None, min_length=1, max_length=80),
    focus_mode: str = Query(default="balanced", pattern="^(balanced|deadline_first|quick_wins|deep_work)$"),
    task_limit: int = Query(default=5, ge=1, le=20),
):
    """Combine local task insights and opt-in learning aggregates; no actions are performed."""
    preferences = ProactiveIntelligenceSettings().get()
    zone_name = timezone or preferences.get("timezone", "Asia/Kolkata")
    try:
        zone = ZoneInfo(zone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="timezone must be a valid IANA timezone") from exc

    now = datetime.now().astimezone()
    local_now = now.astimezone(zone)
    tasks = TaskStore().list(status="pending", limit=200)
    insights = build_insights(tasks, now, zone_name)
    ranked = rank_tasks(tasks, now, zone_name, focus_mode)[:task_limit]

    feedback = AgentLearningStore().list(100)
    count = len(feedback)
    average = round(sum(int(item["rating"]) for item in feedback) / count, 2) if count else None
    positive = sum(1 for item in feedback if item.get("outcome") == "helpful")
    unhelpful = sum(1 for item in feedback if item.get("outcome") == "unhelpful")

    recommendations = []
    summary = insights["summary"]
    if summary["overdue"]:
        recommendations.append({
            "kind": "deadline", "priority": "high",
            "title": "Address overdue work",
            "reason": f'{summary["overdue"]} pending task(s) are overdue.',
            "suggested_action": "Review the highest-ranked overdue task and decide whether to complete it or revise its deadline.",
        })
    if summary["due_today"]:
        recommendations.append({
            "kind": "focus", "priority": "high",
            "title": "Protect time for today's deadlines",
            "reason": f'{summary["due_today"]} pending task(s) are due today.',
            "suggested_action": "Reserve a focused block for the first due-today task in the ranked list.",
        })
    if ranked and not summary["overdue"] and not summary["due_today"]:
        recommendations.append({
            "kind": "next_step", "priority": "normal",
            "title": "Start with your top-ranked task",
            "reason": "; ".join(ranked[0]["reasons"]),
            "suggested_action": f'Review “{ranked[0]["title"]}” ({ranked[0]["estimated_minutes"]} min estimated).',
        })
    if not tasks:
        recommendations.append({
            "kind": "reset", "priority": "low",
            "title": "Plan your next priority",
            "reason": "No pending tasks are recorded.",
            "suggested_action": "Add a task if there is something you want JARVIS to help track.",
        })
    if count >= 3 and average is not None and average < 3:
        recommendations.append({
            "kind": "agent_quality", "priority": "normal",
            "title": "Review recent agent feedback",
            "reason": "Your recent feedback ratings suggest agent plans may need adjustment.",
            "suggested_action": "Review recent agent runs and feedback before using another generated plan.",
        })

    return {
        "status": "available",
        "generated_at": local_now.isoformat(timespec="seconds"),
        "timezone": zone_name,
        "focus_mode": focus_mode,
        "summary": summary,
        "top_tasks": ranked,
        "recommendations": recommendations,
        "agent_feedback_summary": {
            "records_considered": count,
            "average_rating": average,
            "helpful_count": positive,
            "unhelpful_count": unhelpful,
            "comments_included": False,
        },
        "read_only": True,
        "note": "Recommendations are explainable rules, not predictions. No tasks, reminders, emails, calendar events, or external services are changed. Feedback comments are not exposed or sent to an AI provider.",
    }
