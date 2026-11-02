"""Persistent, deduplicated in-app notification queue for proactive alerts."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings


class ProactiveNotificationStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = str(folder / "notifications.db")
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
                CREATE TABLE IF NOT EXISTS proactive_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_key TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL DEFAULT '',
                    kind TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    acknowledged_at TEXT
                )
            """)

    @staticmethod
    def _dict(row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    def create_once(self, event_key: str, title: str, message: str, kind: str, source: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO proactive_notifications(event_key,title,message,kind,source) VALUES (?,?,?,?,?)",
                (event_key, title[:200], message[:1000], kind[:40], source[:80]),
            )
            return cur.rowcount == 1

    def list_unacknowledged(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM proactive_notifications WHERE acknowledged_at IS NULL ORDER BY created_at DESC,id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._dict(row) for row in rows]

    def acknowledge(self, notification_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE proactive_notifications SET acknowledged_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND acknowledged_at IS NULL",
                (notification_id,),
            )
            return cur.rowcount == 1
