"""Local searchable knowledge library with bounded text chunks and keyword ranking."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import math
import os
import re
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings

_WORDS = re.compile(r"[A-Za-z0-9_'-]{2,}", re.UNICODE)


def _terms(text: str) -> list[str]:
    return list(dict.fromkeys(word.casefold() for word in _WORDS.findall(text)))


def _fts_query(terms: list[str]) -> str:
    return " OR ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms)


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _chunks(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    out, start = [], 0
    while start < len(normalized):
        end = min(len(normalized), start + size)
        if end < len(normalized):
            boundary = normalized.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        out.append(normalized[start:end].strip())
        if end >= len(normalized):
            break
        start = max(start + 1, end - overlap)
    return out


class KnowledgeStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            folder = Path(settings.JARVIS_DATA_DIR).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(folder, 0o700)
            except OSError:
                pass
            db_path = str(folder / "knowledge.db")
        self.db_path = db_path
        Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))""")
            conn.execute("""CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL)""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id, chunk_index)")
            conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                title, content, tokenize='unicode61 remove_diacritics 2')""")
            conn.execute("""DELETE FROM knowledge_fts
                WHERE rowid NOT IN (SELECT id FROM chunks)""")
            conn.execute("""INSERT INTO knowledge_fts(rowid,title,content)
                SELECT c.id,d.title,c.content FROM chunks c
                JOIN documents d ON d.id=c.document_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM knowledge_fts f WHERE f.rowid=c.id
                )""")
        try:
            os.chmod(db_path, 0o600)
        except OSError:
            pass

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def add_document(self, title: str, content: str, source: str = "manual") -> dict[str, Any]:
        title, content, source = title.strip(), content.strip(), source.strip() or "manual"
        chunks = _chunks(content)
        with self._connect() as conn:
            cur = conn.execute("INSERT INTO documents(title,content,source) VALUES(?,?,?)",
                               (title, content, source))
            doc_id = cur.lastrowid
            conn.executemany("INSERT INTO chunks(document_id,chunk_index,content) VALUES(?,?,?)",
                             [(doc_id, i, chunk) for i, chunk in enumerate(chunks)])
            conn.execute("""INSERT INTO knowledge_fts(rowid,title,content)
                SELECT c.id,d.title,c.content FROM chunks c
                JOIN documents d ON d.id=c.document_id WHERE d.id=?""", (doc_id,))
            row = conn.execute("SELECT id,title,source,created_at,updated_at FROM documents WHERE id=?",
                               (doc_id,)).fetchone()
        return {**dict(row), "chunk_count": len(chunks), "character_count": len(content)}

    def list_documents(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("""SELECT d.id,d.title,d.source,d.created_at,d.updated_at,
                COUNT(c.id) AS chunk_count,LENGTH(d.content) AS character_count
                FROM documents d LEFT JOIN chunks c ON c.document_id=d.id
                GROUP BY d.id ORDER BY d.updated_at DESC,d.id DESC LIMIT ? OFFSET ?""",
                (limit, offset)).fetchall()
        return [dict(row) for row in rows]

    def get_document(self, document_id: int, include_content: bool = True) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["chunk_count"] = conn.execute(
                "SELECT COUNT(*) FROM chunks WHERE document_id=?", (document_id,)).fetchone()[0]
            if not include_content:
                result.pop("content", None)
            return result

    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        source: str | None = None,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> list[dict[str, Any]]:
        query_terms = _terms(query)
        filters = ["1 = 1"]
        filter_params: list[Any] = []
        if source:
            filters.append("d.source = ?")
            filter_params.append(source)
        if updated_after is not None:
            filters.append("d.updated_at >= ?")
            filter_params.append(_utc_iso(updated_after))
        if updated_before is not None:
            filters.append("d.updated_at <= ?")
            filter_params.append(_utc_iso(updated_before))
        filter_sql = " AND ".join(filters)

        with self._connect() as conn:
            rows = conn.execute(f"""SELECT c.id AS chunk_id,c.document_id,c.chunk_index,c.content,
                d.title,d.source,d.updated_at FROM chunks c JOIN documents d ON d.id=c.document_id
                WHERE {filter_sql}
                ORDER BY d.updated_at DESC,c.chunk_index ASC""", filter_params).fetchall()
            if not rows:
                return []

            base_rows = [dict(row) for row in rows]
            if not query_terms:
                ranked = base_rows[:]
                for item in ranked:
                    item.update(score=0.0, bm25_score=0.0, vector_score=0.0,
                                matched_terms=[], retrieval_mode="metadata_fallback")
            else:
                fts_rows = conn.execute(f"""SELECT c.id AS chunk_id,
                    bm25(knowledge_fts, 3.0, 1.0) AS bm25_rank
                    FROM knowledge_fts JOIN chunks c ON c.id=knowledge_fts.rowid
                    JOIN documents d ON d.id=c.document_id
                    WHERE knowledge_fts MATCH ? AND {filter_sql}
                    ORDER BY bm25_rank ASC""",
                    [_fts_query(query_terms), *filter_params]).fetchall()

                bm25_scores = {
                    row["chunk_id"]: max(0.0, -float(row["bm25_rank"]))
                    for row in fts_rows
                }
                query_counts = Counter(_WORDS.findall(query.casefold()))
                doc_counts = {
                    item["chunk_id"]: Counter(
                        _WORDS.findall((item["title"] + " " + item["content"]).casefold())
                    )
                    for item in base_rows
                }
                document_frequency = Counter(
                    term for counts in doc_counts.values() for term in counts
                )
                corpus_size = len(base_rows)
                inverse_frequency = {
                    term: math.log((corpus_size + 1) / (document_frequency[term] + 1)) + 1
                    for term in query_terms
                }
                query_vector = {
                    term: (1 + math.log(count)) * inverse_frequency[term]
                    for term, count in query_counts.items()
                    if term in inverse_frequency
                }
                query_norm = math.sqrt(sum(weight * weight for weight in query_vector.values()))
                cosine_scores: dict[int, float] = {}
                if query_norm:
                    for item in base_rows:
                        counts = Counter(
                            _WORDS.findall((item["title"] + " " + item["content"]).casefold())
                        )
                        vector = {
                            term: (1 + math.log(count)) * inverse_frequency[term]
                            for term, count in counts.items()
                            if term in inverse_frequency
                        }
                        norm = math.sqrt(sum(weight * weight for weight in vector.values()))
                        if norm:
                            dot = sum(weight * vector.get(term, 0.0)
                                      for term, weight in query_vector.items())
                            cosine_scores[item["chunk_id"]] = dot / (query_norm * norm)

                bm25_order = [row["chunk_id"] for row in fts_rows]
                cosine_order = sorted(cosine_scores, key=lambda key: (
                    -cosine_scores[key],
                    next(item["document_id"] for item in base_rows if item["chunk_id"] == key),
                    next(item["chunk_index"] for item in base_rows if item["chunk_id"] == key),
                ))
                row_by_id = {item["chunk_id"]: item for item in base_rows}
                fused: dict[int, float] = {}
                for order in (bm25_order, cosine_order):
                    for rank, chunk_id in enumerate(order, 1):
                        fused[chunk_id] = fused.get(chunk_id, 0.0) + 0.5 / (60 + rank)

                ranked = []
                for chunk_id, rrf_score in fused.items():
                    item = row_by_id[chunk_id]
                    counts = doc_counts[chunk_id]
                    item.update(
                        score=round(rrf_score, 6),
                        bm25_score=round(bm25_scores.get(chunk_id, 0.0), 6),
                        vector_score=round(cosine_scores.get(chunk_id, 0.0), 6),
                        matched_terms=[term for term in query_terms if counts.get(term, 0)],
                        retrieval_mode="hybrid",
                    )
                    ranked.append(item)
                ranked.sort(key=lambda item: (
                    -item["score"], -item["bm25_score"], -item["vector_score"],
                    item["document_id"], item["chunk_index"],
                ))

            results = ranked[:limit]
            for item in results:
                context_rows = conn.execute("""SELECT chunk_index,content FROM chunks
                    WHERE document_id=? AND chunk_index BETWEEN ? AND ? AND chunk_index != ?
                    ORDER BY chunk_index""",
                    (item["document_id"], item["chunk_index"] - 1, item["chunk_index"] + 1,
                     item["chunk_index"])).fetchall()
                item["context"] = [
                    {"chunk_index": row["chunk_index"], "content": row["content"][:500]}
                    for row in context_rows
                ]
        return results

    def delete_document(self, document_id: int) -> bool:
        with self._connect() as conn:
            conn.execute("""DELETE FROM knowledge_fts WHERE rowid IN
                (SELECT id FROM chunks WHERE document_id=?)""", (document_id,))
            cur = conn.execute("DELETE FROM documents WHERE id=?", (document_id,))
            return cur.rowcount > 0

    def clear(self) -> int:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            conn.execute("DELETE FROM knowledge_fts")
            conn.execute("DELETE FROM documents")
            return count
