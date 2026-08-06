#!/usr/bin/env sh
# FEAT-IDGOV-001 Megumi-signed issue-id wrapper (secid.sh)
#
# The ONLY sanctioned path that stamps attested_writer=megumi on a mint/state
# transition: computes a FRESH random nonce per invocation, signs it with
# Megumi's per-wrapper token (idgov.identity.sign), exports
# IDGOV_SIG/IDGOV_NONCE, then execs issue_id.py passing through every
# argument untouched. issue_id.py itself never accepts a writer name on argv
# -- signing (and therefore writer authority) lives HERE, wrapper-private,
# not as a subcommand of issue_id.py, to keep that attack surface small.
#
# Repo root is resolved from THIS SCRIPT's own location (not the caller's
# cwd), so `secid.sh` behaves identically no matter where it is invoked from.
#
# See docs/superpowers/plans/2026-07-14-issue-id-governance.md Task D2 and
# docs/superpowers/specs/2026-07-13-issue-id-governance-design.md.
#
# Usage: scripts/secid.sh <check|list|new|state|validate> [args...]
#
# SEC-IDGOV-D-003 (P3, least-privilege): check/list/validate are READ-ONLY --
# their output never depends on a signature, so signing for them is unnecessary
# key-material handling and a needless Megumi-token-provisioning side effect on
# a plain read. Only new/state (writer-authorized mutations) sign.
set -eu

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

# CODE-001 (Toji audit 2026-08-03, v9.12.0 Wave B1): resolve python3-first
# (PEP 394-safe) rather than bare `python`. Sourced relative to SCRIPT_DIR
# (this wrapper's own location), matching how SCRIPT_DIR itself is already
# resolved above -- see scripts/lib/python-probe.sh.
# shellcheck source=lib/python-probe.sh
. "$SCRIPT_DIR/lib/python-probe.sh"
if ! dzp_python_probe; then
    echo "secid: no python3/python interpreter found on PATH" >&2
    exit 2
fi

case "${1:-}" in
    check|list|validate)
        exec "$DZP_PYTHON" "$SCRIPT_DIR/issue_id.py" "$@"
        ;;
esac

# B6-style convention (see scripts/brain-index-hook.sh): pass SCRIPT_DIR as a
# DATA argument (sys.argv[1]) rather than interpolating it into the Python
# source string -- interpolation breaks on paths containing apostrophes/quotes.
SIGN_OUT=$("$DZP_PYTHON" -c '
import secrets, sys
sys.path.insert(0, sys.argv[1])
from idgov import identity
token_id = identity.provision("megumi")
nonce = secrets.token_hex(16)
sig = identity.sign(token_id, nonce)
print(nonce)
print(sig)
' "$SCRIPT_DIR") || {
    echo "secid: failed to sign request (Megumi token provisioning/signing error)" >&2
    exit 2
}

IDGOV_NONCE=$(printf '%s\n' "$SIGN_OUT" | sed -n 1p)
IDGOV_SIG=$(printf '%s\n' "$SIGN_OUT" | sed -n 2p)
export IDGOV_NONCE IDGOV_SIG

exec "$DZP_PYTHON" "$SCRIPT_DIR/issue_id.py" "$@"
