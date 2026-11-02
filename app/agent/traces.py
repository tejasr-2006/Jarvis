"""Minimal local execution traces; stores metadata, never upstream payloads."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings


class AgentTraceStore:
    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = folder / "agent_traces.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS agent_traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                goal TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                tool_results_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            )""")

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def add(self, goal: str, plan: list[dict[str, Any]], results: list[dict[str, Any]],
            status: str, session_id: str | None = None) -> int:
        # Deliberately persist tool names/status only, not email/workout content.
        safe_results = [{"tool": r.get("tool"), "status": r.get("status"),
                         "error_code": r.get("error_code")} for r in results]
        with self._connect() as db:
            cur = db.execute(
                "INSERT INTO agent_traces(session_id,goal,plan_json,tool_results_json,status) VALUES (?,?,?,?,?)",
                (session_id, goal[:2000], json.dumps(plan), json.dumps(safe_results), status),
            )
            return int(cur.lastrowid)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM agent_traces ORDER BY id DESC LIMIT ?",
                              (max(1, min(limit, 100)),)).fetchall()
        return [{**dict(row), "plan": json.loads(row["plan_json"]),
                 "tool_results": json.loads(row["tool_results_json"]),
                 "plan_json": None, "tool_results_json": None} for row in rows]
