# FEAT-IDGOV-001 Gojo-signed issue-id wrapper (residentid-gojo.ps1) --
# PowerShell parity with scripts/residentid-gojo.sh; see that file's header
# for the full contract (Toji DESIGN-001 remediation, v9.10.1 Block B2).
#
# The ONLY sanctioned path that stamps attested_writer=gojo: computes a
# FRESH random nonce per invocation, signs it with Gojo's own per-wrapper
# token (idgov.identity.sign), exports IDGOV_SIG/IDGOV_NONCE, then invokes
# issue_id.py passing through every argument untouched.
#
# Repo root is resolved from THIS SCRIPT's own location ($PSScriptRoot), not
# the caller's cwd, so `residentid-gojo.ps1` behaves identically no matter
# where it is invoked from.
#
# See protocol/skills/resident-mint.md and
# docs/superpowers/specs/2026-07-13-issue-id-governance-design.md.
#
# Usage: scripts/residentid-gojo.ps1 <check|list|new|state|validate> [args...]
#
# SEC-IDGOV-D-003 parity (least-privilege): check/list/validate are READ-ONLY
# -- their output never depends on a signature, so signing for them is
# unnecessary key-material handling and a needless token-provisioning side
# effect on a plain read. Only new/state (writer-authorized mutations) sign.
$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot

if ($args.Count -gt 0 -and @("check", "list", "validate") -contains $args[0]) {
    & python (Join-Path $ScriptDir "issue_id.py") @args
    exit $LASTEXITCODE
}

# Pass ScriptDir as a DATA argument (sys.argv[1]) rather than interpolating it
# into the Python source string -- mirrors scripts/secid.ps1's B6-style
# convention (see scripts/brain-index-hook.sh) and scripts/brain-index-hook's
# rationale: interpolation breaks on paths containing quotes/apostrophes.
$SignScript = @'
import secrets, sys
sys.path.insert(0, sys.argv[1])
from idgov import identity
token_id = identity.provision("gojo")
nonce = secrets.token_hex(16)
sig = identity.sign(token_id, nonce)
print(nonce)
print(sig)
'@

$signOut = & python -c $SignScript $ScriptDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "residentid-gojo: failed to sign request (Gojo token provisioning/signing error)"
    exit 2
}

$lines = @($signOut) | Where-Object { $_ -ne "" }
if ($lines.Count -lt 2) {
    Write-Error "residentid-gojo: malformed signing output"
    exit 2
}
$env:IDGOV_NONCE = $lines[0]
$env:IDGOV_SIG = $lines[1]

& python (Join-Path $ScriptDir "issue_id.py") @args
exit $LASTEXITCODE
