#!/usr/bin/env python3
"""FEAT-IDGOV-001 grammar: the single source of ID syntax (imported by CLI, gate,
backfill, validator). Three productions (spec v3 §3.1) + a loose id-shaped heuristic
(Sukuna F1) so bare/malformed IDs in prose are catchable, not silently missed."""
import re

FAMILIES = frozenset({"SEC", "BUG", "FEAT", "IMPL", "CODE", "ISS", "TEST", "MF"})
_FAM = r"(?:" + "|".join(sorted(FAMILIES)) + r")"
_SUB = r"[A-Z][A-Z0-9]{1,23}"
_VER = r"\d+\.\d+\.\d+"
_TAG = r"[A-Z][A-Z0-9]{0,23}"
_SEQ = r"\d{3,}"

# Three productions unioned. Anchored full-match acceptance pattern.
# NOTE: TAG may span multiple dash-joined segments (e.g. SEMVER-CORE).
ISSUE_ID_RE = re.compile(
    rf"^{_FAM}-{_SUB}(?:-{_VER}(?:-{_TAG}(?:-{_TAG})*)?)?-{_SEQ}\Z"
)
# Loose heuristic: ANYTHING id-shaped (family prefix + dash + alnum/dot/dash run).
ID_SHAPED_RE = re.compile(rf"\b{_FAM}-[0-9A-Z][0-9A-Z.\-]*\b")

# SEC-IDGOV-F-001 (P0): the CANONICAL shape scripts/backfill_issue_registry.py
# ::to_legacy_row() produces -- f"{literal}-LEGACY-{YYYYMMDD}-{occurrence_key}"
# where occurrence_key is a 10-char lowercase-hex sha1 prefix. Bounds what
# engine.validate() will accept as a legacy id: a legacy=True row MUST match
# this exact shape, closing the prior unbounded exemption (any legacy=True
# row skipped grammar entirely, letting a hand-forged row carry a clean,
# citable, well-formed id -- see engine.validate() for the positive check).
LEGACY_ID_RE = re.compile(r"^.+-LEGACY-\d{8}-[0-9a-f]{10}\Z")

def is_wellformed(s: str) -> bool:
    return bool(ISSUE_ID_RE.match(s))

def is_id_shaped(s: str) -> bool:
    return bool(ID_SHAPED_RE.fullmatch(s))

def is_legacy_id(s: str) -> bool:
    return bool(LEGACY_ID_RE.match(s))

_PARSE_RE = re.compile(
    rf"^(?P<family>{_FAM})-(?P<subsystem>{_SUB})"
    rf"(?:-(?P<version>{_VER})(?:-(?P<tag>{_TAG}(?:-{_TAG})*))?)?"
    rf"-(?P<seq>{_SEQ})\Z"
)

def parse_id(s: str) -> dict:
    m = _PARSE_RE.match(s)
    if not m:
        raise ValueError(f"malformed issue id: {s!r}")
    d = m.groupdict()
    return {"family": d["family"], "subsystem": d["subsystem"],
            "version": d["version"], "tag": d["tag"], "seq": int(d["seq"])}

def format_id(family, subsystem, seq, version=None, tag=None) -> str:
    parts = [family, subsystem]
    if version: parts.append(version)
    if tag: parts.append(tag)
    parts.append(f"{int(seq):03d}")
    result = "-".join(parts)
    if not is_wellformed(result):
        raise ValueError(f"format_id produced malformed id: {result!r}")
    return result

def counter_key(parsed: dict) -> tuple:
    return (parsed["family"], parsed["subsystem"], parsed["version"], parsed["tag"])
