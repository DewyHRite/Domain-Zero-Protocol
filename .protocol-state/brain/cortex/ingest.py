"""Source discovery, chunking, and incremental indexing."""

from __future__ import annotations

import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from . import paths
from .config import DEFAULT_CONFIG
from .store import Chunk, Store, _SCOPED_PREFIX_RE


# BUG-CORTEX-005 (v9.3.0): install-scoped storage keys for shared brains.
# A "storage key" is the value stored in chunks.source_path / source_state /
# chunk.id. For the default (unshared) case the scope is "" and the storage key is
# exactly the repo-relative path - byte-identical to legacy behavior. For a shared
# store the scope is the per-install id and keys are namespaced as "@<scope>/<rel>"
# so two installs' identically-pathed files never clobber each other.
# A source-key scope is ALWAYS a per-install id = install_id() = 12 lowercase hex
# (see paths.index_scope). So a scoped storage key is precisely `@<12-hex>/<rel>`.
# Matching on this exact shape (not a bare leading "@") avoids misclassifying a
# legitimate repo-relative path that happens to start with "@" (e.g. "@team/x.md")
# as a scoped key — which would corrupt orphan cleanup / freshness accounting.
# CODE-001 (v9.3.3): the pattern is now defined once in store.py and imported above,
# so ingest and store can never drift on the scoped-key format.


def _is_scoped_storage_key(storage_key: str) -> bool:
    return bool(_SCOPED_PREFIX_RE.match(storage_key))


def _scope_prefix(scope: str) -> str:
    return "" if not scope else f"@{scope}/"


def _storage_key(scope: str, rel: str) -> str:
    return _scope_prefix(scope) + rel


def _belongs_to_scope(storage_key: str, scope: str) -> bool:
    """True if a storage key belongs to the given scope (for orphan cleanup)."""
    if scope:
        return storage_key.startswith(_scope_prefix(scope))
    # Default scope only owns UNSCOPED keys, so it never deletes another install's
    # scoped sources from a shared data dir (and vice versa).
    return not _is_scoped_storage_key(storage_key)


BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".docx", ".zip", ".gz", ".db", ".sqlite", ".html"}

# Default per-file cap (SEC-CORTEX-003 / FEAT-CORTEX-SCOPE-001, v9.3.2):
# config-driven via brain.config.yaml `max_file_bytes`; this constant is the
# in-code fallback when the key is absent (kept in sync with config.DEFAULT_CONFIG).
DEFAULT_MAX_FILE_BYTES = 6_000_000

# SEC-CORTEX-002 (v9.3.2): placeholder-aware secret detection.
# Two layers:
#   1. SECRET_FORMAT_PATTERNS  - high-confidence token FORMATS, always dropped.
#   2. _SECRET_KEYWORD_RE       - keyword[:=]value, dropped ONLY when the value is
#      not an obvious placeholder (see _is_placeholder_value). This stops the old
#      naive keyword scan from silently dropping legitimate business docs whose only
#      "secret" is a template like `Password: [PASSWORD]` (Megumi SEC-CORTEX-002).
SECRET_FORMAT_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),                 # PEM private keys
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                               # AWS access key id
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),                     # GitHub tokens
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),                   # Slack tokens
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),  # JWT
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b"),                  # Bearer tokens
]
# No leading \b: a credential keyword is often a SUFFIX of an env var name
# (RESEND_API_KEY=, AWS_SECRET_ACCESS_KEY=) where '_' suppresses a word boundary.
# Longest keywords are listed first so the alternation prefers the specific form.
_SECRET_KEYWORD_RE = re.compile(
    r"(?i)(?:secret[_-]?access[_-]?key|access[_-]?key[_-]?id|api[_-]?key|"
    r"secret|password|passwd|token)\s*[:=]\s*(\S+)"
)
_PLACEHOLDER_WORDS = {
    "your", "example", "changeme", "change-me", "placeholder", "redacted",
    "tbd", "todo", "dummy", "none", "null", "xxx", "sample",
}

