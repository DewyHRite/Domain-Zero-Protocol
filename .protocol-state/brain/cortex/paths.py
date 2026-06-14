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


def install_id(repo_root: str | Path) -> str:
    abspath = str(Path(repo_root).resolve()).lower()
    return hashlib.sha256(abspath.encode("utf-8")).hexdigest()[:12]


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
            raise UnsafePathError(f"Unsafe Cortex data_dir rejected: {resolved} ({', '.join(reasons)})")
        warnings.warn(f"Unsafe Cortex data_dir allowed by explicit override: {resolved} ({', '.join(reasons)})")


def data_dir(repo_root: str | Path, config: dict | None = None, *, allow_unsafe: bool = False) -> Path:
    config = config or {}
    override = str(config.get("data_dir") or "").strip()
    if override:
        d = Path(override).expanduser()
    else:
        d = _os_data_root() / "dzp-cortex" / install_id(repo_root)

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
