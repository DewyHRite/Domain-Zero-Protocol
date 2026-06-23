"""v9.8.0 Cortex encryption migration (PLAN-CORTEX-ENC-001).

Backup-first, atomic, single-user-only.  Encrypts or decrypts a live brain.db
in place using SQLCipher via the ``sqlcipher_export()`` helper.

Safety guarantees
-----------------
1. **Verified plaintext backup** — ``PRAGMA integrity_check`` on the source DB
   must return 'ok' before any write.  The backup byte-copy is written BEFORE
   any mutation so a crash during export leaves the original intact.
2. **Atomic swap** — the encrypted output is written to a ``.tmp`` sidecar and
   only replaced into the live path via ``os.replace()`` (atomic on Windows
   and POSIX) after the integrity check on the encrypted copy passes.
3. **Single-user scope** — refuses to encrypt a brain that has >1 row in
   ``cortex_installs`` (shared-brain key provisioning is deferred to v9.9.x).
4. **Cipher pinned to SQLCipher v4** — every connection goes through
   ``open_encrypted_connection`` which now issues
   ``PRAGMA cipher_compatibility = 4`` immediately after the key PRAGMA,
   ensuring the on-disk format is stable across sqlcipher3 upgrades.

``sqlcipher_export`` direction (spike-verified 2026-06-19)
----------------------------------------------------------
We open the encrypted target with ``open_encrypted_connection`` (so *main* is
encrypted), then ATTACH the plaintext source with an empty key as the
``plaintext`` schema.  The call

    SELECT sqlcipher_export('main', 'plaintext')

copies data FROM the ``plaintext`` attached schema INTO the ``main`` (encrypted)
schema — confirmed live by a manual spike: normal rows, vec0 virtual tables
(float[384] embeddings, KNN MATCH), and fts5 virtual tables all round-trip
correctly.

Usage
-----
  python migrate_cortex_encrypt_9_8.py --data-dir <dir> --key-b64 <b64> --check
  python migrate_cortex_encrypt_9_8.py --data-dir <dir> --key-b64 <b64> --execute
  python migrate_cortex_encrypt_9_8.py --data-dir <dir> --rollback
  python migrate_cortex_encrypt_9_8.py --data-dir <dir> --key-b64 <b64> --decrypt
"""
from __future__ import annotations

import argparse
import base64
import os
import secrets
import shutil
import sqlite3
import sys
import time
from pathlib import Path

# Must be importable as a standalone script — add the brain package to sys.path.
_BRAIN_DIR = Path(__file__).resolve().parent / "brain"
if str(_BRAIN_DIR) not in sys.path:
    sys.path.insert(0, str(_BRAIN_DIR))

from cortex.crypto import open_encrypted_connection, sqlcipher_available  # noqa: E402


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    """UTC timestamp string for backup filenames."""
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _unique_suffix() -> str:
    """Collision-proof suffix: PID + 3-byte hex token.

    ENC-009: _ts() has 1-second granularity.  Two runs in the same second
    would produce identical backup/tmp names.  Appending PID + a random
    token makes collisions cryptographically improbable.
    """
    return f"{os.getpid()}-{secrets.token_hex(3)}"


def _install_count(db_path: Path) -> int:
    """Return the number of rows in ``cortex_installs``; 0 if the table is absent.

    Uses stock sqlite3 (not sqlcipher3) because this is called on the
    *plaintext* source before encryption.
    """
    con = sqlite3.connect(db_path)
    try:
        has_table = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cortex_installs'"
        ).fetchone()
        if not has_table:
            return 0
        return con.execute("SELECT COUNT(*) FROM cortex_installs").fetchone()[0]
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _parse_dim_from_create_sql(create_sql: str, default: int = 384) -> int:
    """Parse the vector dimension from a vec0 CREATE VIRTUAL TABLE SQL string.

    Looks for ``float[<N>]`` in the SQL and returns N.  Falls back to
    ``default`` if the pattern is not found.
    """
    import re
    m = re.search(r"float\[(\d+)\]", create_sql, re.IGNORECASE)
    return int(m.group(1)) if m else default


