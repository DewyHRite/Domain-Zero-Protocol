"""BUG-CORTEX-PROLIF — orphan install-dir classifier.

``classify_orphans(data_root, current_install_id)``
  Yields one dict per candidate dir under *data_root* (direct children only).

Safety invariants enforced here (referenced by tests):
  INV-2  ``*-shared`` dirs (contain '-shared' or match a known-shared pattern) —
         conservatively: any dir whose name is NOT a pure 12-hex hash is SKIPPED.
         (Non-hash dirs include shared labels like ``<project>-shared``, e.g. ``acme-shared``.)
  INV-3  The *current_install_id* dir is SKIPPED.
  INV-4  A hash dir whose ``brain.db`` is >= ORPHAN_DB_THRESHOLD_BYTES OR has > 0
         rows in ``content_refs`` is NOT an orphan.
  INV-5  A hash dir whose ``brain.db`` ``cortex_installs`` ledger has ANY entry
         (regardless of install_id) other than only the dir's own name is SKIPPED
         as a potential foreign/shared brain.  Actually: if the ledger is non-empty
         AND the sole install_id listed is NOT this dir's own name, it's foreign.
         The conservative rule: if ANY ledger row exists, we check:
           - if there's exactly one row and its install_id == dir_name → still might
             be a stub left behind (OK to delete).
           - if any row has install_id != dir_name → foreign, skip.
  INV-6  Only 12-hex-char dirs (``^[0-9a-f]{12}$``) are inspected.
  INV-7  If brain.db exists but cannot be opened/queried → treat as NON-orphan
         (fail-safe: do NOT delete what we cannot inspect).

The module is intentionally side-effect-free: it never deletes anything.
Deletion is performed by the CLI layer (brain.py ``_reset_orphans``).
"""

from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

#: Regex that matches the 12-hex install-id format produced by paths.install_id().
HASH_DIR_RE = re.compile(r"^[0-9a-f]{12}$")

#: Conservative "stub" threshold: brain.db files below this size are inspected
#: further (content row check). Files at or above this size are treated as having
#: real data (INV-4 fast path).
ORPHAN_DB_THRESHOLD_BYTES: int = 512 * 1024  # 512 KB


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _dir_size_bytes(d: Path) -> int:
    """Sum of all file sizes under *d*, excluding model-cache and symlink targets.

    Uses lstat() to avoid following symlinks.
    """
    import stat as _stat
    total = 0
    try:
        for child in d.rglob("*"):
            if child.name == "model-cache" or "model-cache" in child.parts:
                continue
            try:
                st = child.lstat()
                if _stat.S_ISREG(st.st_mode):
                    total += st.st_size
            except OSError:
                pass
    except OSError:
        pass
    return total


def _latest_mtime(d: Path) -> float | None:
    """Return latest mtime under *d*, excluding model-cache; None means unreadable."""
    latest: float | None = None
    try:
        paths = [d, *list(d.rglob("*"))]
    except OSError:
        return None
    for child in paths:
        if child.name == "model-cache" or "model-cache" in child.parts:
            continue
        try:
            st = child.lstat()
        except OSError:
            return None
        latest = st.st_mtime if latest is None else max(latest, st.st_mtime)
    return latest


def _has_nonempty_memories(d: Path) -> tuple[bool, str]:
    """Return True when a memories/ subtree contains any file or cannot be read."""
    memories = d / "memories"
    if not memories.exists():
        return False, ""
    try:
        if not memories.is_dir() or memories.is_symlink():
            return True, "memories path is not a plain directory"
        for child in memories.rglob("*"):
            try:
                st = child.lstat()
            except OSError as exc:
                return True, f"memories unreadable: {exc}"
            import stat as _stat
            if _stat.S_ISREG(st.st_mode):
                return True, "has memories files"
        return False, ""
    except OSError as exc:
        return True, f"memories unreadable: {exc}"


def _is_stub_db(db_path: Path) -> tuple[bool, str]:
    """Return (is_stub, reason) for a brain.db file.

    ``is_stub=True`` means the DB is empty (no content rows), safe to GC.
    ``is_stub=False`` means it has real data or is unreadable (fail-safe).
    ``reason`` is a human-readable explanation.

    INV-7: any exception → (False, 'unreadable: <msg>')
    INV-4: size >= threshold fast path → (False, 'size >= threshold')
    INV-4: content_refs rows > 0 → (False, 'has N content rows')
    """
    if not db_path.exists():
        # No brain.db at all → treat as stub (empty dir)
        return True, "no brain.db"

    # INV-4 fast path: large file → real data, skip inspection
    try:
        size = db_path.stat().st_size
    except OSError as exc:
        return False, f"unreadable: {exc}"

    if size >= ORPHAN_DB_THRESHOLD_BYTES:
        return False, f"size {size} >= threshold {ORPHAN_DB_THRESHOLD_BYTES}"

    # Open and query — INV-7: any exception → non-orphan
    try:
        conn = sqlite3.connect(str(db_path), timeout=1.0)
        try:
            counts: list[str] = []
            for table, label in (
                ("content_refs", "content rows"),
                ("cortex_entities", "entity rows"),
                ("cortex_edges", "edge rows"),
            ):
                has_table = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()
                if has_table is None:
                    return False, f"missing {table} table"
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if count > 0:
                    return False, f"has {count} {label}"
                counts.append(f"0 {label}")

            return True, ", ".join(counts)
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        # INV-7: unreadable → fail-safe, never delete
        return False, f"unreadable: {exc}"


