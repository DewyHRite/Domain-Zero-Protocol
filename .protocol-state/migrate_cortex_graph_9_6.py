#!/usr/bin/env python3
"""
Cortex Graph Migration v2 -> v3 (graph layer, PLAN-CORTEX-GRAPH-001 Phase 1b).

Migrates a Cortex SQLite DB from the v2 content-addressed schema to the v3
graph schema: adds the four graph tables (cortex_entities, cortex_edges,
cortex_query_cache, cortex_bm25) and stamps PRAGMA user_version = 3.

Usage:
    python migrate_cortex_graph_9_6.py --check
    python migrate_cortex_graph_9_6.py --execute --i-have-upgraded-all-installs
    python migrate_cortex_graph_9_6.py --rollback
    python migrate_cortex_graph_9_6.py --rebuild-bm25
    python migrate_cortex_graph_9_6.py --check   --db /path/to/brain.db
    python migrate_cortex_graph_9_6.py --execute --i-have-upgraded-all-installs --repo /path/to/repo

Safety:
    - --check is read-only; makes no changes.
    - --execute backs up the DB to <db>.pre9_6.<UTC>.bak before any write.
    - Phase A: DDL + version stamps in ONE BEGIN IMMEDIATE transaction (atomic).
    - Phase B: BM25 rebuild in batched transactions (~500 rows per batch).
    - --i-have-upgraded-all-installs: shared-brain acknowledgment gate (S2-RISK-001).
      Migration ABORTS if any cortex_installs row has supported_schema < 3 unless
      this flag is explicitly passed. Even with the flag, the ledger check runs and
      blocks if an old install is present.
    - --rollback restores the most-recent .pre9_6.*.bak backup.
    - --rebuild-bm25 re-runs Phase B only (BM25 population from existing content_refs).
    - SEC-GRAPH-010: DB path is validated; paths with '..' traversal are rejected.

References:
    WI-7  (PLAN-CORTEX-GRAPH-001 Phase 1b) — this script
    S2-RISK-001 — cross-install schema lockout; mitigated by --i-have-upgraded-all-installs
    SEC-GRAPH-010 (P2) — migration path traversal check
"""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: locate the cortex package relative to this file.
# ---------------------------------------------------------------------------

_PROTO_STATE = Path(__file__).resolve().parent
_BRAIN_DIR = _PROTO_STATE / "brain"
if str(_BRAIN_DIR) not in sys.path:
    sys.path.insert(0, str(_BRAIN_DIR))

from cortex.store import (  # noqa: E402
    SUPPORTED_SCHEMA,
    Store,
)

# ---------------------------------------------------------------------------
# Schema version constants
# ---------------------------------------------------------------------------

V2 = 2
V3 = 3

# Expected schema after migration.
_TARGET_SCHEMA = V3

