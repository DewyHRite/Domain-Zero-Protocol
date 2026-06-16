"""SQLite storage and vector search for Cortex."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .errors import DependencyError, QueryUnavailable, SchemaMismatchError, SchemaTooNewError

# PLAN-DESIGN-001 Phase 1 (v9.4.0): the highest Cortex storage schema this engine
# understands. PRAGMA user_version is the single canonical authority; metadata.schema_version
# is only a diagnostic mirror.
#   v1 = legacy chunk-addressed storage (v9.3.x)
#   v2 = content-addressed storage (v9.4.0+)
# Bumping this constant is how a future engine declares it can read the new schema.
SUPPORTED_SCHEMA = 2


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


def _make_ref_id(storage_key: str, line_start: int, content_hash: str) -> str:
    """PLAN-DESIGN-001 §3 (OQ5 RESOLVED): deterministic ref_id.

    ref_id = sha256(f"{storage_key}:{line_start}:{content_hash}")[:16]

    Deterministic identity is REQUIRED (not a preference): autoincrement breaks
    idempotent re-migration (duplicate refs on re-run), violates the
    UNIQUE(storage_key, line_start) constraint, and makes rollback→re-run cycles
    non-reproducible for parity.
    """
    return hashlib.sha256(
        f"{storage_key}:{line_start}:{content_hash}".encode()
    ).hexdigest()[:16]


class Store:
    def __init__(
        self,
        db_path: str | Path,
        *,
        dim: int = 384,
        vector_backend: str = "sqlite_vec",
        install_id: str | None = None,
    ):
        # SEC-CORTEX-009 (v9.3.4): dim is interpolated into DDL; reject anything that
        # is not a plain positive integer (bool is a subclass of int, so it must be
        # explicitly excluded to avoid CREATE VIRTUAL TABLE ... float[True]).
        if not isinstance(dim, int) or isinstance(dim, bool) or dim <= 0:
            raise ValueError(f"Store dim must be a positive integer, got {dim!r}")
        self.db_path = Path(db_path)
        self.dim = dim
        self.vector_backend = vector_backend
        # PLAN-DESIGN-001 §0 (Phase 3, v9.4.0): install-membership ledger.
        # When set, init_schema() stamps a row in cortex_installs so the migration
        # script can check whether all sharing engines are v9.3.4+.
        # When None (the default, and in most unit tests), ledger stamping is skipped
        # and no existing tests are affected.
        self._install_id: str | None = install_id
        self._schema_initialized: bool = False  # PERF (v9.3.4): memoize schema guard
        self._active_schema: int = 0  # set after init_schema(); drives method dispatch
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        # SEC-001 (PLAN-DESIGN-001 §4/§6): set busy_timeout before any lock acquisition
        # so write transactions do not silently fail-fast on contention.
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # busy_timeout via PRAGMA (belt-and-suspenders: timeout= covers connect; PRAGMA
        # covers any WAL mode set by a concurrent engine).
        conn.execute("PRAGMA busy_timeout = 10000")
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

    @staticmethod
    def _read_meta_schema_version(conn: sqlite3.Connection) -> int | None:
        """Return metadata.schema_version, or None if the table/key is absent
        (fresh DB, or a pre-v9.3.4 DB that never wrote the mirror)."""
        has_meta = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'metadata'"
        ).fetchone()
        if has_meta is None:
            return None
        row = conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()
        if row is None:
            return None
        try:
            return int(row[0])
        except (TypeError, ValueError) as exc:
            # SEC-CORTEX-008 (v9.3.4): cap the echoed value so a crafted metadata
            # row cannot produce unbounded / log-injecting error output.
            raise SchemaMismatchError(
                f"metadata.schema_version is not an integer: {str(row[0])[:64]!r}"
            ) from exc

    def _assert_schema_compatible(self, conn: sqlite3.Connection) -> int:
        """Preflight guard (v9.3.4+). Fail closed on a too-new or inconsistent DB
        BEFORE any table creation or write. Returns the current user_version.

        This is the single chokepoint: every public instance method AND every
        module-level function that receives a Store calls init_schema() first,
        so the guard fires before any DB op.
        """
        current = int(conn.execute("PRAGMA user_version").fetchone()[0])
        if current > SUPPORTED_SCHEMA:
            # UX (Nobara P1-A, v9.3.4): actionable shared-install upgrade guidance.
            raise SchemaTooNewError(
                f"Cortex DB schema v{current} is newer than this engine supports "
                f"(v{SUPPORTED_SCHEMA}).\n\n"
                f"  The shared brain was upgraded by a newer DZP install; this install\n"
                f"  cannot read or write it until you upgrade.\n\n"
                f"  To fix:\n"
                f"    1. Upgrade THIS install to the DZP version that wrote schema "
                f"v{current} (v9.4.0+).\n"
                f"    2. Run `brain status` to confirm access is restored.\n"
                f"    3. Re-run your command.\n\n"
                f"  Cortex recall is unavailable on this install until then, but your\n"
                f"  workflow continues (Cortex is fail-soft).\n\n"
                f"  DB location : {self.db_path}\n"
                f"  This engine : schema v{SUPPORTED_SCHEMA}  |  DB requires: schema v{current}"
            )
        mirror = self._read_meta_schema_version(conn)
        if mirror is not None and mirror != current:
            # UX (Nobara P1-B, v9.3.4): a partially-migrated DB is recoverable — show exits.
            raise SchemaMismatchError(
                f"Cortex DB schema markers disagree (partially migrated or interrupted).\n\n"
                f"  PRAGMA user_version     : {current}\n"
                f"  metadata.schema_version : {mirror}\n\n"
                f"  The database is in an inconsistent state; refusing to operate (fail-closed).\n\n"
                f"  To recover:\n"
                f"    - Full reset (destroys the local index; re-run `brain index` after):\n"
                f"        brain reset --yes\n"
                f"    - (v9.4.0+) roll back the migration:\n"
                f"        python .protocol-state/migrate_cortex_storage_9_4.py --rollback\n\n"
                f"  DB location: {self.db_path}"
            )
        return current

    def init_schema(self) -> None:
        # PERF (v9.3.4): memoize. The guard still fires on first call because
        # _schema_initialized starts False. Subsequent calls return immediately,
        # avoiding a connect + PRAGMA + sqlite_master round-trip per public op.
        # CRITICAL: the fail-closed schema guard (SchemaTooNewError) is preserved
        # on the first call because we only set the flag AFTER a successful pass.
        if self._schema_initialized:
            return
        with self.connect() as conn:
            current = self._assert_schema_compatible(conn)
            # --- Dispatch on current schema version ---
            if current == 0:
                # Fresh DB: initialize as v2 (content-addressed).
                # SEC-001 (PLAN-DESIGN-001 §4/§6): wrap DDL in BEGIN IMMEDIATE so no
                # concurrent writer can see a partially-created schema.
                conn.execute("BEGIN IMMEDIATE")
                self._create_v2_schema(conn)
                # PLAN-DESIGN-001 §0 (Phase 3): create ledger in v2-path.
                self._create_installs_ledger(conn)
                conn.execute(f"PRAGMA user_version = {SUPPORTED_SCHEMA}")
                conn.execute(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', ?)",
                    (str(SUPPORTED_SCHEMA),),
                )
                self._stamp_install(conn)
                conn.execute("COMMIT")
                self._active_schema = SUPPORTED_SCHEMA  # = 2

            elif current == 1:
                # Legacy v1 DB with real data. MUST NOT auto-upgrade to v2 — that is
                # the Phase 3 migration's job. Auto-stamping v1→v2 without migrating
                # data is the corruption vector (PLAN-DESIGN-001 §3, §5 Phase 1 note).
                # Keep v1 tables, keep user_version = 1, keep running on v1 paths.
                # Backfill the mirror if it is absent (pre-v9.3.4 DB).
                # PLAN-DESIGN-001 §0 (Phase 3): also create ledger on the v1-path so
                # the table exists regardless of DB schema.
                mirror = self._read_meta_schema_version(conn)
                conn.execute("BEGIN IMMEDIATE")
                if mirror is None:
                    # SEC-CORTEX-015 (Phase 1 review): wrap the backfill write in
                    # BEGIN IMMEDIATE for consistency with every other write path.
                    conn.execute(
                        "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', '1')"
                    )
                self._create_installs_ledger(conn)
                self._stamp_install(conn)
                conn.execute("COMMIT")
                self._active_schema = 1

            elif current == 2:
                # Already a v2 DB: ensure v2 tables are present (idempotent re-init).
                # This handles the case where a second Store opens an existing v2 DB.
                conn.execute("BEGIN IMMEDIATE")
                self._create_v2_schema(conn)
                # PLAN-DESIGN-001 §0 (Phase 3): ensure ledger exists in v2-path too
                # (idempotent — CREATE TABLE IF NOT EXISTS).
                self._create_installs_ledger(conn)
                self._stamp_install(conn)
                conn.execute("COMMIT")
                # Mirror is already correct (set at v2 init time).
                self._active_schema = 2

            # current > SUPPORTED_SCHEMA is already handled by _assert_schema_compatible
            # (raises SchemaTooNewError before reaching here).

        # Only mark initialized AFTER a successful pass — if _assert_schema_compatible
        # raised (SchemaTooNewError / SchemaMismatchError), we never reach here, so the
        # flag stays False and the guard will re-fire correctly on the next call.
        self._schema_initialized = True

    # -------------------------------------------------------------------------
    # cortex_installs ledger helpers (PLAN-DESIGN-001 §0, Phase 3, v9.4.0)
    # -------------------------------------------------------------------------

    @staticmethod
    def _create_installs_ledger(conn: sqlite3.Connection) -> None:
        """Create cortex_installs table (idempotent).

        PLAN-DESIGN-001 §0: the install-membership ledger is created in BOTH the
        v1-path and v2-path of init_schema so it exists regardless of DB schema.
        For a legacy v1 DB this call creates the ledger table WITHOUT touching any
        v1 data tables.

        Schema:
            install_id       TEXT PK  — stable per-repo/per-group id (12-hex from paths.install_id)
            supported_schema INTEGER  — SUPPORTED_SCHEMA constant at write time
            protocol_version TEXT     — optional DZP version string (may be NULL)
            last_seen        TEXT     — UTC ISO-8601 timestamp, updated on every engine run

        HONEST LIMITATION: this ledger only records engines that HAVE this code
        (v9.4.0+). Pre-v9.3.4 engines never write a row; the v9.3.4 too-new guard
        is the actual mixed-version protection for guard-bearing installs. The ledger
        is best-effort detection of v9.4.0+ peers — useful for migration pre-flight
        but not a complete census of all engines sharing the DB.
        """
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cortex_installs (
              install_id       TEXT PRIMARY KEY,
              supported_schema INTEGER NOT NULL,
              protocol_version TEXT,
              last_seen        TEXT NOT NULL
            )
            """
        )

    def _stamp_install(self, conn: sqlite3.Connection, *, protocol_version: str | None = None) -> None:
        """Upsert this engine's row into cortex_installs.

        Called inside the init_schema transaction ONLY when self._install_id is set.
        When _install_id is None (most unit tests, callers without a repo root),
        this is a no-op so existing tests are unaffected.
        """
        if self._install_id is None:
            return
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO cortex_installs(install_id, supported_schema, protocol_version, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(install_id) DO UPDATE SET
              supported_schema = excluded.supported_schema,
              protocol_version = excluded.protocol_version,
              last_seen        = excluded.last_seen
            """,
            (self._install_id, SUPPORTED_SCHEMA, protocol_version, now),
        )

    def installs_ledger(self) -> list[dict]:
        """Return all rows from cortex_installs as a list of dicts.

        Returns an empty list if the ledger table does not exist (e.g., a pre-v9.4.0
        DB that was never stamped). The ledger is best-effort — absence of a row does
        NOT mean an engine is absent (see _create_installs_ledger docstring).
        """
        self.init_schema()
        with self.connect() as conn:
            has_table = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cortex_installs'"
            ).fetchone()
            if has_table is None:
                return []
            rows = conn.execute(
                "SELECT install_id, supported_schema, protocol_version, last_seen FROM cortex_installs"
            ).fetchall()
        return [
            {
                "install_id": str(r[0]),
                "supported_schema": int(r[1]),
                "protocol_version": r[2],
                "last_seen": str(r[3]),
            }
            for r in rows
        ]

    # -------------------------------------------------------------------------
    # v2 DDL helpers
    # -------------------------------------------------------------------------

    def _create_v2_schema(self, conn: sqlite3.Connection) -> None:
        """Create (idempotent) the v2 content-addressed schema tables and indexes.

        Must be called inside an already-begun transaction (BEGIN IMMEDIATE) so
        the DDL batch is atomic. Uses CREATE TABLE IF NOT EXISTS / CREATE INDEX IF
        NOT EXISTS for idempotency.
        """
        # --- Core tables ---
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS content (
              content_hash TEXT PRIMARY KEY,
              vector_rowid  INTEGER UNIQUE NOT NULL,
              text          TEXT NOT NULL,
              dim           INTEGER NOT NULL,
              model         TEXT NOT NULL,
              created_at    TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS content_refs (
              ref_id       TEXT PRIMARY KEY,
              content_hash TEXT NOT NULL,
              storage_key  TEXT NOT NULL,
              source_type  TEXT NOT NULL,
              line_start   INTEGER NOT NULL,
              line_end     INTEGER NOT NULL,
              trust        TEXT NOT NULL,
              suspect      INTEGER NOT NULL DEFAULT 0,
              mem_type     TEXT,
              agent        TEXT,
              recorded_date TEXT NOT NULL,
              refs         TEXT,
              UNIQUE (storage_key, line_start)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
              key   TEXT PRIMARY KEY,
              value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS source_state (
              source_path TEXT PRIMARY KEY,
              mtime_ns    INTEGER NOT NULL,
              size        INTEGER NOT NULL,
              indexed_at  TEXT NOT NULL
            )
            """
        )

        # --- content_vectors: vec0 virtual table (or stub fallback) ---
        if self.vector_backend == "sqlite_vec":
            conn.execute(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS content_vectors USING vec0(embedding float[{self.dim}])"
            )
        else:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS content_vectors (
                  rowid     INTEGER PRIMARY KEY,
                  embedding TEXT NOT NULL
                )
                """
            )

        # --- Required indexes (PLAN-DESIGN-001 §3, Todo + Maki all-hands) ---
        # idx_content_refs_content_hash: ref-count delete path + doctor/dedup;
        # without it every delete full-scans content_refs.
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_content_refs_content_hash ON content_refs(content_hash)"
        )
        # idx_content_refs_storage_key: source orphan cleanup (delete all refs for a storage_key).
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_content_refs_storage_key ON content_refs(storage_key)"
        )
        # idx_content_refs_hash_trust: covering index for the trust-filtered query join
        # (vec kNN -> content -> refs).
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_content_refs_hash_trust ON content_refs(content_hash, trust)"
        )

    # -------------------------------------------------------------------------
    # Public API — dispatches on self._active_schema
    # -------------------------------------------------------------------------

    def count(self) -> int:
        self.init_schema()
        with self.connect() as conn:
            if self._active_schema == 2:
                return int(conn.execute("SELECT COUNT(*) FROM content_refs").fetchone()[0])
            # v1 legacy path
            return int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])

    def vec_version(self) -> str:
        # SEC-CORTEX-007 (v9.3.4): funnel through the schema guard like every other
        # public method. Without this, an old engine could open a connection to a
        # too-new/mismatched DB here, falsifying the "single chokepoint" invariant.
        self.init_schema()
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
        if self._active_schema == 2:
            return self._upsert_v2(items)
        return self._upsert_v1(items)

    def delete_by_source(self, source_path: str) -> int:
        self.init_schema()
        if self._active_schema == 2:
            return self._delete_by_source_v2(source_path)
        return self._delete_by_source_v1(source_path)

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
        trust = trust or ["trusted", "semi", "untrusted"]
        placeholders = ",".join("?" for _ in trust)

        if self._active_schema == 2:
            return self._search_v2(vector, k=k, trust=trust, placeholders=placeholders)

        # v1 legacy path
        # PERF (v9.3.4): replace the count() round-trip with a cheaper existence check.
        with self.connect() as conn:
            _exists = conn.execute("SELECT 1 FROM chunks LIMIT 1").fetchone()
        if _exists is None:
            raise QueryUnavailable("Cortex DB is empty; run index first")
        if self.vector_backend == "sqlite_vec":
            return self._search_sqlite_vec_v1(vector, k=k, trust=trust, placeholders=placeholders)
        return self._search_stub_v1(vector, k=k, trust=trust, placeholders=placeholders)

    # -------------------------------------------------------------------------
    # v2 storage methods
    # -------------------------------------------------------------------------

    def _upsert_v2(self, items: Iterable[tuple[Chunk, list[float]]]) -> int:
        """Content-addressed upsert: one content/vector row per distinct content_hash;
        one content_refs row per (storage_key, line_start) occurrence.

        SEC-001 (PLAN-DESIGN-001 §4/§6): wrap each chunk in BEGIN IMMEDIATE so
        concurrent writers cannot interleave between the content existence check
        and the vector insert.
        """
        changed = 0
        for chunk, vector in items:
            if len(vector) != self.dim:
                raise ValueError(f"embedding dimension mismatch: expected {self.dim}, got {len(vector)}")

            ref_id = _make_ref_id(chunk.source_path, chunk.line_start, chunk.content_hash)
            refs_json = json.dumps(chunk.refs or [])

            with self.connect() as conn:
                conn.execute("BEGIN IMMEDIATE")

                # --- Ensure exactly one content + vector row per content_hash ---
                existing_content = conn.execute(
                    "SELECT vector_rowid FROM content WHERE content_hash = ?",
                    (chunk.content_hash,),
                ).fetchone()

                if existing_content is None:
                    # New content: allocate a vector rowid and insert content row.
                    # SEC-CORTEX-014 (Phase 2): use cursor.lastrowid as the primary
                    # source for the assigned rowid. lastrowid is correct for the stub
                    # (a real rowid table) and self-heals on any vec0 quirk: if the
                    # vec0 virtual table does not populate lastrowid reliably, the safe
                    # fallback to SELECT max(rowid) is still valid because the whole
                    # upsert runs inside BEGIN IMMEDIATE (exclusive writer), so no
                    # concurrent insert can interleave. Applied to BOTH branches.
                    if self.vector_backend == "sqlite_vec":
                        import sqlite_vec
                        cur = conn.execute(
                            "INSERT INTO content_vectors(embedding) VALUES (?)",
                            (sqlite_vec.serialize_float32(vector),),
                        )
                        vector_rowid = cur.lastrowid or conn.execute(
                            "SELECT max(rowid) FROM content_vectors"
                        ).fetchone()[0]
                    else:
                        cur = conn.execute(
                            "INSERT INTO content_vectors(embedding) VALUES (?)",
                            (json.dumps(vector),),
                        )
                        vector_rowid = cur.lastrowid or conn.execute(
                            "SELECT max(rowid) FROM content_vectors"
                        ).fetchone()[0]

                    conn.execute(
                        """
                        INSERT INTO content(content_hash, vector_rowid, text, dim, model, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            chunk.content_hash,
                            vector_rowid,
                            chunk.text,
                            self.dim,
                            self.vector_backend,
                            chunk.recorded_date,
                        ),
                    )
                # If existing_content is not None, the vector is already stored — reuse it.

                # --- Check if this ref already points to a DIFFERENT content_hash ---
                # If so, after the upsert we need to GC the old content/vector if orphaned.
                old_hash_row = conn.execute(
                    "SELECT content_hash FROM content_refs WHERE storage_key = ? AND line_start = ?",
                    (chunk.source_path, chunk.line_start),
                ).fetchone()
                old_hash = old_hash_row[0] if (old_hash_row and old_hash_row[0] != chunk.content_hash) else None

                # --- Upsert the content_refs row (one per storage_key+line_start) ---
                conn.execute(
                    """
                    INSERT INTO content_refs(
                      ref_id, content_hash, storage_key, source_type,
                      line_start, line_end, trust, suspect, mem_type, agent,
                      recorded_date, refs
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(storage_key, line_start) DO UPDATE SET
                      ref_id       = excluded.ref_id,
                      content_hash = excluded.content_hash,
                      source_type  = excluded.source_type,
                      line_end     = excluded.line_end,
                      trust        = excluded.trust,
                      suspect      = excluded.suspect,
                      mem_type     = excluded.mem_type,
                      agent        = excluded.agent,
                      recorded_date= excluded.recorded_date,
                      refs         = excluded.refs
                    """,
                    (
                        ref_id,
                        chunk.content_hash,
                        chunk.source_path,
                        chunk.source_type,
                        chunk.line_start,
                        chunk.line_end,
                        chunk.trust,
                        1 if chunk.suspect else 0,
                        chunk.mem_type,
                        chunk.agent,
                        chunk.recorded_date,
                        refs_json,
                    ),
                )
                # --- GC orphaned content/vector if this ref changed its content_hash ---
                if old_hash is not None:
                    orphan = conn.execute(
                        "SELECT NOT EXISTS (SELECT 1 FROM content_refs WHERE content_hash = ?)",
                        (old_hash,),
                    ).fetchone()[0]
                    if orphan:
                        old_vector_row = conn.execute(
                            "SELECT vector_rowid FROM content WHERE content_hash = ?",
                            (old_hash,),
                        ).fetchone()
                        if old_vector_row is not None:
                            conn.execute(
                                "DELETE FROM content_vectors WHERE rowid = ?",
                                (int(old_vector_row[0]),),
                            )
                        conn.execute(
                            "DELETE FROM content WHERE content_hash = ?",
                            (old_hash,),
                        )

                conn.execute("COMMIT")
                changed += 1
        return changed

    def _delete_by_source_v2(self, source_path: str) -> int:
        """Ref-count-based delete: remove source's content_refs, then delete content +
        vector ONLY when the ref_count hits 0.

        Uses NOT EXISTS (not NOT IN) anti-join to avoid O(N×M) scan at scale.
        SEC-001: wrap in BEGIN IMMEDIATE to prevent TOCTOU between ref deletion
        and content orphan check.
        """
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            # 1. Find all content_hashes referenced by this source.
            hashes = [
                row[0]
                for row in conn.execute(
                    "SELECT content_hash FROM content_refs WHERE storage_key = ?",
                    (source_path,),
                ).fetchall()
            ]

            # 2. Delete all content_refs for this source.
            cur = conn.execute(
                "DELETE FROM content_refs WHERE storage_key = ?", (source_path,)
            )
            removed = int(cur.rowcount or 0)

            # 3. For each affected content_hash, delete content + vector if ref_count == 0.
            for ch in hashes:
                # NOT EXISTS is O(index lookup) — no N×M full scan.
                orphan = conn.execute(
                    "SELECT NOT EXISTS (SELECT 1 FROM content_refs WHERE content_hash = ?)",
                    (ch,),
                ).fetchone()[0]
                if orphan:
                    vector_rowid_row = conn.execute(
                        "SELECT vector_rowid FROM content WHERE content_hash = ?", (ch,)
                    ).fetchone()
                    if vector_rowid_row is not None:
                        conn.execute(
                            "DELETE FROM content_vectors WHERE rowid = ?",
                            (int(vector_rowid_row[0]),),
                        )
                    conn.execute("DELETE FROM content WHERE content_hash = ?", (ch,))

            # 4. Always clean up source_state for this source.
            conn.execute("DELETE FROM source_state WHERE source_path = ?", (source_path,))

            conn.execute("COMMIT")
        return removed

    def _search_v2(
        self,
        vector: list[float],
        *,
        k: int,
        trust: list[str],
        placeholders: str,
    ) -> list[dict]:
        """v2 search: kNN over content_vectors → join content → join content_refs.
        Trust filter runs in SQL BEFORE any dedup (preserves SEC-CORTEX-001 default-deny).
        """
        with self.connect() as conn:
            # Existence check: any refs in the DB?
            _exists = conn.execute("SELECT 1 FROM content_refs LIMIT 1").fetchone()
            if _exists is None:
                raise QueryUnavailable("Cortex DB is empty; run index first")

        if self.vector_backend == "sqlite_vec":
            return self._search_sqlite_vec_v2(vector, k=k, trust=trust, placeholders=placeholders)
        return self._search_stub_v2(vector, k=k, trust=trust, placeholders=placeholders)

    def _search_sqlite_vec_v2(
        self,
        vector: list[float],
        *,
        k: int,
        trust: list[str],
        placeholders: str,
    ) -> list[dict]:
        import sqlite_vec

        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                  content_refs.ref_id         AS id,
                  content.text                AS text,
                  content_refs.storage_key    AS source_path,
                  content_refs.line_start     AS line_start,
                  content_refs.line_end       AS line_end,
                  content_refs.source_type    AS source_type,
                  content.content_hash        AS content_hash,
                  content_refs.trust          AS trust,
                  content_refs.suspect        AS suspect,
                  content_refs.recorded_date  AS recorded_date,
                  distance
                FROM content_vectors
                JOIN content ON content.vector_rowid = content_vectors.rowid
                JOIN content_refs ON content_refs.content_hash = content.content_hash
                WHERE content_refs.trust IN ({placeholders})
                AND content_vectors.embedding MATCH ?
                AND k = ?
                ORDER BY distance
                """,
                (*trust, sqlite_vec.serialize_float32(vector), _overfetch_k(k)),
            ).fetchall()
        return _dedupe_by_content([_row_to_result_v2(row) for row in rows], k)

    def _search_stub_v2(
        self,
        vector: list[float],
        *,
        k: int,
        trust: list[str],
        placeholders: str,
    ) -> list[dict]:
        """Stub backend: cosine similarity over all content_vectors, trust-filtered."""
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                  content_refs.ref_id         AS id,
                  content.text                AS text,
                  content_refs.storage_key    AS source_path,
                  content_refs.line_start     AS line_start,
                  content_refs.line_end       AS line_end,
                  content_refs.source_type    AS source_type,
                  content.content_hash        AS content_hash,
                  content_refs.trust          AS trust,
                  content_refs.suspect        AS suspect,
                  content_refs.recorded_date  AS recorded_date,
                  content_vectors.embedding   AS embedding
                FROM content_vectors
                JOIN content ON content.vector_rowid = content_vectors.rowid
                JOIN content_refs ON content_refs.content_hash = content.content_hash
                WHERE content_refs.trust IN ({placeholders})
                """,
                tuple(trust),
            ).fetchall()
        results = []
        for row in rows:
            embedding = json.loads(row["embedding"])
            result = _row_to_result_v2(row)
            result["distance"] = 1.0 - _cosine(vector, embedding)
            results.append(result)
        ordered = sorted(results, key=lambda item: item["distance"])
        return _dedupe_by_content(ordered, k)

    # -------------------------------------------------------------------------
    # v1 legacy storage methods (kept intact for legacy DBs)
    # -------------------------------------------------------------------------

    def _upsert_v1(self, items: Iterable[tuple[Chunk, list[float]]]) -> int:
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

    def _delete_by_source_v1(self, source_path: str) -> int:
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

    def _search_sqlite_vec_v1(self, vector: list[float], *, k: int, trust: list[str], placeholders: str) -> list[dict]:
        import sqlite_vec

        # BUG-CORTEX-006 (v9.3.2): over-fetch, then collapse by content_hash so a
        # shared brain (same canonical text indexed once per install scope) cannot
        # fill all k slots with byte-identical duplicates. Trust filter runs in SQL
        # BEFORE dedup, so dedup can never elevate or relabel a chunk's trust.
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
                (*trust, sqlite_vec.serialize_float32(vector), _overfetch_k(k)),
            ).fetchall()
            return _dedupe_by_content([_row_to_result(row) for row in rows], k)

    def _search_stub_v1(self, vector: list[float], *, k: int, trust: list[str], placeholders: str) -> list[dict]:
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
        ordered = sorted(results, key=lambda item: item["distance"])
        return _dedupe_by_content(ordered, k)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    an = math.sqrt(sum(x * x for x in a)) or 1.0
    bn = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (an * bn)