# SEC-DZPUP-9.9.4-010 (Megumi-ruled, mirrors SEC-DZPUP-9.9.4-005/-006/-007 in
# scan_protected_records.py): a BOUNDED, exact/regex recognizer for TypeScript/
# JSON-schema type-annotation tokens. Value-side ONLY — deliberately NOT added
# to _PLACEHOLDER_WORDS, which is substring-matched (`word in low`, below) and
# would therefore mask any value merely CONTAINING one of these tokens (e.g.
# `password: correcthorse_string_x9`), a real detection weakening. This set is
# matched via fullmatch only, so it cannot widen the substring-match surface.
_TYPE_ANNOTATION_TOKENS = {
    "string", "number", "boolean", "any", "unknown", "void", "object",
    "undefined", "null", "bigint", "symbol", "never", "date",
    "array", "record", "map", "set", "buffer",
    "encryptedstring",
}
_TYPE_ANNOTATION_RE = re.compile(
    r"^(?:" + "|".join(sorted(_TYPE_ANNOTATION_TOKENS, key=len, reverse=True)) + r")(\[\])?$",
    re.IGNORECASE,
)


def _is_placeholder_value(value: str) -> bool:
    """True when a keyword's value is an obvious placeholder, not a real secret."""
    v = value.strip().strip("\"'`,;")
    if not v:
        return True
    # Templated/bracketed placeholders: [..], <..>, {..}, $ENV, %VAR%
    if v[0] in "[<{$%" or v[-1] in "]>}%":
        return True
    # Masks / dummies: ****, ----, xxxx, and embedded x-runs (re_xxxx, sk_xxxx)
    if re.fullmatch(r"[x*\-_.]{3,}", v, re.I) or re.search(r"x{4,}", v, re.I):
        return True
    low = v.lower()
    if any(word in low for word in _PLACEHOLDER_WORDS):
        return True
    if len(v) < 6:  # too short to be a credible secret
        return True
    if _TYPE_ANNOTATION_RE.fullmatch(v):
        return True
    return False


def contains_secret(text: str) -> bool:
    """Whole-text secret check shared by chunk_file (index) and memory.remember."""
    if any(pattern.search(text) for pattern in SECRET_FORMAT_PATTERNS):
        return True
    return any(not _is_placeholder_value(m.group(1)) for m in _SECRET_KEYWORD_RE.finditer(text))


# SEC-DZPUP-9.9.4-013 (Megumi-ruled): restore the SEC-CORTEX-006 injection-pattern
# set that had been reverted to a smaller 3-pattern list. Full set below.
INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?(previous|prior) instructions", re.I),
    re.compile(r"disregard (the )?(above|previous|prior)", re.I),
    re.compile(r"you are now", re.I),
    re.compile(r"new instructions\s*:", re.I),
    re.compile(r"reveal (your )?(system )?(prompt|instructions)", re.I),
    re.compile(r"\bsystem\s*:", re.I),
]


def discover(repo_root: str | Path, cfg: dict) -> list[Path]:
    repo = Path(repo_root).resolve()
    candidates: set[Path] = set()
    for key in ("include_files", "include_protected"):
        for rel in cfg.get(key, []):
            path = (repo / rel).resolve()
            if path.exists() and _safe_candidate(repo, path, cfg):
                candidates.add(path)
    # SEC-CORTEX-011 (v9.3.4): pass recurse_symlinks=False to rglob on Python 3.13+
    # to prevent cyclic-symlink DoS on POSIX systems. The `recurse_symlinks` kwarg was
    # added to Path.rglob() in Python 3.13 (passing the wrong name raises TypeError on
    # 3.13+), so we guard on (3, 13) and fall back to an empty dict on older Pythons.
    _rglob_kw: dict = {"recurse_symlinks": False} if sys.version_info >= (3, 13) else {}
    for key in ("include_folders", "include_reports", "include_code"):
        for rel in cfg.get(key, []):
            folder = (repo / rel).resolve()
            if not folder.exists() or not folder.is_dir():
                continue
            for path in folder.rglob("*", **_rglob_kw):
                if path.is_file() and _safe_candidate(repo, path.resolve(), cfg):
                    candidates.add(path.resolve())
    return sorted(candidates)


