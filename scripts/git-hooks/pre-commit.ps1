# Domain Zero Protocol - Unified Pre-commit Hook (FEAT-GUARD-001, v9.9.5)
# PowerShell equivalent of scripts/git-hooks/pre-commit for PowerShell-driven git
# hook setups.
#
# Run order:
#   1. Secret scan           (SEC-001: protected records always scanned for secrets —
#                              runs BEFORE the publish-branch skip so DZP-v*/release
#                              branches are scanned too, see step 2's comment)
#   2. Publish-branch skip   (DZP-v* / release branches bypass the REMAINING dev-state
#                              checks below, but NOT the secret scan above)
#   3. Append-only guard     (FEAT-GUARD-001: protected docs must only grow)
#   4. Agent/file guard      (FEAT-REQ-001: Cross-Agent Edit Restrictions)
#   5. Protocol validation   (validate-protocol.py --check)
#
# DZP_ALLOW_PROTOCOL_EDIT=1 (v9.9.5+): scoped override for stage 4 ONLY (the
# FEAT-REQ-001 protected-path guard). Mirrors DZP_ALLOW_PROTECTED_REWRITE
# (stage 3's override) so a Gojo/USER-authorized protocol change can commit
# without `git commit --no-verify`, which dangerously skips EVERY stage.
# The two overrides are independent and composable: DZP_ALLOW_PROTOCOL_EDIT
# alone does NOT bypass stage 3 (append-only) or stage 5 (validate-protocol).
#
$ErrorActionPreference = 'Stop'

$root = (& git rev-parse --show-toplevel 2>$null)
if (-not $root) { $root = (Get-Location).Path }
$config = Join-Path $root 'protocol.config.yaml'

# ============================================================================
# 1. SEC-001: PROTECTED-RECORDS SECRET SCAN (compensates the GitHub
#    secret_scanning.yml file-wide path-ignore on dev-notes.md — see that file
#    and scripts/scan_protected_records.py for full rationale)
# ============================================================================
# CodeRabbit PR#108: intentionally runs BEFORE the publish-branch skip (step 2)
# below. DZP-v*/release branches are still real commits that dzp-publish
# produces from real content — the prior ordering let the branch-skip exit
# before this scan ever ran, so a secret staged on a publish branch was never
# caught by this gate at all. Everything else in this hook legitimately does
# not apply to publish branches (dev-state validation, append-only, agent/file
# guard); the secret scan is the one check that must still apply everywhere.
# (Kept in parity with scripts/git-hooks/pre-commit, the POSIX equivalent.)
$secretScan = Join-Path $root 'scripts/scan_protected_records.py'
if (Test-Path $secretScan) {
    $pys = (Get-Command python3 -ErrorAction SilentlyContinue) ?? (Get-Command python -ErrorAction SilentlyContinue)
    if ($pys) {
        & $pys.Source $secretScan
        if ($LASTEXITCODE -ne 0) { exit 1 }
    } else {
        [Console]::Error.WriteLine('[protected-secret-scan] WARNING: python not found — secret scan SKIPPED')
    }
} else {
    [Console]::Error.WriteLine('[protected-secret-scan] WARNING: scripts/scan_protected_records.py not found — secret scan SKIPPED')
}

# ============================================================================
# 2. PUBLISH-BRANCH SKIP
# ============================================================================
# The secret scan (step 1, above) already ran and is NOT bypassed by this
# early exit.
$currentBranch = (& git symbolic-ref --short HEAD 2>$null)
if ($currentBranch -match '^DZP-v\d' -or $currentBranch -eq 'release') {
    Write-Host "Publish branch ($currentBranch, distro artifact) — skipping dev-state validation (gated by dzp-publish)."
    exit 0
}

# ============================================================================
# 3. FEAT-GUARD-001: PROJECT DOCUMENTS append-only enforcement
# ============================================================================
# dev-notes.md, security-review.md and domain.record.md must only grow.
# Override a legit rewrite (rotation / authorized restore) with
# DZP_ALLOW_PROTECTED_REWRITE=1.
$guard = Join-Path $root 'scripts/check_protected_append_only.py'
if (Test-Path $guard) {
    $pyg = (Get-Command python3 -ErrorAction SilentlyContinue) ?? (Get-Command python -ErrorAction SilentlyContinue)
    if ($pyg) {
        & $pyg.Source $guard
        if ($LASTEXITCODE -ne 0) { exit 1 }
    } else {
        [Console]::Error.WriteLine('[protected-guard] WARNING: python not found — append-only guard SKIPPED')
    }
}

