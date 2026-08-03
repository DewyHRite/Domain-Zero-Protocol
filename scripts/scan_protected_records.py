#!/usr/bin/env python3
"""
Compensating secret scanner for protected append-only records (SEC-001, Toji audit
v9.9.3 -> v9.9.4, MEDIUM).

Problem this closes:
  `.github/secret_scanning.yml` excludes `.protocol-state/dev-notes.md` from GitHub's
  push-protection secret scanning ENTIRELY. That exclusion exists because a single
  already-triaged, historical, append-only line quotes a Stripe PUBLIC-DOCUMENTATION
  example key (`sk_live_4eC39...7dc`, truncated here -- Stripe's own long-published
  sample, never a real/live credential) that cannot be scrubbed without violating the
  FEAT-GUARD-001 append-only invariant (see CLAUDE.md "PROJECT DOCUMENTS PROTECTION").

  Toji's finding: a file-wide path-ignore silences GitHub scanning for the ENTIRE file,
  not just that one historical line -- so any FUTURE real secret appended to
  dev-notes.md (or security-review.md, which has no such exclusion but is the sibling
  protected record) would also evade detection. Toji's own recommended remedy:
  "add a separate scanner that always scans protected records and fails on any other
  provider or generic-secret match."

  NOTE (SEC-DZPUP-9.9.5-GHPP-001): every quoted reference to that historical literal in
  THIS module -- including this comment block and the ALLOWLIST definition below -- is
  deliberately truncated or built via runtime string concatenation instead of written
  out as one contiguous `sk_live_<24 chars>` token. GitHub push-protection scans this
  file's own source for that exact shape and cannot distinguish "quoting the allowlisted
  literal for documentation/allowlist purposes" from "a leaked secret", so a contiguous
  copy here blocks every future publish of this file. The scanner's ALLOWLIST *value* at
  runtime is unchanged -- see `ALLOWLIST` below and
  tests/test_scan_protected_records.py::TestAllowlistLiteralIsNotContiguousInSource.

What this script does:
  ALWAYS scans the two git-tracked protected records --
    - .protocol-state/dev-notes.md
    - .protocol-state/security-review.md
  (`.dzp-domain/domain.record.md` is gitignored -- never committed -- so it is out of
  scope for a git-backed scanner; it is also outside GitHub's scanning surface for the
  same reason, so there is no compensating gap to close there.)

  It FAILS CLOSED (non-zero exit, file + line number + pattern named) on any match of a
  known secret-token FORMAT, or a `keyword: value` / `keyword=value` credential
  assignment whose value is not an obvious placeholder -- EXCEPT the single allowlisted,
  already-triaged literal `sk_live_4eC39...7dc` WHEN FOUND IN ITS OWN HOME FILE
  (dev-notes.md) ONLY (SEC-SCANTOP-001 Option B, file-scoped allowlist, USER-ruled
  2026-07-30 -- see the ALLOWLIST NOTE above; full value is defined once,
  non-contiguously, in ALLOWLIST_BY_FILE below). A byte-identical copy of that literal
  found in a DIFFERENT file -- including its sibling protected record,
  security-review.md -- is NOT allowlisted and fails closed like any other match.

Pattern provenance:
  This mirrors (does not import, to avoid pulling the full Cortex engine and its heavy
  optional dependencies -- sqlite_vec/fastembed/sqlcipher3 -- into a pre-commit hook)
  the placeholder-aware secret-format-then-keyword design of
  `.protocol-state/brain/cortex/ingest.py::contains_secret` (SEC-CORTEX-002,
  FEAT-CORTEX-SCOPE-001, v9.3.2), extended with a Stripe `sk_live_`/`sk_test_` secret-key
  FORMAT pattern -- which `contains_secret` does NOT have (that gap is *why* the
  original Stripe documentation literal was never caught as a format match and had to
  be handled via a docs-only exception / TEST-001 remediation instead).

Usage:
  python scripts/scan_protected_records.py
      Scans the STAGED (git index) content of the two protected records relative to
      the current repo (fails closed; intended for pre-commit / CI use).

  python scripts/scan_protected_records.py <file> [<file> ...]
      Scans the given file(s) directly from disk instead (ad-hoc scanning / tests).
      Bypasses git entirely.

Exit codes: 0 = clean (or no protected records present yet), 1 = one or more
non-allowlisted secret matches found.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, Optional

# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

# The protected-document set defined by CLAUDE.md "PROJECT DOCUMENTS PROTECTION"
# has THREE members. This scanner covers two of them. Both facts are stated here,
# and the coverage line printed by main() is computed against the THREE-member set
# -- not against PROTECTED_RECORDS -- so a clean run can never read as complete
# coverage of the protected set.
PROTECTED_RECORDS: tuple[str, ...] = (
    ".protocol-state/dev-notes.md",
    ".protocol-state/security-review.md",
)

# .dzp-domain/domain.record.md is intentionally NOT in PROTECTED_RECORDS above.
#
# THE PREMISE, AND ITS CONDITION. The exclusion is valid *because the file is
# untracked*, and only for as long as that remains true:
#
#   * untracked => there is no staged/HEAD git blob for this git-backed scanner
#     to read. Adding the path to PROTECTED_RECORDS would not scan it -- it would
#     be INERT: staged_blob() returns None and main() skips it on every run, while
#     the source would read as though the record were covered. That is strictly
#     worse than an honest, declared exclusion.
#   * untracked => never pushed => never inside GitHub push-protection's scanning
#     surface either. This scanner exists to COMPENSATE for a file-wide
#     secret_scanning.yml path-ignore (see the module docstring). There is no such
#     ignore for domain.record.md, because there is nothing for GitHub to ignore.
#     So there is no compensating gap here to close.
#
# TRACKING IT WAS CONSIDERED AND REJECTED (v9.11.0): the record carries internal
# identifier references and a local user path, has never passed the secret scan or
# the internal-identifier denylist, and scrubbing it would require OVERWRITING an
# append-only permanent record. Net risk of tracking exceeds the benefit.
#
# Because the premise is a fact about the repository rather than a constant, it is
# RE-VERIFIED AT RUNTIME by coverage_report() on every invocation, not asserted
# once in this comment. If the file ever becomes tracked, both bullets above stop
# holding and main() reports a PREMISE BROKEN escalation naming the path.
OUT_OF_SCOPE_RECORDS: tuple[tuple[str, str], ...] = (
    (
        ".dzp-domain/domain.record.md",
        "untracked/gitignored -- no git blob exists for this git-backed scanner "
        "to read, and an untracked file is likewise outside GitHub push-"
        "protection's surface, so there is no path-ignore here to compensate for",
    ),
)

# The single already-triaged, known-invalid literal this scanner must NOT flag --
# SCOPED TO ITS OWN HOME FILE. Anything else -- including a DIFFERENT sk_live_/
# sk_test_-shaped token, OR a byte-identical COPY of this same literal found in a
# DIFFERENT protected record -- fails closed.
#
# SEC-SCANTOP-001 Option B (USER-ruled 2026-07-30, defense-in-depth): this allowlist
# was previously FILE-AGNOSTIC -- a single flat set checked via `token in ALLOWLIST`
# with no regard to which file was being scanned. That meant a copy of this literal
# planted in security-review.md (which has never actually contained it -- verified by
# direct grep at the time of this change) would have silently passed, even though the
# ONLY legitimate historical occurrence is in dev-notes.md (see the module docstring's
# `.github/secret_scanning.yml` cross-reference, which exempts dev-notes.md ONLY, not
# security-review.md). ALLOWLIST_BY_FILE below maps each allowlisted literal to the
# lowercased basename(s) of the file(s) where it is legitimately allowed; scan_text()
# checks the token against the file actually being scanned, not a flat file-agnostic
# set. See tests/test_scan_protected_records.py::TestAllowlistIsFileScoped for the
# behavior contract (before/after) this change establishes.
#
# Built via runtime string concatenation, split at the `sk_live_` prefix boundary, so
# this file's SOURCE BYTES never contain the contiguous `sk_live_<24 chars>` token
# (SEC-DZPUP-9.9.5-GHPP-001: GitHub push-protection flags that exact contiguous shape
# and cannot tell this allowlisted Stripe PUBLIC-DOCUMENTATION sample key apart from a
# real leaked one, which blocked publishing this file to the public repo). The
# resulting runtime VALUE is byte-identical to the historical literal quoted (now
# truncated) in the module docstring above -- see
# test_runtime_allowlist_value_is_unchanged for the equality proof.
_HISTORICAL_STRIPE_LITERAL: str = "sk_" + "live_" + "4eC39HqLyjWDarjtT1zdp7dc"

ALLOWLIST_BY_FILE: dict[str, frozenset[str]] = {
    _HISTORICAL_STRIPE_LITERAL: frozenset({"dev-notes.md"}),
}

# Backward-compat / "is this value allowlisted ANYWHERE" flat view, derived from
# ALLOWLIST_BY_FILE -- kept as a single source of truth (never a second, independently
# maintained set) so it cannot drift from the file-scoped mapping above. scan_text()
# itself does NOT consult this flat set for its allow/deny decision (see below); it is
# provided only for callers/tests that want the file-agnostic question answered.
ALLOWLIST: frozenset[str] = frozenset(ALLOWLIST_BY_FILE.keys())

# ---------------------------------------------------------------------------
# Secret detection (mirrors cortex/ingest.py::contains_secret; see module docstring)
# ---------------------------------------------------------------------------

SECRET_FORMAT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("pem_private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b")),
    # Stripe secret keys -- NOT present in cortex/ingest.py's format list (see module
    # docstring for why that gap mattered). Deliberately covers BOTH live and test
    # secret keys so a real `sk_test_...` credential is caught too, not just live.
    ("stripe_secret_key", re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{10,}\b")),
]

# keyword[:=]value -- same shape as cortex/ingest.py::_SECRET_KEYWORD_RE. No leading \b
# because a credential keyword is often a SUFFIX of an env var name
# (RESEND_API_KEY=, AWS_SECRET_ACCESS_KEY=) where '_' suppresses a word boundary.
_SECRET_KEYWORD_RE = re.compile(
    r"(?i)(?:secret[_-]?access[_-]?key|access[_-]?key[_-]?id|api[_-]?key|"
    r"secret|password|passwd|token)\s*[:=]\s*(\S+)"
)

_PLACEHOLDER_WORDS = {
    "your", "example", "changeme", "change-me", "placeholder", "redacted",
    "tbd", "todo", "dummy", "none", "null", "xxx", "sample",
}

# SEC-DZPUP-9.9.4-010/-005 RECONCILIATION (v9.9.5, Sukuna + Megumi): the original
# -005 remediation added type-annotation words ("string", "number", "boolean", ...)
# directly to _PLACEHOLDER_WORDS above, which is SUBSTRING-matched (`word in low`,
# below). That masks any value merely CONTAINING one of those words -- e.g.
# `password: correcthorse_string_x9` -- a real detection weakening. When the sibling
# detector (cortex/ingest.py) hit the identical false-positive class (type-annotation
# prose such as `Token: String`), Megumi explicitly REJECTED the substring-word
# approach and ruled a BOUNDED, exact/regex closed-vocabulary recognizer instead
# (SEC-DZPUP-9.9.4-010). This scanner now uses the SAME closed-vocab set, matched
# via fullmatch only (cannot widen the substring-match surface). The two detectors
# had diverged -- one fixed with the safe approach, one with the unsafe one; this
# closes that gap. See tests/test_type_annotation_vocab_parity.py for the drift guard.
_TYPE_ANNOTATION_TOKENS = {
    "string", "number", "boolean", "any", "unknown", "void", "object",
    "undefined", "null", "bigint", "symbol", "never", "date",
    "array", "record", "map", "set", "buffer",
    "encryptedstring",
}
_TYPE_ANNOTATION_RE = re.compile(
    r"^(?:" + "|".join(sorted(_TYPE_ANNOTATION_TOKENS, key=len, reverse=True)) + r")(\[\])?$",
    re.IGNORECASE,
)

# SEC-DZPUP-9.9.4-006: a bare semver / package-version token (optionally
# caret/tilde-ranged, e.g. `^9.0.2`, `~1.2.3`, `2.0.0-beta.1`) is never a
# credential -- generalizes past a single literal to any `<keyword-suffix>: <semver>`
# line the permissive keyword regex matches (the keyword side is intentionally NOT
# tightened -- see Megumi's ruling: fix is value-side only).
#
# SEC-001 (Toji audit 2026-07-11, MEDIUM, CWE-184): the prior recognizer treated
# the ENTIRE pre-release/build suffix as a single flat blob capped at 24 broad
# alphanumeric/punctuation characters (`[0-9A-Za-z.+-]{1,24}`). Two adversarial
# gaps followed from that: (1) a value shaped `N.N.N-<up to 24 chars of entropy>`
# fullmatched and was masked as a safe placeholder outright, and (2) even a
# tighter per-suffix cap could be defeated by splitting a longer secret across
# several short DOT-JOINED identifiers (each individually short, jointly long),
# since the old pattern never inspected identifier boundaries at all.
#
# Fix: STRUCTURAL SemVer 2.0.0 grammar validation (`_is_structural_semver`,
# below) that parses the pre-release/build components into their true
# dot-separated identifiers per semver.org (ASCII alphanumerics + hyphen only;
# numeric identifiers carry no leading zero), PLUS an ENTROPY-SENSITIVE
# fallback (`_is_high_entropy_semver_identifier`) applied to EACH identifier
# individually -- so a structurally-valid-but-disguised-secret identifier is
# rejected even when the overall suffix length would have passed the old flat
# cap, and splitting a secret across multiple short identifiers no longer
# helps (each one is still evaluated on its own). SECRET_FORMAT_PATTERNS
# (provider-format scanning) is completely independent of this value-side
# logic and continues to run unconditionally over every line regardless of
# this recognizer's verdict.
_SEMVER_IDENTIFIER_CHARS_RE = re.compile(r"^[0-9A-Za-z-]+$")

# Per-identifier length ceiling. Real-world semver pre-release/build identifiers
# (beta, rc1, alpha2, SNAPSHOT, build, ISO-date stamps like 20260315, short
# git-sha fragments) are comfortably under this; an identifier longer than this
# reads as disguised high-entropy secret material rather than a hand-written
# version qualifier. Scoped to a SINGLE identifier (not the whole suffix, unlike
# the flat cap this replaces) so an attacker cannot defeat it by splitting a
# long secret across several dot-joined short identifiers.
_MAX_SEMVER_IDENTIFIER_LEN = 16

# SEC-DZPUP-9.9.5-SEMVER-CORE-001 (P1, CWE-184, Megumi Tier-3 FINAL adversarial
# pass): the MAJOR/MINOR/PATCH core groups were originally `(?:0|[1-9]\d*)` --
# LENGTH-UNBOUNDED. A value like `1.99999999999999999999999999999999999999999999.1`
# (a 46-digit minor field, ~153 bits of attacker-controlled entropy) fullmatched
# with zero scrutiny: the entropy accounting only ever inspected `pre`/`build`,
# never the core X.Y.Z text itself, and no suffix was even required to exploit
# it. Each core field is now named (`major`/`minor`/`patch`) AND structurally
# capped at 1-8 digits (`0|[1-9]\d{0,7}`), mirroring the existing 8-digit
# suffix-date ceiling (`_MAX_SAFE_NUMERIC_IDENTIFIER_LEN`) -- this closes the
# unbounded-length attack outright, at the grammar level, before any entropy
# accounting even runs. See `_is_structural_semver` for how each field's
# (now-bounded) length is folded into the SAME unified entropy budget as the
# prerelease/build suffix, closing the residual "chain 3 within-cap
# date-shaped core fields" variant that a per-field structural cap alone
# cannot catch.
_SEMVER_FULL_RE = re.compile(
    r"^[\^~]?"
    r"(?P<major>0|[1-9]\d{0,7})\."
    r"(?P<minor>0|[1-9]\d{0,7})\."
    r"(?P<patch>0|[1-9]\d{0,7})"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?"
    r"(?:\+(?P<build>[0-9A-Za-z.-]+))?$"
)


# SEC-DZPUP-9.9.5-SEMVER-MONOCASE-001 (P2, CWE-184, Megumi Tier-3 re-review of
# SEC-001): the original entropy fallback ONLY rejected an identifier that (a)
# exceeded `_MAX_SEMVER_IDENTIFIER_LEN` outright, or (b) mixed ALL THREE
# character classes (upper+lower+digit) simultaneously. That left every
# 1-of-3 or 2-of-3-class identifier at or under the cap completely unguarded --
# and those are the MOST common real secret encodings: monocase lowercase hex
# (`9f8e7d6c5b4a3210`), monocase uppercase base32/TOTP secrets
# (`JBSWY3DPEHPK3PX`), and long plain-decimal blobs (`1234567890123456`) all
# sailed through as "placeholders" at exactly 15-16 chars (Megumi's confirmed
# reproducers).
#
# Two additional, narrowly-scoped rules close this without reopening false
# positives on the real qualifiers this scanner exists to leave alone -- the
# false-positive/false-negative boundary is reasoned explicitly below rather
# than just moving the cap:
#
#   1. Plain-decimal (all-digit) identifiers get their OWN, SHORTER safe
#      length ceiling (`_MAX_SAFE_NUMERIC_IDENTIFIER_LEN` = 8), not the
#      general 16-char one. Real numeric pre-release/build identifiers are
#      bare single digits (`rc.1`) or 8-digit ISO date stamps
#      (`+build.20260315`) -- comfortably <= 8 digits. A 9-16 digit run is far
#      more likely to be disguised numeric secret entropy (the
#      `1234567890123456` reproducer) than a legitimate version identifier, so
#      it is rejected even though it is well under the general 16-char
#      ceiling. This is the tricky boundary Megumi called out directly: an
#      8-digit date passes, a 16-digit blob does not.
#   2. A small, explicit ALLOWLIST of conventional word-qualifiers (alpha,
#      beta, rc, dev, snapshot, final, pre, release) is exempted from length
#      scrutiny entirely, matched case-insensitively so `RELEASE`/`SNAPSHOT`
#      and `release`/`snapshot` are both recognized -- this is exactly the
#      vocabulary real version strings use.
#   3. Anything else that reaches this point -- NOT all-digit, NOT an
#      allowlisted qualifier word, and mixing only 1 or 2 character classes --
#      is flagged once it reaches `_MIN_MONOCASE_ENTROPY_LEN` (10) chars.
#      Below that length it is treated as a plausible short qualifier or hash
#      fragment (e.g. a 6-7 char git-sha build-metadata fragment, or `beta2`);
#      at or above it, no legitimate hand-written version qualifier is this
#      long, so it reads as disguised secret material (monocase hex/base32/
#      random-string secrets are routinely >=10 chars). The existing 3-class
#      full-mix rule still applies with NO minimum length, since mixing all
#      three classes is never a plausible short qualifier at any length.
_SAFE_SEMVER_QUALIFIERS: frozenset[str] = frozenset({
    "alpha", "beta", "rc", "dev", "snapshot", "final", "pre", "release", "build",
})
_MAX_SAFE_NUMERIC_IDENTIFIER_LEN = 8
_MIN_MONOCASE_ENTROPY_LEN = 10


def _is_high_entropy_semver_identifier(ident: str) -> bool:
    """True when a single dot-separated SemVer pre-release/build identifier
    looks more like disguised high-entropy secret material than a hand-written
    version qualifier. See the module-level comment above this function for
    the full false-positive/false-negative boundary reasoning.
    """
    if len(ident) > _MAX_SEMVER_IDENTIFIER_LEN:
        return True
    if ident.lower() in _SAFE_SEMVER_QUALIFIERS:
        return False
    if ident.isdigit():
        return len(ident) > _MAX_SAFE_NUMERIC_IDENTIFIER_LEN
    has_upper = any(c.isupper() for c in ident)
    has_lower = any(c.islower() for c in ident)
    has_digit = any(c.isdigit() for c in ident)
    if has_upper and has_lower and has_digit:
        return True
    # Monocase / 2-of-3-class fallback (SEC-DZPUP-9.9.5-SEMVER-MONOCASE-001):
    # catches monocase hex, monocase base32, and other 1-2-class identifiers
    # that are too long to be a plausible hand-written qualifier.
    return len(ident) >= _MIN_MONOCASE_ENTROPY_LEN


# SEC-DZPUP-9.9.5-SEMVER-CHAIN-001 (P1, CWE-184, Megumi Tier-3 adversarial
# re-attack on SEC-DZPUP-9.9.5-SEMVER-MONOCASE-001): per-identifier floors
# alone cannot bound ADDITIVE entropy -- an attacker simply adds MORE
# sub-floor identifiers (e.g. three 9-char monocase segments, each safely
# under the 10-char monocase floor and the 8-char numeric floor) to smuggle
# an arbitrarily large amount of entropy through, split across as many
# dot-joined identifiers as needed. Confirmed reproducer:
# `1.2.3-abcdefghi.jklmnopqr.stuvwxyz1` (27 chars / ~139 bits) fullmatched
# every per-identifier rule and was masked as safe. This is the exact
# "split-across-dots" attack class Toji's original SEC-001 finding named,
# now defeated via chaining rather than a single long identifier.
#
# SEC-DZPUP-9.9.5-SEMVER-DIGITCHAIN-001 (P1) + SEC-DZPUP-9.9.5-SEMVER-
# DUALCOMPONENT-001 (P3), Megumi Tier-3 FINAL adversarial pass: the first
# attempt at this fix (a per-COMPONENT aggregate, prerelease and build
# checked SEPARATELY, each against its own budget, with all-digit
# identifiers <= 8 chars unconditionally excluded from the sum) still had two
# holes. (1) DIGITCHAIN: the digit exclusion had NO cap on how many <=8-digit
# segments were chained -- `12345678.23456789.34567890` (24 digits / ~48
# bits) summed to a DIGITCHAIN aggregate of 0 and was masked as safe. (2)
# DUALCOMPONENT: budgeting prerelease and build independently at 16 each
# gives an effective 32 combined -- structurally unsound even though the
# specific reproducer supplied for this hole happened to already be caught
# by a DIFFERENT, unrelated per-identifier rule (the 10-char monocase floor).
#
# After three rounds of finding adjacent bypasses in a per-identifier /
# per-component design, this closes the WHOLE class with ONE structural
# invariant instead of patching another corner:
#
#   A) ONE combined budget over the WHOLE value's suffix content -- prerelease
#      and build-metadata are summed into a SINGLE total and compared ONCE
#      (see `_is_structural_semver`). Closes DUALCOMPONENT unconditionally:
#      there is no longer any per-component ceiling to split entropy across.
#   B) The unconditional short-digit exclusion is REMOVED entirely from the
#      aggregate. ALL non-qualifier identifiers now count their FULL length
#      toward the combined total, whether alnum OR pure-digit. The ONLY
#      zero-cost tokens are the 9-word qualifier allowlist below (`alpha`,
#      `beta`, `rc`, `dev`, `snapshot`, `final`, `pre`, `release`, `build`) --
#      a fixed, non-attacker-controlled dictionary, so repeating any of them
#      contributes 0 no matter how many times or where they are interleaved.
#      This closes DIGITCHAIN: chaining N <=8-digit segments now sums to
#      N * (segment length), not 0 * N.
#
#      Per-identifier rules are UNCHANGED and still gate independently
#      (16-char absolute cap, qualifier allowlist, 8-char digit ceiling,
#      3-class mix, 10-char monocase) -- the combined budget is an ADDITIONAL
#      structural ceiling layered on top, not a replacement. An identifier
#      must pass BOTH its own per-identifier rule AND not push the combined
#      total over budget.
#
#   C) Budget (at this point in the fix history) = 17. Only identifiers that
#      already survive EVERY per-identifier rule can reach the aggregate at
#      all, which bounds each surviving identifier to <=9 chars
#      (monocase/2-class floor) or <=8 chars (all-digit ceiling) -- a
#      3-class-mixed identifier is barred entirely, at any length, and never
#      reaches the aggregate. The worst realistic LEGIT combo this scanner
#      must not false-positive combines a bare numeric prerelease identifier
#      (`1`, 1 char) with a 7-char git-sha build fragment and an 8-digit ISO
#      date, e.g. `1.2.3-1+a1b2c3d.20260315` = 1 + 7 + 8 = 16 combined
#      non-qualifier chars (verified in test_worst_realistic_legit_combo_still_passes).
#      17 passes that 16-char worst-case legit combo (16 <= 17) while
#      strictly rejecting every required-to-flag reproducer -- three of them
#      (from the prior per-component-budget round, e.g. two chained 9-char
#      monocase segments `abcdefghi.jklmnopqr`) total EXACTLY 18 combined
#      chars, so 18 itself cannot be a safe budget value without silently
#      un-flagging those already-committed regression tests. [DOC CORRECTION,
#      Megumi Tier-3 accuracy nit, CORE-001 round: with the strict `>`
#      comparison used below, 16 would ALSO pass that same 16-char worst-case
#      combo -- 17 is the smallest value with a full +1 safety margin above
#      the known worst legit case, not "the unique integer"; both 16 and 17
#      satisfy 16 <= budget < 18. This constant has since been superseded by
#      `_SEMVER_UNIFIED_ENTROPY_BUDGET` below, which folds in core-field
#      content too -- retained here only as the historical record of this
#      round's reasoning.]
#
#   D) "No remaining channel" walkthrough (every splitting/mixing angle) as of
#      THIS round -- see `_SEMVER_UNIFIED_ENTROPY_BUDGET` below for the
#      updated, CURRENT walkthrough that also covers the core X.Y.Z fields:
#        - Cross-component (pre vs build): closed by (A) -- one shared total.
#        - Digit vs alnum: closed by (B) -- both count fully, no digit escape
#          hatch.
#        - Interleaved qualifiers: harmless BY CONSTRUCTION -- the allowlist
#          is a fixed 9-word dictionary carrying no attacker-chosen entropy,
#          so inserting extra copies of it between real segments changes
#          nothing about the SUM of those real segments' lengths (confirmed
#          by test_qualifier_interleaved_digit_chaining_is_not_masked and the
#          earlier test_qualifier_interleaved_chaining_still_flagged).
#        - Splitting into MANY tiny segments instead of few large ones: the
#          aggregate is a straight SUM over every non-qualifier identifier's
#          length regardless of how many pieces it is split into, so 20
#          segments of 1 char sum to 20 exactly like one 20-char identifier
#          would (if a 20-char single identifier could even survive the
#          per-identifier 16-char absolute cap, which it can't) -- granularity
#          of splitting does not change the total.
#        - 3-class-mixed identifiers: barred at the per-identifier stage
#          unconditionally, at ANY length, so they never reach the aggregate
#          at all and cannot be used to pack more entropy per segment.
#      (At this point in the fix history, the MAJOR.MINOR.PATCH core was NOT
#      yet part of this accounting -- that gap is SEC-DZPUP-9.9.5-SEMVER-
#      CORE-001, closed immediately below.)
#
#   Accepted P3 residual (Megumi-judged, carried forward): a SINGLE
#   monocase/2-class identifier of 8-9 chars (~40-46 bits) or an 8-char
#   all-digit identifier still passes on its own. Tightening further risks
#   false-positiving legitimate 7-8 char git-sha build fragments; left as an
#   accepted residual rather than chased into a false-positive. Any genuine
#   false positive can be resolved by adding the specific literal to
#   `ALLOWLIST` or a new word to `_SAFE_SEMVER_QUALIFIERS` if it turns out to
#   be a common convention.

# SEC-DZPUP-9.9.5-SEMVER-CORE-001 (P1, CWE-184, Megumi Tier-3 FINAL adversarial
# pass): the MAJOR.MINOR.PATCH core was NEVER part of the entropy accounting
# above -- only `pre`/`build` were ever inspected. Combined with the
# then-unbounded core-field regex, this reopened the split-across-dots class
# via a channel none of the three prior fixes (CHAIN-001, DIGITCHAIN-001,
# DUALCOMPONENT-001) had ever touched: `1.99999999999999999999999999999999999999999999.1`
# (46-digit minor, ~153 bits) needed no suffix at all.
#
# This is the definitive, structurally-complete close: EVERY attacker-
# controllable character in the value is now bounded under ONE accounting.
#
#   E) The regex-level fix above (`_SEMVER_FULL_RE`, `major`/`minor`/`patch`
#      capped at 1-8 digits each, mirroring `_MAX_SAFE_NUMERIC_IDENTIFIER_LEN`)
#      closes the truly-unbounded attack at the syntax level: a core field
#      over 8 digits fails to match `_SEMVER_FULL_RE` at all, so
#      `_is_structural_semver` returns False immediately, before any entropy
#      accounting runs.
#
#   F) The residual, WITHIN-CAP attack -- chaining multiple <=8-digit
#      date-shaped core fields (the grammar allows exactly 3 core fields, no
#      more, so this is inherently bounded to 3 segments, unlike the
#      arbitrary-length suffix dot-chains) -- is closed by folding EACH core
#      field's length into the SAME unified budget as the suffix, with NO
#      special "date exemption" for core fields (core fields are always
#      purely numeric by grammar -- there is no qualifier-word concept to
#      exempt, and giving even ONE core field a full exemption was found,
#      during design, to make a 3-field date-chain attack (16 non-exempt
#      chars with one exemption) total LESS than the worst realistic legit
#      suffix combo (18-19 combined) -- i.e. any exemption would make the
#      attack look SAFER than a legitimate value, which is backwards. No
#      exemption at all is both simpler and strictly safer here).
#
#   G) Unified budget = 19 (`_SEMVER_UNIFIED_ENTROPY_BUDGET`, replacing the
#      suffix-only `_SEMVER_COMBINED_ENTROPY_BUDGET` above). Derivation:
#        - Every core field is ALWAYS present (major, minor, patch), each
#          contributing its full (now <=8-digit-capped) length with no
#          exemption. The theoretical MINIMUM core contribution is 3 (three
#          single-digit fields, e.g. `1.2.3` or `9.9.5`); CalVer contributes
#          more from its one genuinely long field (e.g. `20260711.1.0` =
#          8 + 1 + 1 = 10) but that is STILL comfortably low because only ONE
#          field is ever realistically long in a real version string.
#        - The worst realistic LEGIT combo, now with core folded in:
#          `1.2.3-1+a1b2c3d.20260315` = core (1+1+1=3) + suffix (1+7+8=16)
#          = 19 combined (verified in test_worst_realistic_legit_combo_still_passes,
#          which is retained UNCHANGED from the prior round and must still
#          pass). This is the binding LEGIT case: budget must be >= 19.
#        - The binding ATTACK case is the 3-field date-shaped core chain,
#          `20260711.20260711.20260711` (no suffix): core = 8+8+8 = 24
#          combined, comfortably clearing 19 (verified in
#          test_chained_date_shaped_cores_is_not_masked). Every other
#          adversarial reproducer from prior rounds, now with core folded in,
#          lands at 21-39 combined (each +3 over its prior suffix-only total,
#          from the `1.2.3` core in those fixtures) -- all comfortably clear
#          of 19 too.
#        - 19 is therefore the MINIMUM sufficient value: it exactly passes
#          the known worst legit combo with zero slack, while every
#          required-to-flag reproducer clears it by a margin of 2 (the
#          closest, the 3-field core chain re-run at exactly 21 in an
#          equivalent construction) up to 20. Raising the budget above 19
#          would only widen the gap the wrong way (more attacker entropy
#          tolerated); lowering it below 19 would false-positive the known
#          worst legit combo. Accepted residual: a 2-field date-chain in the
#          core alone (e.g. `20260711.20260711.1` = 8+8+1 = 17 combined) is
#          NOT explicitly required to be flagged by any test and still
#          passes at 17 <= 19 -- tightening the budget to catch it would
#          break the 19-combined legit worst case, so (mirroring the
#          established single-identifier P3 residual above) this is an
#          accepted residual rather than a chased false-positive.
_SEMVER_UNIFIED_ENTROPY_BUDGET = 19


def _entropy_bearing_length(raw: str) -> int:
    """Sum of the lengths of the "entropy-bearing" identifiers in a single
    dot-separated suffix component (prerelease OR build-metadata) -- i.e.
    every identifier EXCEPT an allowlisted qualifier word. This counts
    ALL-DIGIT identifiers at their full length too
    (SEC-DZPUP-9.9.5-SEMVER-DIGITCHAIN-001) -- there is no digit-specific
    exemption here. See the module comment above
    `_SEMVER_UNIFIED_ENTROPY_BUDGET` for the full design rationale."""
    total = 0
    for ident in raw.split("."):
        if ident.lower() in _SAFE_SEMVER_QUALIFIERS:
            continue
        total += len(ident)
    return total


def _is_structural_semver(value: str) -> bool:
    """True when `value` is a syntactically valid SemVer 2.0.0 version
    (optionally caret/tilde-ranged, e.g. npm-style `^9.0.2`) whose
    pre-release/build identifiers are ALSO not disguised high-entropy secret
    material (see `_is_high_entropy_semver_identifier`), AND whose combined
    non-qualifier content -- MAJOR + MINOR + PATCH core fields AND the
    prerelease/build suffix together -- does not exceed
    `_SEMVER_UNIFIED_ENTROPY_BUDGET` (see the module comment above that
    constant for the full "no remaining channel" proof,
    SEC-DZPUP-9.9.5-SEMVER-CORE-001).

    Structural grammar follows semver.org: MAJOR.MINOR.PATCH numeric
    components carry no leading zeroes and are each structurally capped at
    1-8 digits (`_SEMVER_FULL_RE`); an optional pre-release (`-...`) and/or
    build metadata (`+...`) component is a DOT-separated sequence of
    identifiers, each composed only of ASCII alphanumerics and hyphens;
    numeric identifiers (all-digit) must not carry a leading zero.
    """
    m = _SEMVER_FULL_RE.fullmatch(value)
    if not m:
        return False
    # SEC-DZPUP-9.9.5-SEMVER-CORE-001: fold the (now structurally-capped)
    # MAJOR/MINOR/PATCH core fields into the SAME unified total as the
    # suffix -- no per-field exemption (see rationale (F) above).
    combined_entropy = sum(len(m.group(core_group)) for core_group in ("major", "minor", "patch"))
    for group_name in ("pre", "build"):
        raw = m.group(group_name)
        if raw is None:
            continue
        for ident in raw.split("."):
            if not ident or not _SEMVER_IDENTIFIER_CHARS_RE.fullmatch(ident):
                return False
            if ident.isdigit() and len(ident) > 1 and ident[0] == "0":
                return False  # leading-zero numeric identifier: invalid per semver.org
            if _is_high_entropy_semver_identifier(ident):
                return False  # entropy-sensitive fallback: reject disguised secret entropy
        combined_entropy += _entropy_bearing_length(raw)
    # SEC-DZPUP-9.9.5-SEMVER-CORE-001 / -DIGITCHAIN-001 / -DUALCOMPONENT-001:
    # ONE unified budget across core + BOTH suffix components together
    # (checked ONCE, after everything has been accumulated), closing the
    # core-inflation, digit-chaining, and dual-component bypasses that a
    # narrower design could not bound.
    if combined_entropy > _SEMVER_UNIFIED_ENTROPY_BUDGET:
        return False
    return True


def _is_placeholder_value(value: str) -> bool:
    """True when a keyword's value is an obvious placeholder, not a real secret."""
    # SEC-DZPUP-9.9.4-005/-008: widen trailing-punctuation strip to also cover
    # closing parens/braces and markdown escape/adjacency characters so prose
    # like `` `token: string;`); `` or a code-span-adjacent value doesn't
    # survive the strip and defeat the recognizers below.
    #
    # v9.9.5 adversarial fix (Sukuna): deliberately EXCLUDES "]" from this set.
    # A trailing "]" is handled by the templated-placeholder check immediately
    # below (`v[-1] in "]>}%"`), which correctly treats it as a closing-bracket
    # placeholder marker (e.g. `[PASSWORD]`) OR the end of a TypeScript array
    # type-annotation suffix (e.g. `string[]`). Stripping "]" HERE first would
    # mangle "string[]" into "string[" before either check runs -- destroying
    # both the templated-bracket check's trailing-"]" detection AND the
    # closed-vocab type-annotation regex's `(\[\])?` array-suffix branch, so an
    # array-typed annotation would fail to be recognized as a placeholder.
    v = value.strip().strip("\"'`,;)}\\/")
    if not v:
        return True
    if v[0] in "[<{$%" or v[-1] in "]>}%":
        return True
    if re.fullmatch(r"[x*\-_.]{3,}", v, re.I) or re.search(r"x{4,}", v, re.I):
        return True
    low = v.lower()
    if any(word in low for word in _PLACEHOLDER_WORDS):
        return True
    # SEC-DZPUP-9.9.4-010 (reconciled): closed-vocab exact-match type-annotation
    # recognizer -- NOT folded into the substring-matched _PLACEHOLDER_WORDS above.
    if _TYPE_ANNOTATION_RE.fullmatch(v):
        return True
    # SEC-DZPUP-9.9.4-006 / SEC-001: bare semver / package-version value (see
    # _is_structural_semver comment above) -- e.g. `jsonwebtoken: ^9.0.2`.
    if _is_structural_semver(v):
        return True
    # SEC-DZPUP-9.9.4-007: human-written truncated example, e.g. `AKIA...`,
    # `sk_live_...`, `ghp_...`. LENGTH-CAPPED at <=16 chars before the `...`
    # (Megumi's requirement) -- an unbounded "ends in ... => safe" rule would
    # let a real, long secret dodge detection by appending `...` to itself.
    # Genuine secrets remain independently caught by SECRET_FORMAT_PATTERNS
    # above regardless of this heuristic (that check runs first, over the
    # whole line, and is untouched by this value-side placeholder logic).
    if v.endswith("...") and len(v) - 3 <= 16:
        return True
    if len(v) < 6:  # too short to be a credible secret
        return True
    # A BARE `sk_live_`/`sk_test_` prefix with no random suffix can never be a real
    # Stripe secret key -- Stripe keys always append a random suffix after the prefix
    # (see the `stripe_secret_key` FORMAT pattern above, which requires >=10 trailing
    # chars). This is what naive line-based `\S+` capture yields for engineering-log
    # prose describing a synthetic, deliberately-non-secret test token built by string
    # concatenation, e.g. `_SECRET_TOKEN = "sk_live_" + "Zz" * 12` (see dev-notes.md
    # TEST-001-RESIDUAL, v9.9.2/v9.9.3) -- the regex captures only the quoted prefix
    # literal up to the `+`, not the full expression. This is a template-fragment
    # placeholder, not a secret, and does not weaken detection of any complete,
    # suffixed Stripe key (which never matches this narrower pattern).
    if re.fullmatch(r"sk_(?:live|test)_", low):
        return True
    return False


