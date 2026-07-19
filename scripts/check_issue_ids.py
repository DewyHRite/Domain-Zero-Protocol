#!/usr/bin/env python3
"""FEAT-IDGOV-001 Phase E -- fail-closed enforcement gate for the issue-id
registry (.protocol-state/issue-registry.jsonl). Runs at pre-commit (early
feedback) and CI (authoritative, --ci mode). This module currently implements:

  E1 - skeleton + a LINE-WISE append-only invariant on the registry file
       (the registry only ever grows; a previously-committed line must remain,
       unmodified and in order, as a prefix of the new version). Mirrors the
       byte-prefix technique in scripts/check_protected_append_only.py, but
       line-wise (JSONL rows), not raw bytes.
  E2 - registry-CONTENT invariants (uniqueness of assign ids, grammar,
       monotonic seq, rev-continuity, transition-legality) via REUSE of
       idgov.engine.validate() -- never reimplemented here (DRY).
  E3 - writer-authority. idgov.engine.validate() ALREADY enforces this for
       both `assign` rows (engine.py ~L141-144, `is_authorized(writer,
       family)`) and `transition` rows (engine.py ~L156-159, added in the
       Phase C re-review remediation "validate() checks writer-authority on
       transition rows too"). E3 is therefore satisfied entirely by the E2
       reuse -- no additional gate code was needed; see
       tests/test_check_issue_ids.py::TestWriterAuthority for the dedicated
       regression proof.

  E4 - mint-before-cite. A WELL-FORMED issue id (grammar.is_wellformed())
       newly cited in the ADDED lines of a changed corpus prose file (see
       DEFAULT_CORPUS_PATHS) must already exist as an `assign` row in the
       staged registry -- otherwise the commit is blocked ("mint it first").
       Reuses the git-plumbing helpers below (_baseline_and_candidate) against
       each corpus path instead of the registry path.
  E5 - malformed-id hard block in prose (Sukuna F1). A token matching
       grammar.ID_SHAPED_RE but NOT grammar.is_wellformed(), newly introduced
       in a corpus prose file's ADDED lines, is a hard grammar block -- this
       is the exact bare-`SEC-013` collision-regression class. Pre-existing/
       unchanged bare ids on untouched lines are never flagged (added-lines-
       only scoping handles this for free).
       Go-live prep (real-corpus dry-run finding, 42 FPs, all digitless):
       E5's block is narrowed by a DIGIT-GATE -- a token is only flagged
       malformed if it contains at least one ASCII digit. A real issue id
       ALWAYS carries a numeric SEQ (grammar.py's SEQ production requires
       3+ digits), so a digitless FAMILY-WORD token
       (bare `SEC-ID`, placeholder notation `SEC-NNN`/`MF-N`, a subsystem-
       prefix reference `SEC-GRAPH`/`SEC-CORTEX`) can never be a real OR a
       bare-malformed id -- it is generic prose vocabulary that merely looks
       id-shaped. This is a security-preserving relaxation: every id this
       check must still catch (a real bare id, a version-but-no-seq citation
       like `SEC-DZPUP-9.9.5`) has a digit and is unaffected. See
       _has_seq_digit(). On top of the digit-gate, an explicit, config-driven
       `issue_governance.id_term_allowlist` (protocol.config.yaml) exempts
       exact-match (case-insensitive) tokens too -- covers the rare WITH-digit
       generic term the digit-gate itself would not catch. See
       _is_id_term_allowlisted().
  E4 and E5 share ONE locate-then-classify token scan (_iter_corpus_citations)
  so a citation can never be found by one check and missed by the other: every
  token located by grammar.ID_SHAPED_RE.finditer() is classified with
  grammar.is_wellformed() -- wellformed-and-unminted is E4's concern,
  not-wellformed is E5's. No grammar regex is re-declared here (DRY, single
  source of grammar = idgov.grammar).
  E6 - prose-escape exemptions, applied BEFORE E4/E5 token location so an
       illustrative/quoted id never trips either check:
         (a) inline backtick spans + fenced code blocks (``` / ~~~) --
             _scannable_fragments() strips/skips these before scanning.
         (b) an `<!-- idgov:illustrative -->` line marker -- exempts the
             WHOLE line carrying the marker (not just text after it, for
             simplicity) PLUS the entire next added line. Does not persist
             beyond that.
         (c) corpus-PATH exclusions (DEFAULT_ESCAPE_PATH_EXCLUDES) -- a
             corpus path matching one of these globs/literals is skipped
             entirely, never scanned. Currently moot for DEFAULT_CORPUS_PATHS
             (which contains only the 3 protected docs, none of which match),
             but kept config-ready: when E7 widens corpus_paths (e.g. to
             CLAUDE.md's changelog or docs/superpowers/**), the exclusion
             list is already in place.

E7 - protocol.config.yaml `issue_governance:` config block wiring. Settings
     (enabled, registry_path, families, corpus_paths, escape_path_excludes,
     override_env) are read from protocol.config.yaml at startup via
     load_issue_governance_settings(), mirroring the PyYAML-if-available,
     size-guarded, try/except mechanism in
     check_protected_append_only.py::_load_config() exactly (repo
     consistency -- no new YAML-reading approach introduced). ANY config
     problem (file missing, block missing/malformed, oversized, PyYAML
     unavailable, parse error) falls back to the hardcoded
     DEFAULT_REGISTRY_PATH / DEFAULT_CORPUS_PATHS /
     DEFAULT_ESCAPE_PATH_EXCLUDES / OVERRIDE_ENV / idgov.grammar.FAMILIES
     module constants below -- fail-SAFE, never fail-open: enforcement is
     NEVER silently disabled by a config problem, only by an explicit,
     readable `enabled: false`. A resolved `families` list that diverges
     from idgov.grammar.FAMILIES (the engine's sole authority for id
     recognition -- config can never widen or narrow it) triggers a loud
     startup warning rather than changing gate behavior. `id_term_allowlist`
     (default `[]`) is an additional E5-only settings key -- see the E5
     go-live-prep note above -- of exact-match (case-insensitive) id-shaped
     terms to exempt from the malformed-id block on top of the digit-gate.

Phase E re-review remediation (Megumi Tier-3 findings, closed this pass):

  SEC-IDGOV-E-001 (P1, CWE-436) - fence-state cross-commit desync.
      _scannable_fragments() used to always start with in_fence=False, so a
      baseline ending in a DANGLING (unclosed) fence desynced the scan of the
      newly-added tail: the added tail's own closing fence line was mistaken
      for a fresh opening fence, and the prose line right after it was then
      wrongly treated as "inside a fence" and skipped, even though the
      rendered document shows it as live prose. Fixed by seeding the added-
      lines scan's starting in_fence state from the BASELINE's own cumulative
      fence parity (_fence_state()) -- but ONLY when _added_lines_with_offset
      found a clean line-prefix (the normal append-only shape); when it falls
      back to scanning the whole candidate as "added" (a mid-file rewrite),
      the scan legitimately starts from the true top of the file, so the seed
      is False in that case, never the baseline's tail state.
  SEC-IDGOV-E-002 (P2, CWE-693) - audits/** missing from corpus (USER
      decision: implement now). `corpus_paths` entries may now be a glob
      pattern (e.g. `audits/**`), not just an exact path. Glob entries are
      resolved against the CHANGED files in this diff range (git plumbing has
      no way to enumerate "files under a glob" other than diffing) --
      see _changed_files() / _resolve_corpus_targets(). Exact entries keep
      their original behavior (always attempted; a no-op if unchanged).
  SEC-IDGOV-E-004 (P2, CWE-178) - case-insensitive locate, case-sensitive
      classify. The single-source grammar.ID_SHAPED_RE locator is uppercase-
      only, so a lowercase/mixed-case id-shaped token (e.g. `sec-013`) was
      never even LOCATED, escaping both E4 and E5 entirely. Fixed with a
      LOCAL, gate-only case-insensitive locator built from grammar.FAMILIES
      (grammar.py itself is NOT modified -- single source of truth for what
      counts as well-formed stays exactly grammar.is_wellformed()). Every
      token this locator finds is still classified with the case-SENSITIVE
      grammar.is_wellformed() -- a lowercase hit can therefore only ever
      classify as malformed (E5), never as a false well-formed match, because
      a real minted id is always uppercase by construction (grammar.format_id).
  SEC-IDGOV-E-003 (P2, CWE-807) - capped chained `idgov:illustrative` markers.
      Unbounded marker chaining could exempt unlimited real citations. Capped
      at _ILLUSTRATIVE_MARKER_CAP (3) markers per corpus file per commit; past
      the cap, a loud stderr warning is emitted and further markers in that
      file no longer exempt anything (their citations are scanned normally).
  SEC-IDGOV-E-007 (P2, CWE-16) - warn on corpus/escape overlap + narrowed
      corpus. A startup warning (same style as the families-drift warning)
      now fires when a resolved corpus_paths entry is itself shadowed by a
      resolved escape_path_excludes entry (it can never be scanned), or when
      corpus_paths resolves to empty -- both are non-fatal (the gate still
      runs), closing the "config can silently narrow enforcement with no
      signal" gap. See _corpus_escape_overlap_warnings().
  E-008 - a git/config failure during startup (before the main _run_checks
      try/except) now yields the same clean "[idgov-gate] INTERNAL ERROR
      (fail-closed, blocking)" message instead of a raw traceback; both paths
      remain fail-CLOSED (nonzero exit) either way -- this is a robustness/UX
      fix, not a security-behavior change.
  SEC-IDGOV-E-009 (P3) - _lines() now splits on "\n" only (after stripping
      \r, mirroring check_protected_append_only.py's _normalize + explicit-
      split technique) instead of str.splitlines(), which also treats \v,
      \f, \x1c-\x1e, \x85, U+2028 and U+2029 as line boundaries -- a broader
      Unicode line-boundary set than git's own \n-only (or \r\n-normalized)
      line model, which could silently desync this gate's line-wise view of
      a file from git's actual diff view on content containing those rare
      bytes. Trade-off (accepted, mirrors the sibling guard's own accepted
      design): a lone `\r` not paired with `\n` (classic pre-OSX Mac line
      ending) now MERGES with the following line rather than splitting --
      unrealistic in a git-normalized repo and already an equivalent accepted
      risk in check_protected_append_only.py's own _normalize().

  SEC-IDGOV-E-005 (P2) - id split across two lines: ASSESSED, left as an
      ACCEPTED P3 RESIDUAL (not fixed this pass). Reliably detecting "a
      trailing line-wrapped fragment of an id continues on the next added
      line" without materially widening false-positive surface on ordinary
      wrapped markdown prose (e.g. a sentence that happens to end in a
      hyphenated word right before a line wrap) would require a proper
      markdown-aware line-joiner, not a bounded regex tweak. The registry is
      permanent append-only audit history, not hand-authored prose that gets
      artificially word-wrapped -- a real citation being split exactly at an
      id boundary across two lines is a low-incentive, low-likelihood evasion
      (it also renders as visibly broken/non-human-legible in the source, so
      it does not read as "illustrative" the way E6's exemptions do). Revisit
      if a real citation is ever observed split this way in practice.

Override (backfill / migration / authorized exception): set
DZP_ALLOW_ISSUE_ID_OVERRIDE=1. Independent of the pre-existing 4 DZP override
env vars (DZP_ALLOW_PROTECTED_REWRITE, DZP_ALLOW_PROTOCOL_EDIT,
DZP_ALLOW_TOJI_STUB_UNVERIFIED, DZP_ALLOW_MISSING_APPEND_GUARD). The bypass is
always printed to stderr -- never silent.

Exit codes: 0 = clean (or overridden / not a git repo), 1 = violation(s)
found -> block commit / fail CI.

See docs/superpowers/plans/2026-07-14-issue-id-governance.md Phase E Tasks
E1/E2/E3 and docs/superpowers/specs/2026-07-13-issue-id-governance-design.md.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from idgov import engine, grammar, registry  # noqa: E402

DEFAULT_REGISTRY_PATH = ".protocol-state/issue-registry.jsonl"
OVERRIDE_ENV = "DZP_ALLOW_ISSUE_ID_OVERRIDE"
DEFAULT_CI_BASE_REF = "origin/main"

# E4/E5/E6 -- hardcoded fallback defaults, config-ready. E7's
# load_issue_governance_settings() sources these from protocol.config.yaml's
# `issue_governance:` block when present/readable; these module constants
# remain the FALLBACK on any config problem (same names/shapes so downstream
# callers -- e.g. tests calling _is_path_escape_excluded() with only one
# arg -- do not change).
DEFAULT_CORPUS_PATHS: tuple[str, ...] = (
    ".protocol-state/dev-notes.md",
    ".protocol-state/security-review.md",
    ".dzp-domain/domain.record.md",
    # SEC-IDGOV-E-002: Toji audit reports are a citation surface too. This is
    # a GLOB entry, resolved against the CHANGED files in the diff range (see
    # _resolve_corpus_targets()), not an exact git-show path like the 3
    # entries above. Safe to enable ahead of the Phase G1 hook-wiring (which
    # runs after Phase F's history backfill populates the registry) -- see
    # the matching comment in protocol.config.yaml issue_governance.corpus_paths.
    "audits/**",
)

# (c) corpus-PATH escape exclusions. Glob patterns are matched with fnmatch
# (case-sensitive); plain strings are matched exactly. CLAUDE.md's changelog
# is one huge block of historical ids from every past release, so for now the
# whole file is excluded wholesale rather than trying to carve out just the
# changelog region -- a coarse default E7 may refine (e.g. a byte/line-range
# exclusion instead of a whole-file one).
DEFAULT_ESCAPE_PATH_EXCLUDES: tuple[str, ...] = (
    "docs/superpowers/specs/**",
    "docs/superpowers/plans/**",
    "CLAUDE.md",
    "protocol/CLAUDE.md",
)

# Go-live prep: E5-only exact-match (case-insensitive) exemption list for
# id-shaped tokens that are known generic terms/placeholders/subsystem
# references, not real issue ids. Applied ON TOP OF the digit-gate (see
# _has_seq_digit()) -- covers the rare WITH-digit generic term the digit-gate
# itself would not exempt. Empty by default: the digit-gate alone is the
# workhorse fix; this is an escape hatch for exceptions found in practice.
DEFAULT_ID_TERM_ALLOWLIST: tuple[str, ...] = ()

# ---------------------------------------------------------------------------
# E7: protocol.config.yaml `issue_governance:` config block wiring
# ---------------------------------------------------------------------------

# Mirrors check_protected_append_only.py's SEC-GUARD-004 config size guard --
# protocol.config.yaml is a small YAML file; a multi-MB payload is never
# legitimate and should not be read (fail-SAFE fallback instead).
_MAX_CONFIG_BYTES = 1_000_000


@dataclass(frozen=True)
class IssueGovernanceSettings:
    """Effective issue_governance settings, resolved from protocol.config.yaml
    (or the hardcoded module-constant fallbacks on any config problem)."""

    enabled: bool
    registry_path: str
    families: tuple[str, ...]
    corpus_paths: tuple[str, ...]
    escape_path_excludes: tuple[str, ...]
    override_env: str
    id_term_allowlist: tuple[str, ...] = DEFAULT_ID_TERM_ALLOWLIST
    warnings: tuple[str, ...] = ()


def _load_config(config_path: Path) -> Optional[dict]:
    """Load and return the `issue_governance` section of `config_path`.

    Returns None if the file does not exist, exceeds the size guard, PyYAML
    is unavailable, the key is absent/not-a-mapping, or any read/parse error
    occurs -- caller falls back to the hardcoded module-constant defaults
    (fail-SAFE, never fail-open). This mirrors
    check_protected_append_only.py::_load_config() EXACTLY (same
    PyYAML-if-available / size-guard / try-except-fallback shape) so the repo
    has one consistent config-reading mechanism, not two.
    """
    if not config_path.is_file():
        return None
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
        block = raw.get("issue_governance")
        if not isinstance(block, dict):
            return None
        return block
    except Exception:  # noqa: BLE001 -- any YAML/IO error -> fall back
        return None


def _resolve_config_path(repo_root: Path, config_path: Optional[Path]) -> Path:
    """Return the effective config path: explicit arg > repo_root/protocol.config.yaml."""
    if config_path is not None:
        return config_path
    return repo_root / "protocol.config.yaml"


def _validated_str_tuple(raw: object, default: tuple[str, ...]) -> tuple[str, ...]:
    """Validate that `raw` is a list of non-empty strings; else fall back to
    `default`. Mirrors check_protected_append_only.py's M2 `paths` validation
    (never iterate a bare scalar -- a string would be walked
    character-by-character, silently corrupting the list) so a malformed
    config value can never widen, narrow, or disable enforcement by accident."""
    if isinstance(raw, (list, tuple)):
        parsed: list[str] = []
        for item in raw:
            if not isinstance(item, str):
                return default
            s = item.strip()
            if s:
                parsed.append(s)
        return tuple(parsed) if parsed else default
    return default


def _corpus_escape_overlap_warnings(
    corpus_paths: tuple[str, ...], escape_path_excludes: tuple[str, ...],
) -> list[str]:
    """SEC-IDGOV-E-007: non-fatal startup warnings (same style as the
    families-drift warning above) for two ways config can silently narrow
    enforcement coverage with no other signal:

      (a) a corpus_paths entry is itself matched by an escape_path_excludes
          entry -- that corpus path can NEVER be scanned (a silent coverage
          hole), and
      (b) corpus_paths is empty -- NO prose files are covered by
          mint-before-cite/malformed-id enforcement this run.

    Note: _validated_str_tuple() above deliberately falls back to the
    hardcoded DEFAULT_CORPUS_PATHS whenever a config-supplied corpus_paths
    list parses to empty (a malformed config value must never accidentally
    disable enforcement) -- so case (b) is not reachable through
    load_issue_governance_settings() alone today; it is exercised directly
    against this function (e.g. by a future programmatic caller, or a
    regression test) so the signal exists and is proven correct the moment
    corpus_paths CAN legitimately resolve empty."""
    warnings: list[str] = []
    overlapping = [p for p in corpus_paths if _is_path_escape_excluded(p, escape_path_excludes)]
    for p in overlapping:
        warnings.append(
            f"[idgov-gate] WARNING: issue_governance.corpus_paths entry '{p}' "
            "is also matched by an escape_path_excludes pattern -- it will "
            "NEVER be scanned (silent coverage hole, SEC-IDGOV-E-007)."
        )
    if not corpus_paths:
        warnings.append(
            "[idgov-gate] WARNING: issue_governance.corpus_paths resolved to "
            "empty -- NO prose files are covered by mint-before-cite/"
            "malformed-id enforcement this run (SEC-IDGOV-E-007)."
        )
    elif overlapping and len(overlapping) == len(corpus_paths):
        warnings.append(
            "[idgov-gate] WARNING: every issue_governance.corpus_paths entry "
            "is shadowed by escape_path_excludes -- prose citation coverage "
            "is effectively EMPTY this run (SEC-IDGOV-E-007)."
        )
    return warnings


def load_issue_governance_settings(
    repo_root: Path, config_path: Optional[Path] = None,
) -> IssueGovernanceSettings:
    """Resolve effective issue_governance settings from protocol.config.yaml,
    falling back to the hardcoded module defaults (DEFAULT_REGISTRY_PATH /
    DEFAULT_CORPUS_PATHS / DEFAULT_ESCAPE_PATH_EXCLUDES / OVERRIDE_ENV / the
    engine's idgov.grammar.FAMILIES) on ANY config problem -- missing file,
    missing/malformed `issue_governance` key, oversized file, PyYAML
    unavailable, or a parse error.

    Fail-SAFE, never fail-open: a config problem never disables enforcement,
    it only falls back to the secure defaults, loudly (a warning is attached
    to the returned settings for the caller to print). The ONLY way to
    disable the gate is an explicit, present, readable `enabled: false`.

    A resolved `families` list that diverges from idgov.grammar.FAMILIES (the
    engine's sole authority for id recognition -- config can never widen or
    narrow it) also attaches a warning, without changing gate behavior.
    """
    cfg_file = _resolve_config_path(repo_root, config_path)
    block = _load_config(cfg_file)
    warnings: list[str] = []
    engine_families = tuple(sorted(grammar.FAMILIES))

    if block is None:
        warnings.append(
            f"[idgov-gate] WARNING: {cfg_file} has no readable "
            "`issue_governance` block -- falling back to hardcoded secure "
            "defaults (enforcement remains ACTIVE, not disabled)."
        )
        enabled = True
        registry_path = DEFAULT_REGISTRY_PATH
        families = engine_families
        corpus_paths = DEFAULT_CORPUS_PATHS
        escape_path_excludes = DEFAULT_ESCAPE_PATH_EXCLUDES
        override_env = OVERRIDE_ENV
        id_term_allowlist = DEFAULT_ID_TERM_ALLOWLIST
    else:
        enabled = bool(block.get("enabled", True))
        registry_path = str(block.get("registry_path") or DEFAULT_REGISTRY_PATH)
        families = _validated_str_tuple(block.get("families"), engine_families)
        corpus_paths = _validated_str_tuple(block.get("corpus_paths"), DEFAULT_CORPUS_PATHS)
        escape_path_excludes = _validated_str_tuple(
            block.get("escape_path_excludes"), DEFAULT_ESCAPE_PATH_EXCLUDES,
        )
        override_env = str(block.get("override_env") or OVERRIDE_ENV)
        id_term_allowlist = _validated_str_tuple(
            block.get("id_term_allowlist"), DEFAULT_ID_TERM_ALLOWLIST,
        )

    if tuple(sorted(families)) != engine_families:
        warnings.append(
            "[idgov-gate] WARNING: protocol.config.yaml issue_governance.families "
            f"{sorted(families)} has drifted from the engine's authoritative "
            f"family set {list(engine_families)} (idgov.grammar.FAMILIES). "
            "The engine remains authoritative for id recognition -- config "
            "cannot widen or narrow which families are recognized. Update "
            "the config to match, or investigate the drift."
        )

    warnings.extend(_corpus_escape_overlap_warnings(corpus_paths, escape_path_excludes))

    return IssueGovernanceSettings(
        enabled=enabled,
        registry_path=registry_path,
        families=families,
        corpus_paths=corpus_paths,
        escape_path_excludes=escape_path_excludes,
        override_env=override_env,
        id_term_allowlist=id_term_allowlist,
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Git plumbing (reusable by E4's prose-corpus diff -- see module docstring)
# ---------------------------------------------------------------------------


def _git_show(repo_root: Path, ref_path: str) -> Optional[bytes]:
    """Return the raw bytes of `git show <ref_path>`, or None if it does not
    resolve (path absent at that ref, ref unknown, or not a git repo)."""
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
    """Committed (HEAD) content of `path`, or None if untracked in HEAD."""
    return _git_show(repo_root, f"HEAD:{path}")


def staged_blob(repo_root: Path, path: str) -> Optional[bytes]:
    """Staged (index) content of `path`, or None if absent from the index."""
    return _git_show(repo_root, f":{path}")


def merge_base_blob(repo_root: Path, path: str, base_ref: str) -> Optional[bytes]:
    """Content of `path` at the merge-base of HEAD and `base_ref` (the CI-mode
    baseline). Returns None if the merge-base cannot be resolved or the path
    does not exist there."""
    proc = subprocess.run(
        ["git", "merge-base", "HEAD", base_ref],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if proc.returncode != 0:
        return None
    merge_base_sha = proc.stdout.strip()
    if not merge_base_sha:
        return None
    return _git_show(repo_root, f"{merge_base_sha}:{path}")


def working_tree_blob(repo_root: Path, path: str) -> Optional[bytes]:
    """Raw working-tree bytes of `path` (CI mode reads the checked-out tree
    directly; there is no index-staging concept in a CI checkout), or None if
    the file does not exist on disk."""
    try:
        return (repo_root / path).read_bytes()
    except OSError:
        return None


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


def _baseline_and_candidate(
    repo_root: Path, path: str, *, ci: bool, ci_base_ref: str,
) -> tuple[Optional[bytes], Optional[bytes]]:
    """Return (baseline_bytes, candidate_bytes) for `path`.

    Hook mode (default): baseline = HEAD blob, candidate = staged (index) blob.
    CI mode (--ci): baseline = blob at merge-base(HEAD, ci_base_ref), candidate
    = working-tree blob (a CI checkout has no index-staging step to diff).
    """
    if ci:
        baseline = merge_base_blob(repo_root, path, ci_base_ref)
        candidate = working_tree_blob(repo_root, path)
    else:
        baseline = head_blob(repo_root, path)
        candidate = staged_blob(repo_root, path)
    return baseline, candidate


# ---------------------------------------------------------------------------
# E1: line-wise append-only invariant
# ---------------------------------------------------------------------------


def _lines(data: Optional[bytes]) -> list[str]:
    """Decode `data` to text and split into lines.

    SEC-IDGOV-E-009: splits on "\\n" ONLY, after stripping all "\\r" bytes
    first (mirrors check_protected_append_only.py's _normalize() + explicit-
    split technique -- CRLF becomes LF, a lone pre-OSX-Mac "\\r" merges with
    the following line, an accepted trade-off already made by that sibling
    guard). This is intentionally NARROWER than str.splitlines(), which also
    treats \\v, \\f, \\x1c-\\x1e, \\x85, U+2028 and U+2029 as line boundaries
    -- a broader Unicode line-boundary set than git's own \\n-only line model,
    which could silently desync this gate's line-wise view of a file from
    git's actual diff view on content containing those rare bytes. A single
    trailing "\\n" (this repo's file-write convention) is stripped before
    splitting so it does not manufacture a spurious trailing empty-string
    "line" that would desync the E1 append-only prefix comparison."""
    if data is None:
        return []
    text = data.replace(b"\r", b"").decode("utf-8", errors="replace")
    if not text:
        return []
    if text.endswith("\n"):
        text = text[:-1]
    return text.split("\n")


def find_append_only_violations(baseline_lines: list[str], candidate_lines: list[str]) -> list[str]:
    """Return violation reason string(s) if `candidate_lines` is not, in
    order and unmodified, prefixed by `baseline_lines` (the registry only
    ever grows). Empty list = clean (pure append, unchanged, or first
    creation when baseline_lines == [])."""
    if len(candidate_lines) < len(baseline_lines):
        return [
            f"registry shrank: {len(baseline_lines)} previously-committed line(s) -> "
            f"{len(candidate_lines)} staged line(s) (append-only violation)"
        ]
    for i, base_line in enumerate(baseline_lines):
        if candidate_lines[i] != base_line:
            return [
                f"line {i + 1}: previously-committed registry line was modified or "
                f"reordered (append-only violation)"
            ]
    return []


# ---------------------------------------------------------------------------
# E2 (+ E3 via reuse): registry-content invariants, reused from engine.validate()
# ---------------------------------------------------------------------------


def _validate_candidate_content(candidate: Optional[bytes]) -> list[str]:
    """Run idgov.engine.validate() over the CANDIDATE registry bytes (which
    may be the staged/index blob or a CI working-tree blob, not necessarily
    the on-disk file at DEFAULT_REGISTRY_PATH). engine.validate()/registry
    .read_events() operate on a path, so the candidate is materialized to a
    throwaway temp file first.

    Fails CLOSED: any error while loading/parsing (e.g. malformed JSONL) is
    surfaced as a violation string, never silently swallowed.
    """
    if candidate is None:
        return []
    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".jsonl", delete=False) as tmp:
            tmp.write(candidate)
            tmp_path = tmp.name
        return engine.validate(tmp_path)
    except Exception as e:  # noqa: BLE001 -- fail-closed on any parse/load error
        return [f"registry failed to load for validation: {e}"]
    finally:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# E4/E5/E6: prose-corpus citation scan (shared locate-then-classify token scan
# + escape filtering), feeding check_mint_before_cite / check_malformed_id_block
# ---------------------------------------------------------------------------

# (a) fenced code blocks: a line starting (after leading whitespace) with
# a run of 3+ backticks or tildes toggles "inside a fence" state. The fence
# marker line itself is never scanned (it cannot contain a citation).
_FENCE_RE = re.compile(r"^\s*(?:`{3,}|~{3,})")
# (a) inline code spans: `...` on a single line. Replaced with a space (not
# removed outright) so a token cannot accidentally re-merge across the span
# boundary with adjacent prose text.
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
# (b) illustrative marker -- see _scannable_fragments() docstring for scope.
_ILLUSTRATIVE_MARKER = "<!-- idgov:illustrative -->"
# SEC-IDGOV-E-003: cap on how many `<!-- idgov:illustrative -->` markers a
# single corpus file's ADDED lines may use per commit before the gate stops
# honoring further markers in that file (chained markers would otherwise
# exempt an unbounded number of real citations, Sukuna CWE-807 class).
_ILLUSTRATIVE_MARKER_CAP = 3
# SEC-IDGOV-E-004: LOCAL, gate-only case-insensitive locator built from the
# single-source grammar.FAMILIES set (grammar.py itself is never modified --
# it remains the sole authority for what counts as WELL-FORMED via the
# case-SENSITIVE grammar.is_wellformed()). This locator only widens what
# counts as a CANDIDATE token to inspect; classification is still always
# grammar.is_wellformed(), so a lowercase/mixed-case hit can only ever
# classify as malformed (a real minted id is always uppercase).
_FAMILIES_ALT = "|".join(sorted(grammar.FAMILIES))
_ID_SHAPED_CI_RE = re.compile(
    rf"\b(?:{_FAMILIES_ALT})-[0-9A-Za-z][0-9A-Za-z.\-]*\b", re.IGNORECASE,
)
# Trailing sentence punctuation that ID_SHAPED_RE's own [0-9A-Z.\-]* char
# class can greedily swallow (e.g. "...cite SEC-CORTEX-030." matches through
# the period). A well-formed id's grammar never legitimately ends in any of
# these characters, so stripping them from the tail of a located token before
# classification cannot hide a real citation and prevents a false "malformed"
# classification of an otherwise well-formed id sitting at end-of-sentence.
_TRAILING_PUNCT_RE = re.compile(r"[.,;:!?)\]}\"']+$")


def _is_path_escape_excluded(
    path: str, excludes: tuple[str, ...] = DEFAULT_ESCAPE_PATH_EXCLUDES,
) -> bool:
    """E6(c): True if `path` (repo-relative, POSIX-or-Windows separators)
    matches a literal or glob entry in `excludes`. fnmatch's `*` matches `/`
    too (it is not directory-boundary-aware), so a `**` pattern behaves the
    same as a single `*` here -- sufficient for the exclusion lists in play."""
    norm = path.replace("\\", "/")
    for pattern in excludes:
        if norm == pattern or fnmatch.fnmatchcase(norm, pattern):
            return True
    return False


def _added_lines_with_offset(
    baseline: Optional[bytes], candidate: bytes,
) -> tuple[list[str], int, bool]:
    """Return (added_lines, start_line_no, is_clean_append) for a corpus
    prose file.

    Mirrors check_protected_append_only._added_lines()'s technique: if
    `baseline` is a clean line-prefix of `candidate` (the expected append-only
    shape these corpus docs are governed under, FEAT-GUARD-001), the tail
    past the prefix is "added" and start_line_no is the 1-based line number
    where it begins (is_clean_append=True). If it is NOT a clean prefix (a
    mid-file rewrite -- a separate append-only violation that
    check_protected_append_only.py's own hook already flags), this falls
    back to treating the ENTIRE candidate as "added" (is_clean_append=False)
    so a forged/malformed citation is never silently missed by this gate; it
    does not raise. `is_clean_append` tells the caller whether it is safe to
    seed a scan-state (e.g. SEC-IDGOV-E-001's fence parity) from the
    baseline's tail -- in the fallback case the scan starts at the true top
    of the file, so no baseline-derived state applies.
    """
    baseline_lines = _lines(baseline)
    candidate_lines = _lines(candidate)
    if candidate_lines[: len(baseline_lines)] == baseline_lines:
        return candidate_lines[len(baseline_lines):], len(baseline_lines) + 1, True
    return candidate_lines, 1, False


def _fence_state(lines: list[str]) -> bool:
    """SEC-IDGOV-E-001: return the cumulative fenced-code-block parity after
    processing all of `lines` in order (each line matching _FENCE_RE toggles
    the state) -- the SAME fence-token logic _scannable_fragments() itself
    uses, so the two can never diverge on what counts as "inside a fence".
    Used to seed _scannable_fragments()'s starting in_fence state from the
    committed BASELINE tail, so a baseline ending mid-fence (a dangling,
    unclosed ``` / ~~~ block) is carried forward correctly into the
    added-lines scan instead of resetting to False every call."""
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
    return in_fence


def _scannable_fragments(
    added_lines: list[str], *, initial_in_fence: bool = False,
) -> tuple[list[tuple[int, str]], bool]:
    """Return (fragments, marker_cap_exceeded).

    `fragments` is a list of (offset, fragment) pairs -- `offset` is the
    0-based index into `added_lines`, `fragment` is that line's text with
    escape-exempt spans filtered out (E6a/E6b), ready for id-token location.
    `initial_in_fence` (SEC-IDGOV-E-001) seeds the fence-parity state this
    scan starts in, so a baseline ending mid-fence is honored correctly
    instead of always assuming the added tail starts outside any fence.
    `marker_cap_exceeded` (SEC-IDGOV-E-003) is True if this file's added
    lines used more than _ILLUSTRATIVE_MARKER_CAP `idgov:illustrative`
    markers -- the caller is expected to print a loud warning; markers past
    the cap no longer exempt anything (their lines are scanned normally).

    Chosen `<!-- idgov:illustrative -->` scope (E6b, documented per the task
    brief's request to decide + document): the marker exempts the ENTIRE
    line it appears on (not just the text following the marker -- simpler to
    reason about and test) PLUS the entire NEXT added line. It does not
    persist beyond that one following line.
    """
    fragments: list[tuple[int, str]] = []
    in_fence = initial_in_fence
    illustrative_next = False
    marker_count = 0
    marker_cap_exceeded = False
    for idx, line in enumerate(added_lines):
        carried_illustrative = illustrative_next
        illustrative_next = False
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        has_marker = _ILLUSTRATIVE_MARKER in line
        marker_active = False
        if has_marker:
            marker_count += 1
            if marker_count <= _ILLUSTRATIVE_MARKER_CAP:
                illustrative_next = True
                marker_active = True
            else:
                marker_cap_exceeded = True
        if carried_illustrative or marker_active:
            continue
        fragments.append((idx, _INLINE_CODE_RE.sub(" ", line)))
    return fragments, marker_cap_exceeded


def _extract_id_tokens(text: str) -> list[str]:
    """Locate every id-shaped token in `text` using the LOCAL case-insensitive
    locator _ID_SHAPED_CI_RE (SEC-IDGOV-E-004 -- grammar.ID_SHAPED_RE itself
    is uppercase-only and would silently miss a lowercase/mixed-case
    id-shaped token, e.g. `sec-013`, escaping both E4 and E5 entirely).
    Every token this locator finds is still classified downstream with the
    case-SENSITIVE grammar.is_wellformed() (locate-then-classify, per the
    module docstring, so E4/E5 can never diverge on what counts as a
    citation), trimming trailing sentence punctuation a well-formed id can
    never legitimately end with."""
    tokens = []
    for m in _ID_SHAPED_CI_RE.finditer(text):
        tok = _TRAILING_PUNCT_RE.sub("", m.group(0))
        if tok:
            tokens.append(tok)
    return tokens


# Go-live prep -- E5 digit-gate. A well-formed id ALWAYS carries a numeric
# SEQ component (idgov/grammar.py `_SEQ = r"\d{3,}"`, required by every
# production in ISSUE_ID_RE), so a digitless id-shaped token can never be a
# real id, nor even a bare/malformed CITATION of one -- it is generic prose
# vocabulary that merely happens to look id-shaped (e.g. "SEC-ID" = "security
# ID", "SEC-NNN"/"MF-N" = placeholder notation, "SEC-GRAPH"/"BUG-SESSION" =
# a subsystem-prefix reference, not a specific numbered id).
_DIGIT_RE = re.compile(r"[0-9]")


def _has_seq_digit(token: str) -> bool:
    """E5 digit-gate: True if `token` contains at least one ASCII digit.

    Only a digit-bearing token can be malformed-flagged by E5 -- see the
    module comment above _DIGIT_RE and the E5 module-docstring note. This is
    a security-preserving relaxation of E5: every id E5 must still catch (a
    real bare id like `SEC-013`, a version-but-missing-seq citation like
    `SEC-DZPUP-9.9.5`) has a digit and is completely unaffected; only
    digitless FAMILY-WORD tokens become exempt. Does NOT affect E4
    (check_mint_before_cite) at all -- E4 only classifies WELL-FORMED tokens
    (grammar.is_wellformed(), which itself requires the numeric SEQ), so a
    digitless token is never wellformed and is therefore already outside E4's
    scope regardless of this gate."""
    return bool(_DIGIT_RE.search(token))


def _is_id_term_allowlisted(token: str, allowlist: tuple[str, ...]) -> bool:
    """True if `token` exact-matches (case-insensitive) an
    issue_governance.id_term_allowlist entry (protocol.config.yaml). Applied
    ON TOP OF the digit-gate above -- covers the rare WITH-digit generic term
    the digit-gate itself would not exempt (e.g. a severity-notation token
    like `SEC-P0`). Only ever consulted by E5 (check_malformed_id_block);
    E4's mint-before-cite is untouched by this allowlist too, for the same
    reason given in _has_seq_digit()'s docstring."""
    upper = token.upper()
    return any(upper == entry.upper() for entry in allowlist)


def _changed_files(repo_root: Path, *, ci: bool, ci_base_ref: str) -> list[str]:
    """SEC-IDGOV-E-002: list the repo-relative paths changed in this diff
    range -- the ONLY way to enumerate "which files matched a corpus glob
    changed" via git plumbing (git-show has no glob-expansion concept).

    Hook mode: `git diff --cached --name-only` (index vs HEAD -- the same
    baseline/candidate pairing _baseline_and_candidate() uses in hook mode).
    CI mode: `git diff --name-only <merge-base>` (working tree vs the
    merge-base -- matches _baseline_and_candidate()'s CI-mode candidate,
    working_tree_blob(), which reads the checked-out tree directly).

    Megumi Phase E re-review (Phase G prerequisite): this used to return []
    on ANY git failure -- a fail-SOFT edge in an otherwise fail-CLOSED gate.
    Because DEFAULT_CORPUS_PATHS always contains a glob entry (`audits/**`),
    this function runs on essentially every invocation; a git-plumbing
    failure (realistic on a shallow --ci checkout -- see the project's own
    shallow-repo-push-trap history) would silently drop ALL glob-corpus
    coverage for that run while the gate still exited 0. Now RAISES
    RuntimeError on a non-zero git return code (or lets a raised OSError from
    a failed subprocess launch propagate unchanged) instead of swallowing it
    -- both paths are caught by main()'s existing top-level try/except around
    _run_checks(), which turns them into a clean, non-traceback
    "[idgov-gate] INTERNAL ERROR (fail-closed, blocking): ..." message and a
    non-zero exit. Exact (non-glob) corpus_paths entries are unaffected --
    they never call this function."""
    if ci:
        mb = subprocess.run(
            ["git", "merge-base", "HEAD", ci_base_ref],
            cwd=str(repo_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        if mb.returncode != 0:
            raise RuntimeError(
                f"git merge-base HEAD {ci_base_ref} failed (rc={mb.returncode}): "
                f"{(mb.stderr or '').strip()}"
            )
        merge_base_sha = mb.stdout.strip()
        if not merge_base_sha:
            raise RuntimeError(f"git merge-base HEAD {ci_base_ref} returned no output")
        diff_args = ["git", "diff", "--name-only", merge_base_sha]
    else:
        diff_args = ["git", "diff", "--cached", "--name-only"]
    proc = subprocess.run(
        diff_args, cwd=str(repo_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{' '.join(diff_args)} failed (rc={proc.returncode}): {(proc.stderr or '').strip()}"
        )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _resolve_corpus_targets(
    repo_root: Path, corpus_paths: tuple[str, ...], escape_path_excludes: tuple[str, ...],
    *, ci: bool, ci_base_ref: str,
) -> list[str]:
    """SEC-IDGOV-E-002: resolve the effective set of corpus-prose file paths
    to scan this run. A corpus_paths entry may be an EXACT repo-relative path
    (the 3 protected docs -- scanned unconditionally, a no-op if nothing
    changed since _added_lines_with_offset then reports zero added lines) or
    a GLOB pattern (e.g. `audits/**`), expanded against the CHANGED files in
    this diff range via _changed_files(). A resolved target matching an
    escape_path_excludes entry is dropped (escape wins -- same precedence
    E6(c) already established for exact entries)."""
    targets: list[str] = []
    seen: set[str] = set()
    changed: Optional[list[str]] = None
    for pattern in corpus_paths:
        is_glob = any(ch in pattern for ch in "*?[")
        if not is_glob:
            if pattern not in seen:
                seen.add(pattern)
                targets.append(pattern)
            continue
        if changed is None:
            changed = _changed_files(repo_root, ci=ci, ci_base_ref=ci_base_ref)
        for raw_path in changed:
            norm = raw_path.replace("\\", "/")
            if norm not in seen and fnmatch.fnmatchcase(norm, pattern):
                seen.add(norm)
                targets.append(norm)
    return [t for t in targets if not _is_path_escape_excluded(t, escape_path_excludes)]


def _iter_corpus_citations(
    repo_root: Path, corpus_paths: tuple[str, ...], *, ci: bool, ci_base_ref: str,
    escape_path_excludes: tuple[str, ...] = DEFAULT_ESCAPE_PATH_EXCLUDES,
) -> list[tuple[str, int, str]]:
    """Scan the ADDED, escape-filtered lines of each resolved corpus target
    (SEC-IDGOV-E-002: exact paths + glob-expanded changed files) for
    id-shaped citation tokens. Returns (path, line_no, token) tuples,
    unclassified -- callers (check_mint_before_cite / check_malformed_id_block)
    apply grammar.is_wellformed() to split E4 vs E5 concerns."""
    citations: list[tuple[str, int, str]] = []
    targets = _resolve_corpus_targets(
        repo_root, corpus_paths, escape_path_excludes, ci=ci, ci_base_ref=ci_base_ref,
    )
    for path in targets:
        baseline, candidate = _baseline_and_candidate(repo_root, path, ci=ci, ci_base_ref=ci_base_ref)
        if candidate is None:
            continue  # nothing staged/present for this corpus path
        added, start_line_no, is_clean_append = _added_lines_with_offset(baseline, candidate)
        # SEC-IDGOV-E-001: only seed the fence state from the baseline's tail
        # when the added tail is a genuine append (clean line-prefix) -- the
        # fallback (whole-candidate) case scans from the true top of the
        # file, where no fence is open yet.
        initial_in_fence = _fence_state(_lines(baseline)) if is_clean_append else False
        fragments, marker_cap_exceeded = _scannable_fragments(added, initial_in_fence=initial_in_fence)
        if marker_cap_exceeded:
            print(
                f"[idgov-gate] WARNING: {path} uses more than "
                f"{_ILLUSTRATIVE_MARKER_CAP} `{_ILLUSTRATIVE_MARKER}` markers "
                "in this change -- the cap has been reached; additional "
                "markers no longer exempt citations (SEC-IDGOV-E-003).",
                file=sys.stderr,
            )
        for offset, fragment in fragments:
            line_no = start_line_no + offset
            for token in _extract_id_tokens(fragment):
                citations.append((path, line_no, token))
    return citations


def _known_registry_ids(repo_root: Path, registry_path: str, *, ci: bool, ci_base_ref: str) -> set[str]:
    """Ids with at least one event (assign or transition) in the STAGED/
    candidate registry -- i.e. ids that already have a registry row, per E4's
    "reserved+ row counts as existing" rule (any assigned state qualifies).
    Materializes the candidate to a throwaway temp file, mirroring
    _validate_candidate_content()'s pattern, since registry.read_events()
    operates on a path. Malformed-JSONL errors propagate (fail-closed --
    caught by main()'s existing catch-all, never warn-then-pass)."""
    _baseline, candidate = _baseline_and_candidate(repo_root, registry_path, ci=ci, ci_base_ref=ci_base_ref)
    if candidate is None:
        return set()
    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".jsonl", delete=False) as tmp:
            tmp.write(candidate)
            tmp_path = tmp.name
        events = registry.read_events(tmp_path)
        return registry.all_ids(events)
    finally:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Ordered check functions -- CHECKS is fixed at module load; E7 threads
# config-resolved corpus_paths/escape_path_excludes/id_term_allowlist through
# as keyword arguments (defaulting to the DEFAULT_* module constants) rather
# than restructuring CHECKS itself. Each check function has the signature
#   (repo_root, registry_path, *, ci, ci_base_ref,
#    corpus_paths=DEFAULT_CORPUS_PATHS,
#    escape_path_excludes=DEFAULT_ESCAPE_PATH_EXCLUDES,
#    id_term_allowlist=DEFAULT_ID_TERM_ALLOWLIST) -> list[str]
# (checks that don't need corpus_paths/escape_path_excludes/id_term_allowlist
# simply ignore them -- id_term_allowlist is E5-only, see
# check_malformed_id_block) and returns fully-prefixed, human-readable
# violation strings (empty = clean).
# ---------------------------------------------------------------------------

CheckFn = Callable[..., list]


def check_append_only(
    repo_root: Path, registry_path: str, *, ci: bool, ci_base_ref: str,
    corpus_paths: tuple[str, ...] = DEFAULT_CORPUS_PATHS,
    escape_path_excludes: tuple[str, ...] = DEFAULT_ESCAPE_PATH_EXCLUDES,
    id_term_allowlist: tuple[str, ...] = DEFAULT_ID_TERM_ALLOWLIST,
) -> list[str]:
    baseline, candidate = _baseline_and_candidate(repo_root, registry_path, ci=ci, ci_base_ref=ci_base_ref)
    reasons = find_append_only_violations(_lines(baseline), _lines(candidate))
    return [f"{registry_path}: {r}" for r in reasons]


def check_registry_invariants(
    repo_root: Path, registry_path: str, *, ci: bool, ci_base_ref: str,
    corpus_paths: tuple[str, ...] = DEFAULT_CORPUS_PATHS,
    escape_path_excludes: tuple[str, ...] = DEFAULT_ESCAPE_PATH_EXCLUDES,
    id_term_allowlist: tuple[str, ...] = DEFAULT_ID_TERM_ALLOWLIST,
) -> list[str]:
    """E2 uniqueness/grammar/seq/rev/transition-legality + E3 writer-authority
    (already covered inside engine.validate() -- see module docstring)."""
    _baseline, candidate = _baseline_and_candidate(repo_root, registry_path, ci=ci, ci_base_ref=ci_base_ref)
    reasons = _validate_candidate_content(candidate)
    return [f"{registry_path}: {r}" for r in reasons]


def check_mint_before_cite(
    repo_root: Path, registry_path: str, *, ci: bool, ci_base_ref: str,
    corpus_paths: tuple[str, ...] = DEFAULT_CORPUS_PATHS,
    escape_path_excludes: tuple[str, ...] = DEFAULT_ESCAPE_PATH_EXCLUDES,
    id_term_allowlist: tuple[str, ...] = DEFAULT_ID_TERM_ALLOWLIST,
) -> list[str]:
    """E4: every WELL-FORMED id cited in a corpus prose file's added lines
    must already exist as a registry row (any assigned state -- reserved+).

    Deliberately does NOT accept the digit-gate/id_term_allowlist relaxation
    check_malformed_id_block (E5) does -- that relaxation is scoped to E5
    only (see _has_seq_digit()'s docstring). Not that it would matter here
    regardless: this check only ever classifies grammar.is_wellformed()
    tokens, and a well-formed id always carries a numeric SEQ, so it can
    never BE a digitless token in the first place -- id_term_allowlist is
    accepted as a keyword (for CHECKS-loop signature uniformity) but
    intentionally unused below."""
    citations = _iter_corpus_citations(
        repo_root, corpus_paths, ci=ci, ci_base_ref=ci_base_ref,
        escape_path_excludes=escape_path_excludes,
    )
    wellformed_cited = [(p, ln, t) for (p, ln, t) in citations if grammar.is_wellformed(t)]
    if not wellformed_cited:
        return []
    known_ids = _known_registry_ids(repo_root, registry_path, ci=ci, ci_base_ref=ci_base_ref)
    return [
        f"{p}:{ln}: cited '{t}' has no registry row — mint it first (secid new ...)"
        for (p, ln, t) in wellformed_cited
        if t not in known_ids
    ]


def check_malformed_id_block(
    repo_root: Path, registry_path: str, *, ci: bool, ci_base_ref: str,
    corpus_paths: tuple[str, ...] = DEFAULT_CORPUS_PATHS,
    escape_path_excludes: tuple[str, ...] = DEFAULT_ESCAPE_PATH_EXCLUDES,
    id_term_allowlist: tuple[str, ...] = DEFAULT_ID_TERM_ALLOWLIST,
) -> list[str]:
    """E5 (Sukuna F1): a NEW id-shaped-but-not-well-formed token in a corpus
    prose file's added lines is a hard grammar block -- UNLESS it is exempted
    by the digit-gate (_has_seq_digit()) or the id_term_allowlist
    (_is_id_term_allowlisted()); see the E5 module-docstring go-live-prep
    note for the rationale (real ids always carry a numeric SEQ, so a
    digitless id-shaped token can never be a real or malformed-citation id --
    it is generic prose vocabulary, not a collidable id)."""
    citations = _iter_corpus_citations(
        repo_root, corpus_paths, ci=ci, ci_base_ref=ci_base_ref,
        escape_path_excludes=escape_path_excludes,
    )
    return [
        f"{p}:{ln}: malformed issue id '{t}' — use the full <FAMILY>-<SUBSYSTEM>-<SEQ> grammar"
        for (p, ln, t) in citations
        if not grammar.is_wellformed(t)
        and _has_seq_digit(t)
        and not _is_id_term_allowlisted(t, id_term_allowlist)
    ]


CHECKS: tuple[CheckFn, ...] = (
    check_append_only,
    check_registry_invariants,
    check_mint_before_cite,
    check_malformed_id_block,
)


def _run_checks(
    repo_root: Path, registry_path: str, *, ci: bool, ci_base_ref: str,
    corpus_paths: tuple[str, ...] = DEFAULT_CORPUS_PATHS,
    escape_path_excludes: tuple[str, ...] = DEFAULT_ESCAPE_PATH_EXCLUDES,
    id_term_allowlist: tuple[str, ...] = DEFAULT_ID_TERM_ALLOWLIST,
) -> list[str]:
    violations: list[str] = []
    for check_fn in CHECKS:
        violations.extend(check_fn(
            repo_root, registry_path, ci=ci, ci_base_ref=ci_base_ref,
            corpus_paths=corpus_paths, escape_path_excludes=escape_path_excludes,
            id_term_allowlist=id_term_allowlist,
        ))
    return violations


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_issue_ids.py",
        description="FEAT-IDGOV-001 fail-closed gate for the issue-id registry.",
    )
    parser.add_argument(
        "--registry", default=None,
        help="repo-relative path to the JSONL registry (default: "
             "protocol.config.yaml issue_governance.registry_path, else "
             f"{DEFAULT_REGISTRY_PATH})",
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="CI mode: diff the working tree against the merge-base with "
             "--ci-base-ref instead of the index vs HEAD (hook-mode default)",
    )
    parser.add_argument(
        "--ci-base-ref", default=DEFAULT_CI_BASE_REF,
        help=f"base ref for --ci mode's merge-base baseline (default: {DEFAULT_CI_BASE_REF})",
    )
    return parser


def main(
    argv: Optional[list] = None,
    repo_root: Optional[Path] = None,
    config_path: Optional[Path] = None,
) -> int:
    args = _build_parser().parse_args(argv)

    # E-008: a git or config failure during startup (repo-root resolution,
    # config load) now fails CLOSED with the same clean message as a
    # mid-check internal error, instead of a raw traceback -- robustness/UX
    # only, both paths were already fail-closed (nonzero exit) either way.
    try:
        if repo_root is None:
            repo_root = _repo_toplevel()
            if repo_root is None:
                # Finding 10 (CodeRabbit PR#112, P2): `git rev-parse
                # --show-toplevel` returning a NONZERO exit code (a corrupt
                # worktree, or a genuinely-outside-any-repo invocation) used
                # to be treated as an intentional, benign skip -- exit 0,
                # gate silently disabled. (A MISSING git executable is a
                # DIFFERENT failure mode: subprocess.run raises
                # FileNotFoundError there, which already propagates to the
                # except below and fails closed -- unaffected by this
                # change.) But this gate's only two real call sites (a
                # pre-commit hook, or CI on a checked-out repo) are BOTH
                # always inside a real git repository by construction, so a
                # resolution failure there is an anomaly, not a legitimate
                # skip. Fail CLOSED by default; OVERRIDE_ENV is the SAME
                # override already documented for authorized exceptions to
                # this gate (settings aren't loaded yet at this point, so
                # the module-level default is read directly rather than
                # settings.override_env).
                if os.environ.get(OVERRIDE_ENV) == "1":
                    print(
                        f"[idgov-gate] BYPASS: {OVERRIDE_ENV}=1 - could not resolve a git "
                        "repository toplevel, but the override is set - skipping the "
                        "issue-registry gate for this invocation.",
                        file=sys.stderr,
                    )
                    return 0
                print(
                    "[idgov-gate] BLOCKED (fail-closed): could not resolve a git repository "
                    "toplevel ('git rev-parse --show-toplevel' failed) -- refusing to "
                    f"silently disable the issue-registry gate. Set {OVERRIDE_ENV}=1 for a "
                    "genuine non-repository invocation.",
                    file=sys.stderr,
                )
                return 1

        settings = load_issue_governance_settings(repo_root, config_path)
    except Exception as e:  # noqa: BLE001 -- fail-CLOSED: never warn-then-pass
        print(f"[idgov-gate] INTERNAL ERROR (fail-closed, blocking): {e}", file=sys.stderr)
        return 1

    for warning in settings.warnings:
        print(warning, file=sys.stderr)

    if not settings.enabled:
        print(
            "[idgov-gate] DISABLED via config (issue_governance.enabled=false) "
            "— skipping issue-id registry gate",
            file=sys.stderr,
        )
        return 0

    registry_path = args.registry or settings.registry_path
    override_env = settings.override_env

    try:
        violations = _run_checks(
            repo_root, registry_path, ci=args.ci, ci_base_ref=args.ci_base_ref,
            corpus_paths=settings.corpus_paths,
            escape_path_excludes=settings.escape_path_excludes,
            id_term_allowlist=settings.id_term_allowlist,
        )
    except Exception as e:  # noqa: BLE001 -- fail-CLOSED: never warn-then-pass
        print(f"[idgov-gate] INTERNAL ERROR (fail-closed, blocking): {e}", file=sys.stderr)
        return 1

    if not violations:
        return 0

    bullet = "\n".join(f"    - {v}" for v in violations)
    override = os.environ.get(override_env) == "1"

    if override:
        print(
            f"[idgov-gate] BYPASS: {override_env}=1 - allowing issue-registry gate "
            f"violation(s):\n{bullet}\n"
            "    The registry is append-only permanent audit history (FEAT-IDGOV-001).\n"
            "    Ensure this is an authorized exception (backfill / migration / "
            "authorized restore).\n"
            f"    Scope this variable to the single invocation "
            f"(e.g. `{override_env}=1 git commit ...`) — do not export it globally in CI.",
            file=sys.stderr,
        )
        return 0

    print(
        "[idgov-gate] COMMIT BLOCKED - issue-id registry violation(s) detected:\n"
        f"{bullet}\n\n"
        "   The issue-registry is append-only permanent audit history (FEAT-IDGOV-001).\n"
        f"   Authorized exception? Re-run with {override_env}=1.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
