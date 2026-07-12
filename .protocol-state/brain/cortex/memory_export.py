"""Escrow-wrapped memory-only snapshot/restore (PLAN-CORTEX-RECOVERY-001 §18.3).
Wrapped under the ESCROW passphrase (NOT the DB key) so it survives total DB-key loss.

Owner-only write on every export artifact. Retention controlled by prune_exports
(keep newest N, default 3). No plaintext memory ever lands on disk.

BUG-CORTEX-ESCROW-HOLLOW-001 / BUG-CORTEX-ESCROW-RAISE-002 (P1, Sukuna bug hunt
2026-07-11, repro-CONFIRMED against a real v4 brain): this module previously read a
`cortex_memories` table and a `cortex_entities.source` column -- NEITHER of which has
ever existed in any real Cortex schema (v1 legacy `chunks`, or v2/v3/v4
content-addressed `content`/`content_refs`/`content_vectors`; see store.py
_create_v2_schema/_create_v3_schema). `cortex_memories` was fabricated only by test
fixtures, which is why the defect shipped green through v9.9.0-v9.9.5 while being
completely non-functional against a real brain:
  - HOLLOW-001: `SELECT * FROM cortex_memories` always hit "no such table" ->
    `_safe_rows` returned ([], False) -> the escrow silently captured 0 of N facts.
  - RAISE-002: `SELECT * FROM cortex_entities WHERE source='memory'` always hit
    "no such column: source" (cortex_entities has no `source` column) -> `_safe_rows`
    correctly re-raised (CODE-001 contract) -> export_memories hard-crashed before
    ever reaching HOLLOW-001's silent-empty behavior.
Ground truth (memory.py::remember(), ~line 71-86): a remembered fact is written as a
content-addressed Chunk with source_type="memory", source_path=f"memory:{mem_id}" --
landing in `content_refs` (the occurrence row) joined to `content` (the text) on
content_hash. serialize_memories()/restore_memories() now read/write that real
location. The "cortex_entities.source='memory'" predicate is DROPPED entirely --
"memory-sourced entities" was a fictional concept that never had a corresponding
column; nothing downstream ever populated or read it as a real feature.
"""
from __future__ import annotations
import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from . import crypto, recovery

_log = logging.getLogger(__name__)

# Ground truth from memory.py::remember(): Chunk(source_type="memory",
# source_path=f"memory:{mem_id}", ...). Kept as a local literal (not imported) to
# avoid a hard import-time dependency on memory.py for the read-only export path.
_MEMORY_SOURCE_TYPE = "memory"
_MEMORY_STORAGE_PREFIX = "memory:"

# Format version bumped 1 -> 2: the v1 envelope's "cortex_memories"/"cortex_entities"
# keys were tied to the fictional schema above and never carried real data from a
# production brain. v2 sources memories from content_refs/content (source_type=
# 'memory') and drops the entities concept entirely.
_FORMAT_VERSION = "dzp-memory-export/2"


def _safe_rows(conn, sql) -> "tuple[list, bool]":
    """Execute SQL and return (list-of-dicts, table_present).

    CODE-001 (CWE-391, Toji audit v9.8.0->v9.9.1, remediated v9.9.2): a
    genuinely absent table (sqlite3.OperationalError whose message contains
    "no such table" -- the expected, documented shape for a minimal/schema-
    gated brain) returns ([], False). ANY OTHER exception -- a locked/corrupt
    DB, a real query error, an unexpected connection failure -- is RE-RAISED.
    Previously a bare `except Exception: return []` silently converted every
    failure into "empty table", so a corrupt DB or a mid-query I/O error
    produced an export/manifest that LOOKED valid (0 rows) instead of failing
    loudly; callers had no way to tell "genuinely empty" from "query broke".
    """
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()], True
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc).lower():
            return [], False  # expected: table absent (minimal brain / schema-gated)
        raise  # unexpected DB error -- must FAIL the export, never silently swallow


def serialize_memories(conn) -> bytes:
    """Serialize remembered facts to JSON bytes.
    Format: dzp-memory-export/2 -- content-addressed source of truth.

    HOLLOW-001/RAISE-002 fix: reads content_refs (WHERE source_type='memory')
    JOINed to content (on content_hash) for the fact text -- the real location
    memory.py::remember() writes to. The old `cortex_entities.source='memory'`
    query is gone; entities are not memories and no such column ever existed.

    CODE-001 (retained): per-table presence + row-count diagnostics are embedded
    under the private `_table_meta` key (not consumed by restore_memories/
    verify_memory_export, which only read `memories`) so callers such as
    export_memories() can record them in the sidecar manifest without a second
    DB round-trip. Any query failure OTHER than "no such table" propagates from
    `_safe_rows` above, so a corrupt/locked DB FAILS this function outright
    instead of silently producing a hollow-but-valid artifact. A genuinely
    schema-gated brain (no content_refs table -- e.g. a v1 legacy brain that
    never migrated) legitimately yields an empty, present=False result.
    """
    memory_rows, memories_present = _safe_rows(
        conn,
        """
        SELECT cr.storage_key    AS storage_key,
               cr.mem_type       AS mem_type,
               cr.agent          AS agent,
               cr.recorded_date  AS recorded_date,
               cr.refs           AS refs,
               cr.trust          AS trust,
               cr.suspect        AS suspect,
               cr.content_hash   AS content_hash,
               c.text            AS text
        FROM content_refs cr
        JOIN content c ON cr.content_hash = c.content_hash
        WHERE cr.source_type = 'memory'
        ORDER BY cr.recorded_date ASC
        """,
    )
    memories = []
    for row in memory_rows:
        storage_key = row.get("storage_key") or ""
        mem_id = (
            storage_key[len(_MEMORY_STORAGE_PREFIX):]
            if storage_key.startswith(_MEMORY_STORAGE_PREFIX)
            else storage_key
        )
        memories.append(
            {
                "mem_id": mem_id,
                "text": row.get("text"),
                "mem_type": row.get("mem_type"),
                "agent": row.get("agent"),
                "recorded_date": row.get("recorded_date"),
                "refs": row.get("refs") or "[]",
                "trust": row.get("trust"),
                "suspect": bool(row.get("suspect")),
                "content_hash": row.get("content_hash"),
            }
        )
    doc = {
        "format": _FORMAT_VERSION,
        "memories": memories,
        "_table_meta": {
            "memories": {"present": memories_present, "rows": len(memories)},
        },
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
    # CODE-001: pull the per-table diagnostic metadata that serialize_memories()
    # already computed and embedded in the payload, so the sidecar manifest can
    # record row counts + absent tables without a second DB round-trip (and
    # without changing serialize_memories()'s bytes-only return contract, which
    # existing callers/tests depend on).
    try:
        _table_meta = json.loads(payload.decode("utf-8")).get("_table_meta", {})
    except Exception:
        _table_meta = {}
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
        table_meta=json.dumps(_table_meta, separators=(",", ":")),
    )
    recovery.write_manifest(out_path, manifest)
    return out_path


