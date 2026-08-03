# validate-agents.ps1
# Domain Zero Protocol - Agent File Validation Script
# Version: 8.0.0
# Purpose: Validate .agent.md file structure, YAML frontmatter, and configuration integrity

param(
    [switch]$Verbose = $false,
    [switch]$Quick = $false
)

# Console color configuration
$SuccessColor = "Green"
$ErrorColor = "Red"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

# Validation counters
$script:TotalChecks = 0
$script:PassedChecks = 0
$script:FailedChecks = 0
$script:Warnings = 0

# Configuration
$ProtocolRoot = Split-Path -Parent $PSScriptRoot
$AgentDir = Join-Path $ProtocolRoot "protocol"
$RequiredAgents = @("yuuji", "megumi", "nobara", "gojo")
$RequiredYAMLFields = @("target", "name", "description", "argument-hint", "model", "tools", "handoffs")

function Write-ValidationHeader {
    Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor $InfoColor
    Write-Host "║          DOMAIN ZERO - AGENT VALIDATION v8.0.0              ║" -ForegroundColor $InfoColor
    Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor $InfoColor
}

function Write-CheckResult {
    param(
        [string]$CheckName,
        [bool]$Passed,
        [string]$Message = ""
    )

    $script:TotalChecks++

    if ($Passed) {
        $script:PassedChecks++
        Write-Host "✓ " -NoNewline -ForegroundColor $SuccessColor
        Write-Host "$CheckName" -ForegroundColor White
        if ($Message -and $Verbose) {
            Write-Host "  └─ $Message" -ForegroundColor Gray
        }
    }
    else {
        $script:FailedChecks++
        Write-Host "✗ " -NoNewline -ForegroundColor $ErrorColor
        Write-Host "$CheckName" -ForegroundColor White
        if ($Message) {
            Write-Host "  └─ ERROR: $Message" -ForegroundColor $ErrorColor
        }
    }
}

function Write-Warning {
    param([string]$Message)

    $script:Warnings++
    Write-Host "⚠ " -NoNewline -ForegroundColor $WarningColor
    Write-Host "WARNING: $Message" -ForegroundColor $WarningColor
}

function Test-AgentFileExists {
    param([string]$AgentName)

    $FilePath = Join-Path $AgentDir "$AgentName.agent.md"
    $Exists = Test-Path $FilePath

    Write-CheckResult `
        -CheckName "Agent file exists: $AgentName.agent.md" `
        -Passed $Exists `
        -Message $(if (-not $Exists) { "File not found at: $FilePath" })

    return $Exists
}

function Test-OldAgentFileRemoved {
    param([string]$AgentName)

    $OldFilePath = Join-Path $AgentDir "$($AgentName.ToUpper()).md"
    $Removed = -not (Test-Path $OldFilePath)

    Write-CheckResult `
        -CheckName "Old agent file removed: $($AgentName.ToUpper()).md" `
        -Passed $Removed `
        -Message $(if (-not $Removed) { "Old file still exists at: $OldFilePath" })

    return $Removed
}

