"""SQLite storage and vector search for Cortex."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

_log = logging.getLogger(__name__)

from .errors import DependencyError, GraphSchemaError, QueryUnavailable, SchemaMismatchError, SchemaTooNewError


# SEC-CORTEX-ACCESS-008 (v9.7.1): Anti-destruction guard exceptions.

class SharedBrainError(Exception):
    """Raised when a full-wipe destructive op is attempted on a shared brain
    (cortex_installs has > 1 live member) without the required acknowledgment flags.

    The error message enumerates the peer install_ids and their last_seen timestamps
    so the operator can make an informed decision before re-issuing with
    --shared-ok (scope-self only) or --all-installs-acknowledged (full wipe).
    """


class ForeignInstallError(Exception):
    """Raised when the invoking install_id is absent from cortex_installs (non-empty
    ledger) and --force-foreign was not passed.

    Protects against an unrelated install accidentally wiping a shared brain that
    it has never written to (the 'rhs-shared' root-cause scenario).
    """

# PLAN-DESIGN-001 Phase 1 (v9.4.0): the highest Cortex storage schema this engine
# understands. PRAGMA user_version is the single canonical authority; metadata.schema_version
# is only a diagnostic mirror.
#   v1 = legacy chunk-addressed storage (v9.3.x)
#   v2 = content-addressed storage (v9.4.0+)
#   v3 = graph layer (v9.6.0+) — cortex_entities, cortex_edges, cortex_query_cache, cortex_bm25
#   v4 = storage elasticity (v9.7.0+) — last_recalled_at column on content_refs (LRU opt-in)
# Bumping this constant is how a future engine declares it can read the new schema.
# WI-1 (PLAN-CORTEX-GRAPH-001 Phase 1a): bumped from 2 → 3 for v9.6.0 graph layer.
# WI-S3 (Stage 3 Phase 1, v9.7.0): bumped from 3 → 4 for storage elasticity (last_recalled_at).
SUPPORTED_SCHEMA = 4


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
        lru_eviction_enabled: bool = False,
        include_protected: list[str] | None = None,
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
        # WI-S3-4 (v9.7.0): LRU recall-hit tracking flag.
        # When True, search() and hybrid_search() update last_recalled_at on every hit.
        # DEFAULT: False — S3-RISK-004 (privacy): last_recalled_at is a new data-collection
        # surface. Opt-in only. Requires _active_schema >= 4 to have the column.
        self._lru_eviction_enabled: bool = bool(lru_eviction_enabled)
        # WI-S3-3 (v9.7.0): set of protected source paths for the eviction NEVER-evict guard.
        # Paths here (repo-relative) are never evicted regardless of trust/source_type.
        self._include_protected: set[str] = set(include_protected or [])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # WI-6/WI-9 (PLAN-CORTEX-GRAPH-001 Phase 1a): single probe at __init__ time.
        # FTS5 is standard from SQLite 3.9+ but can be compiled out on some Linux distros.
        # If absent, BM25 component is gracefully disabled — all upsert/search still works
        # (the BM25 block in _upsert_v2 is gated on both _active_schema>=3 AND this flag).
        self._bm25_available: bool = self._probe_fts5()

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

    def _probe_fts5(self) -> bool:
        """WI-6/WI-9: Single FTS5 availability probe at Store.__init__ time.

        Result cached in self._bm25_available. Uses an in-memory DB so the probe
        never touches self.db_path (safe to call before schema init). FTS5 is
        compiled into SQLite on most platforms but can be absent on hardened Linux
        builds. When absent, BM25 is gracefully disabled — hybrid retrieval runs
        without the lexical component; no hard failure.
        """
        try:
            probe_conn = sqlite3.connect(":memory:")
            probe_conn.execute("CREATE VIRTUAL TABLE _fts5_probe USING fts5(x)")
            probe_conn.execute("DROP TABLE IF EXISTS _fts5_probe")
            probe_conn.close()
            return True
        except Exception:
            return False

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

    def _stamp_install_soft(self) -> None:
        """SEC-ACCESS-008-NEW-001 (v9.7.1): Attempt ledger stamp in a separate transaction.

        Called AFTER the main DDL transaction commits in init_schema(). Because this
        runs in its own transaction, a sqlite3.OperationalError (database is locked /
        busy) is caught and logged as a WARNING — stamping is best-effort.

        This keeps brain status and brain query (which now call init_schema()) safe
        under concurrent writers: the DDL portion always succeeds (fresh schema is
        already present); only the stamp may be skipped on contention. The stamp is
        idempotent so the next invocation will succeed.

        NON-NEGOTIABLE: only OperationalError (locked/busy) is swallowed. All other
        exceptions (IntegrityError, ProgrammingError, corruption) propagate normally.
        """
        if self._install_id is None:
            return
        try:
            with self.connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    self._stamp_install(conn)
                    conn.execute("COMMIT")
                except Exception:
                    try:
                        conn.execute("ROLLBACK")
                    except Exception:
                        pass
                    raise
        except sqlite3.OperationalError as exc:
            # Locked/busy: stamp is best-effort. Log and continue.
            _log.warning(
                "SEC-ACCESS-008-NEW-001: ledger stamp skipped (DB locked/busy) — "
                "%s. Stamp will be retried on the next invocation (idempotent).", exc
            )

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
                # Fresh DB: WI-2 (PLAN-CORTEX-GRAPH-001 Phase 1a): initialize directly as v3.
                # WI-S3 (Stage 3, v9.7.0): when SUPPORTED_SCHEMA >= 4 also add v4 schema.
                # v3 = v2 tables + graph tables (cortex_entities, cortex_edges,
                #      cortex_query_cache, cortex_bm25).
                # v4 = v3 + last_recalled_at column on content_refs (LRU opt-in, S3-RISK-004)
                # SEC-001 (PLAN-DESIGN-001 §4/§6): wrap DDL in BEGIN IMMEDIATE so no
                # concurrent writer can see a partially-created schema.
                conn.execute("BEGIN IMMEDIATE")
                self._create_v2_schema(conn)
                # Only add v3 graph tables when the engine actually supports v3.
                # When SUPPORTED_SCHEMA is patched to 2 for test isolation, a fresh
                # DB should not receive v3 tables — the schema gate in run_extraction_for_chunk
                # (and all other v3 callers) relies on the table's absence to confirm v2.
                if SUPPORTED_SCHEMA >= 3:
                    self._create_v3_schema(conn)
                if SUPPORTED_SCHEMA >= 4:
                    self._create_v4_schema(conn)
                # PLAN-DESIGN-001 §0 (Phase 3): create ledger.
                self._create_installs_ledger(conn)
                conn.execute(f"PRAGMA user_version = {SUPPORTED_SCHEMA}")
                conn.execute(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', ?)",
                    (str(SUPPORTED_SCHEMA),),
                )
                conn.execute("COMMIT")
                self._active_schema = SUPPORTED_SCHEMA

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
                conn.execute("COMMIT")
                self._active_schema = 1

            elif current == 2:
                # v2 DB opened by v3 engine: run v2 path only.
                # Do NOT auto-add v3 tables — migration is explicit (WI-7, Phase 1b).
                # The _assert_schema_compatible guard already confirmed 2 <= SUPPORTED_SCHEMA(=3).
                conn.execute("BEGIN IMMEDIATE")
                self._create_v2_schema(conn)
                # PLAN-DESIGN-001 §0 (Phase 3): ensure ledger exists in v2-path too
                # (idempotent — CREATE TABLE IF NOT EXISTS).
                self._create_installs_ledger(conn)
                conn.execute("COMMIT")
                # Mirror is already correct (set at v2 init time).
                self._active_schema = 2
                # A v2 DB never has cortex_bm25 — disable BM25 for this store instance.
                # (The probe flag reflects SQLite FTS5 availability, not DB state;
                # we override it here so _upsert_v2 does not try to write to a missing table.)
                self._bm25_available = False

            elif current == 3:
                # WI-2 (PLAN-CORTEX-GRAPH-001 Phase 1a): v3 DB opened by v4 engine.
                # Run in v3 mode — do NOT auto-upgrade to v4. That is the migration
                # script's job (migrate_cortex_elastic_9_7.py --execute). Auto-upgrading
                # without explicit migration would bypass the backup-first / ledger-gate
                # safety checks.
                conn.execute("BEGIN IMMEDIATE")
                self._create_v2_schema(conn)
                self._create_v3_schema(conn)
                self._create_installs_ledger(conn)
                conn.execute("COMMIT")
                self._active_schema = 3

            elif current == 4:
                # WI-S3 (Stage 3, v9.7.0): v4 DB opened by v4 engine.
                # Idempotent re-init: ensure v2 + v3 + v4 tables all present.
                conn.execute("BEGIN IMMEDIATE")
                self._create_v2_schema(conn)
                self._create_v3_schema(conn)
                self._create_v4_schema(conn)
                self._create_installs_ledger(conn)
                conn.execute("COMMIT")
                self._active_schema = 4

            # current > SUPPORTED_SCHEMA is already handled by _assert_schema_compatible
            # (raises SchemaTooNewError before reaching here).

        # Only mark initialized AFTER a successful pass — if _assert_schema_compatible
        # raised (SchemaTooNewError / SchemaMismatchError), we never reach here, so the
        # flag stays False and the guard will re-fire correctly on the next call.
        self._schema_initialized = True

        # SEC-ACCESS-008-NEW-001 (v9.7.1): stamp the ledger in a SEPARATE fail-soft
        # transaction after the main DDL commits. This decouples the read-path
        # (status/query) from the stamp write so a locked DB never crashes a read-op.
        self._stamp_install_soft()

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
              last_seen        TEXT NOT NULL,
              first_seen       TEXT
            )
            """
        )
        # SEC-CORTEX-ACCESS-008 (v9.7.1): self-heal for older DBs created before
        # the first_seen column was added.  ALTER TABLE ... ADD COLUMN is idempotent-
        # safe: we catch the OperationalError that SQLite raises if the column already
        # exists (it does not support IF NOT EXISTS for columns).
        try:
            conn.execute(
                "ALTER TABLE cortex_installs ADD COLUMN first_seen TEXT"
            )
        except sqlite3.OperationalError:
            pass  # column already exists — older DB is now self-healed

    def _stamp_install(self, conn: sqlite3.Connection, *, protocol_version: str | None = None) -> None:
        """Upsert this engine's row into cortex_installs.

        Called inside the init_schema transaction ONLY when self._install_id is set.
        When _install_id is None (most unit tests, callers without a repo root),
        this is a no-op so existing tests are unaffected.
        """
        if self._install_id is None:
            return
        now = datetime.now(timezone.utc).isoformat()
        # SEC-CORTEX-ACCESS-008 (v9.7.1): first_seen is set on initial INSERT and
        # NEVER overwritten on subsequent stamps (it must remain the oldest timestamp
        # to allow owner-by-first_seen derivation).
        conn.execute(
            """
            INSERT INTO cortex_installs(install_id, supported_schema, protocol_version, last_seen, first_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(install_id) DO UPDATE SET
              supported_schema = excluded.supported_schema,
              protocol_version = excluded.protocol_version,
              last_seen        = excluded.last_seen
            """,
            (self._install_id, SUPPORTED_SCHEMA, protocol_version, now, now),
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
                "SELECT install_id, supported_schema, protocol_version, last_seen, first_seen"
                " FROM cortex_installs"
            ).fetchall()
        return [
            {
                "install_id": str(r[0]),
                "supported_schema": int(r[1]),
                "protocol_version": r[2],
                "last_seen": str(r[3]),
                "first_seen": str(r[4]) if r[4] is not None else None,
            }
            for r in rows
        ]

    # -------------------------------------------------------------------------
    # SEC-CORTEX-ACCESS-009 (v9.7.1): Backup and Integrity Check
    # -------------------------------------------------------------------------

    @staticmethod
    def backup_db(db_path: "str | Path", data_dir: "str | Path", retention_count: int = 3) -> "Path | None":
        """Copy brain.db to <data_dir>/backups/brain-<UTC-ISO8601>.db.

        SEC-CORTEX-ACCESS-009 (v9.7.1): pre-op backup before destructive operations
        (full reset, compact with deletions, migration).

        Args:
            db_path:         Path to the live brain.db.
            data_dir:        External Cortex data directory (data_dir from paths.py).
            retention_count: Maximum number of backup files to keep. Older files
                             are pruned after the new backup is written. Default 3.

        Returns:
            Path to the new backup file, or None if backup failed (fail-soft).

        Pruning: after writing the new backup, all brain-*.db files in backups/
        are sorted by name (ISO-8601 names sort lexicographically = chronologically).
        The oldest are deleted until at most retention_count remain.

        The backups/ directory lives inside data_dir, which is OUTSIDE the repo
        scan root — Cortex never indexes it.
        """
        import shutil as _shutil

        db = Path(db_path)
        if not db.exists():
            _log.warning("backup_db: brain.db does not exist at %s — skipping backup", db)
            return None

        try:
            backups_dir = Path(data_dir) / "backups"
            backups_dir.mkdir(parents=True, exist_ok=True)

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
            dest = backups_dir / f"brain-{now_str}.db"

            _shutil.copy2(str(db), str(dest))
            _log.info("SEC-ACCESS-009: backup created at %s", dest)

            # Prune to retention_count (keep newest)
            if retention_count > 0:
                all_backups = sorted(backups_dir.glob("brain-*.db"))
                excess = len(all_backups) - retention_count
                if excess > 0:
                    for old in all_backups[:excess]:
                        try:
                            old.unlink()
                            _log.info("SEC-ACCESS-009: pruned old backup %s", old)
                        except OSError as prune_exc:
                            _log.warning("SEC-ACCESS-009: could not prune backup %s — %s", old, prune_exc)

            return dest
        except Exception as exc:
            _log.warning("SEC-ACCESS-009: backup_db failed (fail-soft) — %s", exc)
            return None

    def run_integrity_check(self, data_dir: "str | Path | None" = None) -> dict:
        """Run PRAGMA integrity_check and PRAGMA foreign_key_check.

        SEC-CORTEX-ACCESS-009 (v9.7.1): post-compact and post-migration health check.

        Returns:
            {
              "ok":               bool — True iff both checks pass.
              "integrity_check":  str  — "ok" or the first error line.
              "foreign_key_check": str — "ok" or the first violation.
              "errors":           list[str] — all error lines from integrity_check.
            }

        Fail-soft contract:
          - If the DB cannot be opened (e.g. SchemaTooNewError), returns ok=False
            with an error description. NEVER raises.
          - On a non-OK result: prints CRITICAL to stderr AND writes
            <data_dir>/integrity-fail.flag (if data_dir provided). The flag makes
            brain status report DEGRADED.
          - A failed integrity check does NOT crash the calling command.
        """
        import sys as _sys

        result = {
            "ok": False,
            "integrity_check": "not_run",
            "foreign_key_check": "not_run",
            "errors": [],
        }

        try:
            conn = self.connect()
            try:
                # PRAGMA integrity_check returns rows; "ok" = single row with value "ok"
                ic_rows = conn.execute("PRAGMA integrity_check").fetchall()
                ic_values = [str(r[0]) for r in ic_rows]
                if ic_values == ["ok"]:
                    result["integrity_check"] = "ok"
                else:
                    result["integrity_check"] = ic_values[0] if ic_values else "unknown"
                    result["errors"] = ic_values

                # PRAGMA foreign_key_check returns rows only if violations exist
                fk_rows = conn.execute("PRAGMA foreign_key_check").fetchall()
                if not fk_rows:
                    result["foreign_key_check"] = "ok"
                else:
                    result["foreign_key_check"] = f"{len(fk_rows)} violation(s)"
                    result["errors"].extend([str(r) for r in fk_rows])

                result["ok"] = (result["integrity_check"] == "ok" and result["foreign_key_check"] == "ok")
            finally:
                conn.close()
        except Exception as exc:
            result["integrity_check"] = f"error: {exc}"
            result["errors"] = [str(exc)]

        if not result["ok"]:
            print(
                f"CRITICAL (SEC-ACCESS-009): Cortex DB integrity check FAILED — "
                f"{result['integrity_check']}",
                file=_sys.stderr,
            )
            if data_dir is not None:
                try:
                    flag = Path(data_dir) / "integrity-fail.flag"
                    flag.write_text(
                        f"integrity_check failed at {datetime.now(timezone.utc).isoformat()}: "
                        f"{result['integrity_check']}",
                        encoding="utf-8",
                    )
                    _log.warning("SEC-ACCESS-009: integrity-fail.flag written at %s", flag)
                except OSError as flag_exc:
                    _log.warning("SEC-ACCESS-009: could not write integrity-fail.flag — %s", flag_exc)

        return result

    # -------------------------------------------------------------------------
    # SEC-CORTEX-ACCESS-008 (v9.7.1): Anti-destruction guard
    # -------------------------------------------------------------------------

    def check_reset_safety(
        self,
        invoking_install_id: str,
        *,
        shared_ok: bool = False,
        all_installs_acknowledged: bool = False,
        force_foreign: bool = False,
    ) -> None:
        """Guard a destructive brain reset against shared-brain data loss.

        Raises SharedBrainError when the ledger contains > 1 live member and
        neither shared_ok nor all_installs_acknowledged is set.

        Raises ForeignInstallError when invoking_install_id is absent from a
        non-empty ledger and force_foreign is False.

        Fail-OPEN behaviors (no raise):
        - DB does not exist (pre-creation state).
        - Ledger table is absent in the DB (pre-v9.4.0 DB).
        - Ledger is empty (no stamps recorded yet).

        In all fail-OPEN cases a WARNING is printed to stderr so the operator is
        not silently left without feedback.

        Args:
            invoking_install_id: The install_id of the calling install.
            shared_ok: If True, allow scope-self wipe on a shared brain (no full-wipe ack needed).
            all_installs_acknowledged: If True, allow full wipe even on a shared brain.
            force_foreign: If True, bypass the foreign-install check.
        """
        # Fail-OPEN: DB does not exist yet.
        if not self.db_path.exists():
            import sys as _sys
            print(
                "WARNING (SEC-ACCESS-008): Cortex DB does not exist; "
                "skipping shared-brain ledger check (fail-OPEN).",
                file=_sys.stderr,
            )
            return

        ledger = self.installs_ledger()

        # Fail-OPEN: empty ledger (no stamps, or pre-ledger DB).
        if not ledger:
            import sys as _sys
            print(
                "WARNING (SEC-ACCESS-008): cortex_installs ledger is empty; "
                "cannot enumerate peers — proceeding with caution (fail-OPEN). "
                "Pass --shared-ok if this is a known shared brain.",
                file=_sys.stderr,
            )
            return

        # Foreign-install check: invoking install is not in the ledger.
        known_ids = {r["install_id"] for r in ledger}
        if invoking_install_id not in known_ids:
            if not force_foreign:
                raise ForeignInstallError(
                    f"SEC-ACCESS-008: invoking install '{invoking_install_id}' is not "
                    f"registered in cortex_installs (known: {sorted(known_ids)}). "
                    "This may be a foreign install accidentally targeting a shared brain. "
                    "Pass --force-foreign to override (requires explicit acknowledgment)."
                )
            # force_foreign set — allow, but warn
            import sys as _sys
            print(
                f"WARNING (SEC-ACCESS-008): --force-foreign set; proceeding despite "
                f"'{invoking_install_id}' being absent from the ledger.",
                file=_sys.stderr,
            )
            return

        # Multi-member shared brain check.
        peers = [r for r in ledger if r["install_id"] != invoking_install_id]
        if peers and not shared_ok and not all_installs_acknowledged:
            peer_summary = ", ".join(
                f"{r['install_id']} (last_seen={r['last_seen']})" for r in peers
            )
            raise SharedBrainError(
                f"SEC-ACCESS-008: shared brain detected — {len(peers)} other install(s) "
                f"share this DB: {peer_summary}. "
                "A bare 'brain reset --yes' would destroy ALL installs' data. "
                "Safe options:\n"
                "  --scope self --yes                 delete only YOUR install's data (safe)\n"
                "  --yes --all-installs-acknowledged  full wipe with explicit acknowledgment\n"
                "  --yes --shared-ok                  same as --scope self (alias)"
            )

    def reset_scope_self(self, install_id: str) -> dict:
        """Delete ONLY the rows namespaced under @<install_id>/.

        This is the SAFE reset path for shared brains.  It removes:
          - content_refs rows where storage_key LIKE '@<install_id>/%'
          - source_state rows where source_path LIKE '@<install_id>/%'
          - The install's own row in cortex_installs

        Peer installs' data is left completely intact.

        Returns:
            {"deleted_refs": int, "deleted_sources": int}
        """
        prefix = f"@{install_id}/"
        deleted_refs = 0
        deleted_sources = 0

        def _like_escape_prefix(s: str) -> str:
            """Escape LIKE special chars in s and append % for a prefix match."""
            return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                # Remove content_refs for this install's namespace.
                cur = conn.execute(
                    "DELETE FROM content_refs WHERE storage_key LIKE ? ESCAPE '\\'",
                    (_like_escape_prefix(prefix),),
                )
                deleted_refs = int(cur.rowcount or 0)

                # Remove source_state for this install's namespace.
                cur2 = conn.execute(
                    "DELETE FROM source_state WHERE source_path LIKE ? ESCAPE '\\'",
                    (_like_escape_prefix(prefix),),
                )
                deleted_sources = int(cur2.rowcount or 0)

                # Remove ledger row for this install.
                conn.execute(
                    "DELETE FROM cortex_installs WHERE install_id = ?",
                    (install_id,),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

        return {"deleted_refs": deleted_refs, "deleted_sources": deleted_sources}

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

    def _create_v3_schema(self, conn: sqlite3.Connection) -> None:
        """WI-2 (PLAN-CORTEX-GRAPH-001 Phase 1a): Create (idempotent) the v3 graph tables.

        Must be called inside an already-begun transaction (BEGIN IMMEDIATE) so the DDL
        batch is atomic. Uses CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.

        v3 adds four tables:
          cortex_entities   — typed entity registry (Decision, SEC-ID, WorkItem, ...)
          cortex_edges      — typed relationship registry (blocks, supersedes, ...)
          cortex_query_cache — content-hash-keyed result cache for hybrid retrieval
          cortex_bm25       — FTS5 virtual table for lexical search (BM25)

        Design decisions:
          - anchor_content_hash is intentionally ABSENT from cortex_entities (Todo B4):
            denorm goes stale on re-index; join goes through content_refs via anchor_ref_id.
          - cortex_bm25 DDL is wrapped in try/except — FTS5 may be absent on some SQLite
            builds. If FTS5 creation fails, the virtual table is silently skipped.
          - idx_entities_type_status_install uses (entity_type, status, install_id) per
            Todo finding to support install-scoped queries efficiently.
          - edge_id = sha256(f"{from_id}:{rel_type}:{to_id}")[:16] (deterministic).
          - Trust stored on edges is ADVISORY; query-time dual-filter is authoritative
            (SEC-GRAPH-001).
        """
        # --- cortex_entities: first-class typed entity registry ---
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cortex_entities (
              entity_id        TEXT PRIMARY KEY,
              entity_type      TEXT NOT NULL CHECK(entity_type IN (
                                 'Decision', 'SEC-ID', 'WorkItem', 'Version',
                                 'File', 'Blocker', 'Release', 'Lesson'
                               )),
              label            TEXT NOT NULL,
              status           TEXT NOT NULL DEFAULT 'open'
                                 CHECK(status IN ('open', 'closed', 'superseded', 'cascaded', 'resolved')),
              trust            TEXT NOT NULL DEFAULT 'untrusted'
                                 CHECK(trust IN ('trusted', 'semi', 'untrusted')),
              anchor_ref_id    TEXT,
              install_id       TEXT NOT NULL,
              created_at       TEXT NOT NULL,
              updated_at       TEXT NOT NULL,
              metadata_json    TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        # install-scoped covering index for query_open_by_type() (Todo B4 + index fix)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_type_status_install ON cortex_entities(entity_type, status, install_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_trust ON cortex_entities(trust)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_anchor_ref ON cortex_entities(anchor_ref_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_install ON cortex_entities(install_id)"
        )

        # --- cortex_edges: typed directed relationship registry ---
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cortex_edges (
              edge_id          TEXT PRIMARY KEY,
              from_entity_id   TEXT NOT NULL,
              to_entity_id     TEXT NOT NULL,
              rel_type         TEXT NOT NULL CHECK(rel_type IN (
                                 'blocks', 'supersedes', 'resolves', 'maps-to',
                                 'cascades-into', 'decided-by'
                               )),
              trust            TEXT NOT NULL DEFAULT 'untrusted',
              weight           REAL NOT NULL DEFAULT 1.0,
              install_id       TEXT NOT NULL,
              created_at       TEXT NOT NULL,
              provenance_ref_id TEXT
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_unique ON cortex_edges(from_entity_id, rel_type, to_entity_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_from ON cortex_edges(from_entity_id, rel_type)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_to ON cortex_edges(to_entity_id, rel_type)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_trust ON cortex_edges(trust)"
        )

        # --- cortex_query_cache: content-hash-keyed result cache for hybrid retrieval ---
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cortex_query_cache (
              cache_key        TEXT PRIMARY KEY,
              query_hash       TEXT NOT NULL,
              trust_filter     TEXT NOT NULL,
              k                INTEGER NOT NULL,
              created_at       TEXT NOT NULL,
              expires_at       TEXT NOT NULL,
              result_json      TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_expires ON cortex_query_cache(expires_at)"
        )

        # --- cortex_bm25: FTS5 virtual table for lexical search ---
        # Wrapped in try/except: FTS5 is standard from SQLite 3.9+ but can be compiled
        # out on some Linux distros. If absent, the virtual table is silently skipped
        # and _bm25_available remains False. All other v3 tables are still created.
        try:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS cortex_bm25
                  USING fts5(
                    ref_id   UNINDEXED,
                    text,
                    trust    UNINDEXED,
                    tokenize = 'unicode61 remove_diacritics 1'
                  )
                """
            )
        except Exception:
            # FTS5 not available — cortex_bm25 not created; _bm25_available stays False.
            pass

    def _create_v4_schema(self, conn: sqlite3.Connection) -> None:
        """WI-S3 (Stage 3 Phase 1, v9.7.0): Add last_recalled_at column to content_refs.

        Must be called inside an already-begun transaction (BEGIN IMMEDIATE).

        v4 adds:
          - content_refs.last_recalled_at TEXT (nullable) — LRU recall-hit timestamp.
            NULL by default (S3-RISK-004: privacy — opt-in only via lru_eviction_enabled).
            Only written when lru_eviction_enabled=True in Store config.

        SQLite does NOT support ALTER TABLE ... ADD COLUMN IF NOT EXISTS, so we check
        for column existence via PRAGMA table_info before issuing the ALTER.
        """
        # Check whether last_recalled_at already exists (idempotent).
        existing_cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(content_refs)").fetchall()
        }
        if "last_recalled_at" not in existing_cols:
            conn.execute(
                "ALTER TABLE content_refs ADD COLUMN last_recalled_at TEXT"
            )

    # -------------------------------------------------------------------------
    # Public API — dispatches on self._active_schema
    # -------------------------------------------------------------------------

    def count(self) -> int:
        self.init_schema()
        with self.connect() as conn:
            if self._active_schema in (2, 3, 4):  # v2, v3, v4 all use content_refs
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
        if self._active_schema in (2, 3, 4):  # v3/v4 use _upsert_v2 with BM25 gating
            return self._upsert_v2(items)
        return self._upsert_v1(items)

    def delete_by_source(self, source_path: str) -> int:
        self.init_schema()
        if self._active_schema in (2, 3, 4):
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

        if self._active_schema in (2, 3, 4):  # v3/v4 search uses the same v2 vector path
            results = self._search_v2(vector, k=k, trust=trust, placeholders=placeholders)
            # WI-S3-4 (v9.7.0): update last_recalled_at on result chunks.
            # Only when lru_eviction_enabled=True AND schema v4 (column present).
            # S3-RISK-004: disabled by default (privacy).
            if self._lru_eviction_enabled and self._active_schema >= 4 and results:
                self._update_last_recalled_at([r["id"] for r in results])
            return results

        # v1 legacy path
        # PERF (v9.3.4): replace the count() round-trip with a cheaper existence check.
        with self.connect() as conn:
            _exists = conn.execute("SELECT 1 FROM chunks LIMIT 1").fetchone()
        if _exists is None:
            raise QueryUnavailable("Cortex DB is empty; run index first")
        if self.vector_backend == "sqlite_vec":
            return self._search_sqlite_vec_v1(vector, k=k, trust=trust, placeholders=placeholders)
        return self._search_stub_v1(vector, k=k, trust=trust, placeholders=placeholders)

    def _update_last_recalled_at(self, ref_ids: list[str]) -> None:
        """WI-S3-4 (v9.7.0): Write last_recalled_at = now for each ref_id in ref_ids.

        Called ONLY when lru_eviction_enabled=True AND _active_schema >= 4.
        Fail-soft: any write error is logged as WARNING and silently swallowed —
        LRU tracking must never break a search call.
        S3-RISK-004: this is a new data-collection surface; opt-in only.
        """
        if not ref_ids:
            return
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            placeholders = ",".join("?" for _ in ref_ids)
            with self.connect() as conn:
                conn.execute(
                    f"UPDATE content_refs SET last_recalled_at = ? WHERE ref_id IN ({placeholders})",
                    (now, *ref_ids),
                )
        except Exception as exc:
            _log.warning("LRU: failed to update last_recalled_at for %d chunks: %s", len(ref_ids), exc)

    # -------------------------------------------------------------------------
    # WI-S3-2/S3-3: Storage elasticity — size probe and eviction engine (v9.7.0)
    # -------------------------------------------------------------------------

    def _db_size_mb(self) -> float:
        """WI-S3-2 (Stage 3 Phase 1, v9.7.0): Return the on-disk DB size in MB.

        Used by ingest.index() to decide whether eviction should run after indexing.

        SEC-UNIFIED-005 P3: OSError is silently swallowed and returns 0.0 (accepted
        residual: caller sees 0 MB, skips eviction rather than crashing the index run).
        """
        try:
            return os.path.getsize(self.db_path) / (1024 * 1024)
        except OSError:
            return 0.0

    def _evict_to_budget(
        self,
        conn: sqlite3.Connection,
        target_mb: float,
        dry_run: bool = False,
    ) -> dict:
        """WI-S3-3 (Stage 3 Phase 1, v9.7.0): Evict content_refs to bring DB under target_mb.

        SAFETY-CRITICAL (S3-RISK-001 — NON-NEGOTIABLE, ABSOLUTE):
          NEVER evict source_type='protected' (live dev-notes/security-review/domain.record).
          NEVER evict trust='trusted' (canonical protocol material).
          NEVER evict any chunk whose storage_key matches self._include_protected paths.
          These constraints are hard-coded and cannot be overridden by config.

        S3-RISK-002: if still over budget after exhausting all evictable tiers, log an
        advisory warning and RETURN — do NOT loop, do NOT crash, do NOT touch never-evict set.

        Priority order (oldest recorded_date ASC within each tier):
          1. source_type='archive' AND trust != 'trusted' (cold archives — evict first)
          2. trust='untrusted' AND source_type NOT IN ('protected','archive')
          3. trust='semi'    AND source_type NOT IN ('protected','archive')
          4. LRU within tiers 1-3 (ONLY if self._lru_eviction_enabled — S3-RISK-004)

        dry_run=True: count evictable chunks without deleting anything.

        Returns:
          {
            evicted_count:     int,
            evicted_mb_estimate: float,
            tiers_used:        list[str],
          }
        """
        # Build the set of protected storage_keys from self._include_protected.
        # These are stored as repo-relative paths; we match prefix-style against storage_key.
        # NOTE: conn is passed in for the read queries. _delete_by_source_v2 opens its own
        # connection (BEGIN IMMEDIATE) for actual deletes — this is intentional.

        evicted_count = 0
        evicted_mb_estimate = 0.0
        tiers_used: list[str] = []

        # Pre-compute an estimate of bytes per chunk for mb accounting.
        # This is a rough heuristic — actual VACUUM savings may differ.
        try:
            total_refs = int(conn.execute("SELECT COUNT(*) FROM content_refs").fetchone()[0])
            current_size_mb = self._db_size_mb()
            bytes_per_chunk = (current_size_mb * 1024 * 1024 / total_refs) if total_refs > 0 else 4096
        except Exception:
            bytes_per_chunk = 4096

        def _still_over_budget() -> bool:
            # Re-check live size only in non-dry_run mode (deletions actually happened).
            if dry_run:
                # In dry_run: estimate based on what we'd have removed.
                return (current_size_mb - evicted_mb_estimate) > target_mb
            return self._db_size_mb() > target_mb

        def _protected_key_check(storage_key: str) -> bool:
            """Return True if storage_key is a protected path (never evict)."""
            for protected in self._include_protected:
                # Match exact or prefix (e.g. ".protocol-state/dev-notes.md")
                if storage_key == protected or storage_key.startswith(protected + "/"):
                    return True
            return False

        # SEC-ELAST-001 (v9.7.0 Phase 2): SQL-level include_protected guard.
        # Defense-in-depth on top of the Python _protected_key_check filter.
        # Build a parameterized NOT IN / NOT LIKE clause from self._include_protected.
        # When include_protected is empty (most prod cases), no extra clause is added.
        def _protected_sql_clause() -> tuple[str, list]:
            """Return (extra_where_clause, params) to exclude protected storage_keys.

            For each protected path P we exclude exact match (storage_key = P) AND
            prefix match (storage_key LIKE 'P/%').  Built as a list of NOT conditions
            joined by AND so the planner can use the storage_key index.
            Returns ('', []) when include_protected is empty (zero overhead).

            SEC-ELAST-002 (v9.7.1): escape `%`, `_`, and `\\` in the path before
            binding to prevent LIKE wildcard over-matching on protected paths that
            contain these characters.  ESCAPE '\\' is added to each NOT LIKE predicate.
            """
            if not self._include_protected:
                return "", []

            def _like_escape(s: str) -> str:
                """Escape LIKE special chars in s for use with ESCAPE '\\'."""
                return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

            conditions: list[str] = []
            params: list[str] = []
            for p in self._include_protected:
                p_esc = _like_escape(p)
                conditions.append("(storage_key != ? AND storage_key NOT LIKE ? ESCAPE '\\')")
                params.append(p)
                params.append(p_esc + "/%")
            clause = " AND " + " AND ".join(conditions)
            return clause, params

        def _get_evictable_by_tier(tier_name: str) -> list[str]:
            """Return ordered list of storage_keys to evict for the given tier.

            SEC-ELAST-001: SQL-level include_protected guard is applied at query time
            (defense-in-depth).  The Python _protected_key_check guard below is retained
            as the primary safety net (S3-RISK-001).
            """
            sql_guard, guard_params = _protected_sql_clause()
            if tier_name == "archive":
                rows = conn.execute(
                    f"""
                    SELECT DISTINCT storage_key
                    FROM content_refs
                    WHERE source_type = 'archive'
                      AND trust != 'trusted'
                      {sql_guard}
                    ORDER BY recorded_date ASC
                    """,
                    guard_params,
                ).fetchall()
            elif tier_name == "untrusted":
                rows = conn.execute(
                    f"""
                    SELECT DISTINCT storage_key
                    FROM content_refs
                    WHERE trust = 'untrusted'
                      AND source_type NOT IN ('protected', 'archive')
                      {sql_guard}
                    ORDER BY recorded_date ASC
                    """,
                    guard_params,
                ).fetchall()
            elif tier_name == "semi":
                rows = conn.execute(
                    f"""
                    SELECT DISTINCT storage_key
                    FROM content_refs
                    WHERE trust = 'semi'
                      AND source_type NOT IN ('protected', 'archive')
                      {sql_guard}
                    ORDER BY recorded_date ASC
                    """,
                    guard_params,
                ).fetchall()
            else:
                rows = []

            keys: list[str] = []
            for row in rows:
                skey = str(row[0])
                # S3-RISK-001: primary Python guard (double-check after SQL guard).
                if _protected_key_check(skey):
                    continue
                keys.append(skey)
            return keys

        def _get_evictable_lru_by_tier(tier_name: str) -> list[str]:
            """Return storage_keys ordered by LRU (last_recalled_at ASC, NULLs first).

            SEC-ELAST-001: SQL-level include_protected guard applied here too.
            """
            sql_guard, guard_params = _protected_sql_clause()
            if tier_name == "archive":
                rows = conn.execute(
                    f"""
                    SELECT DISTINCT storage_key,
                      COALESCE(last_recalled_at, '1970-01-01') AS lru_ts
                    FROM content_refs
                    WHERE source_type = 'archive'
                      AND trust != 'trusted'
                      {sql_guard}
                    ORDER BY lru_ts ASC
                    """,
                    guard_params,
                ).fetchall()
            elif tier_name == "untrusted":
                rows = conn.execute(
                    f"""
                    SELECT DISTINCT storage_key,
                      COALESCE(last_recalled_at, '1970-01-01') AS lru_ts
                    FROM content_refs
                    WHERE trust = 'untrusted'
                      AND source_type NOT IN ('protected', 'archive')
                      {sql_guard}
                    ORDER BY lru_ts ASC
                    """,
                    guard_params,
                ).fetchall()
            elif tier_name == "semi":
                rows = conn.execute(
                    f"""
                    SELECT DISTINCT storage_key,
                      COALESCE(last_recalled_at, '1970-01-01') AS lru_ts
                    FROM content_refs
                    WHERE trust = 'semi'
                      AND source_type NOT IN ('protected', 'archive')
                      {sql_guard}
                    ORDER BY lru_ts ASC
                    """,
                    guard_params,
                ).fetchall()
            else:
                rows = []

            keys: list[str] = []
            for row in rows:
                skey = str(row[0])
                # Primary Python guard retained (S3-RISK-001).
                if _protected_key_check(skey):
                    continue
                keys.append(skey)
            return keys

        # Determine ordering function: LRU (when enabled) or recorded_date (default)
        _get_evictable = (
            _get_evictable_lru_by_tier
            if self._lru_eviction_enabled and self._active_schema >= 4
            else _get_evictable_by_tier
        )

        # Priority order: archive → untrusted → semi
        for tier in ("archive", "untrusted", "semi"):
            if not _still_over_budget():
                break

            keys = _get_evictable(tier)
            if not keys:
                continue

            tier_used = False
            for skey in keys:
                if not _still_over_budget():
                    break

                # Count chunks for this source_key
                chunk_count = int(conn.execute(
                    "SELECT COUNT(*) FROM content_refs WHERE storage_key = ?", (skey,)
                ).fetchone()[0])

                if dry_run:
                    evicted_count += chunk_count
                    evicted_mb_estimate += (chunk_count * bytes_per_chunk) / (1024 * 1024)
                    tier_used = True
                else:
                    try:
                        removed = self._delete_by_source_v2(skey)
                        if removed > 0:
                            evicted_count += removed
                            evicted_mb_estimate += (removed * bytes_per_chunk) / (1024 * 1024)
                            tier_used = True
                    except Exception as exc:
                        _log.warning(
                            "eviction: failed to delete source %r — skipping (%s)", skey, exc
                        )

            if tier_used:
                tiers_used.append(tier)

        # S3-RISK-002: if still over budget after exhausting all evictable tiers,
        # log advisory and return — NEVER touch the never-evict set.
        if _still_over_budget() and not dry_run:
            _log.warning(
                "Cortex eviction: DB (%.1f MB) still exceeds budget (%.1f MB) after "
                "evicting all evictable content. Protected/trusted chunks cannot be "
                "evicted. Increase storage_budget_mb or remove data manually.",
                self._db_size_mb(),
                target_mb,
            )

        return {
            "evicted_count": evicted_count,
            "evicted_mb_estimate": evicted_mb_estimate,
            "tiers_used": tiers_used,
        }

    # -------------------------------------------------------------------------
    # WI-S3-6 (Stage 3 Phase 2, v9.7.0): Compaction — orphan sweep + VACUUM
    # -------------------------------------------------------------------------

    def compact(
        self,
        dry_run: bool = False,
        lock_path: "Path | None" = None,
        data_dir: "Path | None" = None,
        backup_retention_count: int = 3,
    ) -> dict:
        """Sweep orphaned content rows (no surviving content_refs) and VACUUM.

        An "orphan" is a content/content_vectors row whose content_hash has zero
        entries in content_refs.  This arises after _delete_by_source_v2() removes
        refs but a concurrent or aborted ingest left content rows without refs.

        S3-RISK-003: If lock_path is provided and exists, abort immediately with
        aborted_lock_held=True and 0 deletions.  The caller (brain compact CLI)
        passes db_dir/index.lock.

        SEC-UNIFIED-004 (P2): VACUUM may raise sqlite3.OperationalError when another
        connection holds the DB (e.g. a concurrent reader on WAL mode).  This is
        caught and logged as an advisory — compact() NEVER raises due to VACUUM.

        SEC-CORTEX-ACCESS-009 (v9.7.1): when data_dir is provided and orphan rows
        will be deleted (non-dry-run, non-locked), a backup is written to
        <data_dir>/backups/ before deletion. Backup failure is fail-soft.
        After compaction, run_integrity_check() is called; the result is included
        in the return dict under "integrity_check".

        Args:
            dry_run:               Count orphans without deleting.
            lock_path:             Path to an index.lock file.  If it exists, abort.
            data_dir:              External Cortex data directory for backup + integrity-flag.
                                   When None, backup and integrity-flag write are skipped.
            backup_retention_count: Max backups to keep (default 3).

        Returns dict:
            {
              "orphan_content_rows_deleted": int,
              "freed_mb_estimate":           float,
              "before_mb":                   float,
              "after_mb":                    float,
              "dry_run":                     bool,
              "aborted_lock_held":           bool,   # True iff aborted due to lock
              "integrity_check":             dict,   # run_integrity_check() result (when data_dir set)
            }
        """
        # S3-RISK-003: abort if index.lock is held
        if lock_path is not None and lock_path.exists():
            _log.warning(
                "compact: index.lock held at %s — aborting compact (S3-RISK-003)", lock_path
            )
            before_mb = self._db_size_mb()
            return {
                "orphan_content_rows_deleted": 0,
                "freed_mb_estimate": 0.0,
                "before_mb": before_mb,
                "after_mb": before_mb,
                "dry_run": dry_run,
                "aborted_lock_held": True,
            }

        # Ensure schema exists before operating (safe on a fresh/empty DB).
        self.init_schema()

        before_mb = self._db_size_mb()
        orphan_count = 0

        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            # Find all content_hash values that have no surviving content_refs.
            # NOT EXISTS is O(index lookup) — avoids N×M full scan.
            orphan_rows = conn.execute(
                """
                SELECT c.content_hash, c.vector_rowid
                FROM content c
                WHERE NOT EXISTS (
                    SELECT 1 FROM content_refs cr
                    WHERE cr.content_hash = c.content_hash
                )
                """
            ).fetchall()

            if dry_run:
                # Estimate freed MB based on current per-row average.
                try:
                    total_content = int(
                        conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
                    )
                    freed_mb_estimate = (
                        (before_mb * len(orphan_rows) / total_content)
                        if total_content > 0
                        else 0.0
                    )
                except Exception:
                    freed_mb_estimate = 0.0

                conn.execute("ROLLBACK")
                return {
                    "orphan_content_rows_deleted": len(orphan_rows),
                    "freed_mb_estimate": freed_mb_estimate,
                    "before_mb": before_mb,
                    "after_mb": before_mb,
                    "dry_run": True,
                    "aborted_lock_held": False,
                }

            # SEC-CORTEX-ACCESS-009: pre-op backup before any deletion (fail-soft).
            if data_dir is not None:
                self.backup_db(self.db_path, data_dir, backup_retention_count)

            # Real deletion: remove vector rows then content rows.
            for ch, vrid in orphan_rows:
                if vrid is not None:
                    conn.execute(
                        "DELETE FROM content_vectors WHERE rowid = ?", (int(vrid),)
                    )
                conn.execute(
                    "DELETE FROM content WHERE content_hash = ?", (ch,)
                )
                orphan_count += 1

            conn.execute("COMMIT")

        # VACUUM reclaims freed pages.
        # SEC-UNIFIED-004: _compact_vacuum() handles the try/except internally.
        # Outer try/except here defends against unexpected exceptions from overrides
        # (e.g. test monkeypatching) so compact() NEVER raises due to VACUUM.
        try:
            self._compact_vacuum()
        except Exception as exc:
            _log.warning(
                "compact: _compact_vacuum raised unexpectedly (fail-soft) — %s", exc
            )

        after_mb = self._db_size_mb()
        freed_mb = max(0.0, before_mb - after_mb)

        result: dict = {
            "orphan_content_rows_deleted": orphan_count,
            "freed_mb_estimate": freed_mb,
            "before_mb": before_mb,
            "after_mb": after_mb,
            "dry_run": False,
            "aborted_lock_held": False,
        }

        # SEC-CORTEX-ACCESS-009: post-compact integrity check (fail-soft).
        if data_dir is not None:
            ic_result = self.run_integrity_check(data_dir=data_dir)
            result["integrity_check"] = ic_result
        else:
            # Always include integrity_check key, even without data_dir
            ic_result = self.run_integrity_check(data_dir=None)
            result["integrity_check"] = ic_result

        return result

    def _compact_vacuum(self) -> None:
        """SEC-UNIFIED-004 (v9.7.0): Issue VACUUM to reclaim freed pages.

        Isolated as a method so tests can monkeypatch it to simulate
        OperationalError without patching sqlite3 globally.

        NEVER raises — OperationalError (e.g. DB locked by concurrent reader in
        WAL mode) is caught and logged as an advisory warning (fail-soft).
        """
        try:
            with self.connect() as vconn:
                vconn.execute("VACUUM")
        except Exception as exc:
            _log.warning(
                "compact: VACUUM failed (advisory, ignored) — %s "
                "(SEC-UNIFIED-004: VACUUM OperationalError is fail-soft)", exc
            )

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

                # --- BM25 maintenance (schema v3+ only, inside existing transaction) ---
                # FTS5 does not support UPSERT; DELETE + INSERT is the correct pattern.
                if self._active_schema >= 3 and self._bm25_available:
                    conn.execute(
                        "DELETE FROM cortex_bm25 WHERE ref_id = ?",
                        (ref_id,),
                    )
                    conn.execute(
                        "INSERT INTO cortex_bm25(ref_id, text, trust) VALUES (?, ?, ?)",
                        (ref_id, chunk.text, chunk.trust),
                    )

                conn.execute("COMMIT")
                changed += 1
        return changed

    def _upsert_bm25_batch(self, rows: list[tuple[str, str, str]]) -> int:
        """Migration-only helper: bulk-populate cortex_bm25 from (ref_id, text, trust) tuples.

        Processes in batches of 500 to bound transaction size. Used by WI-7 migration
        script to backfill BM25 after upgrading a v2 DB to v3. NOT called during normal
        ingest (that goes through _upsert_v2). Requires _active_schema >= 3.
        """
        if self._active_schema < 3 or not self._bm25_available:
            return 0
        batch_size = 500
        total = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            with self.connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                for ref_id, text, trust in batch:
                    conn.execute(
                        "DELETE FROM cortex_bm25 WHERE ref_id = ?",
                        (ref_id,),
                    )
                    conn.execute(
                        "INSERT INTO cortex_bm25(ref_id, text, trust) VALUES (?, ?, ?)",
                        (ref_id, text, trust),
                    )
                conn.execute("COMMIT")
                total += len(batch)
        return total

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

    # -------------------------------------------------------------------------
    # Graph delegation methods (WI-4, v9.6.0)
    # -------------------------------------------------------------------------

    def graph_conn(self) -> "sqlite3.Connection":
        """Return an open connection to the Cortex DB for graph operations.

        Caller is responsible for BEGIN/COMMIT and closing. Intended for
        use by graph.py helpers that accept an explicit conn argument.
        Requires schema >= 3 (graph tables must exist).
        """
        from .errors import GraphSchemaError

        self.init_schema()
        if self._active_schema < 3:
            raise GraphSchemaError(
                "Graph tables require schema v3; run: python .protocol-state/migrate_cortex_graph_9_6.py"
                " --execute --i-have-upgraded-all-installs"
            )
        return self.connect()

    def upsert_entity(self, **kwargs) -> None:
        """Delegate to graph.upsert_entity inside a BEGIN IMMEDIATE transaction.

        Injects install_id from Store context so callers do not need to supply it.
        Requires schema >= 3.  SEC-GRAPH-NEW-003: self.init_schema() is called first
        so a direct-API caller on a fresh v3 DB does not need to call it explicitly.
        """
        from .errors import GraphSchemaError
        from .graph import upsert_entity as _upsert_entity

        self.init_schema()  # SEC-GRAPH-NEW-003: idempotent; sets _active_schema
        if self._active_schema < 3:
            raise GraphSchemaError(
                "Graph tables require schema v3; run: python .protocol-state/migrate_cortex_graph_9_6.py"
                " --execute --i-have-upgraded-all-installs"
            )
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            _upsert_entity(conn, install_id=self._install_id or "local", **kwargs)
            conn.execute("COMMIT")

    def upsert_edge(self, **kwargs) -> str:
        """Delegate to graph.upsert_edge inside a BEGIN IMMEDIATE transaction.

        Returns the deterministic edge_id. Requires schema >= 3.  SEC-GRAPH-NEW-003:
        self.init_schema() is called first so a direct-API caller on a fresh v3 DB
        does not need to call it explicitly.
        """
        from .errors import GraphSchemaError
        from .graph import upsert_edge as _upsert_edge

        self.init_schema()  # SEC-GRAPH-NEW-003: idempotent; sets _active_schema
        if self._active_schema < 3:
            raise GraphSchemaError(
                "Graph tables require schema v3; run: python .protocol-state/migrate_cortex_graph_9_6.py"
                " --execute --i-have-upgraded-all-installs"
            )
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            edge_id = _upsert_edge(conn, install_id=self._install_id or "local", **kwargs)
            conn.execute("COMMIT")
        return edge_id

    def hybrid_search(
        self,
        query_text: str,
        vector: list[float],
        *,
        k: int = 5,
        trust: list[str] | None = None,
        rrf_k: int = 60,
        recency_half_life_days: float = 30.0,
        use_cache: bool = False,
        cache_ttl_seconds: int = 0,
    ) -> list[dict]:
        """WI-11 (PLAN-CORTEX-GRAPH-001 Phase 2): Hybrid BM25 + dense vector retrieval.

        Pipeline (Maki F3 — single connection for the read path where possible):
          1. Cache lookup (skipped if use_cache=False or ttl=0).
          2. BM25 lexical search (gracefully skipped if _bm25_available=False, S2-RISK-002).
          3. Dense vector search (existing _search_v2 path).
          4. rrf_fuse() — TRUE RRF + trust filter (SEC-GRAPH-006/008).
          5. Optional cache write.

        SEC-GRAPH-003: secrets in text_preview are redacted before returning (enforced
        inside rrf_fuse). The single-connection constraint (Maki F3) applies to the
        read pipeline; the cache WRITE uses its own short connection (BEGIN IMMEDIATE).
        SEC-GRAPH-008: only chunks within the requested trust set are returned.
        S2-RISK-002: if _bm25_available=False, falls back to vector-only without crashing.
        """
        from .retrieval import (
            _query_cache_key, _get_index_epoch,
            lookup_cache, store_cache,
            bm25_search, rrf_fuse,
        )

        self.init_schema()
        trust = trust or ["trusted", "semi", "untrusted"]

        # 1. Cache lookup
        if use_cache and cache_ttl_seconds > 0:
            epoch = _get_index_epoch(self)
            cache_key = _query_cache_key(query_text, trust=trust, k=k, index_epoch=epoch)
            hit = lookup_cache(self, cache_key)
            if hit is not None:
                return hit
        else:
            cache_key = None

        # 2. BM25 lexical search (S2-RISK-002: no-op if BM25 unavailable)
        bm25_results: list[dict] = []
        if self._bm25_available and self._active_schema >= 3:
            bm25_results = bm25_search(self, query_text, trust=trust, k=k * 2)

        # 3. Dense vector search (existing v2 path — works for v2, v3, v4)
        vector_results: list[dict] = []
        if self._active_schema in (2, 3, 4):
            try:
                vector_results = self.search(vector, k=k * 2, trust=trust)
            except Exception:
                vector_results = []

        # 4. RRF fusion (SEC-GRAPH-006/008 trust filter applied inside rrf_fuse)
        fused = rrf_fuse(
            bm25_results=bm25_results,
            vector_results=vector_results,
            rrf_k=rrf_k,
            trust=trust,
            recency_half_life_days=recency_half_life_days,
            k=k,
        )

        # 5. Optional cache write
        # SEC-HYBRID-004: pass real trust + k for auditability in metadata columns
        if use_cache and cache_ttl_seconds > 0 and cache_key is not None:
            store_cache(self, cache_key, fused, ttl_seconds=cache_ttl_seconds,
                        trust=trust, k=k)

        # WI-S3-4 (v9.7.0): update last_recalled_at on fused result chunks (BM25+vector).
        # Note: search() (step 3) already tracks vector hits; this catches BM25-only hits.
        # Only when lru_eviction_enabled=True AND schema v4 (column present).
        if self._lru_eviction_enabled and self._active_schema >= 4 and fused:
            self._update_last_recalled_at([r["id"] for r in fused if "id" in r])

        return fused

    def go_no_go_pack(self, release_entity_id: str, *, trust: list) -> dict:
        """Delegate to graph.go_no_go_pack.

        SEC-GRAPH-002: trust must be a strict subset of {'trusted','semi'}; raises
        ValueError if 'untrusted' is present (enforced inside graph.go_no_go_pack).
        Requires schema >= 3.  SEC-GRAPH-NEW-003: self.init_schema() is called first
        so a direct-API caller on a fresh v3 DB does not need to call it explicitly.
        """
        from .errors import GraphSchemaError
        from .graph import go_no_go_pack as _pack

        self.init_schema()  # SEC-GRAPH-NEW-003: idempotent; sets _active_schema
        if self._active_schema < 3:
            raise GraphSchemaError(
                "Graph tables require schema v3; run: python .protocol-state/migrate_cortex_graph_9_6.py"
                " --execute --i-have-upgraded-all-installs"
            )
        with self.connect() as conn:
            return _pack(conn, release_entity_id, trust=trust)


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
        if store._active_schema in (2, 3, 4):
            # v2/v3/v4: content-addressed metrics (v3+ is a superset of v2; same core tables).
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
        if store._active_schema in (2, 3, 4):
            # v2/v3/v4: same core tables; v3 adds graph tables, v4 adds last_recalled_at.
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
                "schema_version": store._active_schema,
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
