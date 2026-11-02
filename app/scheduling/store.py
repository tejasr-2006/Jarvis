"""Local SQLite storage for proposed and explicitly confirmed schedules."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.config import settings


class ScheduleProposalStore:
    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = folder / "schedule_proposals.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL CHECK(status IN ('pending_approval','confirmed','rejected')),
                plan_date TEXT NOT NULL,
                timezone TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            )""")

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _decode(row) -> dict[str, Any]:
        item = dict(row)
        item["plan"] = json.loads(item.pop("payload"))
        return item

    def create(self, plan_date: str, timezone: str, plan: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as db:
            cur = db.execute(
                "INSERT INTO proposals(status,plan_date,timezone,payload) VALUES('pending_approval',?,?,?)",
                (plan_date, timezone, json.dumps(plan, ensure_ascii=False)),
            )
            row = db.execute("SELECT * FROM proposals WHERE id=?", (cur.lastrowid,)).fetchone()
        return self._decode(row)

    def get(self, proposal_id: int) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        return self._decode(row) if row else None

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM proposals ORDER BY id DESC LIMIT ?", (max(1,min(limit,100)),)).fetchall()
        return [self._decode(row) for row in rows]

    def decide(self, proposal_id: int, decision: str) -> dict[str, Any] | None:
        if decision not in {"confirmed", "rejected"}:
            raise ValueError("unsupported decision")
        with self._connect() as db:
            cur = db.execute(
                "UPDATE proposals SET status=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') "
                "WHERE id=? AND status='pending_approval'",
                (decision, proposal_id),
            )
            if cur.rowcount != 1:
                return None
            row = db.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        return self._decode(row)