function Get-YAMLFrontmatter {
    param([string]$FilePath)

    try {
        $Content = Get-Content $FilePath -Raw

        # Extract YAML frontmatter between --- markers.
        # SEC-AGENTVAL-001 (v9.11.0 WP5 Item 2): every .agent.md now begins with a
        # "<!-- [CORE FILE] - Domain Zero Protocol vX.Y.Z -->" stamp line BEFORE the
        # opening '---', so anchoring '^---' at the literal start of the string no
        # longer matches and frontmatter extraction silently returned null for every
        # agent file. The pattern now tolerates zero or more leading HTML-comment
        # stamp lines before the frontmatter fence.
        if ($Content -match '(?s)^(?:\s*<!--.*?-->\s*\r?\n)*---\s*\r?\n(.*?)\n---') {
            $YAMLText = $matches[1]

            # Parse YAML manually (basic implementation)
            $YAML = @{}
            $Lines = $YAMLText -split '\n'
            $CurrentKey = $null
            $CurrentList = $null

            foreach ($Line in $Lines) {
                $Line = $Line.TrimEnd()

                # Skip empty lines
                if ([string]::IsNullOrWhiteSpace($Line)) { continue }

                # List item
                if ($Line -match '^\s*-\s+(.+)$') {
                    if ($CurrentList) {
                        $CurrentList += $matches[1].Trim()
                    }
                }
                # Key-value pair
                elseif ($Line -match '^\s*([a-zA-Z_-]+):\s*(.*)$') {
                    $Key = $matches[1]
                    $Value = $matches[2].Trim()

                    # Empty value = start of list
                    if ([string]::IsNullOrWhiteSpace($Value)) {
                        $CurrentKey = $Key
                        $CurrentList = @()
                        $YAML[$Key] = $CurrentList
                    }
                    else {
                        # Remove quotes if present
                        $Value = $Value -replace '^["'']|["'']$', ''
                        $YAML[$Key] = $Value
                        $CurrentKey = $null
                        $CurrentList = $null
                    }
                }
                # Nested key-value (for handoffs)
                elseif ($Line -match '^\s{2,}([a-zA-Z_-]+):\s*(.*)$') {
                    # Skip nested parsing for now (handoffs structure)
                    continue
                }
            }

            return $YAML
        }
        else {
            Write-Warning "No YAML frontmatter found in: $FilePath"
            return $null
        }
    }
    catch {
        Write-Warning "Failed to parse YAML from: $FilePath - $_"
        return $null
    }
}

function Test-YAMLFrontmatter {
    param(
        [string]$AgentName,
        [string]$FilePath
    )

    $YAML = Get-YAMLFrontmatter -FilePath $FilePath

    if (-not $YAML) {
        Write-CheckResult `
            -CheckName "YAML frontmatter present: $AgentName" `
            -Passed $false `
            -Message "Could not extract YAML frontmatter"
        return $false
    }

    Write-CheckResult `
        -CheckName "YAML frontmatter present: $AgentName" `
        -Passed $true

    # Check required fields
    $AllFieldsPresent = $true
    foreach ($Field in $RequiredYAMLFields) {
        $FieldPresent = $YAML.ContainsKey($Field)

        if (-not $Quick) {
            Write-CheckResult `
                -CheckName "  Required field '$Field': $AgentName" `
                -Passed $FieldPresent `
                -Message $(if (-not $FieldPresent) { "Field '$Field' is missing" })
        }

        $AllFieldsPresent = $AllFieldsPresent -and $FieldPresent
    }

    return $AllFieldsPresent
}

function Test-ToolAccessMatrix {
    param(
        [string]$AgentName,
        [string]$FilePath
    )

    $Content = Get-Content $FilePath -Raw

    # Check for Tool Access Matrix section
    $HasMatrix = $Content -match '##\s+🛠️\s+TOOL ACCESS MATRIX'

    Write-CheckResult `
        -CheckName "Tool Access Matrix present: $AgentName" `
        -Passed $HasMatrix `
        -Message $(if (-not $HasMatrix) { "Missing Tool Access Matrix section" })

    return $HasMatrix
}

function Test-ContentIntegrity {
    param(
        [string]$AgentName,
        [string]$FilePath
    )

    $Content = Get-Content $FilePath -Raw

    # Check minimum content length (should have substantial content beyond frontmatter)
    $MinimumLength = 5000
    $HasContent = $Content.Length -gt $MinimumLength

    Write-CheckResult `
        -CheckName "Sufficient content: $AgentName" `
        -Passed $HasContent `
        -Message $(if (-not $HasContent) { "Content too short: $($Content.Length) chars (minimum: $MinimumLength)" })

    return $HasContent
}