def _safe_candidate(repo: Path, path: Path, cfg: dict) -> bool:
    try:
        rel = path.relative_to(repo).as_posix()
    except ValueError:
        return False
    lowered = rel.lower()
    suffix = path.suffix.lower()
    # Denylist: known binary formats always blocked (defense-in-depth layer 1).
    if suffix in BINARY_SUFFIXES:
        return False
    # SEC-002 (v9.3.3): positive ALLOWLIST (defense-in-depth layer 2).
    # Only extensions present in index_extensions are admitted; unknown/absent
    # extensions are excluded by default, preventing accidental indexing of
    # binary-looking files that weren't in BINARY_SUFFIXES.
    allowed_exts: list[str] = cfg.get("index_extensions", DEFAULT_CONFIG["index_extensions"])
    # Normalise to lowercase. An explicit "" entry is preserved so callers can opt in
    # extension-less files (Makefile, Dockerfile, LICENSE) per the index_extensions
    # contract documented in config.py — filtering it out here silently broke that.
    allowed_lower = {ext.lower() for ext in allowed_exts}
    if suffix not in allowed_lower:
        return False
    max_bytes = int(cfg.get("max_file_bytes", DEFAULT_MAX_FILE_BYTES))  # config-driven cap (v9.3.2)
    if path.stat().st_size > max_bytes:
        return False
    tokens = [str(token).lower() for token in cfg.get("exclude_tokens", [])]
    generated = ("brain.db", "cortex-snapshot.md", "model-cache", "index.log", "memories/")
    # Generated-files guard: hardcoded Cortex artefacts that must never be indexed.
    # Listed separately from exclude_tokens so they fire unconditionally and cannot
    # be bypassed by exclude_exceptions (these artefacts never live under a
    # plans-style subtree in practice, but we enforce it defensively).
    if any(token and token in lowered for token in generated):
        return False
    # FEAT-CORTEX-EXCL-001 (v9.4.1): exclude_exceptions — a more-specific per-token
    # override.  For each exclude_token that WOULD block this path we ask: does an
    # exception exist that (a) re-admits this exact path AND (b) is a narrower
    # specialisation of the blocking token (i.e. exc starts with that token)?
    #
    # Condition (b) is the critical safety gate: it means exception "docs/superpowers/plans"
    # can only cancel the token "docs/superpowers" (because plans starts with superpowers),
    # never an unrelated token like "__pycache__" or "internal-docs".  Without (b) the
    # exception would silence ALL tokens for a path it matches on condition (a) alone,
    # allowing __pycache__ or internal-docs paths inside plans/ to slip through.
    #
    # Design choices documented here for Megumi / Toji review:
    #   - Matching basis: normalised lowercase POSIX relative path (same as tokens).
    #   - An exception "exc" re-admits a path when: lowered == exc OR lowered.startswith(exc+"/")
    #     The trailing "/" enforces a true path-segment boundary: "plans-archive" does NOT
    #     match exception "plans" because it doesn't start with "plans/".
    #   - An exception "exc" cancels token "token" only when exc.startswith(token):
    #     the exception is a sub-path of what the token blocks, so it's genuinely narrower.
    #   - If multiple tokens match, ALL must be individually cancelled; any un-cancelled
    #     token still blocks the path.
    #   - Generated-files guard (above) is unconditional and cannot be bypassed.
    #   - Binary/ext/size guards already fired before this block.
    #   - contains_secret() at chunk_file time is unaffected (runs after admission).
    exceptions_raw: list = cfg.get("exclude_exceptions", DEFAULT_CONFIG["exclude_exceptions"])
    exceptions = [str(e).lower() for e in exceptions_raw if e]

    def _token_cancelled_by_exception(token: str) -> bool:
        """True if an exception both re-admits the current path AND is a narrower
        sub-path of the blocking token (so it genuinely overrides that token only)."""
        for exc in exceptions:
            path_re_admitted = (lowered == exc or lowered.startswith(exc + "/"))
            exception_is_narrower = exc.startswith(token)
            if path_re_admitted and exception_is_narrower:
                return True
        return False

    for token in tokens:
        if not token:
            continue
        if token in lowered:
            if not _token_cancelled_by_exception(token):
                return False
    return True


