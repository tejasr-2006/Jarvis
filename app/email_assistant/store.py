"""SQLite storage for reviewable email drafts. This store never sends email."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings

class EmailDraftStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            db_path = str(folder / "email_drafts.db")
        self.db_path = str(db_path)
        Path(self.db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS email_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT NOT NULL DEFAULT '',
                recipient TEXT NOT NULL DEFAULT '',
                subject TEXT NOT NULL DEFAULT '',
                original_email TEXT NOT NULL,
                intent TEXT NOT NULL,
                draft_body TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending_review',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            )""")

    @staticmethod
    def _row(row):
        return dict(row) if row else None

    def create(self, *, email_id: str, recipient: str, subject: str, original_email: str, intent: str, draft_body: str):
        with self._connect() as conn:
            cur = conn.execute("INSERT INTO email_drafts(email_id,recipient,subject,original_email,intent,draft_body) VALUES(?,?,?,?,?,?)",
                (email_id, recipient, subject, original_email, intent, draft_body))
            return self._row(conn.execute("SELECT * FROM email_drafts WHERE id=?", (cur.lastrowid,)).fetchone())

    def list(self, limit: int = 50):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM email_drafts ORDER BY id DESC LIMIT ?", (max(1, min(limit, 100)),)).fetchall()
            return [self._row(row) for row in rows]

    def get(self, draft_id: int):
        with self._connect() as conn:
            return self._row(conn.execute("SELECT * FROM email_drafts WHERE id=?", (draft_id,)).fetchone())

    def decide(self, draft_id: int, decision: str):
        if decision not in {"approved", "rejected"}:
            raise ValueError("Unsupported draft decision")
        with self._connect() as conn:
            cur = conn.execute("UPDATE email_drafts SET status=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND status='pending_review'", (decision, draft_id))
            if cur.rowcount != 1:
                return None
            return self._row(conn.execute("SELECT * FROM email_drafts WHERE id=?", (draft_id,)).fetchone())
