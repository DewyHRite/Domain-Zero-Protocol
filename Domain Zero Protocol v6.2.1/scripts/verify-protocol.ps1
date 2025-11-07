# Domain Zero Protocol Verification Script (PowerShell)
# Version: 1.0
# Purpose: Verify protocol integrity, configuration completeness, and enforcement rules

param(
    [switch]$Verbose = $false,
    [switch]$Fix = $false,
    [switch]$Help = $false
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$ErrorCount = 0
$WarningCount = 0
$PassCount = 0

# Colors for output
$ColorPass = "Green"
$ColorFail = "Red"
$ColorWarn = "Yellow"
$ColorInfo = "Cyan"
$ColorHeader = "Magenta"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor $ColorHeader
    Write-Host $Message -ForegroundColor $ColorHeader
    Write-Host "========================================" -ForegroundColor $ColorHeader
}

function Write-Pass {
    param([string]$Message)
    Write-Host "  [PASS] $Message" -ForegroundColor $ColorPass
    $script:PassCount++
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  [FAIL] $Message" -ForegroundColor $ColorFail
    $script:ErrorCount++
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [WARN] $Message" -ForegroundColor $ColorWarn
    $script:WarningCount++
}

function Write-InfoMsg {
    param([string]$Message)
    if ($Verbose) {
        Write-Host "  [INFO] $Message" -ForegroundColor $ColorInfo
    }
}

function Show-Help {
    Write-Host @"

Domain Zero Protocol Verification Script

USAGE:
    .\scripts\verify-protocol.ps1 [OPTIONS]

OPTIONS:
    -Verbose    Show detailed information during verification
    -Fix        Attempt to auto-fix issues (NOT IMPLEMENTED YET)
    -Help       Show this help message

DESCRIPTION:
    This script verifies the integrity and completeness of the Domain Zero Protocol
    installation. It checks:

    1. File Existence - Ensure all required protocol files are present
    2. Configuration Completeness - Verify protocol.config.yaml has required fields
    3. Isolation Vocabulary - Scan for forbidden cross-agent vocabulary
    4. Output Templates - Check role outputs conform to required headers
    5. CLAUDE.md Protection - Verify CODEOWNERS or protection rules exist
    6. Backup Configuration - Ensure backup requirements are configured

EXAMPLES:
    # Basic verification
    .\scripts\verify-protocol.ps1

    # Verbose output
    .\scripts\verify-protocol.ps1 -Verbose

    # Auto-fix issues (future feature)
    .\scripts\verify-protocol.ps1 -Fix

EXIT CODES:
    0 - All checks passed
    1 - Errors found
    2 - Warnings only (no errors)

"@
    exit 0
}

# ============================================================================
# VERIFICATION CHECKS
# ============================================================================

function Test-FileExistence {
    Write-Header "1. File Existence Check"

    $RequiredFiles = @(
        "protocol/CLAUDE.md",
        "protocol/YUUJI.md",
        "protocol/MEGUMI.md",
        "protocol/GOJO.md",
        "protocol/TIER-SELECTION-GUIDE.md",
        "protocol.config.yaml",
        ".protocol-state/project-state.json",
        ".protocol-state/dev-notes.md",
        ".protocol-state/security-review.md"
    )

    $OptionalFiles = @(
        "PROTOCOL_QUICKSTART.md",
        ".github/copilot-instructions.md",
        "CODEOWNERS",
        ".gitignore"
    )

    Write-InfoMsg "Checking required files..."
    foreach ($File in $RequiredFiles) {
        if (Test-Path $File) {
            Write-Pass "Found: $File"
        } else {
            Write-Fail "Missing required file: $File"
        }
    }

    Write-InfoMsg "Checking optional files..."
    foreach ($File in $OptionalFiles) {
        if (Test-Path $File) {
            Write-Pass "Found: $File"
        } else {
            Write-Warn "Optional file not found: $File"
        }
    }
}

function Test-ConfigCompleteness {
    Write-Header "2. Configuration Completeness Check"

    if (-not (Test-Path "protocol.config.yaml")) {
        Write-Fail "protocol.config.yaml not found - cannot verify configuration"
        return
    }

    Write-InfoMsg "Reading protocol.config.yaml..."
    $ConfigContent = Get-Content "protocol.config.yaml" -Raw

    # Check for placeholder values that need to be updated
    $Placeholders = @(
        "Your Name",
        "email@example.com",
        "Your Project Name",
        "Your Organization",
        "your-org/your-repo"
    )

    $PlaceholdersFound = @()
    foreach ($Placeholder in $Placeholders) {
        if ($ConfigContent -match [regex]::Escape($Placeholder)) {
            $PlaceholdersFound += $Placeholder
        }
    }

    if ($PlaceholdersFound.Count -eq 0) {
        Write-Pass "No placeholder values detected in config"
    } else {
        Write-Warn "Found placeholder values in config (consider updating):"
        foreach ($Placeholder in $PlaceholdersFound) {
            Write-Host "      - $Placeholder" -ForegroundColor $ColorWarn
        }
    }

    # Check for required sections
    $RequiredSections = @(
        "user:",
        "project:",
        "roles:",
        "enforcement:",
        "ai:",
        "tiers:",
        "paths:"
    )

    foreach ($Section in $RequiredSections) {
        if ($ConfigContent -match $Section) {
            Write-Pass "Config section present: $Section"
        } else {
            Write-Fail "Missing config section: $Section"
        }
    }
}

