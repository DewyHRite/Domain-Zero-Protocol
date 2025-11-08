# Domain Zero Protocol Verification Script (PowerShell)
# Version: 2.0
# Purpose: Verify protocol integrity, configuration completeness, and enforcement rules

param(
    [switch]$Verbose = $false,
    [switch]$Quick = $false,
    [string[]]$Skip = @(),
    [string[]]$Only = @(),
    [switch]$List = $false,
    [switch]$Help = $false
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$script:ErrorCount = 0
$script:WarningCount = 0
$script:PassCount = 0
$script:CriticalError = $false

# Colors for output
$ColorPass = "Green"
$ColorFail = "Red"
$ColorWarn = "Yellow"
$ColorInfo = "Cyan"
$ColorHeader = "Magenta"

# Available checks: name:function:level
$AvailableChecks = @(
    @{Name="dependencies"; Function="Test-Dependencies"; Level="critical"}
    @{Name="files"; Function="Test-FileExistence"; Level="critical"}
    @{Name="config"; Function="Test-ConfigCompleteness"; Level="critical"}
    @{Name="yaml"; Function="Test-YamlSyntax"; Level="critical"}
    @{Name="isolation"; Function="Test-IsolationVocabulary"; Level="warning"}
    @{Name="templates"; Function="Test-OutputTemplates"; Level="warning"}
    @{Name="protection"; Function="Test-ClaudeMdProtection"; Level="warning"}
    @{Name="backup"; Function="Test-BackupConfiguration"; Level="warning"}
)

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

function Write-FailWithContext {
    param(
        [string]$Message,
        [string]$Impact = "",
        [string]$Action = "",
        [string]$DocLink = ""
    )

    Write-Fail $Message
    if ($Impact) {
        Write-Host "      Impact: $Impact" -ForegroundColor $ColorInfo
    }
    if ($Action) {
        Write-Host "      Action: $Action" -ForegroundColor $ColorInfo
    }
    if ($DocLink) {
        Write-Host "      Docs: $DocLink" -ForegroundColor $ColorInfo
    }
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

Domain Zero Protocol Verification Script v2.0

USAGE:
    .\scripts\verify-protocol.ps1 [OPTIONS]

OPTIONS:
    -Verbose        Show detailed information during verification
    -Quick          Run only critical checks (faster)
    -Skip CHECK     Skip specific check (can be used multiple times)
    -Only CHECK     Run only specific check (can be used multiple times)
    -List           List all available checks and exit
    -Help           Show this help message

DESCRIPTION:
    This script verifies the integrity and completeness of the Domain Zero Protocol
    installation. It checks:

    0. Dependencies - Verify required command-line tools are installed
    1. File Existence - Ensure all required protocol files are present
    2. Configuration Completeness - Verify protocol.config.yaml has required fields
    3. YAML Syntax - Validate YAML syntax in configuration files
    4. Isolation Vocabulary - Scan for forbidden cross-agent vocabulary
    5. Output Templates - Check role outputs conform to required headers
    6. CLAUDE.md Protection - Verify CODEOWNERS or protection rules exist
    7. Backup Configuration - Ensure backup requirements are configured

EXAMPLES:
    # Basic verification
    .\scripts\verify-protocol.ps1

    # Verbose output
    .\scripts\verify-protocol.ps1 -Verbose

    # Quick mode (critical checks only)
    .\scripts\verify-protocol.ps1 -Quick

    # Skip isolation check
    .\scripts\verify-protocol.ps1 -Skip isolation

    # Run only file and config checks
    .\scripts\verify-protocol.ps1 -Only files,config

    # List available checks
    .\scripts\verify-protocol.ps1 -List

EXIT CODES:
    0 - All checks passed
    1 - Errors found
    2 - Warnings only (no errors)
    3 - Missing dependencies (cannot proceed)

"@
    exit 0
}

function Show-CheckList {
    Write-Host ""
    Write-Host "Available Checks:"
    Write-Host ""
    Write-Host ("  {0,-15} {1,-10} {2}" -f "NAME", "LEVEL", "DESCRIPTION")
    Write-Host "  " + ("-" * 57)

    $descriptions = @(
        @{Name="dependencies"; Level="critical"; Desc="Verify required command-line tools"}
        @{Name="files"; Level="critical"; Desc="Check protocol file existence"}
        @{Name="config"; Level="critical"; Desc="Validate configuration completeness"}
        @{Name="yaml"; Level="critical"; Desc="Check YAML syntax validity"}
        @{Name="isolation"; Level="warning"; Desc="Scan for forbidden vocabulary"}
        @{Name="templates"; Level="warning"; Desc="Check output template structure"}
        @{Name="protection"; Level="warning"; Desc="Verify CLAUDE.md protection"}
        @{Name="backup"; Level="warning"; Desc="Check backup configuration"}
    )

    foreach ($item in $descriptions) {
        Write-Host ("  {0,-15} {1,-10} {2}" -f $item.Name, $item.Level, $item.Desc)
    }

    Write-Host ""
    Write-Host "Usage: -Skip CHECK or -Only CHECK"
    Write-Host ""
    exit 0
}

function Test-ShouldRunCheck {
    param(
        [string]$CheckName,
        [string]$CheckLevel
    )

    # Skip if in skip list
    if ($Skip -contains $CheckName) {
        return $false
    }

    # Skip if only specific checks requested and this isn't one
    if ($Only.Count -gt 0 -and $Only -notcontains $CheckName) {
        return $false
    }

    # Skip non-critical if quick mode
    if ($Quick -and $CheckLevel -ne "critical") {
        return $false
    }

    return $true
}

# ============================================================================
# VERIFICATION CHECKS
# ============================================================================

function Test-Dependencies {
    Write-Header "0. Dependency Check"

    $requiredTools = @("powershell")  # PowerShell itself
    $optionalTools = @("python", "python3", "yamllint")
    $missingRequired = @()

    Write-InfoMsg "Checking required command-line tools..."
    foreach ($tool in $requiredTools) {
        if (Get-Command $tool -ErrorAction SilentlyContinue) {
            Write-Pass "Found: $tool"
        } else {
            $missingRequired += $tool
            Write-FailWithContext `
                -Message "Required tool not found: $tool" `
                -Impact "Verification cannot proceed without this tool" `
                -Action "Ensure PowerShell is properly installed" `
                -DocLink ""
        }
    }

    if ($missingRequired.Count -gt 0) {
        Write-Host ""
        Write-Host "  [X] Missing required tools: $($missingRequired -join ', ')" -ForegroundColor $ColorFail
        Write-Host "  Install them before proceeding" -ForegroundColor $ColorInfo
        Write-Host ""
        exit 3
    }

    Write-InfoMsg "Checking optional tools..."
    foreach ($tool in $optionalTools) {
        if (Get-Command $tool -ErrorAction SilentlyContinue) {
            Write-Pass "Found (optional): $tool"
        } else {
            Write-InfoMsg "Optional tool not found: $tool"
        }
    }
}

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

    $missingCritical = @()

    Write-InfoMsg "Checking required files..."
    foreach ($File in $RequiredFiles) {
        if (Test-Path $File) {
            Write-Pass "Found: $File"
        } else {
            $missingCritical += $File
            Write-FailWithContext `
                -Message "Missing required file: $File" `
                -Impact "Protocol cannot function without this file" `
                -Action "Copy from Domain Zero repository or re-run setup" `
                -DocLink "https://github.com/DewyHRite/Domain-Zero-Protocol#installation"
        }
    }

    if ($missingCritical.Count -gt 0) {
        $script:CriticalError = $true
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

function Test-YamlSyntax {
    Write-Header "3. YAML Syntax Validation"

    if (-not (Test-Path "protocol.config.yaml")) {
        Write-FailWithContext `
            -Message "protocol.config.yaml not found" `
            -Impact "Cannot validate YAML syntax" `
            -Action "Ensure protocol.config.yaml exists" `
            -DocLink ""
        $script:CriticalError = $true
        return
    }

    # Try Python validation first
    $pythonCmd = $null
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        $pythonCmd = "python3"
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonCmd = "python"
    }

    if ($pythonCmd) {
        Write-InfoMsg "Validating YAML syntax with Python..."
        $yamlTest = & $pythonCmd -c "import yaml; yaml.safe_load(open('protocol.config.yaml'))" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Pass "YAML syntax valid (verified with Python)"
            return
        }

        if ($yamlTest -match "ModuleNotFoundError: No module named 'yaml'") {
            Write-Warn "PyYAML not installed; skipping python-based YAML validation"
            if (Get-Command yamllint -ErrorAction SilentlyContinue) {
                Write-InfoMsg "Falling back to yamllint for syntax validation..."
                $null = yamllint -d relaxed protocol.config.yaml 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Pass "YAML syntax valid (verified with yamllint)"
                    return
                }
                Write-FailWithContext `
                    -Message "Invalid YAML syntax in protocol.config.yaml" `
                    -Impact "Configuration file has syntax errors" `
                    -Action "Run 'yamllint protocol.config.yaml' for details" `
                    -DocLink ""
                $script:CriticalError = $true
                return
            }
            Write-InfoMsg "Install PyYAML or yamllint for syntax validation"
            return
        }

        Write-FailWithContext `
            -Message "Invalid YAML syntax in protocol.config.yaml" `
            -Impact "Configuration file cannot be parsed" `
            -Action "Fix syntax errors using a YAML validator" `
            -DocLink "https://www.yamllint.com/"
        $script:CriticalError = $true
        return
    } elseif (Get-Command yamllint -ErrorAction SilentlyContinue) {
        Write-InfoMsg "Validating YAML syntax with yamllint..."
        $yamlTest = yamllint -d relaxed protocol.config.yaml 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Pass "YAML syntax valid (verified with yamllint)"
        } else {
            Write-FailWithContext `
                -Message "Invalid YAML syntax in protocol.config.yaml" `
                -Impact "Configuration file has syntax errors" `
                -Action "Run 'yamllint protocol.config.yaml' for details" `
                -DocLink ""
            $script:CriticalError = $true
            return
        }
    } else {
        Write-Warn "YAML validation skipped (Python/yamllint not found)"
        Write-InfoMsg "Install Python or yamllint for syntax validation"
    }
}