def _smoke_test_virtual_tables(con) -> None:
    """Smoke-test vec0 and fts5 virtual tables in an already-open encrypted connection.

    Enumerates virtual tables from sqlite_master and:
    - For each vec0 table: runs ``SELECT count(*)`` and, if non-empty, a bounded
      KNN MATCH with a zero vector of the correct dimension.
    - For each fts5 table: runs ``SELECT count(*)`` and, if non-empty, a bounded
      full-text MATCH.

    Raises RuntimeError on any failure.  The caller is responsible for closing
    the connection and cleaning up the tmp file before the error propagates
    (required on Windows where an open connection locks the file).

    If no vec0/fts5 tables exist (minimal brain), the check is a no-op.
    """
    import struct

    try:
        rows = con.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
        ).fetchall()
    except Exception as exc:
        raise RuntimeError(
            f"encrypted output failed sqlite_master enumeration: {exc}; "
            "aborting, brain.db untouched"
        ) from exc

    for name, sql in rows:
        sql_upper = (sql or "").upper()
        if "USING VEC0" in sql_upper:
            try:
                count = con.execute(f"SELECT count(*) FROM [{name}]").fetchone()[0]
                if count > 0:
                    dim = _parse_dim_from_create_sql(sql)
                    zero_vec = struct.pack(f"{dim}f", *([0.0] * dim))
                    con.execute(
                        f"SELECT rowid FROM [{name}] WHERE embedding MATCH ? ORDER BY distance LIMIT 1",
                        (zero_vec,),
                    ).fetchall()
            except Exception as exc:
                raise RuntimeError(
                    f"encrypted output failed vec0 queryability check on table '{name}': {exc}; "
                    "aborting, brain.db untouched"
                ) from exc

        elif "USING FTS5" in sql_upper:
            try:
                count = con.execute(f"SELECT count(*) FROM [{name}]").fetchone()[0]
                if count > 0:
                    con.execute(
                        f"SELECT rowid FROM [{name}] WHERE [{name}] MATCH 'a' LIMIT 1"
                    ).fetchall()
            except Exception as exc:
                raise RuntimeError(
                    f"encrypted output failed fts5 queryability check on table '{name}': {exc}; "
                    "aborting, brain.db untouched"
                ) from exc


