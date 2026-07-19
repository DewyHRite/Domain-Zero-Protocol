"""DZP Cortex — Graph Entity Extraction (WI-22, PLAN-CORTEX-GRAPH-001 Phase 3a).

Extracts typed graph entities from indexed chunk text and upserts them into
cortex_entities via graph.upsert_entity().

Schema-gated: ALL extraction is a strict NO-OP when store._active_schema < 3.
A v2 live DB is never touched by this module (WI-22 requirement).

Supported entity types:
  SEC-ID   : SEC-[A-Z]+-\\d+          (e.g. SEC-CORTEX-011, SEC-GRAPH-003)
  WorkItem : WI-\\d+                  (e.g. WI-16, WI-22)
  Version  : v?\\d+\\.\\d+\\.\\d+    (e.g. v9.6.0, 9.5.0)
  Decision : DECISION:\\s+<text>      (first 80 chars of decision text used as label)

SEC-UNIFIED-003 (P2): config-supplied entity_extraction_patterns overrides are
  validated at config.validate() time via re.compile(). This module compiles
  the active patterns at call time from the config or from BUILTIN_PATTERNS.
  All user-supplied patterns must be valid Python regex — invalid patterns are
  rejected before ingest ever runs.

SEC-GRAPH-008 (P2): Default patterns are bounded to prevent catastrophic
  backtracking on adversarial chunk text.
  - SEC_ID_RE: anchored by specific prefix (SEC-), followed by bounded char class
  - WORK_ITEM_RE: anchored by WI-, bounded digit group \\d{1,6}
  - VERSION_RE: bounded v?\\d{1,4}\\.\\d{1,4}\\.\\d{1,4}
  - DECISION_RE: bounded 80-char capture group

Import constraints:
  - Must NOT import from memory.py (avoid circular imports)
  - May import from store.py, graph.py, errors.py

FEAT-IDGOV-001 Phase I (advisory only): registry_advisories() below reads the
  idgov issue-registry JSONL FILE DIRECTLY (json + pathlib stdlib only). It does
  NOT import the scripts/idgov/ package — that subsystem is not guaranteed to be
  on the Cortex runtime sys.path, and is a separate subsystem from this module's
  documented import boundary above. The advisory is data, not instructions:
  non-blocking, side-effect-free, and a total no-op (including when the registry
  file does not exist yet, e.g. before FEAT-IDGOV-001 go-live).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .store import Store

# ---------------------------------------------------------------------------
# SEC-GRAPH-008: Bounded default patterns
# ---------------------------------------------------------------------------

# SEC-ID: e.g. SEC-CORTEX-011, SEC-GRAPH-003
# Bounded: prefix anchored, suffix is 1-6 digits (no catastrophic backtracking)
_DEFAULT_SEC_ID_RE = re.compile(r"\bSEC-[A-Z]{1,20}-\d{1,6}\b")

# WorkItem: e.g. WI-16, WI-22
# Bounded: prefix anchored, 1-6 digits
_DEFAULT_WORK_ITEM_RE = re.compile(r"\bWI-\d{1,6}\b")

# Version: e.g. v9.6.0, v9.5.0, 9.4.1
# Bounded: each component 1-4 digits
_DEFAULT_VERSION_RE = re.compile(r"\bv?\d{1,4}\.\d{1,4}\.\d{1,4}\b")

# Decision: lines starting with DECISION: (case-insensitive)
# Bounded: capture group limited to 80 chars max
_DEFAULT_DECISION_RE = re.compile(r"(?i)DECISION:\s+(.{1,80})")

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_entities_from_chunk(
    chunk_text: str,
    *,
    trust: str,
    ref_id: str,
    cfg: dict | None = None,
) -> list[dict]:
    """Extract typed entities from a chunk of text.

    Returns a list of entity dicts suitable for passing to graph.upsert_entity().
    Each dict has:
      - entity_id: str
      - entity_type: str  (one of ENTITY_TYPES from graph.py)
      - label: str
      - trust: str  (inherited from chunk's trust)
      - anchor_ref_id: str  (the chunk's ref_id)
      - status: str (always 'open' for newly extracted entities)

    Schema-gating is handled by run_extraction_for_chunk() — this function can be
    called directly for unit testing without a live store.

    SEC-UNIFIED-003: if cfg contains 'entity_extraction_patterns', those compiled
    patterns are used instead of defaults. Config validation (at load time) ensures
    they are valid regex — we trust them here.
    """
    patterns = _get_patterns(cfg)
    entities: list[dict] = []
    seen_ids: set[str] = set()

    def _add(entity_id: str, entity_type: str, label: str) -> None:
        if entity_id not in seen_ids:
            seen_ids.add(entity_id)
            entities.append({
                "entity_id": entity_id,
                "entity_type": entity_type,
                "label": label,
                "trust": trust,
                "anchor_ref_id": ref_id,
                "status": "open",
            })

    # SEC-ID extraction
    sec_id_re = patterns.get("SEC-ID", _DEFAULT_SEC_ID_RE)
    for m in sec_id_re.finditer(chunk_text):
        eid = m.group(0)
        _add(eid, "SEC-ID", eid)

    # WorkItem extraction
    wi_re = patterns.get("WorkItem", _DEFAULT_WORK_ITEM_RE)
    for m in wi_re.finditer(chunk_text):
        eid = m.group(0)
        _add(eid, "WorkItem", eid)

    # Version extraction
    ver_re = patterns.get("Version", _DEFAULT_VERSION_RE)
    for m in ver_re.finditer(chunk_text):
        eid = m.group(0)
        # Normalise: ensure 'v' prefix
        if not eid.startswith("v"):
            eid = "v" + eid
        _add(eid, "Version", eid)

    # Decision extraction
    dec_re = patterns.get("Decision", _DEFAULT_DECISION_RE)
    for idx, m in enumerate(dec_re.finditer(chunk_text)):
        label = m.group(1).strip()[:80]
        # Use ref_id + index as the entity_id for decisions (they have no natural ID)
        eid = f"DEC:{ref_id[:8]}:{idx}"
        # Truncate to 64 chars (upsert_entity precondition)
        eid = eid[:64]
        _add(eid, "Decision", label)

    return entities


def run_extraction_for_chunk(
    *,
    store: "Store",
    chunk_text: str,
    trust: str,
    ref_id: str,
    cfg: dict | None = None,
    install_id: str = "local",
) -> int:
    """Extract entities from a chunk and upsert them into the graph.

    WI-22 SCHEMA GATE: This is a strict NO-OP when store._active_schema < 3.
    v2 DBs are never touched. Returns 0 in that case.

    Returns the count of entities upserted (0 on schema < 3 or empty text).
    """
    # SCHEMA GATE: do nothing on v2 or v1 DBs
    if store._active_schema < 3:
        return 0

    entities = extract_entities_from_chunk(chunk_text, trust=trust, ref_id=ref_id, cfg=cfg)
    if not entities:
        return 0

    from .graph import upsert_entity

    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        for entity in entities:
            upsert_entity(
                conn,
                entity_id=entity["entity_id"],
                entity_type=entity["entity_type"],
                label=entity["label"],
                status=entity["status"],
                trust=entity["trust"],
                anchor_ref_id=entity["anchor_ref_id"],
                install_id=install_id,
            )
        conn.execute("COMMIT")

    return len(entities)


# ---------------------------------------------------------------------------
# FEAT-IDGOV-001 Phase I — optional, non-blocking registry advisory
# ---------------------------------------------------------------------------

# repo root = parents[3] of this file (.protocol-state/brain/cortex/extractor.py)
_DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[3] / ".protocol-state" / "issue-registry.jsonl"


def registry_advisories(
    entities: list[dict],
    registry_path: str | Path | None = None,
) -> list[dict]:
    """Cross-check extracted SEC-ID entities against the idgov issue registry.

    ADVISORY ONLY — data, not instructions. Never raises, never mutates
    `entities`, never affects extraction or upsert. Reads the registry as a
    plain JSONL file (does NOT import the scripts/idgov/ package — see the
    module docstring's import-boundary note).

    Returns a list of advisory dicts, one per SEC-ID entity whose entity_id is
    not found among the registry's known ids (either the current `id` or a
    preserved `legacy_id`). Returns [] when the registry file is missing,
    empty, unreadable, or when every cited SEC-ID is already known — this
    includes the pre-go-live state where the registry does not exist yet.
    """
    try:
        sec_id_entities = [e for e in entities if e.get("entity_type") == "SEC-ID"]
        if not sec_id_entities:
            return []

        known_ids = _known_registry_ids(registry_path)
        if not known_ids:
            return []

        advisories: list[dict] = []
        seen: set[str] = set()
        for entity in sec_id_entities:
            eid = entity.get("entity_id")
            if not eid or eid in seen or eid in known_ids:
                continue
            seen.add(eid)
            advisories.append({
                "kind": "unregistered-sec-id",
                "entity_id": eid,
                "note": "cited SEC-ID not found in issue registry (advisory only)",
            })
        return advisories
    except Exception:
        # Fail-soft, total: any error in the advisory path degrades to "no
        # advisory" and must never propagate into extraction/ingest.
        return []


def _known_registry_ids(registry_path: str | Path | None) -> set[str]:
    """Read the idgov issue-registry JSONL file and return the set of known
    ids (both `id` and, where present, `legacy_id`).

    Fail-soft: missing file -> empty set; malformed line -> skipped (other
    valid lines still consulted); any other error -> empty set.
    """
    path = Path(registry_path) if registry_path is not None else _DEFAULT_REGISTRY_PATH
    known: set[str] = set()
    try:
        if not path.exists():
            return known
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(row, dict):
                    continue
                rid = row.get("id")
                if isinstance(rid, str) and rid:
                    known.add(rid)
                legacy_id = row.get("legacy_id")
                if isinstance(legacy_id, str) and legacy_id:
                    known.add(legacy_id)
    except Exception:
        return set()
    return known


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_patterns(cfg: dict | None) -> dict[str, re.Pattern]:
    """Return compiled regex patterns, using config overrides if present.

    SEC-UNIFIED-003: config patterns were validated at config.validate() time.
    We trust them here — just compile and return.
    """
    if not cfg:
        return {}
    overrides_raw = cfg.get("entity_extraction_patterns", {})
    if not overrides_raw or not isinstance(overrides_raw, dict):
        return {}
    # Compile override patterns (already validated at load time — safe here)
    compiled: dict[str, re.Pattern] = {}
    for entity_type, pattern_str in overrides_raw.items():
        try:
            compiled[entity_type] = re.compile(pattern_str)
        except re.error:
            # Defensive: skip invalid patterns (should have been caught at validate())
            pass
    return compiled
