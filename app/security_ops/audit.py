"""Minimal local audit trail; intentionally excludes headers, query strings, and bodies."""
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from app.config import settings

class AuditStore:
    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            directory = Path(settings.JARVIS_DATA_DIR).expanduser()
            directory.mkdir(parents=True, exist_ok=True)
            db_path = directory / "audit.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    method TEXT NOT NULL,
                    route TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    request_id TEXT NOT NULL
                )
            """)

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def record(self, method: str, route: str, status_code: int,
               duration_ms: int, request_id: str) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO audit_events(created_at,method,route,status_code,duration_ms,request_id) "
                "VALUES(?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 method[:12], route[:180], int(status_code), max(0, int(duration_ms)), request_id[:64]),
            )

    def list(self, limit: int = 100, offset: int = 0) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT id,created_at,method,route,status_code,duration_ms,request_id "
                "FROM audit_events ORDER BY id DESC LIMIT ? OFFSET ?",
                (max(1, min(int(limit), 200)), max(0, int(offset))),
            ).fetchall()
        return [dict(row) for row in rows]