def chunk_file(
    repo_root: str | Path,
    path: str | Path,
    cfg: dict,
    install_scope: str = "",
    drop_reason: list[str] | None = None,
) -> list[Chunk]:
    """Chunk a file for indexing.

    SEC-DZPUP-9.9.4-012 (Megumi-ruled, decisive semantics per Sukuna): secret
    detection is now PER-CHUNK, not whole-file. A chunk whose text matches
    contains_secret() is OMITTED from the returned list — the rest of the file
    is still indexed. This replaces the prior `if contains_secret(text): return []`
    whole-file drop (Defect B, BUG-CORTEX-INGEST-SECRET-FP-001), which discarded
    an entire legitimate document (e.g. an 18,237-line typed spec) over a handful
    of false-positive lines.

    `drop_reason`, if provided, is an out-parameter: each secret-shaped chunk
    skipped appends a "{rel}:{line_start}" marker to it, letting callers (index())
    report per-file/per-chunk secret-drop counts (SEC-DZPUP-9.9.4-011).
    """
    repo = Path(repo_root).resolve()
    p = Path(path).resolve()
    rel = p.relative_to(repo).as_posix()
    # Storage key carries the install scope; classification/trust use the CLEAN rel.
    skey = _storage_key(install_scope, rel)
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    max_chars = int((cfg.get("chunk") or {}).get("code_max_chars" if p.suffix == ".py" else "md_max_chars", 1200))
    chunks: list[Chunk] = []
    start = 0
    while start < len(lines):
        end = start
        chars = 0
        while end < len(lines) and chars + len(lines[end]) + 1 <= max_chars:
            chars += len(lines[end]) + 1
            end += 1
        if end == start:
            end += 1
        body = "\n".join(lines[start:end]).strip()
        if body:
            # SEC-DZPUP-9.9.4-012: per-chunk secret gate. Only THIS chunk is
            # dropped; sibling chunks in the same file are unaffected.
            if contains_secret(body):
                if drop_reason is not None:
                    drop_reason.append(f"{rel}:{start + 1}")
                # SEC-DZPUP-9.9.4-011: loud, unconditional stderr signal — a
                # knowledge base that silently omits content is unacceptable
                # (Defect C, BUG-CORTEX-INGEST-SECRET-FP-001).
                print(
                    f"[cortex:ingest] REDACT {rel}:{start + 1}: secret-shaped chunk dropped from index.",
                    file=sys.stderr,
                )
                start = end
                continue
            content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            chunks.append(
                Chunk(
                    id=f"{skey}:{start + 1}:{content_hash[:16]}",
                    source_path=skey,
                    source_type=_source_type(rel),
                    line_start=start + 1,
                    line_end=end,
                    content_hash=content_hash,
                    recorded_date=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    text=body,
                    trust=_trust_for(rel),
                    suspect=any(pattern.search(body) for pattern in INJECTION_PATTERNS),
                )
            )
        start = end
    # SEC-002 (v9.3.3): per-file chunk cap. If max_file_chunks > 0 and we exceeded
    # it, drop the entire file and warn. We check AFTER chunking so we get an accurate
    # count; dropping partial chunks would create index drift, so the all-or-nothing
    # policy is the safe choice. (Unrelated to the per-chunk secret gate above — this
    # is a size/volume guard, not a secret-content guard.)
    max_chunks = cfg.get("max_file_chunks", DEFAULT_CONFIG["max_file_chunks"])
    if max_chunks and len(chunks) > max_chunks:
        print(
            f"[cortex:ingest] SKIP {rel}: chunk cap exceeded "
            f"({len(chunks)} chunks > max_file_chunks={max_chunks}). "
            "Increase max_file_chunks or exclude this file.",
            file=sys.stderr,
        )
        return []
    return chunks


