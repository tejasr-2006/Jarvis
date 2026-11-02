"""Local SQLite audit store for user-approved computer actions."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from app.config import settings

def _db_path() -> Path:
    path = Path(settings.JARVIS_DATA_DIR).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path / "computer_actions.db"

class ComputerActionStore:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else _db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS computer_actions (
                    id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    target TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    executed_at TEXT,
                    result TEXT
                )
            """)

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _serialize(row):
        item = dict(row)
        if item.get("result"):
            try: item["result"] = json.loads(item["result"])
            except (ValueError, TypeError): pass
        return item

    def create(self, action_type: str, target: str) -> dict:
        item = {
            "id": uuid.uuid4().hex,
            "action_type": action_type,
            "target": target,
            "status": "proposed",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "executed_at": None,
            "result": None,
        }
        with self._connect() as db:
            db.execute(
                "INSERT INTO computer_actions (id, action_type, target, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (item["id"], action_type, target, item["status"], item["created_at"]),
            )
        return item

    def get(self, action_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM computer_actions WHERE id=?", (action_id,)).fetchone()
        return self._serialize(row) if row else None

    def update(self, action_id: str, status: str, result: dict | None = None) -> dict | None:
        executed_at = datetime.now(timezone.utc).isoformat(timespec="seconds") if status in {"executed", "failed"} else None
        with self._connect() as db:
            db.execute(
                "UPDATE computer_actions SET status=?, executed_at=?, result=? WHERE id=?",
                (status, executed_at, json.dumps(result) if result is not None else None, action_id),
            )
        return self.get(action_id)

    def list(self, limit: int = 50) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM computer_actions ORDER BY created_at DESC LIMIT ?",
                (max(1, min(limit, 200)),),
            ).fetchall()
        return [self._serialize(row) for row in rows]