def verify_memory_export(path, passphrase: str) -> dict:
    """Unwrap and parse a memory-export artifact. Returns a summary dict.
    Raises CortexKeyUnavailableError on wrong passphrase or tampered artifact.

    `entities` is retained in the returned dict for backward-compatible shape but
    is now always 0 -- the "memory-sourced cortex_entities" concept HOLLOW-001/
    RAISE-002 removed was fictional (no such column ever existed); this key is not
    a functional regression, it never carried real data."""
    data, meta = crypto.unwrap_payload(Path(path).read_bytes(), passphrase)
    doc = json.loads(data.decode("utf-8"))
    return {
        "memories": len(doc.get("memories", [])),
        "entities": len(doc.get("cortex_entities", [])),
        "ok": doc.get("format") == _FORMAT_VERSION,
        "meta": meta,
    }


def restore_memories(store, path, passphrase: str, *, embedder) -> int:
    """Re-seed remembered facts from a memory-export artifact into `store` via the
    SAME insertion path memory.py::remember() uses (Chunk -> Store.upsert), i.e.
    the real content-addressed storage. Returns the number of memories inserted.

    HOLLOW-001/RAISE-002 fix: the prior implementation issued a raw
    `INSERT INTO cortex_memories(...)` -- a table that has never existed in any
    real Cortex schema (v1 legacy or v2+ content-addressed) -- so it could never
    have successfully restored a single real memory. Content-addressed storage
    requires a vector row (content_vectors) alongside content/content_refs; there
    is no way to "just INSERT a row" without an embedding, so restoration goes
    through Store.upsert() (the same call memory.remember() makes), not a bespoke
    INSERT.

    `store` is a `cortex.store.Store` already constructed with the destination
    brain's db_path/dim/vector_backend/install_id. `embedder` re-embeds each
    restored fact's text (same contract as memory.remember()'s `embedder` param)
    so semantic recall works on the restored brain, not just plaintext storage.

    Idempotent: Store.upsert() keys content_refs on (storage_key, line_start) with
    ON CONFLICT DO UPDATE (see store.py _upsert_v2), and reuses the existing
    content/vector row when content_hash already exists -- re-running restore
    against the same target brain does not duplicate rows.

    Malformed rows (missing mem_id or text) are silently skipped -- same
    defensive posture as the pre-fix SEC-B3-001 column allow-set behavior (never
    let a corrupt/foreign artifact raise mid-restore).
    """
    from .store import Chunk  # local import: keep memory_export import-light for read paths

    data, _ = crypto.unwrap_payload(Path(path).read_bytes(), passphrase)
    doc = json.loads(data.decode("utf-8"))
    rows = doc.get("memories", [])

    items: list[tuple[Chunk, list[float]]] = []
    for r in rows:
        mem_id = r.get("mem_id")
        text = r.get("text")
        if not mem_id or not text:
            continue  # malformed/incomplete row -- skip rather than crash the restore
        content_hash = r.get("content_hash") or hashlib.sha256(text.encode("utf-8")).hexdigest()
        try:
            refs = json.loads(r.get("refs") or "[]")
            if not isinstance(refs, list):
                refs = []
        except (TypeError, ValueError):
            refs = []
        chunk = Chunk(
            id=f"{_MEMORY_STORAGE_PREFIX}{mem_id}",
            source_path=f"{_MEMORY_STORAGE_PREFIX}{mem_id}",
            source_type=_MEMORY_SOURCE_TYPE,
            line_start=1,
            line_end=1,
            content_hash=content_hash,
            recorded_date=r.get("recorded_date") or _now_iso(),
            text=text,
            trust=r.get("trust") or "untrusted",
            suspect=bool(r.get("suspect")),
            mem_type=r.get("mem_type"),
            agent=r.get("agent"),
            refs=refs,
        )
        items.append((chunk, embedder.embed(text)))

    if not items:
        return 0
    store.upsert(items)
    return len(items)


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
