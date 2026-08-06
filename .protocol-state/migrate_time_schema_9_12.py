#!/usr/bin/env python3
"""
Domain Zero Protocol - v9.12.0 Wave A / A5: Versioned Legacy-State Migration
Mint: IMPL-TIMESCHEMA-9.12.0-001 (writer=yuuji)

Governing contract: docs/superpowers/specs/2026-08-04-clock-authority-adr.md
(revision 6, USER-signed-off, Sukuna-ratified) -- decision D8 (Toji gate 5).
Governing audit: audits/2026-08-01-toji-session-time-authority-claude-codex.md
-- finding IMPL-003 (MEDIUM): "Legacy naive timestamps are silently
reclassified as UTC."

PURPOSE
-------
`_parse_utc()` in session_monitor.py assigns UTC to every naive ISO
timestamp unconditionally. Commit ae5fac9 (2025-12-31) shows session_monitor.py
producers wrote naive LOCAL datetimes before migrating to aware UTC; commit
236e5b2 (2026-07-21) shows the same class of naive-local era for
project_state_manager.py's own writers. Legacy records from either era have
no offset, so their original instant cannot be recovered from the bytes
alone -- misparsing them as UTC can shift historical durations/gaps/
continuity classifications by the workstation's UTC offset (up to 4 hours in
Eastern Daylight Time, per the audit).

This module implements ADR D8's three-bucket classification (known-utc /
known-local / ambiguous), a `--dry-run` report (mutates nothing), an
`--execute` path (requires a prior dry-run report; creates a checksum-
verified timestamped backup; rewrites ONLY known-utc/known-local records;
stamps `time_schema: 1`), and a `--rollback` path -- following the exact
backup/lock/atomic-write conventions established by
`migrate_state_consolidation.py` (PATCH-STATE-001) for this same class of
operation.

CLASSIFICATION METHOD (git archaeology)
----------------------------------------
D8.2 requires classifying each naive timestamp by PRODUCER VERSION, not by
the timestamp's own face value (the value might be wrong -- that is the
entire premise of the ambiguity). This module answers "which producer wrote
this value, and was that producer naive-local or aware-UTC at the time" by:

1. Matching the record's JSON path against a small registry of KNOWN
   producer path-patterns, each with a CONFIRMED naive-local -> aware-UTC
   cutover commit (investigated and recorded in dev-notes.md for this
   task):
     - `session_monitor.py`  -- commit ae5fac9 (2025-12-31T22:09:47+00:00)
     - `project_state_manager.py` -- commit 236e5b2 (2026-07-21T05:20:55+00:00)
2. Running `git log -S<exact value> --format=%aI -- <tracked file>` to find
   the EARLIEST commit that introduced this literal string into the
   repository, and comparing that commit's date against the matched
   producer's cutover.
3. A path match + a git-confirmed pre-cutover introduction => known-local.
   A path match + a git-confirmed POST-cutover introduction is a
   contradiction (that producer should have been aware by then) => ambiguous
   with an investigation note, never silently trusted either way.
   No path match, OR no git history found for the exact value (untracked
   working-tree-only data, shallow clone, or git unavailable) => ambiguous.
4. A SEPARATE, exact-literal check flags `benchmark_patch_state_001.py`'s
   hardcoded seed values (`"2025-01-01T00:00:00"` / `"2025-01-01T01:00:00"`,
   confirmed via `git log -S` against that script) as synthetic, non-
   authoritative test-fixture data -- never a real instant to convert,
   folded into the `ambiguous` bucket per D8.2 (the safe default) with a
   `recommended_disposition: "permanently_exclude"` so the USER can bulk-
   adjudicate D8.5's third disposition option ("leave permanently excluded
   from continuity decisions") efficiently instead of treating ~2000
   near-identical rows as individually novel.

`known-utc` exists for D8.2 completeness (a naive value from a producer
confirmed to ALWAYS write aware UTC would be a pure formatting anomaly, not
a genuine ambiguity) but nothing in the investigated live dataset naturally
resolves there -- it is reachable via an explicit adjudication-file
override at `execute()` time.

WORK-STREAK SEEDING (considered design decision, not an ADR requirement)
--------------------------------------------------------------------------
`project_state_manager.py`'s `get_work_streak()` implements ADR D7.6: once
`time_schema >= 1`, an ABSENT `work_streak` block fails CLOSED
(`high_risk_block_active=True`) rather than silently defaulting to a fresh
empty streak. Read literally, stamping `time_schema: 1` without ALSO
writing a valid `work_streak` block would trip that fail-closed branch on
the very next read -- not because of any genuine unresolved protection
window, but purely because migration ran before any session populated the
namespace. `execute()` therefore seeds `ProjectStateManager._default_work_streak()`
(structurally valid, `high_risk_block_active=False`, `last_trusted_boundary_utc`
set to the migration instant) IF AND ONLY IF no `work_streak` block already
exists, in the SAME locked write as the `time_schema` stamp. D7.6's
fail-closed guarantee is fully preserved for any LATER corruption event --
this only avoids treating the migration event itself as a corruption event.
Documented here, in dev-notes.md, and asserted by
tests/test_time_schema_migration_9_12.py::TestD76ActivationAfterRealMigration
so the decision is never silent.

SOURCE-STATE BINDING (DESIGN-002 / DESIGN-003, Toji audit 2026-08-06)
-----------------------------------------------------------------------
The audit found that `execute()` applied a dry-run report's classified old
values to the CURRENT project-state.json's dotted/list-index paths without
ever confirming the current file was still the same snapshot the report
was built from (CWE-367 TOCTOU) -- a normal write between `--dry-run` and
`--execute` (including ordinary list pruning of `session_history`, which
the module itself caps at 30 entries) could silently redirect an
adjudicated ruling onto a different record, or overwrite a legitimate
later update with a stale value. DESIGN-002 closes this with THREE layers,
all enforced INSIDE `_migration_lock()`, BEFORE any mutation (including
before the pre-migration backup is created):

1. `classify_all()` now stamps every report with `source_state_digest` --
   a SHA-256 digest of the state's CANONICAL JSON serialization
   (`sort_keys=True, separators=(",", ":")`, deliberately NOT the on-disk
   file's raw bytes, which are formatting-dependent and not what
   `_atomic_write()` reproduces byte-for-byte -- see `_canonical_digest()`).
   `execute()` recomputes this digest against the state it just loaded
   under the lock and requires an EXACT match; any mismatch raises
   `StateDriftError` and touches nothing.
2. A digest-less or schema-mismatched report (anything predating this
   fix, including the concrete report this session's live migration
   produced) is refused outright via `LegacyReportMissingDigestError` --
   fail-closed on an unbound legacy artifact rather than trusting
   whatever the live file happens to contain right now.
3. Independent of (1)/(2), `_verify_records_bound_to_state()` re-checks
   EVERY classified record against the freshly-loaded state: the value at
   its exact path must be unchanged, and -- for a record nested inside a
   list element -- that element's STABLE IDENTITY (its own `session_id`/
   `id` field if present, else a content digest of the whole element,
   captured once at classification time) must still resolve to the same
   element, not merely to whatever now sits at that numeric index. This
   layer is normally redundant with (1) (a matching whole-state digest
   implies every sub-path is unchanged) -- it exists as an independently
   testable second gate per the audit's explicit recommendation, not
   merely reachable only in combination with the digest check.
Any failure in any layer raises a subclass of `UnboundMigrationReportError`
and instructs a fresh `--dry-run` + adjudication reconciliation; nothing
is backed up or mutated first.

DESIGN-003 closes the matching rollback gap: `rollback()` no longer
restores via a bare `shutil.copy2()` straight onto the live path outside
any lock. It now (a) verifies the backup's on-disk checksum against a
`.sha256` sidecar recorded at BACKUP-CREATION time (`_create_backup()`)
BEFORE entering the mutation phase -- catching post-creation corruption or
tampering of the backup itself, not merely confirming it still parses as
JSON -- (b) performs the restore under the SAME `_migration_lock()` and
the SAME `ProjectStateManager._atomic_write()` primitive forward migration
already uses, and (c) re-reads the committed file and compares it against
the restored content WHILE STILL HOLDING THE LOCK, so a concurrent writer
racing the lock release can never be mistaken for a successful rollback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

try:
    from project_state_manager import ProjectStateManager
except ImportError:  # pragma: no cover
    print("[ERROR] Cannot import ProjectStateManager")
    print("  Ensure project_state_manager.py exists in .protocol-state/")
    sys.exit(1)

try:
    from timing_policy import load_timing_policy
except ImportError:  # pragma: no cover
    load_timing_policy = None  # zone resolution degrades to "no zone" below


TIME_SCHEMA_VERSION = 1
# DESIGN-002 (Toji audit 2026-08-06): bumped 1 -> 2 alongside the new
# mandatory source_state_digest/source_state_digest_algo report fields and
# per-record identity_anchor_path/identity_kind/identity_value fields --
# execute() treats ANY report whose report_schema != REPORT_SCHEMA_VERSION
# as unbound/legacy and refuses it (LegacyReportMissingDigestError).
REPORT_SCHEMA_VERSION = 2

BACKUP_PATTERN = re.compile(r"^time-schema-migration_\d{8}_\d{6}(_\d+)?$")

# A naive ISO-8601 datetime: no trailing 'Z' and no explicit +HH:MM/-HH:MM
# offset. Deliberately does NOT match values that already carry an offset --
# this module only ever classifies/rewrites genuinely naive records.
_NAIVE_TS_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$"
)

# Confirmed via `benchmark_patch_state_001.py::_create_mock_troubleshooting_history()`
# (hardcoded literal, git-log -S confirmed) -- synthetic test-fixture data
# that leaked into a live project-state.json, never a real instant.
_SYNTHETIC_BENCHMARK_VALUES = {
    "2025-01-01T00:00:00",
    "2025-01-01T01:00:00",
}
_SYNTHETIC_BENCHMARK_PATH_HINT = "troubleshooting.history.sessions"


class Bucket(Enum):
    KNOWN_UTC = "known-utc"
    KNOWN_LOCAL = "known-local"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class ProducerRule:
    """A known producer's path pattern + confirmed naive-local -> aware-UTC
    cutover commit (ADR D8.2's 'producer is unambiguous from context')."""

    path_pattern: "re.Pattern[str]"
    producer: str
    cutover_commit: str
    cutover_utc: datetime


# Investigated and recorded in dev-notes.md for IMPL-TIMESCHEMA-9.12.0-001.
_PRODUCER_REGISTRY: List[ProducerRule] = [
    ProducerRule(
        path_pattern=re.compile(
            r"^session_tracking\.session_history\[\d+\]\.(start_time|end_time)$"
        ),
        producer="session_monitor.py",
        cutover_commit="ae5fac9",
        cutover_utc=datetime(2025, 12, 31, 22, 9, 47, tzinfo=timezone.utc),
    ),
    ProducerRule(
        path_pattern=re.compile(
            r"^(tier_tracking\.last_updated"
            r"|troubleshooting\.statistics\.last_updated"
            r"|agent_invocation_tracking\._last_updated"
            r"|agent_invocation_tracking\.invocations\.[\w-]+\.last_invocation"
            r"|agent_invocation_tracking\.bypass_detection\.bypass_alerts\[\d+\]\.timestamp"
            r"|session_tracking\.last_updated)$"
        ),
        producer="project_state_manager.py",
        cutover_commit="236e5b2",
        cutover_utc=datetime(2026, 7, 21, 5, 20, 55, tzinfo=timezone.utc),
    ),
]


@dataclass
class ClassificationResult:
    bucket: Bucket
    producer: Optional[str] = None
    note: str = ""
    recommended_disposition: str = "review"
    synthetic_benchmark_data: bool = False
    evidence: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Classification engine (pure function -- no I/O beyond the injected
# git_lookup callable, so it is fully unit-testable offline).
# ---------------------------------------------------------------------------

def classify_record(
    path: str,
    value: str,
    *,
    git_lookup: Optional[Callable[[str], Optional[datetime]]] = None,
) -> ClassificationResult:
    """Classify one naive-timestamp record per ADR D8.2.

    Args:
        path: dotted/bracketed JSON path (e.g.
            "session_tracking.session_history[0].start_time").
        value: the naive ISO-8601 string as persisted.
        git_lookup: callable(value) -> earliest introduction datetime (aware
            UTC) or None if not found / unavailable. Defaults to the real
            `_git_first_introduction_utc()` bound to the repo root when
            omitted (production use); tests inject a fake for determinism.
    """
    if git_lookup is None:
        git_lookup = lambda v: _git_first_introduction_utc(REPO_ROOT_DEFAULT, PROJECT_STATE_RELATIVE, v)  # noqa: E731

    if _SYNTHETIC_BENCHMARK_PATH_HINT in path and value in _SYNTHETIC_BENCHMARK_VALUES:
        return ClassificationResult(
            bucket=Bucket.AMBIGUOUS,
            producer="benchmark_patch_state_001.py (test fixture)",
            note=(
                "Exact-literal match to benchmark_patch_state_001.py's "
                "hardcoded mock-history seed value -- synthetic test-fixture "
                "data, never a real instant. Safe default per D8.2; "
                "recommended for D8.5's 'permanently excluded from "
                "continuity decisions' disposition rather than individual "
                "per-row review."
            ),
            recommended_disposition="permanently_exclude",
            synthetic_benchmark_data=True,
        )

    rule = next((r for r in _PRODUCER_REGISTRY if r.path_pattern.match(path)), None)
    if rule is None:
        return ClassificationResult(
            bucket=Bucket.AMBIGUOUS,
            note="No known producer path pattern matches this record.",
            recommended_disposition="review",
        )

    introduced_at = git_lookup(value)
    if introduced_at is None:
        return ClassificationResult(
            bucket=Bucket.AMBIGUOUS,
            producer=rule.producer,
            note=(
                f"Path matches known producer '{rule.producer}', but git "
                "archaeology could not confirm when this exact value was "
                "introduced (untracked/working-tree-only, shallow clone, or "
                "git unavailable). Provenance cannot be established; safe "
                "default per D8.2."
            ),
            recommended_disposition="review",
            evidence={"producer_cutover_commit": rule.cutover_commit},
        )

    if introduced_at < rule.cutover_utc:
        return ClassificationResult(
            bucket=Bucket.KNOWN_LOCAL,
            producer=rule.producer,
            note=(
                f"Introduced {introduced_at.isoformat()}, before "
                f"{rule.producer}'s confirmed naive-local -> aware-UTC "
                f"cutover ({rule.cutover_commit}, {rule.cutover_utc.isoformat()})."
            ),
            recommended_disposition="convert",
            evidence={
                "producer_cutover_commit": rule.cutover_commit,
                "introduced_at_utc": introduced_at.isoformat(),
            },
        )

    return ClassificationResult(
        bucket=Bucket.AMBIGUOUS,
        producer=rule.producer,
        note=(
            f"Path matches known producer '{rule.producer}', but this value "
            f"was introduced {introduced_at.isoformat()} -- AT OR AFTER that "
            f"producer's confirmed aware-UTC cutover "
            f"({rule.cutover_commit}, {rule.cutover_utc.isoformat()}). A "
            "naive value from an already-aware producer is a contradiction; "
            "never silently trusted either way -- flagged for investigation."
        ),
        recommended_disposition="investigate",
        evidence={
            "producer_cutover_commit": rule.cutover_commit,
            "introduced_at_utc": introduced_at.isoformat(),
        },
    )


# ---------------------------------------------------------------------------
# Git archaeology
# ---------------------------------------------------------------------------

REPO_ROOT_DEFAULT = Path(__file__).resolve().parent.parent
PROJECT_STATE_RELATIVE = ".protocol-state/project-state.json"


def _git_first_introduction_utc(
    repo_root: Path, tracked_file: str, exact_value: str
) -> Optional[datetime]:
    """Return the EARLIEST commit's author date (aware UTC) that introduced
    `exact_value` as a literal substring into `tracked_file`'s history, or
    None if git is unavailable, the repo has no history for that file, or
    the value was never committed (untracked/working-tree-only)."""
    try:
        result = subprocess.run(
            [
                "git", "log", "--all", "--format=%aI",
                f"-S{exact_value}", "--", tracked_file,
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    dates = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not dates:
        return None
    parsed = []
    for d in dates:
        try:
            parsed.append(datetime.fromisoformat(d))
        except ValueError:
            continue
    if not parsed:
        return None
    return min(parsed).astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# State walking
# ---------------------------------------------------------------------------

def _iter_naive_timestamps(obj: Any, path: str = ""):
    """Depth-first walk yielding (path, value) for every string value that
    looks like a naive ISO-8601 datetime (no offset)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_naive_timestamps(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _iter_naive_timestamps(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        if _NAIVE_TS_PATTERN.match(obj):
            yield (path, obj)


def _set_by_path(state: Dict[str, Any], path: str, value: Any) -> None:
    """Set a value at a dotted/bracketed path produced by `_iter_naive_timestamps()`."""
    tokens = re.findall(r"[^.\[\]]+|\[\d+\]", path)
    cursor: Any = state
    for i, token in enumerate(tokens):
        is_last = i == len(tokens) - 1
        if token.startswith("["):
            idx = int(token[1:-1])
            if is_last:
                cursor[idx] = value
            else:
                cursor = cursor[idx]
        else:
            if is_last:
                cursor[token] = value
            else:
                cursor = cursor[token]


def _get_by_path(state: Any, path: str) -> "tuple[bool, Any]":
    """Read-only mirror of `_set_by_path()`: returns `(found, value)` for
    `path` in `state`, WITHOUT raising on a missing key / out-of-range
    index / type mismatch. A "not found" result is itself a meaningful
    DESIGN-002 signal (the record a report classified no longer exists at
    that location) -- never a crash, and never silently coerced to a
    default."""
    tokens = re.findall(r"[^.\[\]]+|\[\d+\]", path)
    cursor: Any = state
    for token in tokens:
        if token.startswith("["):
            idx = int(token[1:-1])
            if not isinstance(cursor, list) or idx < 0 or idx >= len(cursor):
                return False, None
            cursor = cursor[idx]
        else:
            if not isinstance(cursor, dict) or token not in cursor:
                return False, None
            cursor = cursor[token]
    return True, cursor


def _canonical_json_bytes(obj: Any) -> bytes:
    """DESIGN-002: deterministic byte serialization used ONLY for
    source-state/record-identity binding digests -- sorted keys, no
    incidental whitespace, UTF-8. Deliberately distinct from:

    - `ProjectStateManager._atomic_write()`'s on-disk formatting
      (`indent=2`, insertion-order-preserving) -- that format is for human
      readability and stable diffs, not digest stability.
    - `attestation.py`'s raw-file-bytes hashing -- that hashes the EXACT
      bytes actually on disk, which is the right thing for "did this exact
      file change since the last sanctioned write", but the WRONG thing
      here: a dry-run report's `source_state_digest` must compare equal
      against ANY later independent load of the same logical content,
      regardless of that load's own key order or incidental whitespace.

    This is why `_verify_records_bound_to_state()` re-derives identity
    digests the same way rather than ever comparing raw file bytes.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _canonical_digest(obj: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(obj)).hexdigest()


def _last_list_index_anchor(path: str) -> Optional[str]:
    """DESIGN-002: return the dotted/bracketed sub-path to the NEAREST
    enclosing list element for `path` (the path through and including the
    LAST `[N]` token), or None if `path` contains no list index at all --
    a pure dict path is not subject to the index-drift a list element is."""
    tokens = re.findall(r"[^.\[\]]+|\[\d+\]", path)
    last_idx = None
    for i, tok in enumerate(tokens):
        if tok.startswith("["):
            last_idx = i
    if last_idx is None:
        return None
    out = ""
    for tok in tokens[: last_idx + 1]:
        if tok.startswith("["):
            out += tok
        else:
            out += ("." if out else "") + tok
    return out


def _capture_record_identity(state: Any, path: str) -> "tuple[Optional[str], Optional[str], Optional[str]]":
    """DESIGN-002: for a record nested inside a list element, capture a
    STABLE identity for that element at classification time, independent
    of its numeric index -- the element's own `session_id` if present,
    else its `id` if present, else a content digest of the whole element.
    Returns `(identity_anchor_path, identity_kind, identity_value)`, or
    `(None, None, None)` for a pure-dict path with no enclosing list
    index."""
    anchor = _last_list_index_anchor(path)
    if anchor is None:
        return None, None, None
    found, element = _get_by_path(state, anchor)
    if not found:  # pragma: no cover - unreachable at classification time
        return anchor, None, None
    if isinstance(element, dict):
        session_id = element.get("session_id")
        if isinstance(session_id, str) and session_id:
            return anchor, "session_id", session_id
        element_id = element.get("id")
        if isinstance(element_id, str) and element_id:
            return anchor, "id", element_id
    return anchor, "content_digest", _canonical_digest(element)


# ---------------------------------------------------------------------------
# Migration errors
# ---------------------------------------------------------------------------

class MigrationNotReadyError(RuntimeError):
    """Raised when --execute is invoked without a prior --dry-run report."""


class BackupIntegrityError(RuntimeError):
    """Raised when a created backup's checksum does not match the source."""


class AdjudicationValidationError(RuntimeError):
    """v9.12.0 A6 (ADR D8.5 Option C sequencing layer, per the read-side-
    gating design note, docs/superpowers/specs/2026-08-05-timeschema-read-side-gating-design-note.md
    Section 2 Option C): raised when a USER adjudication-input file is
    malformed -- an unknown disposition, a missing required field, an
    invalid `path_pattern` regex, or an invalid IANA `zone` override. Fails
    LOUD at load time, before any state mutation -- a silently-skipped
    malformed entry would look identical to "no adjudication decision for
    this record," which would then fall through to the record's own
    bucket-derived default, silently discarding the USER's actual ruling.
    This is exactly the class of failure D8.5 exists to prevent, applied to
    the adjudication mechanism itself."""


class UnboundMigrationReportError(RuntimeError):
    """DESIGN-002 (Toji audit 2026-08-06, HIGH; CWE-367): base class for
    every way `execute()` can determine that the most recent dry-run
    report can no longer be safely bound to the CURRENT project-state.json
    snapshot. Always raised BEFORE any mutation of live state -- before
    backup creation, before the atomic write -- so the safe recovery is
    always the same: run a fresh `--dry-run`, reconcile any adjudication
    file against the new report's records, and retry `--execute`."""


class LegacyReportMissingDigestError(UnboundMigrationReportError):
    """The most recent dry-run report predates DESIGN-002's source-state
    binding (wrong/missing `report_schema`, or no `source_state_digest`
    field) and was therefore never bound to any specific state snapshot in
    the first place. Fail-closed rather than execute an unbound legacy
    report against whatever the live state happens to contain right now."""


class StateDriftError(UnboundMigrationReportError):
    """project-state.json's canonical content digest no longer matches the
    dry-run report's recorded `source_state_digest` -- some writer (a live
    session, another migration attempt, manual editing, ordinary
    session_history pruning) has changed the file since the report was
    generated. Applying the report's classified old values to the current
    file's paths under these conditions is exactly the TOCTOU this finding
    describes."""


class RecordIdentityMismatchError(UnboundMigrationReportError):
    """Defense-in-depth beyond `StateDriftError`: one or more individual
    classified records no longer match the current state at the exact path
    the report recorded, or (for a record nested inside a list element)
    that element's stable identity captured at dry-run time no longer
    resolves to the same element. In ordinary operation this is
    unreachable whenever the whole-state digest check already passed (a
    matching digest implies every sub-path is unchanged) -- it exists as
    an independent, separately-testable safety net per the audit's
    explicit recommendation not to rely on the whole-state digest alone
    for list-index binding."""


# ---------------------------------------------------------------------------
# Adjudication input (v9.12.0 A6 -- ADR D8.5 Option C sequencing layer)
# ---------------------------------------------------------------------------

# The three dispositions execute() understands. Validated at LOAD time
# (below), not merely checked defensively deep inside execute()'s loop --
# see AdjudicationValidationError's docstring for why load-time validation
# matters here specifically.
_VALID_DISPOSITIONS = {"known_local", "known_utc", "permanently_exclude"}


@dataclass(frozen=True)
class _BulkRule:
    """One `bulk_decisions[]` entry: a compiled path-pattern regex + the
    disposition to apply to every UNRESOLVED (not already covered by an
    exact `decisions[]` entry) record whose path fully matches it.

    Added specifically because the original per-exact-path-only
    `decisions` format (still supported, unchanged, and always takes
    precedence -- see `AdjudicationTable.resolve()`) would require ~2000
    individual entries to dispose of the live dataset's synthetic-benchmark
    rows (`troubleshooting.history.sessions[0..999].(started_at|completed_at)`)
    -- exactly the small, worthwhile extension the ADR's Option C text
    calls out as needed "regardless of which option is chosen."
    """

    pattern: "re.Pattern[str]"
    path_pattern: str
    disposition: str
    reason: Optional[str] = None
    zone: Optional[str] = None
    match_synthetic_benchmark_data: Optional[bool] = None
    override_classifier_bucket: Optional[bool] = None


@dataclass
class AdjudicationTable:
    """The loaded, validated contents of a USER adjudication-input file,
    resolved per-record via `resolve()`.

    Precedence: an exact `decisions[]` entry for a path ALWAYS wins over any
    matching `bulk_decisions[]` rule for that same path -- more specific
    beats more general, the same precedence an explicit per-record USER
    override would intuitively carry over a broad bulk ruling.

    SEC-CLOCKADR-9.12.0-026 (P2): `resolve()` returning a decision does NOT
    by itself mean `execute()` applies it. A decision only ever applies
    unconditionally to a record the classifier bucketed `ambiguous` -- the
    documented, intended use case (the whole reason adjudication exists).
    Applying a decision to a NON-ambiguous record (`known_utc`/`known_local`,
    already resolved with HIGH confidence by git archaeology) requires the
    decision to carry an explicit `override_classifier_bucket: true` flag;
    absent that flag, `execute()` REFUSES the decision -- loudly, with a
    distinguishing per-record audit-trail entry -- and falls back to the
    record's own bucket-derived default, exactly as if no adjudication
    entry had matched at all. This mirrors the same principle
    `AdjudicationValidationError` already enforces for malformed INPUT
    (never silently discard/reinterpret a USER ruling without a trace),
    applied here to the mechanism's own SCOPE boundary: a decision must
    never silently override a record nobody actually flagged as needing
    review.
    """

    exact: Dict[str, Dict[str, Any]]
    bulk: List[_BulkRule]

    def resolve(self, path: str, record: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Return the decision dict for `path` (exact match first, then the
        first matching bulk rule, in file order), or None if nothing
        adjudicates this record -- callers fall back to the record's own
        classifier-assigned bucket, exactly as before this extension."""
        if path in self.exact:
            return self.exact[path]
        for rule in self.bulk:
            if not rule.pattern.fullmatch(path):
                continue
            if rule.match_synthetic_benchmark_data is not None:
                actual_flag = bool((record or {}).get("synthetic_benchmark_data"))
                if actual_flag != rule.match_synthetic_benchmark_data:
                    continue
            return {
                "path": path,
                "disposition": rule.disposition,
                "reason": rule.reason,
                "zone": rule.zone,
                "override_classifier_bucket": rule.override_classifier_bucket,
                "_bulk_source": rule.path_pattern,
            }
        return None


def _validate_adjudication_zone_string(zone: Any, *, context: str) -> None:
    """Validate an adjudication entry's optional `zone` override against the
    `zoneinfo` database (the same validation standard the D4 zone resolver
    applies elsewhere in this codebase) -- fails loud at LOAD time, not at
    the moment `execute()` tries to use an invalid zone deep in its loop."""
    if not isinstance(zone, str) or not zone:
        raise AdjudicationValidationError(
            f"{context}: 'zone' must be a non-empty IANA zone identifier string "
            f"(got {zone!r})."
        )
    try:
        ZoneInfo(zone)
    except Exception as e:
        raise AdjudicationValidationError(
            f"{context}: 'zone' {zone!r} is not a valid IANA zone identifier: {e}"
        ) from e


# ---------------------------------------------------------------------------
# Migrator
# ---------------------------------------------------------------------------

class TimeSchemaMigrator:
    def __init__(
        self,
        protocol_root: Path,
        manager: Optional[ProjectStateManager] = None,
        git_lookup: Optional[Callable[[str], Optional[datetime]]] = None,
    ):
        self.protocol_root = Path(protocol_root)
        self.state_dir = self.protocol_root / ".protocol-state"
        self.migrations_dir = self.state_dir / "migrations"
        self.manager = manager or ProjectStateManager(self.protocol_root)
        self._git_lookup = git_lookup or (
            lambda v: _git_first_introduction_utc(
                self.protocol_root, PROJECT_STATE_RELATIVE, v
            )
        )
        self._user_zone: Optional[ZoneInfo] = self._resolve_user_zone()

    # -- zone resolution -----------------------------------------------

    def _resolve_user_zone(self) -> Optional[ZoneInfo]:
        """D4-consistent zone resolution for interpreting known-local naive
        values. Degrades to None (never converts known-local records) if
        the loader is unavailable or the zone cannot be resolved -- this
        module never silently substitutes the execution host's zone."""
        if load_timing_policy is None:
            return None
        try:
            policy = load_timing_policy(protocol_root=self.protocol_root)
        except Exception:
            return None
        if policy.user_zone.iana is None:
            return None
        try:
            return ZoneInfo(policy.user_zone.iana)
        except Exception:
            return None

    # -- classification ---------------------------------------------------

    def classify_all(self, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if state is None:
            state = self.manager.load_project_state()

        # DESIGN-002: bind this report to the EXACT snapshot it classifies.
        # Computed from the loaded dict's canonical serialization, not the
        # source file's raw bytes -- see `_canonical_json_bytes()`'s
        # docstring for why (must survive an independent later re-load).
        source_state_digest = _canonical_digest(state)

        records = []
        for path, value in _iter_naive_timestamps(state):
            result = classify_record(path, value, git_lookup=self._git_lookup)
            identity_anchor_path, identity_kind, identity_value = _capture_record_identity(state, path)
            records.append(
                {
                    "path": path,
                    "value": value,
                    "bucket": result.bucket.value,
                    "producer": result.producer,
                    "note": result.note,
                    "recommended_disposition": result.recommended_disposition,
                    "synthetic_benchmark_data": result.synthetic_benchmark_data,
                    "evidence": result.evidence,
                    # DESIGN-002: stable-identity binding for list-borne
                    # records (None/None/None for a pure-dict path -- see
                    # `_capture_record_identity()`).
                    "identity_anchor_path": identity_anchor_path,
                    "identity_kind": identity_kind,
                    "identity_value": identity_value,
                }
            )

        counts = {
            "total": len(records),
            "known_utc": sum(1 for r in records if r["bucket"] == Bucket.KNOWN_UTC.value),
            "known_local": sum(1 for r in records if r["bucket"] == Bucket.KNOWN_LOCAL.value),
            "ambiguous": sum(1 for r in records if r["bucket"] == Bucket.AMBIGUOUS.value),
        }

        report = {
            "report_schema": REPORT_SCHEMA_VERSION,
            "generated_at_utc": self.manager.time_provider.utc_now().isoformat(),
            "user_zone_iana": str(self._user_zone.key) if self._user_zone else None,
            # DESIGN-002: required by execute() for the source-state-binding
            # gate -- see UnboundMigrationReportError and its subclasses.
            "source_state_digest": source_state_digest,
            "source_state_digest_algo": "sha256",
            "counts": counts,
            "records": records,
            "adjudication_required": [r for r in records if r["bucket"] == Bucket.AMBIGUOUS.value],
        }
        return report

    # -- DESIGN-002 verification -------------------------------------------

    def _verify_records_bound_to_state(
        self, records: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[str]:
        """DESIGN-002 defense-in-depth: independent of the whole-state
        digest check in `execute()`, verify EACH classified record still
        matches `state` -- the value at its path is unchanged, and (for a
        record nested inside a list element) that element's stable
        identity captured at dry-run time still resolves to the same
        element. Returns a list of human-readable mismatch diagnostics
        (empty == fully bound); never raises itself, so this stays
        independently unit-testable against hand-built states -- the
        caller (`execute()`) decides how to fail closed on a non-empty
        result."""
        mismatches: List[str] = []
        for record in records:
            path = record["path"]
            found, current_value = _get_by_path(state, path)
            if not found:
                mismatches.append(f"{path}: no longer present in the current state.")
                continue
            if current_value != record["value"]:
                mismatches.append(
                    f"{path}: current value {current_value!r} does not match the "
                    f"report's classified value {record['value']!r}."
                )
                continue

            anchor = record.get("identity_anchor_path")
            if not anchor:
                continue
            found_anchor, current_element = _get_by_path(state, anchor)
            if not found_anchor:
                mismatches.append(f"{path}: enclosing record at {anchor} no longer exists.")
                continue
            expected_kind = record.get("identity_kind")
            expected_value = record.get("identity_value")
            if expected_kind == "session_id":
                actual = current_element.get("session_id") if isinstance(current_element, dict) else None
            elif expected_kind == "id":
                actual = current_element.get("id") if isinstance(current_element, dict) else None
            elif expected_kind == "content_digest":
                actual = _canonical_digest(current_element)
            else:  # pragma: no cover - defense-in-depth, unreachable via classify_all()
                actual = None
            if actual != expected_value:
                mismatches.append(
                    f"{path}: enclosing record at {anchor} no longer matches its "
                    f"dry-run identity ({expected_kind}={expected_value!r} vs current "
                    f"{actual!r}) -- list position may have shifted (pruning/"
                    "reordering) since the dry-run report was generated."
                )
        return mismatches

    # -- dry-run ------------------------------------------------------

    def dry_run(self) -> Dict[str, Any]:
        report = self.classify_all()
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        timestamp = self.manager.time_provider.utc_now().strftime("%Y%m%d_%H%M%S_%f")
        report_path = self.migrations_dir / f"time_schema_migration_report_{timestamp}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        report["_report_path"] = str(report_path)

        print("=== Time-Schema Migration: DRY RUN (no changes made) ===")
        print(f"Total naive timestamps found: {report['counts']['total']}")
        print(f"  known-utc:   {report['counts']['known_utc']}")
        print(f"  known-local: {report['counts']['known_local']}")
        print(f"  ambiguous:   {report['counts']['ambiguous']} (USER adjudication required)")
        print(f"Report written to: {report_path}")
        return report

    def _latest_dry_run_report_path(self) -> Optional[Path]:
        if not self.migrations_dir.exists():
            return None
        candidates = sorted(self.migrations_dir.glob("time_schema_migration_report_*.json"))
        return candidates[-1] if candidates else None

    # -- execute --------------------------------------------------------

    def _compute_checksum(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _create_backup(self) -> Path:
        timestamp = self.manager.time_provider.utc_now().strftime("%Y%m%d_%H%M%S_%f")
        backup_dir = self.state_dir / "backups" / f"time-schema-migration_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        source = self.manager.project_state_file
        target = backup_dir / source.name
        shutil.copy2(source, target)
        source_hash = self._compute_checksum(source)
        target_hash = self._compute_checksum(target)
        if source_hash != target_hash:
            raise BackupIntegrityError(
                f"Backup checksum mismatch for {source.name}: "
                f"expected {source_hash}, got {target_hash}"
            )
        # DESIGN-003: record the checksum as a sidecar AT CREATION TIME so a
        # LATER --rollback can detect post-creation corruption/tampering of
        # the backup file itself, not merely confirm it still parses as
        # JSON. Written after the integrity check above passes, so a sidecar
        # existing at all is itself evidence the backup was verified once.
        sidecar = target.parent / (target.name + ".sha256")
        sidecar.write_text(target_hash + "\n", encoding="utf-8")
        return backup_dir

    def _localize_naive_to_utc(self, naive_value: str, zone: ZoneInfo) -> str:
        dt = datetime.fromisoformat(naive_value)
        localized = dt.replace(tzinfo=zone)
        return localized.astimezone(timezone.utc).isoformat()

    def _load_adjudication(self, adjudication_path: Optional[Path]) -> AdjudicationTable:
        """v9.12.0 A6 (ADR D8.5 Option C sequencing layer): load and VALIDATE
        a USER adjudication-input file. Supports two entry kinds, both
        optional and combinable:

        - `decisions[]` (original, per-exact-path; unchanged shape):
          `{"path": "...", "disposition": "known_local"|"known_utc"|
          "permanently_exclude", "reason": "...", "zone": "..." (optional)}`.
          `zone`, if present, is an explicit IANA override used INSTEAD of
          the migrator's globally-resolved `self._user_zone` for this one
          record's `known_local` conversion -- recorded explicitly on the
          decision itself so the adjudicated conversion is reproducible
          regardless of what `protocol.config.yaml::user.timezone` /
          `DZP_USER_TIMEZONE` happen to resolve to at a LATER `--execute`
          time (D8.5: "an explicit reclassification action, itself an
          ordinary provenance-recorded revision, not an automated
          inference" -- an implicit, environment-dependent zone would not
          meet that bar).
        - `bulk_decisions[]` (NEW): `{"path_pattern": "<regex>",
          "disposition": ..., "reason": "...", "zone": "..." (optional),
          "match_synthetic_benchmark_data": true|false (optional)}`. Applies
          to every record whose path `re.fullmatch()`es `path_pattern` AND
          (if `match_synthetic_benchmark_data` is given) whose own
          `synthetic_benchmark_data` report flag equals it -- the
          Option-C-recommended extension for disposing of a large uniform
          bucket (e.g. ~2000 synthetic-benchmark rows) without an individual
          entry per row. An exact `decisions[]` entry for the same path
          always takes precedence (see `AdjudicationTable.resolve()`).

        Both entry kinds also accept an optional `override_classifier_bucket`
        boolean (SEC-CLOCKADR-9.12.0-026): REQUIRED to be `true` before
        `execute()` will apply a decision to a record the classifier did
        NOT bucket `ambiguous` -- see `AdjudicationTable`'s class docstring
        for the full scope-gate semantics. Validated as a boolean here (if
        present) for the same fail-loud-at-load-time reason as every other
        field.

        Raises `AdjudicationValidationError` (fail loud, at load time,
        before any state mutation) on: a missing/non-string `path` /
        `path_pattern`; a `disposition` outside
        `{known_local, known_utc, permanently_exclude}`; an invalid
        `path_pattern` regex; or a `zone` that does not resolve via
        `zoneinfo`. A malformed entry is NEVER silently skipped -- that
        would look identical to "no adjudication for this record," silently
        discarding an actual USER ruling.
        """
        if adjudication_path is None:
            return AdjudicationTable(exact={}, bulk=[])
        with open(adjudication_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        exact: Dict[str, Dict[str, Any]] = {}
        for i, d in enumerate(data.get("decisions", [])):
            path = d.get("path")
            disposition = d.get("disposition")
            if not path or not isinstance(path, str):
                raise AdjudicationValidationError(
                    f"decisions[{i}]: missing/invalid 'path' (got {path!r})."
                )
            if disposition not in _VALID_DISPOSITIONS:
                raise AdjudicationValidationError(
                    f"decisions[{i}] ({path!r}): disposition {disposition!r} is "
                    f"not one of {sorted(_VALID_DISPOSITIONS)}."
                )
            zone = d.get("zone")
            if zone is not None:
                _validate_adjudication_zone_string(zone, context=f"decisions[{i}] ({path!r})")
            override_flag = d.get("override_classifier_bucket")
            if override_flag is not None and not isinstance(override_flag, bool):
                raise AdjudicationValidationError(
                    f"decisions[{i}] ({path!r}): 'override_classifier_bucket' must be a "
                    f"boolean if present (got {override_flag!r})."
                )
            exact[path] = d

        bulk: List[_BulkRule] = []
        for i, b in enumerate(data.get("bulk_decisions", [])):
            pattern_str = b.get("path_pattern")
            disposition = b.get("disposition")
            if not pattern_str or not isinstance(pattern_str, str):
                raise AdjudicationValidationError(
                    f"bulk_decisions[{i}]: missing/invalid 'path_pattern' "
                    f"(got {pattern_str!r})."
                )
            if disposition not in _VALID_DISPOSITIONS:
                raise AdjudicationValidationError(
                    f"bulk_decisions[{i}] ({pattern_str!r}): disposition "
                    f"{disposition!r} is not one of {sorted(_VALID_DISPOSITIONS)}."
                )
            try:
                compiled = re.compile(pattern_str)
            except re.error as e:
                raise AdjudicationValidationError(
                    f"bulk_decisions[{i}]: invalid path_pattern regex "
                    f"{pattern_str!r}: {e}"
                ) from e
            zone = b.get("zone")
            if zone is not None:
                _validate_adjudication_zone_string(
                    zone, context=f"bulk_decisions[{i}] ({pattern_str!r})"
                )
            match_synth = b.get("match_synthetic_benchmark_data")
            if match_synth is not None and not isinstance(match_synth, bool):
                raise AdjudicationValidationError(
                    f"bulk_decisions[{i}]: 'match_synthetic_benchmark_data' must "
                    f"be a boolean if present (got {match_synth!r})."
                )
            override_flag = b.get("override_classifier_bucket")
            if override_flag is not None and not isinstance(override_flag, bool):
                raise AdjudicationValidationError(
                    f"bulk_decisions[{i}]: 'override_classifier_bucket' must be a "
                    f"boolean if present (got {override_flag!r})."
                )
            bulk.append(
                _BulkRule(
                    pattern=compiled,
                    path_pattern=pattern_str,
                    disposition=disposition,
                    reason=b.get("reason"),
                    zone=zone,
                    match_synthetic_benchmark_data=match_synth,
                    override_classifier_bucket=override_flag,
                )
            )

        return AdjudicationTable(exact=exact, bulk=bulk)

    def execute(self, *, adjudication_path: Optional[Path] = None) -> Dict[str, Any]:
        """D8.4: requires a prior --dry-run report to exist. DESIGN-002:
        the report must also be BOUND to the current state -- a matching
        `source_state_digest` recomputed inside the migration lock, plus a
        per-record value/stable-identity re-verification -- before ANY
        mutation, including backup creation. Only then creates a
        timestamped, checksum-verified backup and rewrites known-utc/
        known-local records (plus any adjudicated overrides) via
        `ProjectStateManager`'s migration-locked atomic-write path, stamps
        `time_schema`, and seeds `work_streak` if absent (see module
        docstring)."""
        report_path = self._latest_dry_run_report_path()
        if report_path is None:
            raise MigrationNotReadyError(
                "No dry-run report found. Run --dry-run first (ADR D8.4: "
                "execution requires the dry-run report to exist)."
            )
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        # DESIGN-002: refuse an unbound legacy report outright -- one that
        # predates this fix (wrong/missing report_schema, no
        # source_state_digest) was never bound to any specific state
        # snapshot in the first place, so there is nothing to verify it
        # against. This check does not itself require the migration lock
        # (it can never proceed to mutate anything either way), but it is
        # strictly EARLIER and cheaper than acquiring the lock only to
        # refuse immediately afterward.
        if (
            report.get("report_schema") != REPORT_SCHEMA_VERSION
            or not report.get("source_state_digest")
        ):
            raise LegacyReportMissingDigestError(
                f"The most recent dry-run report ({report_path}) predates "
                "DESIGN-002's source-state binding (missing/mismatched "
                "report_schema or source_state_digest). Refusing --execute "
                "against an unbound legacy report -- run a fresh --dry-run "
                "(and reconcile any adjudication file against the new "
                "report) before executing."
            )

        adjudication = self._load_adjudication(adjudication_path)

        applied = {
            "known_utc": 0,
            "known_local": 0,
            "adjudicated": 0,
            "left_ambiguous": 0,
            # SEC-CLOCKADR-9.12.0-026 (P2): counters for the ambiguous-bucket
            # scope gate -- see AdjudicationTable's class docstring.
            "non_ambiguous_override_refused": 0,
            "non_ambiguous_override_applied": 0,
        }
        # Per-record audit trail (SEC-CLOCKADR-9.12.0-026): every time a
        # decision resolves against a NON-ambiguous record -- refused or
        # explicitly overridden -- gets a distinguishing entry here, never
        # silent either way. Empty for an ordinary run (no non-ambiguous
        # overrides encountered).
        override_audit: List[Dict[str, Any]] = []

        with self.manager._migration_lock():
            state = self.manager._load_project_state_internal()

            # DESIGN-002 (Toji HIGH, CWE-367): bind execution to the EXACT
            # snapshot the report classified -- INSIDE the lock, BEFORE any
            # mutation (including backup creation, which happens further
            # below, only once both checks below pass).
            current_digest = _canonical_digest(state)
            if current_digest != report["source_state_digest"]:
                raise StateDriftError(
                    f"project-state.json has changed since the dry-run "
                    f"report ({report_path}) was generated "
                    f"(source_state_digest {report['source_state_digest']} "
                    f"!= current {current_digest}). Applying this report's "
                    "classified values to the current file risks writing a "
                    "stale value over a legitimate later update, or "
                    "misapplying an adjudicated ruling to a different "
                    "list-index record. Refusing --execute -- run a fresh "
                    "--dry-run and reconcile adjudication against it before "
                    "executing again."
                )

            mismatches = self._verify_records_bound_to_state(report["records"], state)
            if mismatches:
                raise RecordIdentityMismatchError(
                    "One or more classified records no longer match the "
                    "current state (checked independently of the "
                    "whole-state digest above). Refusing --execute -- run a "
                    "fresh --dry-run and reconcile adjudication against it "
                    "before executing again. Mismatches:\n  - "
                    + "\n  - ".join(mismatches)
                )

            backup_dir = self._create_backup()

            for record in report["records"]:
                path = record["path"]
                value = record["value"]
                bucket = record["bucket"]
                decision = adjudication.resolve(path, record)

                if decision is not None and bucket != Bucket.AMBIGUOUS.value:
                    # SEC-CLOCKADR-9.12.0-026: a decision (exact or bulk)
                    # resolving against a record the classifier did NOT
                    # bucket `ambiguous` requires an explicit escape hatch
                    # before it may apply -- otherwise an overbroad bulk
                    # pattern (or a mistaken exact entry) could silently
                    # override a HIGH-confidence known_utc/known_local
                    # classification with no trace. Never silent either way.
                    if decision.get("override_classifier_bucket"):
                        override_audit.append(
                            {
                                "path": path,
                                "bucket": bucket,
                                "disposition": decision.get("disposition"),
                                "action": "applied_non_ambiguous_override",
                            }
                        )
                        applied["non_ambiguous_override_applied"] += 1
                        print(
                            f"[i] Adjudication for {path} (bucket={bucket!r}) EXPLICITLY "
                            "overrides a non-ambiguous classifier bucket via "
                            "'override_classifier_bucket': true.",
                            file=sys.stderr,
                        )
                    else:
                        override_audit.append(
                            {
                                "path": path,
                                "bucket": bucket,
                                "disposition": decision.get("disposition"),
                                "action": "refused_non_ambiguous_override",
                            }
                        )
                        applied["non_ambiguous_override_refused"] += 1
                        print(
                            f"[!] Adjudication for {path} (bucket={bucket!r}) would override a "
                            "non-ambiguous classifier bucket without "
                            "'override_classifier_bucket': true -- REFUSED, falling back to "
                            "the record's own bucket-derived default instead of silently "
                            "applying this adjudication decision.",
                            file=sys.stderr,
                        )
                        # Fall through to the record's own bucket-derived
                        # default below, exactly as if nothing had resolved.
                        decision = None

                if decision is not None:
                    disposition = decision["disposition"]
                    if disposition == "known_local":
                        # v9.12.0 A6: an explicit per-decision `zone`
                        # override (exact or bulk) always wins over the
                        # migrator's globally-resolved `self._user_zone` --
                        # already validated against `zoneinfo` at LOAD time
                        # (`_load_adjudication()`), so this resolution can
                        # only fail if the zoneinfo database itself changed
                        # between load and execute (astronomically unlikely,
                        # still handled defensively, never silently ignored).
                        zone_override = decision.get("zone")
                        zone = self._user_zone
                        if zone_override:
                            try:
                                zone = ZoneInfo(zone_override)
                            except Exception as e:
                                print(
                                    f"[!] Adjudication for {path} specified zone "
                                    f"override {zone_override!r}, which no longer "
                                    f"resolves ({e}); leaving value untouched "
                                    "rather than silently falling back to a "
                                    "different zone than the USER specified.",
                                    file=sys.stderr,
                                )
                                applied["left_ambiguous"] += 1
                                continue
                        if zone is None:
                            print(
                                f"[!] Adjudication for {path} requested known_local "
                                "conversion, but no user zone is resolved -- leaving "
                                "value untouched.",
                                file=sys.stderr,
                            )
                            applied["left_ambiguous"] += 1
                            continue
                        new_value = self._localize_naive_to_utc(value, zone)
                        _set_by_path(state, path, new_value)
                        applied["adjudicated"] += 1
                        continue
                    if disposition == "known_utc":
                        new_value = value + "+00:00"
                        _set_by_path(state, path, new_value)
                        applied["adjudicated"] += 1
                        continue
                    if disposition == "permanently_exclude":
                        applied["left_ambiguous"] += 1
                        continue
                    # Unrecognized disposition -- unreachable via
                    # `_load_adjudication()` (validated at load time), kept
                    # as defense-in-depth against a future caller that
                    # constructs an AdjudicationTable directly. Never
                    # silently applied.
                    print(
                        f"[!] Unrecognized adjudication disposition {disposition!r} "
                        f"for {path}; leaving untouched.",
                        file=sys.stderr,
                    )
                    applied["left_ambiguous"] += 1
                    continue

                if bucket == Bucket.KNOWN_UTC.value:
                    new_value = value + "+00:00"
                    _set_by_path(state, path, new_value)
                    applied["known_utc"] += 1
                elif bucket == Bucket.KNOWN_LOCAL.value:
                    if self._user_zone is None:
                        print(
                            f"[!] {path} classified known-local, but no user "
                            "zone is resolved -- leaving untouched (never "
                            "guessing the execution host's zone).",
                            file=sys.stderr,
                        )
                        applied["left_ambiguous"] += 1
                        continue
                    new_value = self._localize_naive_to_utc(value, self._user_zone)
                    _set_by_path(state, path, new_value)
                    applied["known_local"] += 1
                else:
                    applied["left_ambiguous"] += 1

            # D8.1/D8.6: stamp the schema version.
            state["time_schema"] = TIME_SCHEMA_VERSION

            # Considered design decision (module docstring): seed a valid
            # work_streak block if none exists yet, so migration itself
            # never trips D7.6's fail-closed branch for a brand-new install.
            if "work_streak" not in state or not isinstance(state.get("work_streak"), dict):
                seeded = self.manager._default_work_streak()
                seeded["last_trusted_boundary_utc"] = self.manager.time_provider.utc_now().isoformat()
                seeded["last_updated"] = self.manager.time_provider.utc_now().isoformat()
                state["work_streak"] = seeded

            self.manager._atomic_write(state, self.manager.project_state_file)

        print("=== Time-Schema Migration: EXECUTE complete ===")
        print(f"  known-utc converted:   {applied['known_utc']}")
        print(f"  known-local converted: {applied['known_local']}")
        print(f"  adjudicated:           {applied['adjudicated']}")
        print(f"  left ambiguous:        {applied['left_ambiguous']}")
        print(f"  non-ambiguous overrides refused: {applied['non_ambiguous_override_refused']}")
        print(f"  non-ambiguous overrides applied: {applied['non_ambiguous_override_applied']}")
        print(f"Backup: {backup_dir}")

        return {
            "applied": applied,
            "backup_dir": str(backup_dir),
            "report_path": str(report_path),
            # SEC-CLOCKADR-9.12.0-026: per-record detail for every
            # non-ambiguous-bucket decision encountered (refused or
            # explicitly overridden). Empty on an ordinary run.
            "override_audit": override_audit,
        }

    # -- rollback ---------------------------------------------------------

    def rollback(self, backup_dir: Optional[Path] = None) -> None:
        """DESIGN-003 (Toji audit 2026-08-06, MEDIUM; CWE-362): restore
        project-state.json from a time-schema-migration backup through the
        SAME migration lock and atomic-replace primitive forward migration
        uses -- never a bare `shutil.copy2()` straight onto the live path
        outside any lock. Sequence:

        1. Locate and verify the backup BEFORE entering the mutation phase:
           it must parse as valid JSON, and (for a backup created after this
           fix) its current on-disk checksum must match the `.sha256`
           sidecar recorded at BACKUP-CREATION time -- catching corruption
           or tampering of the backup itself, not merely confirming it
           still parses.
        2. Perform the restore under `_migration_lock()`, via
           `ProjectStateManager._atomic_write()` (temp-file + fsync +
           `os.replace`) -- identical to the primitive `execute()` already
           uses for the forward write.
        3. Re-read the committed file and compare it against the restored
           content WHILE STILL HOLDING THE LOCK, so a concurrent writer
           racing the lock release can never be mistaken for a successful
           rollback.
        """
        backups_root = self.state_dir / "backups"
        if backup_dir is None:
            candidates = sorted(
                (
                    b for b in backups_root.glob("time-schema-migration_*")
                    if b.is_dir() and BACKUP_PATTERN.match(b.name)
                ),
                reverse=True,
            )
            if not candidates:
                raise FileNotFoundError(
                    f"No time-schema-migration backups found under {backups_root}"
                )
            backup_dir = candidates[0]
        else:
            backup_dir = Path(backup_dir)

        backup_file = backup_dir / "project-state.json"
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        # -- (1) verify BEFORE entering the mutation phase -----------------
        backup_checksum = self._compute_checksum(backup_file)
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                backup_state = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            raise BackupIntegrityError(
                f"Backup at {backup_file} is not valid JSON -- refusing to "
                f"roll back from a corrupt backup: {e}"
            ) from e

        sidecar = backup_file.parent / (backup_file.name + ".sha256")
        if sidecar.exists():
            recorded = sidecar.read_text(encoding="utf-8").strip()
            if recorded != backup_checksum:
                raise BackupIntegrityError(
                    f"Backup checksum sidecar mismatch for {backup_file}: "
                    f"recorded {recorded}, current {backup_checksum} -- the "
                    "backup file may have been modified or corrupted since "
                    "creation. Refusing to roll back."
                )
        else:
            # Pre-DESIGN-003 backups have no sidecar. Degrade to the
            # weaker (but never silent) guarantee: valid JSON, not
            # cross-verified against a value recorded at creation time.
            print(
                f"[!] No checksum sidecar found for {backup_file} "
                "(pre-DESIGN-003 backup) -- integrity confirmed only as "
                "valid JSON, not cross-verified against a value recorded "
                "at backup-creation time.",
                file=sys.stderr,
            )

        # -- (2) restore under the SAME lock + atomic primitive as forward
        #    migration; (3) verify the committed result while still holding
        #    the lock. ------------------------------------------------------
        with self.manager._migration_lock():
            self.manager._atomic_write(backup_state, self.manager.project_state_file)

            with open(self.manager.project_state_file, "r", encoding="utf-8") as f:
                committed_state = json.load(f)
            if committed_state != backup_state:
                raise BackupIntegrityError(
                    "Rollback verification failed: the committed "
                    "project-state.json content does not match the backup "
                    "that was restored, even though the atomic write "
                    "reported success. Refusing to report rollback as "
                    "successful."
                )

        print(f"[OK] Rolled back to backup: {backup_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol v9.12.0 A5 - Versioned legacy-state "
        "time_schema migration (IMPL-TIMESCHEMA-9.12.0-001)"
    )
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--dry-run", action="store_true",
        help="Classify naive timestamps and write an ambiguity/provenance "
             "report. Mutates NOTHING (ADR D8.4 default-safe entry point).",
    )
    action_group.add_argument(
        "--execute", action="store_true",
        help="Apply the migration (requires a prior --dry-run report).",
    )
    action_group.add_argument(
        "--rollback", action="store_true",
        help="Restore project-state.json from the most recent time-schema "
             "migration backup.",
    )
    parser.add_argument("--protocol-root", type=str, help="Protocol root directory")
    parser.add_argument(
        "--adjudication", type=str,
        help="Path to a USER adjudication JSON file (only used with --execute).",
    )

    args = parser.parse_args()

    protocol_root = Path(args.protocol_root).resolve() if args.protocol_root else Path(__file__).resolve().parent.parent

    dzp_markers = [protocol_root / ".protocol-state", protocol_root / "protocol.config.yaml"]
    if not all(marker.exists() for marker in dzp_markers):
        print(f"[ERROR] Invalid protocol root: {protocol_root}")
        print("  Directory must contain .protocol-state/ and protocol.config.yaml")
        sys.exit(1)

    migrator = TimeSchemaMigrator(protocol_root)

    if args.dry_run:
        migrator.dry_run()
    elif args.execute:
        adjudication_path = Path(args.adjudication).resolve() if args.adjudication else None
        try:
            migrator.execute(adjudication_path=adjudication_path)
        except (MigrationNotReadyError, UnboundMigrationReportError) as e:
            # DESIGN-002: UnboundMigrationReportError and its subclasses
            # (LegacyReportMissingDigestError, StateDriftError,
            # RecordIdentityMismatchError) get the same clean CLI
            # diagnostic-and-exit treatment as the pre-existing
            # MigrationNotReadyError, rather than an unhandled traceback.
            print(f"[ERROR] {e}")
            sys.exit(1)
    elif args.rollback:
        try:
            migrator.rollback()
        except (FileNotFoundError, BackupIntegrityError) as e:
            # DESIGN-003: a refused/corrupt backup gets the same clean CLI
            # diagnostic-and-exit treatment, not an unhandled traceback.
            print(f"[ERROR] {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
