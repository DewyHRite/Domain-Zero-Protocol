# Domain Zero Protocol - Research Directory Initializer (PowerShell)
# Version: 1.0.0
#
# Purpose: Properly create the research directory structure with correct path separators
# This script fixes the common issue where directories are created with missing separators
# (e.g., ".protocol-stateresearchgojo" instead of ".protocol-state/research/gojo/")
#
# Usage:
#   .\init-research-dirs.ps1           # Create directories
#   .\init-research-dirs.ps1 -Clean    # Remove malformed directories first
#   .\init-research-dirs.ps1 -Verify   # Only verify structure, don't create

param(
    [switch]$Clean,
    [switch]$Verify,
    [string]$Path = "."
)

# ANSI color codes
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

# Fallback for older PowerShell
if ($PSVersionTable.PSVersion.Major -lt 7) {
    $Red = $Green = $Yellow = $Blue = $Cyan = $Reset = ""
}

Write-Host "${Cyan}============================================================${Reset}"
Write-Host "${Cyan}  Domain Zero Protocol - Research Directory Initializer${Reset}"
Write-Host "${Cyan}============================================================${Reset}"
Write-Host ""

# Define correct directory structure
$ProtocolStateDir = Join-Path -Path $Path -ChildPath ".protocol-state"
$ResearchDir = Join-Path -Path $ProtocolStateDir -ChildPath "research"
$AgentDirs = @("yuuji", "megumi", "nobara", "gojo")

# Define malformed directory patterns to detect/clean
$MalformedPatterns = @(
    ".protocol-stateresearch*",
    ".protocol-state research*",
    ".protocolstateresearch*"
)

# Function to detect malformed directories
function Find-MalformedDirs {
    param([string]$BasePath)

    $malformed = @()
    foreach ($pattern in $MalformedPatterns) {
        $found = Get-ChildItem -Path $BasePath -Directory -Filter $pattern -ErrorAction SilentlyContinue
        foreach ($dir in $found) {
            $malformed += $dir.FullName
        }
    }

    # Also check for agent-specific malformed paths
    foreach ($agent in $AgentDirs) {
        $badPatterns = @(
            ".protocol-stateresearch$agent",
            ".protocol-state research$agent",
            ".protocolstateresearch$agent"
        )
        foreach ($pattern in $badPatterns) {
            $badPath = Join-Path -Path $BasePath -ChildPath $pattern
            if (Test-Path -Path $badPath) {
                $malformed += $badPath
            }
        }
    }

    return $malformed | Select-Object -Unique
}

# Function to verify directory structure
function Test-ResearchStructure {
    param([string]$BasePath)

    $issues = @()

    # Check .protocol-state exists
    $stateDir = Join-Path -Path $BasePath -ChildPath ".protocol-state"
    if (-not (Test-Path -Path $stateDir)) {
        $issues += "Missing: .protocol-state/"
    }

    # Check research directory
    $researchDir = Join-Path -Path $stateDir -ChildPath "research"
    if (-not (Test-Path -Path $researchDir)) {
        $issues += "Missing: .protocol-state/research/"
    }

    # Check agent subdirectories
    foreach ($agent in $AgentDirs) {
        $agentDir = Join-Path -Path $researchDir -ChildPath $agent
        if (-not (Test-Path -Path $agentDir)) {
            $issues += "Missing: .protocol-state/research/$agent/"
        }
    }

    # Check research-index.json
    $indexFile = Join-Path -Path $researchDir -ChildPath "research-index.json"
    if (-not (Test-Path -Path $indexFile)) {
        $issues += "Missing: .protocol-state/research/research-index.json"
    }

    # Check README.md
    $readmeFile = Join-Path -Path $researchDir -ChildPath "README.md"
    if (-not (Test-Path -Path $readmeFile)) {
        $issues += "Missing: .protocol-state/research/README.md"
    }

    return $issues
}

# Step 1: Detect malformed directories
Write-Host "${Blue}Step 1: Checking for malformed directories...${Reset}"
$malformedDirs = Find-MalformedDirs -BasePath $Path

if ($malformedDirs.Count -gt 0) {
    Write-Host "${Yellow}[!] Found $($malformedDirs.Count) malformed directory(s):${Reset}"
    foreach ($dir in $malformedDirs) {
        Write-Host "    ${Red}$dir${Reset}"
    }
    Write-Host ""

    if ($Clean) {
        Write-Host "${Yellow}Cleaning malformed directories...${Reset}"
        foreach ($dir in $malformedDirs) {
            try {
                Remove-Item -Path $dir -Recurse -Force
                Write-Host "  ${Green}[REMOVED]${Reset} $dir"
            } catch {
                Write-Host "  ${Red}[FAILED]${Reset} Could not remove: $dir"
                Write-Host "    Error: $_"
            }
        }
        Write-Host ""
    } else {
        Write-Host "${Yellow}Use -Clean flag to remove these directories${Reset}"
        Write-Host ""
    }
} else {
    Write-Host "  ${Green}[OK]${Reset} No malformed directories found"
    Write-Host ""
}

# Step 2: Verify current structure
Write-Host "${Blue}Step 2: Verifying directory structure...${Reset}"
$issues = Test-ResearchStructure -BasePath $Path

