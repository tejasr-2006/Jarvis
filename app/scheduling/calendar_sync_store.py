"""Local idempotency/audit store for schedule-to-calendar synchronization."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings


class CalendarSyncStore:
    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = folder / "calendar_sync.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS syncs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK(status IN ('syncing','synced','partial','failed')),
                event_ids TEXT NOT NULL DEFAULT '[]',
                result TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            )""")

    def _connect(self):
        db=sqlite3.connect(self.db_path,timeout=10)
        db.row_factory=sqlite3.Row
        return db

    @staticmethod
    def _decode(row):
        if not row: return None
        item=dict(row)
        item["event_ids"]=json.loads(item["event_ids"])
        item["result"]=json.loads(item["result"])
        return item

    def get(self, proposal_id: int):
        with self._connect() as db:
            row=db.execute("SELECT * FROM syncs WHERE proposal_id=?",(proposal_id,)).fetchone()
        return self._decode(row)

    def begin(self, proposal_id: int):
        """Atomic unique insert prevents duplicate sync attempts for a proposal."""
        try:
            with self._connect() as db:
                cur=db.execute("INSERT INTO syncs(proposal_id,status) VALUES(?,'syncing')",(proposal_id,))
                row=db.execute("SELECT * FROM syncs WHERE id=?",(cur.lastrowid,)).fetchone()
            return self._decode(row)
        except sqlite3.IntegrityError:
            return None

    def update(self, proposal_id: int, status: str, event_ids: list[str], result: dict[str, Any]):
        with self._connect() as db:
            db.execute("UPDATE syncs SET status=?,event_ids=?,result=?,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE proposal_id=?",
                       (status,json.dumps(event_ids),json.dumps(result,ensure_ascii=False),proposal_id))
            row=db.execute("SELECT * FROM syncs WHERE proposal_id=?",(proposal_id,)).fetchone()
        return self._decode(row)