function Test-ConfigCompleteness {
    Write-Header "2. Configuration Completeness Check"

    if (-not (Test-Path "protocol.config.yaml")) {
        Write-FailWithContext `
            -Message "protocol.config.yaml not found" `
            -Impact "Cannot verify configuration" `
            -Action "Copy protocol.config.yaml from Domain Zero repository" `
            -DocLink "https://github.com/DewyHRite/Domain-Zero-Protocol"
        $script:CriticalError = $true
        return
    }

    Write-InfoMsg "Reading protocol.config.yaml..."
    $ConfigContent = Get-Content "protocol.config.yaml" -Raw

    if ([string]::IsNullOrWhiteSpace($ConfigContent)) {
        Write-FailWithContext `
            -Message "protocol.config.yaml is empty" `
            -Impact "No configuration available" `
            -Action "Populate protocol.config.yaml with valid configuration" `
            -DocLink ""
        $script:CriticalError = $true
        return
    }

    # Check for placeholder values that need to be updated
    $Placeholders = @(
        "Your Name",
        "email@example.com",
        "Your Project Name",
        "Your Organization",
        "your-org/your-repo",
        "YYYY-MM-DD"
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
        Write-Fail "Configuration contains placeholder values that must be updated:"
        foreach ($Placeholder in $PlaceholdersFound) {
            Write-Host "      [X] $Placeholder" -ForegroundColor $ColorFail
        }
        Write-Host ""
        Write-Host "  HOW TO FIX:" -ForegroundColor $ColorInfo
        Write-Host "  1. Open protocol.config.yaml in your editor" -ForegroundColor $ColorInfo
        Write-Host "  2. Search for the placeholder values listed above" -ForegroundColor $ColorInfo
        Write-Host "  3. Replace them with your actual project information" -ForegroundColor $ColorInfo
        Write-Host ""
        Write-Host "  Example configuration:" -ForegroundColor $ColorInfo
        Write-Host "    user:" -ForegroundColor $ColorInfo
        Write-Host "      name: `"John Smith`"" -ForegroundColor $ColorInfo
        Write-Host "      contact: `"john.smith@company.com`"" -ForegroundColor $ColorInfo
        Write-Host "      organization: `"Acme Corp`"" -ForegroundColor $ColorInfo
        Write-Host ""
        Write-Host "    project:" -ForegroundColor $ColorInfo
        Write-Host "      name: `"My Awesome Project`"" -ForegroundColor $ColorInfo
        Write-Host "      repo: `"https://github.com/myorg/my-project`"" -ForegroundColor $ColorInfo
        $exampleDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Write-Host "      created: `"$exampleDate`"" -ForegroundColor $ColorInfo
        Write-Host ""
        Write-Host "  Note: The '<PINNED_SHA>' placeholder is optional and can be left as-is." -ForegroundColor $ColorWarn
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
        if ($ConfigContent -match [regex]::Escape($Section)) {
            Write-Pass "Config section present: $Section"
        } else {
            Write-FailWithContext `
                -Message "Missing config section: $Section" `
                -Impact "Configuration incomplete" `
                -Action "Add required section to protocol.config.yaml" `
                -DocLink ""
        }
    }
}

function Test-IsolationVocabulary {
    Write-Header "4. Isolation Vocabulary Check"

    Write-InfoMsg "Checking for forbidden cross-agent vocabulary..."

    $isolationErrors = 0

    # Yuuji should not mention Gojo directly
    if (Test-Path "protocol/YUUJI.md") {
        $forbiddenTerms = @("GOJO", "Satoru Gojo", "Mission Control", "Trigger 19", "trigger-19")
        $yuujiFound = $false

        foreach ($term in $forbiddenTerms) {
            if ((Get-Content "protocol/YUUJI.md" -Raw) -match [regex]::Escape($term)) {
                Write-Warn "Yuuji protocol mentions forbidden term: $term"
                $isolationErrors++
                $yuujiFound = $true
            }
        }

        if (-not $yuujiFound) {
            Write-Pass "Yuuji isolation vocabulary check passed"
        }
    } else {
        Write-Warn "protocol/YUUJI.md not found"
    }

    # Megumi should not mention Gojo directly
    if (Test-Path "protocol/MEGUMI.md") {
        $forbiddenTerms = @("GOJO", "Satoru Gojo", "Mission Control", "Trigger 19", "trigger-19")
        $megumiFound = $false

        foreach ($term in $forbiddenTerms) {
            if ((Get-Content "protocol/MEGUMI.md" -Raw) -match [regex]::Escape($term)) {
                Write-Warn "Megumi protocol mentions forbidden term: $term"
                $isolationErrors++
                $megumiFound = $true
            }
        }

        if (-not $megumiFound) {
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
    Write-Header "5. Output Template Check"

    Write-InfoMsg "Checking for required output structure..."

    if (Test-Path ".protocol-state/dev-notes.md") {
        Write-Pass "dev-notes.md exists (Yuuji's output template)"
    } else {
        Write-Warn "dev-notes.md not found - Yuuji hasn't created implementation log yet"
    }

    if (Test-Path ".protocol-state/security-review.md") {
        Write-Pass "security-review.md exists (Megumi's output template)"
    } else {
        Write-Warn "security-review.md not found - Megumi hasn't created security review yet"
    }

    Write-InfoMsg "Note: Deep template structure validation not yet implemented"
}

function Test-ClaudeMdProtection {
    Write-Header "6. CLAUDE.md Protection Check"

    if (Test-Path "CODEOWNERS") {
        if ((Get-Content "CODEOWNERS" -Raw) -match "protocol/CLAUDE.md") {
            Write-Pass "CODEOWNERS file protects protocol/CLAUDE.md"
        } else {
            Write-Warn "CODEOWNERS exists but doesn't protect protocol/CLAUDE.md"
        }
    } else {
        Write-Warn "CODEOWNERS file not found - consider adding for CLAUDE.md protection"
    }

    if (Test-Path "protocol.config.yaml") {
        if ((Get-Content "protocol.config.yaml" -Raw) -match "claude_md_protected:.*true") {
            Write-Pass "Config has CLAUDE.md protection enabled"
        } else {
            Write-Warn "Config does not explicitly enable CLAUDE.md protection"
        }
    }
}

function Test-BackupConfiguration {
    Write-Header "7. Backup Configuration Check"

    if (-not (Test-Path "protocol.config.yaml")) {
        Write-FailWithContext `
            -Message "protocol.config.yaml not found" `
            -Impact "Cannot verify backup configuration" `
            -Action "Ensure protocol.config.yaml exists" `
            -DocLink ""
        return
    }

    $ConfigContent = Get-Content "protocol.config.yaml" -Raw

    if ($ConfigContent -match "required_for:.*yuuji") {
        Write-Pass "Backup requirement configured for Yuuji"
    } else {
        Write-Warn "Backup requirement for Yuuji not found in config"
    }

    if ($ConfigContent -match "retention_days:\s*\d+") {
        Write-Pass "Backup retention policy configured"
    } else {
        Write-Warn "Backup retention policy not found in config"
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if ($Help) {
    Show-Help
}

if ($List) {
    Show-CheckList
}

Write-Host @"

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        DOMAIN ZERO PROTOCOL VERIFICATION TOOL                 ║
║                     Version 2.0                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

"@

Write-InfoMsg "Starting protocol verification..."
Write-InfoMsg "Working directory: $(Get-Location)"

if ($Quick) {
    Write-InfoMsg "Running in QUICK mode (critical checks only)"
}

if ($Skip.Count -gt 0) {
    Write-InfoMsg "Skipping checks: $($Skip -join ', ')"
}

if ($Only.Count -gt 0) {
    Write-InfoMsg "Running only: $($Only -join ', ')"
}

# Execute checks based on configuration
foreach ($check in $AvailableChecks) {
    if (Test-ShouldRunCheck -CheckName $check.Name -CheckLevel $check.Level) {
        & $check.Function

        # Stop if critical error occurred in critical check
        if ($script:CriticalError -and $check.Level -eq "critical") {
            Write-Host ""
            Write-Host "  [!] Critical error detected. Stopping verification." -ForegroundColor $ColorFail
            Write-Host "  Fix critical errors before running additional checks." -ForegroundColor $ColorInfo
            break
        }
    } else {
        Write-InfoMsg "Skipped check: $($check.Name)"
    }
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Header "Verification Summary"

Write-Host ""
Write-Host "  PASSED: $PassCount" -ForegroundColor $ColorPass
Write-Host "  WARNINGS: $WarningCount" -ForegroundColor $ColorWarn
Write-Host "  ERRORS: $ErrorCount" -ForegroundColor $ColorFail
Write-Host ""

if ($script:CriticalError) {
    Write-Host "  [X] Protocol verification FAILED (Critical Errors)" -ForegroundColor $ColorFail
    Write-Host "    Fix critical errors before proceeding." -ForegroundColor $ColorFail
    Write-Host ""
    Write-Host "  Tip: Run with -Verbose for detailed information" -ForegroundColor $ColorInfo
    exit 1
} elseif ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "  [PASS] Protocol verification PASSED - All checks successful!" -ForegroundColor $ColorPass
    exit 0
} elseif ($ErrorCount -eq 0) {
    Write-Host "  [WARN] Protocol verification PASSED with WARNINGS" -ForegroundColor $ColorWarn
    Write-Host "    Consider addressing warnings for optimal protocol operation." -ForegroundColor $ColorWarn
    exit 2
} else {
    Write-Host "  [X] Protocol verification FAILED" -ForegroundColor $ColorFail
    Write-Host "    Please fix errors before proceeding." -ForegroundColor $ColorFail
    Write-Host ""
    Write-Host "  Tip: Run with -Verbose for detailed information" -ForegroundColor $ColorInfo
    exit 1
}