if ($issues.Count -gt 0) {
    Write-Host "${Yellow}[!] Found $($issues.Count) issue(s):${Reset}"
    foreach ($issue in $issues) {
        Write-Host "    ${Yellow}$issue${Reset}"
    }
    Write-Host ""
} else {
    Write-Host "  ${Green}[OK]${Reset} Directory structure is correct"
    Write-Host ""
}

# Exit if verify-only mode
if ($Verify) {
    Write-Host "${Blue}Verify mode - no changes made${Reset}"
    if ($issues.Count -eq 0 -and $malformedDirs.Count -eq 0) {
        Write-Host "${Green}Research directory structure is correct!${Reset}"
        exit 0
    } else {
        Write-Host "${Yellow}Issues found. Run without -Verify to fix.${Reset}"
        exit 1
    }
}

# Step 3: Create correct directory structure
Write-Host "${Blue}Step 3: Creating correct directory structure...${Reset}"

# Create .protocol-state
if (-not (Test-Path -Path $ProtocolStateDir)) {
    New-Item -Path $ProtocolStateDir -ItemType Directory -Force | Out-Null
    Write-Host "  ${Green}[CREATED]${Reset} .protocol-state/"
}

# Create research directory
if (-not (Test-Path -Path $ResearchDir)) {
    New-Item -Path $ResearchDir -ItemType Directory -Force | Out-Null
    Write-Host "  ${Green}[CREATED]${Reset} .protocol-state/research/"
}

# Create agent subdirectories
foreach ($agent in $AgentDirs) {
    $agentDir = Join-Path -Path $ResearchDir -ChildPath $agent
    if (-not (Test-Path -Path $agentDir)) {
        New-Item -Path $agentDir -ItemType Directory -Force | Out-Null
        Write-Host "  ${Green}[CREATED]${Reset} .protocol-state/research/$agent/"
    } else {
        Write-Host "  ${Blue}[EXISTS]${Reset} .protocol-state/research/$agent/"
    }
}

# Create research-index.json if missing
$indexFile = Join-Path -Path $ResearchDir -ChildPath "research-index.json"
if (-not (Test-Path -Path $indexFile)) {
    $indexContent = @{
        version = "1.0"
        created = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        agents = @{
            yuuji = @{
                last_session = $null
                session_count = 0
                topics = @()
            }
            megumi = @{
                last_session = $null
                session_count = 0
                topics = @()
            }
            nobara = @{
                last_session = $null
                session_count = 0
                topics = @()
            }
            gojo = @{
                last_session = $null
                session_count = 0
                topics = @()
            }
        }
    }
    $indexContent | ConvertTo-Json -Depth 10 | Set-Content -Path $indexFile -Encoding UTF8
    Write-Host "  ${Green}[CREATED]${Reset} .protocol-state/research/research-index.json"
}

# Create README.md if missing
$readmeFile = Join-Path -Path $ResearchDir -ChildPath "README.md"
if (-not (Test-Path -Path $readmeFile)) {
    $readmeContent = @"
# Domain Zero Protocol - Research Directory

This directory contains research session outputs from Domain Zero agents.

## Structure

```
.protocol-state/research/
├── research-index.json       # Global index tracking all research sessions
├── yuuji/                    # Yuuji (Implementation) research outputs
├── megumi/                   # Megumi (Security) research outputs
├── nobara/                   # Nobara (Creative Strategy/UX) research outputs
├── gojo/                     # Gojo (Mission Control) research outputs
└── README.md                 # This file
```

## File Naming Convention

- Summaries: `{timestamp}.summary.md` (version controlled)
- Raw notes: `{timestamp}.raw.log` (gitignored for privacy)

## Usage

Invoke research mode with any agent:
- `Read yuuji.agent.md --research and investigate [topic]`
- `Read megumi.agent.md --research and investigate [topic]`
- `Read nobara.agent.md --research and investigate [topic]`
- `Read gojo.agent.md --research and investigate [topic]`

## Privacy

Raw research notes (.raw.log files) are gitignored by default to protect privacy.
Only curated summaries (.summary.md) are tracked in version control.
"@
    $readmeContent | Set-Content -Path $readmeFile -Encoding UTF8
    Write-Host "  ${Green}[CREATED]${Reset} .protocol-state/research/README.md"
}

Write-Host ""

# Final verification
Write-Host "${Blue}Step 4: Final verification...${Reset}"
$finalIssues = Test-ResearchStructure -BasePath $Path

if ($finalIssues.Count -eq 0) {
    Write-Host "  ${Green}[OK]${Reset} All directories created successfully!"
    Write-Host ""
    Write-Host "${Green}============================================================${Reset}"
    Write-Host "${Green}  Research directory structure is ready!${Reset}"
    Write-Host "${Green}============================================================${Reset}"
    Write-Host ""
    Write-Host "Directory structure:"
    Write-Host "  .protocol-state/"
    Write-Host "  └── research/"
    Write-Host "      ├── research-index.json"
    Write-Host "      ├── README.md"
    Write-Host "      ├── yuuji/"
    Write-Host "      ├── megumi/"
    Write-Host "      ├── nobara/"
    Write-Host "      └── gojo/"
    Write-Host ""
    exit 0
} else {
    Write-Host "${Red}[ERROR]${Reset} Some issues remain:"
    foreach ($issue in $finalIssues) {
        Write-Host "    ${Red}$issue${Reset}"
    }
    exit 1
}
