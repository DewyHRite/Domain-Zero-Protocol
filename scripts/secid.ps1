# FEAT-IDGOV-001 Megumi-signed issue-id wrapper (secid.ps1) -- PowerShell
# parity with scripts/secid.sh; see that file's header for the full contract.
#
# The ONLY sanctioned path that stamps attested_writer=megumi: computes a
# FRESH random nonce per invocation, signs it with Megumi's per-wrapper token
# (idgov.identity.sign), exports IDGOV_SIG/IDGOV_NONCE, then invokes
# issue_id.py passing through every argument untouched.
#
# Repo root is resolved from THIS SCRIPT's own location ($PSScriptRoot), not
# the caller's cwd, so `secid.ps1` behaves identically no matter where it is
# invoked from.
#
# See docs/superpowers/plans/2026-07-14-issue-id-governance.md Task D2 and
# docs/superpowers/specs/2026-07-13-issue-id-governance-design.md.
#
# Usage: scripts/secid.ps1 <check|list|new|state|validate> [args...]
#
# SEC-IDGOV-D-003 (P3, least-privilege): check/list/validate are READ-ONLY --
# their output never depends on a signature, so signing for them is unnecessary
# key-material handling and a needless Megumi-token-provisioning side effect on
# a plain read. Only new/state (writer-authorized mutations) sign.
$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot

if ($args.Count -gt 0 -and @("check", "list", "validate") -contains $args[0]) {
    & python (Join-Path $ScriptDir "issue_id.py") @args
    exit $LASTEXITCODE
}

# Pass ScriptDir as a DATA argument (sys.argv[1]) rather than interpolating it
# into the Python source string -- mirrors scripts/secid.sh's B6-style
# convention (see scripts/brain-index-hook.sh) and scripts/brain-index-hook's
# rationale: interpolation breaks on paths containing quotes/apostrophes.
$SignScript = @'
import secrets, sys
sys.path.insert(0, sys.argv[1])
from idgov import identity
token_id = identity.provision("megumi")
nonce = secrets.token_hex(16)
sig = identity.sign(token_id, nonce)
print(nonce)
print(sig)
'@

$signOut = & python -c $SignScript $ScriptDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "secid: failed to sign request (Megumi token provisioning/signing error)"
    exit 2
}

$lines = @($signOut) | Where-Object { $_ -ne "" }
if ($lines.Count -lt 2) {
    Write-Error "secid: malformed signing output"
    exit 2
}
$env:IDGOV_NONCE = $lines[0]
$env:IDGOV_SIG = $lines[1]

& python (Join-Path $ScriptDir "issue_id.py") @args
exit $LASTEXITCODE
