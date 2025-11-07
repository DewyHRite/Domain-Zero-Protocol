# Domain Zero Protocol - Instruction File Updater (PowerShell)
#
# Purpose: Safely append Domain Zero Protocol pointers to existing AI instruction files
# Safety: Dry-run by default, only modifies with -Apply switch
# Idempotent: Won't add duplicate pointers

<#
.SYNOPSIS
Appends Domain Zero Protocol references to existing AI instruction files.

.DESCRIPTION
Scans for common AI instruction file patterns and appends a "Domain Zero Protocol"
section with pointers to protocol/CLAUDE.md. Safe and non-destructive.

.PARAMETER Apply
Actually modify files. Without this flag, script runs in dry-run mode (default).

.PARAMETER Path
Root directory to scan. Defaults to current directory.

.PARAMETER Backup
Create .backup files before modifying. Enabled by default with -Apply.

.EXAMPLE
.\update-instructions.ps1
Dry-run mode - shows what would be changed

.EXAMPLE
.\update-instructions.ps1 -Apply
Actually append protocol pointers to instruction files

.EXAMPLE
.\update-instructions.ps1 -Apply -Path "C:\Projects\MyProject"
Update instruction files in specific directory
#>

param(
    [switch]$Apply,
    [string]$Path = ".",
    [switch]$Backup = $true
)

# ANSI color codes (if terminal supports it)
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

# Fallback for older PowerShell
if ($PSVersionTable.PSVersion.Major -lt 7) {
    $Red = $Green = $Yellow = $Blue = $Reset = ""
}

# Protocol pointer template
$ProtocolSection = @"

---

## Domain Zero Protocol

This project follows the Domain Zero Protocol for AI-assisted development.

**Primary entrypoint**: [`protocol/CLAUDE.md`](protocol/CLAUDE.md)

**Workflow guidance**:
- Mission Control & initialization: `protocol/GOJO.md`
- Feature implementation: `protocol/YUUJI.md`
- Security review: `protocol/MEGUMI.md`
- Tier selection guide: `protocol/TIER-SELECTION-GUIDE.md`

For complete protocol details, read [`protocol/CLAUDE.md`](protocol/CLAUDE.md) - the canonical source of truth.

---
"@

# Common instruction file patterns
$InstructionFilePatterns = @(
    "AI_INSTRUCTIONS.md",
    "AI.md",
    ".github/copilot-instructions.md",
    ".github/instructions/*.md",
    ".cursorrules",
    "CONTRIBUTING.md",
    "DEVELOPMENT.md",
    ".vscode/instructions.md",
    ".idea/instructions.md"
)

# Function to check if file already has protocol pointer
function Test-HasProtocolPointer {
    param([string]$FilePath)

    $content = Get-Content -Path $FilePath -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content) { return $false }

    # Check for various indicators that protocol pointer exists
    return $content -match "protocol/CLAUDE\.md" -or
           $content -match "Domain Zero Protocol"
}

# Function to append protocol pointer
function Add-ProtocolPointer {
    param(
        [string]$FilePath,
        [bool]$DryRun = $true
    )

    if (Test-HasProtocolPointer -FilePath $FilePath) {
        Write-Host "  ${Yellow}[SKIP]${Reset} Already has protocol pointer: $FilePath"
        return $false
    }

    if ($DryRun) {
        Write-Host "  ${Blue}[DRY-RUN]${Reset} Would append to: $FilePath"
        return $true
    }

    # Create backup if requested
    if ($Backup) {
        $backupPath = "$FilePath.backup"
        Copy-Item -Path $FilePath -Destination $backupPath -Force
        Write-Host "  ${Green}[BACKUP]${Reset} Created: $backupPath"
    }

    # Append protocol pointer
    Add-Content -Path $FilePath -Value $ProtocolSection -NoNewline -Encoding UTF8
    Write-Host "  ${Green}[UPDATED]${Reset} Appended protocol pointer to: $FilePath"
    return $true
}

