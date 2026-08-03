# FEAT-IDGOV-001 Sukuna-signed issue-id wrapper (residentid-sukuna.ps1) --
# PowerShell parity with scripts/residentid-sukuna.sh; see that file's header
# for the full contract (Toji DESIGN-001 remediation, v9.10.1 Block B2).
#
# The ONLY sanctioned path that stamps attested_writer=sukuna: computes a
# FRESH random nonce per invocation, signs it with Sukuna's own per-wrapper
# token (idgov.identity.sign), exports IDGOV_SIG/IDGOV_NONCE, then invokes
# issue_id.py passing through every argument untouched.
#
# Repo root is resolved from THIS SCRIPT's own location ($PSScriptRoot), not
# the caller's cwd, so `residentid-sukuna.ps1` behaves identically no matter
# where it is invoked from.
#
# See protocol/skills/resident-mint.md and
# docs/superpowers/specs/2026-07-13-issue-id-governance-design.md.
#
# Usage: scripts/residentid-sukuna.ps1 <check|list|new|state|validate> [args...]
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
# INVARIANT (ISS-IDGOVPS-001) -- THE $SignScript HERE-STRING MUST CONTAIN ZERO
# DOUBLE-QUOTE CHARACTERS. The writer name is passed as a DATA argument
# (sys.argv[2]), exactly as $ScriptDir already was, and for the same reason.
#
# Windows PowerShell 5.1 -- and PowerShell 7.x running with
# $PSNativeCommandArgumentPassing='Legacy' -- strip embedded `"` characters
# while building a native command line. `identity.provision("<writer>")` then
# reaches Python as `identity.provision(<writer>)`, a bare name, and raises
# NameError. Every mint (`new`) and state transition (`state`) via this wrapper
# failed closed on those hosts. PowerShell 7.x in its DEFAULT mode preserves
# the quotes, which is why the defect survived review.
#
# DO NOT "FIX" A REGRESSION HERE BY ESCAPING THE QUOTES (\"). That repairs 5.1
# and simultaneously BREAKS 7.3+ default mode, which passes the literal
# backslash through to Python as a SyntaxError. With zero `"` characters there
# is nothing for the legacy mangler to strip, so this is correct on 5.1, on 7.x
# default, and on 7.x Legacy with no host detection or version branching.
#
# Machine-enforced by tests/test_ps1_sign_script_quote_invariant.py -- not
# comment-enforced. Run it after touching this block.
$SignScript = @'
import secrets, sys
sys.path.insert(0, sys.argv[1])
from idgov import identity
token_id = identity.provision(sys.argv[2])
nonce = secrets.token_hex(16)
sig = identity.sign(token_id, nonce)
print(nonce)
print(sig)
'@

$signOut = & python -c $SignScript $ScriptDir 'sukuna'
if ($LASTEXITCODE -ne 0) {
    # BUG-IDGOVPS-001: stderr is written EXPLICITLY here, not through the
    # Write-Error cmdlet. Under the $ErrorActionPreference = "Stop" set above, that
    # cmdlet raises a TERMINATING error -- the script dies on that line and the
    # `exit 2` below never runs, so every caller saw exit 1. The documented
    # "signing failed = 2" contract had therefore never been observable on any host
    # or engine (reproduced on both powershell 5.1 and pwsh 7, with a positive
    # control). [Console]::Error.WriteLine() is a plain write with no error-action
    # semantics, so the intended exit code is actually reached. Do not "tidy" this
    # back; tests/test_ps1_mint_wrapper_exit_contract.py fails if you do.
    [Console]::Error.WriteLine("residentid-sukuna: failed to sign request (Sukuna token provisioning/signing error)")
    exit 2
}

$lines = @($signOut) | Where-Object { $_ -ne "" }
if ($lines.Count -lt 2) {
    [Console]::Error.WriteLine("residentid-sukuna: malformed signing output")
    exit 2
}
$env:IDGOV_NONCE = $lines[0]
$env:IDGOV_SIG = $lines[1]

& python (Join-Path $ScriptDir "issue_id.py") @args
exit $LASTEXITCODE