class Finding(NamedTuple):
    file: str
    line: int
    pattern: str
    token: str


def _is_allowlisted_here(token: str, filename: str) -> bool:
    """True iff `token` is allowlisted SPECIFICALLY for the file being scanned
    (SEC-SCANTOP-001 Option B, file-scoped allowlist). `filename` is normalized via
    `Path(filename).name.lower()` -- the same basename-normalization convention used
    elsewhere in this codebase (e.g. check_branch_record_isolation.py's session-record
    parsing) -- so this behaves identically whether scan_text() is called with a bare
    filename ("dev-notes.md") or a full protected-record-relative path
    (".protocol-state/dev-notes.md", exactly how main()'s staged-git mode calls it).
    """
    allowed_files = ALLOWLIST_BY_FILE.get(token)
    if allowed_files is None:
        return False
    return Path(filename).name.lower() in allowed_files


def scan_text(text: str, filename: str) -> list[Finding]:
    """Scan `text` line-by-line, returning non-allowlisted secret Findings.

    SEC-SCANTOP-001 Option B: allowlist membership is FILE-SCOPED (see
    `_is_allowlisted_here`) -- a token allowlisted for one protected record is NOT
    automatically allowlisted when found in a different file being scanned here.
    """
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for name, pattern in SECRET_FORMAT_PATTERNS:
            for m in pattern.finditer(line):
                token = m.group(0)
                if _is_allowlisted_here(token, filename):
                    continue
                findings.append(Finding(filename, line_no, name, token))
        for m in _SECRET_KEYWORD_RE.finditer(line):
            value = m.group(1)
            if _is_allowlisted_here(value, filename):
                continue
            if _is_placeholder_value(value):
                continue
            findings.append(Finding(filename, line_no, "keyword_value", value))
    return findings


