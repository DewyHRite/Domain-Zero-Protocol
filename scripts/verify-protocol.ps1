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

    # Check for PowerShell (accept either pwsh or powershell executable)
    $foundPowerShell = $false
    $psExecutables = @("pwsh", "powershell")

    Write-InfoMsg "Checking for PowerShell executable..."
    foreach ($exe in $psExecutables) {
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            Write-Pass "Found PowerShell executable: $exe"
            $foundPowerShell = $true
            break
        }
    }

    if (-not $foundPowerShell) {
        Write-FailWithContext `
            -Message "No PowerShell executable found in PATH" `
            -Impact "Verification cannot proceed without PowerShell" `
            -Action "Install PowerShell (pwsh) or ensure it's in PATH" `
            -DocLink "https://learn.microsoft.com/powershell/"
        exit 3
    }

    # Check optional tools
    $optionalTools = @("python", "python3", "yamllint")
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
        "protocol/yuuji.agent.md",
        "protocol/megumi.agent.md",
        "protocol/nobara.agent.md",
        "protocol/gojo.agent.md",
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
        # SEC-001 (v9.3.3): force UTF-8 so valid non-ASCII YAML does not false-fail
        # on Windows, where open() otherwise uses the active ANSI code page.
        $yamlTest = & $pythonCmd -c "import yaml; yaml.safe_load(open('protocol.config.yaml', encoding='utf-8'))" 2>&1
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

    # Check for placeholder values that need to be updated.
    # SEC-9720-004: the contact placeholder (email@example.com) is demoted to a
    # WARNING so a fresh install passes verification; all other placeholders remain
    # hard ERRORs because they affect project identity / repo references.
    # BUGREPORT-009 (re-rated P3 -> P2): this check could NEVER FIRE.
    #
    # It searched only for Title-Case literals ("Your Name", "Your Project
    # Name", ...). The distribution actually ships UPPER_SNAKE placeholders --
    # protocol.config.yaml carries `name: "YOUR_NAME"` and
    # `name: "YOUR_PROJECT_NAME"`. PowerShell's -match is case-insensitive, so
    # case was never the problem; the SEPARATOR was. "Your Name" (space) can
    # not match "YOUR_NAME" (underscore). Zero overlap across the entire list.
    #
    # This was not drift that degraded accuracy. There was no configuration of
    # a fresh install in which this check could fire on the identity fields it
    # exists to guard, so its "No placeholder values detected" PASS carried no
    # information for that check class, in every install, for an unknown
    # period. A gate that cannot fail is worse than an absent gate: it
    # manufactures false confidence. Confirmed empirically before this fix by
    # running `-Only config` against a config containing BOTH placeholders --
    # the checker printed PASS.
    #
    # The fix is a case/separator-TOLERANT regex family, so a future template
    # restyling (YOUR_NAME -> Your-Name -> your name) cannot silently
    # reintroduce the same false negative. Matching a fixed literal is what
    # broke; matching the SHAPE is what survives.
    $ContactPlaceholder = "email@example.com"

    # Retained for backward compatibility with older or hand-edited configs
    # that really do carry the Title-Case forms. No regression.
    $LegacyPlaceholders = @(
        "Your Name",
        "Your Project Name",
        "Your Organization",
        "your-org/your-repo",
        "YYYY-MM-DD"
    )

    $PlaceholderPatterns = @(
        @{ Label = "YOUR_NAME-style placeholder";         Regex = "YOUR[_\-\s]+NAME\b" },
        @{ Label = "YOUR_PROJECT_NAME-style placeholder"; Regex = "YOUR[_\-\s]+PROJECT[_\-\s]+NAME\b" },
        @{ Label = "YOUR_ORGANIZATION-style placeholder"; Regex = "YOUR[_\-\s]+ORG(ANIZATION)?\b" },
        @{ Label = "YOUR_REPO-style placeholder";         Regex = "YOUR[_\-\s]+REPO\b" }
    )

    # Scope detection to YAML *values* by stripping inline comments. Without
    # this the file's own explanatory prose -- e.g. a comment reading "adjust
    # for your project" -- false-positives.
    #
    # SEC-VERIFYPS-001: the first version of this scoping split on the FIRST
    # '#' in the line, unconditionally. A '#' living INSIDE a quoted scalar
    # (a URL fragment, a channel name, a product name such as "C# Toolkit")
    # therefore truncated the line and hid every placeholder after it. That is
    # a newly-introduced path along which THIS GATE CANNOT FIRE, created inside
    # the fix for a finding titled "a gate that could never fire". The earlier
    # claim that no shipped config places a '#' inside a quoted value was true
    # of the shipped configs and irrelevant to the CONSUMER configs this gate
    # actually runs against.
    #
    # Rule applied (YAML's own): a '#' opens a comment only when it is OUTSIDE
    # quotes AND is at the start of the line or preceded by whitespace.
    #
    # Deliberately NOT a YAML parse: this script must keep working on a config
    # too malformed to parse, which is exactly when it matters most. A line
    # with unbalanced quotes therefore strips NOTHING, which fails toward
    # reporting a placeholder rather than toward hiding one.
    function Get-YamlValuePortion {
        param([string]$Line)
        $inSingle = $false
        $inDouble = $false
        for ($i = 0; $i -lt $Line.Length; $i++) {
            $ch = $Line[$i]
            if ($ch -eq "'" -and -not $inDouble) { $inSingle = -not $inSingle; continue }
            if ($ch -eq '"' -and -not $inSingle) { $inDouble = -not $inDouble; continue }
            if ($ch -eq '#' -and -not $inSingle -and -not $inDouble) {
                if ($i -eq 0 -or [char]::IsWhiteSpace($Line[$i - 1])) {
                    return $Line.Substring(0, $i)
                }
            }
        }
        return $Line
    }

    $ConfigValuesOnly = (
        ($ConfigContent -split "`n") | ForEach-Object { Get-YamlValuePortion $_ }
    ) -join "`n"

    $PlaceholdersFound = @()
    foreach ($Placeholder in $LegacyPlaceholders) {
        if ($ConfigValuesOnly -match [regex]::Escape($Placeholder)) {
            $PlaceholdersFound += $Placeholder
        }
    }
    foreach ($Pattern in $PlaceholderPatterns) {
        if ($ConfigValuesOnly -match $Pattern.Regex) {
            $PlaceholdersFound += $Pattern.Label
        }
    }

    # Check the contact placeholder separately as a warning.
    # SEC-9720-004 preserved: contact stays a WARNING so a fresh install still
    # passes verification; every identity placeholder above remains a hard
    # ERROR.
    if ($ConfigValuesOnly -match [regex]::Escape($ContactPlaceholder)) {
        Write-Warn "contact field still contains placeholder '$ContactPlaceholder' - update protocol.config.yaml with your real contact address."
    }

    if ($PlaceholdersFound.Count -eq 0) {
        Write-Pass "No (non-contact) placeholder values detected in config"
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
    if (Test-Path "protocol/yuuji.agent.md") {
        $forbiddenTerms = @("GOJO", "Satoru Gojo", "Mission Control", "Trigger 19", "trigger-19")
        $yuujiFound = $false

        foreach ($term in $forbiddenTerms) {
            if ((Get-Content "protocol/yuuji.agent.md" -Raw) -match [regex]::Escape($term)) {
                Write-Warn "Yuuji protocol mentions forbidden term: $term"
                $isolationErrors++
                $yuujiFound = $true
            }
        }

        if (-not $yuujiFound) {
            Write-Pass "Yuuji isolation vocabulary check passed"
        }
    } else {
        Write-Warn "protocol/yuuji.agent.md not found"
    }

    # Megumi should not mention Gojo directly
    if (Test-Path "protocol/megumi.agent.md") {
        $forbiddenTerms = @("GOJO", "Satoru Gojo", "Mission Control", "Trigger 19", "trigger-19")
        $megumiFound = $false

        foreach ($term in $forbiddenTerms) {
            if ((Get-Content "protocol/megumi.agent.md" -Raw) -match [regex]::Escape($term)) {
                Write-Warn "Megumi protocol mentions forbidden term: $term"
                $isolationErrors++
                $megumiFound = $true
            }
        }

        if (-not $megumiFound) {
            Write-Pass "Megumi isolation vocabulary check passed"
        }
    } else {
        Write-Warn "protocol/megumi.agent.md not found"
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

+---------------------------------------------------------------+
|                                                               |
|        DOMAIN ZERO PROTOCOL VERIFICATION TOOL                 |
|                     Version 2.0                               |
|                                                               |
+---------------------------------------------------------------+

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
