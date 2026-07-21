# Domain Zero Protocol - Unified Pre-commit Hook (FEAT-GUARD-001, v9.10.2)
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
#   6. Issue-id registry gate (FEAT-IDGOV-001: check_issue_ids.py — early
#                              feedback only; INERT while protocol.config.yaml
#                              issue_governance.enabled=false, see that gate's
#                              own docstring; the AUTHORITATIVE tier is CI --
#                              .github/workflows/idgov-gate.yml, Phase G2)
#
# DZP_ALLOW_PROTOCOL_EDIT=1 (v9.9.5+): scoped override for stage 4 ONLY (the
# FEAT-REQ-001 protected-path guard). Mirrors DZP_ALLOW_PROTECTED_REWRITE
# (stage 3's override) so a Gojo/USER-authorized protocol change can commit
# without `git commit --no-verify`, which dangerously skips EVERY stage.
# The two overrides are independent and composable: DZP_ALLOW_PROTOCOL_EDIT
# alone does NOT bypass stage 3 (append-only) or stage 5 (validate-protocol).
#
# DZP_ALLOW_MISSING_SECRET_SCAN=1 (F9/F10, v9.9.5+): a THIRD, independent,
# dedicated break-glass override -- for stage 1 ONLY, covering BOTH ways the
# mandatory SEC-001 secret scan can fail to run: (F9) the scanner file
# cannot be found, and (F10) no python3/python runtime is available to RUN
# it even when present. Both used to WARN then allow the commit through;
# stage 1 now fails CLOSED by default in both cases. Never conflated with
# the other two overrides above (stage 3's append-only guard intentionally
# stays best-effort when python is absent; stage 5's validate-protocol.py
# already fails closed independently when python is absent).
#
# DZP_ALLOW_MISSING_APPEND_GUARD=1 (BUG-HOOK-SELF-DISARM-001, v9.9.6+): a
# FOURTH, independent, dedicated break-glass override -- for stage 3 ONLY,
# covering the guard FILE (scripts/check_protected_append_only.py) being
# absent (e.g. deleted, or a distro install missing it). Previously an
# absent guard file silently WARNED-then-passed with no block -- the entire
# FEAT-GUARD-001 append-only check (and the SEC-TOJI-102 stub tripwire it
# also performs) vanished with zero warning, unlike stage 1's F9/F10.
# Stage 3 now fails CLOSED by default when the guard file cannot be found.
# Never reused for, or conflated with, DZP_ALLOW_PROTECTED_REWRITE (a
# legitimate rewrite when the guard IS present and running),
# DZP_ALLOW_PROTOCOL_EDIT (stage 4), or DZP_ALLOW_MISSING_SECRET_SCAN
# (stage 1) -- this is "the append-only guard file itself cannot be found."
#
# DZP_ALLOW_ISSUE_ID_OVERRIDE=1 (FEAT-IDGOV-001, v9.10.0+): a FIFTH,
# independent, dedicated break-glass override -- for stage 6's GENUINE
# REGISTRY VIOLATION path ONLY (the issue-id registry gate,
# scripts/check_issue_ids.py returning non-zero because it found a real
# append-only/E1-E6 violation). Same override name check_issue_ids.py itself
# already documents and implements internally for a genuine registry
# violation (backfill / migration / authorized exception) -- this hook stage
# does not reimplement that bypass logic, it only runs the script and
# propagates its exit code. Never conflated with DZP_ALLOW_PROTECTED_REWRITE,
# DZP_ALLOW_PROTOCOL_EDIT, DZP_ALLOW_MISSING_SECRET_SCAN, or
# DZP_ALLOW_MISSING_APPEND_GUARD.
#
# DZP_ALLOW_MISSING_ISSUE_ID_GATE=1 (SEC-IDGOV-G-001, Megumi Phase G review,
# v9.10.0+): a SIXTH, independent, dedicated break-glass override -- for
# stage 6's DEPENDENCY-GAP path ONLY, covering the gate SCRIPT
# (scripts/check_issue_ids.py) being absent OR no python3/python runtime
# being available to run it. Earlier drafts reused DZP_ALLOW_ISSUE_ID_OVERRIDE
# for BOTH the genuine-violation path above AND this missing-gate fallback --
# Megumi's Phase G review flagged that as the same conflation class
# BUG-HOOK-SELF-DISARM-001 closed for stage 3: an operator setting
# DZP_ALLOW_ISSUE_ID_OVERRIDE=1 to authorize a legitimate content override
# (e.g. a backfill) would unknowingly ALSO mask a broken/missing gate, since
# one flag covered two unrelated risk decisions. This dedicated override
# mirrors DZP_ALLOW_MISSING_APPEND_GUARD's split from
# DZP_ALLOW_PROTECTED_REWRITE exactly. Setting DZP_ALLOW_ISSUE_ID_OVERRIDE
# alone no longer bypasses the missing-gate branches -- only this override
# does. Never conflated with any of the other five overrides above.
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
        # F10 (CodeRabbit PR#109 round-2, P2): previously WARNED then allowed
        # the commit through -- a missing Python runtime silently skipped the
        # mandatory SEC-001 secret scan. Reuses the SAME
        # DZP_ALLOW_MISSING_SECRET_SCAN override as the scanner-missing
        # branch below (F9) -- no new env var. Scoped to this stage only.
        if ($env:DZP_ALLOW_MISSING_SECRET_SCAN -eq '1') {
            [Console]::Error.WriteLine('[protected-secret-scan] BYPASS: DZP_ALLOW_MISSING_SECRET_SCAN=1 — Python runtime not found, SEC-001 scan SKIPPED (authorized).')
        } else {
            [Console]::Error.WriteLine('[protected-secret-scan] COMMIT BLOCKED: no Python runtime — mandatory SEC-001 secret scan cannot run.')
            [Console]::Error.WriteLine('  Fix: install Python 3, or set DZP_ALLOW_MISSING_SECRET_SCAN=1 git commit ... to bypass (authorized).')
            exit 1
        }
    }
} else {
    # F9 (CodeRabbit PR#109, P2): previously WARNED then allowed the commit
    # through — a missing scanner silently skipped the mandatory SEC-001
    # secret-scan gate. Now fails CLOSED by default, with a dedicated
    # break-glass override (DZP_ALLOW_MISSING_SECRET_SCAN).
    if ($env:DZP_ALLOW_MISSING_SECRET_SCAN -eq '1') {
        [Console]::Error.WriteLine('[protected-secret-scan] BYPASS: DZP_ALLOW_MISSING_SECRET_SCAN=1 — scanner not found, SEC-001 scan SKIPPED (authorized).')
    } else {
        [Console]::Error.WriteLine('[protected-secret-scan] COMMIT BLOCKED: scripts/scan_protected_records.py not found — mandatory SEC-001 secret scan cannot run.')
        [Console]::Error.WriteLine('  Fix: restore the scanner or reinstall via scripts/install-git-hooks.(sh|ps1).')
        [Console]::Error.WriteLine('  Authorized exception: DZP_ALLOW_MISSING_SECRET_SCAN=1 git commit ...')
        exit 1
    }
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
} else {
    # BUG-HOOK-SELF-DISARM-001 (Sukuna Bug Hunt 2026-07-11, P1, gap 2): this
    # branch previously did not exist -- a missing guard file silently
    # skipped the ENTIRE FEAT-GUARD-001 append-only check (and the
    # SEC-TOJI-102 stub tripwire), with no warning and no block. Mirrors
    # stage 1's F9 fail-closed structure exactly, with its OWN dedicated
    # break-glass override (see header comment for why this is not
    # DZP_ALLOW_PROTECTED_REWRITE / DZP_ALLOW_PROTOCOL_EDIT /
    # DZP_ALLOW_MISSING_SECRET_SCAN).
    if ($env:DZP_ALLOW_MISSING_APPEND_GUARD -eq '1') {
        [Console]::Error.WriteLine('[protected-guard] BYPASS: DZP_ALLOW_MISSING_APPEND_GUARD=1 — guard not found, FEAT-GUARD-001 append-only check SKIPPED (authorized).')
    } else {
        [Console]::Error.WriteLine('[protected-guard] COMMIT BLOCKED: scripts/check_protected_append_only.py not found — mandatory FEAT-GUARD-001 append-only guard cannot run.')
        [Console]::Error.WriteLine('  Fix: restore the guard or reinstall via scripts/install-git-hooks.(sh|ps1).')
        [Console]::Error.WriteLine('  Authorized exception: DZP_ALLOW_MISSING_APPEND_GUARD=1 git commit ...')
        exit 1
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
        # BUG-HOOK-SELF-DISARM-001 residual (P3 fold-in): this fallback must
        # never be a WEAKER list than the config-driven path below -- it now
        # mirrors the same security-critical engine scripts added to
        # protocol.config.yaml immutable_paths, so a degraded (python/yaml
        # unavailable) run of this hook still protects them.
        $defaultPaths = @(
            'protocol/', '.claude/agents/',
            '.protocol-state/custom-agent-registry.json',
            '.protocol-state/authorization/', 'protocol.config.yaml',
            'scripts/git-hooks/',
            'scripts/scan_protected_records.py',
            'scripts/check_protected_append_only.py',
            'scripts/validate-protocol.py',
            'scripts/check_branch_record_isolation.py',
            'scripts/distro/assert_version.py',
            'scripts/distro/check_version_stamps.py',
            'scripts/check_issue_ids.py',
            'scripts/backfill_issue_registry.py',
            'scripts/issue_id.py',
            'scripts/idgov/grammar.py',
            'scripts/idgov/registry.py',
            'scripts/idgov/identity.py',
            'scripts/idgov/engine.py',
            'scripts/idgov/__init__.py',
            'scripts/secid.sh',
            'scripts/secid.ps1',
            'scripts/residentid-sukuna.sh',
            'scripts/residentid-sukuna.ps1',
            'scripts/residentid-gojo.sh',
            'scripts/residentid-gojo.ps1',
            'scripts/residentid-yuuji.sh',
            'scripts/residentid-yuuji.ps1',
            '.protocol-state/script_coordinator.py',
            '.protocol-state/script_dependencies.yaml'
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

# ============================================================================
# 6. FEAT-IDGOV-001: ISSUE-ID REGISTRY GATE (Phase G1)
# ============================================================================
# check_issue_ids.py enforces the append-only issue-id registry invariants.
# EARLY FEEDBACK ONLY -- the authoritative tier is CI
# (.github/workflows/idgov-gate.yml, Phase G2), which diffs the full push/PR
# range, not just the staged index.
#
# INERT BY DESIGN: protocol.config.yaml issue_governance.enabled governs
# whether the gate actually checks anything -- when false (the shipped
# default while FEAT-IDGOV-001 is pending its own separate, deliberate,
# USER-gated go-live), check_issue_ids.py itself prints a loud
# "[idgov-gate] DISABLED via config" notice to stderr and exits 0. This stage
# does not duplicate that logic -- it always invokes the script and trusts
# its own config-driven no-op. A genuine registry violation's bypass
# (DZP_ALLOW_ISSUE_ID_OVERRIDE=1) is handled entirely INSIDE
# check_issue_ids.py; this stage just runs the script (inheriting the
# caller's environment) and propagates the result.
$idgovGate = Join-Path $root 'scripts/check_issue_ids.py'
if (Test-Path $idgovGate) {
    $pyi = (Get-Command python3 -ErrorAction SilentlyContinue) ?? (Get-Command python -ErrorAction SilentlyContinue)
    if ($pyi) {
        & $pyi.Source $idgovGate
        if ($LASTEXITCODE -ne 0) { exit 1 }
    } else {
        # SEC-IDGOV-G-001 (Megumi Phase G review, P2): "python runtime not
        # found" dependency-gap case -- distinct from a genuine registry
        # violation. Uses the dedicated DZP_ALLOW_MISSING_ISSUE_ID_GATE
        # override (NOT DZP_ALLOW_ISSUE_ID_OVERRIDE -- see header note).
        if ($env:DZP_ALLOW_MISSING_ISSUE_ID_GATE -eq '1') {
            [Console]::Error.WriteLine('[idgov-gate] BYPASS: DZP_ALLOW_MISSING_ISSUE_ID_GATE=1 — Python runtime not found, issue-id registry gate SKIPPED (authorized).')
        } else {
            [Console]::Error.WriteLine('[idgov-gate] COMMIT BLOCKED: no Python runtime — issue-id registry gate cannot run.')
            [Console]::Error.WriteLine('  Fix: install Python 3, or set DZP_ALLOW_MISSING_ISSUE_ID_GATE=1 git commit ... to bypass (authorized).')
            exit 1
        }
    }
} else {
    # SEC-IDGOV-G-001: the gate SCRIPT itself cannot be found. Same dedicated
    # override as the missing-python branch above; DZP_ALLOW_ISSUE_ID_OVERRIDE
    # (the genuine-violation override check_issue_ids.py implements
    # internally) intentionally does NOT gate this branch anymore.
    if ($env:DZP_ALLOW_MISSING_ISSUE_ID_GATE -eq '1') {
        [Console]::Error.WriteLine('[idgov-gate] BYPASS: DZP_ALLOW_MISSING_ISSUE_ID_GATE=1 — scripts/check_issue_ids.py not found, issue-id registry gate SKIPPED (authorized).')
    } else {
        [Console]::Error.WriteLine('[idgov-gate] COMMIT BLOCKED: scripts/check_issue_ids.py not found — mandatory issue-id registry gate cannot run.')
        [Console]::Error.WriteLine('  Fix: restore the gate or reinstall via scripts/install-git-hooks.(sh|ps1).')
        [Console]::Error.WriteLine('  Authorized exception: DZP_ALLOW_MISSING_ISSUE_ID_GATE=1 git commit ...')
        exit 1
    }
}

exit 0