# Main execution
Write-Host "${Blue}╔════════════════════════════════════════════════════════════╗${Reset}"
Write-Host "${Blue}║  Domain Zero Protocol - Instruction File Updater         ║${Reset}"
Write-Host "${Blue}╚════════════════════════════════════════════════════════════╝${Reset}"
Write-Host ""

if (-not $Apply) {
    Write-Host "${Yellow}⚠️  DRY-RUN MODE${Reset} - No files will be modified"
    Write-Host "   Use -Apply to actually update files"
    Write-Host ""
}

$foundFiles = @()
$willUpdate = @()

# Scan for instruction files
Write-Host "Scanning for instruction files in: $Path"
Write-Host ""

foreach ($pattern in $InstructionFilePatterns) {
    $fullPattern = Join-Path -Path $Path -ChildPath $pattern
    $files = Get-ChildItem -Path $fullPattern -ErrorAction SilentlyContinue

    foreach ($file in $files) {
        # Skip if it's in protocol/ directory (those are canonical sources)
        if ($file.FullName -match "[/\\]protocol[/\\]") {
            continue
        }

        # Skip if it's AI_INSTRUCTIONS.md (that's our shim, shouldn't modify)
        if ($file.Name -eq "AI_INSTRUCTIONS.md") {
            continue
        }

        $foundFiles += $file

        $hasPointer = Test-HasProtocolPointer -FilePath $file.FullName
        if (-not $hasPointer) {
            $willUpdate += $file
        }
    }
}

# Report findings
if ($foundFiles.Count -eq 0) {
    Write-Host "${Yellow}No instruction files found.${Reset}"
    Write-Host ""
    Write-Host "Common locations:"
    Write-Host "  - .github/copilot-instructions.md"
    Write-Host "  - .cursorrules"
    Write-Host "  - CONTRIBUTING.md"
    Write-Host ""
    exit 0
}

Write-Host "Found $($foundFiles.Count) instruction file(s):"
Write-Host ""

# Process each file
$updatedCount = 0
foreach ($file in $foundFiles) {
    $updated = Add-ProtocolPointer -FilePath $file.FullName -DryRun (-not $Apply)
    if ($updated) {
        $updatedCount++
    }
}

# Summary
Write-Host ""
Write-Host "${Blue}═══════════════════════════════════════════════════════════${Reset}"
Write-Host "Summary:"
Write-Host "  Files found: $($foundFiles.Count)"
Write-Host "  Files that need update: $($willUpdate.Count)"

if ($Apply) {
    Write-Host "  ${Green}Files updated: $updatedCount${Reset}"
    if ($Backup) {
        Write-Host "  ${Green}Backups created: $updatedCount${Reset}"
    }
} else {
    Write-Host "  ${Yellow}Files would be updated: $updatedCount${Reset} (use -Apply to modify)"
}

Write-Host "${Blue}═══════════════════════════════════════════════════════════${Reset}"
Write-Host ""

if (-not $Apply -and $willUpdate.Count -gt 0) {
    Write-Host "${Yellow}▶ Next Steps:${Reset}"
    Write-Host "  1. Review the files listed above"
    Write-Host "  2. Run with -Apply to actually update them:"
    Write-Host "     ${Green}.\update-instructions.ps1 -Apply${Reset}"
    Write-Host ""
}

if ($Apply -and $updatedCount -gt 0) {
    Write-Host "${Green}✓ Update complete!${Reset}"
    Write-Host ""
    Write-Host "Modified files now point to protocol/CLAUDE.md as canonical source."
    Write-Host "Backup files created (*.backup) - delete these when confirmed working."
    Write-Host ""
}

# Exit codes
if ($Apply) {
    exit 0  # Success
} else {
    if ($willUpdate.Count -gt 0) {
        exit 1  # Dry-run found files to update
    } else {
        exit 0  # Nothing to do
    }
}
