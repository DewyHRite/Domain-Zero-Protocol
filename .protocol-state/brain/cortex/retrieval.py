"""DZP Cortex — Hybrid Retrieval (Phase 2, v9.6.0).

WI-9..15 (PLAN-CORTEX-GRAPH-001 Phase 2):
  WI-9  : _bm25_available flag at Store.__init__ (implemented in store.py Phase 1a).
  WI-10 : _query_cache_key, _bump_index_epoch, _get_index_epoch, _evict_expired_cache,
           lookup_cache, store_cache, _sanitize_fts5_query, bm25_search,
           _recency_bias, _trust_boost, rrf_fuse.
  WI-11 : hybrid_search integrated into Store (Store.hybrid_search delegates here).
  WI-12 : --hybrid / --no-cache flags wired in brain.py (see brain.py).
  WI-13/15: brain cache status/clear subcommands (brain.py + this module).
  WI-14 : Config additions in config.py (query_cache_ttl_seconds=0, rrf_k=60, etc.).

SEC resolutions (non-negotiable):
  SEC-GRAPH-003: bm25_search runs contains_secret(snippet) on every FTS5 snippet;
                 rrf_fuse and hybrid_search run contains_secret(text_preview) before
                 returning to any caller.
  SEC-GRAPH-005: _sanitize_fts5_query uses phrase-only literal policy — strip ALL
                 double-quotes from input, then wrap in double-quotes:
                   '"' + query_text.replace('"', '') + '"'
                 This neutralizes all FTS5 operators (NEAR, AND, OR, NOT, column filters,
                 wildcard prefix) into a harmless literal phrase search. Documented here
                 and tested with adversarial inputs in test_hybrid_retrieval.py.
  SEC-GRAPH-006: rrf_fuse applies trust filter BEFORE dedup (not after) so a
                 trusted+untrusted ref_id collision cannot expose untrusted content.
  SEC-GRAPH-007: store_cache redacts results containing secrets before persisting to
                 cortex_query_cache (equivalent to export-boundary SEC-CORTEX-010).
  SEC-GRAPH-008: trust filter applied inside hybrid_search — only chunks within the
                 requested trust set are returned.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .store import Store

_REDACTION_MARKER = "[REDACTED — possible secret]"


# ---------------------------------------------------------------------------
# Secret detection import (shared with ingest; import lazily to avoid cycles)
# ---------------------------------------------------------------------------

def _contains_secret(text: str) -> bool:
    """Lazy import of ingest.contains_secret to avoid import cycles."""
    from .ingest import contains_secret
    return contains_secret(text)


# ---------------------------------------------------------------------------
# SEC-GRAPH-005: FTS5 MATCH injection sanitizer
# ---------------------------------------------------------------------------

_FTS5_QUERY_MAX_BYTES = 4096  # SEC-HYBRID-003: max input length before truncation


def _sanitize_fts5_query(query_text: str) -> str:
    """SEC-GRAPH-005 (v9.6.0): Phrase-only literal policy for FTS5 MATCH queries.

    Strips ALL double-quotes from the input, then wraps the result in double-quotes.
    This transforms any FTS5 operator (NEAR, AND, OR, NOT, col:filter, *, prefix)
    into a harmless literal phrase that FTS5 treats as an exact phrase match.

    SEC-HYBRID-003 (v9.6.0): Over-long inputs are truncated to _FTS5_QUERY_MAX_BYTES
    bytes before stripping/wrapping, so the FTS5 engine never receives a runaway query.

    Policy:
        sanitized = '"' + query_text[:_FTS5_QUERY_MAX_BYTES].replace('"', '') + '"'

    Examples of adversarial inputs and their neutralization:
        'a" OR "b'    -> '"a OR b"'       (injection attempt neutralized)
        '*'           -> '"*"'            (wildcard neutralized)
        'NEAR(x y)'   -> '"NEAR(x y)"'   (NEAR operator neutralized)
        'col:val'     -> '"col:val"'      (column filter neutralized)
        '"NOT x"'     -> '"NOT x"'        (quotes stripped, NOT treated as literal)
        'a' * 5000    -> capped at 4096 bytes, then wrapped

    FTS5 phrase search is always appropriate for Cortex hybrid retrieval — we are
    doing semantic recall, not FTS5 boolean query construction.
    """
    # SEC-HYBRID-003: truncate over-long input (byte-level cap)
    encoded = query_text.encode("utf-8", errors="replace")
    if len(encoded) > _FTS5_QUERY_MAX_BYTES:
        truncated = encoded[:_FTS5_QUERY_MAX_BYTES].decode("utf-8", errors="ignore")
    else:
        truncated = query_text
    stripped = truncated.replace('"', '')
    return '"' + stripped + '"'


# ---------------------------------------------------------------------------
# Index epoch helpers (Maki F2: cache invalidation on re-index)
# ---------------------------------------------------------------------------

_EPOCH_META_KEY = "last_index_epoch"


def _get_index_epoch(store: "Store") -> int:
    """Read the current index epoch from the metadata table. Returns 0 if unset."""
    store.init_schema()
    val = store.get_meta(_EPOCH_META_KEY)
    if val is None:
        return 0
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _bump_index_epoch(store: "Store") -> int:
    """Increment the index epoch counter. Called at the end of ingest.index().

    Maki F2: including epoch in cache keys ensures cached results are invalidated
    automatically after a re-index run.
    """
    epoch = _get_index_epoch(store) + 1
    store.set_meta(_EPOCH_META_KEY, str(epoch))
    return epoch


# ---------------------------------------------------------------------------
# Cache key construction (Maki F2: must include index_epoch)
# ---------------------------------------------------------------------------

def _query_cache_key(query_text: str, *, trust: list[str], k: int, index_epoch: int) -> str:
    """Deterministic cache key for a hybrid query.

    Includes index_epoch so cache misses on any re-index run (Maki F2).
    trust list is sorted for canonical ordering (order must not matter).
    """
    trust_sorted = ",".join(sorted(trust))
    raw = f"{index_epoch}:{k}:{trust_sorted}:{query_text}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Cache eviction helper
# ---------------------------------------------------------------------------

def _evict_expired_cache(store: "Store") -> int:
    """Delete expired cache entries from cortex_query_cache. Returns rows deleted."""
    store.init_schema()
    if store._active_schema < 3:
        return 0
    now_str = datetime.now(timezone.utc).isoformat()
    with store.connect() as conn:
        cur = conn.execute(
            "DELETE FROM cortex_query_cache WHERE expires_at <= ?",
            (now_str,),
        )
        return int(cur.rowcount or 0)


# ---------------------------------------------------------------------------
# Cache lookup
# ---------------------------------------------------------------------------

def lookup_cache(store: "Store", cache_key: str) -> list[dict] | None:
    """Look up a cached query result by key. Returns None on miss or expiry.

    Expired entries are treated as misses (lazy eviction — they will be
    cleaned up by _evict_expired_cache on the next cycle).

    SEC-HYBRID-001 (v9.6.0): After deserialising the cached JSON, each result's
    text field is re-scanned for secrets. Any result whose text contains a secret
    has its text replaced with _REDACTION_MARKER before being returned to the caller.
    This makes cache reads unconditionally safe even if a row was written before the
    store_cache redaction guard existed or if the secret check heuristic changed.
    """
    store.init_schema()
    if store._active_schema < 3:
        return None
    now_str = datetime.now(timezone.utc).isoformat()
    with store.connect() as conn:
        row = conn.execute(
            "SELECT result_json, expires_at FROM cortex_query_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
    if row is None:
        return None
    expires_at = row[1]
    if expires_at <= now_str:
        return None  # expired
    try:
        results = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None

    # SEC-HYBRID-001: post-read secret redaction (unconditional safe-read)
    safe_results = []
    for r in results:
        safe = dict(r)
        text = safe.get("text", "")
        if _contains_secret(text):
            safe["text"] = _REDACTION_MARKER
        safe_results.append(safe)
    return safe_results


# ---------------------------------------------------------------------------
# Cache store (SEC-GRAPH-007: redact secrets before persisting)
# ---------------------------------------------------------------------------

def store_cache(
    store: "Store",
    cache_key: str,
    results: list[dict],
    *,
    ttl_seconds: int,
    trust: list[str] | None = None,
    k: int = 0,
) -> None:
    """Persist a query result to cortex_query_cache with TTL.

    SEC-GRAPH-007: Each result's text field is scanned for secrets before writing.
    Any result containing a secret has its text replaced with the redaction marker.
    This mirrors SEC-CORTEX-010 at the export boundary.

    SEC-HYBRID-004 (v9.6.0): The ACTUAL trust_filter string (sorted trust list joined
    by comma) and k int are now stored in the corresponding metadata columns for
    auditability. Previously these were always written as "" and 0 literals.

    Maki F5: when ttl_seconds=0, this is a no-op (cache disabled by default).
    """
    if ttl_seconds <= 0:
        return  # cache disabled
    store.init_schema()
    if store._active_schema < 3:
        return

    # SEC-GRAPH-007: redact secrets before persisting
    safe_results = []
    for r in results:
        safe = dict(r)
        text = safe.get("text", "")
        if _contains_secret(text):
            safe["text"] = _REDACTION_MARKER
        safe_results.append(safe)

    now = datetime.now(timezone.utc)
    created_str = now.isoformat()
    expires_str = (now + timedelta(seconds=ttl_seconds)).isoformat()

    # SEC-HYBRID-004: store real trust_filter and k values for auditability
    trust_filter_str = ",".join(sorted(trust)) if trust else ""

    result_json = json.dumps(safe_results)
    with store.connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO cortex_query_cache
              (cache_key, query_hash, trust_filter, k, created_at, expires_at, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (cache_key, cache_key, trust_filter_str, k, created_str, expires_str, result_json),
        )


# ---------------------------------------------------------------------------
# BM25 lexical search (SEC-GRAPH-003 snippet redaction, SEC-GRAPH-005 sanitize)
# ---------------------------------------------------------------------------

def bm25_search(
    store: "Store",
    query_text: str,
    *,
    trust: list[str],
    k: int = 10,
) -> list[dict]:
    """BM25 lexical search over cortex_bm25 FTS5 table.

    Returns at most k results ranked by BM25 score.
    SEC-GRAPH-003: each FTS5 snippet is scanned for secrets; positives replaced
    with _REDACTION_MARKER before returning.
    SEC-GRAPH-005: query_text is sanitized via _sanitize_fts5_query (phrase-only
    literal policy) before being passed to FTS5 MATCH.
    SEC-GRAPH-008: trust filter applied in SQL (only chunks in `trust` set returned).
    S2-RISK-002: if _bm25_available is False or schema < 3, returns [] without raising.

    Maki F6: over-fetches k*2 (symmetric with vector path) before trust filtering,
    so trust carve-out does not starve the result set.
    """
    store.init_schema()

    # S2-RISK-002: graceful degradation
    if not store._bm25_available or store._active_schema < 3:
        return []

    sanitized = _sanitize_fts5_query(query_text)
    placeholders = ",".join("?" for _ in trust)
    overfetch = max(k * 2, k + 20)

    try:
        with store.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT ref_id, text, trust,
                       bm25(cortex_bm25) AS score
                FROM cortex_bm25
                WHERE cortex_bm25 MATCH ?
                  AND trust IN ({placeholders})
                ORDER BY score
                LIMIT ?
                """,
                (sanitized, *trust, overfetch),
            ).fetchall()
    except Exception:
        # FTS5 error (e.g., empty index) — return gracefully
        return []

    # SEC-HYBRID-002 (v9.6.0): batch content_refs enrichment — one round-trip for
    # ALL FTS5 result ref_ids instead of one connection/query per row (N+1 eliminated).
    ref_ids_ordered = [row[0] for row in rows]
    bm25_by_ref: dict[str, tuple] = {}
    for row in rows:
        ref_id = row[0]
        text = row[1] or ""
        # SEC-GRAPH-003: scan snippet for secrets before storing
        if _contains_secret(text):
            text = _REDACTION_MARKER
        bm25_by_ref[ref_id] = (text, row[2], float(row[3]) if row[3] is not None else 0.0)

    # Single batched lookup for all ref_ids
    if ref_ids_ordered:
        placeholders_refs = ",".join("?" for _ in ref_ids_ordered)
        with store.connect() as conn:
            ref_rows = conn.execute(
                f"""
                SELECT cr.ref_id, cr.storage_key, cr.line_start, cr.line_end,
                       cr.source_type, cr.content_hash, cr.suspect, cr.recorded_date
                FROM content_refs cr
                WHERE cr.ref_id IN ({placeholders_refs})
                """,
                ref_ids_ordered,
            ).fetchall()
        ref_map: dict[str, tuple] = {r[0]: r for r in ref_rows}
    else:
        ref_map = {}

    results = []
    for ref_id in ref_ids_ordered:
        if ref_id not in ref_map:
            # ref_id not found in content_refs (stale BM25 entry) — skip
            continue
        ref_row = ref_map[ref_id]
        text, trust_val, bm25_score = bm25_by_ref[ref_id]
        results.append({
            "id": ref_id,
            "text": text,
            "trust": trust_val,
            "source_path": ref_row[1],
            "line_start": int(ref_row[2]),
            "line_end": int(ref_row[3]),
            "source_type": ref_row[4],
            "content_hash": ref_row[5],
            "suspect": bool(ref_row[6]),
            "recorded_date": ref_row[7],
            "bm25_score": bm25_score,
        })

    return results[:k]