def _overfetch_k(k: int) -> int:
    """BUG-CORTEX-006: fetch extra candidates so dedup can still return k distinct."""
    return max(k * 8, k + 50)


def _dedupe_by_content(rows: list[dict], k: int) -> list[dict]:
    """Collapse rows sharing a content_hash, keeping the first (lowest-distance)
    occurrence, and return at most k distinct results. Order is preserved."""
    seen: set[str] = set()
    out: list[dict] = []
    for row in rows:
        digest = row.get("content_hash")
        if digest in seen:
            continue
        seen.add(digest)
        out.append(row)
        if len(out) >= k:
            break
    return out


# A scope is always a 12-hex install_id, so a scoped key is exactly `@<12-hex>/<rel>`.
# Matching this precise shape avoids stripping a legitimate repo path like "@team/x.md".
# CODE-001 (v9.3.3): canonical single definition of the scoped-key pattern. ingest.py
# imports this rather than redeclaring it, so a future scope-format change updates one
# place and both modules stay consistent (was duplicated in store.py + ingest.py).
_SCOPED_PREFIX_RE = re.compile(r"^@[0-9a-f]{12}/")


def dedup_report(store: "Store", *, redactor=None) -> dict:
    """IMPL-003 (v9.3.3) / Phase 5 (v9.4.0): READ-ONLY duplicate analysis.

    Schema-aware: returns different metric shapes for v1 and v2.

    v2 (content-addressed) returns:
      total_refs      (int):   rows in content_refs
      unique_content  (int):   rows in content (distinct content_hash values)
      shared_content  (int):   content rows with ref_count > 1 (reused across sources)
      dedup_savings   (int):   total_refs - unique_content (vectors saved vs naive storage)
      dedup_ratio     (float): dedup_savings / total_refs  (0.0 if empty)
      top_duplicates  (list):  top-10 content_hashes by ref count (desc), each entry:
                                { content_hash, occurrences, text_preview }

    v1 (legacy) returns the original shape:
      total_chunks    (int):   total rows in chunks table
      unique_hashes   (int):   distinct content_hash values
      duplicate_chunks(int):   chunks that share a content_hash with at least one other
      duplicate_ratio (float): duplicate_chunks / total_chunks  (0.0 if empty)
      top_duplicates  (list):  top-10 content_hashes by share count (desc)

    SEC-CORTEX-DIAG-003 (v9.3.3): `redactor` is an optional callable `(text) -> bool`.
    When supplied and it returns True for a chunk's text, the `text_preview` is replaced
    with a redaction marker instead of the raw snippet. Callers pass `contains_secret`
    (injected from ingest to avoid a store<-ingest import cycle) so any chunk that slipped
    past the indexing-time secret filter is not re-disclosed to stdout by this report.
    """
    store.init_schema()

    def _preview(text: str) -> str:
        if redactor is not None and redactor(text):
            return "[REDACTED — possible secret]"
        return text[:80]

    with store.connect() as conn:
        if store._active_schema == 2:
            # v2: content-addressed metrics.
            # total_refs = all content_refs rows (one per source occurrence).
            # unique_content = distinct content rows (one per distinct content_hash).
            # shared_content = content rows referenced by more than one ref.
            # dedup_savings = vectors saved vs a naive per-ref storage model.
            total_refs = int(conn.execute("SELECT COUNT(*) FROM content_refs").fetchone()[0])
            unique_content = int(conn.execute("SELECT COUNT(*) FROM content").fetchone()[0])
            # Count content rows that have more than one ref pointing at them.
            shared_content = int(conn.execute(
                """
                SELECT COUNT(*) FROM (
                  SELECT content_hash
                  FROM content_refs
                  GROUP BY content_hash
                  HAVING COUNT(*) > 1
                )
                """
            ).fetchone()[0])
            dedup_savings = max(0, total_refs - unique_content)
            ratio = dedup_savings / total_refs if total_refs > 0 else 0.0
            # Top-10 content_hashes by ref count, for shared content only.
            top_rows = conn.execute(
                """
                SELECT cr.content_hash, COUNT(*) AS occurrences,
                       c.text AS text_preview
                FROM content_refs cr
                JOIN content c ON c.content_hash = cr.content_hash
                GROUP BY cr.content_hash
                HAVING COUNT(*) > 1
                ORDER BY occurrences DESC
                LIMIT 10
                """
            ).fetchall()

            top_dupes = [
                {
                    "content_hash": str(r[0]),
                    "occurrences": int(r[1]),
                    "text_preview": _preview(str(r[2])),
                }
                for r in top_rows
            ]
            return {
                "total_refs": total_refs,
                "unique_content": unique_content,
                "shared_content": shared_content,
                "dedup_savings": dedup_savings,
                "dedup_ratio": round(ratio, 4),
                "top_duplicates": top_dupes,
            }

        else:
            # v1 legacy path — shape unchanged for backward compatibility.
            total = int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
            unique = int(conn.execute("SELECT COUNT(DISTINCT content_hash) FROM chunks").fetchone()[0])
            duplicate_chunks = total - unique if total > unique else 0
            ratio = duplicate_chunks / total if total > 0 else 0.0
            top_rows = conn.execute(
                """
                SELECT content_hash, COUNT(*) AS occurrences,
                       MIN(text) AS text_preview
                FROM chunks
                GROUP BY content_hash
                HAVING COUNT(*) > 1
                ORDER BY occurrences DESC
                LIMIT 10
                """
            ).fetchall()

            top_dupes = [
                {
                    "content_hash": str(r[0]),
                    "occurrences": int(r[1]),
                    "text_preview": _preview(str(r[2])),
                }
                for r in top_rows
            ]
            return {
                "total_chunks": total,
                "unique_hashes": unique,
                "duplicate_chunks": duplicate_chunks,
                "duplicate_ratio": round(ratio, 4),
                "top_duplicates": top_dupes,
            }