# Backup filename pattern produced by --execute.
# Example: brain.db.pre9_6.2026-06-17T14-30-00-123456Z.bak
_BACKUP_RE = re.compile(r"\.pre9_6\.\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(?:-\d+)?Z\.bak$")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _now_utc_filename() -> str:
    """UTC timestamp safe for use in a filename (colons replaced by dashes).
    Includes microseconds so concurrent calls produce distinct filenames.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%fZ")


def _open_db(db: Path, *, timeout: float = 10.0) -> sqlite3.Connection:
    """Open the DB with busy_timeout set."""
    conn = sqlite3.connect(str(db), timeout=timeout)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def _get_user_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _set_user_version(conn: sqlite3.Connection, v: int) -> None:
    conn.execute(f"PRAGMA user_version = {int(v)}")


def _read_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    return str(row[0]) if row else None


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _probe_fts5() -> bool:
    """Check whether FTS5 is available in this SQLite build (in-memory probe)."""
    try:
        probe = sqlite3.connect(":memory:")
        probe.execute("CREATE VIRTUAL TABLE _probe USING fts5(x)")
        probe.execute("DROP TABLE IF EXISTS _probe")
        probe.close()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# SEC-GRAPH-010: path validation
# ---------------------------------------------------------------------------

def _validate_db_path(db_path_str: str) -> Path:
    """Resolve and validate the DB path.

    SEC-GRAPH-010 (P2 — remediate-during-implementation):
    - Reject paths that contain '..' components before resolution (traversal attempt).
    - Resolve symlinks so the actual target is checked.
    - The resolved path must be an absolute path (sanity check; Path.resolve() always is).

    Returns the resolved Path if valid. Raises ValueError if traversal detected.
    """
    raw = Path(db_path_str)

    # Check for '..' in the raw path parts before resolution — this catches
    # intentional traversal attempts even if the resolved path happens to be safe.
    if ".." in raw.parts:
        raise ValueError(
            f"SEC-GRAPH-010: DB path contains '..' traversal component: {db_path_str!r}. "
            "Specify an absolute path to the Cortex DB."
        )

    resolved = raw.expanduser().resolve()
    return resolved


# ---------------------------------------------------------------------------
# Backup helpers
# ---------------------------------------------------------------------------

def _backup_path(db: Path) -> Path:
    return db.parent / f"{db.name}.pre9_6.{_now_utc_filename()}.bak"


def _create_backup(db: Path) -> Path:
    """Copy the DB to a timestamped .bak file. Returns the backup path.

    SEC-GRAPH-NEW-004: defense-in-depth assertion that the backup stays in the
    same directory as the DB — prevents a path manipulation attack where a
    crafted DB filename could escape the intended parent directory.
    """
    bak = _backup_path(db)
    # SEC-GRAPH-NEW-004: assert backup parent matches DB parent (resolved)
    if bak.parent.resolve() != db.parent.resolve():
        raise ValueError(
            f"SEC-GRAPH-NEW-004: backup path {bak!r} escapes the DB directory "
            f"{db.parent!r}. This should never happen with a well-formed DB path."
        )
    shutil.copy2(str(db), str(bak))
    if bak.stat().st_size != db.stat().st_size:
        bak.unlink(missing_ok=True)
        raise RuntimeError(f"Backup size mismatch: {db} vs {bak}")
    return bak


def _find_latest_backup(db: Path) -> Path | None:
    """Find the most-recent .pre9_6.*.bak file next to the DB."""
    backups = sorted(
        (f for f in db.parent.iterdir() if _BACKUP_RE.search(f.name)),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return backups[0] if backups else None


# ---------------------------------------------------------------------------
# Resolve the DB path (mirrors migrate_cortex_storage_9_4.py convention)
# ---------------------------------------------------------------------------

def _resolve_db(args_db: str | None, args_repo: str | None) -> Path:
    """Return the brain.db path from --db, --repo, or the default OS location."""
    if args_db:
        return _validate_db_path(args_db)
    from cortex import paths as _paths
    repo = Path(args_repo).resolve() if args_repo else Path.cwd()
    try:
        config: dict[str, Any] = {}
        cfg_file = repo / ".protocol-state" / "brain" / "brain.config.yaml"
        if cfg_file.exists():
            import re as _re
            text = cfg_file.read_text(encoding="utf-8")
            for line in text.splitlines():
                m = _re.match(r"^\s*(\w+)\s*:\s*(.+)", line)
                if m:
                    config[m.group(1).strip()] = m.group(2).strip().strip('"').strip("'")
        db = _paths.db_path(repo, config, allow_unsafe=True)
        return db
    except Exception as exc:
        print(f"[WARN] Could not resolve DB via cortex.paths: {exc}", file=sys.stderr)
        print("[WARN] Falling back to cwd/brain.db — use --db to specify explicitly.", file=sys.stderr)
        return Path.cwd() / "brain.db"


# ---------------------------------------------------------------------------
# S2-RISK-001: cross-install schema guard
# ---------------------------------------------------------------------------

def _check_all_installs_upgraded(conn: sqlite3.Connection) -> list[dict]:
    """Return a list of cortex_installs rows with supported_schema < 3.

    S2-RISK-001: in a shared-brain environment, migrating to v3 bumps
    PRAGMA user_version to 3. Any engine still at SUPPORTED_SCHEMA=2 will
    immediately fail with SchemaTooNewError when it next opens the DB.

    If this list is non-empty, migration must be blocked unless the user
    has explicitly acknowledged the risk with --i-have-upgraded-all-installs.
    Even with that flag present, we still block: the flag means "I have already
    upgraded all installs", which implies the ledger should be clear. If it is
    not clear, the user's claim is false and we refuse to proceed.
    """
    if not _table_exists(conn, "cortex_installs"):
        return []
    rows = conn.execute(
        "SELECT install_id, supported_schema, last_seen FROM cortex_installs WHERE supported_schema < ?",
        (V3,),
    ).fetchall()
    return [{"install_id": r[0], "supported_schema": r[1], "last_seen": r[2]} for r in rows]


# ---------------------------------------------------------------------------
# v3 DDL helpers (Phase A)
# ---------------------------------------------------------------------------

def _apply_v3_ddl(conn: sqlite3.Connection) -> None:
    """Apply the v3 graph tables inside an already-open transaction.

    Mirrors Store._create_v3_schema() but handles the FTS5 case inline.
    Called exclusively within a BEGIN IMMEDIATE block.
    """
    # cortex_entities
    conn.execute("""
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
    """)
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

    # cortex_edges
    conn.execute("""
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
    """)
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

    # cortex_query_cache
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cortex_query_cache (
          cache_key        TEXT PRIMARY KEY,
          query_hash       TEXT NOT NULL,
          trust_filter     TEXT NOT NULL,
          k                INTEGER NOT NULL,
          created_at       TEXT NOT NULL,
          expires_at       TEXT NOT NULL,
          result_json      TEXT NOT NULL
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_cache_expires ON cortex_query_cache(expires_at)"
    )

    # cortex_bm25 — FTS5 virtual table; wrapped in try/except (FTS5 may be absent)
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS cortex_bm25
              USING fts5(
                ref_id   UNINDEXED,
                text,
                trust    UNINDEXED,
                tokenize = 'unicode61 remove_diacritics 1'
              )
        """)
    except Exception:
        # FTS5 not available — cortex_bm25 not created; BM25 Phase B will be skipped.
        pass