function Test-IsolationVocabulary {
    Write-Header "3. Isolation Vocabulary Check"

    Write-InfoMsg "Checking for forbidden cross-agent vocabulary..."

    $isolationErrors = 0

    # Yuuji should not mention Gojo directly in protocol definition
    if (Test-Path "protocol/YUUJI.md") {
        $YuujiContent = Get-Content "protocol/YUUJI.md" -Raw
        $ForbiddenTerms = @("GOJO", "Satoru Gojo", "Mission Control", "Trigger 19", "trigger-19")

        foreach ($Term in $ForbiddenTerms) {
            if ($YuujiContent -match $Term) {
                Write-Warn "Yuuji protocol mentions forbidden term: $Term"
                $isolationErrors++
            }
        }

        if ($isolationErrors -eq 0) {
            Write-Pass "Yuuji isolation vocabulary check passed"
        }
    } else {
        Write-Warn "protocol/YUUJI.md not found"
    }

    # Megumi should not mention Gojo directly in protocol definition
    if (Test-Path "protocol/MEGUMI.md") {
        $MegumiContent = Get-Content "protocol/MEGUMI.md" -Raw
        $ForbiddenTerms = @("GOJO", "Satoru Gojo", "Mission Control", "Trigger 19", "trigger-19")

        foreach ($Term in $ForbiddenTerms) {
            if ($MegumiContent -match $Term) {
                Write-Warn "Megumi protocol mentions forbidden term: $Term"
                $isolationErrors++
            }
        }

        if ($isolationErrors -eq 0) {
            Write-Pass "Megumi isolation vocabulary check passed"
        }
    } else {
        Write-Warn "protocol/MEGUMI.md not found"
    }

    if ($isolationErrors -gt 0) {
        Write-Warn "Found $isolationErrors isolation vocabulary violations"
        Write-InfoMsg "The 'weight' mechanism requires Yuuji and Megumi to remain unaware of Gojo's existence"
    }
}

function Test-OutputTemplates {
    Write-Header "4. Output Template Check"

    Write-InfoMsg "Checking for required output structure..."

    # Check dev-notes.md for Yuuji's output headers
    if (Test-Path ".protocol-state/dev-notes.md") {
        Write-Pass "dev-notes.md exists (Yuuji's output template)"
    } else {
        Write-Warn "dev-notes.md not found - Yuuji hasn't created implementation log yet"
    }

    # Check security-review.md for Megumi's output headers
    if (Test-Path ".protocol-state/security-review.md") {
        Write-Pass "security-review.md exists (Megumi's output template)"
    } else {
        Write-Warn "security-review.md not found - Megumi hasn't created security review yet"
    }

    Write-InfoMsg "Note: Deep template structure validation not yet implemented"
}

function Test-ClaudeMdProtection {
    Write-Header "5. CLAUDE.md Protection Check"

    if (Test-Path "CODEOWNERS") {
        $Codeowners = Get-Content "CODEOWNERS" -Raw
        if ($Codeowners -match "protocol/CLAUDE.md") {
            Write-Pass "CODEOWNERS file protects protocol/CLAUDE.md"
        } else {
            Write-Warn "CODEOWNERS exists but doesn't protect protocol/CLAUDE.md"
        }
    } else {
        Write-Warn "CODEOWNERS file not found - consider adding for CLAUDE.md protection"
    }

    # Check if config has protection enabled
    if (Test-Path "protocol.config.yaml") {
        $Config = Get-Content "protocol.config.yaml" -Raw
        if ($Config -match "claude_md_protected:\s*true") {
            Write-Pass "Config has CLAUDE.md protection enabled"
        } else {
            Write-Warn "Config does not explicitly enable CLAUDE.md protection"
        }
    }
}

function Test-BackupConfiguration {
    Write-Header "6. Backup Configuration Check"

    if (Test-Path "protocol.config.yaml") {
        $Config = Get-Content "protocol.config.yaml" -Raw

        if ($Config -match "(?i)required_for:.*yuuji") {
            Write-Pass "Backup requirement configured for Yuuji"
        } else {
            Write-Warn "Backup requirement for Yuuji not found in config (regex case-insensitive search)"
        }

        if ($Config -match "retention_days:\s*\d+") {
            Write-Pass "Backup retention policy configured"
        } else {
            Write-Warn "Backup retention policy not found in config (expects numeric days)"
        }
    } else {
        Write-Fail "protocol.config.yaml not found - cannot verify backup configuration"
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if ($Help) {
    Show-Help
}

Write-Host @"

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        DOMAIN ZERO PROTOCOL VERIFICATION TOOL                 ║
║                     Version 1.0                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

"@

Write-InfoMsg "Starting protocol verification..."
Write-InfoMsg "Working directory: $(Get-Location)"

# Run all verification checks
Test-FileExistence
Test-ConfigCompleteness
Test-IsolationVocabulary
Test-OutputTemplates
Test-ClaudeMdProtection
Test-BackupConfiguration

# ============================================================================
# SUMMARY
# ============================================================================

Write-Header "Verification Summary"

Write-Host ""
Write-Host "  PASSED: $PassCount" -ForegroundColor $ColorPass
Write-Host "  WARNINGS: $WarningCount" -ForegroundColor $ColorWarn
Write-Host "  ERRORS: $ErrorCount" -ForegroundColor $ColorFail
Write-Host ""

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "  ✓ Protocol verification PASSED - All checks successful!" -ForegroundColor $ColorPass
    exit 0
} elseif ($ErrorCount -eq 0) {
    Write-Host "  ⚠ Protocol verification PASSED with WARNINGS" -ForegroundColor $ColorWarn
    Write-Host "    Consider addressing warnings for optimal protocol operation." -ForegroundColor $ColorWarn
    exit 2
} else {
    Write-Host "  ✗ Protocol verification FAILED" -ForegroundColor $ColorFail
    Write-Host "    Please fix errors before proceeding." -ForegroundColor $ColorFail
    exit 1
}
