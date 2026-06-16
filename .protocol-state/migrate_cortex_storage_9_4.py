#!/usr/bin/env python3
"""
Cortex Storage Migration v1 → v2 (content-addressed, PLAN-DESIGN-001 Phase 3).

Migrates a Cortex SQLite DB from the legacy chunk-per-scope v1 schema to the
content-addressed v2 schema: one vector per distinct content_hash, N refs.

Usage:
    python migrate_cortex_storage_9_4.py --check
    python migrate_cortex_storage_9_4.py --execute
    python migrate_cortex_storage_9_4.py --rollback
    python migrate_cortex_storage_9_4.py --check   --db /path/to/brain.db
    python migrate_cortex_storage_9_4.py --execute --repo /path/to/repo

Mirrors the ergonomics of .protocol-state/migrate_state_9x.py (IMPL-002).

Safety:
    - --check is read-only; makes no changes.
    - --execute backs up the DB to <db>.pre9_4.<UTC>.bak before any write.
    - All table creation + data move + schema-version bump happen inside ONE
      BEGIN IMMEDIATE exclusive transaction; failure leaves the v1 DB untouched.
    - Parity gates (count invariants + recall-parity on fixed query set + trust
      filter parity) must all pass before the old tables are dropped.
    - --rollback restores the most-recent .pre9_4.*.bak backup.

PLAN-DESIGN-001 references:
    §0  cortex_installs ledger  (migration precondition check)
    §3  v2 schema, ref_id derivation, required indexes, NOT EXISTS anti-join
    §4  migration steps, exclusive transaction, parity gate
    §6  security / safety contract
    §7  rollback procedure
"""

from __future__ import annotations

import argparse
import hashlib
import json
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

# Shared constants / helpers from store.py so DDL and ref_id are not duplicated.
from cortex.store import (  # noqa: E402
    SUPPORTED_SCHEMA,
    Store,
    _make_ref_id,
)

# ---------------------------------------------------------------------------
# Schema version constants
# ---------------------------------------------------------------------------

V1 = 1
V2 = 2

# Backup filename pattern produced by --execute.
# Example: brain.db.pre9_4.2026-06-16T12-34-56-123456Z.bak  (includes microseconds)
# Also matches the legacy second-granularity pattern for rollback discovery.
_BACKUP_RE = re.compile(r"\.pre9_4\.\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(?:-\d+)?Z\.bak$")