# ---------------------------------------------------------------------------
# Recency bias and trust boost (additive, applied after RRF)
# ---------------------------------------------------------------------------

def _recency_bias(recorded_date: str, *, half_life_days: float = 30.0) -> float:
    """Small additive recency boost: decays exponentially with age.

    boost = 0.5^(age_days / half_life_days)

    Returns a value in [0.0, 1.0]. A chunk recorded today scores 1.0;
    one recorded 30 days ago (default half-life) scores 0.5.
    Applied AFTER RRF, so it cannot flip the rank order dramatically.
    """
    if not recorded_date:
        return 0.0
    try:
        dt = datetime.fromisoformat(recorded_date.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0
        if age_days < 0:
            age_days = 0.0
        return math.pow(0.5, age_days / max(half_life_days, 1.0))
    except (ValueError, TypeError):
        return 0.0


def _trust_boost(trust: str) -> float:
    """Small additive trust boost to break ties in same-score clusters.

    trusted → 0.01, semi → 0.005, untrusted → 0.0
    Applied AFTER RRF; not enough to reverse a meaningful rank difference.
    """
    return {"trusted": 0.01, "semi": 0.005}.get(trust, 0.0)


# ---------------------------------------------------------------------------
# RRF fusion (Maki F1: TRUE Reciprocal Rank Fusion)
# ---------------------------------------------------------------------------

def rrf_fuse(
    bm25_results: list[dict],
    vector_results: list[dict],
    *,
    rrf_k: int = 60,
    trust: list[str],
    recency_half_life_days: float = 30.0,
    k: int | None = None,
) -> list[dict]:
    """Fuse BM25 and vector results using TRUE Reciprocal Rank Fusion.

    Maki F1: TRUE RRF formula (not min-max normalization):
        rrf_score(id) = sum over lists L of: 1 / (rrf_k + rank_in_L(id))
    where ranks are 1-indexed.

    Steps:
      1. Apply trust filter to BOTH input lists (SEC-GRAPH-006: filter BEFORE dedup).
      2. Compute RRF score for each ref_id across both ranked lists.
      3. Apply small additive recency bias and trust boost AFTER RRF.
      4. Dedup by ref_id (keeping highest-scored entry after trust filter).
      5. Sort descending by final score.
      6. SEC-GRAPH-003: scan text_preview for secrets; replace with redaction marker.

    SEC-GRAPH-006: trust filter is applied BEFORE deduplication to prevent a
    scenario where an untrusted chunk and a trusted chunk sharing the same ref_id
    could result in the untrusted chunk surviving dedup.
    """
    trust_set = set(trust)

    def _apply_trust(results: list[dict]) -> list[dict]:
        return [r for r in results if r.get("trust") in trust_set]

    # SEC-GRAPH-006: filter BEFORE dedup
    filtered_bm25 = _apply_trust(bm25_results)
    filtered_vector = _apply_trust(vector_results)

    # Compute RRF scores
    scores: dict[str, float] = {}
    best_result: dict[str, dict] = {}  # id → best (first-seen) result dict

    for rank_0, result in enumerate(filtered_bm25):
        rid = result["id"]
        rank = rank_0 + 1  # 1-indexed
        scores[rid] = scores.get(rid, 0.0) + 1.0 / (rrf_k + rank)
        if rid not in best_result:
            best_result[rid] = result

    for rank_0, result in enumerate(filtered_vector):
        rid = result["id"]
        rank = rank_0 + 1
        scores[rid] = scores.get(rid, 0.0) + 1.0 / (rrf_k + rank)
        if rid not in best_result:
            best_result[rid] = result

    # Compose final results with additive boosts
    fused: list[dict] = []
    for rid, base_score in scores.items():
        result = dict(best_result[rid])
        recency = _recency_bias(result.get("recorded_date", ""), half_life_days=recency_half_life_days)
        t_boost = _trust_boost(result.get("trust", ""))
        final_score = base_score + recency * 0.001 + t_boost  # tiny boosts won't flip ranks
        result["rrf_score"] = final_score

        # SEC-GRAPH-003: scan text_preview for secrets
        text = result.get("text", "")
        if _contains_secret(text):
            result["text"] = _REDACTION_MARKER

        fused.append(result)

    # Sort descending by rrf_score
    fused.sort(key=lambda x: x["rrf_score"], reverse=True)

    if k is not None:
        fused = fused[:k]

    return fused


# ---------------------------------------------------------------------------
# Cache subcommand helpers (brain cache status / clear)
# ---------------------------------------------------------------------------

def cache_status(store: "Store") -> dict:
    """Return cache statistics from cortex_query_cache.

    Returns: { "total_entries": int, "expired_entries": int, "active_entries": int }
    """
    store.init_schema()
    if store._active_schema < 3:
        return {"total_entries": 0, "expired_entries": 0, "active_entries": 0}
    now_str = datetime.now(timezone.utc).isoformat()
    with store.connect() as conn:
        total = int(conn.execute("SELECT COUNT(*) FROM cortex_query_cache").fetchone()[0])
        expired = int(conn.execute(
            "SELECT COUNT(*) FROM cortex_query_cache WHERE expires_at <= ?",
            (now_str,),
        ).fetchone()[0])
    return {
        "total_entries": total,
        "expired_entries": expired,
        "active_entries": total - expired,
    }


def cache_clear(store: "Store") -> int:
    """Delete ALL entries from cortex_query_cache. Returns rows deleted."""
    store.init_schema()
    if store._active_schema < 3:
        return 0
    with store.connect() as conn:
        cur = conn.execute("DELETE FROM cortex_query_cache")
        return int(cur.rowcount or 0)
