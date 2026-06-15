# Domain Zero Protocol - Agent / Protected-File Commit Guard (FEAT-REQ-001, v9.3.0)
# PowerShell equivalent of scripts/git-hooks/pre-commit for PowerShell-driven git
# hook setups. Blocks commits touching DZP-protected paths (Cross-Agent Edit
# Restrictions); protected paths are read from protocol.config.yaml.
$ErrorActionPreference = 'Stop'

$root = (& git rev-parse --show-toplevel 2>$null)
if (-not $root) { $root = (Get-Location).Path }
$config = Join-Path $root 'protocol.config.yaml'

# Check BOTH sides of renames/copies (a rename FROM a protected path must be
# blocked) and include Deletions. --name-status emits "M<TAB>path", "D<TAB>path",
# "R<score><TAB>old<TAB>new", etc.; collect every path column (skip the status code).
$status = & git diff --cached --name-status --find-renames --diff-filter=ACMRD
if (-not $status) { exit 0 }
$staged = @()
foreach ($line in $status) {
    $parts = $line -split "`t"
    if ($parts.Count -ge 2) { $staged += $parts[1..($parts.Count - 1)] | Where-Object { $_ } }
}
if (-not $staged) { exit 0 }

$defaultPaths = @(
    'protocol/', '.claude/agents/',
    '.protocol-state/custom-agent-registry.json',
    '.protocol-state/authorization/', 'protocol.config.yaml'
)

function Get-ProtectedPaths {
    $py = (Get-Command python3 -ErrorAction SilentlyContinue) ?? (Get-Command python -ErrorAction SilentlyContinue)
    if ($py -and (Test-Path $config)) {
        $script = @'
import sys
try:
    import yaml
    cfg = yaml.safe_load(open(sys.argv[1], encoding="utf-8")) or {}
    fp = ((cfg.get("custom_agent_security") or {}).get("file_protection") or {})
    for p in (fp.get("immutable_paths") or []):
        print(str(p).strip())
except Exception:
    sys.exit(7)
'@
        try {
            $out = $script | & $py.Source - $config 2>$null
            if ($LASTEXITCODE -eq 0 -and $out) { return @($out | Where-Object { $_ }) }
        } catch { }
    }
    return $defaultPaths
}

$protected = Get-ProtectedPaths | ForEach-Object { $_.Trim() } | Where-Object { $_ }
$violations = @()
foreach ($f in $staged) {
    $ff = $f.Trim()
    foreach ($p in $protected) {
        if ($ff.StartsWith($p)) { $violations += "  $ff    (protected: $p)" }
    }
}

if ($violations.Count -gt 0) {
    Write-Host ''
    Write-Host '=================================================================='
    Write-Host '  DZP PROTECTED-FILE COMMIT BLOCKED (Cross-Agent Edit Restrictions)'
    Write-Host '=================================================================='
    Write-Host 'Staged changes modify DZP-protected paths:'
    Write-Host ''
    $violations | ForEach-Object { Write-Host $_ }
    Write-Host ''
    Write-Host 'These files are protected. Sanctioned ways to proceed:'
    Write-Host '  1. Invoke Gojo (Mission Control) for an authorized protocol change.'
    Write-Host '  2. Invoke Sukuna via Gojo for system / protocol updates.'
    Write-Host '  3. Override intentionally:  git commit --no-verify'
    Write-Host ''
    Write-Host 'Reference: protocol/CLAUDE.md  (Cross-Agent Edit Restrictions)'
    Write-Host ''
    exit 1
}
exit 0
