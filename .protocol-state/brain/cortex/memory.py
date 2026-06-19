"""Cortex remembered-fact write path."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .errors import UnsafePathError
from .store import Chunk, Store
from .ingest import contains_secret, INJECTION_PATTERNS


ALLOWED_TYPES = {"decision", "lesson", "sec", "note"}


def validate_refs(repo_root: str | Path, refs: list[str]) -> list[str]:
    repo = Path(repo_root).resolve()
    cleaned: list[str] = []
    for ref in refs:
        if not ref:
            continue
        path = (repo / ref).resolve()
        try:
            rel = path.relative_to(repo).as_posix()
        except ValueError as exc:
            raise UnsafePathError(f"memory ref escapes repo: {ref}") from exc
        if not path.exists():
            raise UnsafePathError(f"memory ref does not exist: {ref}")
        cleaned.append(rel)
    return cleaned


def remember(
    repo_root: str | Path,
    text: str,
    *,
    mem_type: str,
    refs: list[str],
    agent: str,
    store: Store,
    embedder,
    memories_dir: str | Path,
) -> dict:
    if mem_type not in ALLOWED_TYPES:
        raise ValueError(f"unsupported memory type: {mem_type}")
    if not text.strip():
        raise ValueError("memory text is required")
    if contains_secret(text):
        raise ValueError("memory text appears to contain a secret; refusing to remember")
    cleaned_refs = validate_refs(repo_root, refs)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    mem_id = hashlib.sha256(f"{ts}:{agent}:{text}".encode("utf-8")).hexdigest()[:16]
    record = {"id": mem_id, "ts": ts, "agent": agent, "type": mem_type, "refs": cleaned_refs, "text": text}
    mdir = Path(memories_dir)
    mdir.mkdir(parents=True, exist_ok=True)
    month_file = mdir / f"{ts[:7]}.jsonl"
    with month_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True) + "\n")
    # SEC-CORTEX-013 (v9.3.4): apply the same injection-pattern detection that
    # chunk_file uses so prompt-injection text is stored with suspect=True even
    # when it arrives via the remember() path (not only via the file-ingest path).
    # INJECTION_PATTERNS is the single shared list imported from ingest — no
    # regex duplication.
    _is_suspect = any(pattern.search(text) for pattern in INJECTION_PATTERNS)
    # WI-MEM-001 (SEC-CORTEX-MEM-001): use per-memory unique source_path so that
    # the v2 UNIQUE(storage_key, line_start) constraint does not collapse all
    # same-month memories to a single row.  The monthly bucket key (ts[:7])
    # was the root cause of silent overwrite on v2/v3/v4 brains.
    chunk = Chunk(
        id=f"memory:{mem_id}",
        source_path=f"memory:{mem_id}",
        source_type="memory",
        line_start=1,
        line_end=1,
        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        recorded_date=ts,
        text=text,
        trust="untrusted",
        suspect=_is_suspect,
        mem_type=mem_type,
        agent=agent,
        refs=cleaned_refs,
    )
    store.upsert([(chunk, embedder.embed(text))])
    return record