def index(repo_root: str | Path, cfg: dict, store: Store, embedder, *, dry_run: bool = False, force: bool = False, progress=None, install_scope: str | None = None) -> dict:
    batch_size = int((cfg.get("index") or {}).get("batch_size", 64))
    # BUG-CORTEX-005: derive the install scope (empty unless a shared store is opted
    # into). All source keys, state lookups, and orphan cleanup use the storage key.
    scope = paths.index_scope(repo_root, cfg) if install_scope is None else install_scope
    files = discover(repo_root, cfg)
    all_chunks = 0
    upserted = 0
    skipped = 0
    removed = 0
    # SEC-DZPUP-9.9.4-011: observability counters for the per-chunk secret gate
    # (SEC-DZPUP-9.9.4-012).
    #
    # CODE-001 (Toji audit 2026-07-11, MEDIUM): `files_dropped_secret` was named
    # as though it counted files whose content vanished from the index, but its
    # actual semantics were "had >=1 chunk redacted" -- clean sibling chunks from
    # the SAME file are still indexed (see the per-chunk gate in chunk_file()
    # above), so a telemetry consumer reading files_dropped_secret > 0 could
    # wrongly conclude an entire source disappeared. Three fields now report
    # this precisely:
    #   files_with_secret_redactions - files with >=1 redacted chunk, REGARDLESS
    #     of whether clean siblings from that file were still indexed. This is
    #     the accurately-named successor to the old field.
    #   files_fully_omitted_secret   - the STRICT SUBSET of the above where the
    #     file ended up with ZERO indexed chunks (every chunk in it was secret-
    #     shaped, or the file was otherwise fully dropped) -- i.e. content
    #     actually vanished from the index, not merely partially redacted.
    #   files_dropped_secret         - BACK-COMPAT ALIAS, always numerically
    #     equal to files_with_secret_redactions. Kept so existing consumers/
    #     tests reading this key are not broken by this rename.
    # chunks_dropped_secret is the total redacted-chunk count across the run
    # (unchanged). All four surface in the returned result dict so a knowledge
    # base can never silently omit content without it showing up in
    # `brain.sh index` output.
    files_dropped_secret = 0
    files_fully_omitted_secret = 0
    chunks_dropped_secret = 0
    pending: list[Chunk] = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    discovered_sources: set[str] = set()
    for file_index, path in enumerate(files, 1):
        rel = path.relative_to(Path(repo_root).resolve()).as_posix()
        skey = _storage_key(scope, rel)
        discovered_sources.add(skey)
        stat = path.stat()
        if not dry_run and not force and store.source_state(skey) == (stat.st_mtime_ns, stat.st_size):
            skipped += 1
            continue
        drop_reason: list[str] = []
        file_chunks = chunk_file(repo_root, path, cfg, install_scope=scope, drop_reason=drop_reason)
        if drop_reason:
            # CODE-001: this file had >=1 chunk redacted (files_with_secret_redactions
            # / files_dropped_secret alias). It is ADDITIONALLY counted as fully
            # omitted only when it produced zero indexed chunks overall.
            files_dropped_secret += 1
            chunks_dropped_secret += len(drop_reason)
            if not file_chunks:
                files_fully_omitted_secret += 1
        all_chunks += len(file_chunks)
        if dry_run:
            continue
        removed += store.delete_by_source(skey)
        if not file_chunks:
            store.delete_source_state(skey)
            continue
        pending.extend(file_chunks)
        if len(pending) >= batch_size:
            upserted += _flush(pending, store, embedder)
            if progress:
                progress({"files_scanned": len(files), "files_done": file_index, "chunks_upserted": upserted})
            pending = []
        store.set_source_state(skey, mtime_ns=stat.st_mtime_ns, size=stat.st_size, indexed_at=now)
    if dry_run:
        return {
            "files_scanned": len(files),
            "files_skipped": 0,
            "chunks": all_chunks,
            "upserted": 0,
            "removed": 0,
            "files_dropped_secret": files_dropped_secret,  # back-compat alias (CODE-001)
            "chunks_dropped_secret": chunks_dropped_secret,
            "files_with_secret_redactions": files_dropped_secret,
            "files_fully_omitted_secret": files_fully_omitted_secret,
        }
    if pending:
        upserted += _flush(pending, store, embedder)
        if progress:
            progress({"files_scanned": len(files), "files_done": len(files), "chunks_upserted": upserted})
    # Orphan cleanup is SCOPE-AWARE: an install only removes its OWN sources, never
    # another install's entries from a shared data dir.
    owned = {s for s in store.list_indexed_sources() if _belongs_to_scope(s, scope)}
    for source in owned - discovered_sources:
        removed += store.delete_by_source(source)
    store.set_meta("last_index", now)
    # WI-S3-5 (Stage 3 Phase 1, v9.7.0): post-index eviction.
    # Run ONLY when storage_budget_mb is configured AND DB is over budget.
    # Fail-soft: eviction errors log a WARNING but never fail the index run.
    # Budget None (default) = unlimited = skip eviction entirely.
    _run_post_index_eviction(store, cfg)
    return {
        "files_scanned": len(files),
        "files_skipped": skipped,
        "chunks": all_chunks,
        "upserted": upserted,
        "removed": removed,
        "files_dropped_secret": files_dropped_secret,  # back-compat alias (CODE-001)
        "chunks_dropped_secret": chunks_dropped_secret,
        "files_with_secret_redactions": files_dropped_secret,
        "files_fully_omitted_secret": files_fully_omitted_secret,
    }