# ---------------------------------------------------------------------------
# Phase B: BM25 rebuild helper
# ---------------------------------------------------------------------------

def _rebuild_bm25_from_refs(conn_factory, *, batch_size: int = 500) -> int:
    """Populate cortex_bm25 from content + content_refs.

    Called from Phase B of --execute and from --rebuild-bm25.
    Returns total rows inserted. Returns 0 if FTS5 is unavailable.

    conn_factory is a callable that returns a new sqlite3.Connection each call
    (used for batched transactions; each batch gets its own BEGIN IMMEDIATE).
    """
    if not _probe_fts5():
        print("[INFO] FTS5 not available — BM25 rebuild skipped.", file=sys.stderr)
        return 0

    # Fetch all (ref_id, text, trust) pairs from content_refs JOIN content
    with conn_factory() as conn:
        rows = conn.execute(
            """
            SELECT cr.ref_id, c.text, cr.trust
            FROM content_refs cr
            JOIN content c ON cr.content_hash = c.content_hash
            ORDER BY cr.ref_id
            """
        ).fetchall()

    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        with conn_factory() as conn:
            conn.execute("BEGIN IMMEDIATE")
            for ref_id, text, trust in batch:
                conn.execute("DELETE FROM cortex_bm25 WHERE ref_id = ?", (ref_id,))
                conn.execute(
                    "INSERT INTO cortex_bm25(ref_id, text, trust) VALUES (?, ?, ?)",
                    (ref_id, text, trust),
                )
            conn.execute("COMMIT")
            total += len(batch)

    return total


# ---------------------------------------------------------------------------
# Public commands (called by CLI and tests)
# ---------------------------------------------------------------------------

