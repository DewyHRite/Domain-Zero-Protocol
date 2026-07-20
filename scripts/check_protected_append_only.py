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

Toji AI-001 (full stub grammar validation, Sukuna Block B5, v9.10.1):
  SEC-TOJI-102 above (and the AI-001 scoped fix that normalizes a backticked
  report path) only ever validated the "full report: <path>" field's
  EXISTENCE. Toji's own AI-001 finding (`audits/2026-07-18-toji-dzp-9-10-0-
  audit.md`) observed that the guard "does not validate the scope, counts,
  signature suffix, duplicate audit identifier, extension agreement, or full
  stub grammar" -- demonstrated by the two REAL committed stubs whose
  `scope:` value ("v9.10.0-idgov-full-audit (design+impl+review+go-live)")
  contains dots, spaces, parentheses, and a plus sign despite the mandatory
  `[a-z0-9-]+` safe-slug rule (protocol/toji.agent.md Section 1.3.4).

  This guard now validates every NEWLY-ADDED "[TOJI AUDIT LOG]" line against
  the FULL standardized grammar:

    > [TOJI AUDIT LOG] YYYY-MM-DD · scope: <safe-slug> · findings: N (C/H/M/L)
      · full report: <path> · —Toji (Sentinel) vX.Y.Z

  A line containing the TOJI_STUB_MARKER that does NOT match this grammar is
  now a MALFORMED STUB and BLOCKS the commit outright (fail-closed) -- this
  supersedes the prior "fails soft on parse ambiguity" behavior for a
  stub-like-but-unparseable line (AI-001's explicit recommendation: "Reject
  malformed marker lines instead of failing soft on parse ambiguity").
  A grammar-conforming stub is then further checked for:
    - a real calendar date (not just YYYY-MM-DD shape -- e.g. month 13 fails)
    - findings arithmetic: N must equal C+H+M+L
    - report path extension in _TOJI_STUB_ALLOWED_EXTENSIONS (.md/.docx, per
      Section 1.3.4: "<ext> MUST match the actual extension... md or docx")
    - report path existence (reusing the existing SEC-TOJI-102 check)
    - per-file (date, scope) uniqueness against every stub ALREADY PRESENT IN
      HEAD for that same protected file (a duplicate committed audit
      identifier is a violation), plus against other newly-added stubs in
      the SAME commit

  CRITICAL SCOPING (unchanged from SEC-TOJI-102): only NEWLY-ADDED staged
  content is ever validated -- a pre-existing, already-committed stub
  (including the two real 2026-07-18 stubs whose scope violates the
  safe-slug rule) is NEVER retroactively re-validated or re-blocked by a
  later, unrelated commit; it is permanent history. As of the P1 fix below,
  "newly-added" is now determined by an exact per-line text comparison
  against HEAD (see _existing_stub_line_identifiers), not by the
  byte-offset tail slice _added_lines() used to compute.

P1 (Megumi Tier-3 bundle review, v9.10.1): stub-marker splice bypass, FIXED.
  _added_lines() (still defined below, no longer called by
  find_toji_stub_violations) computed the newly-staged tail as a byte-OFFSET
  slice of the staged content (staged_norm[len(head_norm):]). When HEAD does
  NOT end with a trailing newline, a two-commit sequence could SPLICE a
  forged stub across the commit boundary: commit 1 appends a PARTIAL marker
  with no trailing newline (e.g. "> [TOJI AUDIT LO", not yet a complete
  "[TOJI AUDIT LOG]" substring -- nothing is flagged, commit passes clean);
  commit 2's staged bytes then complete that SAME physical line (e.g.
  "G] ... full report: <missing> ..."). The byte-offset tail computed for
  commit 2 starts MID-LINE at "G]" and never contains the literal marker
  text -- so the stub scan skipped it entirely, and a complete, well-formed-
  looking forged stub (referencing a report that does not exist) landed
  with ZERO warning.

  Fix (Megumi option (a)): find_toji_stub_violations now scans the FULL
  staged content (every line split from the whole normalized staged text,
  not just the byte-offset tail) for TOJI_STUB_MARKER lines, and exempts a
  line from re-validation ONLY when its exact (normalized) text was already
  present, byte-for-byte, as a line in HEAD -- i.e. genuinely unchanged
  history. _existing_stub_line_identifiers() is the identity function
  backing this exemption: "identity" is simply the full normalized line
  text, which works uniformly for well-formed AND malformed historical
  lines alike (no (date, scope) parsing required, so it is inherently
  robust for a malformed line that has no parseable scope field -- it
  "falls back" to the full line trivially, by construction). This is
  deliberately a DIFFERENT, coarser identity than _existing_stub_identifiers
  (date, scope) below, which remains dedicated to the semantic
  duplicate-audit-identifier check -- a NEW stub whose (date, scope) merely
  MATCHES an old one (but whose full line text differs, e.g. a different
  referenced report) is correctly NOT exempted by the per-line check and
  still surfaces as a "duplicates an existing audit identifier" violation.

  Same override: DZP_ALLOW_TOJI_STUB_UNVERIFIED=1 remains the single
  break-glass for this whole stub-guard family (existence, grammar, AND
  the splice bypass above).

Exit codes: 0 = clean (or overridden / disabled), 1 = violation(s) blocking commit.
"""

from __future__ import annotations

import datetime
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
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

# Toji AI-001 (2026-07-18, promoted from the v9.10.1 queue -- USER-reported
# recurring operational pain): _TOJI_REPORT_RE's \S+ capture has no concept
# of markdown/prose formatting, so a report path wrapped in backticks (the
# standard style for a path reference in a stub, e.g.
# "full report: `audits/2026-07-18-toji-v9.10.0-idgov-full-audit.md`")
# captures the surrounding backticks AS PART OF the path, which then never
# matches a real file and fails the existence check even though the report
# genuinely exists -- forcing DZP_ALLOW_TOJI_STUB_UNVERIFIED every time.
# This is a SCOPED fix (strip common wrapping/trailing punctuation before
# the existence check); full stub-grammar validation is deferred to
# v9.10.1 per AI-001's own recommendation. Order matters: strip matched
# wrapping characters FIRST (a trailing ')' that pairs with a leading '('
# is wrapping, not sentence punctuation), then strip trailing sentence
# punctuation that can follow a bare or already-unwrapped path.
_TOJI_PATH_WRAP_CHARS = "`'\"()[]<>"
_TOJI_PATH_TRAILING_PUNCT_RE = re.compile(r"[.,;:]+$")


