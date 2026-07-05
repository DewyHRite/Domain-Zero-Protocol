"""Escrow-wrapped memory-only snapshot/restore (PLAN-CORTEX-RECOVERY-001 §18.3).
Wrapped under the ESCROW passphrase (NOT the DB key) so it survives total DB-key loss.

Owner-only write on every export artifact. Retention controlled by prune_exports
(keep newest N, default 3). No plaintext memory ever lands on disk.
"""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from . import crypto, recovery

_log = logging.getLogger(__name__)


def _safe_rows(conn, sql) -> list:
    """Execute SQL and return list-of-dicts. Returns [] if table absent (minimal brain)."""
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception:
        return []   # table absent (minimal brain) -> empty


def serialize_memories(conn) -> bytes:
    """Serialize cortex_memories (+ memory-sourced cortex_entities) to JSON bytes.
    Format: dzp-memory-export/1 — tables absent -> empty lists (portable across schemas)."""
    doc = {
        "format": "dzp-memory-export/1",
        "cortex_memories": _safe_rows(conn, "SELECT * FROM cortex_memories"),
        "cortex_entities": _safe_rows(conn, "SELECT * FROM cortex_entities WHERE source='memory'"),
    }
    return json.dumps(doc, separators=(",", ":")).encode("utf-8")


def export_memories(
    conn,
    out_path,
    passphrase: str,
    *,
    data_dir,
    install_id: str,
    key_generation: str,
    schema_version: int,
) -> Path:
    """Serialize memories -> wrap_payload -> owner-only write -> sibling manifest.

    Returns the path of the written artifact.
    The artifact is NEVER written in plaintext form; wrap_payload raises on failure
    so the caller always gets either a valid wrapped file or an exception.
    """
    out_path = Path(out_path)
    payload = serialize_memories(conn)
    meta = {
        "kind": "memory-export",
        "install_id": install_id,
        "key_generation": key_generation,
        "schema_version": schema_version,
    }
    wrapped = crypto.wrap_payload(payload, passphrase, meta=meta)
    recovery.write_owner_only(out_path, wrapped)
    # Write a sibling manifest (non-secret metadata sidecar, SEC-003 compliant)
    digest = recovery.sha256_digest(out_path)
    manifest = recovery.RecoveryManifest(
        artifact_version=1,
        created=_now_iso(),
        key_generation=key_generation,
        schema_version=schema_version,
        encryption_state="memory-export",
        install_id=install_id,
        db_identity=install_id,
        integrity_digest=digest,
        provenance="memory-export",
    )
    recovery.write_manifest(out_path, manifest)
    return out_path


def verify_memory_export(path, passphrase: str) -> dict:
    """Unwrap and parse a memory-export artifact. Returns a summary dict.
    Raises CortexKeyUnavailableError on wrong passphrase or tampered artifact."""
    data, meta = crypto.unwrap_payload(Path(path).read_bytes(), passphrase)
    doc = json.loads(data.decode("utf-8"))
    return {
        "memories": len(doc.get("cortex_memories", [])),
        "entities": len(doc.get("cortex_entities", [])),
        "ok": doc.get("format") == "dzp-memory-export/1",
        "meta": meta,
    }


def restore_memories(conn, path, passphrase: str) -> int:
    """Re-seed cortex_memories (and memory-sourced cortex_entities) from an export
    artifact into a fresh (empty) DB.  Returns the number of cortex_memories rows
    inserted. Commits atomically.

    SEC-B3-001: column names are validated against the target DB's live schema via
    PRAGMA table_info before any INSERT is constructed.  Unknown/malicious keys from
    the deserialized artifact are silently dropped; only known columns are inserted.
    Rows where zero valid columns remain are skipped entirely.

    F4 (CodeRabbit PR#104): serialize_memories captures memory-sourced cortex_entities
    but the original restore_memories only re-inserted cortex_memories rows, silently
    dropping the entities on F8 re-seed.  We now restore them too using the same
    schema-validated column allow-set pattern.  If the target DB has no cortex_entities
    table (minimal brain / schema-gated), entity restore is skipped silently.
    """
    data, _ = crypto.unwrap_payload(Path(path).read_bytes(), passphrase)
    doc = json.loads(data.decode("utf-8"))
    rows = doc.get("cortex_memories", [])

    # Build allow-set from the real DB schema — names come from a trusted source.
    allowed = {
        row[1]
        for row in conn.execute("PRAGMA table_info(cortex_memories)").fetchall()
    }

    n = 0
    for r in rows:
        # Keep only keys present in the DB schema; discard anything else.
        valid = {k: v for k, v in r.items() if k in allowed}
        if not valid:
            continue  # no recognized columns — skip this row
        col_list = list(valid.keys())
        cols = ",".join(col_list)
        ph = ",".join("?" for _ in col_list)
        conn.execute(
            f"INSERT INTO cortex_memories({cols}) VALUES ({ph})",
            tuple(valid[k] for k in col_list),
        )
        n += 1

    # F4: restore memory-sourced entities (captured by serialize_memories).
    # Fail-soft if cortex_entities table is absent (schema-gated / minimal brain).
    entity_rows = doc.get("cortex_entities", [])
    if entity_rows:
        try:
            entity_allowed = {
                row[1]
                for row in conn.execute("PRAGMA table_info(cortex_entities)").fetchall()
            }
            if entity_allowed:  # table exists in target DB
                for er in entity_rows:
                    valid_e = {k: v for k, v in er.items() if k in entity_allowed}
                    if not valid_e:
                        continue
                    col_list_e = list(valid_e.keys())
                    cols_e = ",".join(col_list_e)
                    ph_e = ",".join("?" for _ in col_list_e)
                    conn.execute(
                        f"INSERT OR IGNORE INTO cortex_entities({cols_e}) VALUES ({ph_e})",
                        tuple(valid_e[k] for k in col_list_e),
                    )
        except Exception as exc:
            # fail-soft: entity restore is best-effort (memories are committed below);
            # log for visibility so a silent schema/insert failure is not invisible.
            _log.warning("memory-export entity restore skipped (best-effort): %s", exc)

    conn.commit()
    return n


def prune_exports(export_dir, *, keep: int = 3) -> list:
    """Remove oldest memory-export-*.dzpc artifacts (+ their .manifest.json sidecars)
    keeping the newest `keep` artifacts. Returns list of removed filenames."""
    export_dir = Path(export_dir)
    arts = sorted(export_dir.glob("memory-export-*.dzpc"))
    removed = []
    to_delete = arts[:-keep] if keep > 0 else arts
    for old in to_delete:
        for p in (old, old.with_suffix(old.suffix + ".manifest.json")):
            try:
                p.unlink()
                removed.append(p.name)
            except OSError:
                pass
    return removed


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