def cmd_check(db: Path) -> int:
    """Read-only preflight check. Returns 0 if DB is ready to migrate."""
    if not db.exists():
        print(f"[ERROR] DB not found: {db}", file=sys.stderr)
        return 1

    conn = _open_db(db)
    try:
        user_v = _get_user_version(conn)
        meta_v = _read_meta(conn, "schema_version") if _table_exists(conn, "metadata") else None

        print(f"DB path          : {db}")
        print(f"user_version     : {user_v}")
        print(f"metadata mirror  : {meta_v!r}")

        if user_v == V3:
            print("[INFO] DB is already at v3 — migration already applied.")
            return 1
        if user_v > V3:
            print(f"[ERROR] DB is at schema v{user_v}, newer than v3 target. Not migratable.")
            return 1
        if user_v != V2:
            print(f"[ERROR] Expected user_version=2 to migrate to v3; got {user_v}.")
            return 1

        # Count existing content_refs that will become BM25 rows
        ref_count = 0
        if _table_exists(conn, "content_refs"):
            ref_count = int(conn.execute("SELECT COUNT(*) FROM content_refs").fetchone()[0])

        # Check install ledger
        old_installs = _check_all_installs_upgraded(conn)

        print(f"content_refs     : {ref_count}  (will be BM25-indexed in Phase B)")
        print(f"FTS5 available   : {_probe_fts5()}")

        if old_installs:
            print(f"[WARN] {len(old_installs)} install(s) in cortex_installs with supported_schema < 3:")
            for row in old_installs:
                print(f"         install_id={row['install_id']}  schema={row['supported_schema']}  last_seen={row['last_seen']}")
            print("[WARN] Migration will fail unless all installs are upgraded first.")
            print("[WARN] Use --i-have-upgraded-all-installs only after upgrading ALL installs.")
        else:
            print("[OK] cortex_installs: all installs at schema >= 3 (or ledger empty).")

        print("[OK] DB is eligible for v2 -> v3 migration.")
        print("Run: python migrate_cortex_graph_9_6.py --execute --i-have-upgraded-all-installs")
        return 0
    finally:
        conn.close()


def cmd_execute(db: Path, *, upgraded_flag: bool) -> int:
    """Execute the v2 -> v3 migration.

    upgraded_flag corresponds to --i-have-upgraded-all-installs.

    S2-RISK-001 gate: if any cortex_installs row has supported_schema < 3,
    migration is blocked regardless of upgraded_flag. The flag's purpose is
    to acknowledge the shared-brain risk, NOT to bypass the ledger check.

    Phase A: BEGIN IMMEDIATE — apply DDL + stamp user_version=3 + update metadata.
    Phase B: BM25 rebuild in batched transactions (~500 rows each).
    """
    if not db.exists():
        print(f"[ERROR] DB not found: {db}", file=sys.stderr)
        return 1

    conn = _open_db(db)
    try:
        user_v = _get_user_version(conn)

        if user_v == V3:
            print("[INFO] DB is already at v3 — nothing to do.", file=sys.stderr)
            conn.close()
            return 1

        if user_v != V2:
            print(
                f"[ERROR] Expected user_version=2 to migrate to v3; got {user_v}. "
                "Run --check to diagnose.",
                file=sys.stderr,
            )
            conn.close()
            return 1

        # S2-RISK-001: check all installs in the ledger
        old_installs = _check_all_installs_upgraded(conn)
        if old_installs:
            print(
                f"[ERROR] S2-RISK-001: {len(old_installs)} install(s) in cortex_installs "
                "still report supported_schema < 3:",
                file=sys.stderr,
            )
            for row in old_installs:
                print(
                    f"  install_id={row['install_id']}  schema={row['supported_schema']}  "
                    f"last_seen={row['last_seen']}",
                    file=sys.stderr,
                )
            print(
                "\nMigration blocked. Upgrade ALL installs to v9.6.0+ first, then re-run.",
                file=sys.stderr,
            )
            conn.close()
            return 1

        # Require explicit acknowledgment for shared-brain safety
        if not upgraded_flag:
            print(
                "[ERROR] --i-have-upgraded-all-installs is required for migration.\n"
                "  This flag acknowledges that ALL DZP installs sharing this brain DB\n"
                "  have been upgraded to v9.6.0+. Without it, older engines will fail\n"
                "  with SchemaTooNewError (S2-RISK-001).\n"
                "  Re-run with: --execute --i-have-upgraded-all-installs",
                file=sys.stderr,
            )
            conn.close()
            return 1

        conn.close()
    except Exception:
        conn.close()
        raise

    # ----- Phase A: backup + DDL + version stamps in ONE BEGIN IMMEDIATE -----
    print(f"[INFO] Creating backup of {db} ...", file=sys.stderr)
    bak = _create_backup(db)
    print(f"[INFO] Backup created: {bak}", file=sys.stderr)

    conn = _open_db(db)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _apply_v3_ddl(conn)
        _set_user_version(conn, V3)
        conn.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', ?)",
            (str(V3),),
        )
        conn.execute("COMMIT")
        print("[OK] Phase A complete: v3 DDL applied, user_version=3 stamped.", file=sys.stderr)
    except Exception as exc:
        print(f"[ERROR] Phase A failed: {exc}", file=sys.stderr)
        print(f"[INFO] DB unchanged. Backup available at: {bak}", file=sys.stderr)
        conn.close()
        return 1
    finally:
        conn.close()

    # ----- Phase B: BM25 rebuild (batched, outside Phase A transaction) -----
    def _conn_factory() -> sqlite3.Connection:
        return _open_db(db)

    print("[INFO] Phase B: rebuilding BM25 index ...", file=sys.stderr)
    bm25_count = _rebuild_bm25_from_refs(_conn_factory)
    print(f"[OK] Phase B complete: {bm25_count} BM25 rows populated.", file=sys.stderr)

    print("[OK] Migration complete: v2 -> v3.", file=sys.stderr)
    return 0


