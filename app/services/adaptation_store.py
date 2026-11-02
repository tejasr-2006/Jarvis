"""Local preference and lightweight feedback store for adaptive planning."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings


class AdaptationStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = str(folder / "adaptation.db")
        self.db_path = db_path
        Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                event TEXT NOT NULL,
                planned_minutes INTEGER,
                actual_minutes INTEGER,
                priority TEXT,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))""")

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def preferences(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = dict(conn.execute("SELECT key,value FROM preferences").fetchall())
        return {
            "enabled": rows.get("enabled", "false") == "true",
            "focus_mode": rows.get("focus_mode", "balanced"),
            "default_available_minutes": int(rows.get("default_available_minutes", "120")),
            "prefer_deadline_first": rows.get("prefer_deadline_first", "false") == "true",
            "collect_feedback": rows.get("collect_feedback", "true") == "true",
        }

    def update_preferences(self, values: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO preferences(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                [(key, str(value).lower() if isinstance(value, bool) else str(value))
                 for key, value in values.items()])
        return self.preferences()

    def record_feedback(self, task_id: int | None, event: str,
                        planned_minutes: int | None = None,
                        actual_minutes: int | None = None,
                        priority: str | None = None) -> dict[str, Any]:
        prefs = self.preferences()
        if not prefs["collect_feedback"]:
            raise PermissionError("Feedback collection is disabled")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO feedback(task_id,event,planned_minutes,actual_minutes,priority) VALUES(?,?,?,?,?)",
                (task_id, event, planned_minutes, actual_minutes, priority))
            row = conn.execute("SELECT * FROM feedback WHERE id=?", (cur.lastrowid,)).fetchone()
            return dict(row)

    def list_feedback(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    def clear_feedback(self) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM feedback")
            return cur.rowcount
