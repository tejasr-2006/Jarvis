"""Persistent proposals and run state for the guarded goal-based agent."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings


class AgentRunStore:
    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = folder / "agent_runs.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending_approval',
                    results_json TEXT,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    approved_at TEXT,
                    executed_at TEXT
                )
            """)

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _serialize(row):
        item = dict(row)
        item["steps"] = json.loads(item.pop("plan_json"))
        item["results"] = json.loads(item.pop("results_json")) if item.get("results_json") else None
        return item

    def create(self, goal: str, steps: list[dict[str, Any]]) -> dict:
        with self._connect() as db:
            cur = db.execute("INSERT INTO agent_runs(goal,plan_json) VALUES (?,?)",
                             (goal, json.dumps(steps, ensure_ascii=False)))
            row = db.execute("SELECT * FROM agent_runs WHERE id=?", (cur.lastrowid,)).fetchone()
        return self._serialize(row)

    def get(self, run_id: int) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM agent_runs WHERE id=?", (run_id,)).fetchone()
        return self._serialize(row) if row else None

    def list(self, limit: int = 50) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM agent_runs ORDER BY id DESC LIMIT ?",
                              (max(1, min(limit, 100)),)).fetchall()
        return [self._serialize(row) for row in rows]

    def approve(self, run_id: int) -> dict | None:
        with self._connect() as db:
            cur = db.execute("""UPDATE agent_runs SET status='approved',
                approved_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE id=? AND status='pending_approval'""", (run_id,))
            if cur.rowcount != 1:
                return None
            row = db.execute("SELECT * FROM agent_runs WHERE id=?", (run_id,)).fetchone()
        return self._serialize(row)

    def reject(self, run_id: int) -> dict | None:
        with self._connect() as db:
            cur = db.execute("""UPDATE agent_runs SET status='rejected'
                WHERE id=? AND status='pending_approval'""", (run_id,))
            if cur.rowcount != 1:
                return None
            row = db.execute("SELECT * FROM agent_runs WHERE id=?", (run_id,)).fetchone()
        return self._serialize(row)

    def finish(self, run_id: int, results: list[dict[str, Any]]) -> dict | None:
        with self._connect() as db:
            cur = db.execute("""UPDATE agent_runs SET status='executed', results_json=?,
                executed_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE id=? AND status='approved'""",
                (json.dumps(results, ensure_ascii=False), run_id))
            if cur.rowcount != 1:
                return None
            row = db.execute("SELECT * FROM agent_runs WHERE id=?", (run_id,)).fetchone()
        return self._serialize(row)
