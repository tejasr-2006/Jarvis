from fastapi import APIRouter, Depends, HTTPException, Query
from app.security import require_jarvis_key
from app.reminders.store import ReminderStore
from app.reminders.notification_store import ProactiveNotificationStore

router = APIRouter(prefix="/notifications", tags=["Notifications"],
                   dependencies=[Depends(require_jarvis_key)])
# `store` remains public for backwards compatibility and existing reminder clients/tests.
store = ReminderStore()
proactive_store = ProactiveNotificationStore()

@router.get("")
def list_notifications(limit: int = Query(default=50, ge=1, le=200)):
    """List fired reminders and unacknowledged proactive alerts."""
    reminder_items = store.list(status="fired", limit=limit)
    proactive_items = []
    for item in proactive_store.list_unacknowledged(limit=limit):
        # Negative IDs keep this namespace distinct from reminder IDs.
        proactive_items.append({
            "id": -int(item["id"]),
            "title": item["title"],
            "message": item["message"],
            "status": "fired",
            "kind": item["kind"],
            "source": item["source"],
            "created_at": item["created_at"],
        })
    items = reminder_items + proactive_items
    items.sort(key=lambda item: str(item.get("fired_at") or item.get("created_at") or ""), reverse=True)
    return {"notifications": items[:limit]}

@router.post("/{notification_id}/ack")
def acknowledge_notification(notification_id: int):
    if notification_id < 0:
        if not proactive_store.acknowledge(abs(notification_id)):
            raise HTTPException(status_code=404, detail="Notification not found or already acknowledged")
        return {"status": "acknowledged", "id": notification_id}
    if not store.acknowledge(notification_id):
        raise HTTPException(status_code=404, detail="Notification not found or already acknowledged")
    return {"status": "acknowledged", "id": notification_id}
