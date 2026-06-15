"""Source discovery, chunking, and incremental indexing."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from . import paths
from .store import Chunk, Store


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
_SCOPED_PREFIX_RE = re.compile(r"^@[0-9a-f]{12}/")


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
SECRET_PATTERNS = [
    re.compile(r"api[_-]?key\s*=", re.I),
    re.compile(r"secret\s*=", re.I),
    re.compile(r"password\s*=", re.I),
    re.compile(r"token\s*=", re.I),
    # SEC-BRAIN-008: AWS provider key formats (2026-06-14)
    # These require explicit keyword matching because the keyword is not adjacent
    # to a bare "secret=" or "key=" that the patterns above would catch.
    re.compile(r"access[_-]?key[_-]?id\s*=", re.I),       # AWS_ACCESS_KEY_ID=
    re.compile(r"secret[_-]?access[_-]?key\s*=", re.I),   # AWS_SECRET_ACCESS_KEY=
]
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
    if path.suffix.lower() in BINARY_SUFFIXES:
        return False
    if path.stat().st_size > 1_000_000:
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
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
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


def _source_type(rel: str) -> str:
    if rel.startswith(".protocol-state/dev-notes") or rel.startswith(".protocol-state/security") or rel.startswith(".dzp-domain/"):
        return "protected"
    if rel.startswith("scripts/") or rel.endswith(".py") or rel.endswith(".ps1") or rel.endswith(".sh"):
        return "code"
    if rel.startswith("internal-docs/"):
        return "report"
    return "doc"


def _trust_for(rel: str) -> str:
    if rel.startswith("protocol/") or rel in {"CLAUDE.md", "AI_INSTRUCTIONS.md", "README.md"} or rel.startswith("scripts/"):
        return "trusted"
    if rel.startswith(".protocol-state/") or rel.startswith(".dzp-domain/") or rel.startswith("internal-docs/"):
        return "semi"
    return "trusted"