def integrity_report(store: "Store") -> dict:
    """IMPL-003 (v9.3.3) / Phase 5 (v9.4.0): READ-ONLY integrity check for brain doctor.

    Schema-aware: returns different field shapes for v1 and v2.

    v2 (content-addressed) returns:
      schema_version     (int):         always 2 for a v2 DB
      content_count      (int):         rows in content table (one per distinct content_hash)
      vector_count       (int):         rows in content_vectors (must equal content_count)
      refs_count         (int):         rows in content_refs (one per source occurrence)
      integrity_ok       (bool):        True when content_count == vector_count
      mismatch_detail    (str | None):  description if content/vector counts disagree
      trust_distribution (dict):        {trust_level: count, ...} (from content_refs)

    v1 (legacy) returns the original shape:
      chunks_count       (int):         rows in chunks
      rowmap_count       (int):         rows in rowmap
      vectors_count      (int):         rows in chunk_vectors
      integrity_ok       (bool):        True when all three counts are equal
      mismatch_details   (str | None):  description if mismatch detected
      trust_distribution (dict):        {trust_level: count, ...}
    """
    store.init_schema()
    with store.connect() as conn:
        if store._active_schema == 2:
            content_count = int(conn.execute("SELECT COUNT(*) FROM content").fetchone()[0])
            vector_count = int(conn.execute("SELECT COUNT(*) FROM content_vectors").fetchone()[0])
            refs_count = int(conn.execute("SELECT COUNT(*) FROM content_refs").fetchone()[0])
            trust_rows = conn.execute(
                "SELECT trust, COUNT(*) FROM content_refs GROUP BY trust ORDER BY trust"
            ).fetchall()
            trust_dist = {str(r[0]): int(r[1]) for r in trust_rows}
            # v2 integrity invariant: one vector per content_hash (content_count == vector_count).
            ok = (content_count == vector_count)
            mismatch = None
            if not ok:
                mismatch = f"content={content_count}, content_vectors={vector_count}"
            return {
                "schema_version": 2,
                "content_count": content_count,
                "vector_count": vector_count,
                "refs_count": refs_count,
                "integrity_ok": ok,
                "mismatch_detail": mismatch,
                "trust_distribution": trust_dist,
            }
        else:
            # v1 legacy — shape unchanged for backward compatibility.
            chunks_count = int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
            rowmap_count = int(conn.execute("SELECT COUNT(*) FROM rowmap").fetchone()[0])
            vectors_count = int(conn.execute("SELECT COUNT(*) FROM chunk_vectors").fetchone()[0])
            trust_rows = conn.execute(
                "SELECT trust, COUNT(*) FROM chunks GROUP BY trust ORDER BY trust"
            ).fetchall()
            trust_dist = {str(r[0]): int(r[1]) for r in trust_rows}
            ok = (chunks_count == rowmap_count == vectors_count)
            mismatch = None
            if not ok:
                mismatch = f"chunks={chunks_count}, rowmap={rowmap_count}, vectors={vectors_count}"
            return {
                "chunks_count": chunks_count,
                "rowmap_count": rowmap_count,
                "vectors_count": vectors_count,
                "integrity_ok": ok,
                "mismatch_details": mismatch,
                "trust_distribution": trust_dist,
            }


