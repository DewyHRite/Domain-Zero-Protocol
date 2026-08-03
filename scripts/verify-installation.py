#!/usr/bin/env python3
"""
Domain Zero Protocol - Installation Verification
Verifies complete file structure and identifies missing components

SEC-P1-FILEINTEG-9.11.0: also wires in the SHA-256 file-integrity check
(.protocol-state/security/file_integrity.py, PATCH-SEC-002) -- the only file
under .protocol-state/security/ that ships to consumers. This is the real
caller that gate/wiring was missing before this fix; see
verify_file_integrity_gate() below and the --init-integrity CLI flag.
"""

from pathlib import Path
import sys

# Complete file manifest
REQUIRED_FILES = {
    # Root files
    'AI_INSTRUCTIONS.md': 'Root',
    'CLAUDE.md': 'Root',
    'CHANGELOG.md': 'Root',
    'LICENSE': 'Root',
    'protocol.config.yaml': 'Root',
    'PROTOCOL_QUICKSTART.md': 'Root',
    'README.md': 'Root',
    'SECURITY.md': 'Root',
    'VERSION.md': 'Root',

    # Protocol agents
    'protocol/gojo.agent.md': 'Agent',
    'protocol/yuuji.agent.md': 'Agent',
    'protocol/megumi.agent.md': 'Agent',
    'protocol/nobara.agent.md': 'Agent',
    'protocol/todo.agent.md': 'Agent',
    'protocol/maki.agent.md': 'Agent',
    'protocol/panda.agent.md': 'Agent',
    'protocol/inumaki.agent.md': 'Agent',
    'protocol/sukuna.agent.md': 'Agent',
    'protocol/toji.agent.md': 'Agent',

    # Protocol main
    'protocol/CLAUDE.md': 'Protocol',

    # Protocol reference
    'protocol/AGENT_SELF_IDENTIFICATION_STANDARD.md': 'Reference',
    'protocol/CANONICAL_SOURCE_ADOPTION.md': 'Reference',
    'protocol/EMERGENCY_STOP_STANDARD.md': 'Reference',
    'protocol/ENVIRONMENT_TARGETING.md': 'Reference',
    'protocol/HANDOFF_SPECIFICATION.md': 'Reference',
    'protocol/MASK_MODE.md': 'Reference',
    'protocol/MCP_INTEGRATION.md': 'Reference',
    'protocol/MODE_INDICATORS.md': 'Reference',
    'protocol/RESEARCH_MODE.md': 'Reference',
    'protocol/TECHNICAL_LEVEL_ADAPTATION.md': 'Reference',
    'protocol/TIER-SELECTION-GUIDE.md': 'Reference',

    # Protocol modules
    'protocol/modules/BINDING_OATH.md': 'Module',
    'protocol/modules/EMERGENCY_STOP_PROTOCOL.md': 'Module',
    'protocol/modules/ESCAPE_PATH_PROTOCOL.md': 'Module',
    'protocol/modules/MASK_MODE_BEHAVIOR.md': 'Module',
    'protocol/modules/MISSION_CONTROL_ISOLATION.md': 'Module',
    'protocol/modules/SAFETY_FIRST.md': 'Module',
    'protocol/modules/USER_LEVEL_ADAPTATION.md': 'Module',

    # Gojo procedures
    'protocol/gojo-procedures/OPERATIONAL_PROCEDURES.md': 'Procedures',

    # Skills
    'protocol/skills/AGENT_SKILLS_MAP.yaml': 'Skills',
    'protocol/skills/SKILL_REGISTRY.md': 'Skills',
    'protocol/skills/skill-builder.md': 'Skills',

    # Documentation
    'docs/FAQ.md': 'Docs',
    'docs/SYSTEM_UPDATE_IMPLEMENTATION_GUIDE.md': 'Docs',
    'docs/TOKEN_EFFICIENCY_RECOMMENDATIONS.md': 'Docs',

    # Docs - Guides
    'docs/guides/AGENT_BINDING_OATH.md': 'Guides',
    'docs/guides/CREATING_CLAUDE_AGENTS.md': 'Guides',
    'docs/guides/DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md': 'Guides',
    'docs/guides/EMERGENCY_STOP_GUIDE.md': 'Guides',
    'docs/guides/TIER_TRANSITION_GUIDE.md': 'Guides',
    'docs/guides/USER_LEVEL_GUIDE.md': 'Guides',

    # Docs - Installation
    'docs/installation/IMPLEMENTATION_GUIDE.md': 'Installation',
    'docs/installation/SLASH_COMMANDS_INSTALLATION.md': 'Installation',

    # Docs - Reference
    'docs/reference/AUTHORIZATION_PROTOCOL.md': 'Reference',
    'docs/reference/DOMAIN_ZERO_RESEARCH_AND_SKILLS_GUIDE.md': 'Reference',
    'docs/reference/INSTRUCTION_CONFIRMATION_PROTOCOL.md': 'Reference',
    'docs/reference/MIGRATION_GUIDE_TEMPLATE.md': 'Reference',
    'docs/reference/playwright.md': 'Reference',
    'docs/reference/REALITY_CHECK.md': 'Reference',

    # Docs - Templates
    'docs/templates/DECISION_REASONING_TEMPLATE.md': 'Templates',

    # State files
    '.protocol-state/custom-agent-registry.example.json': 'State',
    '.protocol-state/custom_agent_monitor.py': 'State',
    '.protocol-state/dev-notes.md': 'State',
    '.protocol-state/dev-notes.template.md': 'State',
    '.protocol-state/security-review.md': 'State',
    '.protocol-state/session_monitor.py': 'State',
    '.protocol-state/session-state.example.json': 'State',
    '.protocol-state/work-session-alert.template.md': 'State',

    # State files (PATCH-STATE-001 modules - v8.12.0)
    '.protocol-state/project_state_manager.py': 'State',
    '.protocol-state/migrate_state_consolidation.py': 'State',
    '.protocol-state/migrate_state_9x.py': 'State',
    '.protocol-state/troubleshooting_tracker.py': 'State',
    '.protocol-state/session-state.template.json': 'State',
    '.protocol-state/troubleshooting-history.template.json': 'State',
    '.protocol-state/validation-state.template.json': 'State',

    # Security control modules (v9.11.0)
    # SEC-INSTALL-PENDING-B: file_integrity.py is the ONE .protocol-state/security/
    # module that ships to consumers (proven end-to-end by
    # tests/distro/test_security_module_shipping.py), so a genuine install always
    # has it. Declaring it REQUIRED means its absence is reported by the
    # file-presence check INDEPENDENTLY of the integrity gate -- previously,
    # deleting this single file disabled the integrity control with no signal from
    # any part of this script. Its three siblings are dev-only and deliberately
    # NOT listed here.
    '.protocol-state/security/file_integrity.py': 'Security',

    # JJK Character Reference
    '.protocol-state/jjk-character-reference/ryomen-sukuna.md': 'JJK',
    '.protocol-state/jjk-character-reference/satoru-gojo.md': 'JJK',

    # Scripts
    'scripts/verify-protocol.ps1': 'Scripts',
    'scripts/verify-protocol.sh': 'Scripts',

    # Dev/tooling requirements (BUG-VALIDATE-002, v9.3.0)
    'requirements-dev.txt': 'Root',

    # Domain Record System (v8.8.0+)
    '.dzp-domain/domain.record.md': 'Domain Record',
    '.dzp-domain/domain.record.template.md': 'Domain Record',
    '.dzp-domain/.rotation-metadata.json': 'Domain Record',
}

