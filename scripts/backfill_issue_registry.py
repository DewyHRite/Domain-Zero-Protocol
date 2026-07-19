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


def scan(corpus_paths) -> list:
    """Walk each path in corpus_paths and return a list of occurrence dicts:
    {"file": <label>, "line": <1-based lineno>, "literal": <id-shaped token>}.

    A directory is walked recursively for *.md files (sorted, deterministic
    order). A file is scanned directly, using the path AS GIVEN as its label
    (so callers/tests get predictable, caller-controlled file labels). A
    nonexistent path is skipped silently (fail-soft scanning -- mirrors the
    corpus-path handling style elsewhere in idgov tooling; the caller decides
    whether an empty/partial scan is acceptable).

    Multiple literals on one line, and the same literal appearing on multiple
    lines/files, each produce their own distinct occurrence.
    """
    occurrences = []
    for cp in corpus_paths:
        p = pathlib.Path(cp)
        if p.is_dir():
            for f in sorted(p.rglob("*.md")):
                occurrences.extend(_scan_file(f, str(f)))
        elif p.is_file():
            occurrences.extend(_scan_file(p, str(cp)))
        # else: nonexistent path -- skip silently (fail-soft)
    return occurrences


def _scan_file(path: pathlib.Path, label: str) -> list:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in grammar.ID_SHAPED_RE.finditer(line):
            literal = _TRAILING_PUNCT_RE.sub("", m.group(0))
            if literal:
                out.append({"file": label, "line": lineno, "literal": literal})
    return out


def occurrence_key(file, line, literal) -> str:
    """Deterministic short hash of (file, line, literal) -- the identity of a
    single scanned occurrence, used for idempotent re-runs."""
    h = hashlib.sha1(f"{file}::{line}::{literal}".encode("utf-8"))
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
    key = occurrence_key(occ["file"], occ["line"], literal)
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
                  origin=None, date=None) -> dict:
    """Scan corpus_paths, append one legacy row per NEW occurrence (skipping
    occurrences whose occurrence_key already has a legacy row in the
    registry), and return a summary dict. Never touches the corpus files.

    SEC-IDGOV-F-004: self-guards the DZP_ALLOW_ISSUE_ID_OVERRIDE break-glass
    gate INSIDE this function (mirrors how idgov.engine.mint() enforces writer
    identity inside itself, not just in the CLI wrapper) -- a direct
    import/call of run_backfill() bypassing main()'s own early check is
    refused too, never silently writes. Loud on stderr either way.
    """
    if os.environ.get(OVERRIDE_ENV) != "1":
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

    events = registry.read_events(registry_path)
    existing_keys = _existing_occurrence_keys(events)
    occurrences = scan(corpus_paths)
    groups = set()
    new_rows = 0
    for occ in occurrences:
        groups.add(occ["literal"])
        key = occurrence_key(occ["file"], occ["line"], occ["literal"])
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
    return parser


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = _build_parser().parse_args(argv)

    if os.environ.get(OVERRIDE_ENV) != "1":
        print(f"[backfill] REFUSED: {OVERRIDE_ENV}=1 is required to run the legacy-id "
              f"backfill (backfill/migration operations only). No rows written.",
              file=sys.stderr)
        return 2

    print(f"[backfill] {OVERRIDE_ENV}=1 override ACTIVE -- legacy backfill running "
          f"(non-destructive, append-only).", file=sys.stderr)

    summary = run_backfill(args.registry, args.corpus,
                            protocol_version=args.protocol_version, origin=args.origin)
    print(f"[backfill] occurrences={summary['occurrences']} "
          f"new_legacy_rows={summary['new_rows']} "
          f"collision_groups={summary['collision_groups']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
