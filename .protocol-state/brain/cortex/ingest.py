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
    return False


def contains_secret(text: str) -> bool:
    """Whole-text secret check shared by chunk_file (index) and memory.remember."""
    if any(pattern.search(text) for pattern in SECRET_FORMAT_PATTERNS):
        return True
    return any(not _is_placeholder_value(m.group(1)) for m in _SECRET_KEYWORD_RE.finditer(text))


INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?(previous|prior) instructions", re.I),
    re.compile(r"you are now", re.I),
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
    for key in ("include_folders", "include_reports", "include_code"):
        for rel in cfg.get(key, []):
            folder = (repo / rel).resolve()
            if not folder.exists() or not folder.is_dir():
                continue
            for path in folder.rglob("*"):
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
    return not any(token and token in lowered for token in [*tokens, *generated])


def chunk_file(repo_root: str | Path, path: str | Path, cfg: dict, install_scope: str = "") -> list[Chunk]:
    repo = Path(repo_root).resolve()
    p = Path(path).resolve()
    rel = p.relative_to(repo).as_posix()
    # Storage key carries the install scope; classification/trust use the CLEAN rel.
    skey = _storage_key(install_scope, rel)
    text = p.read_text(encoding="utf-8", errors="replace")
    if contains_secret(text):
        return []
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
    # policy is the safe choice.
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


def index(repo_root: str | Path, cfg: dict, store: Store, embedder, *, dry_run: bool = False, progress=None, install_scope: str | None = None) -> dict:
    batch_size = int((cfg.get("index") or {}).get("batch_size", 64))
    # BUG-CORTEX-005: derive the install scope (empty unless a shared store is opted
    # into). All source keys, state lookups, and orphan cleanup use the storage key.
    scope = paths.index_scope(repo_root, cfg) if install_scope is None else install_scope
    files = discover(repo_root, cfg)
    all_chunks = 0
    upserted = 0
    skipped = 0
    removed = 0
    pending: list[Chunk] = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    discovered_sources: set[str] = set()
    for file_index, path in enumerate(files, 1):
        rel = path.relative_to(Path(repo_root).resolve()).as_posix()
        skey = _storage_key(scope, rel)
        discovered_sources.add(skey)
        stat = path.stat()
        if not dry_run and store.source_state(skey) == (stat.st_mtime_ns, stat.st_size):
            skipped += 1
            continue
        file_chunks = chunk_file(repo_root, path, cfg, install_scope=scope)
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
        return {"files_scanned": len(files), "files_skipped": 0, "chunks": all_chunks, "upserted": 0, "removed": 0}
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
    return {"files_scanned": len(files), "files_skipped": skipped, "chunks": all_chunks, "upserted": upserted, "removed": removed}


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
    """
    store.init_schema()
    with store.connect() as conn:
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
    if rel.startswith("protocol/") or rel in {"CLAUDE.md", "AI_INSTRUCTIONS.md", "README.md"} or rel.startswith("scripts/"):
        return "trusted"
    return "semi"