def engine_hash() -> str:
    """IMPL-003 (v9.3.3): Compute a stable SHA-256 digest of all cortex .py files.

    Returns a hex string. Callers can compare this between installs to detect
    engine drift without distributing separate checksums. READ-ONLY.
    """
    cortex_dir = Path(__file__).resolve().parent
    py_files = sorted(cortex_dir.glob("*.py"))
    h = hashlib.sha256()
    for f in py_files:
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


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
    """Build result dict from a v1 chunks-joined row."""
    return {
        "id": row["id"],
        "text": row["text"],
        "source_path": _display_source(row["source_path"]),
        "line_start": int(row["line_start"]),
        "line_end": int(row["line_end"]),
        "source_type": row["source_type"],
        "content_hash": row["content_hash"],
        "trust": row["trust"],
        "suspect": bool(row["suspect"]),
        "recorded_date": row["recorded_date"],
        "distance": float(row["distance"]) if "distance" in row.keys() else 0.0,
    }


def _row_to_result_v2(row: sqlite3.Row) -> dict:
    """Build result dict from a v2 content+content_refs joined row.

    The public result contract is identical to v1 — same field names, same types.
    source_path is display-stripped of any scope prefix for clean citation output.
    """
    return {
        "id": row["id"],
        "text": row["text"],
        "source_path": _display_source(row["source_path"]),
        "line_start": int(row["line_start"]),
        "line_end": int(row["line_end"]),
        "source_type": row["source_type"],
        "content_hash": row["content_hash"],
        "trust": row["trust"],
        "suspect": bool(row["suspect"]),
        "recorded_date": row["recorded_date"],
        "distance": float(row["distance"]) if "distance" in row.keys() else 0.0,
    }
