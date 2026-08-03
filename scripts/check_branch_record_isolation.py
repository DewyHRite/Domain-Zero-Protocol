#!/usr/bin/env python3
"""
Branch-isolation prefix-divergence check (IMPL-001, Toji audit v9.9.3 -> v9.9.4, MEDIUM).

Problem this closes:
  `scripts/check_protected_append_only.py` enforces the append-only invariant WITHIN a
  single branch's own commit history (staged content must be a byte-prefix extension of
  HEAD). It has NO visibility into a *sibling* branch that independently extends the same
  shared protected-record prefix. On 2026-07-09 exactly this happened: `Main-v9.9.4` and
  `program-L` each appended DIFFERENT terminal session-record content for the same
  session (`session_20260707_203626`) starting at the same shared byte offset in
  `.protocol-state/dev-notes.md` (and `project-state.json`) -- a REPLACEMENT-style
  divergence relative to their common ancestor, not a pure append by either branch
  considered alone. Toji's recommended fix: "a check that rejects differing content at
  an existing protected-record prefix before branch publication."

What this script does (TWO independent checks, either can fail closed):

  Layer 1 -- structural (byte-prefix) invariant:
    1. Computes `git merge-base <base-ref> <compare-ref>` -- the last commit both
       branches share.
    2. Reads the record's blob at that merge-base ("the shared prefix baseline").
    3. Reads the record's blob on EACH ref.
    4. Verifies each ref's blob is a pure append-only extension of the merge-base blob
       (same byte-prefix invariant as check_protected_append_only.is_append_only, reused
       directly from that module -- see import below).
    If either ref rewrote or deleted bytes within the shared merge-base prefix, this is a
    cross-branch append-only VIOLATION: FAIL CLOSED, naming the file, the offending ref,
    and the first divergent line.

    If BOTH refs are pure append-only extensions of the merge-base (the normal case --
    each branch legitimately appended its own, disjoint new content after the point
    where the branches split), this layer PASSES.

  Layer 2 -- semantic "conflicting terminal records" check (added after the real
  2026-07-09 IMPL-001 incident showed Layer 1 alone is INSUFFICIENT): the actual
  incident was not a shared-prefix rewrite -- the session-end record for
  `session_20260707_203626` is entirely ABSENT from the merge-base (both files), so
  `Main-v9.9.4` and `program-L` each independently *appended a different, conflicting
  terminal record for the same session* past the common base. That is structurally a
  pure append on BOTH sides (Layer 1 says "clean"), yet the two branches now disagree
  about historical fact (32h30m/2-alerts vs 23h24m/0-alerts for the same session id).
  Layer 2 closes this gap:
    1. For each ref, takes the divergent TAIL of the record (content beyond the
       merge-base blob -- or, defensively, the whole blob if Layer 1 already flagged it
       as not a clean extension).
    2. Parses session-end record blocks out of that tail by header:
         dev-notes.md:        `## Work Session Ended - <ts>` blocks, with
                               `**Session ID:**` / `**Duration:**` / `**Alerts Issued:**`
         security-review.md:  `## Security Review - Session End - <ts>` blocks, with
                               `**Session ID:**` / `**Total Duration:**` /
                               `**Wellbeing Compliance:**` (`<n> breaks taken, <m> alerts
                               acknowledged`)
    3. Builds session_id -> normalized(end-ts, duration-in-minutes, alerts) per ref's
       tail, per file.
    4. If the SAME session_id appears in BOTH refs' tails for the SAME file with a
       DIFFERING comparable field, that is a semantic conflict: FAIL CLOSED, naming the
       session id, the file, and both refs' conflicting values.
  Parsing is deliberately fail-SOFT: a block that cannot be parsed (missing session id,
  or no comparable field extracted at all) is simply skipped -- it never manufactures a
  false-positive conflict, and Layer 1's structural check still runs independently
  regardless of Layer 2's parse success.

Scope:
  - .protocol-state/dev-notes.md
  - .protocol-state/security-review.md
  `.dzp-domain/domain.record.md` is intentionally OUT OF SCOPE: it is gitignored (never
  committed to git in any branch), so there is no shared git blob history to compare --
  each clone/branch maintains its own independent, untracked copy of that file, and
  cross-branch git-level comparison is not meaningful for it.

Usage:
  python scripts/check_branch_record_isolation.py <base-ref> [<compare-ref>]

    <base-ref>     required. e.g. a branch name, tag, or commit SHA (e.g. "program-L").
    <compare-ref>  optional. Defaults to "HEAD" (the current branch).

Intended use: run this BEFORE publishing, merging, or promoting either branch (e.g. as
part of the pre-release / pre-publication checklist), not on every routine commit --
unlike check_protected_append_only.py, this check requires TWO refs and is inherently a
cross-branch comparison, not a single-commit gate.

Exit codes:
  0 = clean under BOTH layers -- protected records are pure append-only extensions of
      merge-base(base_ref, compare_ref) with no conflicting terminal records.
  1 = one or more violations found under EITHER layer (structural rewrite, or a
      same-session-id conflicting terminal record) -- commit/publish/merge should be
      blocked until reconciled.
  2 = could not run the check at all (missing/invalid CLI args, not a git repository, or
      the merge-base of the two refs could not be resolved for a reason OTHER than the
      exit-3 orphan case below -- e.g. an unknown/unresolvable ref). F8 (CodeRabbit
      PR#109, P2): this used to collide with the clean-exit 0 above, making "the check
      passed" indistinguishable from "the check never ran" to a calling script.
      CI/publish callers MUST treat BOTH exit code 1 and exit code 2 as blocking -- only
      exit code 0 is a genuine clean pass.
  3 = SKIP (non-blocking) -- added for BUG-BRANCHISO-9.11.0-001 (v9.11.0, first live
      run of the SEC-BRANCHISO-001 publish gate). Both `base_ref` and `compare_ref`
      resolve to VALID commits in this repo, but `git merge-base` itself reports no
      common ancestor between them (git's own exit code 1 for `merge-base` -- see
      `git help merge-base`, EXIT STATUS). This is the DESIGNED, permanent state for
      two orphan branches with unrelated histories -- e.g. under the dev/release repo
      isolation split, every DZP-vX.Y.Z release branch is created via
      `git worktree add --orphan` (see docs/guides/DISTRO_RELEASE_WORKFLOW.md section
      3), so it can NEVER share history with the dev branch. An ancestry-based
      divergence check is not meaningful when there is no common ancestor to diff
      against -- this is the isolation-split analogue of the "comparison branch is
      entirely absent" skip already handled by the release-gate wrapper
      (`scripts/distro/dzp_publish_core.py::branch_record_isolation_guard_cli`), not a
      genuine execution failure. It is distinguished from exit 2 by checking BOTH refs
      resolve to valid commit objects first: if either ref is invalid/unresolvable,
      that is still "could not run" (exit 2), never this skip.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, Optional

# Reuse the byte-prefix invariant logic directly rather than re-implementing it, so the
# two checks (single-branch append-only vs. cross-branch prefix-divergence) can never
# silently drift on what "append-only" means.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_protected_append_only import _normalize, is_append_only  # noqa: E402

# .dzp-domain/domain.record.md is intentionally excluded -- see module docstring.
PROTECTED_RECORDS: tuple[str, ...] = (
    ".protocol-state/dev-notes.md",
    ".protocol-state/security-review.md",
)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _git_show(repo_root: Path, ref_path: str) -> Optional[bytes]:
    proc = subprocess.run(
        ["git", "show", ref_path],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def blob_at(repo_root: Path, ref: str, path: str) -> Optional[bytes]:
    """Content of `path` as committed on `ref`, or None if it doesn't exist there."""
    return _git_show(repo_root, f"{ref}:{path}")


