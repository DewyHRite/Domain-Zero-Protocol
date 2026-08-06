#!/usr/bin/env sh
# scripts/lib/python-probe.sh
#
# Shared PEP 394-safe Python 3 interpreter probe for DZP POSIX wrappers
# (Toji audit CODE-001, HIGH, 2026-08-03,
# audits/2026-08-03-toji-macos-linux-support-v9-12-planning.md; remediated
# v9.12.0 Wave B1). Extracted from the working python3-first-then-python
# pattern that already existed in scripts/verify-protocol.sh (pre-B1) --
# every OTHER POSIX wrapper in this repo called bare `python` directly,
# which PEP 394 explicitly permits Unix distributors to omit entirely (some
# ship ONLY `python3`), and whose meaning is otherwise environment-dependent
# where it does exist.
#
# CONTRACT
#   - Source this file, then call dzp_python_probe().
#   - On success: sets DZP_PYTHON to "python3" or "python" (whichever
#     resolves first AND passes the version check below) and returns 0.
#   - On failure (no interpreter found that is BOTH present on PATH and a
#     compatible Python 3): sets DZP_PYTHON to the empty string and
#     returns 1. A present-but-incompatible candidate (Python 2, or a
#     Python 3 older than DZP_PYTHON_MIN_MINOR below) is treated IDENTICALLY
#     to an absent one -- the caller cannot distinguish "not found" from
#     "found but rejected" from the return value alone, by design (CODE-002,
#     MEDIUM, 2026-08-06, audits/2026-08-06-toji-v9-12-0-recent-work.md: the
#     caller's existing "no interpreter" error path is already explicit and
#     actionable, so reusing it for a rejected candidate needs no new
#     messaging plumbing here).
#   - VERSION VALIDATION (CODE-002 remediation): `command -v` only proves a
#     name resolves to SOME executable on PATH -- it says nothing about what
#     that executable actually is. PEP 394 explicitly permits `python` to
#     resolve to Python 2, Python 3, or nothing at all, distro-dependent.
#     Before accepting either candidate, this probe actually INVOKES it with
#     a `sys.version_info` assertion (see `_dzp_python_is_valid` below) and
#     only accepts a candidate that reports Python 3 at or above
#     DZP_PYTHON_MIN_MINOR -- this repository's real floor (requires
#     `zoneinfo`, stdlib since 3.9; see requirements-clock.txt and
#     IMPL-002, same audit). This closes the gap where a `python` alias
#     pointing at Python 2 (or an ancient Python 3) was returned to the
#     caller as if it were proven Python-3-safe.
#   - NEVER calls `exit` itself. Callers in this repo disagree on purpose
#     about how to fail when no interpreter is found (some hooks warn and
#     skip a best-effort stage, some fail closed and block) -- this probe
#     stays policy-neutral and lets each caller decide.
#   - Pure POSIX sh (no bashisms): safe to source from both
#     `#!/usr/bin/env sh` and `#!/usr/bin/env bash` wrappers.
#
# USAGE (from a caller script; repo root/self-location resolved from the
# CALLER's own path, per this repo's established `SCRIPT_DIR=$(cd
# "$(dirname "$0")" && pwd)` convention -- never from the working directory,
# which may differ from where the wrapper itself lives, e.g. under a git
# hook or when invoked via an absolute path from an unrelated cwd):
#
#   SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
#   # shellcheck source=lib/python-probe.sh
#   . "$SCRIPT_DIR/lib/python-probe.sh"
#   if ! dzp_python_probe; then
#       echo "myscript: no python3/python interpreter found on PATH" >&2
#       exit 1
#   fi
#   "$DZP_PYTHON" some_script.py
# This repository's real Python 3 floor. session_monitor.py unconditionally
# `import zoneinfo` (stdlib since 3.9) -- see IMPL-002 (MEDIUM, same audit)
# and requirements-clock.txt, which already states 3.9+ as the floor. Kept
# as a single named variable so a future floor change touches one line.
DZP_PYTHON_MIN_MINOR=9

# _dzp_python_is_valid <candidate>
#   Invokes <candidate> with a `sys.version_info` assertion against
#   DZP_PYTHON_MIN_MINOR. Returns 0 only if the candidate IS Python 3 at or
#   above the floor. Returns 1 for anything else: Python 2 (PEP 394 alias),
#   a too-old Python 3, or a name that resolves on PATH but is not actually
#   a working Python interpreter at all (the `-c` invocation itself fails).
#   Output is discarded either way -- this is a pass/fail probe, not a
#   version-string reporter.
_dzp_python_is_valid() {
    "$1" -c "import sys; sys.exit(0 if (sys.version_info[0] == 3 and sys.version_info[1] >= ${DZP_PYTHON_MIN_MINOR}) else 1)" >/dev/null 2>&1
}

dzp_python_probe() {
    DZP_PYTHON=""
    if command -v python3 >/dev/null 2>&1 && _dzp_python_is_valid python3; then
        DZP_PYTHON=python3
        return 0
    fi
    if command -v python >/dev/null 2>&1 && _dzp_python_is_valid python; then
        DZP_PYTHON=python
        return 0
    fi
    return 1
}
