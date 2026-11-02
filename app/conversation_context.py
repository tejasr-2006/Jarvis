"""Local, bounded conversational context. Does not store tool result payloads."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from app.config import settings


class ConversationContextStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = str(folder / "conversation_context.db")
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
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_command TEXT NOT NULL,
                    intent TEXT NOT NULL DEFAULT 'unknown',
                    status TEXT NOT NULL DEFAULT 'unknown',
                    assistant_summary TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversation_session_id ON conversation_turns(session_id, id DESC)")

    def recent(self, session_id: str, limit: int | None = None) -> list[dict]:
        limit = max(1, min(limit or settings.CONVERSATION_CONTEXT_TURNS, 20))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id,session_id,user_command,intent,status,assistant_summary,created_at "
                "FROM conversation_turns WHERE session_id=? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def add_turn(self, session_id: str, user_command: str, intent: str,
                 status: str, assistant_summary: str) -> dict:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO conversation_turns(session_id,user_command,intent,status,assistant_summary) VALUES(?,?,?,?,?)",
                (session_id, user_command[:2000], intent[:100], status[:50], assistant_summary[:500]),
            )
            row = conn.execute("SELECT id,session_id,user_command,intent,status,assistant_summary,created_at FROM conversation_turns WHERE id=?", (cur.lastrowid,)).fetchone()
            # Keep only a bounded number of turns per session.
            conn.execute("""
                DELETE FROM conversation_turns WHERE session_id=? AND id NOT IN
                (SELECT id FROM conversation_turns WHERE session_id=? ORDER BY id DESC LIMIT 20)
            """, (session_id, session_id))
        return dict(row)

    def clear(self, session_id: str) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM conversation_turns WHERE session_id=?", (session_id,))
            return cur.rowcount

    def clear_all(self) -> int:
        """Delete all bounded conversational context stored for all sessions."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM conversation_turns")
            return cur.rowcount
