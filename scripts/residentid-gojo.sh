#!/usr/bin/env sh
# FEAT-IDGOV-001 Gojo-signed issue-id wrapper (residentid-gojo.sh)
#
# Parity wrapper for scripts/secid.sh (Toji DESIGN-001 remediation, v9.10.1
# Block B2) -- the ONLY sanctioned path that stamps attested_writer=gojo on
# a mint/state transition. Computes a FRESH random nonce per invocation,
# signs it with Gojo's own per-wrapper token (idgov.identity.sign), exports
# IDGOV_SIG/IDGOV_NONCE, then execs issue_id.py passing through every
# argument untouched. issue_id.py itself never accepts a writer name on argv
# -- signing (and therefore writer authority) lives HERE, wrapper-private,
# not as a subcommand of issue_id.py, to keep that attack surface small.
#
# Gojo is authorized (scripts/idgov/engine.py AUTHORITY) for: ISS. Minting/
# transitioning any other family fails closed with a "not authorized" error
# from the engine -- this wrapper does not pre-filter, the engine is the
# single source of truth for the authority matrix.
#
# Identity-model decision (D11 parity, documented in
# protocol/skills/resident-mint.md): scripts/idgov/identity.py derives
# attested_writer from WHICH per-wrapper token signed the call, never from a
# caller-supplied flag. A single generic wrapper accepting a --writer
# argument would let any caller choose to sign as sukuna, gojo, OR yuuji from
# one shared script -- breaking the "identity = which file you invoke" model
# secid.sh already established and reintroducing a confusable-deputy risk.
# Unlike Megumi (no Bash access, hence the mediated-execution model in
# protocol/skills/megumi-secid.md), Sukuna/Gojo/Yuuji all have their OWN Bash
# access already (root/protocol CLAUDE.md tool-access matrix) -- so each gets
# its own hardcoded-identity wrapper, exactly mirroring secid.sh's hardcoded
# "megumi", instead of a mediated flow.
#
# Repo root is resolved from THIS SCRIPT's own location (not the caller's
# cwd), so `residentid-gojo.sh` behaves identically no matter where it is
# invoked from.
#
# See protocol/skills/resident-mint.md and
# docs/superpowers/specs/2026-07-13-issue-id-governance-design.md.
#
# Usage: scripts/residentid-gojo.sh <check|list|new|state|validate> [args...]
#
# SEC-IDGOV-D-003 parity (least-privilege): check/list/validate are READ-ONLY
# -- their output never depends on a signature, so signing for them is
# unnecessary key-material handling and a needless token-provisioning side
# effect on a plain read. Only new/state (writer-authorized mutations) sign.
set -eu

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

case "${1:-}" in
    check|list|validate)
        exec python "$SCRIPT_DIR/issue_id.py" "$@"
        ;;
esac

# B6-style convention (see scripts/brain-index-hook.sh): pass SCRIPT_DIR as a
# DATA argument (sys.argv[1]) rather than interpolating it into the Python
# source string -- interpolation breaks on paths containing apostrophes/quotes.
SIGN_OUT=$(python -c '
import secrets, sys
sys.path.insert(0, sys.argv[1])
from idgov import identity
token_id = identity.provision("gojo")
nonce = secrets.token_hex(16)
sig = identity.sign(token_id, nonce)
print(nonce)
print(sig)
' "$SCRIPT_DIR") || {
    echo "residentid-gojo: failed to sign request (Gojo token provisioning/signing error)" >&2
    exit 2
}

IDGOV_NONCE=$(printf '%s\n' "$SIGN_OUT" | sed -n 1p)
IDGOV_SIG=$(printf '%s\n' "$SIGN_OUT" | sed -n 2p)
export IDGOV_NONCE IDGOV_SIG

exec python "$SCRIPT_DIR/issue_id.py" "$@"
