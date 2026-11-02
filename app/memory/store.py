"""Local SQLite memory store. No network calls are made by this module."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from app.config import settings


class MemoryStore:
    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            data_dir = Path(settings.JARVIS_DATA_DIR).expanduser()
            data_dir.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(data_dir, 0o700)
            except OSError:
                # Windows or restricted filesystems may not support POSIX modes.
                pass
            db_path = str(data_dir / "memory.db")
        self.db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        parent = Path(self.db_path).expanduser().parent
        parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    tags TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                )
            """)
        try:
            os.chmod(self.db_path, 0o600)
        except OSError:
            pass

    @staticmethod
    def _fact(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["tags"] = [tag for tag in item["tags"].split(",") if tag]
        return item

    def get_preferences(self) -> dict[str, bool]:
        """Return persisted memory controls, falling back to privacy-safe config defaults."""
        defaults = {
            "context_enabled": True,
            "cloud_context_enabled": bool(settings.MEMORY_CONTEXT_TO_CLOUD),
            "conversation_storage_enabled": bool(settings.MEMORY_STORE_CONVERSATIONS),
        }
        with self._connect() as conn:
            rows = conn.execute("SELECT key, value FROM memory_preferences").fetchall()
        for row in rows:
            if row["key"] in defaults:
                defaults[row["key"]] = row["value"] == "true"
        return defaults

    def update_preferences(self, preferences: dict[str, bool]) -> dict[str, bool]:
        """Persist only explicitly supplied controls."""
        allowed = {"context_enabled", "cloud_context_enabled", "conversation_storage_enabled"}
        with self._connect() as conn:
            for key, value in preferences.items():
                if key not in allowed:
                    continue
                conn.execute(
                    "INSERT INTO memory_preferences(key, value, updated_at) VALUES (?, ?, "
                    "strftime('%Y-%m-%dT%H:%M:%fZ','now')) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value, "
                    "updated_at=excluded.updated_at",
                    (key, "true" if value else "false"),
                )
        return self.get_preferences()

    def counts(self) -> dict[str, int]:
        with self._connect() as conn:
            facts = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
            conversations = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        return {"facts": int(facts), "saved_conversations": int(conversations)}

    def create_fact(self, title: str, content: str, category: str, tags: list[str]) -> dict[str, Any]:
        normalized_tags = ",".join(dict.fromkeys(t.strip().lower() for t in tags if t.strip()))
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO facts(title, content, category, tags) VALUES (?, ?, ?, ?)",
                (title.strip(), content.strip(), category.strip().lower(), normalized_tags),
            )
            row = conn.execute("SELECT * FROM facts WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return self._fact(row)

    def list_facts(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM facts ORDER BY updated_at DESC, id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [self._fact(row) for row in rows]

    def search_facts(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        # Parameterized LIKE search; user input is never interpolated into SQL.
        terms = [term.strip() for term in query.split() if term.strip()]
        if not terms:
            return []
        clauses, params = [], []
        for term in terms:
            clauses.append("(title LIKE ? OR content LIKE ? OR category LIKE ? OR tags LIKE ?)")
            needle = f"%{term}%"
            params.extend([needle, needle, needle, needle])
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM facts WHERE " + " AND ".join(clauses) +
                " ORDER BY updated_at DESC, id DESC LIMIT ?",
                params,
            ).fetchall()
            return [self._fact(row) for row in rows]

    def update_fact(self, fact_id: int, title: str, content: str, category: str, tags: list[str]) -> dict[str, Any] | None:
        normalized_tags = ",".join(dict.fromkeys(t.strip().lower() for t in tags if t.strip()))
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE facts SET title=?, content=?, category=?, tags=?, "
                "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
                (title.strip(), content.strip(), category.strip().lower(), normalized_tags, fact_id),
            )
            if cursor.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM facts WHERE id=?", (fact_id,)).fetchone()
            return self._fact(row)

    def delete_fact(self, fact_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
            return cursor.rowcount > 0

    def delete_all_facts(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM facts")
            return cursor.rowcount

    def create_conversation(self, user_message: str, assistant_message: str) -> dict[str, Any]:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO conversations(user_message, assistant_message) VALUES (?, ?)",
                (user_message.strip(), assistant_message.strip()),
            )
            row = conn.execute(
                "SELECT id, user_message, assistant_message, created_at FROM conversations WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
            return dict(row)

    def list_conversations(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, user_message, assistant_message, created_at FROM conversations "
                "ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_all_conversations(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM conversations")
            return cursor.rowcount