# Optional files (won't fail if missing)
OPTIONAL_FILES = {
    'PASSIVE_OBSERVER.md': 'Root (optional - Gojo passive observation guide)',
    '.protocol-state/project-state.json': 'State (created on first use)',
    '.protocol-state/session-state.json': 'State (created by session_monitor.py)',
    '.protocol-state/authorization/session-state.json': 'Auth (created on first use)',

    # BUG-VERIFY-001 (v9.3.0): DEV-ONLY files intentionally EXCLUDED from the
    # published distributable (see scripts/distro/publish-manifest.yaml: the whole
    # `.protocol-state/system-update-framework` tree is excluded, and
    # DZP_DZA_INSTALLATION_REVIEW.md is excluded as a private case study). They
    # exist in the development tree but a fresh canonical install must NOT fail for
    # their absence - so they are optional, not required.
    'docs/DZP_DZA_INSTALLATION_REVIEW.md': 'Dev-only (excluded from distro)',
    # WP1 commit-b2 (v9.11.0): describes installing dzp_server.py, which does
    # not exist anywhere in this codebase (see the doc's own new non-existence
    # banner). Excluded from the manifest so consumers are never shipped an
    # install guide for a nonexistent server -- see
    # tests/distro/test_manifest_doc_exclusions.py for the mechanical pin.
    'docs/installation/MCP_SERVER_SETUP.md': 'Dev-only (excluded from distro; describes a nonexistent server)',
    '.protocol-state/WORK_SESSION_STATUS.md': 'Dev-only (excluded from distro)',
    '.protocol-state/gojo-session-monitoring-guide.md': 'Dev-only (excluded from distro)',
    '.protocol-state/system-update-framework/backup-manifest.template.json': 'Dev-only SUF (excluded from distro)',
    '.protocol-state/system-update-framework/file-classifications.template.json': 'Dev-only SUF (excluded from distro)',
    '.protocol-state/system-update-framework/plan-documentation.md': 'Dev-only SUF (excluded from distro)',
    '.protocol-state/system-update-framework/plan-documentation.template.md': 'Dev-only SUF (excluded from distro)',
    '.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.md': 'Dev-only SUF (excluded from distro)',
    '.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.template.md': 'Dev-only SUF (excluded from distro)',
    '.protocol-state/system-update-framework/version-registry.template.json': 'Dev-only SUF (excluded from distro)',
}

