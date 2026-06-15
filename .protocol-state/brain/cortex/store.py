"""SQLite storage and vector search for Cortex."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .errors import DependencyError, QueryUnavailable


@dataclass
class Chunk:
    id: str
    source_path: str
    source_type: str
    line_start: int
    line_end: int
    content_hash: str
    recorded_date: str
    text: str
    trust: str
    suspect: bool = False
    mem_type: str | None = None
    agent: str | None = None
    refs: list[str] | None = None


class Store:
    def __init__(self, db_path: str | Path, *, dim: int = 384, vector_backend: str = "sqlite_vec"):
        self.db_path = Path(db_path)
        self.dim = dim
        self.vector_backend = vector_backend
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        if self.vector_backend == "sqlite_vec":
            self._load_sqlite_vec(conn)
        return conn

    def _load_sqlite_vec(self, conn: sqlite3.Connection) -> None:
        try:
            import sqlite_vec
        except Exception as exc:  # pragma: no cover - optional package
            raise DependencyError("sqlite-vec is not installed; install requirements-brain.txt or use STUB model for tests") from exc
        conn.enable_load_extension(True)
        try:
            sqlite_vec.load(conn)
        finally:
            conn.enable_load_extension(False)

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute("PRAGMA user_version = 1")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                  id TEXT PRIMARY KEY,
                  source_path TEXT NOT NULL,
                  source_type TEXT NOT NULL,
                  line_start INTEGER NOT NULL,
                  line_end INTEGER NOT NULL,
                  content_hash TEXT NOT NULL,
                  recorded_date TEXT NOT NULL,
                  text TEXT NOT NULL,
                  trust TEXT NOT NULL,
                  suspect INTEGER NOT NULL DEFAULT 0,
                  mem_type TEXT,
                  agent TEXT,
                  refs TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rowmap (
                  rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                  chunk_id TEXT UNIQUE NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                  key TEXT PRIMARY KEY,
                  value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS source_state (
                  source_path TEXT PRIMARY KEY,
                  mtime_ns INTEGER NOT NULL,
                  size INTEGER NOT NULL,
                  indexed_at TEXT NOT NULL
                )
                """
            )
            if self.vector_backend == "sqlite_vec":
                conn.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(embedding float[{self.dim}])")
            else:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chunk_vectors (
                      rowid INTEGER PRIMARY KEY,
                      embedding TEXT NOT NULL
                    )
                    """
                )

    def count(self) -> int:
        self.init_schema()
        with self.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])

    def vec_version(self) -> str:
        if self.vector_backend != "sqlite_vec":
            return "stub"
        with self.connect() as conn:
            row = conn.execute("SELECT vec_version()").fetchone()
            return str(row[0])

    def set_meta(self, key: str, value: str) -> None:
        self.init_schema()
        with self.connect() as conn:
            conn.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)", (key, value))

    def get_meta(self, key: str) -> str | None:
        self.init_schema()
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
            return str(row[0]) if row else None

    def source_state(self, source_path: str) -> tuple[int, int] | None:
        self.init_schema()
        with self.connect() as conn:
            row = conn.execute("SELECT mtime_ns, size FROM source_state WHERE source_path = ?", (source_path,)).fetchone()
            return (int(row["mtime_ns"]), int(row["size"])) if row else None

    def set_source_state(self, source_path: str, *, mtime_ns: int, size: int, indexed_at: str) -> None:
        self.init_schema()
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO source_state(source_path, mtime_ns, size, indexed_at) VALUES (?, ?, ?, ?)",
                (source_path, mtime_ns, size, indexed_at),
            )

    def upsert(self, items: Iterable[tuple[Chunk, list[float]]]) -> int:
        self.init_schema()
        changed = 0
        with self.connect() as conn:
            for chunk, vector in items:
                if len(vector) != self.dim:
                    raise ValueError(f"embedding dimension mismatch: expected {self.dim}, got {len(vector)}")
                conn.execute("INSERT OR IGNORE INTO rowmap(chunk_id) VALUES (?)", (chunk.id,))
                rowid = int(conn.execute("SELECT rowid FROM rowmap WHERE chunk_id = ?", (chunk.id,)).fetchone()[0])
                conn.execute("DELETE FROM chunk_vectors WHERE rowid = ?", (rowid,))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO chunks (
                      id, source_path, source_type, line_start, line_end, content_hash,
                      recorded_date, text, trust, suspect, mem_type, agent, refs
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.id,
                        chunk.source_path,
                        chunk.source_type,
                        chunk.line_start,
                        chunk.line_end,
                        chunk.content_hash,
                        chunk.recorded_date,
                        chunk.text,
                        chunk.trust,
                        1 if chunk.suspect else 0,
                        chunk.mem_type,
                        chunk.agent,
                        json.dumps(chunk.refs or []),
                    ),
                )
                if self.vector_backend == "sqlite_vec":
                    import sqlite_vec

                    conn.execute("INSERT INTO chunk_vectors(rowid, embedding) VALUES (?, ?)", (rowid, sqlite_vec.serialize_float32(vector)))
                else:
                    conn.execute("INSERT INTO chunk_vectors(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(vector)))
                changed += 1
        return changed

    def delete_by_source(self, source_path: str) -> int:
        self.init_schema()
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT rowmap.rowid FROM rowmap JOIN chunks ON chunks.id = rowmap.chunk_id WHERE chunks.source_path = ?",
                (source_path,),
            ).fetchall()
            for row in rows:
                conn.execute("DELETE FROM chunk_vectors WHERE rowid = ?", (int(row[0]),))
            conn.execute("DELETE FROM rowmap WHERE chunk_id IN (SELECT id FROM chunks WHERE source_path = ?)", (source_path,))
            cur = conn.execute("DELETE FROM chunks WHERE source_path = ?", (source_path,))
            conn.execute("DELETE FROM source_state WHERE source_path = ?", (source_path,))
            return int(cur.rowcount or 0)

    def list_indexed_sources(self) -> list[str]:
        self.init_schema()
        with self.connect() as conn:
            rows = conn.execute("SELECT source_path FROM source_state WHERE source_path NOT LIKE 'memory:%'").fetchall()
            return [str(row[0]) for row in rows]

    def delete_source_state(self, source_path: str) -> None:
        self.init_schema()
        with self.connect() as conn:
            conn.execute("DELETE FROM source_state WHERE source_path = ?", (source_path,))

    def search(self, vector: list[float], *, k: int = 5, trust: list[str] | None = None) -> list[dict]:
        self.init_schema()
        if self.count() == 0:
            raise QueryUnavailable("Cortex DB is empty; run index first")
        trust = trust or ["trusted", "semi", "untrusted"]
        placeholders = ",".join("?" for _ in trust)
        if self.vector_backend == "sqlite_vec":
            return self._search_sqlite_vec(vector, k=k, trust=trust, placeholders=placeholders)
        return self._search_stub(vector, k=k, trust=trust, placeholders=placeholders)

    def _search_sqlite_vec(self, vector: list[float], *, k: int, trust: list[str], placeholders: str) -> list[dict]:
        import sqlite_vec

        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT chunks.*, distance
                FROM chunk_vectors
                JOIN rowmap ON rowmap.rowid = chunk_vectors.rowid
                JOIN chunks ON chunks.id = rowmap.chunk_id
                WHERE chunks.trust IN ({placeholders})
                AND chunk_vectors.embedding MATCH ?
                AND k = ?
                ORDER BY distance
                """,
                (*trust, sqlite_vec.serialize_float32(vector), k),
            ).fetchall()
            return [_row_to_result(row) for row in rows]

    def _search_stub(self, vector: list[float], *, k: int, trust: list[str], placeholders: str) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT chunks.*, chunk_vectors.embedding
                FROM chunks
                JOIN rowmap ON rowmap.chunk_id = chunks.id
                JOIN chunk_vectors ON chunk_vectors.rowid = rowmap.rowid
                WHERE chunks.trust IN ({placeholders})
                """,
                tuple(trust),
            ).fetchall()
        results = []
        for row in rows:
            embedding = json.loads(row["embedding"])
            result = _row_to_result(row)
            result["distance"] = 1.0 - _cosine(vector, embedding)
            results.append(result)
        return sorted(results, key=lambda item: item["distance"])[:k]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    an = math.sqrt(sum(x * x for x in a)) or 1.0
    bn = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (an * bn)


# A scope is always a 12-hex install_id, so a scoped key is exactly `@<12-hex>/<rel>`.
# Matching this precise shape avoids stripping a legitimate repo path like "@team/x.md".
_SCOPED_PREFIX_RE = re.compile(r"^@[0-9a-f]{12}/")


def _display_source(source_path: str) -> str:
    """Strip an install-scope prefix ('@<12-hex>/<rel>' -> '<rel>') for citations.

    BUG-CORTEX-005 (v9.3.0): shared-brain storage keys carry a '@<install-id>/' prefix;
    users want clean repo-relative provenance in query output, not the namespace.
    Unscoped keys (the default) and real paths that merely start with '@' are
    returned unchanged.
    """
    if _SCOPED_PREFIX_RE.match(source_path):
        return source_path.split("/", 1)[1]
    return source_path


def _row_to_result(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "text": row["text"],
        "source_path": _display_source(row["source_path"]),
        "line_start": int(row["line_start"]),
        "line_end": int(row["line_end"]),
        "source_type": row["source_type"],
        "trust": row["trust"],
        "suspect": bool(row["suspect"]),
        "recorded_date": row["recorded_date"],
        "distance": float(row["distance"]) if "distance" in row.keys() else 0.0,
    }
