#!/usr/bin/env python3
"""
Cortex Storage Elasticity Migration v3 -> v4 (Stage 3 Phase 1, v9.7.0).

Migrates a Cortex SQLite DB from the v3 graph schema to the v4 storage-elasticity
schema: adds the nullable `last_recalled_at TEXT` column to `content_refs` and stamps
PRAGMA user_version = 4.

The v4 schema change is minimal — one ALTER TABLE — so there is no Phase B
(no BM25 rebuild, no vector backfill required). Phase A handles everything in a
single BEGIN IMMEDIATE transaction.

Usage:
    python migrate_cortex_elastic_9_7.py --check
    python migrate_cortex_elastic_9_7.py --execute --i-have-upgraded-all-installs
    python migrate_cortex_elastic_9_7.py --rollback
    python migrate_cortex_elastic_9_7.py --check   --db /path/to/brain.db
    python migrate_cortex_elastic_9_7.py --execute --i-have-upgraded-all-installs --repo /path/to/repo

Safety:
    - --check is read-only; makes no changes.
    - --execute backs up the DB to <db>.pre9_7.<UTC>.bak before any write.
    - Phase A: ADD COLUMN + version stamps in ONE BEGIN IMMEDIATE transaction (atomic).
      SQLite ALTER TABLE ADD COLUMN is transactional; the whole Phase A is atomic.
    - --i-have-upgraded-all-installs: shared-brain acknowledgment gate (S3-RISK-001/S2-RISK-001).
      Migration ABORTS if any cortex_installs row has supported_schema < 4 AND this
      flag is NOT passed. Even with the flag, the ledger check runs and blocks if
      an old install is present (the flag acknowledges risk, not bypasses the check).
    - --rollback restores the most-recent .pre9_7.*.bak backup.
    - SEC-GRAPH-010 (P2): DB path is validated; paths with '..' traversal are rejected.

References:
    WI-S3-10 (Stage 3 Phase 1, v9.7.0) — this script
    S3-RISK-001 — eviction safety (never-evict set must be preserved)
    SEC-GRAPH-010 (P2) — migration path traversal check
    PLAN-DESIGN-001 §0 — cortex_installs ledger gate pattern
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

V3 = 3
V4 = 4

# Expected schema after migration.
_TARGET_SCHEMA = V4

# Backup filename pattern produced by --execute.
# Example: brain.db.pre9_7.2026-06-17T14-30-00-123456Z.bak
_BACKUP_RE = re.compile(r"\.pre9_7\.\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(?:-\d+)?Z\.bak$")


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


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Return True if `column` exists in `table`.

    Uses PRAGMA table_info because SQLite ALTER TABLE ADD COLUMN IF NOT EXISTS
    is not supported — we must check manually before issuing the ALTER.
    """
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in cols)


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
            f"SEC-GRAPH-010: DB path contains '..' path traversal component: {db_path_str!r}. "
            "Specify an absolute path to the Cortex DB."
        )

    resolved = raw.expanduser().resolve()
    return resolved


# ---------------------------------------------------------------------------
# Backup helpers
# ---------------------------------------------------------------------------

