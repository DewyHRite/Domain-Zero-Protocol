# Mask-Off Mode Verification Script
# Version: 1.0
# Purpose: Scan for prohibited themed vocabulary when mask_mode.enabled=false

param(
    [string]$ConfigPath = "protocol.config.yaml",
    [switch]$Strict,
    [switch]$Verbose
)

Write-Host "🎭 Domain Zero Protocol - Mask-Off Verification Script v1.0" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host ""

# Check if config exists
if (!(Test-Path $ConfigPath)) {
    Write-Host "[ERROR] Configuration file not found: $ConfigPath" -ForegroundColor Red
    exit 1
}

# Read config to check mask mode setting
$configContent = Get-Content $ConfigPath -Raw
$maskEnabled = $configContent -match 'mask_mode:\s*[\r\n]+\s*enabled:\s*true'
$strictMode = $configContent -match 'strict_professional:\s*true'

Write-Host "[INFO] Mask Mode Status:" -ForegroundColor Yellow
Write-Host "  - mask_mode.enabled: $(if ($maskEnabled) {'true'} else {'false'})"
Write-Host "  - strict_professional: $(if ($strictMode) {'true'} else {'false'})"
Write-Host ""

if ($maskEnabled) {
    Write-Host "[SKIP] Mask mode is ENABLED (JJK theme active)" -ForegroundColor Green
    Write-Host "       Verification only runs when mask_mode.enabled=false"
    exit 0
}

Write-Host "[INFO] Mask mode is DISABLED - checking for prohibited themed vocabulary..." -ForegroundColor Yellow
Write-Host ""

# Define banned terms (should not appear in mask-off mode)
$bannedTerms = @(
    'Domain Zero',
    'Domain Expansion',
    'The Weight',
    'Trigger 19',
    '🛠️',
    '🛡️',
    '🌀',
    '🎯'
)

# Files to scan (agent output, state files, etc.)
$filesToScan = @(
    '.protocol-state/dev-notes.md',
    '.protocol-state/security-review.md',
    '.protocol-state/trigger-19.md'
)

$violations = @()
$filesScanned = 0

foreach ($file in $filesToScan) {
    if (!(Test-Path $file)) {
        if ($Verbose) {
            Write-Host "[SKIP] File not found: $file" -ForegroundColor Gray
        }
        continue
    }

    $filesScanned++
    $content = Get-Content $file -Raw -ErrorAction SilentlyContinue

    if (!$content) {
        continue
    }

    foreach ($term in $bannedTerms) {
        if ($content -match [regex]::Escape($term)) {
            $violations += [PSCustomObject]@{
                File = $file
                Term = $term
            }
            if ($Verbose) {
                Write-Host "[VIOLATION] Found '$term' in $file" -ForegroundColor Red
            }
        }
    }
}

Write-Host "Files scanned: $filesScanned" -ForegroundColor Cyan
Write-Host ""

if ($violations.Count -eq 0) {
    Write-Host "✅ [PASS] No prohibited themed vocabulary detected" -ForegroundColor Green
    Write-Host ""
    Write-Host "Mask-off mode verification successful!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ [FAIL] Found $($violations.Count) prohibited term(s) in mask-off mode:" -ForegroundColor Red
    Write-Host ""

    $violations | Group-Object File | ForEach-Object {
        Write-Host "  File: $($_.Name)" -ForegroundColor Yellow
        $_.Group | ForEach-Object {
            Write-Host "    - Prohibited term: $($_.Term)" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "[ACTION] Fix these violations:" -ForegroundColor Yellow
    Write-Host "  1. Ensure mask_mode.enabled=false in protocol.config.yaml"
    Write-Host "  2. Clear agent session/context and restart"
    Write-Host "  3. Reseed AI memory with professional mode template (see MASK_MODE.md)"
    Write-Host "  4. Re-run this script to verify"
    Write-Host ""

    if ($strictMode) {
        Write-Host "[STRICT MODE] strict_professional=true requires ZERO themed vocabulary" -ForegroundColor Magenta
        exit 1
    } else {
        Write-Host "[WARN] Consider enabling strict_professional=true for compliance" -ForegroundColor Yellow
        exit 1
    }
}
