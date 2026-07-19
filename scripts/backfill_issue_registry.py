#!/usr/bin/env python3
"""FEAT-IDGOV-001 Phase F -- non-destructive legacy-row corpus reconciliation
(spec §6 "Historical reuse remediation").

Scans a corpus of prose files for id-shaped literals (both well-formed and
bare/malformed -- e.g. the historical bare `SEC-001` reused 5 different times)
and appends one `legacy:true` `assign` row per DISTINCT OCCURRENCE to the
issue-id registry. Each row carries:
  - a unique `id` (`<literal>-LEGACY-<date>-<occurrence_key>`) -- deliberately
    NOT grammar-valid. `idgov.engine.validate()` (Phase F re-review,
    SEC-IDGOV-F-001/F-002) replaces grammar/writer-authority checks for
    legacy rows with BOUNDED positive substitutes -- id must match
    `idgov.grammar.LEGACY_ID_RE` (this exact shape) and `attested_writer`
    must equal `idgov.registry.LEGACY_ATTESTED_WRITER` -- rather than
    exempting them outright, while still enforcing structural integrity
    (unique id, rev-continuity) on them as before.
  - `legacy_id` = the original collided literal (e.g. "SEC-001").
  - `collision_group` = the literal itself, so every occurrence of the same
    collided literal (e.g. all 5 historical `SEC-001`s) groups together.
  - `occurrence_key` = a deterministic sha1-derived key of (file, line,
    literal), used for IDEMPOTENCY: a re-run recomputes the same key for the
    same occurrence and skips it if a legacy row with that key already
    exists in the registry. This is intentionally decoupled from the `<date>`
    embedded in `id` (which reflects the day a given occurrence was FIRST
    backfilled and never changes thereafter) so idempotency holds even if the
    tool is re-run on a later date.

NON-DESTRUCTIVE: this tool NEVER modifies, reorders, or deletes anything in
the scanned corpus files -- it only APPENDS rows to the registry via
idgov.registry.append() (itself append-only under idgov.registry.Lock).

Break-glass gated: requires DZP_ALLOW_ISSUE_ID_OVERRIDE=1 (the SAME override
named in spec §5.1's "5th independent override" -- backfill/migration only).
Loud on stderr either way (present or absent), never silent.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import pathlib
import re
import sys

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from idgov import grammar, registry  # noqa: E402

DEFAULT_REGISTRY_PATH = ".protocol-state/issue-registry.jsonl"
OVERRIDE_ENV = "DZP_ALLOW_ISSUE_ID_OVERRIDE"
# SEC-IDGOV-F-002: single-sourced from idgov.registry (engine.validate() now
# enforces this same sentinel positively -- see engine.py) instead of a
# locally-duplicated literal that could drift.
LEGACY_ATTESTED_WRITER = registry.LEGACY_ATTESTED_WRITER

_FAMILY_PREFIX_RE = re.compile(r"^(" + "|".join(sorted(grammar.FAMILIES)) + r")-")

# Mirrors scripts/check_issue_ids.py::_TRAILING_PUNCT_RE (idgov item 5) --
# ID_SHAPED_RE's char class includes a literal dot, so a sentence-final
# citation like "SEC-001." swallows the period into the match. Stripping it
# here keeps a backfilled legacy_id/collision_group aligned with the same
# literal the gate itself would classify, instead of fragmenting the group
# into "SEC-001" and "SEC-001." for what is really one collided literal.
_TRAILING_PUNCT_RE = re.compile(r"[.,;:!?)\]}\"']+$")


def _extract_family(literal: str):
    """Best-effort family extraction from an id-shaped literal. Every token
    scan() locates is matched via grammar.ID_SHAPED_RE, which always starts
    with a FAMILIES member + '-', so this should always match in practice;
    None is a defensive fallback only, never expected in normal operation."""
    m = _FAMILY_PREFIX_RE.match(literal)
    return m.group(1) if m else None


class CorpusScanError(Exception):
    """Finding 6 (CodeRabbit PR#112, P2): raised when scan() could not read
    or decode one or more corpus files/directories, UNLESS the caller opted
    into a partial scan via allow_partial=True. Carries the list of
    (path, reason) offenders so the caller can report them."""
    def __init__(self, offenders):
        self.offenders = offenders
        super().__init__(
            "corpus scan encountered unreadable/undecodable path(s): "
            + ", ".join(f"{p!r} ({why})" for p, why in offenders)
        )


def scan(corpus_paths, *, allow_partial: bool = False) -> list:
    """Walk each path in corpus_paths and return a list of occurrence dicts:
    {"file": <label>, "line": <1-based lineno>, "literal": <id-shaped token>,
    "ordinal": <0-based index of this occurrence among duplicates of the
    same (file, line, literal) tuple, in scan order>}.

    A directory is walked recursively for *.md files (sorted, deterministic
    order). A file is scanned directly, using the path AS GIVEN as its label
    (so callers/tests get predictable, caller-controlled file labels). A
    NONEXISTENT path is still skipped silently (not an error -- a corpus
    entry that legitimately doesn't exist yet, e.g. an optional directory,
    is not the same class of problem as a path that exists but could not be
    READ).

    Finding 6 (CodeRabbit PR#112, P2): a path that DOES exist but is
    unreadable (permission denied) or undecodable (not valid UTF-8) used to
    be silently folded into "zero occurrences", and the caller (run_backfill)
    reported success regardless -- a corpus scan that silently skipped part
    of its input is indistinguishable from one that genuinely found nothing
    to backfill. Such a path is now COLLECTED as an offender; by default
    (allow_partial=False) scan() raises CorpusScanError instead of returning
    a partial result. Pass allow_partial=True for an explicit, caller-chosen
    partial migration.

    Multiple literals on one line, and the same literal appearing on multiple
    lines/files, each produce their own distinct occurrence (finding 7: two
    identical literals on the SAME line are no longer collapsed -- see the
    per-line `ordinal` counter below and occurrence_key()'s handling of it).
    """
    occurrences = []
    offenders = []
    for cp in corpus_paths:
        p = pathlib.Path(cp)
        if p.is_dir():
            for f in sorted(p.rglob("*.md")):
                occ, err = _scan_file(f, str(f))
                occurrences.extend(occ)
                if err:
                    offenders.append((str(f), err))
        elif p.is_file():
            occ, err = _scan_file(p, str(cp))
            occurrences.extend(occ)
            if err:
                offenders.append((str(cp), err))
        # else: nonexistent path -- skip silently (legitimately absent corpus
        # entry, not a read failure)
    if offenders and not allow_partial:
        raise CorpusScanError(offenders)
    return occurrences


def _scan_file(path: pathlib.Path, label: str):
    """Returns (occurrences, error_reason). error_reason is None on success,
    else a short string describing why the file could not be scanned
    (finding 6) -- occurrences is always [] when error_reason is set."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return [], f"OSError: {e}"
    except UnicodeDecodeError as e:
        return [], f"UnicodeDecodeError: {e}"
    out = []
    # Finding 7: an occurrence_key ordinal, scoped per (label, line, literal)
    # within THIS file scan, so a SECOND identical literal on the same line
    # gets a distinguishable identity instead of silently colliding with the
    # first's key and being skipped as "already seen".
    dup_counts: dict = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in grammar.ID_SHAPED_RE.finditer(line):
            literal = _TRAILING_PUNCT_RE.sub("", m.group(0))
            if literal:
                dup_key = (label, lineno, literal)
                ordinal = dup_counts.get(dup_key, 0)
                dup_counts[dup_key] = ordinal + 1
                out.append({"file": label, "line": lineno, "literal": literal,
                             "ordinal": ordinal})
    return out, None


def occurrence_key(file, line, literal, ordinal: int = 0) -> str:
    """Deterministic short hash of (file, line, literal[, ordinal]) -- the
    identity of a single scanned occurrence, used for idempotent re-runs.

    Finding 7 (CodeRabbit PR#112, P2, back-compat-preserving fix): the FIRST
    occurrence of a given (file, line, literal) tuple (ordinal=0, the
    overwhelmingly common case and the ONLY shape that has ever existed in
    the already-backfilled 1229-row registry) keeps generating the EXACT
    SAME key as before this fix -- the hash input is byte-identical to the
    pre-fix scheme when ordinal==0. Only a SECOND+ duplicate literal on the
    same line (ordinal>=1, which the pre-fix scheme silently collapsed into
    occurrence #1 and therefore never actually produced a registry row for)
    gets a NEW, distinguishing key shape. This is purely additive: no
    existing legacy row's occurrence_key can be invalidated by this change,
    and a re-run remains idempotent (the same ordinal on a re-scan always
    re-derives the same key).
    """
    if ordinal:
        h = hashlib.sha1(f"{file}::{line}::{literal}::{ordinal}".encode("utf-8"),
                          usedforsecurity=False)
    else:
        h = hashlib.sha1(f"{file}::{line}::{literal}".encode("utf-8"),
                          usedforsecurity=False)
    return h.hexdigest()[:10]


def to_legacy_row(occ: dict, collision_group: str, *, date=None,
                   protocol_version=None, origin=None) -> dict:
    """Build a legacy=True `assign` event row for one occurrence. Field set
    mirrors idgov.engine.mint()'s emitted event dict (same schema, unknowns
    set to null) plus the 3 legacy-specific fields already reserved on a
    real minted row's schema (legacy/legacy_id/collision_group) and one new
    field, occurrence_key, used for idempotent dedupe (see module docstring).
    """
    literal = occ["literal"]
    key = occurrence_key(occ["file"], occ["line"], literal, occ.get("ordinal", 0))
    d = date or _today()
    new_id = f"{literal}-LEGACY-{d}-{key}"
    return {
        "schema": registry.SCHEMA_VERSION, "event": "assign", "id": new_id, "rev": 1,
        "family": _extract_family(literal), "subsystem": None, "version": None,
        "tag": None, "seq": None,
        "attested_writer": LEGACY_ATTESTED_WRITER, "writer_token_id": None,
        "reported_by": None, "assigned_at": _now_iso(),
        "protocol_version": protocol_version, "origin": origin or "backfill",
        "title": f"legacy occurrence of {literal} ({occ['file']}:{occ['line']})",
        "state": "open", "prev_state": None,
        "cwe": None, "owasp": None, "location": f"{occ['file']}:{occ['line']}",
        "supersedes": None, "superseded_by": None, "review_ref": None,
        "legacy": True, "legacy_id": literal, "collision_group": collision_group,
        "occurrence_key": key,
    }


def _today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _existing_occurrence_keys(events) -> set:
    return {
        ev.get("occurrence_key")
        for ev in events
        if ev.get("event") == "assign" and ev.get("legacy") and ev.get("occurrence_key")
    }


def _registry_corpus_collisions(registry_path, corpus_paths) -> list:
    """SEC-IDGOV item 2: return the corpus_paths entries whose RESOLVED path
    is identical to the resolved registry_path -- appending JSONL rows onto a
    protected prose doc (which FEAT-GUARD-001's byte-prefix guard would NOT
    catch, since the JSONL append IS a byte-prefix-preserving append) would
    silently corrupt that document's content. Exact top-level path equality
    only, mirroring how --registry/--corpus are given on the command line.

    Megumi Phase F re-review (Phase G prerequisite): a Path.resolve() OSError
    (registry path OR any individual corpus entry) used to be swallowed into
    "no collision for this path" (fail-OPEN) -- a resolve failure silently
    SKIPPED that path from the comparison instead of refusing, so a
    pathological/unresolvable path could dodge the very guard meant to catch
    it. An unresolvable path is now treated as UNSAFE, not proven safe: this
    function no longer catches OSError itself -- it PROPAGATES, and the
    caller (run_backfill) turns it into the same loud-stderr, write-nothing
    refusal as a genuine detected collision (see run_backfill)."""
    reg_resolved = pathlib.Path(registry_path).resolve()
    offenders = []
    for cp in corpus_paths:
        if pathlib.Path(cp).resolve() == reg_resolved:
            offenders.append(str(cp))
    return offenders


def run_backfill(registry_path, corpus_paths, *, protocol_version=None,
                  origin=None, date=None, allow_partial: bool = False,
                  dry_run: bool = False) -> dict:
    """Scan corpus_paths, append one legacy row per NEW occurrence (skipping
    occurrences whose occurrence_key already has a legacy row in the
    registry), and return a summary dict. Never touches the corpus files.

    SEC-IDGOV-F-004: self-guards the DZP_ALLOW_ISSUE_ID_OVERRIDE break-glass
    gate INSIDE this function (mirrors how idgov.engine.mint() enforces writer
    identity inside itself, not just in the CLI wrapper) -- a direct
    import/call of run_backfill() bypassing main()'s own early check is
    refused too, never silently writes. Loud on stderr either way. This
    override is NOT required when dry_run=True (finding 9): a dry run makes
    no writes at all, so gating it behind the same break-glass as the real
    write path would defeat its own purpose (checking BEFORE deciding to
    invoke the override).

    Finding 8 (CodeRabbit PR#112, P2): the read -> dedupe -> append sequence
    below now runs under ONE held registry.Lock spanning the WHOLE batch
    (plus one pre-batch backup), instead of each row's registry.append()
    independently acquiring/releasing its own lock -- closes the window
    where two concurrent backfill runs could both read the same
    existing_keys snapshot and each append a duplicate legacy row for the
    same occurrence. registry.append()'s OWN internal Lock(reg_path) call is
    safely REENTRANT here (same pid/ppid token), matching the existing
    documented reentrancy contract (registry.Lock, tests/test_issue_id_
    registry.py::test_append_within_held_lock).
    """
    if not dry_run and os.environ.get(OVERRIDE_ENV) != "1":
        print(f"[backfill] REFUSED: {OVERRIDE_ENV}=1 is required to run the legacy-id "
              f"backfill (backfill/migration operations only). No rows written.",
              file=sys.stderr)
        raise PermissionError(f"{OVERRIDE_ENV}=1 is required to run run_backfill()")

    # SEC-IDGOV item 2: registry/corpus path-collision guard. Fail-CLOSED
    # (Megumi Phase F re-review): a Path.resolve() OSError while checking is
    # treated the same as a genuine detected collision -- refuse, write
    # nothing, loud stderr -- rather than letting the check silently skip
    # that path (an unresolvable path is unsafe, not proven safe).
    try:
        collisions = _registry_corpus_collisions(registry_path, corpus_paths)
    except OSError as e:
        print(f"[backfill] REFUSED: could not resolve --registry path "
              f"{str(registry_path)!r} or a --corpus target to check for a path "
              f"collision ({e}) -- an unresolvable path is treated as unsafe, not safe. "
              f"No rows written.", file=sys.stderr)
        raise ValueError(
            f"path-collision check failed: unable to resolve path(s): {e}"
        ) from e
    if collisions:
        print(f"[backfill] REFUSED: --registry path {str(registry_path)!r} resolves to "
              f"the same file as --corpus target(s) {collisions!r} -- refusing to append "
              f"registry JSONL onto a corpus target. No rows written.", file=sys.stderr)
        raise ValueError(
            f"registry path collides with corpus target(s): {collisions}"
        )

    occurrences = scan(corpus_paths, allow_partial=allow_partial)

    if dry_run:
        # Write-free: read for a preview only, take no lock, touch nothing.
        events = registry.read_events(registry_path)
        existing_keys = _existing_occurrence_keys(events)
        groups = set()
        would_write = 0
        for occ in occurrences:
            groups.add(occ["literal"])
            key = occurrence_key(occ["file"], occ["line"], occ["literal"], occ.get("ordinal", 0))
            if key in existing_keys:
                continue
            existing_keys.add(key)
            would_write += 1
        return {
            "occurrences": len(occurrences),
            "new_rows": would_write,
            "collision_groups": len(groups),
            "dry_run": True,
        }

    reg_path_obj = pathlib.Path(registry_path)
    groups = set()
    new_rows = 0
    with registry.Lock(reg_path_obj):
        registry._backup_before_append(reg_path_obj)
        events = registry.read_events(registry_path)
        existing_keys = _existing_occurrence_keys(events)
        for occ in occurrences:
            groups.add(occ["literal"])
            key = occurrence_key(occ["file"], occ["line"], occ["literal"], occ.get("ordinal", 0))
            if key in existing_keys:
                continue
            row = to_legacy_row(occ, occ["literal"], date=date,
                                 protocol_version=protocol_version, origin=origin)
            registry.append(registry_path, row)
            existing_keys.add(key)
            new_rows += 1
    return {
        "occurrences": len(occurrences),
        "new_rows": new_rows,
        "collision_groups": len(groups),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Non-destructive legacy-id backfill for the FEAT-IDGOV-001 issue registry.")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY_PATH,
                         help=f"registry JSONL path (default: {DEFAULT_REGISTRY_PATH})")
    parser.add_argument("--corpus", action="append", required=True,
                         help="corpus file or directory to scan (repeatable)")
    parser.add_argument("--protocol-version", default=None)
    parser.add_argument("--origin", default="backfill")
    # Finding 9 (CodeRabbit PR#112, P2): a write-free preview, documented in
    # AI_INSTRUCTIONS.md / PROTOCOL_QUICKSTART.md's activation flow but never
    # actually implemented -- this closes that gap. Does NOT require
    # OVERRIDE_ENV (no writes happen); clearly reports the override that WILL
    # be required for the real run.
    parser.add_argument("--dry-run", action="store_true",
                         help="scan and report what WOULD be backfilled, without writing "
                              "anything or requiring the override")
    # Finding 6 (CodeRabbit PR#112, P2): scan() now refuses (CorpusScanError)
    # on any unreadable/undecodable corpus path by default; this is the
    # explicit, scoped opt-in for a genuinely-intended partial migration.
    parser.add_argument("--allow-partial", action="store_true",
                         help="proceed even if some corpus paths could not be read/decoded "
                              "(default: refuse on any such path)")
    return parser


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = _build_parser().parse_args(argv)

    if args.dry_run:
        print(f"[backfill] --dry-run: scanning only, nothing will be written. The real run "
              f"additionally requires {OVERRIDE_ENV}=1.", file=sys.stderr)
        try:
            summary = run_backfill(args.registry, args.corpus,
                                    protocol_version=args.protocol_version, origin=args.origin,
                                    allow_partial=args.allow_partial, dry_run=True)
        except CorpusScanError as e:
            print(f"[backfill] REFUSED: {e}. Pass --allow-partial to scan anyway.",
                  file=sys.stderr)
            return 2
        print(f"[backfill] DRY RUN occurrences={summary['occurrences']} "
              f"would_write_new_legacy_rows={summary['new_rows']} "
              f"collision_groups={summary['collision_groups']}")
        return 0

    if os.environ.get(OVERRIDE_ENV) != "1":
        print(f"[backfill] REFUSED: {OVERRIDE_ENV}=1 is required to run the legacy-id "
              f"backfill (backfill/migration operations only). No rows written.",
              file=sys.stderr)
        return 2

    print(f"[backfill] {OVERRIDE_ENV}=1 override ACTIVE -- legacy backfill running "
          f"(non-destructive, append-only).", file=sys.stderr)

    try:
        summary = run_backfill(args.registry, args.corpus,
                                protocol_version=args.protocol_version, origin=args.origin,
                                allow_partial=args.allow_partial)
    except CorpusScanError as e:
        print(f"[backfill] REFUSED: {e}. Pass --allow-partial to include a partial scan "
              f"anyway. No rows written.", file=sys.stderr)
        return 2
    print(f"[backfill] occurrences={summary['occurrences']} "
          f"new_legacy_rows={summary['new_rows']} "
          f"collision_groups={summary['collision_groups']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