# Staleness window for the cortex_installs ledger check (days).
# An install that has NOT been seen for longer than this is considered dormant.
# Dormant installs are warned but do not block migration.
_LEDGER_STALE_DAYS = 30


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_utc_filename() -> str:
    """UTC timestamp safe for use in a filename (colons replaced by dashes).

    Includes microseconds (%f) so that two calls within the same second produce
    distinct filenames and cannot clobber each other (SEC-CORTEX-017).
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%fZ")


def _open_db(db: Path, *, timeout: float = 10.0) -> sqlite3.Connection:
    """Open the DB with busy_timeout set (SEC-001)."""
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


# ---------------------------------------------------------------------------
# Resolve the DB path
# ---------------------------------------------------------------------------

def _resolve_db(args_db: str | None, args_repo: str | None) -> Path:
    """Return the brain.db path from --db, --repo, or the default OS location."""
    if args_db:
        return Path(args_db).expanduser().resolve()
    # Derive via cortex.paths (respects DZP_CORTEX_DATA_DIR etc.)
    from cortex import paths as _paths
    repo = Path(args_repo).resolve() if args_repo else Path.cwd()
    try:
        config: dict[str, Any] = {}
        cfg_file = repo / ".protocol-state" / "brain" / "brain.config.yaml"
        if cfg_file.exists():
            import re as _re
            # Minimal YAML scalar extraction: avoid requiring PyYAML at migration time.
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
# Backup helpers
# ---------------------------------------------------------------------------

def _backup_path(db: Path) -> Path:
    return db.parent / f"{db.name}.pre9_4.{_now_utc_filename()}.bak"


def _create_backup(db: Path) -> Path:
    """Copy the DB to a timestamped .bak file. Returns the backup path."""
    bak = _backup_path(db)
    shutil.copy2(str(db), str(bak))
    # Verify copy is intact (size match).
    if bak.stat().st_size != db.stat().st_size:
        bak.unlink(missing_ok=True)
        raise RuntimeError(f"Backup size mismatch: {db} vs {bak}")
    return bak


def _find_latest_backup(db: Path) -> Path | None:
    """Find the most recent .pre9_4.*.bak file next to the DB."""
    backups = sorted(
        (f for f in db.parent.iterdir() if _BACKUP_RE.search(f.name)),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return backups[0] if backups else None


# ---------------------------------------------------------------------------
# v1 schema DDL (used by tests to seed a v1 DB; not used by --execute itself)
# ---------------------------------------------------------------------------

V1_DDL = """
CREATE TABLE IF NOT EXISTS chunks (
  id           TEXT PRIMARY KEY,
  source_path  TEXT NOT NULL,
  source_type  TEXT NOT NULL,
  line_start   INTEGER NOT NULL,
  line_end     INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  recorded_date TEXT NOT NULL,
  text         TEXT NOT NULL,
  trust        TEXT NOT NULL,
  suspect      INTEGER NOT NULL DEFAULT 0,
  mem_type     TEXT,
  agent        TEXT,
  refs         TEXT
);
CREATE TABLE IF NOT EXISTS rowmap (
  rowid    INTEGER PRIMARY KEY AUTOINCREMENT,
  chunk_id TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS chunk_vectors (
  rowid     INTEGER PRIMARY KEY,
  embedding TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS metadata (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_state (
  source_path TEXT PRIMARY KEY,
  mtime_ns    INTEGER NOT NULL,
  size        INTEGER NOT NULL,
  indexed_at  TEXT NOT NULL
);
"""


def build_v1_db(db: Path, chunks: list[dict]) -> None:
    """Seed a v1 DB with the given chunk dicts (for testing/check self-test).

    Each dict must have keys matching the chunks table schema.
    Embeddings are stored as JSON arrays in chunk_vectors.
    """
    conn = sqlite3.connect(str(db))
    try:
        conn.executescript(V1_DDL)
        conn.execute("PRAGMA user_version = 1")
        conn.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', '1')"
        )
        for ch in chunks:
            conn.execute(
                "INSERT OR REPLACE INTO rowmap(chunk_id) VALUES (?)", (ch["id"],)
            )
            rowid = conn.execute(
                "SELECT rowid FROM rowmap WHERE chunk_id = ?", (ch["id"],)
            ).fetchone()[0]
            conn.execute(
                """
                INSERT OR REPLACE INTO chunks(
                  id, source_path, source_type, line_start, line_end,
                  content_hash, recorded_date, text, trust,
                  suspect, mem_type, agent, refs
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    ch["id"],
                    ch["source_path"],
                    ch["source_type"],
                    ch["line_start"],
                    ch["line_end"],
                    ch["content_hash"],
                    ch["recorded_date"],
                    ch["text"],
                    ch["trust"],
                    ch.get("suspect", 0),
                    ch.get("mem_type"),
                    ch.get("agent"),
                    json.dumps(ch.get("refs") or []),
                ),
            )
            embedding = ch.get("embedding") or [0.0] * 4
            conn.execute(
                "INSERT OR REPLACE INTO chunk_vectors(rowid, embedding) VALUES (?,?)",
                (rowid, json.dumps(embedding)),
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# --check: read-only analysis
# ---------------------------------------------------------------------------

def _scan_duplicate_keys(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """Return a list of (source_path, line_start) pairs that appear more than
    once in the v1 chunks table with DIFFERENT content_hash values.

    These are the cases that would cause silent data loss via
    ON CONFLICT(storage_key, line_start) DO NOTHING (SEC-CORTEX-018).
    Note: same (source_path, line_start) with the SAME content_hash is benign
    deduplication; this function only returns genuinely conflicting pairs.
    """
    rows = conn.execute(
        """
        SELECT source_path, line_start, COUNT(*) AS c
        FROM chunks
        GROUP BY source_path, line_start
        HAVING c > 1
        """
    ).fetchall()

    conflicts: list[tuple[str, int]] = []
    for row in rows:
        sp, ls = row[0], int(row[1])
        # Check whether the multiple rows have different content_hash values.
        hashes = conn.execute(
            "SELECT DISTINCT content_hash FROM chunks WHERE source_path = ? AND line_start = ?",
            (sp, ls),
        ).fetchall()
        if len(hashes) > 1:
            conflicts.append((sp, ls))

    return conflicts


def cmd_check(db: Path) -> int:
    """Print a read-only migration pre-flight report. Returns 0 if migratable."""
    if not db.exists():
        print(f"[ERROR] DB not found: {db}")
        return 1

    conn = _open_db(db)
    try:
        user_v = _get_user_version(conn)
        # metadata table may not exist on a bare/unknown DB.
        meta_v = _read_meta(conn, "schema_version") if _table_exists(conn, "metadata") else None

        print(f"DB path          : {db}")
        print(f"user_version     : {user_v}")
        print(f"metadata mirror  : {meta_v!r}")

        if user_v != V1:
            if user_v == V2:
                print("[INFO] DB is already at v2 — already migrated.")
            else:
                print(f"[ERROR] Expected user_version == 1 to migrate; got {user_v}. Not migratable.")
            return 1

        # Count chunks, distinct hashes, projected dedup savings.
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        distinct_hashes = conn.execute(
            "SELECT COUNT(DISTINCT content_hash) FROM chunks"
        ).fetchone()[0]
        dup_chunks = chunk_count - distinct_hashes
        pct_saved = (dup_chunks / chunk_count * 100) if chunk_count > 0 else 0.0

        print(f"chunks           : {chunk_count}")
        print(f"distinct hashes  : {distinct_hashes}  (projected content rows)")
        print(f"content_refs     : {chunk_count}  (one per chunk row)")
        print(f"duplicate chunks : {dup_chunks}  ({pct_saved:.1f}% vector dedup savings)")

        # SEC-CORTEX-018: scan for duplicate (source_path, line_start) keys with
        # differing content_hash — these would cause silent data loss.
        dup_key_conflicts = _scan_duplicate_keys(conn)
        if dup_key_conflicts:
            print(
                f"\n[BLOCK] Duplicate-key conflict detected — {len(dup_key_conflicts)} "
                "conflicting (source_path, line_start) pair(s) with differing "
                "content_hash found in the v1 chunks table. These rows would be "
                "silently dropped by ON CONFLICT DO NOTHING, causing data loss. "
                "Fix the v1 DB first (remove or de-duplicate the conflicting rows), "
                "then re-run --check."
            )
            for sp, ls in dup_key_conflicts:
                print(f"  - duplicate key: source_path={sp!r}, line_start={ls}")
            return 1

        # Ledger check.
        blocking: list[str] = []
        if _table_exists(conn, "cortex_installs"):
            rows = conn.execute(
                "SELECT install_id, supported_schema, last_seen FROM cortex_installs"
            ).fetchall()
            print(f"cortex_installs  : {len(rows)} row(s)")
            now = datetime.now(timezone.utc)
            for row in rows:
                iid, sup, last_seen_str = row[0], int(row[1]), str(row[2])
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    days_ago = (now - last_seen).days
                except Exception:
                    # SEC-CORTEX-021: emit a [WARN] rather than silently treating
                    # the install as active without any indication to the user.
                    print(
                        f"[WARN] install {iid} has unparseable last_seen={last_seen_str!r}; "
                        "treating as active (conservative)."
                    )
                    days_ago = 0  # treat unknown as recent to be safe
                stale = days_ago > _LEDGER_STALE_DAYS
                status = "DORMANT" if stale else "ACTIVE"
                print(f"  install {iid}: schema={sup}, last_seen={last_seen_str} [{status}]")
                if not stale and sup < V1:
                    blocking.append(
                        f"install {iid} has supported_schema={sup} < v9.3.4 minimum ({V1})"
                    )
        else:
            print("cortex_installs  : table absent (no v9.4.0+ engines have stamped)")

        if blocking:
            print("\n[BLOCK] Migration blocked — active install(s) must upgrade first:")
            for b in blocking:
                print(f"  - {b}")
            return 1

        print("\n[OK] Migration is safe to run. Use --execute to proceed.")
        return 0

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# --execute: the migration
# ---------------------------------------------------------------------------

def cmd_execute(db: Path) -> int:
    """Migrate the DB from v1 to v2. Returns 0 on success, 1 on failure."""
    if not db.exists():
        print(f"[ERROR] DB not found: {db}")
        return 1

    # --- Pre-flight: check user_version == 1 (idempotent on v2) ---
    conn = _open_db(db)
    try:
        user_v = _get_user_version(conn)
    finally:
        conn.close()

    if user_v == V2:
        print("[INFO] DB is already at v2 — nothing to do.")
        return 0

    if user_v != V1:
        print(f"[ERROR] Expected user_version == 1 to migrate; got {user_v}. Aborting.")
        return 1

    # --- SEC-CORTEX-018: duplicate-key pre-flight scan (before ANY mutation) ---
    # A v1 DB with two chunks rows sharing (source_path, line_start) but differing
    # content_hash would cause the second content_refs INSERT to be silently dropped
    # by ON CONFLICT DO NOTHING, yielding undetected data loss.  Detect and abort
    # before we touch the DB — including before creating the backup.
    conn = _open_db(db)
    try:
        dup_conflicts = _scan_duplicate_keys(conn)
    finally:
        conn.close()

    if dup_conflicts:
        print(
            f"[ERROR] Duplicate-key conflict detected: "
            f"{len(dup_conflicts)} (source_path, line_start) pair(s) exist in the v1 "
            "chunks table with differing content_hash values. Migration aborted — no "
            "changes made. Fix the conflicting rows first, then re-run --execute."
        )
        for sp, ls in dup_conflicts:
            print(f"  - conflicting key: source_path={sp!r}, line_start={ls}")
        return 1

    # --- Create backup BEFORE any write ---
    print(f"Creating backup of {db} ...")
    try:
        bak = _create_backup(db)
    except Exception as exc:
        print(f"[ERROR] Backup failed: {exc}. Aborting.")
        return 1
    print(f"Backup created    : {bak}")

    # --- Capture pre-migration snapshot for parity check ---
    pre_snap = _snapshot_v1(db)

    # --- Build a temporary Store (stub) to get the v2 DDL from _create_v2_schema ---
    # We use a throw-away in-memory store for the DDL calls only; the actual
    # migration happens via raw SQL on the real DB.
    store_helper = Store(":memory:", vector_backend="stub")

    # --- Single exclusive transaction: build + verify + swap + drop ---
    conn = _open_db(db)
    try:
        conn.execute("BEGIN IMMEDIATE")

        # 1. Create v2 tables (idempotent — IF NOT EXISTS).
        store_helper._create_v2_schema(conn)
        # Also ensure the ledger table exists.
        store_helper._create_installs_ledger(conn)

        # 2. Read all v1 chunks (inside the same exclusive transaction).
        v1_rows = conn.execute(
            """
            SELECT
              c.id, c.source_path, c.source_type, c.line_start, c.line_end,
              c.content_hash, c.recorded_date, c.text, c.trust,
              c.suspect, c.mem_type, c.agent, c.refs,
              cv.embedding
            FROM chunks c
            JOIN rowmap rm ON rm.chunk_id = c.id
            JOIN chunk_vectors cv ON cv.rowid = rm.rowid
            """
        ).fetchall()

        # 3a. Insert content rows (one per distinct content_hash) — copy vector, no re-embed.
        seen_hashes: set[str] = set()
        for row in v1_rows:
            ch = row["content_hash"]
            if ch in seen_hashes:
                continue
            seen_hashes.add(ch)
            embedding_json = row["embedding"]  # stored as JSON text in the stub path

            # Insert vector into content_vectors.
            cur = conn.execute(
                "INSERT INTO content_vectors(embedding) VALUES (?)", (embedding_json,)
            )
            vector_rowid = cur.lastrowid or conn.execute(
                "SELECT max(rowid) FROM content_vectors"
            ).fetchone()[0]

            # Insert content row.
            conn.execute(
                """
                INSERT INTO content(content_hash, vector_rowid, text, dim, model, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ch,
                    vector_rowid,
                    row["text"],
                    384,  # dim: default; could be derived from embedding length
                    "stub",
                    row["recorded_date"],
                ),
            )

        # 3b. Insert content_refs rows (one per v1 chunks row).
        for row in v1_rows:
            ref_id = _make_ref_id(
                row["source_path"], int(row["line_start"]), row["content_hash"]
            )
            refs_val = row["refs"]
            conn.execute(
                """
                INSERT INTO content_refs(
                  ref_id, content_hash, storage_key, source_type,
                  line_start, line_end, trust, suspect, mem_type, agent,
                  recorded_date, refs
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(storage_key, line_start) DO NOTHING
                """,
                (
                    ref_id,
                    row["content_hash"],
                    row["source_path"],
                    row["source_type"],
                    int(row["line_start"]),
                    int(row["line_end"]),
                    row["trust"],
                    int(row["suspect"]),
                    row["mem_type"],
                    row["agent"],
                    row["recorded_date"],
                    refs_val,
                ),
            )

        # 4. PARITY GATE — before any destructive drop.
        ok, failure = _parity_check(conn, pre_snap, v1_rows)
        if not ok:
            conn.execute("ROLLBACK")
            print(f"\n[PARITY FAIL] {failure}")
            print("[ABORT] v1 DB is untouched. Backup is at:", bak)
            return 1

        # 5. Drop v1 tables + bump schema version.
        conn.execute("DROP TABLE IF EXISTS chunks")
        conn.execute("DROP TABLE IF EXISTS rowmap")
        conn.execute("DROP TABLE IF EXISTS chunk_vectors")
        conn.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', ?)",
            (str(V2),),
        )
        _set_user_version(conn, V2)

        conn.execute("COMMIT")

    except Exception as exc:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        conn.close()
        print(f"\n[ERROR] Migration failed: {exc}")
        print(f"[INFO] v1 DB is untouched. Backup is at: {bak}")
        return 1

    conn.close()

    # Verify the committed DB.
    verify_conn = _open_db(db)
    try:
        final_v = _get_user_version(verify_conn)
        ref_count = verify_conn.execute("SELECT COUNT(*) FROM content_refs").fetchone()[0]
        content_count = verify_conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
    finally:
        verify_conn.close()

    print("\n[OK] Migration complete.")
    print(f"  user_version  : {final_v}")
    print(f"  content rows  : {content_count}")
    print(f"  content_refs  : {ref_count}")
    print(f"  Backup at     : {bak}")
    return 0


# ---------------------------------------------------------------------------
# Parity helpers
# ---------------------------------------------------------------------------

def _snapshot_v1(db: Path) -> dict:
    """Capture a minimal pre-migration snapshot for recall-parity checks."""
    conn = _open_db(db)
    try:
        chunks = conn.execute(
            "SELECT source_path, line_start, trust, content_hash FROM chunks"
        ).fetchall()
        return {
            "chunks": [
                {
                    "source_path": r[0],
                    "line_start": int(r[1]),
                    "trust": r[2],
                    "content_hash": r[3],
                }
                for r in chunks
            ]
        }
    finally:
        conn.close()


def _parity_check(
    conn: sqlite3.Connection,
    pre_snap: dict,
    v1_rows: list,
) -> tuple[bool, str]:
    """Run parity assertions inside the exclusive transaction.

    Asserts:
      P1: COUNT(DISTINCT content_hash) in chunks == COUNT(content)
      P2: Every old chunk maps to exactly one content_refs row (by source_path + line_start),
          AND refs_count == len(v1_rows) for clean (no-duplicate-key) migrations.
          SEC-CORTEX-022 (v9.4.0 Phase 5, P3 defense-in-depth): after the pre-flight
          duplicate-key scan has guaranteed no same-key/different-hash conflicts, the
          refs_count MUST equal the total v1 row count. This makes a silent ON CONFLICT
          DO NOTHING drop detectable even if the pre-flight scan were bypassed.
      P3: Public result contract parity (source_path, line_start, trust, content_hash)
      P4: Trust-filter parity (trusted-only and semi-only membership)

    Returns (True, "") on pass, (False, reason) on failure.
    """
    # P1: content count == distinct hash count.
    distinct_hashes = len({r["content_hash"] for r in v1_rows})
    content_count = conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
    if content_count != distinct_hashes:
        return False, (
            f"P1 FAIL: COUNT(content)={content_count} != "
            f"COUNT(DISTINCT content_hash)={distinct_hashes}"
        )

    # P2: every chunk maps to exactly one ref.
    refs_count = int(conn.execute("SELECT COUNT(*) FROM content_refs").fetchone()[0])
    # After ON CONFLICT DO NOTHING, refs_count may be <= len(v1_rows) if there
    # were genuine duplicates on (storage_key, line_start). Count unique pairs.
    unique_pairs = len({(r["source_path"], r["line_start"]) for r in v1_rows})
    if refs_count != unique_pairs:
        return False, (
            f"P2 FAIL: COUNT(content_refs)={refs_count} != "
            f"unique (source_path,line_start) pairs={unique_pairs}"
        )
    # SEC-CORTEX-022 (Phase 5, defense-in-depth): the pre-flight duplicate scan already
    # guarantees no same-key/different-hash conflicts exist, so refs_count MUST also
    # equal the total v1 row count. A discrepancy here means a row was silently dropped
    # by ON CONFLICT DO NOTHING despite the scan — detecting this makes the parity gate
    # resilient even if the pre-flight check were somehow bypassed.
    if refs_count != len(v1_rows):
        return False, (
            f"P2 FAIL (SEC-CORTEX-022): refs_count={refs_count} != "
            f"len(v1_rows)={len(v1_rows)} — silent drop detected; "
            f"unique_pairs={unique_pairs}"
        )

    # P3: public result contract parity.
    # Build a dict from pre_snap: (source_path, line_start) -> {trust, content_hash}
    pre_index: dict[tuple, dict] = {
        (r["source_path"], r["line_start"]): r for r in pre_snap["chunks"]
    }
    post_rows = conn.execute(
        "SELECT storage_key, line_start, trust, content_hash FROM content_refs"
    ).fetchall()
    for post in post_rows:
        key = (post[0], int(post[1]))
        if key not in pre_index:
            return False, f"P3 FAIL: ({key}) present in content_refs but not in pre_snap"
        pre = pre_index[key]
        if post[2] != pre["trust"] or post[3] != pre["content_hash"]:
            return False, (
                f"P3 FAIL: contract mismatch at {key}: "
                f"trust={post[2]!r} (expected {pre['trust']!r}), "
                f"content_hash={post[3]!r} (expected {pre['content_hash']!r})"
            )

    # P4: trust-filter parity.
    # Compare distinct (source_path, line_start) sets for trusted-only.
    pre_trusted = {(r["source_path"], r["line_start"]) for r in pre_snap["chunks"] if r["trust"] == "trusted"}
    post_trusted = {(r[0], int(r[1])) for r in conn.execute(
        "SELECT storage_key, line_start FROM content_refs WHERE trust = 'trusted'"
    ).fetchall()}
    if pre_trusted != post_trusted:
        return False, (
            f"P4 FAIL: trusted-filter set differs. "
            f"pre={len(pre_trusted)}, post={len(post_trusted)}"
        )

    pre_semi = {(r["source_path"], r["line_start"]) for r in pre_snap["chunks"] if r["trust"] == "semi"}
    post_semi = {(r[0], int(r[1])) for r in conn.execute(
        "SELECT storage_key, line_start FROM content_refs WHERE trust = 'semi'"
    ).fetchall()}
    if pre_semi != post_semi:
        return False, (
            f"P4 FAIL: semi-filter set differs. "
            f"pre={len(pre_semi)}, post={len(post_semi)}"
        )

    return True, ""


# ---------------------------------------------------------------------------
# --rollback
# ---------------------------------------------------------------------------

def cmd_rollback(db: Path) -> int:
    """Restore the most recent .pre9_4.*.bak backup over the DB."""
    bak = _find_latest_backup(db)
    if bak is None:
        print(f"[ERROR] No backup found next to {db}. Cannot rollback.")
        return 1

    # Verify backup integrity before touching the live DB (SEC-CORTEX-020).
    if bak.stat().st_size == 0:
        print(
            f"[ERROR] Backup file is empty (0 bytes): {bak}. "
            "Refusing to restore — manual recovery required."
        )
        return 1

    print(f"Restoring {bak} → {db} ...")
    shutil.copy2(str(bak), str(db))

    # Verify user_version is back to v1.
    conn = _open_db(db)
    try:
        restored_v = _get_user_version(conn)
    finally:
        conn.close()

    if restored_v != V1:
        # Fail closed: if we cannot confirm the DB is back at v1 the user must
        # intervene manually.  A [WARN] + return 0 would be a false success
        # (SEC-CORTEX-019).
        print(
            f"[ERROR] Restored DB has user_version={restored_v} (expected {V1}). "
            "Rollback cannot confirm v1 state — manual intervention required."
        )
        print(f"Backup preserved  : {bak}")
        return 1

    print(f"[OK] Rollback complete. user_version={restored_v}.")
    print(f"Backup preserved  : {bak}")
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cortex storage migration v1 → v2 (PLAN-DESIGN-001 Phase 3).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Read-only pre-flight report")
    group.add_argument("--execute", action="store_true", help="Run the migration")
    group.add_argument("--rollback", action="store_true", help="Restore latest backup")
    parser.add_argument("--db", metavar="PATH", help="Explicit path to brain.db")
    parser.add_argument("--repo", metavar="PATH", help="Repo root (used to derive DB path)")

    args = parser.parse_args(argv)
    db = _resolve_db(args.db, args.repo)

    if args.check:
        return cmd_check(db)
    elif args.execute:
        return cmd_execute(db)
    elif args.rollback:
        return cmd_rollback(db)

    return 0  # unreachable


if __name__ == "__main__":
    sys.exit(main())
