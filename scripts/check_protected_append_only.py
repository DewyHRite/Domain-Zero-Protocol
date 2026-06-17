#!/usr/bin/env python3
"""
Protected-document APPEND-ONLY enforcement guard (FEAT-GUARD-001).

CLAUDE.md classifies three files as PROJECT DOCUMENTS that are NEVER overwritten —
only appended to (history is permanent project memory):

  - .protocol-state/dev-notes.md        (Yuuji implementation log)
  - .protocol-state/security-review.md  (Megumi security findings)
  - .dzp-domain/domain.record.md        (Gojo + Sukuna strategic notes)

That rule was procedural only. On 2026-06-16 a full-file rewrite silently condensed
~366 lines of security-review.md history (recoverable only because it was uncommitted).
This guard makes the invariant MECHANICAL at pre-commit time: the committed (HEAD)
content of each protected doc must be a byte-PREFIX of the staged content.

  - pure append            -> OK (HEAD content preserved as prefix)
  - unchanged / equal      -> OK
  - first creation (no HEAD)-> OK
  - mid-file change        -> BLOCK
  - net deletion / shrink  -> BLOCK

Override (legit rotation / authorized restore): set DZP_ALLOW_PROTECTED_REWRITE=1.
The override is loud and intentional — it warns and allows.

Config surface (FEAT-GUARD-001 Phase 1):
  Add a `protected_documents` block to protocol.config.yaml to customize:
    protected_documents:
      enabled: true                         # false = no-op (exit 0)
      paths:
        - .protocol-state/dev-notes.md
        - .protocol-state/security-review.md
        - .dzp-domain/domain.record.md
      override_env: DZP_ALLOW_PROTECTED_REWRITE

  If the block is absent, the guard falls back to the hardcoded PROTECTED_DOCS
  constant.  On any config error the guard also falls back to hardcoded defaults
  (fail-safe, never fail-open).

SEC-GUARD-002 (CRLF normalization):
  The byte-prefix check normalizes both sides by stripping \\r before comparison
  so a working-tree CRLF append (repos lacking text=auto) never false-positives.

Exit codes: 0 = clean (or overridden / disabled), 1 = violation(s) blocking commit.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

PROTECTED_DOCS: tuple[str, ...] = (
    ".protocol-state/dev-notes.md",
    ".protocol-state/security-review.md",
    ".dzp-domain/domain.record.md",
)

OVERRIDE_ENV = "DZP_ALLOW_PROTECTED_REWRITE"

# SEC-GUARD-004: maximum config file size before _load_config falls back to
# hardcoded constants (fail-SAFE).  protocol.config.yaml is a small YAML file;
# 1 MB is a generous upper bound that no legitimate config should exceed.
_MAX_CONFIG_BYTES = 1_000_000


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def _load_config(config_path: Path) -> Optional[dict]:
    """Load and return the `protected_documents` section from config_path.

    Returns None if the file does not exist, does not have the key, or any
    error occurs — caller falls back to hardcoded constants.

    SEC-GUARD-004: if the file on disk exceeds _MAX_CONFIG_BYTES, skip loading
    and return None (fail-SAFE fallback).  protocol.config.yaml is a small YAML
    file; a multi-MB payload is never legitimate and should not be read.
    """
    if not config_path.is_file():
        return None
    # SEC-GUARD-004: size guard — reject oversized configs before reading
    try:
        if config_path.stat().st_size > _MAX_CONFIG_BYTES:
            return None
    except OSError:
        return None
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None
    try:
        with config_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        block = raw.get("protected_documents")
        if not isinstance(block, dict):
            return None
        return block
    except Exception:  # noqa: BLE001 — any YAML/IO error -> fall back
        return None


def _resolve_config_path(repo_root: Path, config_path: Optional[Path]) -> Path:
    """Return the effective config path: explicit arg > repo_root/protocol.config.yaml."""
    if config_path is not None:
        return config_path
    return repo_root / "protocol.config.yaml"


def _effective_settings(
    repo_root: Path,
    config_path: Optional[Path],
) -> tuple[bool, tuple[str, ...], str]:
    """Return (enabled, protected_paths, override_env_name) from config or hardcoded fallback."""
    cfg_file = _resolve_config_path(repo_root, config_path)
    block = _load_config(cfg_file)

    if block is None:
        # Fall back to hardcoded constants — fail-safe
        return True, PROTECTED_DOCS, OVERRIDE_ENV

    enabled: bool = bool(block.get("enabled", True))
    raw_paths = block.get("paths") or []
    paths: tuple[str, ...] = tuple(str(p).strip() for p in raw_paths if p)
    override_env: str = str(block.get("override_env") or OVERRIDE_ENV)

    # If config provided no paths, fall back to hardcoded paths (but respect enabled flag)
    if not paths:
        paths = PROTECTED_DOCS

    return enabled, paths, override_env


# ---------------------------------------------------------------------------
# Core comparison logic (SEC-GUARD-002: CRLF-normalizing prefix check)
# ---------------------------------------------------------------------------


def _normalize(data: bytes) -> bytes:
    """Strip all \\r bytes for cross-platform line-ending normalization."""
    return data.replace(b"\r", b"")


def is_append_only(old: bytes, new: bytes) -> bool:
    """True iff `old` is a normalized byte-prefix of `new` (pure append; equal counts).

    SEC-GUARD-002: both sides are normalized (\\r stripped) before comparison so a
    working-tree CRLF append to a LF-HEAD doc is not falsely reported as a violation.
    """
    return _normalize(new).startswith(_normalize(old))


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _git_show(repo_root: Path, ref_path: str) -> Optional[bytes]:
    """Return the raw bytes of `git show <ref_path>`, or None if it does not exist."""
    proc = subprocess.run(
        ["git", "show", ref_path],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def head_blob(repo_root: Path, path: str) -> Optional[bytes]:
    """Committed (HEAD) content of `path`, or None if not tracked in HEAD."""
    return _git_show(repo_root, f"HEAD:{path}")


def staged_blob(repo_root: Path, path: str) -> Optional[bytes]:
    """Staged (index) content of `path`, or None if not present in the index."""
    return _git_show(repo_root, f":{path}")


# ---------------------------------------------------------------------------
# Violation detection
# ---------------------------------------------------------------------------


def find_violations(
    repo_root: Path,
    protected: Optional[tuple[str, ...]] = None,
    config_path: Optional[Path] = None,
) -> list[str]:
    """Return the protected paths whose staged content breaks the append-only invariant.

    When `protected` is None, paths are resolved from config_path (or hardcoded fallback).
    When `protected` is explicitly provided it is used as-is (for backward-compat / tests).

    SEC-GUARD-001: a staged deletion (git rm) is also a violation.  When
    staged_blob() returns None the file is absent from the index — either it
    was never tracked (not a violation) or it was removed via `git rm` (violation).
    We distinguish the two cases by checking HEAD: if the file existed in HEAD
    but is now gone from the index it was deleted, which breaks append-only.
    """
    if protected is None:
        _, protected, _ = _effective_settings(repo_root, config_path)

    violations: list[str] = []
    for path in protected:
        staged = staged_blob(repo_root, path)
        if staged is None:
            # File absent from index: check whether it existed in HEAD.
            head = head_blob(repo_root, path)
            if head is not None:
                # File was tracked in HEAD but is now removed from the index
                # (staged deletion via `git rm`) — this breaks append-only.
                violations.append(path)
            # else: never tracked in HEAD either -> first-absence, not a violation
            continue
        head = head_blob(repo_root, path)
        if head is None:
            continue  # first creation -> allowed
        if not is_append_only(head, staged):
            violations.append(path)
    return violations


# ---------------------------------------------------------------------------
# Repo detection
# ---------------------------------------------------------------------------


def _repo_toplevel() -> Optional[Path]:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return Path(proc.stdout.strip())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(
    argv: Optional[list[str]] = None,
    repo_root: Optional[Path] = None,
    config_path: Optional[Path] = None,
) -> int:
    if repo_root is None:
        repo_root = _repo_toplevel()
        if repo_root is None:
            print("[protected-guard] not a git repository — skipping", file=sys.stderr)
            return 0

    # Resolve effective settings (config-driven or hardcoded fallback)
    enabled, protected, override_env = _effective_settings(repo_root, config_path)

    if not enabled:
        print(
            "[protected-guard] protected_documents.enabled=false — skipping append-only check",
            file=sys.stderr,
        )
        return 0

    violations = find_violations(repo_root, protected=protected)
    if not violations:
        return 0

    override = os.environ.get(override_env) == "1"
    bullet = "\n".join(f"    - {v}" for v in violations)

    if override:
        print(
            "[protected-guard] APPEND-ONLY OVERRIDE ACTIVE "
            f"({override_env}=1) - allowing non-append change to protected doc(s):\n"
            f"{bullet}\n"
            "    This rewrites permanent project memory. Ensure it is intentional "
            "(rotation / authorized restore).\n"
            f"    Scope this variable to the single commit invocation "
            f"(e.g. `{override_env}=1 git commit ...`) — "
            "do not export it globally in CI.",
            file=sys.stderr,
        )
        return 0

    print(
        "[protected-guard] COMMIT BLOCKED - protected document(s) are APPEND-ONLY but the\n"
        "   staged change is NOT a pure append (mid-file edit or deletion detected):\n"
        f"{bullet}\n\n"
        "   These files are permanent project memory (CLAUDE.md PROJECT DOCUMENTS PROTECTION).\n"
        "   Fix: restore the file from HEAD and re-append only your new content, e.g.:\n"
        "     git restore --staged <file> && git checkout -- <file>\n"
        "     # then append your additions to the end and re-stage\n\n"
        f"   Legit rewrite (rotation / authorized restore)? Re-run with {override_env}=1.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
