"""SQLite-backed recurring routine definitions and execution deduplication."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings


class RoutineStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = str(folder / "routines.db")
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
                CREATE TABLE IF NOT EXISTS routines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    time_local TEXT NOT NULL,
                    weekdays TEXT NOT NULL DEFAULT '0,1,2,3,4,5,6',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    last_fired_date TEXT
                )
            """)

    @staticmethod
    def _serialize(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["enabled"] = bool(item["enabled"])
        item["weekdays"] = [int(x) for x in item["weekdays"].split(",") if x != ""]
        return item

    def create(self, name: str, message: str, time_local: str, weekdays: list[int]) -> dict[str, Any]:
        days = ",".join(str(day) for day in sorted(set(weekdays)))
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO routines(name,message,time_local,weekdays) VALUES(?,?,?,?)",
                (name.strip(), message.strip(), time_local, days),
            )
            row = conn.execute("SELECT * FROM routines WHERE id=?", (cur.lastrowid,)).fetchone()
            return self._serialize(row)

    def list(self, include_disabled: bool = True) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if include_disabled:
                rows = conn.execute("SELECT * FROM routines ORDER BY time_local,id").fetchall()
            else:
                rows = conn.execute("SELECT * FROM routines WHERE enabled=1 ORDER BY time_local,id").fetchall()
            return [self._serialize(row) for row in rows]

    def get(self, routine_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM routines WHERE id=?", (routine_id,)).fetchone()
            return self._serialize(row) if row else None

    def set_enabled(self, routine_id: int, enabled: bool) -> dict[str, Any] | None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE routines SET enabled=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
                (int(enabled), routine_id),
            )
            row = conn.execute("SELECT * FROM routines WHERE id=?", (routine_id,)).fetchone()
            return self._serialize(row) if row else None

    def delete(self, routine_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM routines WHERE id=?", (routine_id,))
            return cur.rowcount > 0

    def due(self, now):
        """Return enabled routines due at the current local minute and not fired today."""
        today = now.date().isoformat()
        weekday = now.weekday()
        minute = now.strftime("%H:%M")
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM routines
                WHERE enabled=1 AND time_local=? AND last_fired_date IS NOT ?
                ORDER BY id
            """, (minute, today)).fetchall()
            due_rows = []
            for row in rows:
                routine = self._serialize(row)
                if weekday in routine["weekdays"]:
                    due_rows.append(routine)
            return due_rows

    def mark_fired(self, routine_id: int, local_date: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """UPDATE routines SET last_fired_date=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                   WHERE id=? AND enabled=1 AND (last_fired_date IS NULL OR last_fired_date<>?)""",
                (local_date, routine_id, local_date),
            )
            return cur.rowcount == 1