def _run_post_index_eviction(store: "Store", cfg: dict) -> None:
    """WI-S3-5 helper: invoke eviction if over budget (fail-soft).

    Separated from index() to keep the main function clean.
    Uses a SEPARATE connection to run eviction outside the index transaction.
    """
    import logging as _logging
    _elog = _logging.getLogger(__name__)

    budget_mb = cfg.get("storage_budget_mb")
    if budget_mb is None:
        return  # unlimited — no eviction

    try:
        current_mb = store._db_size_mb()
        if current_mb <= budget_mb:
            return  # within budget — skip

        _elog.info(
            "Cortex: post-index eviction triggered (%.1f MB > budget %.1f MB)",
            current_mb, budget_mb,
        )
        with store.connect() as conn:
            result = store._evict_to_budget(conn, target_mb=float(budget_mb))
        if result["evicted_count"] > 0:
            _elog.info(
                "Cortex: evicted %d chunks (~%.2f MB estimate) — tiers: %s",
                result["evicted_count"],
                result["evicted_mb_estimate"],
                result["tiers_used"],
            )
    except Exception as exc:
        # Fail-soft: eviction failure never fails the index run.
        import logging as _l
        _l.getLogger(__name__).warning(
            "Cortex: post-index eviction failed (fail-soft): %s", exc
        )


def _flush(chunks: list[Chunk], store: Store, embedder) -> int:
    vectors = embedder.embed_many(chunk.text for chunk in chunks)
    # A3: Guard against cardinality mismatch before upsert (ingest.py:153).
    # A mismatched list would silently zip to the shorter side and corrupt the index.
    if len(vectors) != len(chunks):
        raise ValueError(
            f"Cortex ingest: chunk/vector count mismatch — "
            f"{len(chunks)} chunks vs {len(vectors)} vectors. "
            "Aborting upsert to prevent index corruption."
        )
    return store.upsert(zip(chunks, vectors))


def freshness_summary(repo_root: str | Path, cfg: dict, store: Store, install_scope: str | None = None) -> dict:
    repo = Path(repo_root).resolve()
    scope = paths.index_scope(repo, cfg) if install_scope is None else install_scope
    files = discover(repo, cfg)
    # Key on storage keys so freshness is computed against THIS install's namespace.
    discovered = {_storage_key(scope, path.relative_to(repo).as_posix()): path for path in files}
    indexed = {s for s in store.list_indexed_sources() if _belongs_to_scope(s, scope)}
    changed = []
    missing = sorted(indexed - set(discovered))
    for skey, path in discovered.items():
        stat = path.stat()
        if store.source_state(skey) != (stat.st_mtime_ns, stat.st_size):
            changed.append(skey)
    return {
        "files_discovered": len(discovered),
        "changed_sources": len(changed),
        "missing_sources": len(missing),
        "stale": bool(changed or missing),
    }