def merge_base(repo_root: Path, ref_a: str, ref_b: str) -> Optional[str]:
    """The commit SHA of the last commit shared by `ref_a` and `ref_b`, or None."""
    proc = subprocess.run(
        ["git", "merge-base", ref_a, ref_b],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip()
    return sha or None


def _ref_is_valid_commit(repo_root: Path, ref: str) -> bool:
    """True iff `ref` resolves to a valid commit object in the repo at `repo_root`."""
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=str(repo_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def merge_base_is_unrelated_histories(repo_root: Path, ref_a: str, ref_b: str) -> bool:
    """True iff `ref_a` and `ref_b` BOTH resolve to valid commits in this repo, but
    `git merge-base` itself reports no common ancestor between them (git's own exit
    code 1 for `merge-base` -- distinct from exit 128/other codes for an invalid
    ref or a git-execution failure). This is the DESIGNED state for two orphan
    branches with unrelated histories (BUG-BRANCHISO-9.11.0-001) -- see module
    docstring, exit code 3.

    False whenever at least one ref does not resolve to a valid commit -- that case
    is always "could not run" (exit 2), never this skip, regardless of what
    `git merge-base` itself would report.
    """
    if not (_ref_is_valid_commit(repo_root, ref_a) and _ref_is_valid_commit(repo_root, ref_b)):
        return False
    proc = subprocess.run(
        ["git", "merge-base", ref_a, ref_b],
        cwd=str(repo_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 1


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
# Violation detection
# ---------------------------------------------------------------------------


def _first_divergent_line(base: bytes, other: bytes) -> int:
    """1-based line number of the first byte at which `other` diverges from `base`.

    Only meaningful/called once a violation (not append-only) is already established --
    used purely to make the failure message actionable.
    """
    base_n = _normalize(base)
    other_n = _normalize(other)
    limit = min(len(base_n), len(other_n))
    idx = 0
    while idx < limit and base_n[idx] == other_n[idx]:
        idx += 1
    return base_n[:idx].count(b"\n") + 1


def find_violations(
    repo_root: Path,
    base_ref: str,
    compare_ref: str,
    records: tuple[str, ...] = PROTECTED_RECORDS,
    _merge_base_sha: Optional[str] = None,
) -> list[str]:
    """Return violation messages for any protected record that diverged mid-prefix
    between `base_ref` and `compare_ref` relative to their common ancestor.

    Returns an empty list (soft-skip) if the merge-base itself cannot be computed
    (e.g. unrelated histories, unknown ref) -- this check fails closed on a DETECTED
    violation, but a ref-resolution problem is a separate, louder failure mode the
    caller should notice independently (e.g. `git merge-base` erroring) rather than
    being silently conflated with a content violation here.

    `_merge_base_sha` lets a caller that already resolved the merge-base (main(), to
    avoid a redundant `git merge-base` subprocess call and to distinguish "no
    merge-base" from "no violations" in its own messaging) pass it in directly;
    callers (including tests) normally omit it and let this function resolve it.
    """
    mb = _merge_base_sha if _merge_base_sha is not None else merge_base(repo_root, base_ref, compare_ref)
    if mb is None:
        return []

    violations: list[str] = []
    for path in records:
        base_blob = blob_at(repo_root, mb, path)
        if base_blob is None:
            continue  # record didn't exist at the common ancestor -- nothing shared yet

        for ref in (base_ref, compare_ref):
            ref_blob = blob_at(repo_root, ref, path)
            if ref_blob is None:
                # F7 (CodeRabbit PR#109, P2): previously silently `continue`d here,
                # deferring entirely to the single-branch append-only guard
                # (check_protected_append_only.py). But that guard only runs on the
                # branch performing the deletion at ITS OWN commit time -- it has no
                # visibility into a sibling branch's cross-branch comparison, and a
                # true `git rm` of a protected record is not append-only by any
                # definition. Flag it here as its own violation rather than trusting
                # a guard that never actually inspects this cross-branch relationship.
                violations.append(
                    f"{path}: ref '{ref}' has the protected record entirely REMOVED "
                    f"relative to merge-base({base_ref}, {compare_ref}) -- a cross-branch "
                    f"deletion is not append-only and is not guaranteed to have been "
                    f"caught by the single-branch guard"
                )
                continue
            if not is_append_only(base_blob, ref_blob):
                line = _first_divergent_line(base_blob, ref_blob)
                violations.append(
                    f"{path}: ref '{ref}' rewrote/removed bytes within the shared "
                    f"merge-base({base_ref}, {compare_ref}) prefix (first divergence at "
                    f"line {line})"
                )
    return violations


# ---------------------------------------------------------------------------
# Layer 2: semantic "conflicting terminal records" check
# ---------------------------------------------------------------------------

# Session-end record block headers, one per protected record file.
_DEV_NOTES_HEADER_RE = re.compile(r"^##\s*Work Session Ended\s*-\s*(?P<ts>\S+)\s*$", re.MULTILINE)
_SEC_REVIEW_HEADER_RE = re.compile(
    r"^##\s*Security Review\s*-\s*Session End\s*-\s*(?P<ts>.+?)\s*$", re.MULTILINE
)

_SESSION_ID_RE = re.compile(r"\*\*Session ID:\*\*\s*(\S+)")
# dev-notes.md: "**Duration:** 32 hours 30 minutes"
_DEV_DURATION_RE = re.compile(r"\*\*Duration:\*\*\s*(.+)")
_DEV_ALERTS_RE = re.compile(r"\*\*Alerts Issued:\*\*\s*(\d+)")
# security-review.md: "**Total Duration:** 32 hours 30 minutes"
_SEC_DURATION_RE = re.compile(r"\*\*Total Duration:\*\*\s*(.+)")
# security-review.md: "**Wellbeing Compliance:** 0 breaks taken, 2 alerts acknowledged"
_WELLBEING_RE = re.compile(
    r"\*\*Wellbeing Compliance:\*\*\s*\d+\s*breaks?\s*taken,\s*(\d+)\s*alerts?\s*acknowledged",
    re.IGNORECASE,
)

_HOURS_RE = re.compile(r"(\d+)\s*hours?", re.IGNORECASE)
_MINUTES_RE = re.compile(r"(\d+)\s*minutes?", re.IGNORECASE)


def _duration_to_minutes(text: str) -> Optional[int]:
    """Normalize a free-form duration string ("32 hours 30 minutes", "13 minutes") to
    total minutes. Returns None if neither an hours nor a minutes component is found
    (fail-soft -- an unparseable duration is simply not comparable, not an error).
    """
    h = _HOURS_RE.search(text)
    m = _MINUTES_RE.search(text)
    if not h and not m:
        return None
    return (int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0)


class SessionRecord(NamedTuple):
    session_id: str
    end_ts: str
    duration_minutes: Optional[int]
    raw_duration: str
    alerts: Optional[int]


def _divergent_tail(base_blob: bytes, ref_blob: bytes) -> bytes:
    """The bytes of `ref_blob` that are NEW relative to `base_blob` (content past the
    shared byte-prefix). If `ref_blob` is not a clean superset of `base_blob` (Layer 1
    would already flag this as a structural violation), fall back to scanning the
    WHOLE ref blob defensively so Layer 2 still has a chance to surface a session
    conflict rather than silently missing it because the prefix math doesn't apply.
    """
    base_n = _normalize(base_blob)
    ref_n = _normalize(ref_blob)
    if ref_n.startswith(base_n):
        return ref_n[len(base_n):]
    return ref_n


def _parse_session_records(text: str, path: str) -> dict[str, SessionRecord]:
    """Parse session-end record blocks out of `text` (expected to be the divergent tail
    of `path`), returning {session_id: SessionRecord}.

    Fails SOFT: any block missing a Session ID, or with no comparable field extractable
    at all (duration AND alerts both unparseable), is silently skipped -- never raises,
    never manufactures a record that would produce a false-positive conflict later.
    """
    basename = Path(path).name.lower()
    if basename == "dev-notes.md":
        header_re = _DEV_NOTES_HEADER_RE
    elif basename == "security-review.md":
        header_re = _SEC_REVIEW_HEADER_RE
    else:
        return {}

    records: dict[str, SessionRecord] = {}
    headers = list(header_re.finditer(text))
    for i, header_match in enumerate(headers):
        block_start = header_match.end()
        block_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[block_start:block_end]

        sid_match = _SESSION_ID_RE.search(block)
        if not sid_match:
            continue  # fail-soft: no session id in this block
        session_id = sid_match.group(1).strip()

        if basename == "dev-notes.md":
            dur_match = _DEV_DURATION_RE.search(block)
            alerts_match = _DEV_ALERTS_RE.search(block)
        else:
            dur_match = _SEC_DURATION_RE.search(block)
            alerts_match = _WELLBEING_RE.search(block)

        raw_duration = dur_match.group(1).strip() if dur_match else ""
        duration_minutes = _duration_to_minutes(raw_duration) if dur_match else None
        alerts = int(alerts_match.group(1)) if alerts_match else None

        if duration_minutes is None and alerts is None:
            continue  # fail-soft: session id present but nothing comparable parsed

        # Last block with this session_id in the tail wins (mirrors "most recent entry
        # is authoritative" -- and duplicate session-end blocks within a single ref's
        # own tail are not this layer's concern).
        records[session_id] = SessionRecord(
            session_id=session_id,
            end_ts=header_match.group("ts").strip(),
            duration_minutes=duration_minutes,
            raw_duration=raw_duration,
            alerts=alerts,
        )
    return records


def _records_conflict(a: SessionRecord, b: SessionRecord) -> bool:
    """True iff `a` and `b` (same session_id) disagree on at least one field that is
    actually comparable (present/parsed on BOTH sides). Fields unparseable on either
    side are simply excluded from the comparison (fail-soft) rather than treated as a
    mismatch -- so a partially-parsed block never manufactures a false positive.
    """
    comparable_diffs = []
    if a.end_ts and b.end_ts:
        comparable_diffs.append(a.end_ts != b.end_ts)
    if a.duration_minutes is not None and b.duration_minutes is not None:
        comparable_diffs.append(a.duration_minutes != b.duration_minutes)
    if a.alerts is not None and b.alerts is not None:
        comparable_diffs.append(a.alerts != b.alerts)
    return any(comparable_diffs)


def find_semantic_conflicts(
    repo_root: Path,
    base_ref: str,
    compare_ref: str,
    records: tuple[str, ...] = PROTECTED_RECORDS,
    _merge_base_sha: Optional[str] = None,
) -> list[str]:
    """Return violation messages for any session_id that appears in BOTH refs'
    divergent tails of the same protected record with CONFLICTING comparable values
    (Layer 2 -- see module docstring). Same id + identical values, or different ids
    entirely, are not violations. Soft-skips (returns []) if the merge-base cannot be
    resolved, matching find_violations()'s behavior.
    """
    mb = _merge_base_sha if _merge_base_sha is not None else merge_base(repo_root, base_ref, compare_ref)
    if mb is None:
        return []

    violations: list[str] = []
    for path in records:
        base_blob = blob_at(repo_root, mb, path) or b""
        a_blob = blob_at(repo_root, base_ref, path)
        b_blob = blob_at(repo_root, compare_ref, path)
        if a_blob is None or b_blob is None:
            continue  # missing entirely on one side -- Layer 1 / append-only guard's concern

        a_tail = _divergent_tail(base_blob, a_blob).decode("utf-8", errors="replace")
        b_tail = _divergent_tail(base_blob, b_blob).decode("utf-8", errors="replace")

        a_records = _parse_session_records(a_tail, path)
        b_records = _parse_session_records(b_tail, path)

        for session_id in sorted(set(a_records) & set(b_records)):
            ra, rb = a_records[session_id], b_records[session_id]
            if _records_conflict(ra, rb):
                violations.append(
                    f"{path}: session '{session_id}' has CONFLICTING terminal records — "
                    f"'{base_ref}' (end={ra.end_ts}, duration={ra.raw_duration}, "
                    f"alerts={ra.alerts}) vs '{compare_ref}' (end={rb.end_ts}, "
                    f"duration={rb.raw_duration}, alerts={rb.alerts})"
                )
    return violations


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None, repo_root: Optional[Path] = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    _usage = "Usage: python scripts/check_branch_record_isolation.py <base-ref> [<compare-ref>]"

    if not args:
        print(_usage, file=sys.stderr)
        return 2

    base_ref = args[0]
    compare_ref = args[1] if len(args) > 1 else "HEAD"

    # BUG-BRANCHISO-9.11.0-001 review observation: any argv token was previously
    # accepted positionally, including flag-like tokens (e.g. '--help'), which were
    # then handed straight to `git merge-base` as a literal ref name. Reject
    # obviously flag-like arguments up front with usage text -- "could not run" (exit
    # 2), consistent with the existing missing-args case above, never a silent
    # attempt to resolve '--help' as a branch/tag/SHA.
    if base_ref.startswith("-") or compare_ref.startswith("-"):
        bad = base_ref if base_ref.startswith("-") else compare_ref
        print(f"{_usage}\n       (got unexpected flag-like argument: '{bad}')", file=sys.stderr)
        return 2

    if repo_root is None:
        repo_root = _repo_toplevel()
        if repo_root is None:
            # F8 (CodeRabbit PR#109, P2): was `return 0`, colliding with the clean-exit
            # 0 below. "Could not run" must be distinguishable from "ran and passed".
            print("[branch-isolation] not a git repository — could not run", file=sys.stderr)
            return 2

    mb = merge_base(repo_root, base_ref, compare_ref)
    if mb is None:
        # BUG-BRANCHISO-9.11.0-001 (v9.11.0): distinguish the DESIGNED orphan-branch
        # case (both refs valid, but no common ancestor exists -- e.g. every
        # DZP-vX.Y.Z release branch under the dev/release repo isolation split) from
        # a genuine "could not run" failure (invalid/unresolvable ref, git execution
        # failure, etc.). Only the former becomes the new loud, non-blocking skip.
        if merge_base_is_unrelated_histories(repo_root, base_ref, compare_ref):
            print(
                f"[branch-isolation] SKIP -- comparison branch '{base_ref}' exists but "
                f"shares no history with '{compare_ref}' (orphan release branch under "
                f"the dev/release isolation split); ancestry-based divergence check not "
                f"applicable.",
                file=sys.stderr,
            )
            return 3
        # F8 (CodeRabbit PR#109, P2): was `return 0` (see above) -- an unresolvable
        # merge-base means this check never actually ran, not that it passed clean.
        print(
            f"[branch-isolation] could not compute merge-base of '{base_ref}' and "
            f"'{compare_ref}' — could not run (check the refs exist and share history); "
            f"CI/publish callers must treat this as blocking, not a clean pass",
            file=sys.stderr,
        )
        return 2

    structural_violations = find_violations(repo_root, base_ref, compare_ref, _merge_base_sha=mb)
    semantic_violations = find_semantic_conflicts(repo_root, base_ref, compare_ref, _merge_base_sha=mb)

    if structural_violations:
        bullet = "\n".join(f"    - {v}" for v in structural_violations)
        print(
            "[branch-isolation] BLOCKED (Layer 1: structural) — protected record(s)\n"
            "   diverged with a mid-shared-prefix rewrite between branches\n"
            "   (replacement-style edit, not a pure append past the common ancestor):\n"
            f"{bullet}\n\n"
            "   Each branch's protected-record history must extend the shared\n"
            "   ancestor's content by pure append only. Fix: reconcile manually\n"
            "   (choose one branch's version as canonical, and re-append the other\n"
            "   branch's unique additions as a new dated entry rather than\n"
            "   overwriting the shared bytes), then re-run this check before\n"
            "   merging / publishing / promoting either branch.\n",
            file=sys.stderr,
        )

    if semantic_violations:
        bullet = "\n".join(f"    - {v}" for v in semantic_violations)
        print(
            "[branch-isolation] BLOCKED (Layer 2: semantic) — both branches\n"
            "   independently appended CONFLICTING terminal records for the SAME\n"
            "   session id past their common ancestor (each side is individually a\n"
            "   pure append, so Layer 1 alone would miss this):\n"
            f"{bullet}\n\n"
            "   Fix: determine the authoritative values (e.g. from project-state.json\n"
            "   session history / wellbeing-monitor invariants), then append a\n"
            "   RECONCILIATION note to each branch's lineage documenting which values\n"
            "   are authoritative and why — never rewrite either branch's existing\n"
            "   entry. Re-run this check before merging / publishing / promoting\n"
            "   either branch.\n",
            file=sys.stderr,
        )

    if structural_violations or semantic_violations:
        return 1

    print(
        f"[branch-isolation] OK — protected records are pure append-only extensions "
        f"of merge-base({base_ref}, {compare_ref}) with no conflicting terminal records",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
