"""Cortex Graph Layer — entity/edge CRUD and query helpers (PLAN-CORTEX-GRAPH-001 Phase 1).

This module implements the v9.6.0 typed entity and relationship layer that sits on top
of the existing v9.4.0 content-addressed sqlite-vec store.

Security constraints (non-negotiable):
  SEC-GRAPH-001: Every traversal helper applies an explicit DUAL filter —
    `cortex_entities.trust IN (?)` AND `cortex_edges.trust IN (?)` on every hop.
    Stored edge trust is ADVISORY; query-time dual-filter is authoritative.
  SEC-GRAPH-002: go_no_go_pack() requires `trust` to be a STRICT SUBSET of
    {'trusted','semi'}. Any 'untrusted' token raises ValueError before any SQL runs.
  SEC-GRAPH-004: ALL SQL uses ? parameterized placeholders. No f-string/format/%
    interpolation of user-supplied fields. upsert_entity validates len(entity_id)<=64
    and len(label)<=256 as preconditions. This is a HARD module-level invariant.

Import constraints:
  - Must NOT import from memory.py or ingest.py (avoids circular imports).
  - May import from store.py and errors.py.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENTITY_TYPES = frozenset({
    "Decision", "SEC-ID", "WorkItem", "Version",
    "File", "Blocker", "Release", "Lesson",
})

# SEC-GRAPH-NEW-002: maximum byte size for serialized metadata_json.
# Prevents unbounded blobs from being stored in the entities table.
MAX_METADATA_BYTES = 4096
REL_TYPES = frozenset({
    "blocks", "supersedes", "resolves", "maps-to",
    "cascades-into", "decided-by",
})
STATUS_VALUES = frozenset({
    "open", "closed", "superseded", "cascaded", "resolved",
})
TRUST_VALUES = frozenset({"trusted", "semi", "untrusted"})

# UX-005 (Nobara): Formal trust-token convention.
# Used across all three output surfaces: gnogo, entity query, --recall.
TRUST_TOKEN: dict[str, str] = {
    "trusted": "[T]",
    "semi": "[S]",
    "untrusted": "[U]",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _edge_id(from_id: str, rel_type: str, to_id: str) -> str:
    """Deterministic edge_id: sha256(f'{from_id}:{rel_type}:{to_id}')[:16].

    SEC-GRAPH-004: inputs are used only as hash inputs, never interpolated into SQL.
    """
    return hashlib.sha256(
        f"{from_id}:{rel_type}:{to_id}".encode()
    ).hexdigest()[:16]


def _now() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Entity CRUD
# ---------------------------------------------------------------------------

def upsert_entity(
    conn,
    entity_id: str,
    entity_type: str,
    label: str,
    *,
    status: str = "open",
    trust: str = "untrusted",
    anchor_ref_id: str | None = None,
    # anchor_content_hash is intentionally ABSENT — denorm removed (Todo B4).
    # Callers needing content_hash join through content_refs via anchor_ref_id.
    install_id: str,
    metadata: dict | None = None,
) -> None:
    """Upsert a graph entity. Idempotent. Trust is NEVER downgraded by upsert.

    On conflict, label, status, updated_at, and metadata_json are updated.
    Trust is NOT updated on conflict — it can only be raised by an explicit
    set_entity_trust() call (future API; not in Phase 1a scope).

    SEC-GRAPH-004 preconditions (validated BEFORE any SQL):
      - len(entity_id) <= 64    (raises ValueError if violated)
      - len(label) <= 256       (raises ValueError if violated)
      - entity_type in ENTITY_TYPES
      - trust in TRUST_VALUES
      - status in STATUS_VALUES

    ALL SQL uses ? parameterized placeholders. No f-string interpolation of
    user-supplied values (entity_id, label, rel_type, etc.) anywhere in this
    module. This is a HARD module-level invariant.
    """
    # SEC-GRAPH-004: precondition validation before any SQL
    if len(entity_id) > 64:
        raise ValueError(f"entity_id exceeds 64 chars: {entity_id!r}")
    if len(label) > 256:
        raise ValueError(f"label exceeds 256 chars (len={len(label)})")
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Unknown entity_type: {entity_type!r}. Must be one of {sorted(ENTITY_TYPES)}")
    if trust not in TRUST_VALUES:
        raise ValueError(f"Unknown trust: {trust!r}. Must be one of {sorted(TRUST_VALUES)}")
    if status not in STATUS_VALUES:
        raise ValueError(f"Unknown status: {status!r}. Must be one of {sorted(STATUS_VALUES)}")

    now = _now()
    metadata_str = json.dumps(metadata or {})

    # SEC-GRAPH-NEW-002: size cap — reject oversized metadata before any SQL runs
    if len(metadata_str) > MAX_METADATA_BYTES:
        raise ValueError(
            f"metadata_json exceeds {MAX_METADATA_BYTES} bytes (len={len(metadata_str)})"
        )

    # SEC-GRAPH-004: parameterized SQL — no f-string interpolation of user-supplied fields
    conn.execute(
        """
        INSERT INTO cortex_entities
            (entity_id, entity_type, label, status, trust, anchor_ref_id,
             install_id, created_at, updated_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entity_id) DO UPDATE SET
            label         = excluded.label,
            status        = excluded.status,
            updated_at    = excluded.updated_at,
            metadata_json = excluded.metadata_json
            -- trust NOT updated on conflict: trust only increases via explicit set_entity_trust()
        """,
        (
            entity_id, entity_type, label, status, trust, anchor_ref_id,
            install_id, now, now,
            metadata_str,
        ),
    )


def set_entity_status(conn, entity_id: str, status: str) -> None:
    """Update entity status. Validates against STATUS_VALUES.

    SEC-GRAPH-004: parameterized SQL — no f-string interpolation.
    """
    if status not in STATUS_VALUES:
        raise ValueError(f"Unknown status: {status!r}. Must be one of {sorted(STATUS_VALUES)}")
    conn.execute(
        "UPDATE cortex_entities SET status = ?, updated_at = ? WHERE entity_id = ?",
        (status, _now(), entity_id),
    )


# ---------------------------------------------------------------------------
# Edge CRUD
# ---------------------------------------------------------------------------

def upsert_edge(
    conn,
    from_entity_id: str,
    to_entity_id: str,
    rel_type: str,
    *,
    trust: str = "untrusted",
    install_id: str,
    provenance_ref_id: str | None = None,
) -> str:
    """Upsert a directed edge. Returns edge_id.

    Stored edge trust is ADVISORY. Query-time trust enforcement uses the
    dual-filter pattern (SEC-GRAPH-001): both cortex_entities.trust AND
    cortex_edges.trust are checked on every hop. An edge's effective trust is
    min(from_entity.trust, to_entity.trust) computed at query time — the stored
    trust column here serves only as a cache for faster filtering.

    ALL SQL uses ? parameterized placeholders (SEC-GRAPH-004).
    """
    if rel_type not in REL_TYPES:
        raise ValueError(f"Unknown rel_type: {rel_type!r}. Must be one of {sorted(REL_TYPES)}")
    if trust not in TRUST_VALUES:
        raise ValueError(f"Unknown trust: {trust!r}. Must be one of {sorted(TRUST_VALUES)}")

    eid = _edge_id(from_entity_id, rel_type, to_entity_id)
    # SEC-GRAPH-004: parameterized INSERT — no f-string on rel_type or entity IDs
    conn.execute(
        """
        INSERT INTO cortex_edges
            (edge_id, from_entity_id, to_entity_id, rel_type, trust,
             install_id, created_at, provenance_ref_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(from_entity_id, rel_type, to_entity_id) DO NOTHING
        """,
        (eid, from_entity_id, to_entity_id, rel_type, trust,
         install_id, _now(), provenance_ref_id),
    )
    return eid


# ---------------------------------------------------------------------------
# Query helpers — ALL apply SEC-GRAPH-001 dual-filter on every hop
# ---------------------------------------------------------------------------

def query_open_by_type(
    conn,
    entity_type: str,
    *,
    trust: list[str],
    install_id: str | None = None,  # None = all installs (federation mode)
    limit: int = 50,
) -> list[dict]:
    """Return open entities of a given type, filtered by trust.

    SEC-GRAPH-001: trust filter applied directly on cortex_entities.trust.
    No edge traversal here, so single-table filter is sufficient.
    SEC-GRAPH-004: parameterized placeholders for entity_type, trust values, install_id.
    """
    trust_placeholders = ",".join("?" for _ in trust)
    if install_id is not None:
        # SEC-GRAPH-004: install_id passed as parameter, not interpolated
        rows = conn.execute(
            f"""
            SELECT entity_id, entity_type, label, status, trust, anchor_ref_id,
                   install_id, created_at, updated_at, metadata_json
            FROM cortex_entities
            WHERE entity_type = ?
              AND status = 'open'
              AND trust IN ({trust_placeholders})
              AND install_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (entity_type, *trust, install_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            f"""
            SELECT entity_id, entity_type, label, status, trust, anchor_ref_id,
                   install_id, created_at, updated_at, metadata_json
            FROM cortex_entities
            WHERE entity_type = ?
              AND status = 'open'
              AND trust IN ({trust_placeholders})
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (entity_type, *trust, limit),
        ).fetchall()
    cols = ["entity_id", "entity_type", "label", "status", "trust", "anchor_ref_id",
            "install_id", "created_at", "updated_at", "metadata_json"]
    return [dict(zip(cols, r)) for r in rows]


def query_blockers_for(
    conn,
    entity_id: str,
    *,
    trust: list[str],
) -> list[dict]:
    """Return all entities that block the given entity_id (via 'blocks' edges).

    SEC-GRAPH-001 DUAL-FILTER: trust is applied to BOTH cortex_entities.trust
    AND cortex_edges.trust on every hop. An untrusted entity cannot launder its
    way to the result set via a trusted edge, and vice versa.

    SQL uses ? parameterized placeholders throughout (SEC-GRAPH-004).
    trust args appear TWICE: once for entity trust filter, once for edge trust filter.
    """
    trust_placeholders = ",".join("?" for _ in trust)
    # SEC-GRAPH-001 DUAL-FILTER: entity trust AND edge trust both constrained
    rows = conn.execute(
        f"""
        SELECT e.entity_id, e.entity_type, e.label, e.status, e.trust,
               e.anchor_ref_id, e.install_id, e.created_at, e.updated_at,
               eg.rel_type, eg.edge_id
        FROM cortex_edges eg
        JOIN cortex_entities e ON eg.from_entity_id = e.entity_id
        WHERE eg.to_entity_id = ?
          AND eg.rel_type = 'blocks'
          AND e.trust IN ({trust_placeholders})    -- entity trust filter (SEC-GRAPH-001)
          AND eg.trust IN ({trust_placeholders})   -- edge trust filter (SEC-GRAPH-001)
        ORDER BY e.updated_at DESC
        """,
        (entity_id, *trust, *trust),   # trust args appear twice: entity + edge filters
    ).fetchall()
    cols = ["entity_id", "entity_type", "label", "status", "trust", "anchor_ref_id",
            "install_id", "created_at", "updated_at", "rel_type", "edge_id"]
    return [dict(zip(cols, r)) for r in rows]


def query_resolution_chain(
    conn,
    entity_id: str,
    *,
    trust: list[str],
) -> list[dict]:
    """Return the supersedes/resolves chain for a given entity (decision audit trail).

    SEC-GRAPH-001 DUAL-FILTER: both cortex_entities.trust AND cortex_edges.trust
    are constrained on every hop — untrusted nodes/edges cannot appear in the chain.

    SQL uses ? parameterized placeholders throughout (SEC-GRAPH-004).
    """
    trust_placeholders = ",".join("?" for _ in trust)
    rows = conn.execute(
        f"""
        SELECT e.entity_id, e.entity_type, e.label, e.status, e.trust,
               e.anchor_ref_id, e.created_at, eg.rel_type, eg.edge_id
        FROM cortex_edges eg
        JOIN cortex_entities e ON eg.to_entity_id = e.entity_id
        WHERE eg.from_entity_id = ?
          AND eg.rel_type IN ('supersedes', 'resolves')
          AND e.trust IN ({trust_placeholders})    -- entity trust filter (SEC-GRAPH-001)
          AND eg.trust IN ({trust_placeholders})   -- edge trust filter (SEC-GRAPH-001)
        ORDER BY e.created_at ASC
        """,
        (entity_id, *trust, *trust),
    ).fetchall()
    cols = ["entity_id", "entity_type", "label", "status", "trust", "anchor_ref_id",
            "created_at", "rel_type", "edge_id"]
    return [dict(zip(cols, r)) for r in rows]


def query_version_cascade(
    conn,
    version_entity_id: str,
    *,
    trust: list[str],
) -> list[dict]:
    """Return all entities with 'cascades-into' edges pointing to this version.

    SEC-GRAPH-001 DUAL-FILTER: both cortex_entities.trust AND cortex_edges.trust
    are constrained — untrusted nodes/edges cannot appear in the cascade set.

    SQL uses ? parameterized placeholders throughout (SEC-GRAPH-004).
    """
    trust_placeholders = ",".join("?" for _ in trust)
    rows = conn.execute(
        f"""
        SELECT e.entity_id, e.entity_type, e.label, e.status, e.trust,
               e.anchor_ref_id, e.created_at, eg.edge_id
        FROM cortex_edges eg
        JOIN cortex_entities e ON eg.from_entity_id = e.entity_id
        WHERE eg.to_entity_id = ?
          AND eg.rel_type = 'cascades-into'
          AND e.trust IN ({trust_placeholders})    -- entity trust filter (SEC-GRAPH-001)
          AND eg.trust IN ({trust_placeholders})   -- edge trust filter (SEC-GRAPH-001)
        ORDER BY e.created_at ASC
        """,
        (version_entity_id, *trust, *trust),
    ).fetchall()
    cols = ["entity_id", "entity_type", "label", "status", "trust",
            "anchor_ref_id", "created_at", "edge_id"]
    return [dict(zip(cols, r)) for r in rows]


def go_no_go_pack(
    conn,
    release_entity_id: str,
    *,
    trust: list[str],  # MUST be a strict subset of {'trusted','semi'} — see SEC-GRAPH-002
) -> dict:
    """Emit a structured Go/No-Go evidence pack for release gate decisions.

    SEC-GRAPH-002 TRUST FLOOR: `trust` must be a STRICT SUBSET of {'trusted','semi'}.
    Any 'untrusted' value present in the list raises ValueError — even if 'trusted' or
    'semi' are also present. This is enforced BEFORE any SQL executes.
    Rationale: Go/No-Go release gates must never include untrusted evidence as
    qualifying input. The entire trust list must be within the trusted/semi tier.

    SEC-GRAPH-001 DUAL-FILTER: All sub-queries below apply trust to both
    cortex_entities.trust AND cortex_edges.trust on every hop.

    SEC-GRAPH-009: stale_sources sub-query filters by calling install's install_id
    to prevent cross-install file path disclosure.

    ALL SQL uses ? parameterized placeholders (SEC-GRAPH-004).

    Verdict logic (UX-004):
    - 'no-go'           : open_sec_ids OR open_blockers non-empty, OR incomplete_cascade non-empty
    - 'go-with-warnings': verdict is go but stale_sources or open_work_items are non-empty
    - 'go'              : all lists empty

    Returns:
      {
        'release': entity_id,
        'open_sec_ids': [...],
        'open_work_items': [...],
        'open_blockers': [...],
        'incomplete_cascade': [...],  # version cascade items not yet 'cascaded'
        'stale_sources': [...],       # sources not re-indexed in > 24h (install-scoped)
        'verdict': 'go' | 'go-with-warnings' | 'no-go',
        'verdict_reason': str,        # human-readable rationale (UX-004)
        'trust_filters_applied': [...],
      }
    """
    # SEC-GRAPH-002: strict trust floor — reject any list containing 'untrusted'
    _allowed = frozenset({"trusted", "semi"})
    if not trust:
        raise ValueError("go_no_go_pack: trust list must not be empty")
    if not frozenset(trust).issubset(_allowed):
        raise ValueError(
            f"go_no_go_pack: trust must be a strict subset of {{'trusted','semi'}}. "
            f"'untrusted' is not permitted for release gate decisions. Got: {trust!r}"
        )

    trust_placeholders = ",".join("?" for _ in trust)

    # Sub-query: open SEC-IDs
    # SEC-IDs are standalone entities; entity trust filter alone is sufficient (no edge traversal).
    open_sec_ids = conn.execute(
        f"""
        SELECT entity_id, label FROM cortex_entities
        WHERE entity_type = 'SEC-ID'
          AND status = 'open'
          AND trust IN ({trust_placeholders})
        ORDER BY created_at ASC
        """,
        (*trust,),
    ).fetchall()

    # Sub-query: open work items
    open_work_items = conn.execute(
        f"""
        SELECT entity_id, label FROM cortex_entities
        WHERE entity_type = 'WorkItem'
          AND status = 'open'
          AND trust IN ({trust_placeholders})
        ORDER BY created_at ASC
        """,
        (*trust,),
    ).fetchall()

    # Sub-query: open blockers for the release entity
    # SEC-GRAPH-001 DUAL-FILTER: entity trust AND edge trust on the 'blocks' traversal
    open_blockers = conn.execute(
        f"""
        SELECT e.entity_id, e.label FROM cortex_edges eg
        JOIN cortex_entities e ON eg.from_entity_id = e.entity_id
        WHERE eg.to_entity_id = ?
          AND eg.rel_type = 'blocks'
          AND e.status = 'open'
          AND e.trust IN ({trust_placeholders})    -- entity trust (SEC-GRAPH-001)
          AND eg.trust IN ({trust_placeholders})   -- edge trust (SEC-GRAPH-001)
        ORDER BY e.created_at ASC
        """,
        (release_entity_id, *trust, *trust),
    ).fetchall()

    # Sub-query: version cascade completeness
    # SEC-GRAPH-001 DUAL-FILTER: entity trust AND edge trust on 'cascades-into' traversal
    all_cascade = conn.execute(
        f"""
        SELECT e.entity_id, e.label, e.status FROM cortex_edges eg
        JOIN cortex_entities e ON eg.from_entity_id = e.entity_id
        WHERE eg.to_entity_id = ?
          AND eg.rel_type = 'cascades-into'
          AND e.trust IN ({trust_placeholders})    -- entity trust (SEC-GRAPH-001)
          AND eg.trust IN ({trust_placeholders})   -- edge trust (SEC-GRAPH-001)
        """,
        (release_entity_id, *trust, *trust),
    ).fetchall()
    incomplete_cascade = [r for r in all_cascade if r[2] != "cascaded"]

    # Sub-query: stale sources (SEC-GRAPH-009: install-scoped, no cross-install path disclosure)
    # source_state.source_path uses scoped-key format "@<12-hex-install-id>/<rel-path>" for
    # shared-brain installs. Filter with LIKE '@<install_id>/%' to confine results to
    # this install only. For unscoped (single-user) installs with no '@' prefix, the
    # install_id is absent from metadata; in that case we skip the stale_sources query
    # entirely (safe: do not disclose any paths we cannot scope correctly).
    install_id_row = conn.execute(
        "SELECT value FROM metadata WHERE key = 'install_id'"
    ).fetchone()
    if install_id_row is not None:
        install_id_val = install_id_row[0]
        # Use scoped prefix pattern: source_paths for this install start with '@<install_id>/'
        scope_prefix = f"@{install_id_val}/%"
        stale_sources = conn.execute(
            """
            SELECT source_path, indexed_at FROM source_state
            WHERE source_path LIKE ?
              AND indexed_at < datetime('now', '-24 hours')
            ORDER BY indexed_at ASC
            """,
            (scope_prefix,),
        ).fetchall()
    else:
        # No install_id in metadata — skip stale_sources (safe: do not disclose any paths)
        stale_sources = []

    # Verdict logic (UX-004)
    if open_sec_ids or open_blockers or incomplete_cascade:
        verdict = "no-go"
        reason_parts = []
        if open_sec_ids:
            reason_parts.append(f"{len(open_sec_ids)} open SEC-ID(s)")
        if open_blockers:
            reason_parts.append(f"{len(open_blockers)} open blocker(s)")
        if incomplete_cascade:
            reason_parts.append(f"{len(incomplete_cascade)} incomplete cascade item(s)")
        verdict_reason = "No-go: " + "; ".join(reason_parts) + "."
    elif stale_sources or open_work_items:
        verdict = "go-with-warnings"
        warn_parts = []
        if open_work_items:
            warn_parts.append(f"{len(open_work_items)} open work item(s)")
        if stale_sources:
            warn_parts.append(f"{len(stale_sources)} stale source(s)")
        verdict_reason = "Go with warnings: " + "; ".join(warn_parts) + "."
    else:
        verdict = "go"
        verdict_reason = "All checks clear."

    return {
        "release": release_entity_id,
        "open_sec_ids": [{"entity_id": r[0], "label": r[1]} for r in open_sec_ids],
        "open_work_items": [{"entity_id": r[0], "label": r[1]} for r in open_work_items],
        "open_blockers": [{"entity_id": r[0], "label": r[1]} for r in open_blockers],
        "incomplete_cascade": [{"entity_id": r[0], "label": r[1]} for r in incomplete_cascade],
        "stale_sources": [{"source_path": r[0], "indexed_at": r[1]} for r in stale_sources],
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "trust_filters_applied": list(trust),
    }


# ---------------------------------------------------------------------------
# GC helper
# ---------------------------------------------------------------------------

def _gc_orphaned_provenance_refs(conn, deleted_ref_ids: list[str]) -> int:
    """Nullify cortex_edges.provenance_ref_id for edges whose provenance chunk was deleted.

    Called from _delete_by_source_v2() after source chunk deletion. Returns count nullified.
    (Todo B4 — application-level GC for orphaned anchor/provenance ref_ids.)

    SEC-GRAPH-004: parameterized SQL — no f-string interpolation.
    """
    if not deleted_ref_ids:
        return 0
    count = 0
    for ref_id in deleted_ref_ids:
        cur = conn.execute(
            "UPDATE cortex_edges SET provenance_ref_id = NULL WHERE provenance_ref_id = ?",
            (ref_id,),
        )
        count += cur.rowcount or 0
    return count