# ============================================================================
# 4. FEAT-REQ-001: AGENT / PROTECTED-FILE GUARD (Cross-Agent Edit Restrictions)
# ============================================================================
# Check BOTH sides of renames/copies (a rename FROM a protected path must be
# blocked) and include Deletions. --name-status emits "M<TAB>path", "D<TAB>path",
# "R<score><TAB>old<TAB>new", etc.; collect every path column (skip the status code).
$status = & git diff --cached --name-status --find-renames --diff-filter=ACMRD
if ($status) {
    $staged = @()
    foreach ($line in $status) {
        $parts = $line -split "`t"
        if ($parts.Count -ge 2) { $staged += $parts[1..($parts.Count - 1)] | Where-Object { $_ } }
    }

    if ($staged) {
        $defaultPaths = @(
            'protocol/', '.claude/agents/',
            '.protocol-state/custom-agent-registry.json',
            '.protocol-state/authorization/', 'protocol.config.yaml'
        )

        function Get-ProtectedPaths {
            $py = (Get-Command python3 -ErrorAction SilentlyContinue) ?? (Get-Command python -ErrorAction SilentlyContinue)
            if ($py -and (Test-Path $config)) {
                $script = @'
import sys
try:
    import yaml
    cfg = yaml.safe_load(open(sys.argv[1], encoding="utf-8")) or {}
    fp = ((cfg.get("custom_agent_security") or {}).get("file_protection") or {})
    for p in (fp.get("immutable_paths") or []):
        print(str(p).strip())
except Exception:
    sys.exit(7)
'@
                try {
                    $out = $script | & $py.Source - $config 2>$null
                    if ($LASTEXITCODE -eq 0 -and $out) { return @($out | Where-Object { $_ }) }
                } catch { }
            }
            return $defaultPaths
        }

        $protected = Get-ProtectedPaths | ForEach-Object { $_.Trim() } | Where-Object { $_ }
        $violations = @()
        foreach ($f in $staged) {
            $ff = $f.Trim()
            foreach ($p in $protected) {
                if ($ff.StartsWith($p)) { $violations += "  $ff    (protected: $p)" }
            }
        }

        if ($violations.Count -gt 0) {
            if ($env:DZP_ALLOW_PROTOCOL_EDIT -eq '1') {
                # Scoped bypass for THIS stage only. Loud, unconditional, never
                # silent. Stage 3 (append-only) and stage 5 (validate-protocol)
                # below are NOT affected by this variable and still run.
                [Console]::Error.WriteLine('')
                [Console]::Error.WriteLine('[protocol-guard] BYPASS: authorized protocol edit (DZP_ALLOW_PROTOCOL_EDIT=1) - FEAT-REQ-001 protected-path check skipped for this commit.')
                [Console]::Error.WriteLine('Staged changes allowed through by this override:')
                [Console]::Error.WriteLine('')
                $violations | ForEach-Object { [Console]::Error.WriteLine($_) }
                [Console]::Error.WriteLine('Append-only guard (stage 3) and validate-protocol.py (stage 5) remain ACTIVE and unaffected.')
                [Console]::Error.WriteLine('')
            } else {
                Write-Host ''
                Write-Host '=================================================================='
                Write-Host '  DZP PROTECTED-FILE COMMIT BLOCKED (Cross-Agent Edit Restrictions)'
                Write-Host '=================================================================='
                Write-Host 'Staged changes modify DZP-protected paths:'
                Write-Host ''
                $violations | ForEach-Object { Write-Host $_ }
                Write-Host ''
                Write-Host 'These files are protected. Sanctioned ways to proceed:'
                Write-Host '  1. Invoke Gojo (Mission Control) for an authorized protocol change.'
                Write-Host '  2. Invoke Sukuna via Gojo for system / protocol updates.'
                Write-Host '  3. Override intentionally:  git commit --no-verify'
                Write-Host '  4. Override just this stage (keeps append-only + validation active): DZP_ALLOW_PROTOCOL_EDIT=1 git commit'
                Write-Host ''
                Write-Host 'Reference: protocol/CLAUDE.md  (Cross-Agent Edit Restrictions)'
                Write-Host ''
                exit 1
            }
        }
    }
}

# ============================================================================
# 5. PROTOCOL STATE VALIDATION
# ============================================================================
Write-Host "Running Domain Zero Protocol validation..."

$py = (Get-Command python3 -ErrorAction SilentlyContinue) ?? (Get-Command python -ErrorAction SilentlyContinue)
if ($py) {
    & $py.Source (Join-Path $root 'scripts/validate-protocol.py') --check
    $validationExit = $LASTEXITCODE
} else {
    # M4 (CodeRabbit PR#99): fail-CLOSED when python is absent.
    # The prior code set $validationExit = 0 (fail-OPEN), allowing commits to
    # bypass protocol validation entirely when no python runtime was installed.
    # Protocol validation is a GATE — missing python must block the commit.
    # NOTE: the append-only guard (stage 3, above) is intentionally best-effort
    # / non-fatal when python is absent (it warns and skips). This stage is a
    # hard gate; the distinction is documented in both hooks for clarity.
    [Console]::Error.WriteLine("COMMIT BLOCKED: Python runtime is required for protocol validation (scripts/validate-protocol.py --check).")
    [Console]::Error.WriteLine("Install Python 3 (https://python.org) or bypass intentionally with: git commit --no-verify")
    $validationExit = 1
}

if ($validationExit -ne 0) {
    Write-Host ""
    Write-Host "COMMIT BLOCKED: Protocol validation failed"
    Write-Host ""
    Write-Host "State files have validation errors. Fix the issues above before committing."
    Write-Host ""
    Write-Host "To bypass this check (NOT RECOMMENDED):"
    Write-Host "  git commit --no-verify"
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Protocol validation passed - proceeding with commit"
Write-Host ""

exit 0
