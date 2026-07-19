#!/usr/bin/env python3
"""FEAT-IDGOV-001 general CLI — thin argparse wrapper over scripts/idgov/engine.py.

Subcommands: check | list | new | state | validate.

Writer identity for `new`/`state` is DERIVED from a signature over a fresh nonce,
supplied via the environment (`IDGOV_SIG` / `IDGOV_NONCE`) by a signed wrapper
(scripts/secid.sh / scripts/secid.ps1, Phase D2) — this CLI NEVER accepts a
trusted writer name as an argument (`--reported-by` is free-text provenance
only, e.g. for Toji proxy-mints, and does not affect authorization).

See docs/superpowers/plans/2026-07-14-issue-id-governance.md Task D1 and
docs/superpowers/specs/2026-07-13-issue-id-governance-design.md §4.
"""
import argparse
import json
import os
import pathlib
import re
import sys

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from idgov import engine  # noqa: E402

REPO_ROOT = _HERE.parent
DEFAULT_REGISTRY = REPO_ROOT / ".protocol-state" / "issue-registry.jsonl"
ORIGIN = "Domain Zero Protocol"
_VERSION_RE = re.compile(r"\*\*Version:\*\*\s*v?(\d+\.\d+\.\d+)")


def _protocol_version() -> str:
    """Best-effort current protocol_version, read from VERSION.md (same source
    scripts/distro/assert_version.py treats as authoritative). Never hardcoded
    here so the CLI doesn't drift stale across version bumps."""
    try:
        text = (REPO_ROOT / "VERSION.md").read_text(encoding="utf-8")
    except OSError:
        return "0.0.0-unknown"
    m = _VERSION_RE.search(text)
    return m.group(1) if m else "0.0.0-unknown"


def _require_signature():
    """Reads IDGOV_SIG/IDGOV_NONCE from env. Returns (sig, nonce) or None + prints
    a wrapper-pointer error. Never accepts writer identity from argv."""
    sig = os.environ.get("IDGOV_SIG")
    nonce = os.environ.get("IDGOV_NONCE")
    if not sig or not nonce:
        print(
            "error: missing IDGOV_SIG/IDGOV_NONCE in the environment — invoke this "
            "command via the signed wrapper (scripts/secid.sh or scripts/secid.ps1), "
            "never issue_id.py directly.",
            file=sys.stderr,
        )
        return None
    return sig, nonce


def _cmd_check(args) -> int:
    rec = engine.check(args.registry, args.id)
    if rec is None:
        print("free")
        return 1
    print(json.dumps(rec, sort_keys=True))
    return 0


def _cmd_list(args) -> int:
    rows = engine.list_ids(
        args.registry, family=args.family, subsystem=args.subsystem, state=args.state
    )
    print(json.dumps(rows, sort_keys=True))
    return 0


def _cmd_new(args) -> int:
    creds = _require_signature()
    if creds is None:
        return 2
    signature, nonce = creds
    audit = {}
    if args.cwe is not None:
        audit["cwe"] = args.cwe
    if args.owasp is not None:
        audit["owasp"] = args.owasp
    if args.location is not None:
        audit["location"] = args.location
    if args.review_ref is not None:
        audit["review_ref"] = args.review_ref
    new_id = engine.mint(
        args.registry, args.family, args.subsystem, args.title,
        version=args.version, tag=args.tag, reserved=args.reserved,
        reported_by=args.reported_by, signature=signature, nonce=nonce,
        protocol_version=_protocol_version(), origin=ORIGIN, **audit,
    )
    print(new_id)
    return 0


def _cmd_state(args) -> int:
    creds = _require_signature()
    if creds is None:
        return 2
    signature, nonce = creds
    engine.transition(
        args.registry, args.id, args.new_state,
        signature=signature, nonce=nonce, note=args.note,
    )
    print(f"{args.id}: -> {args.new_state}")
    return 0


def _cmd_validate(args) -> int:
    violations = engine.validate(args.registry)
    for v in violations:
        print(v)
    return 1 if violations else 0


def _add_registry_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--registry", default=DEFAULT_REGISTRY,
        help="path to the JSONL registry (default: .protocol-state/issue-registry.jsonl)",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="issue_id.py",
        description="FEAT-IDGOV-001 issue-id registry CLI (check/list/new/state/validate).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="look up an id: exists (latest record) or free")
    _add_registry_arg(p_check)
    p_check.add_argument("id")
    p_check.set_defaults(func=_cmd_check)

    p_list = sub.add_parser("list", help="list the latest-rev projection, optionally filtered")
    _add_registry_arg(p_list)
    p_list.add_argument("--family")
    p_list.add_argument("--subsystem")
    p_list.add_argument("--state")
    p_list.set_defaults(func=_cmd_list)

    p_new = sub.add_parser(
        "new", help="mint a new id (writer derived from IDGOV_SIG/IDGOV_NONCE, never a CLI flag)"
    )
    _add_registry_arg(p_new)
    p_new.add_argument("family", help="family prefix, e.g. SEC/BUG/FEAT/IMPL/CODE/ISS/TEST/MF")
    p_new.add_argument("--subsystem", required=True)
    p_new.add_argument("--title", required=True)
    p_new.add_argument("--version")
    p_new.add_argument("--tag")
    p_new.add_argument("--reserved", action="store_true")
    p_new.add_argument(
        "--reported-by", dest="reported_by",
        help="free-text provenance only (e.g. 'toji' for a proxy-mint); NOT a writer/authority input",
    )
    p_new.add_argument("--cwe")
    p_new.add_argument("--owasp")
    p_new.add_argument("--location")
    p_new.add_argument("--review-ref", dest="review_ref")
    p_new.set_defaults(func=_cmd_new)

    p_state = sub.add_parser(
        "state", help="transition an id's state (writer derived from IDGOV_SIG/IDGOV_NONCE)"
    )
    _add_registry_arg(p_state)
    p_state.add_argument("id")
    p_state.add_argument("new_state")
    p_state.add_argument("--note")
    p_state.set_defaults(func=_cmd_state)

    p_validate = sub.add_parser(
        "validate", help="full registry integrity check (grammar/uniqueness/seq/rev/legality)"
    )
    _add_registry_arg(p_validate)
    p_validate.set_defaults(func=_cmd_validate)

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return args.func(args)
    # SEC-IDGOV-D-001 (P2, CWE-703): OSError covers PermissionError/TimeoutError plus
    # every other OS-level failure (NotADirectoryError, disk-full ENOSPC/EIO, etc.)
    # that registry.append()'s mkdir/open/fsync calls can raise. Without this, those
    # subclasses escaped uncaught -> raw traceback + Python's default exit 1, which
    # collides with the "1 = domain-negative result" contract (see _cmd_check/_cmd_validate)
    # that Phase E's gate branches on. PermissionError/TimeoutError kept explicit for
    # readability even though both are already OSError subclasses on this Python.
    except (ValueError, OSError, PermissionError, TimeoutError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
