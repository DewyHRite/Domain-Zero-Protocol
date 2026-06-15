"""Source discovery, chunking, and incremental indexing."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .store import Chunk, Store


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


def chunk_file(repo_root: str | Path, path: str | Path, cfg: dict) -> list[Chunk]:
    repo = Path(repo_root).resolve()
    p = Path(path).resolve()
    rel = p.relative_to(repo).as_posix()
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
                    id=f"{rel}:{start + 1}:{content_hash[:16]}",
                    source_path=rel,
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


def index(repo_root: str | Path, cfg: dict, store: Store, embedder, *, dry_run: bool = False, progress=None) -> dict:
    batch_size = int((cfg.get("index") or {}).get("batch_size", 64))
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
        discovered_sources.add(rel)
        stat = path.stat()
        if not dry_run and store.source_state(rel) == (stat.st_mtime_ns, stat.st_size):
            skipped += 1
            continue
        file_chunks = chunk_file(repo_root, path, cfg)
        all_chunks += len(file_chunks)
        if dry_run:
            continue
        removed += store.delete_by_source(rel)
        if not file_chunks:
            store.delete_source_state(rel)
            continue
        pending.extend(file_chunks)
        if len(pending) >= batch_size:
            upserted += _flush(pending, store, embedder)
            if progress:
                progress({"files_scanned": len(files), "files_done": file_index, "chunks_upserted": upserted})
            pending = []
        store.set_source_state(rel, mtime_ns=stat.st_mtime_ns, size=stat.st_size, indexed_at=now)
    if dry_run:
        return {"files_scanned": len(files), "files_skipped": 0, "chunks": all_chunks, "upserted": 0, "removed": 0}
    if pending:
        upserted += _flush(pending, store, embedder)
        if progress:
            progress({"files_scanned": len(files), "files_done": len(files), "chunks_upserted": upserted})
    for source in set(store.list_indexed_sources()) - discovered_sources:
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


def freshness_summary(repo_root: str | Path, cfg: dict, store: Store) -> dict:
    repo = Path(repo_root).resolve()
    files = discover(repo, cfg)
    discovered = {path.relative_to(repo).as_posix(): path for path in files}
    indexed = set(store.list_indexed_sources())
    changed = []
    missing = sorted(indexed - set(discovered))
    for rel, path in discovered.items():
        stat = path.stat()
        if store.source_state(rel) != (stat.st_mtime_ns, stat.st_size):
            changed.append(rel)
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