def _has_foreign_ledger(db_path: Path, dir_name: str) -> tuple[bool, str]:
    """Return (has_foreign, reason).

    INV-5: if cortex_installs has any row whose install_id != dir_name,
    the DB is considered foreign and must not be deleted.

    Returns (True, reason) when the dir is foreign/shared.
    Returns (False, "") when it is safe (ledger empty, or sole entry matches dir_name).

    INV-7 applies here too: on any error → return (True, 'unreadable: ...') to fail-safe.
    """
    if not db_path.exists():
        return False, ""

    try:
        conn = sqlite3.connect(str(db_path), timeout=1.0)
        try:
            has_table = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cortex_installs'"
            ).fetchone()
            if has_table is None:
                return False, ""

            rows = conn.execute(
                "SELECT install_id FROM cortex_installs"
            ).fetchall()

            if not rows:
                return False, ""

            install_ids = [r[0] for r in rows]
            foreign = [iid for iid in install_ids if iid != dir_name]
            if foreign:
                return True, f"foreign ledger entries: {foreign}"
            # Only our own dir_name is in the ledger — still a stub, not foreign
            return False, ""
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        # INV-7: unreadable → fail-safe
        return True, f"unreadable ledger: {exc}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_orphans(
    data_root: Path,
    current_install_id: str,
    *,
    older_than_days: int = 30,
) -> list[dict]:
    """Classify all candidate dirs under *data_root* and return a list of dicts.

    Only direct children of *data_root* are inspected (no recursion, no symlink
    traversal outside the root).

    Each result dict has:
        name         (str)   directory name
        path         (Path)  full path
        is_orphan    (bool)  True → safe-to-delete orphan candidate
        reason       (str)   human-readable classification reason
        size_bytes   (int)   total byte size of the directory

    Dirs that are protected (shared, current, non-hash) are NOT included in the
    result list at all — only hash-named dirs are returned (is_orphan=True or False).
    """
    results: list[dict] = []

    try:
        children = list(data_root.iterdir())
    except OSError:
        return results

    for child in children:
        # Only look at directories; skip files (e.g. index.log) and symlinks.
        # Use lstat to avoid following symlinks (symlink to a dir is not traversed).
        try:
            st = child.lstat()
        except OSError:
            continue
        import stat as _stat
        if not _stat.S_ISDIR(st.st_mode):
            continue

        name = child.name

        # INV-6: only 12-hex dirs are classified
        if not HASH_DIR_RE.fullmatch(name):
            continue  # shared labels, misc dirs — not in results at all

        # INV-3: skip current install
        if name == current_install_id:
            continue

        size_bytes = _dir_size_bytes(child)
        db_path = child / "brain.db"

        latest_mtime = _latest_mtime(child)
        if latest_mtime is None:
            results.append({
                "name": name,
                "path": child,
                "is_orphan": False,
                "reason": "mtime unreadable",
                "size_bytes": size_bytes,
            })
            continue
        if older_than_days > 0:
            age_seconds = time.time() - latest_mtime
            min_age_seconds = older_than_days * 86400
            if age_seconds < min_age_seconds:
                results.append({
                    "name": name,
                    "path": child,
                    "is_orphan": False,
                    "reason": f"recently modified (< {older_than_days} days)",
                    "size_bytes": size_bytes,
                })
                continue

        # INV-5: check for foreign ledger entries first (fail-safe: if foreign → not orphan)
        is_foreign, foreign_reason = _has_foreign_ledger(db_path, name)
        if is_foreign:
            results.append({
                "name": name,
                "path": child,
                "is_orphan": False,
                "reason": foreign_reason,
                "size_bytes": size_bytes,
            })
            continue

        has_memories, memories_reason = _has_nonempty_memories(child)
        if has_memories:
            results.append({
                "name": name,
                "path": child,
                "is_orphan": False,
                "reason": memories_reason,
                "size_bytes": size_bytes,
            })
            continue

        if size_bytes >= ORPHAN_DB_THRESHOLD_BYTES:
            results.append({
                "name": name,
                "path": child,
                "is_orphan": False,
                "reason": f"recursive size {size_bytes} >= threshold {ORPHAN_DB_THRESHOLD_BYTES}",
                "size_bytes": size_bytes,
            })
            continue

        # INV-4 + INV-7: stub check
        is_stub, stub_reason = _is_stub_db(db_path)
        results.append({
            "name": name,
            "path": child,
            "is_orphan": is_stub,
            "reason": stub_reason,
            "size_bytes": size_bytes,
        })

    return results