def _normalize_toji_report_ref(raw: str) -> str:
    """Strip surrounding backticks/quotes/brackets and trailing sentence
    punctuation from a captured 'full report: <path>' reference before the
    existence check. Never widens what is ACCEPTED as a path (no traversal/
    absolute-path handling here -- that stays _safe_audit_rel_path()'s job);
    this only removes formatting characters a human/Toji would never intend
    as part of the filename itself.

    Applied as a small fixed-point loop (bounded, each pass strictly
    shrinks or leaves the string unchanged, so this always terminates): a
    single wrap-strip-then-punct-strip pass leaves a dangling closer behind
    for a combined case like "`path`." (backtick-wrapped, sentence-final
    period right after the closing backtick) -- wrap-strip only removes the
    OPENING backtick there (the trailing char is '.', not in the wrap set,
    so the closing backtick is untouched on that pass), then punct-strip
    removes the trailing '.', leaving a lone trailing backtick. A second
    pass cleans that up.
    """
    normalized = raw
    for _ in range(6):
        stripped = normalized.strip(_TOJI_PATH_WRAP_CHARS)
        stripped = _TOJI_PATH_TRAILING_PUNCT_RE.sub("", stripped)
        if stripped == normalized:
            break
        normalized = stripped
    return normalized


def _added_lines(head: Optional[bytes], staged: bytes) -> list[str]:
    """Return the lines newly present in `staged` that are not part of `head`.

    SUPERSEDED (P1, v9.10.1): find_toji_stub_violations() no longer calls this
    function. Its byte-OFFSET tail-slice approach is exactly what enabled the
    stub-marker splice bypass (see the module docstring's "P1" section) — when
    `head` does not end with a trailing newline, a two-commit sequence can
    complete a partial marker line across the commit boundary, and the
    resulting tail slice starts mid-line, never containing the full marker
    text. find_toji_stub_violations() now scans the FULL staged content and
    exempts already-committed lines by exact per-line text comparison
    (_existing_stub_line_identifiers) instead. Kept defined (unused) for
    historical/API-compatibility reasons only — do not reintroduce it as the
    basis for the stub scan.

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


# ---------------------------------------------------------------------------
# Toji AI-001: full "[TOJI AUDIT LOG]" stub grammar validation
# ---------------------------------------------------------------------------

# protocol/toji.agent.md Section 1.3.4: "<ext> MUST match the actual
# extension of the written report file -- md or docx (Section 6.2 permits
# either format based on requestor preference)".
_TOJI_STUB_ALLOWED_EXTENSIONS = (".md", ".docx")

# Full standardized stub grammar:
#   > [TOJI AUDIT LOG] YYYY-MM-DD · scope: <safe-slug> · findings: N (C/H/M/L)
#     · full report: <path> · —Toji (Sentinel) vX.Y.Z
# The report-path group accepts an OPTIONAL surrounding backtick pair --
# Toji's natural markdown-path-reference style (see _normalize_toji_report_ref
# above; both committed real stubs use one convention or the other) -- in
# addition to a bare path, both are legitimate.
_TOJI_STUB_FULL_RE = re.compile(
    r"^\s*>\s*\[TOJI AUDIT LOG\]\s*"
    r"(?P<date>\d{4}-\d{2}-\d{2})\s*·\s*"
    r"scope:\s*(?P<scope>[a-z0-9-]+)\s*·\s*"
    r"findings:\s*(?P<total>\d+)\s*\(\s*(?P<c>\d+)/(?P<h>\d+)/(?P<m>\d+)/(?P<l>\d+)\s*\)\s*·\s*"
    r"full report:\s*(?P<report>`[^`]+`|\S+)\s*·\s*"
    r"—Toji \(Sentinel\)\s*v(?P<ver>\d+\.\d+\.\d+)\s*$"
)

# LOOSE (date, scope) extraction used ONLY for the per-file uniqueness dedup
# check against committed HEAD content. Deliberately looser than
# _TOJI_STUB_FULL_RE (which requires a safe [a-z0-9-]+ scope) so a
# pre-standardization / already-malformed HISTORICAL stub's raw scope text
# (e.g. "v9.10.0-idgov-full-audit (design+impl+review+go-live)") still
# registers as an existing identifier for dedup purposes -- a NEW stub must
# not be allowed to collide with an old malformed one's (date, scope) pair
# either, even though the old one would itself fail _TOJI_STUB_FULL_RE.
_TOJI_LOOSE_DATE_SCOPE_RE = re.compile(
    r"\[TOJI AUDIT LOG\]\s*(?P<date>\S+)\s*·\s*scope:\s*(?P<scope>[^·]+?)\s*·"
)


def _is_valid_calendar_date(date_str: str) -> bool:
    """True if `date_str` (already YYYY-MM-DD shaped by the regex) is also a
    REAL calendar date (e.g. rejects 2026-13-40)."""
    try:
        datetime.date.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def _existing_stub_identifiers(head: Optional[bytes]) -> set[tuple[str, str]]:
    """Return the set of (date, scope) identifiers for every "[TOJI AUDIT
    LOG]" line already present in the COMMITTED (HEAD) content of a protected
    doc -- used only for the new-stub duplicate-identifier check. Uses the
    LOOSE extractor (see _TOJI_LOOSE_DATE_SCOPE_RE) so even a pre-existing
    malformed historical stub still counts."""
    ids: set[tuple[str, str]] = set()
    if head is None:
        return ids
    text = _normalize(head).decode("utf-8", errors="replace")
    for line in text.splitlines():
        if TOJI_STUB_MARKER not in line:
            continue
        m = _TOJI_LOOSE_DATE_SCOPE_RE.search(line)
        if m:
            ids.add((m.group("date").strip(), m.group("scope").strip()))
    return ids


def _existing_stub_line_identifiers(head: Optional[bytes]) -> set[str]:
    """Return the set of exact (normalized, stripped) "[TOJI AUDIT LOG]"
    line-texts already committed in HEAD for a protected doc.

    P1 fix (v9.10.1, Megumi Tier-3 bundle review): this is the identity
    function backing find_toji_stub_violations()'s full-content-scan
    exemption -- a candidate staged line is treated as genuinely unchanged
    history (and skipped, never re-validated) ONLY when its exact text is a
    member of this set. Using the full line text (rather than a parsed
    (date, scope) pair, as _existing_stub_identifiers above uses for the
    separate semantic duplicate-check) is deliberate and load-bearing:

      - It is trivially robust for a MALFORMED historical line (no scope:
        field to parse at all) -- there is no separate "parse failure"
        branch to get wrong; the full line text IS the identity, always.
      - It does NOT over-exempt a genuinely NEW line that merely shares a
        (date, scope) with an old one but differs in content (e.g. a
        different referenced report) -- that case must still surface as a
        "duplicates an existing audit identifier" violation via
        _existing_stub_identifiers, which this function does not replace.
    """
    ids: set[str] = set()
    if head is None:
        return ids
    text = _normalize(head).decode("utf-8", errors="replace")
    for line in text.splitlines():
        if TOJI_STUB_MARKER in line:
            ids.add(line.strip())
    return ids


_AUDITS_DIRNAME = "audits"


def _safe_audit_rel_path(repo_root: Path, rel_path: str) -> Optional[str]:
    """Validate an untrusted 'full report: <path>' reference before any lookup.

    Returns the normalized (POSIX, forward-slash) relative path string if it is
    safe to use with filesystem/Git lookups, or None if it must be rejected.

    Rejected (fail-CLOSED -> caller treats the reference as not-existing):
      - absolute paths (POSIX `/...` or Windows `C:\\...`) — `Path.__truediv__`
        discards the left operand when the right side is absolute, so
        `repo_root / rel_path` would silently escape repo_root entirely and a
        forged stub could point at ANY file on disk to fake existence.
      - parent-directory traversal (any `..` path segment) — could resolve
        outside repo_root even when the raw string looks relative.
      - any path whose resolved, normalized form does not stay under
        `<repo_root>/audits/` — Toji audit reports only ever live there
        (protocol/toji.agent.md Section 1.3.4); nothing else is a legitimate
        reference target for this stub.
    """
    candidate = rel_path.strip()
    if not candidate:
        return None
    # Normalize to forward slashes so a Windows-style backslash traversal
    # (e.g. "..\\..\\secrets.txt") is caught by the same "/" segment check.
    normalized = candidate.replace("\\", "/")
    if PurePosixPath(normalized).is_absolute():
        return None
    # Windows drive-letter absolute paths (e.g. "C:/Windows/...") are not
    # flagged by PurePosixPath.is_absolute() — check explicitly.
    if re.match(r"^[A-Za-z]:/", normalized):
        return None
    segments = [seg for seg in normalized.split("/") if seg not in ("", ".")]
    if any(seg == ".." for seg in segments):
        return None
    if not segments or segments[0] != _AUDITS_DIRNAME:
        return None

    try:
        audits_root = (repo_root / _AUDITS_DIRNAME).resolve()
        resolved = (repo_root / Path(*segments)).resolve()
    except (OSError, ValueError):
        return None
    try:
        resolved.relative_to(audits_root)
    except ValueError:
        return None

    return "/".join(segments)


def _report_ref_exists(repo_root: Path, rel_path: str) -> bool:
    """True if `rel_path` exists on disk, is staged in the index, or is tracked in HEAD.

    SEC (CodeRabbit PR#108): `rel_path` is parsed from a NEW, untrusted staged
    line (the "full report: <path>" field of a "[TOJI AUDIT LOG]" stub) before
    this function ever runs. It is validated via `_safe_audit_rel_path()`
    first — rejecting absolute paths, `..` traversal, and anything outside
    `<repo_root>/audits/` — so a forged stub can never reference an arbitrary
    file elsewhere on disk (or escape the repo) to fake a passing existence
    check. Any rejected reference returns False, i.e. fails CLOSED — the
    stub is treated exactly like a reference to a genuinely missing report.
    """
    safe_rel_path = _safe_audit_rel_path(repo_root, rel_path)
    if safe_rel_path is None:
        return False
    try:
        if (repo_root / safe_rel_path).is_file():
            return True
    except OSError:
        pass
    if staged_blob(repo_root, safe_rel_path) is not None:
        return True
    if head_blob(repo_root, safe_rel_path) is not None:
        return True
    return False


def find_toji_stub_violations(
    repo_root: Path,
    paths: tuple[str, ...] = TOJI_STUB_SCOPE,
) -> list[str]:
    """Return violation messages for newly-staged "[TOJI AUDIT LOG]" stubs.

    Only NEWLY-ADDED staged content is inspected — pre-existing committed
    content, including old free-form Toji entries predating the standardized
    stub format AND already-committed stubs that do not conform to the
    safe-slug scope rule, is NEVER retroactively flagged; only new additions
    are validated. As of the P1 fix (v9.10.1), "newly-added" is determined by
    scanning the FULL staged content and exempting any line whose exact
    (normalized) text already exists as a line in HEAD (see
    _existing_stub_line_identifiers) — NOT by the byte-offset tail slice
    _added_lines() used to compute, which enabled a two-commit splice bypass
    (see the module docstring's "P1" section for the full mechanism).

    Toji AI-001 (full grammar validation, Sukuna Block B5, v9.10.1): a
    newly-added line containing TOJI_STUB_MARKER is now REQUIRED to match the
    full standardized stub grammar (_TOJI_STUB_FULL_RE) — a line that merely
    LOOKS stub-like but does not conform is now a MALFORMED-STUB violation
    (fail-CLOSED), superseding the prior fail-soft-on-parse-ambiguity
    behavior. A grammar-conforming stub is further checked for: a real
    calendar date, findings-count arithmetic (N == C+H+M+L), an allowed
    report-file extension, report existence (the original SEC-TOJI-102
    check), and per-file (date, scope) uniqueness against every stub already
    committed in HEAD (plus other newly-added stubs in the same commit).
    """
    violations: list[str] = []
    for path in paths:
        staged = staged_blob(repo_root, path)
        if staged is None:
            continue  # nothing staged for this file
        head = head_blob(repo_root, path)
        existing_ids = _existing_stub_identifiers(head)
        existing_line_ids = _existing_stub_line_identifiers(head)
        seen_this_commit: set[tuple[str, str]] = set()
        # P1 fix: scan the FULL staged content (every line), not the
        # byte-offset tail — see _existing_stub_line_identifiers' docstring.
        staged_text = _normalize(staged).decode("utf-8", errors="replace")
        for line in staged_text.splitlines():
            if TOJI_STUB_MARKER not in line:
                continue
            if line.strip() in existing_line_ids:
                # Byte-identical to a line already committed in HEAD — this
                # is permanent, already-validated history. Exempt from
                # re-validation regardless of well-formed/malformed shape.
                continue

            full_match = _TOJI_STUB_FULL_RE.match(line)
            if not full_match:
                violations.append(
                    f"{path}: malformed [TOJI AUDIT LOG] stub — does not match the "
                    "standardized grammar '> [TOJI AUDIT LOG] YYYY-MM-DD · scope: "
                    "<safe-slug> · findings: N (C/H/M/L) · full report: <path> · "
                    "—Toji (Sentinel) vX.Y.Z' (protocol/toji.agent.md Section 1.3.4) "
                    f"(offending line: {line.strip()!r})"
                )
                continue

            date = full_match.group("date")
            scope = full_match.group("scope")
            total = int(full_match.group("total"))
            c, h, m_, l_ = (int(full_match.group(g)) for g in ("c", "h", "m", "l"))
            report_ref_raw = full_match.group("report")
            # Toji AI-001 (scoped fix, retained): strip formatting characters
            # (backticks, quotes, brackets, trailing sentence punctuation)
            # before checking existence/extension — see
            # _normalize_toji_report_ref()'s docstring.
            report_ref = _normalize_toji_report_ref(report_ref_raw)

            if not _is_valid_calendar_date(date):
                violations.append(
                    f"{path}: [TOJI AUDIT LOG] stub date {date!r} is not a valid "
                    f"calendar date (offending line: {line.strip()!r})"
                )
                continue

            if total != c + h + m_ + l_:
                violations.append(
                    f"{path}: [TOJI AUDIT LOG] stub findings count {total} != sum "
                    f"of severities {c}/{h}/{m_}/{l_} = {c + h + m_ + l_} "
                    f"(offending line: {line.strip()!r})"
                )
                continue

            report_ext = Path(report_ref).suffix.lower()
            if report_ext not in _TOJI_STUB_ALLOWED_EXTENSIONS:
                violations.append(
                    f"{path}: [TOJI AUDIT LOG] stub report path {report_ref!r} has an "
                    f"unrecognized extension {report_ext!r} (allowed: "
                    f"{', '.join(_TOJI_STUB_ALLOWED_EXTENSIONS)}) "
                    f"(offending line: {line.strip()!r})"
                )
                continue

            if not _report_ref_exists(repo_root, report_ref):
                violations.append(
                    f"{path}: [TOJI AUDIT LOG] stub references a report that does not "
                    f"exist: '{report_ref_raw}' (offending line: {line.strip()!r})"
                )
                continue

            identifier = (date, scope)
            if identifier in existing_ids or identifier in seen_this_commit:
                violations.append(
                    f"{path}: [TOJI AUDIT LOG] stub duplicates an existing audit "
                    f"identifier (date={date}, scope={scope!r}) — the stable "
                    "audit-id (date, scope) pair must be unique per file "
                    f"(offending line: {line.strip()!r})"
                )
                continue
            seen_this_commit.add(identifier)
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