def encrypt_brain(db_path, key: bytes, *, ledger_check: bool = True) -> dict:
    """Encrypt a plaintext brain.db in-place.

    Parameters
    ----------
    db_path:
        Path to the plaintext ``brain.db`` file.
    key:
        32 raw bytes used as the SQLCipher raw key.
    ledger_check:
        When True (default), refuse if ``cortex_installs`` has >1 row —
        shared-brain encryption is out-of-scope for v9.8.0.
        Pass ``ledger_check=False`` in tests that use throwaway DBs without a
        ledger table.

    Returns
    -------
    dict
        ``{"backup": "<path>", "encrypted": True}``

    Notes
    -----
    After a successful encrypt, a PLAINTEXT backup (``*.pre-encrypt.*.bak``)
    remains next to the now-encrypted ``brain.db``.  This backup is intentional
    for recovery, but it defeats encryption-at-rest if left in place.  The
    operator MUST securely delete it after confirming the encrypted brain works
    correctly.  See RISK-ENC-003 in the design spec.
    """
    db_path = Path(db_path)

    if not sqlcipher_available():
        raise RuntimeError(
            "sqlcipher3 is not installed.  "
            "Install requirements-enc.txt before running the encryption migration."
        )

    # Guard: single-user scope only.
    if ledger_check and _install_count(db_path) > 1:
        raise RuntimeError(
            "Brain is shared by >1 install (cortex_installs has >1 row).  "
            "Single-user encryption only in v9.8.0; shared-brain key provisioning "
            "is deferred to v9.9.x.  Run on a single-install brain or use "
            "--rollback to restore."
        )

    # Step 1: integrity check on the plaintext source and capture user_version.
    # BUG-CORTEX-ENC-UV-001: SQLCipher's sqlcipher_export() copies tables and
    # rows but silently drops the PRAGMA user_version header field.  The engine's
    # schema guard (SEC-ACCESS-010) compares user_version against
    # metadata.schema_version; a mismatch causes fail-closed / unavailable even
    # when all data is intact.  We capture the value here and restore it on the
    # encrypted destination after the export.
    src_con = sqlite3.connect(db_path)
    try:
        check_result = src_con.execute("PRAGMA integrity_check").fetchone()[0]
        src_user_version: int = src_con.execute("PRAGMA user_version").fetchone()[0]
    finally:
        src_con.close()
    if check_result != "ok":
        raise RuntimeError(
            f"Source DB failed integrity_check (got {check_result!r}); "
            "aborting to avoid encrypting a corrupt database."
        )

    # Step 2: verified plaintext backup (byte-copy before any mutation).
    # ENC-009: include pid+token suffix so two runs in the same second never
    # overwrite each other's backup (write_bytes has no collision guard).
    _sfx = _unique_suffix()
    backup = db_path.with_name(f"{db_path.name}.pre-encrypt.{_ts()}.{_sfx}.bak")
    backup.write_bytes(db_path.read_bytes())
    # Verify backup is plaintext.
    if backup.read_bytes()[:13] != b"SQLite format":
        backup.unlink(missing_ok=True)
        raise RuntimeError("Backup byte-copy does not appear to be a valid SQLite file.")

    # Step 3: export plaintext -> encrypted .tmp via sqlcipher_export.
    # Reuse the same suffix so the tmp file is also collision-proof.
    tmp = db_path.with_name(f"{db_path.name}.enc.{_ts()}.{_sfx}.tmp")
    if tmp.exists():
        tmp.unlink()

    # open_encrypted_connection creates the encrypted target (main schema).
    # cipher_compatibility=4 is applied inside open_encrypted_connection.
    enc_con = open_encrypted_connection(tmp, key)
    try:
        # ATTACH the plaintext source with an empty key as schema 'plaintext'.
        # The empty string for KEY '' means no encryption (standard sqlite3 DB).
        enc_con.execute("ATTACH DATABASE ? AS plaintext KEY ''", (str(db_path),))
        # Export FROM the 'plaintext' attached schema INTO 'main' (encrypted).
        # Spike-verified 2026-06-19: this direction correctly copies all tables
        # including vec0 virtual tables (float[384], KNN MATCH) and fts5 tables.
        enc_con.execute("SELECT sqlcipher_export('main', 'plaintext')")
        enc_con.execute("DETACH DATABASE plaintext")
        # BUG-CORTEX-ENC-UV-001: restore user_version — sqlcipher_export does
        # NOT carry the PRAGMA user_version header field from the source DB.
        # Writing it here (after the export, before commit/close) ensures the
        # schema guard reads the correct version when the encrypted DB is opened.
        enc_con.execute(f"PRAGMA user_version = {src_user_version}")
        enc_con.commit()
    finally:
        enc_con.close()

    # Step 4: integrity check + vec0/FTS5 smoke-test + user_version assertion on
    # the encrypted .tmp before the atomic replace.
    # The connection must be closed BEFORE any unlink attempt (Windows file-lock requirement).
    v_con = open_encrypted_connection(tmp, key)
    _smoke_error: RuntimeError | None = None
    try:
        v_result = v_con.execute("PRAGMA integrity_check").fetchone()[0]
        if v_result != "ok":
            _smoke_error = RuntimeError(
                f"Encrypted output failed integrity_check (got {v_result!r}); "
                "original DB is unchanged.  The pre-encrypt backup is at: "
                f"{backup}"
            )
        else:
            # BUG-CORTEX-ENC-UV-001: assert that user_version was correctly
            # restored on the encrypted output.  integrity_check passes even
            # when user_version is 0, so we must assert this explicitly here
            # to guarantee the schema guard never sees a mismatch at runtime.
            # Abort (do not atomic-replace) if the marker is wrong — the
            # original brain.db + the backup remain intact.
            dest_uv = v_con.execute("PRAGMA user_version").fetchone()[0]
            if dest_uv != src_user_version:
                _smoke_error = RuntimeError(
                    f"Encrypted output has user_version={dest_uv} but source had "
                    f"user_version={src_user_version}; aborting to prevent schema-guard "
                    "fail-closed on the encrypted brain (BUG-CORTEX-ENC-UV-001).  "
                    f"Original brain.db untouched.  Backup at: {backup}"
                )
            else:
                # Smoke-test: verify vec0 and FTS5 virtual tables are queryable —
                # integrity_check can pass while a virtual table fails at runtime.
                # Raises RuntimeError on any failure; we capture and re-raise after close.
                try:
                    _smoke_test_virtual_tables(v_con)
                except RuntimeError as exc:
                    _smoke_error = exc
    finally:
        v_con.close()

    if _smoke_error is not None:
        tmp.unlink(missing_ok=True)
        raise _smoke_error

    # Step 5: atomic replace — only reached if integrity check + smoke-test passed.
    os.replace(tmp, db_path)

    return {"backup": str(backup), "encrypted": True}


