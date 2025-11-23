# Domain Zero Protocol - Release Folder Sync Script
# Version: 1.1.0
# Purpose: Sync DZP and DZA files to the release folder for GitHub push
#
# Usage:
#   .\scripts\sync-release.ps1           # Sync to release folder
#   .\scripts\sync-release.ps1 -DryRun   # Preview what would be synced
#
# This script copies ONLY public DZP/DZA files to the release folder.
# Internal documentation is excluded.
#
# WORKFLOW:
# 1. Make changes to DZP/DZA files in root project
# 2. Run this script to sync changes to release folder
# 3. Commit and push the release folder to GitHub

param(
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Get current version from protocol.config.yaml
$ConfigPath = Join-Path $ProjectRoot "protocol.config.yaml"
$Version = "unknown"
if (Test-Path $ConfigPath) {
    $ConfigContent = Get-Content $ConfigPath -Raw
    if ($ConfigContent -match 'protocol_version:\s*"?(\d+\.\d+\.\d+)"?') {
        $Version = $Matches[1]
    }
}

# Release folder is always named "release" (not versioned)
$ReleaseFolder = Join-Path $ProjectRoot "release"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Domain Zero Protocol - Release Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Version: v$Version" -ForegroundColor Yellow
Write-Host "Release Folder: $ReleaseFolder" -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "Mode: DRY RUN (no changes will be made)" -ForegroundColor Magenta
}
Write-Host ""

# ============================================================================
# RELEASE FILES DEFINITION
# ============================================================================
# These are the ONLY files that should be in the release folder and pushed to GitHub.
# Internal documentation, session summaries, and development files are EXCLUDED.

$ReleaseFolders = @(
    "protocol",                              # Core protocol files (CLAUDE.md, agents)
    "Domain Zero Agents - Full JJK Edition", # DZA - Full JJK agent set
    "scripts",                               # Validation scripts
    "docs"                                   # Public documentation
)

$ReleaseFiles = @(
    "protocol.config.yaml",      # Configuration
    "README.md",                 # Main readme
    "CHANGELOG.md",              # Version history
    "VERSION.md",                # Version info
    "IMPLEMENTATION_GUIDE.md",   # Implementation guide
    "PROTOCOL_QUICKSTART.md",    # Quick start guide
    "FAQ.md",                    # FAQ
    "SECURITY.md",               # Security policy
    "LICENSE",                   # License
    "REALITY_CHECK.md",          # Honest assessment
    "AGENT_BINDING_OATH.md",     # Agent oath
    "DECISION_REASONING_TEMPLATE.md",  # Decision template
    "DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md",  # Dual workflow guide
    "GIT_WORKFLOW.md",           # Git workflow
    ".gitignore"                 # Git ignore
)

# Files to EXCLUDE from release (internal documentation)
$ExcludePatterns = @(
    "SYSTEM_UPDATE_*.md",
    "SESSION_SUMMARY_*.md",
    "*_REVIEW.md",
    "*_IMPLEMENTATION.md",
    "*_ACTION_PLAN.md",
    "RELEASE_NOTES_*.md",
    "P*_*.md",
    "*.py",
    "*.py.backup",
    "Screenshot",
    "Test",
    "apps",
    "__pycache__",
    ".protocol-state",
    ".vscode",
    ".claude",
    ".git",
    ".github",
    "Domain Zero Protocol Backups",
    "Domain Zero Agents",          # Generic agents (use Full JJK Edition instead)
    "src",
    "tests",
    "v*.0",                        # Other version folders
    "MIGRATION_GUIDE_TEMPLATE.md",
    "TIER_TRANSITION_GUIDE.md",
    "VERSION_MANAGEMENT_GUIDE.md",
    "README_RELEASE.md"            # Release notes template
)

# ============================================================================
# SYNC LOGIC
# ============================================================================

# Create release folder if it doesn't exist
if (-not (Test-Path $ReleaseFolder)) {
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $ReleaseFolder -Force | Out-Null
    }
    Write-Host "[CREATE] $ReleaseFolder" -ForegroundColor Green
}

$SyncedFiles = 0
$SyncedFolders = 0

# Sync folders
foreach ($Folder in $ReleaseFolders) {
    $SourcePath = Join-Path $ProjectRoot $Folder
    $DestPath = Join-Path $ReleaseFolder $Folder

    if (Test-Path $SourcePath) {
        Write-Host "[FOLDER] $Folder" -ForegroundColor Cyan
        if (-not $DryRun) {
            # Remove existing folder and copy fresh
            if (Test-Path $DestPath) {
                Remove-Item -Path $DestPath -Recurse -Force
            }
            Copy-Item -Path $SourcePath -Destination $DestPath -Recurse -Force
        }
        $SyncedFolders++
    } else {
        Write-Host "[SKIP] $Folder (not found)" -ForegroundColor DarkGray
    }
}

# Sync individual files
foreach ($File in $ReleaseFiles) {
    $SourcePath = Join-Path $ProjectRoot $File
    $DestPath = Join-Path $ReleaseFolder $File

    if (Test-Path $SourcePath) {
        Write-Host "[FILE] $File" -ForegroundColor Green
        if (-not $DryRun) {
            Copy-Item -Path $SourcePath -Destination $DestPath -Force
        }
        $SyncedFiles++
    } else {
        Write-Host "[SKIP] $File (not found)" -ForegroundColor DarkGray
    }
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sync Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Folders synced: $SyncedFolders" -ForegroundColor Yellow
Write-Host "Files synced: $SyncedFiles" -ForegroundColor Yellow
Write-Host "Release folder: $ReleaseFolder" -ForegroundColor Yellow

if ($DryRun) {
    Write-Host ""
    Write-Host "DRY RUN complete. No files were modified." -ForegroundColor Magenta
    Write-Host "Run without -DryRun to actually sync files." -ForegroundColor Magenta
} else {
    Write-Host ""
    Write-Host "Sync complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Review the release folder contents"
    Write-Host "  2. git add release/"
    Write-Host "  3. git commit -m 'Update release folder to v$Version'"
    Write-Host "  4. git push"
}

Write-Host ""
