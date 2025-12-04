#!/usr/bin/env python3
"""
Domain Zero Protocol - Installation Verification
Verifies complete file structure and identifies missing components
"""

from pathlib import Path
import sys

# Complete file manifest
REQUIRED_FILES = {
    # Root files
    'AI_INSTRUCTIONS.md': 'Root',
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
    'docs/DZP_DZA_INSTALLATION_REVIEW.md': 'Docs',
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
    'docs/installation/MCP_SERVER_SETUP.md': 'Installation',
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
    '.protocol-state/gojo-session-monitoring-guide.md': 'State',
    '.protocol-state/session_monitor.py': 'State',
    '.protocol-state/session-state.example.json': 'State',
    '.protocol-state/work-session-alert.template.md': 'State',
    '.protocol-state/WORK_SESSION_STATUS.md': 'State',

    # System Update Framework
    '.protocol-state/system-update-framework/backup-manifest.template.json': 'SUF',
    '.protocol-state/system-update-framework/file-classifications.template.json': 'SUF',
    '.protocol-state/system-update-framework/plan-documentation.md': 'SUF',
    '.protocol-state/system-update-framework/plan-documentation.template.md': 'SUF',
    '.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.md': 'SUF',
    '.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.template.md': 'SUF',
    '.protocol-state/system-update-framework/version-registry.template.json': 'SUF',

    # JJK Character Reference
    '.protocol-state/jjk-character-reference/ryomen-sukuna.md': 'JJK',
    '.protocol-state/jjk-character-reference/satoru-gojo.md': 'JJK',

    # Scripts
    'scripts/verify-protocol.ps1': 'Scripts',
    'scripts/verify-protocol.sh': 'Scripts',
}

# Optional files (won't fail if missing)
OPTIONAL_FILES = {
    'PASSIVE_OBSERVER.md': 'Root (optional - Gojo passive observation guide)',
    '.protocol-state/project-state.json': 'State (created on first use)',
    '.protocol-state/session-state.json': 'State (created by session_monitor.py)',
    '.protocol-state/authorization/session-state.json': 'Auth (created on first use)',
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
        print("2. Read: protocol/CLAUDE.md")
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

if __name__ == '__main__':
    exit_code = verify_installation()
    sys.exit(exit_code)