def rollback(db_path) -> dict:
    """Restore the most recent pre-encrypt backup over the live db_path.

    Finds the latest ``.pre-encrypt.*.bak`` sidecar created by ``encrypt_brain``
    in the same directory and replaces the live db with it.

    Returns
    -------
    dict
        ``{"restored_from": "<backup_path>"}``
    """
    db_path = Path(db_path)
    backups = sorted(
        db_path.parent.glob(f"{db_path.name}.pre-encrypt.*.bak")
    )
    if not backups:
        raise RuntimeError(
            f"No pre-encrypt backup found next to {db_path}.  "
            "Cannot rollback — was encrypt_brain ever run?"
        )
    latest = backups[-1]
    # Use copy2 (not os.replace/move) so the backup file is PRESERVED on disk.
    # os.replace would MOVE (destroy) the backup, making a second rollback
    # impossible.  shutil.copy2 copies metadata + content and leaves the source
    # intact, so rollback is re-runnable without a new encrypt_brain call.
    shutil.copy2(latest, db_path)
    return {"restored_from": str(latest)}


def decrypt_brain(db_path, key: bytes) -> dict:
    """Decrypt an encrypted brain.db back to plaintext in-place.

    Uses the same ``sqlcipher_export`` mechanism as ``encrypt_brain`` but in
    reverse: we open the encrypted source as ``main`` and ATTACH an empty
    plaintext target, then export FROM main TO plaintext.

    Returns
    -------
    dict
        ``{"decrypted": True}``
    """
    db_path = Path(db_path)

    if not sqlcipher_available():
        raise RuntimeError(
            "sqlcipher3 is not installed.  "
            "Install requirements-enc.txt before running the decryption migration."
        )

    # Pre-decrypt backup: mirror encrypt_brain's backup discipline so a failed
    # decrypt does not leave the user without their (encrypted) database.
    _sfx = _unique_suffix()
    backup = db_path.with_name(f"{db_path.name}.pre-decrypt.{_ts()}.{_sfx}.bak")
    shutil.copy2(db_path, backup)

    tmp = db_path.with_name(f"{db_path.name}.dec.{_ts()}.{_sfx}.tmp")
    if tmp.exists():
        tmp.unlink()

    # Open the encrypted source as 'main'.
    enc_con = open_encrypted_connection(db_path, key)
    try:
        # BUG-CORTEX-ENC-UV-001: capture user_version from the encrypted source
        # BEFORE the export.  sqlcipher_export() does not carry this header field
        # into the plaintext output — we must restore it manually afterward.
        src_user_version: int = enc_con.execute("PRAGMA user_version").fetchone()[0]
        # ATTACH the plaintext output target with empty key as schema 'plaintext'.
        enc_con.execute("ATTACH DATABASE ? AS plaintext KEY ''", (str(tmp),))
        # Export FROM 'main' (encrypted source) INTO 'plaintext' (unencrypted target).
        # Single-arg form exports the main schema into the attached schema.
        enc_con.execute("SELECT sqlcipher_export('plaintext')")
        enc_con.execute("DETACH DATABASE plaintext")
        enc_con.commit()
    finally:
        enc_con.close()

    # BUG-CORTEX-ENC-UV-001: restore user_version on the plaintext tmp.
    # The plaintext target is now a standard SQLite file (no encryption) so we
    # use stock sqlite3 — the encrypted connection is already closed above.
    pt_con = sqlite3.connect(tmp)
    try:
        pt_con.execute(f"PRAGMA user_version = {src_user_version}")
        pt_con.commit()
    finally:
        pt_con.close()

    # SEC-DISTRO-MC-003: re-verify user_version on the plaintext tmp BEFORE the
    # atomic replace — mirror encrypt_brain's post-write assertion discipline.
    # If the PRAGMA write was silently dropped (e.g. driver bug), the schema guard
    # would see a mismatch at runtime and fail-closed.  Abort here instead so the
    # original encrypted db_path + the pre-decrypt backup remain intact.
    _reverify_con = sqlite3.connect(tmp)
    try:
        dest_uv = _reverify_con.execute("PRAGMA user_version").fetchone()[0]
    finally:
        _reverify_con.close()

    if dest_uv != src_user_version:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"decrypt_brain: plaintext tmp has user_version={dest_uv} but source "
            f"had user_version={src_user_version}; aborting to prevent schema-guard "
            "fail-closed on the decrypted brain (SEC-DISTRO-MC-003).  "
            f"Original encrypted db_path is unchanged.  Pre-decrypt backup: {backup}"
        )

    # Atomic replace — only reached when user_version re-verification passes.
    os.replace(tmp, db_path)
    return {"decrypted": True, "backup": str(backup)}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    """CLI for the v9.8.0 encryption migration.

    NEVER call with --execute against a real data-dir in automated tests.
    Tests must call encrypt_brain() / decrypt_brain() / rollback() directly
    on throwaway tmp_path DBs.
    """
    ap = argparse.ArgumentParser(
        description="DZP Cortex v9.8.0 encryption migration utility."
    )
    ap.add_argument("--data-dir", required=True, help="Path to the DZP Cortex data directory")
    ap.add_argument("--key-b64", help="32-byte encryption key as base64 (required for --execute / --decrypt)")
    ap.add_argument("--check", action="store_true", help="Check migration readiness (no mutations)")
    ap.add_argument("--execute", action="store_true", help="Perform the encryption migration")
    ap.add_argument("--rollback", action="store_true", help="Restore the pre-encrypt backup")
    ap.add_argument("--decrypt", action="store_true", help="Decrypt an encrypted brain.db back to plaintext")
    args = ap.parse_args(argv)

    db_path = Path(args.data_dir) / "brain.db"

    if args.check:
        count = _install_count(db_path)
        print(
            f"check: installs={count} sqlcipher={sqlcipher_available()} "
            f"db_exists={db_path.exists()} db={db_path}"
        )
        if not sqlcipher_available():
            print("ERROR: sqlcipher3 not installed", file=sys.stderr)
            return 1
        if count > 1:
            print(f"ERROR: {count} installs in cortex_installs; single-user only", file=sys.stderr)
            return 1
        print("OK: ready for --execute")
        return 0

    # All mutation modes require a key (except --rollback).
    key: bytes | None = None
    if args.key_b64:
        key = base64.b64decode(args.key_b64)
    elif not args.rollback:
        print("ERROR: --key-b64 is required for --execute and --decrypt", file=sys.stderr)
        return 2

    if args.execute:
        result = encrypt_brain(db_path, key)
        print(f"encrypt: {result}")
        print(
            f"\nWARNING: a PLAINTEXT backup remains at {result['backup']}. "
            "After confirming the encrypted brain works, securely delete it — "
            "it defeats encryption-at-rest if left in place."
        )
        return 0

    if args.rollback:
        result = rollback(db_path)
        print(f"rollback: {result}")
        return 0

    if args.decrypt:
        result = decrypt_brain(db_path, key)
        print(f"decrypt: {result}")
        return 0

    print("ERROR: specify --check, --execute, --rollback, or --decrypt", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
