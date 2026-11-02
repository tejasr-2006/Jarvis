"""Local SQLite reminder and notification queue; this module makes no network calls."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings

class ReminderStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = str(folder / "reminders.db")
        self.db_path = db_path
        Path(self.db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'scheduled',
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    fired_at TEXT,
                    acknowledged_at TEXT
                )
            """)

    @staticmethod
    def _dict(row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    def create(self, title: str, due_at: str) -> dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute("INSERT INTO reminders(title, due_at) VALUES (?, ?)",
                               (title.strip(), due_at))
            row = conn.execute("SELECT * FROM reminders WHERE id = ?", (cur.lastrowid,)).fetchone()
            return self._dict(row)

    def list(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM reminders WHERE status = ? ORDER BY due_at LIMIT ?",
                    (status, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM reminders ORDER BY due_at LIMIT ?", (limit,)).fetchall()
            return [self._dict(row) for row in rows]

    def delete(self, reminder_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM reminders WHERE id = ? AND status = 'scheduled'",
                               (reminder_id,))
            return cur.rowcount > 0

    def mark_due(self) -> int:
        # ISO-8601 timestamps are normalized to UTC by the API before insertion.
        with self._connect() as conn:
            cur = conn.execute("""
                UPDATE reminders SET status = 'fired',
                    fired_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE status = 'scheduled'
                  AND julianday(due_at) <= julianday('now')
            """)
            return cur.rowcount

    def acknowledge(self, reminder_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("""
                UPDATE reminders SET status = 'acknowledged',
                    acknowledged_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE id = ? AND status = 'fired'
            """, (reminder_id,))
            return cur.rowcount > 0
