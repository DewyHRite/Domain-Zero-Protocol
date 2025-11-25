# Domain Zero Protocol - File Structure Verification Script
# Version: 1.0.0
# Protocol Version: 8.3.1
# Created: 2025-11-25
#
# This script verifies that all protected files exist in the repository.
# Run this before every commit to prevent file loss.

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Domain Zero Protocol - File Structure Check" -ForegroundColor Cyan
Write-Host "Protocol Version: 8.3.1" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$Errors = 0
$Warnings = 0

function Check-File {
    param (
        [string]$FilePath,
        [string]$Level  # CRITICAL or PROTECTED
    )

    # Input validation - file path must not be empty
    if ([string]::IsNullOrWhiteSpace($FilePath)) {
        Write-Host "[ERROR] Check-File called with empty path" -ForegroundColor Red
        $script:Errors++
        return
    }

    if (Test-Path $FilePath) {
        Write-Host "[OK] $FilePath" -ForegroundColor Green
    } else {
        if ($Level -eq "CRITICAL") {
            Write-Host "[CRITICAL MISSING] $FilePath" -ForegroundColor Red
            $script:Errors++
        } else {
            Write-Host "[MISSING] $FilePath" -ForegroundColor Yellow
            $script:Warnings++
        }
    }
}

function Check-Directory {
    param (
        [string]$DirPath
    )

    # Input validation - directory path must not be empty
    if ([string]::IsNullOrWhiteSpace($DirPath)) {
        Write-Host "[ERROR] Check-Directory called with empty path" -ForegroundColor Red
        $script:Errors++
        return
    }

    if (Test-Path $DirPath -PathType Container) {
        Write-Host "[OK] $DirPath/" -ForegroundColor Green
    } else {
        Write-Host "[MISSING DIR] $DirPath/" -ForegroundColor Red
        $script:Errors++
    }
}

Write-Host "Checking CRITICAL files..." -ForegroundColor White
Write-Host "-------------------------" -ForegroundColor Gray
Check-File "protocol\CLAUDE.md" "CRITICAL"
Check-File "protocol\yuuji.agent.md" "CRITICAL"
Check-File "protocol\megumi.agent.md" "CRITICAL"
Check-File "protocol\nobara.agent.md" "CRITICAL"
Check-File "protocol\gojo.agent.md" "CRITICAL"
Check-File "protocol.config.yaml" "CRITICAL"
Check-File ".protocol-state\project-state.json" "CRITICAL"
Check-File "FILE_STRUCTURE_PROTECTION.md" "CRITICAL"

Write-Host ""
Write-Host "Checking PROTECTED files..." -ForegroundColor White
Write-Host "---------------------------" -ForegroundColor Gray

# Root files
Check-File "README.md" "PROTECTED"
Check-File "CHANGELOG.md" "PROTECTED"
Check-File "VERSION.md" "PROTECTED"
Check-File "SECURITY.md" "PROTECTED"
Check-File "FAQ.md" "PROTECTED"
Check-File "CODEOWNERS" "PROTECTED"
Check-File "AGENT_BINDING_OATH.md" "PROTECTED"
Check-File "DECISION_REASONING_TEMPLATE.md" "PROTECTED"
Check-File "IMPLEMENTATION_GUIDE.md" "PROTECTED"
Check-File "PROTOCOL_QUICKSTART.md" "PROTECTED"
Check-File "REALITY_CHECK.md" "PROTECTED"

# Protocol files
Check-File "protocol\HANDOFF_SPECIFICATION.md" "PROTECTED"
Check-File "protocol\MCP_INTEGRATION.md" "PROTECTED"
Check-File "protocol\ENVIRONMENT_TARGETING.md" "PROTECTED"
Check-File "protocol\RESEARCH_MODE.md" "PROTECTED"
Check-File "protocol\MASK_MODE.md" "PROTECTED"
Check-File "protocol\MODE_INDICATORS.md" "PROTECTED"
Check-File "protocol\AGENT_SELF_IDENTIFICATION_STANDARD.md" "PROTECTED"
Check-File "protocol\CANONICAL_SOURCE_ADOPTION.md" "PROTECTED"
Check-File "protocol\TIER-SELECTION-GUIDE.md" "PROTECTED"

# Protocol state files
Check-File ".protocol-state\dev-notes.md" "PROTECTED"
Check-File ".protocol-state\security-review.md" "PROTECTED"
Check-File ".protocol-state\tier-system-specification.md" "PROTECTED"
Check-File ".protocol-state\work-session-alert.template.md" "PROTECTED"

# Domain Zero Agents
Check-File "Domain Zero Agents\README.md" "PROTECTED"
Check-File "Domain Zero Agents\AGENT_TEMPLATE.md" "PROTECTED"
Check-File "Domain Zero Agents\examples\KIRA_DOCUMENTATION_SPECIALIST.md" "PROTECTED"

# Skills
Check-File "protocol\skills\AGENT_SKILLS_MAP.yaml" "PROTECTED"
Check-File "protocol\skills\SKILL_REGISTRY.md" "PROTECTED"
Check-File "protocol\skills\skill-builder.md" "PROTECTED"

# MCP Servers
Check-File "protocol\mcp-servers\package.json" "PROTECTED"
Check-File "protocol\mcp-servers\handoff-server.js" "PROTECTED"

# Docs
Check-File "docs\INSTRUCTION_CONFIRMATION_PROTOCOL.md" "PROTECTED"

Write-Host ""
Write-Host "Checking directories..." -ForegroundColor White
Write-Host "----------------------" -ForegroundColor Gray
Check-Directory "protocol"
Check-Directory "protocol\skills"
Check-Directory "protocol\mcp-servers"
Check-Directory ".protocol-state"
Check-Directory ".protocol-state\research"
Check-Directory "Domain Zero Agents"
Check-Directory "Domain Zero Agents\examples"
Check-Directory "scripts"
Check-Directory "docs"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Critical Errors: $Errors" -ForegroundColor $(if ($Errors -gt 0) { "Red" } else { "Green" })
Write-Host "Warnings: $Warnings" -ForegroundColor $(if ($Warnings -gt 0) { "Yellow" } else { "Green" })

if ($Errors -gt 0) {
    Write-Host ""
    Write-Host "FILE STRUCTURE CHECK FAILED" -ForegroundColor Red
    Write-Host "Critical files are missing. DO NOT COMMIT until resolved." -ForegroundColor Red
    Write-Host ""
    Write-Host "To recover missing files:" -ForegroundColor White
    Write-Host "  git fetch new-repo main" -ForegroundColor Gray
    Write-Host "  git checkout new-repo/main -- `"<path/to/missing/file>`"" -ForegroundColor Gray
    exit 1
}

if ($Warnings -gt 0) {
    Write-Host ""
    Write-Host "FILE STRUCTURE CHECK PASSED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "Some protected files are missing. Consider recovering them." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "FILE STRUCTURE CHECK PASSED" -ForegroundColor Green
Write-Host "All protected files are present." -ForegroundColor Green
exit 0
