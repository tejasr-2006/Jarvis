"""Local, user-controlled agent feedback storage."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings


class AgentLearningStore:
    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = folder / "agent_learning.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL UNIQUE,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                outcome TEXT NOT NULL,
                comment TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            )""")

    def _connect(self):
        db=sqlite3.connect(self.db_path, timeout=10)
        db.row_factory=sqlite3.Row
        return db

    def add(self, run_id: int, rating: int, outcome: str, comment: str = "") -> dict[str, Any]:
        with self._connect() as db:
            cur=db.execute("INSERT INTO feedback(run_id,rating,outcome,comment) VALUES (?,?,?,?)",
                           (run_id,rating,outcome,comment.strip()[:500]))
            row=db.execute("SELECT * FROM feedback WHERE id=?",(cur.lastrowid,)).fetchone()
        return dict(row)

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows=db.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT ?",(max(1,min(limit,100)),)).fetchall()
        return [dict(row) for row in rows]

    def context(self, limit: int = 8) -> list[dict[str, Any]]:
        # Keep the context small and bounded; caller must explicitly opt in before sending to AI.
        return [{"rating":x["rating"],"outcome":x["outcome"],"comment":x["comment"][:300]}
                for x in self.list(limit)]

    def clear(self) -> int:
        with self._connect() as db:
            cur=db.execute("DELETE FROM feedback")
            return cur.rowcount
