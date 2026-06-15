"""Resolve external Cortex data locations.

This module is the single source of truth for live Cortex data paths.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path
import warnings

from .errors import UnsafePathError


_SYNC_TOKENS = ("onedrive", "dropbox", "google drive", "icloud")


_INSTALL_GROUP_RE = re.compile(r"[^a-z0-9._-]+")


def install_id(repo_root: str | Path) -> str:
    abspath = str(Path(repo_root).resolve()).lower()
    return hashlib.sha256(abspath.encode("utf-8")).hexdigest()[:12]


def _sanitize_group(raw: str) -> str:
    """Normalize an install-group label to a safe, portable directory name.

    The allowed-char class keeps '.', so a label of "." or ".." (or any all-dot
    label) would otherwise survive and let data_dir() resolve OUTSIDE the intended
    `.../dzp-cortex/<segment>` boundary (path traversal). Reject those explicitly.
    """
    cleaned = _INSTALL_GROUP_RE.sub("-", raw.strip().lower()).strip("-").strip(".")
    cleaned = cleaned[:64]
    if not cleaned or set(cleaned) <= {"."}:
        return ""
    return cleaned


def resolve_install_segment(repo_root: str | Path, config: dict | None = None) -> str:
    """
    Return the directory segment used under <os-data-root>/dzp-cortex/<segment>.

    BUG-CORTEX-001 (v9.3.0): first-class shared-brain mechanism for parent +
    nested-submodule installs. By default each repo keys on
    sha256(repo_abspath)[:12], so a parent and a nested submodule each get a
    SEPARATE brain. Setting an `install_group` (config key `install_group:` or the
    env var DZP_CORTEX_INSTALL_GROUP) to the SAME plain label in two+ installs makes
    them resolve to the SAME data dir - WITHOUT committing an absolute machine path
    (the prior only-lever, which leaked a username/path and broke portability).

    Precedence: env DZP_CORTEX_INSTALL_GROUP > config['install_group'] > per-repo hash.
    """
    config = config or {}
    group = os.environ.get("DZP_CORTEX_INSTALL_GROUP") or str(config.get("install_group") or "")
    sanitized = _sanitize_group(group)
    if sanitized:
        return sanitized
    return install_id(repo_root)


def index_scope(repo_root: str | Path, config: dict | None = None) -> str:
    """
    Storage namespace for a SHARED brain (BUG-CORTEX-005, v9.3.0).

    Returns "" (NO namespacing - byte-identical legacy behavior, no DB migration)
    UNLESS this install opts into a shared store via `install_group` /
    DZP_CORTEX_INSTALL_GROUP, or `shared_index: true` in brain.config.yaml. When a
    store is shared across 2+ installs, source keys MUST be install-scoped or files
    with the same relative path collide: `delete_by_source(rel)` + the source_state
    PRIMARY KEY would let one install's protected docs (dev-notes.md,
    security-review.md, domain.record.md) clobber another's. When sharing is on we
    return the per-repo install_id so each install occupies a distinct namespace and
    a true union of all installs' memory is possible.
    """
    config = config or {}
    group = os.environ.get("DZP_CORTEX_INSTALL_GROUP") or str(config.get("install_group") or "")
    shared = bool(_sanitize_group(group)) or bool(config.get("shared_index"))
    return install_id(repo_root) if shared else ""


def _os_data_root() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base)


def _looks_like_unc(raw: str) -> bool:
    return raw.startswith("\\\\") or bool(re.match(r"^//[^/]+/[^/]+", raw))


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_data_dir(path: Path, repo_root: str | Path, *, allow_unsafe: bool = False) -> None:
    repo = Path(repo_root).resolve()
    resolved = path.resolve()
    raw = str(path)
    lowered = str(resolved).lower()
    reasons: list[str] = []

    if _is_relative_to(resolved, repo):
        reasons.append("inside repository")
    if any(token in lowered for token in _SYNC_TOKENS):
        reasons.append("inside synced folder")
    if _looks_like_unc(raw) or _looks_like_unc(str(resolved)):
        reasons.append("network share")

    if reasons:
        if not allow_unsafe:
            # BUG-CORTEX-002 (v9.3.0): surface the fix, not just the rejection.
            # The common trigger is a project living under OneDrive/Dropbox/etc.,
            # where the only valid persistent location is an absolute OS data dir.
            hint = (
                "Cortex data must live OUTSIDE the repo and OUTSIDE synced/network "
                "folders. Fix: set DZP_CORTEX_DATA_DIR (or 'data_dir:' in "
                "brain.config.yaml) to an absolute OS path, e.g. "
                "%LOCALAPPDATA%\\dzp-cortex\\<id> on Windows or "
                "~/.local/share/dzp-cortex/<id> on macOS/Linux. The built-in default "
                "(unset data_dir) already resolves there automatically. To share one "
                "brain across nested installs without an absolute machine path, set "
                "'install_group:' / DZP_CORTEX_INSTALL_GROUP instead (see brain/README.md)."
            )
            raise UnsafePathError(
                f"Unsafe Cortex data_dir rejected: {resolved} ({', '.join(reasons)}).\n{hint}"
            )
        warnings.warn(f"Unsafe Cortex data_dir allowed by explicit override: {resolved} ({', '.join(reasons)})")


def data_dir(repo_root: str | Path, config: dict | None = None, *, allow_unsafe: bool = False) -> Path:
    config = config or {}
    override = str(config.get("data_dir") or "").strip()
    if override:
        d = Path(override).expanduser()
        # A4: anchor relative overrides to repo_root (paths.py:75).
        # Without this, a relative path resolves against CWD which changes
        # depending on how/where the CLI is invoked, producing different
        # data directories for the same repo.
        if not d.is_absolute():
            d = Path(repo_root).resolve() / d
    else:
        # BUG-CORTEX-001 (v9.3.0): use the resolved install segment, which honors
        # an `install_group` shared label (env/config) before falling back to the
        # per-repo hash. This is the portable, no-absolute-path shared-brain path.
        d = _os_data_root() / "dzp-cortex" / resolve_install_segment(repo_root, config)

    validate_data_dir(d, repo_root, allow_unsafe=allow_unsafe)
    d = d.resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path(repo_root: str | Path, config: dict | None = None, *, allow_unsafe: bool = False) -> Path:
    return data_dir(repo_root, config, allow_unsafe=allow_unsafe) / "brain.db"


def memories_dir(repo_root: str | Path, config: dict | None = None, *, allow_unsafe: bool = False) -> Path:
    d = data_dir(repo_root, config, allow_unsafe=allow_unsafe) / "memories"
    d.mkdir(parents=True, exist_ok=True)
    return d


def model_cache(repo_root: str | Path, config: dict | None = None, *, allow_unsafe: bool = False) -> Path:
    d = data_dir(repo_root, config, allow_unsafe=allow_unsafe) / "model-cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def index_log(repo_root: str | Path, config: dict | None = None, *, allow_unsafe: bool = False) -> Path:
    return data_dir(repo_root, config, allow_unsafe=allow_unsafe) / "index.log"