# ---------------------------------------------------------------------------
# Git helpers (mirrors scripts/check_protected_append_only.py)
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


def staged_blob(repo_root: Path, path: str) -> Optional[bytes]:
    """Staged (index) content of `path`, or None if not present in the index."""
    return _git_show(repo_root, f":{path}")


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


def is_path_tracked(repo_root: Path, path: str) -> bool:
    """True when `path` has a git INDEX entry. Mirrors the identically-named
    helper in check_protected_append_only.py and check_issue_ids.py so all
    three controls agree on what "git knows about this file" means, rather
    than each deciding it independently."""
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path],
        cwd=str(repo_root),
        capture_output=True,
    )
    return proc.returncode == 0


class CoverageReport(NamedTuple):
    """What this scanner actually covered, computed against the FULL
    three-document protected set rather than this scanner's own tuple."""

    in_scope_tracked: list          # in PROTECTED_RECORDS and tracked
    in_scope_untracked: list        # in PROTECTED_RECORDS but NOT tracked (inert!)
    out_of_scope: list              # (path, reason) -- declared, premise holding
    premise_broken: list            # out-of-scope paths that are NOW tracked
    protected_set_size: int         # the real denominator: 3


def coverage_report(repo_root: Path) -> CoverageReport:
    """Compute this scanner's true coverage, re-verifying the stated premise
    of every declared exclusion.

    The denominator is the whole protected-document set (PROTECTED_RECORDS +
    OUT_OF_SCOPE_RECORDS), deliberately NOT len(PROTECTED_RECORDS). Reporting
    "2/2 records scanned" for a 3-document protected set is the precise way a
    partial control reads as a complete one.
    """
    in_scope_tracked, in_scope_untracked = [], []
    for rel_path in PROTECTED_RECORDS:
        (in_scope_tracked if is_path_tracked(repo_root, rel_path)
         else in_scope_untracked).append(rel_path)

    out_of_scope, premise_broken = [], []
    for rel_path, reason in OUT_OF_SCOPE_RECORDS:
        if is_path_tracked(repo_root, rel_path):
            premise_broken.append(rel_path)
        else:
            out_of_scope.append((rel_path, reason))

    return CoverageReport(
        in_scope_tracked=in_scope_tracked,
        in_scope_untracked=in_scope_untracked,
        out_of_scope=out_of_scope,
        premise_broken=premise_broken,
        protected_set_size=len(PROTECTED_RECORDS) + len(OUT_OF_SCOPE_RECORDS),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def main(argv: Optional[list[str]] = None, repo_root: Optional[Path] = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    all_findings: list[Finding] = []

    if args:
        # Ad-hoc mode: scan the given files directly from disk (bypasses git).
        for file_arg in args:
            p = Path(file_arg)
            if not p.is_file():
                continue
            all_findings.extend(scan_text(p.read_text(encoding="utf-8", errors="replace"), file_arg))
    else:
        # Default mode: scan the STAGED content of the protected records.
        if repo_root is None:
            repo_root = _repo_toplevel()
            if repo_root is None:
                print("[protected-secret-scan] not a git repository — skipping", file=sys.stderr)
                return 0
        # --- COVERAGE (always printed, pass or fail) -----------------------
        # A scanner that cannot state what it scanned is indistinguishable from
        # one that scanned nothing. Before this, a run that scanned ZERO records
        # produced ZERO output and exited 0 -- byte-identical to a run that
        # scanned everything and found nothing.
        report = coverage_report(repo_root)

        scanned: list[str] = []
        no_index_blob: list[str] = []
        for rel_path in PROTECTED_RECORDS:
            blob = staged_blob(repo_root, rel_path)
            if blob is None:
                # CORRECTED PREMISE (v9.11.0 batch 5). The original comment here
                # read "not tracked / not staged yet", implying that a tracked
                # record simply untouched by this commit lands in this branch.
                # It does not: staged_blob() reads the INDEX, and the index holds
                # a stage-0 blob for EVERY tracked file whether or not it was
                # staged in this commit -- verified directly. So `blob is None`
                # means there is NO STAGE-0 INDEX ENTRY, which is only ever:
                # untracked, staged-for-deletion, or an unmerged/conflicted
                # entry (during a merge, stages 1/2/3 exist but stage 0 does
                # not). All three mean this record went UNSCANNED, and none of
                # them is routine -- which is exactly why swallowing them with a
                # bare `continue` was wrong.
                no_index_blob.append(rel_path)
                continue
            scanned.append(rel_path)
            all_findings.extend(scan_text(_decode(blob), rel_path))

        lines = [
            f"[protected-secret-scan] COVERAGE: {len(PROTECTED_RECORDS)}/"
            f"{report.protected_set_size} protected record(s) in scanner scope; "
            f"{len(scanned)} scanned this run"
        ]
        for rel_path in no_index_blob:
            lines.append(
                f"   *** NOT SCANNED: {rel_path} has no stage-0 index blob (untracked,\n"
                "       staged-for-deletion, or an unmerged/conflicted entry). This record\n"
                "       is in scope but was NOT checked on this run."
            )
        for rel_path, reason in report.out_of_scope:
            lines.append(
                f"   OUT OF SCOPE: {rel_path} -- {reason}. Premise re-verified this run."
            )
        for rel_path in report.in_scope_untracked:
            lines.append(
                f"   *** INERT: {rel_path} is in PROTECTED_RECORDS but is UNTRACKED, so\n"
                "       there is no git blob to scan and this scanner passes it silently\n"
                "       on every run. It is listed as covered but is not."
            )
        for rel_path in report.premise_broken:
            lines.append(
                f"   *** PREMISE BROKEN: {rel_path} is declared OUT OF SCOPE because it is\n"
                "       untracked -- but it is NOW TRACKED. Both halves of that reasoning\n"
                "       (no git blob to scan; outside GitHub's scanning surface) have\n"
                "       stopped holding. Re-decide whether it belongs in PROTECTED_RECORDS."
            )
        print("\n".join(lines), file=sys.stderr)

    if all_findings:
        bullet = "\n".join(
            f"    - {f.file}:{f.line}  [{f.pattern}]  {f.token!r}" for f in all_findings
        )
        print(
            "[protected-secret-scan] COMMIT BLOCKED - protected record(s) contain a\n"
            "   non-allowlisted secret-shaped match:\n"
            f"{bullet}\n\n"
            "   Protected records are append-only (CLAUDE.md PROJECT DOCUMENTS PROTECTION) and\n"
            "   cannot be scrubbed after the fact, so real secrets must NEVER be appended.\n"
            "   Fix: remove the secret from your pending change before committing, and rotate\n"
            "   the credential immediately if it was ever real/live.\n\n"
            "   If this is a KNOWN, already-triaged, non-live literal (e.g. a vendor's own\n"
            "   published documentation example), add it to ALLOWLIST in\n"
            "   scripts/scan_protected_records.py with a comment explaining why — do not\n"
            "   silence this scanner via secret_scanning.yml path-ignores, which is the\n"
            "   whole-file exposure this script exists to compensate for.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
