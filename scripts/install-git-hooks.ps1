# Domain Zero Protocol - Git Hook Installer (FEAT-GUARD-001, v9.9.4)
#
# Installs the DZP unified pre-commit hook (publish-branch skip + append-only
# guard + agent/protected-file guard + protocol validation). Git cannot
# auto-install hooks from a clone, so this opt-in installer is part of setup.
#
# Usage:  pwsh scripts/install-git-hooks.ps1   [-Uninstall]
[CmdletBinding()]
param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'

$root = (& git rev-parse --show-toplevel 2>$null)
if (-not $root) { $root = (Get-Location).Path }
$hooksDir = (& git rev-parse --git-path hooks 2>$null)
if (-not $hooksDir) { $hooksDir = Join-Path $root '.git/hooks' }
if (-not [System.IO.Path]::IsPathRooted($hooksDir)) { $hooksDir = Join-Path $root $hooksDir }

$src  = Join-Path $root 'scripts/git-hooks/pre-commit'
$dest = Join-Path $hooksDir 'pre-commit'

# Match either the new unified hook header or the legacy FEAT-REQ-001 header.
function Test-IsDzpHook($path) {
    if (-not (Test-Path $path)) { return $false }
    $content = Get-Content $path -Raw -ErrorAction SilentlyContinue
    return $content -match 'Domain Zero Protocol - (Unified Pre-commit Hook|Agent / Protected-File Commit Guard)'
}

if ($Uninstall) {
    if (Test-IsDzpHook $dest) {
        Remove-Item $dest -Force
        Write-Host "[OK] Removed DZP pre-commit hook: $dest"
    } else {
        Write-Host "[--] No DZP pre-commit hook found at: $dest"
    }
    exit 0
}

if (-not (Test-Path $src)) { Write-Error "Hook source not found: $src"; exit 1 }
if (-not (Test-Path $hooksDir)) { New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null }

if ((Test-Path $dest) -and -not (Test-IsDzpHook $dest)) {
    $backup = "$dest.dzp-backup.$(Get-Date -Format yyyyMMdd_HHmmss)"
    Copy-Item $dest $backup -Force
    Write-Host "[!] Existing pre-commit hook backed up to: $backup"
}

# The POSIX hook runs under Git's bundled sh on Windows too, so install it as the
# canonical pre-commit. (A PowerShell variant lives at scripts/git-hooks/pre-commit.ps1.)
Copy-Item $src $dest -Force
Write-Host "[OK] Installed DZP unified pre-commit hook: $dest"
Write-Host "    Guards: publish-branch skip, append-only docs, protected paths,"
Write-Host "    and protocol state validation."
Write-Host "    Protects: protocol/, .claude/agents/, protocol.config.yaml, and other"
Write-Host "    custom_agent_security.file_protection.immutable_paths entries."
Write-Host "    Override a single commit with: git commit --no-verify"