def cmd_rollback(db: Path) -> int:
    """Restore the DB from the most-recent .pre9_6.*.bak backup."""
    bak = _find_latest_backup(db)
    if bak is None:
        print(f"[ERROR] No .pre9_6.*.bak backup found next to: {db}", file=sys.stderr)
        return 1

    print(f"[INFO] Restoring from backup: {bak}", file=sys.stderr)
    shutil.copy2(str(bak), str(db))

    # Verify restore
    conn = _open_db(db)
    try:
        user_v = _get_user_version(conn)
    finally:
        conn.close()

    print(f"[OK] Rollback complete. DB restored to schema v{user_v}.", file=sys.stderr)
    return 0


def cmd_rebuild_bm25(db: Path) -> int:
    """Re-run Phase B only: rebuild the BM25 index from existing content_refs.

    Useful for recovering from an interrupted Phase B without re-applying Phase A.
    """
    if not db.exists():
        print(f"[ERROR] DB not found: {db}", file=sys.stderr)
        return 1

    conn = _open_db(db)
    try:
        user_v = _get_user_version(conn)
        if user_v < V3:
            print(
                f"[ERROR] --rebuild-bm25 requires a v3 DB (user_version=3); got {user_v}.\n"
                "  Run --execute first to migrate to v3.",
                file=sys.stderr,
            )
            conn.close()
            return 1
        bm25_table_exists = _table_exists(conn, "cortex_bm25")
    finally:
        conn.close()

    if not bm25_table_exists:
        print("[ERROR] cortex_bm25 table not found. FTS5 may be unavailable on this build.", file=sys.stderr)
        return 1

    def _conn_factory() -> sqlite3.Connection:
        return _open_db(db)

    print("[INFO] Rebuilding BM25 index ...", file=sys.stderr)
    count = _rebuild_bm25_from_refs(_conn_factory)
    print(f"[OK] BM25 rebuild complete: {count} rows.", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="migrate_cortex_graph_9_6",
        description="Cortex v2 -> v3 (graph layer) migration. PLAN-CORTEX-GRAPH-001 WI-7.",
    )
    parser.add_argument("--db", default=None, help="Explicit path to brain.db")
    parser.add_argument("--repo", default=None, help="Repository root (used to locate brain.db)")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Read-only preflight check")
    mode.add_argument("--execute", action="store_true", help="Apply v2 -> v3 migration")
    mode.add_argument("--rollback", action="store_true", help="Restore from latest backup")
    mode.add_argument(
        "--rebuild-bm25",
        action="store_true",
        help="Re-run Phase B only: repopulate BM25 from existing content_refs",
    )

    parser.add_argument(
        "--i-have-upgraded-all-installs",
        dest="upgraded_flag",
        action="store_true",
        default=False,
        help=(
            "Required for --execute in a shared-brain environment. "
            "Acknowledges that ALL DZP installs sharing this brain DB have been "
            "upgraded to v9.6.0+ (S2-RISK-001 mitigation)."
        ),
    )

    args = parser.parse_args(argv)

    # SEC-GRAPH-010: validate DB path early
    try:
        db = _resolve_db(args.db, args.repo)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    if args.check:
        return cmd_check(db)
    if args.execute:
        return cmd_execute(db, upgraded_flag=args.upgraded_flag)
    if args.rollback:
        return cmd_rollback(db)
    if args.rebuild_bm25:
        return cmd_rebuild_bm25(db)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