function Test-NoOldReferences {
    $FilesToCheck = @(
        (Join-Path $ProtocolRoot "protocol\CLAUDE.md"),
        (Join-Path $ProtocolRoot "README.md"),
        (Join-Path $ProtocolRoot "protocol.config.yaml")
    )

    $OldReferences = @()

    foreach ($File in $FilesToCheck) {
        if (Test-Path $File) {
            $Content = Get-Content $File -Raw

            # Check for references to old agent file names
            if ($Content -match 'YUUJI\.md|MEGUMI\.md|NOBARA\.md|GOJO\.md') {
                $OldReferences += $File
            }
        }
    }

    $NoOldRefs = $OldReferences.Count -eq 0

    Write-CheckResult `
        -CheckName "No old agent file references in docs" `
        -Passed $NoOldRefs `
        -Message $(if (-not $NoOldRefs) { "Found references in: $($OldReferences -join ', ')" })

    return $NoOldRefs
}

function Show-ValidationSummary {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $InfoColor
    Write-Host "VALIDATION SUMMARY" -ForegroundColor $InfoColor
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor $InfoColor

    Write-Host "Total Checks:   " -NoNewline
    Write-Host $script:TotalChecks -ForegroundColor White

    Write-Host "Passed:         " -NoNewline
    Write-Host $script:PassedChecks -ForegroundColor $SuccessColor

    Write-Host "Failed:         " -NoNewline
    Write-Host $script:FailedChecks -ForegroundColor $(if ($script:FailedChecks -eq 0) { $SuccessColor } else { $ErrorColor })

    Write-Host "Warnings:       " -NoNewline
    Write-Host $script:Warnings -ForegroundColor $(if ($script:Warnings -eq 0) { $SuccessColor } else { $WarningColor })

    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor $InfoColor

    if ($script:FailedChecks -eq 0 -and $script:Warnings -eq 0) {
        Write-Host "✓ ALL VALIDATIONS PASSED - Agent files are correctly configured" -ForegroundColor $SuccessColor
        return $true
    }
    elseif ($script:FailedChecks -eq 0) {
        Write-Host "⚠ VALIDATIONS PASSED WITH WARNINGS - Review warnings above" -ForegroundColor $WarningColor
        return $true
    }
    else {
        Write-Host "✗ VALIDATION FAILED - Fix errors above before proceeding" -ForegroundColor $ErrorColor
        return $false
    }
}

# ============================================================================
# MAIN VALIDATION EXECUTION
# ============================================================================

Write-ValidationHeader

Write-Host "Validating Domain Zero agent files..." -ForegroundColor $InfoColor
Write-Host "Protocol Root: $ProtocolRoot`n" -ForegroundColor Gray

# Phase 1: Check for new agent files
Write-Host "━━━ Phase 1: Agent File Existence ━━━`n" -ForegroundColor $InfoColor

foreach ($Agent in $RequiredAgents) {
    $null = Test-AgentFileExists -AgentName $Agent
}

# Phase 2: Check old files are removed
Write-Host "`n━━━ Phase 2: Old Agent File Cleanup ━━━`n" -ForegroundColor $InfoColor

foreach ($Agent in $RequiredAgents) {
    $null = Test-OldAgentFileRemoved -AgentName $Agent
}

# Phase 3: Validate YAML frontmatter
if (-not $Quick) {
    Write-Host "`n━━━ Phase 3: YAML Frontmatter Validation ━━━`n" -ForegroundColor $InfoColor

    foreach ($Agent in $RequiredAgents) {
        $FilePath = Join-Path $AgentDir "$Agent.agent.md"
        if (Test-Path $FilePath) {
            $null = Test-YAMLFrontmatter -AgentName $Agent -FilePath $FilePath
        }
    }
}

# Phase 4: Validate Tool Access Matrix
Write-Host "`n━━━ Phase 4: Tool Access Matrix ━━━`n" -ForegroundColor $InfoColor

foreach ($Agent in $RequiredAgents) {
    $FilePath = Join-Path $AgentDir "$Agent.agent.md"
    if (Test-Path $FilePath) {
        $null = Test-ToolAccessMatrix -AgentName $Agent -FilePath $FilePath
    }
}

# Phase 5: Content integrity
Write-Host "`n━━━ Phase 5: Content Integrity ━━━`n" -ForegroundColor $InfoColor

foreach ($Agent in $RequiredAgents) {
    $FilePath = Join-Path $AgentDir "$Agent.agent.md"
    if (Test-Path $FilePath) {
        $null = Test-ContentIntegrity -AgentName $Agent -FilePath $FilePath
    }
}

# Phase 6: Check for old references
Write-Host "`n━━━ Phase 6: Documentation References ━━━`n" -ForegroundColor $InfoColor

$null = Test-NoOldReferences

# Display summary and exit
$Success = Show-ValidationSummary

if ($Success) {
    exit 0
}
else {
    exit 1
}
