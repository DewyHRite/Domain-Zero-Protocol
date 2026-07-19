#!/usr/bin/env python3
"""
dzp.py — DZP Script Orchestration Entry Point
Domain Zero Protocol v9.10.1

Thin entry point that resolves the repo root from its own __file__ location
and delegates ALL logic to .protocol-state/script_coordinator.py.

The coordinator returns integer exit codes and prints all output internally.
dzp.py is a thin delegator: it parses args, calls the coordinator, and
propagates the exit code.  It never post-processes coordinator return values.

Usage:
    python dzp.py event <name> [--dry-run] [--json]
    python dzp.py status [--json]
    python dzp.py doctor [--json]

Examples:
    python dzp.py event session-update --dry-run
    python dzp.py event pre-release
    python dzp.py event session-update --json
    python dzp.py status
    python dzp.py doctor

Subcommands:
    event <name>   Run the event's registered steps.
    status         Show registered events/scripts and last run results.
    doctor         Run diagnostics on the orchestration system.

Flags:
    --dry-run      Show what would run without executing anything.
    --json         Print structured JSON output (forwarded to coordinator).

Exit codes:
    0   Success (or dry-run completed).
    1   One or more steps failed.  For fail-closed gate events (pre-release,
        pre-publish, pre-protected-edit) this means the gate is blocking the
        caller (SEC-ORCH-003).
    2   Usage / argument error.
    3   Registry or configuration error (RegistryError or unexpected error).

Developer notes:
    - dzp.py SHIPS in the public distro (USER ruling 2026-07-19, ISS-084/
      ISS-085): this file, .protocol-state/script_coordinator.py, and
      .protocol-state/script_dependencies.yaml (the "orchestration trio")
      are all included via scripts/distro/publish-manifest.yaml's
      include_files/include_state and are covered by the fail-closed
      manifest_completeness_offenders() Scope 5 gate in dzp_publish_core.py.
      This reverses an earlier "DEV-ONLY, must not ship" stance that this
      docstring used to state — that stance is stale and no longer true.
      scripts/distro/** itself (the release/publish TOOLING, as opposed to
      this orchestration trio) remains maintainer-only and is never shipped
      — see the pre-release/pre-publish note below.
    - The engine lives at .protocol-state/script_coordinator.py.
    - The registry lives at .protocol-state/script_dependencies.yaml.
    - Do NOT add output helpers that duplicate coordinator's own printing.
    - The coordinator does not expose a 'verbose' flag; do not forward one.
    - `pre-release` and `pre-publish` are MAINTAINER-ONLY events: their
      steps invoke scripts/distro/assert_version.py and
      scripts/distro/check_version_stamps.py, which are intentionally never
      shipped to a consumer install (scripts/distro/** stays out of the
      distro; see distro.gitignore + publish-manifest.yaml). Running either
      event on a consumer install fails closed with a clear
      "maintainer-only tooling not present in this install" diagnostic
      (script_coordinator.py::_missing_script_diagnostic, P2-b, v9.10.1) —
      this is expected, not a bug. See AI_INSTRUCTIONS.md's "Script
      Orchestration Events" section for the consumer-facing explanation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Resolve repo root from this file's location (repo root = parent of dzp.py)
_REPO_ROOT = Path(__file__).parent.resolve()

# Add .protocol-state to path so we can import script_coordinator
_PROTOCOL_STATE = _REPO_ROOT / ".protocol-state"
if str(_PROTOCOL_STATE) not in sys.path:
    sys.path.insert(0, str(_PROTOCOL_STATE))

from script_coordinator import (  # noqa: E402
    ScriptCoordinator,
    RegistryError,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dzp",
        description="DZP Script Orchestration — Domain Zero Protocol v9.10.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Events: session-update, session-end, ts-start, ts-complete,\n"
            "        pre-protected-edit, pre-release, pre-publish, toji-snapshot\n"
            "\n"
            "Gate events (pre-release, pre-protected-edit, pre-publish) are\n"
            "fail-closed: any failure exits non-zero (blocks CI / caller).\n"
            "\n"
            "pre-release and pre-publish are MAINTAINER-ONLY (maintainer-only;\n"
            "requires unshipped scripts/distro tooling) — their steps invoke\n"
            "scripts/distro/assert_version.py and check_version_stamps.py,\n"
            "which are intentionally never shipped to a consumer install. See\n"
            "AI_INSTRUCTIONS.md's Script Orchestration Events section."
        ),
    )
    sub = parser.add_subparsers(dest="subcommand")

    # event subcommand
    ev = sub.add_parser("event", help="Run a lifecycle event's steps")
    ev.add_argument("name", help="Event name (e.g. session-update, pre-release)")
    ev.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would run; execute nothing",
    )
    ev.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output",
    )

    # status subcommand
    status = sub.add_parser("status", help="Show registered events and last run results")
    status.add_argument("--json", action="store_true", help="Print structured JSON output")

    # doctor subcommand
    doctor = sub.add_parser("doctor", help="Run diagnostics on the orchestration system")
    doctor.add_argument("--json", action="store_true", help="Print structured JSON output")

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Entry-point returning an exit code.

    Exit codes:
        0  — success
        1  — step(s) failed; for fail-closed gates this is a blocking failure
             (SEC-ORCH-003)
        2  — usage error
        3  — registry / configuration error
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.subcommand is None:
        parser.print_help()
        return 2

    coord = ScriptCoordinator(repo_root=_REPO_ROOT)

    if args.subcommand == "event":
        try:
            # coordinator.run_event returns int (0=success, 1=failure).
            # Fail-closed gate events return 1 when a required step fails,
            # preserving SEC-ORCH-003 without any FailClosedError exception.
            return coord.run_event(
                args.name,
                dry_run=args.dry_run,
                json_output=args.json,
            )
        except RegistryError as exc:
            print(f"\n[ERROR] Registry error: {exc}", file=sys.stderr)
            return 3
        except Exception as exc:  # noqa: BLE001
            print(f"\n[ERROR] Unexpected error during event '{args.name}': {exc}", file=sys.stderr)
            return 3

    if args.subcommand == "status":
        try:
            return coord.status(json_output=args.json)
        except Exception as exc:  # noqa: BLE001
            print(f"\n[ERROR] Status failed: {exc}", file=sys.stderr)
            return 3

    if args.subcommand == "doctor":
        try:
            return coord.doctor(json_output=args.json)
        except Exception as exc:  # noqa: BLE001
            print(f"\n[ERROR] Doctor failed: {exc}", file=sys.stderr)
            return 3

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