def _backup_path(db: Path) -> Path:
    return db.parent / f"{db.name}.pre9_7.{_now_utc_filename()}.bak"


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
    """Find the most-recent .pre9_7.*.bak file next to the DB."""
    backups = sorted(
        (f for f in db.parent.iterdir() if _BACKUP_RE.search(f.name)),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return backups[0] if backups else None


# ---------------------------------------------------------------------------
# Resolve the DB path (mirrors migrate_cortex_graph_9_6.py convention)
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
# S3-RISK-001 / PLAN-DESIGN-001 §0: cross-install schema guard
# ---------------------------------------------------------------------------

def _check_all_installs_upgraded(conn: sqlite3.Connection) -> list[dict]:
    """Return a list of cortex_installs rows with supported_schema < 4.

    In a shared-brain environment, migrating to v4 bumps PRAGMA user_version to 4.
    Any engine still at SUPPORTED_SCHEMA <= 3 will immediately fail with
    SchemaTooNewError when it next opens the DB.

    If this list is non-empty, migration must be blocked unless the user has
    explicitly acknowledged the risk with --i-have-upgraded-all-installs.
    Even with that flag, we still block: the flag means "I have already upgraded
    all installs", so if the ledger still shows old installs, the user's claim
    is false and we refuse to proceed.
    """
    if not _table_exists(conn, "cortex_installs"):
        return []
    rows = conn.execute(
        "SELECT install_id, supported_schema, last_seen FROM cortex_installs WHERE supported_schema < ?",
        (V4,),
    ).fetchall()
    return [{"install_id": r[0], "supported_schema": r[1], "last_seen": r[2]} for r in rows]


# ---------------------------------------------------------------------------
# Phase A: DDL helpers
# ---------------------------------------------------------------------------

def _apply_v4_ddl(conn: sqlite3.Connection) -> None:
    """Apply the v4 storage-elasticity DDL inside an already-open transaction.

    v4 adds exactly one nullable column to content_refs:
      last_recalled_at TEXT  (S3-RISK-004: NULL by default, opt-in LRU tracking)

    SQLite ALTER TABLE ADD COLUMN does not support IF NOT EXISTS, so we check
    for column existence via _column_exists() before issuing the ALTER.

    Called exclusively within a BEGIN IMMEDIATE block — the whole Phase A is atomic.
    """
    if not _column_exists(conn, "content_refs", "last_recalled_at"):
        conn.execute(
            "ALTER TABLE content_refs ADD COLUMN last_recalled_at TEXT"
        )


# ---------------------------------------------------------------------------
# Public commands (called by CLI and tests)
# ---------------------------------------------------------------------------

def cmd_check(db: Path) -> int:
    """Read-only preflight check. Returns 0 if DB is ready to migrate v3 -> v4."""
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

        if user_v == V4:
            print("[INFO] DB is already at v4 — migration already applied.")
            return 1
        if user_v > V4:
            print(f"[ERROR] DB is at schema v{user_v}, newer than v4 target. Not migratable.")
            return 1
        if user_v != V3:
            print(f"[ERROR] Expected user_version=3 to migrate to v4; got {user_v}.")
            return 1

        # Count existing content_refs rows
        ref_count = 0
        if _table_exists(conn, "content_refs"):
            ref_count = int(conn.execute("SELECT COUNT(*) FROM content_refs").fetchone()[0])

        # Check install ledger
        old_installs = _check_all_installs_upgraded(conn)

        # Check column presence
        col_present = _column_exists(conn, "content_refs", "last_recalled_at")

        print(f"content_refs     : {ref_count}  (existing rows will get NULL last_recalled_at)")
        print(f"last_recalled_at : {'already present' if col_present else 'absent (will be added)'}")

        if old_installs:
            print(f"[WARN] {len(old_installs)} install(s) in cortex_installs with supported_schema < 4:")
            for row in old_installs:
                print(f"         install_id={row['install_id']}  schema={row['supported_schema']}  last_seen={row['last_seen']}")
            print("[WARN] Migration will fail unless all installs are upgraded first.")
            print("[WARN] Use --i-have-upgraded-all-installs only after upgrading ALL installs.")
        else:
            print("[OK] cortex_installs: all installs at schema >= 4 (or ledger empty).")

        print("[OK] DB is eligible for v3 -> v4 migration.")
        print("Run: python migrate_cortex_elastic_9_7.py --execute --i-have-upgraded-all-installs")
        return 0
    finally:
        conn.close()


def cmd_execute(db: Path, *, upgraded_flag: bool) -> int:
    """Execute the v3 -> v4 migration.

    upgraded_flag corresponds to --i-have-upgraded-all-installs.

    S3-RISK-001 / S2-RISK-001 gate: if any cortex_installs row has
    supported_schema < 4, migration is blocked regardless of upgraded_flag.
    The flag's purpose is to acknowledge the shared-brain risk, NOT to bypass
    the ledger check.

    Phase A (the only phase): BEGIN IMMEDIATE — ADD COLUMN + stamp user_version=4
    + update metadata. All DDL is inside one atomic transaction.
    """
    if not db.exists():
        print(f"[ERROR] DB not found: {db}", file=sys.stderr)
        return 1

    conn = _open_db(db)
    try:
        user_v = _get_user_version(conn)

        if user_v == V4:
            print("[INFO] DB is already at v4 — nothing to do.", file=sys.stderr)
            conn.close()
            return 1

        if user_v != V3:
            print(
                f"[ERROR] Expected user_version=3 to migrate to v4; got {user_v}. "
                "Run --check to diagnose.",
                file=sys.stderr,
            )
            conn.close()
            return 1

        # S3-RISK-001: check all installs in the ledger
        old_installs = _check_all_installs_upgraded(conn)
        if old_installs:
            print(
                f"[ERROR] S3-RISK-001: {len(old_installs)} install(s) in cortex_installs "
                "still report supported_schema < 4:",
                file=sys.stderr,
            )
            for row in old_installs:
                print(
                    f"  install_id={row['install_id']}  schema={row['supported_schema']}  "
                    f"last_seen={row['last_seen']}",
                    file=sys.stderr,
                )
            print(
                "\nMigration blocked. Upgrade ALL installs to v9.7.0+ first, then re-run.",
                file=sys.stderr,
            )
            conn.close()
            return 1

        # Require explicit acknowledgment for shared-brain safety
        if not upgraded_flag:
            print(
                "[ERROR] --i-have-upgraded-all-installs is required for migration.\n"
                "  This flag acknowledges that ALL DZP installs sharing this brain DB\n"
                "  have been upgraded to v9.7.0+. Without it, older engines will fail\n"
                "  with SchemaTooNewError (S3-RISK-001 / S2-RISK-001).\n"
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
        _apply_v4_ddl(conn)
        _set_user_version(conn, V4)
        conn.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', ?)",
            (str(V4),),
        )
        conn.execute("COMMIT")
        print("[OK] Phase A complete: v4 DDL applied, user_version=4 stamped.", file=sys.stderr)
    except Exception as exc:
        print(f"[ERROR] Phase A failed: {exc}", file=sys.stderr)
        print(f"[INFO] DB unchanged. Backup available at: {bak}", file=sys.stderr)
        conn.close()
        return 1
    finally:
        conn.close()

    print("[OK] Migration complete: v3 -> v4.", file=sys.stderr)
    return 0


def cmd_rollback(db: Path) -> int:
    """Restore the DB from the most-recent .pre9_7.*.bak backup."""
    bak = _find_latest_backup(db)
    if bak is None:
        print(f"[ERROR] No .pre9_7.*.bak backup found next to: {db}", file=sys.stderr)
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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="migrate_cortex_elastic_9_7",
        description="Cortex v3 -> v4 (storage elasticity) migration. Stage 3 Phase 1 WI-S3-10.",
    )
    parser.add_argument("--db", default=None, help="Explicit path to brain.db")
    parser.add_argument("--repo", default=None, help="Repository root (used to locate brain.db)")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Read-only preflight check")
    mode.add_argument("--execute", action="store_true", help="Apply v3 -> v4 migration")
    mode.add_argument("--rollback", action="store_true", help="Restore from latest backup")

    parser.add_argument(
        "--i-have-upgraded-all-installs",
        dest="upgraded_flag",
        action="store_true",
        default=False,
        help=(
            "Required for --execute in a shared-brain environment. "
            "Acknowledges that ALL DZP installs sharing this brain DB have been "
            "upgraded to v9.7.0+ (S3-RISK-001 mitigation)."
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

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
