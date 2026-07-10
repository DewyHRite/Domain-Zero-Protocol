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

SEC-TOJI-102 (mechanical fabrication tripwire for the Toji audit-log stub):
  Toji (protocol/toji.agent.md Section 1.3.4) appends a standardized one-line
  "[TOJI AUDIT LOG]" stub to dev-notes.md and security-review.md after writing
  a full report to audits/<filename>.md. That tripwire was behavioral only —
  nothing verified the referenced report actually existed, so a forged stub
  was trivial to commit. This guard mechanizes it: for every NEWLY-ADDED
  staged line (never pre-existing/committed content) matching the
  "[TOJI AUDIT LOG]" format in dev-notes.md or security-review.md, the
  "full report: <path>" reference must resolve to a real file (on disk,
  staged in the index, or tracked in HEAD) or the commit is blocked.

  Override (legit exceptional case): set DZP_ALLOW_TOJI_STUB_UNVERIFIED=1.
  Separate from DZP_ALLOW_PROTECTED_REWRITE because this checks report
  *existence*, not the append-only byte-prefix invariant. The bypass is
  always printed to stderr — never silent.

Exit codes: 0 = clean (or overridden / disabled), 1 = violation(s) blocking commit.
"""

from __future__ import annotations

import os
import re
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

    # M2 (CodeRabbit PR#99): validate that `paths` is a list of non-empty strings.
    # A scalar (str/int/None/bool) must NOT be iterated — a string would be walked
    # character-by-character, silently replacing real paths with single-char entries
    # and effectively disabling enforcement. A non-list scalar crashes on iteration.
    # Any element that is not a str also triggers the fallback (fail-SAFE).
    # When validation fails, fall back to PROTECTED_DOCS (never fail-open).
    raw_paths = block.get("paths")
    if isinstance(raw_paths, (list, tuple)):
        valid = True
        parsed = []
        for p in raw_paths:
            if not isinstance(p, str):
                valid = False
                break
            s = p.strip()
            if s:
                parsed.append(s)
        paths: tuple[str, ...] = tuple(parsed) if valid else PROTECTED_DOCS
    else:
        # scalar (str, int, None, bool, …) — fall back to hardcoded constants
        paths = PROTECTED_DOCS

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
# SEC-TOJI-102: Toji "[TOJI AUDIT LOG]" stub existence check
# ---------------------------------------------------------------------------

# Only these two protected records receive the standardized Toji stub check
# (per protocol/toji.agent.md Section 1.3.4 / CLAUDE.md). domain.record.md
# is out of scope for THIS mechanical check by design.
TOJI_STUB_SCOPE: tuple[str, ...] = (
    ".protocol-state/dev-notes.md",
    ".protocol-state/security-review.md",
)

TOJI_STUB_MARKER = "[TOJI AUDIT LOG]"
TOJI_STUB_OVERRIDE_ENV = "DZP_ALLOW_TOJI_STUB_UNVERIFIED"

# Matches the "full report: <path>" field in the standardized stub, e.g.:
#   ... · full report: audits/2026-07-09-toji-full-se-qa.md · —Toji ...
_TOJI_REPORT_RE = re.compile(r"full report:\s*(\S+)")


def _added_lines(head: Optional[bytes], staged: bytes) -> list[str]:
    """Return the lines newly present in `staged` that are not part of `head`.

    Normalizes CRLF (consistent with is_append_only) before diffing. When the
    normalized `head` is a prefix of normalized `staged` (the expected,
    append-only case), this returns exactly the appended tail. If it is NOT a
    prefix (a mid-file rewrite — already a separate append-only violation),
    this falls back to scanning the full staged content so a forged stub
    is never silently missed; it does not raise.
    """
    staged_norm = _normalize(staged)
    head_norm = _normalize(head) if head is not None else b""
    if staged_norm.startswith(head_norm):
        tail = staged_norm[len(head_norm):]
    else:
        tail = staged_norm
    return tail.decode("utf-8", errors="replace").splitlines()


def _report_ref_exists(repo_root: Path, rel_path: str) -> bool:
    """True if `rel_path` exists on disk, is staged in the index, or is tracked in HEAD."""
    rel_path = rel_path.strip()
    if not rel_path:
        return False
    try:
        if (repo_root / rel_path).is_file():
            return True
    except OSError:
        pass
    if staged_blob(repo_root, rel_path) is not None:
        return True
    if head_blob(repo_root, rel_path) is not None:
        return True
    return False


def find_toji_stub_violations(
    repo_root: Path,
    paths: tuple[str, ...] = TOJI_STUB_SCOPE,
) -> list[str]:
    """Return violation messages for newly-staged "[TOJI AUDIT LOG]" stubs whose
    referenced report does not exist.

    Only NEWLY-ADDED staged lines are inspected (see _added_lines) — pre-existing
    committed content, including old free-form Toji entries predating the
    standardized stub format, is never flagged. Fails soft (skips) on a stub-like
    line it cannot parse a report path from; fails CLOSED (reports a violation)
    when a report path is parsed but does not resolve to a real file.
    """
    violations: list[str] = []
    for path in paths:
        staged = staged_blob(repo_root, path)
        if staged is None:
            continue  # nothing staged for this file
        head = head_blob(repo_root, path)
        for line in _added_lines(head, staged):
            if TOJI_STUB_MARKER not in line:
                continue
            match = _TOJI_REPORT_RE.search(line)
            if not match:
                # Fail-soft: looks stub-like but unparseable — do not block on ambiguity.
                continue
            report_ref = match.group(1)
            if not _report_ref_exists(repo_root, report_ref):
                violations.append(
                    f"{path}: [TOJI AUDIT LOG] stub references a report that does not "
                    f"exist: '{report_ref}' (offending line: {line.strip()!r})"
                )
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

    exit_code = 0

    # --- Check 1: append-only byte-prefix invariant ------------------------
    violations = find_violations(repo_root, protected=protected)
    if violations:
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
        else:
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
            exit_code = 1

    # --- Check 2 (SEC-TOJI-102): "[TOJI AUDIT LOG]" stub report existence --
    toji_violations = find_toji_stub_violations(repo_root)
    if toji_violations:
        toji_override = os.environ.get(TOJI_STUB_OVERRIDE_ENV) == "1"
        toji_bullet = "\n".join(f"    - {v}" for v in toji_violations)

        if toji_override:
            print(
                "[toji-stub-guard] OVERRIDE ACTIVE "
                f"({TOJI_STUB_OVERRIDE_ENV}=1) - allowing unverifiable [TOJI AUDIT LOG] stub(s):\n"
                f"{toji_bullet}\n"
                "    Ensure this is an authorized exception (e.g. report published separately).\n"
                f"    Scope this variable to the single commit invocation "
                f"(e.g. `{TOJI_STUB_OVERRIDE_ENV}=1 git commit ...`) — "
                "do not export it globally in CI.",
                file=sys.stderr,
            )
        else:
            print(
                "[toji-stub-guard] COMMIT BLOCKED - a newly-added [TOJI AUDIT LOG] stub references\n"
                "   a report file that does not exist (fabrication tripwire, SEC-TOJI-102):\n"
                f"{toji_bullet}\n\n"
                "   Per protocol/toji.agent.md Section 1.3.4, a stub must never be committed\n"
                "   without a real, written report at the stated audits/ path.\n"
                "   Fix: write the missing report, or correct the stub's report path, then re-stage.\n\n"
                f"   Authorized exception? Re-run with {TOJI_STUB_OVERRIDE_ENV}=1.",
                file=sys.stderr,
            )
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
