# DZP downstream update check — READ-ONLY (PowerShell parity).
# Compares THIS install's protocol_version against the canonical 'release' branch.
#
# ONE-WAY INVARIANT: only READS from canonical (raw VERSION.md over HTTPS). Never pushes
# to, modifies, or writes the canonical DZP dev repo. Downstream consumes + reports issues only.
$ErrorActionPreference = "SilentlyContinue"

$Canon   = "https://github.com/DewyHRite/Domain-Zero-Protocol"
$RawVer  = "https://raw.githubusercontent.com/DewyHRite/Domain-Zero-Protocol/release/VERSION.md"
$Issues  = "$Canon/issues"
$Security = "$Canon/security/advisories"

$Repo  = (git rev-parse --show-toplevel 2>$null)
if (-not $Repo) { $Repo = (Get-Location).Path }
$state = Join-Path $Repo ".protocol-state/project-state.json"

$localVer = "?"
if (Test-Path $state) {
    $m = Select-String -Path $state -Pattern '"protocol_version"\s*:\s*"([0-9]+\.[0-9]+\.[0-9]+)"' | Select-Object -First 1
    if ($m) { $localVer = $m.Matches[0].Groups[1].Value }
}

$canonVer = ""
try {
    $body = Invoke-RestMethod -Uri $RawVer -TimeoutSec 15
    $mm = [regex]::Match($body, '[0-9]+\.[0-9]+\.[0-9]+')
    if ($mm.Success) { $canonVer = $mm.Value }
} catch { }

Write-Host "Canonical source : $Canon (branch: release)"
Write-Host "Local version    : $localVer"
if (-not $canonVer) {
    Write-Host "Canonical version: (unreachable - check network, or the 'release' branch is not published yet)"
    Write-Host "Status           : UNKNOWN"
} elseif ($localVer -eq $canonVer) {
    Write-Host "Canonical version: $canonVer"
    Write-Host "Status           : UP TO DATE"
} else {
    Write-Host "Canonical version: $canonVer"
    Write-Host "Status           : UPDATE AVAILABLE (local $localVer -> canonical $canonVer)"
    Write-Host "How to update    : pull the published 'release' branch from canonical (one-way). Never push upstream."
}
Write-Host ""
Write-Host "Report an issue  : $Issues"
Write-Host "Report security  : $Security"