def top_sources_by_chunks(store: "Store", *, n: int = 10) -> list[dict]:
    """SEC-002 (v9.3.3): Return the top-n indexed sources ranked by chunk count (descending).

    READ-ONLY diagnostic. Returns a list of dicts with keys:
      source_path (str): repo-relative path (install-scope prefix stripped)
      chunk_count (int): number of chunks from this source in the index
    Returns [] if the index is empty.

    PLAN-DESIGN-001 Phase 1 (v9.4.0): dispatches on store._active_schema.
      v2: queries content_refs.storage_key (replaces chunks.source_path)
      v1: queries chunks.source_path (legacy behavior unchanged)
    """
    store.init_schema()
    with store.connect() as conn:
        if store._active_schema in (2, 3, 4):
            # v2/v3: content-addressed — source paths are in content_refs.storage_key.
            rows = conn.execute(
                """
                SELECT storage_key AS source_path, COUNT(*) AS chunk_count
                FROM content_refs
                GROUP BY storage_key
                ORDER BY chunk_count DESC
                LIMIT ?
                """,
                (n,),
            ).fetchall()
        else:
            # v1 legacy — source paths are in chunks.source_path.
            rows = conn.execute(
                """
                SELECT source_path, COUNT(*) AS chunk_count
                FROM chunks
                GROUP BY source_path
                ORDER BY chunk_count DESC
                LIMIT ?
                """,
                (n,),
            ).fetchall()
    from .store import _display_source  # local import avoids circular at module level
    return [
        {"source_path": _display_source(str(row[0])), "chunk_count": int(row[1])}
        for row in rows
    ]


def _source_type(rel: str) -> str:
    # C2 (v9.5.0, S-RISK-007 Case A): archive roots are classified FIRST.
    # SEC-UNIFIED-001 (CLOSED, Megumi Tier-3 @approved): archived protected-doc content
    # uses source_type='archive', NOT 'protected'. This is intentionally distinct from
    # the live protected-doc classification so that STAGE 3 eviction can treat archives
    # as evictable (Priority 1) while live protected docs remain in the NEVER-evict block.
    # NOTE: The plan prose (S-RISK-007 line ~1361) says "protected/trusted-equivalent"
    # but SEC-UNIFIED-001 OVERRIDES that to 'archive'/'semi'. Implementation follows
    # SEC-UNIFIED-001. Megumi to rule on prose discrepancy in Tier-3 review.
    if rel.startswith(".dzp-domain/archive/") or rel.startswith(".protocol-state/archive/"):
        return "archive"
    # Live protected docs (must check AFTER archive guard above so archived rotations
    # of dev-notes/security-review/domain.record are not misclassified as 'protected').
    if rel.startswith(".protocol-state/dev-notes") or rel.startswith(".protocol-state/security") or rel.startswith(".dzp-domain/"):
        return "protected"
    if rel.startswith("scripts/") or rel.endswith(".py") or rel.endswith(".ps1") or rel.endswith(".sh"):
        return "code"
    if rel.startswith("internal-docs/"):
        return "report"
    return "doc"


def _trust_for(rel: str) -> str:
    # SEC-CORTEX-001 (v9.3.2): default-deny trust. Only canonical, instruction-bearing
    # protocol material is `trusted`; ALL other content (docs/, project data, memories,
    # newly-indexed business/project files) defaults to `semi`. This prevents trust
    # inflation when Cortex scope is expanded beyond the protocol layer.
    #
    # C2 (v9.5.0, S-RISK-007 Case A): archive roots are explicitly 'semi'.
    # SEC-UNIFIED-001 (CLOSED): archived content must use trust='semi' — they are
    # historical, re-indexable from disk, and not live protected documents. This also
    # ensures STAGE 3 can evict archive chunks under Priority 1 (evictable) without
    # hitting the NEVER-evict guard that covers trust='trusted' chunks.
    # Archive check must come BEFORE the scripts/ 'trusted' check since archive paths
    # ending in .py/.ps1/.sh (unlikely but possible) must not inherit 'trusted'.
    if rel.startswith(".dzp-domain/archive/") or rel.startswith(".protocol-state/archive/"):
        return "semi"
    if rel.startswith("protocol/") or rel in {"CLAUDE.md", "AI_INSTRUCTIONS.md", "README.md"} or rel.startswith("scripts/"):
        return "trusted"
    return "semi"
