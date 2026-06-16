"""Load and validate Cortex configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import os

import yaml

from . import paths


DEFAULT_CONFIG: dict[str, Any] = {
    "model": "BAAI/bge-small-en-v1.5",
    "top_k": 5,
    "max_file_bytes": 6_000_000,  # SEC-CORTEX-003 (v9.3.2): config-driven per-file cap
    "include_folders": ["protocol", "docs"],
    "include_files": [
        "CLAUDE.md",
        "protocol/CLAUDE.md",
        "AI_INSTRUCTIONS.md",
        "README.md",
        ".protocol-state/session_monitor.py",
        ".protocol-state/project_state_manager.py",
        ".protocol-state/troubleshooting_tracker.py",
    ],
    "include_protected": [
        ".protocol-state/dev-notes.md",
        ".protocol-state/security-review.md",
        ".dzp-domain/domain.record.md",
    ],
    "include_reports": [],
    "include_code": ["scripts"],
    "exclude_tokens": [
        "backups",
        "__pycache__",
        "node_modules",
        ".env",
        ".dzp-killswitch",
        "brain.db",
        "cortex-snapshot.md",
        "project-state.json",
        "troubleshooting-history.json",
        ".protocol-state/internal-docs",
        ".protocol-state/stress_tests",
        ".protocol-state/system-update-framework",
        "internal-docs",
        "docs/superpowers",
    ],
    "chunk": {"md_max_chars": 1200, "code_max_chars": 1500, "overlap": 120},
    "index": {"batch_size": 64},
}


def config_path(repo_root: str | Path) -> Path:
    return Path(repo_root) / ".protocol-state" / "brain" / "brain.config.yaml"


def load(repo_root: str | Path, *, allow_unsafe: bool = False) -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    path = config_path(repo_root)
    if path.exists():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError("brain.config.yaml must contain a mapping")
        cfg = _deep_merge(cfg, loaded)

    env_data_dir = os.environ.get("DZP_CORTEX_DATA_DIR")
    if env_data_dir:
        cfg["data_dir"] = env_data_dir

    validate(cfg, repo_root, allow_unsafe=allow_unsafe)
    return cfg


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def validate(cfg: dict[str, Any], repo_root: str | Path, *, allow_unsafe: bool = False) -> None:
    if not isinstance(cfg.get("model"), str) or not cfg["model"].strip():
        raise ValueError("model must be a non-empty string")
    if int(cfg.get("top_k", 0)) <= 0:
        raise ValueError("top_k must be positive")
    # SEC-CORTEX-004 (v9.3.2): reject non-positive / non-int / bool max_file_bytes.
    # bool is a subclass of int, so it must be rejected explicitly.
    mfb = cfg.get("max_file_bytes", DEFAULT_CONFIG["max_file_bytes"])
    if isinstance(mfb, bool) or not isinstance(mfb, int) or mfb <= 0:
        raise ValueError("max_file_bytes must be a positive integer")
    for key in ("include_folders", "include_files", "include_protected", "include_reports", "include_code", "exclude_tokens"):
        if not isinstance(cfg.get(key), list):
            raise ValueError(f"{key} must be a list")
    chunk = cfg.get("chunk")
    if not isinstance(chunk, dict):
        raise ValueError("chunk must be a mapping")
    index = cfg.get("index")
    if not isinstance(index, dict) or int(index.get("batch_size", 0)) <= 0:
        raise ValueError("index.batch_size must be positive")
    if cfg.get("data_dir"):
        paths.validate_data_dir(Path(str(cfg["data_dir"])), repo_root, allow_unsafe=allow_unsafe)


def is_stub_model(cfg: dict[str, Any]) -> bool:
    return str(cfg.get("model", "")).upper() == "STUB"
