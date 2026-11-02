"""SQLite storage for AI-proposed plans; plans never execute without approval."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings

class PlanStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = str(folder / "plans.db")
        self.db_path = db_path
        Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                tasks_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending_approval',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                decided_at TEXT
            )""")
    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    @staticmethod
    def _item(row):
        item = dict(row)
        item['tasks'] = json.loads(item.pop('tasks_json'))
        return item
    def create(self, goal: str, tasks: list[dict[str, Any]]):
        with self._connect() as conn:
            cur = conn.execute('INSERT INTO plans(goal,tasks_json) VALUES (?,?)', (goal, json.dumps(tasks)))
            row = conn.execute('SELECT * FROM plans WHERE id=?', (cur.lastrowid,)).fetchone()
            return self._item(row)
    def get(self, plan_id: int):
        with self._connect() as conn:
            row = conn.execute('SELECT * FROM plans WHERE id=?', (plan_id,)).fetchone()
            return self._item(row) if row else None
    def decide(self, plan_id: int, expected: str, new_status: str):
        with self._connect() as conn:
            cur = conn.execute("UPDATE plans SET status=?, decided_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND status=?", (new_status, plan_id, expected))
            if cur.rowcount != 1:
                return None
            row = conn.execute('SELECT * FROM plans WHERE id=?', (plan_id,)).fetchone()
            return self._item(row)
    def list(self, limit: int = 50):
        with self._connect() as conn:
            rows = conn.execute('SELECT * FROM plans ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
            return [self._item(row) for row in rows]
