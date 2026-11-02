"""SQLite-backed local task store; no network calls."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings


class TaskStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = str(folder / "tasks.db")
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
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    priority TEXT NOT NULL DEFAULT 'normal',
                    due_at TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    completed_at TEXT
                )
            """)

    @staticmethod
    def _dict(row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    def create(self, title: str, description: str = '', priority: str = 'normal', due_at: str | None = None):
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO tasks(title, description, priority, due_at) VALUES (?, ?, ?, ?)",
                (title.strip(), description.strip(), priority, due_at),
            )
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
            return self._dict(row)

    def list(self, status: str | None = None, limit: int = 100):
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, due_at IS NULL, due_at, id LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tasks ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, due_at IS NULL, due_at, id LIMIT ?",
                    (limit,),
                ).fetchall()
            return [self._dict(row) for row in rows]

    def complete(self, task_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            conn.execute("UPDATE tasks SET status='completed', completed_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND status='pending'", (task_id,))
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            return self._dict(row) if row else None

    def delete(self, task_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            return cur.rowcount > 0