def verify_installation():
    """Verify complete DZP installation"""

    missing_files = []
    present_files = []

    print("=" * 70)
    print("DOMAIN ZERO PROTOCOL - INSTALLATION VERIFICATION")
    print("=" * 70)
    print()

    # Check required files
    for file_path, category in REQUIRED_FILES.items():
        path = Path(file_path)
        if path.exists():
            present_files.append((file_path, category))
        else:
            missing_files.append((file_path, category))

    # Report results
    total = len(REQUIRED_FILES)
    present_count = len(present_files)
    missing_count = len(missing_files)

    print(f"RESULTS: {present_count}/{total} files present")
    print()

    if missing_count == 0:
        print("[OK] INSTALLATION COMPLETE - All required files present")
        print()
        print("Next steps:")
        print("1. Run: python scripts/sync-templates.py")
        print("2. Read: ./CLAUDE.md")
        return 0

    else:
        print(f"[FAIL] INSTALLATION INCOMPLETE - {missing_count} files missing")
        print()
        print("MISSING FILES:")
        print()

        # Group by category
        by_category = {}
        for file_path, category in missing_files:
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(file_path)

        for category, files in sorted(by_category.items()):
            print(f"  {category} ({len(files)} missing):")
            for file_path in sorted(files):
                print(f"    [MISSING] {file_path}")
            print()

        print("RECOVERY STEPS:")
        print("1. Identify source: core-files-vX.Y.Z/ directory")
        print("2. Copy missing files from source to current directory")
        print("3. Re-run this verification script")
        print("4. See Section 9 in AI_INSTRUCTIONS.md for detailed recovery")
        print()

        return 1

def _load_file_integrity_module():
    """Dynamically load .protocol-state/security/file_integrity.py by file path.

    Cannot use a normal `import` statement: the containing directories
    (".protocol-state") are not valid Python package identifiers. Returns None
    if the module (or its containing repo layout) is not present, so this
    script degrades gracefully rather than crashing when run somewhere the
    file happens not to exist.
    """
    import importlib.util

    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / '.protocol-state' / 'security' / 'file_integrity.py'
    if not src.exists():
        return None

    spec = importlib.util.spec_from_file_location('dzp_file_integrity', src)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verify_file_integrity_gate(init_if_missing: bool = False, require_baseline: bool = False) -> int:
    """Run the SHA-256 file-integrity check (PATCH-SEC-002) as part of
    installation verification.

    SEC-P1-FILEINTEG-9.11.0: this is the file-integrity control's ONE real
    caller in the shipped consumer surface (previously it had ZERO callers
    anywhere -- shipping it unwired would have reproduced the exact
    dead-control problem this fix exists to close).

    Args:
        init_if_missing: if True, and no baseline exists yet, create one now
            (the explicit `--init-integrity` action -- see module docstring in
            file_integrity.py for why this must be a deliberate, human-invoked
            call site rather than an ambient environment-variable bypass).
        require_baseline: if True, a MISSING baseline is treated as a failure
            (exit 1) instead of an informational notice. Default False so the
            ordinary post-install verification flow does not hard-fail on a
            fresh install that has not yet run --init-integrity (missing
            baseline is expected there, not an error).

    Returns:
        0 on pass (or informational "no baseline yet" in non-strict mode),
        1 on failure (tampering detected, corrupted baseline, or a missing
        baseline in --require-integrity mode).
    """
    mod = _load_file_integrity_module()
    if mod is None:
        msg = ".protocol-state/security/file_integrity.py not found"
        # SEC-INSTALL-PENDING-B: the degradation is now gated on STRICTNESS.
        # Previously this returned 0 unconditionally -- BEFORE require_baseline
        # was ever consulted -- so --require-integrity reported SUCCESS when the
        # control module itself was absent. That is strictly worse than the
        # missing-baseline state that same flag exists to catch, and deleting one
        # file is a cheaper bypass than tampering with the (unsigned) baseline.
        # The fail-open was additionally pinned as intended by a passing test.
        #
        # Graceful degradation is retained ONLY for the default path, and that is
        # a deliberate, reviewed decision rather than an oversight: this script is
        # a general installation checker that must stay useful against a partial
        # or non-standard tree. Strict mode is the contract for automation, and
        # strict mode now fails closed.
        #
        # SEC-INSTALL-002: init_if_missing is likewise NOT a degradable mode.
        # `--init-integrity` is an explicit, human-invoked ACTION whose entire
        # purpose is to CREATE the baseline. Previously it left require_baseline
        # at its default, so the strictness gate above did not apply and the
        # operator got a [WARN] and EXIT 0 for a creation that never happened --
        # then proceeded, and any CI that shelled out to it proceeded, believing
        # a trusted baseline now existed. There is no degraded form of "create
        # the baseline"; either it was created or the command failed.
        if require_baseline or init_if_missing:
            reason = (
                "--require-integrity (strict) mode"
                if require_baseline
                else "--init-integrity, which exists to CREATE that baseline"
            )
            print(f"[FAIL] {msg} -- the integrity control is ABSENT.")
            print(f"       Refusing to report success in {reason}:")
            if require_baseline:
                print("       a missing control cannot have verified anything.")
            else:
                print("       no baseline was created and none can be.")
            return 1
        print(f"[WARN] {msg} -- skipping integrity check")
        return 0

    baseline_path = Path(mod.INTEGRITY_FILE)

    if not baseline_path.exists():
        if init_if_missing:
            print("[INFO] No integrity baseline found -- creating one now.")
            print("[INFO] This establishes the files CURRENTLY ON DISK as the trusted baseline.")
            print("[INFO] Run this immediately after install/update, before making any manual")
            print("[INFO] edits, so the baseline reflects a known-good state.")
            # SEC-INSTALL-002 (folded item): initialize_integrity_baseline()
            # raises RuntimeError when it REFUSES to manufacture an empty or
            # under-covering baseline (SEC-FILEINTEG-PENDING-A). Unwrapped, that
            # surfaced as an uncaught traceback. Exit status was still non-zero,
            # so it still failed closed -- but it threw away the carefully
            # written diagnostic that tells the operator what to do next.
            try:
                mod.initialize_integrity_baseline()
            except RuntimeError as e:
                print(f"[FAIL] Could not create the integrity baseline: {e}")
                return 1
            print(f"[OK] Integrity baseline created at {mod.INTEGRITY_FILE}")
            return 0

        if require_baseline:
            print("[FAIL] No integrity baseline found.")
            print("       Run: python scripts/verify-installation.py --init-integrity")
            return 1

        print("[INFO] No file-integrity baseline established yet (optional hardening).")
        print("       To establish one: python scripts/verify-installation.py --init-integrity")
        return 0

    try:
        violations = mod.verify_file_integrity()
    except RuntimeError as e:
        print(f"[FAIL] Integrity verification error: {e}")
        return 1

    if violations:
        print(f"[FAIL] INTEGRITY VIOLATIONS DETECTED ({len(violations)}):")
        for filepath, reason in sorted(violations.items()):
            print(f"    [TAMPERED] {filepath}: {reason}")
        print()
        print("These files differ from the trusted baseline. This may indicate")
        print("unauthorized modification. If this is an authorized change, update the")
        print("baseline via file_integrity.update_integrity_baseline() (USER/GOJO/SYSTEM only).")
        return 1

    # SEC-FILEINTEG-PENDING-A: report the count ACTUALLY verified, never
    # len(PROTECTED_FILES). The old line printed the number of files the control
    # INTENDED to check, so a baseline declaring zero hashes produced the literal
    # output "File integrity verified: 16 protected files checked, 0 violations"
    # having opened none of them. load_baseline() is fail-closed (it now rejects
    # an empty/under-covering baseline outright), but the count is still derived
    # from the real baseline so the attestation cannot over-report even if the
    # protected set and the baseline legitimately diverge in future.
    try:
        checked = len(mod.load_baseline())
    except (RuntimeError, AttributeError) as e:
        print(f"[FAIL] Integrity verification error while counting verified files: {e}")
        return 1

    print(f"[OK] File integrity verified: {checked} files checked against the baseline, 0 violations")
    return 0


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Domain Zero Protocol installation verification'
    )
    parser.add_argument(
        '--init-integrity', action='store_true',
        help='Create the initial SHA-256 file-integrity baseline (PATCH-SEC-002) and exit. '
             'Run this once, immediately after install/update, before making manual edits.'
    )
    parser.add_argument(
        '--skip-integrity', action='store_true',
        help='Skip the file-integrity check; only run the file-presence check.'
    )
    parser.add_argument(
        '--require-integrity', action='store_true',
        help='Treat a MISSING file-integrity baseline as a failure (strict/CI mode) '
             'instead of an informational notice.'
    )
    args = parser.parse_args()

    if args.init_integrity:
        sys.exit(verify_file_integrity_gate(init_if_missing=True))

    exit_code = verify_installation()

    if not args.skip_integrity:
        integrity_exit_code = verify_file_integrity_gate(require_baseline=args.require_integrity)
        if integrity_exit_code != 0:
            exit_code = integrity_exit_code

    sys.exit(exit_code)
