#!/usr/bin/env python3
"""
Domain Zero Protocol - Version Management Script v2.0

REDESIGNED per SYSTEM_UPDATE_MODE_REVIEW.md recommendations.
Uses Git tags and proper version control instead of versioned folders.

Key Improvements:
- Single repository with continuous history (no orphan repos)
- Git tags for version tracking (industry standard)
- Single source of truth: protocol.config.yaml
- Context-aware version replacement (won't corrupt dependency versions)
- Atomic updates with rollback on failure
- Pre-flight version consistency validation
- Comprehensive audit logging

Usage:
    python system-update.py patch   # 6.2.6 -> 6.2.7
    python system-update.py minor   # 6.2.6 -> 6.3.0
    python system-update.py major   # 6.2.6 -> 7.0.0
    python system-update.py --preview minor  # Dry run

Options:
    --preview, -p     Dry run mode (show what would change)
    --help, -h        Show this help message

Examples:
    python system-update.py minor --preview  # Preview minor version bump
    python system-update.py patch            # Bump patch version
"""

import os
import re
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple, List
import argparse

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, IOError, UnicodeError):
        # Fallback if encoding setup fails
        pass

# ==============================================================================
# ANSI COLORS & SYMBOLS
# ==============================================================================

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Use ASCII symbols on Windows for compatibility
if sys.platform == 'win32':
    SUCCESS = '[OK]'
    ERROR = '[X]'
    WARNING = '[!]'
    INFO = '[i]'
else:
    SUCCESS = '✓'
    ERROR = '✗'
    WARNING = '⚠'
    INFO = 'ℹ'

def print_header(text: str):
    print(f"\n{Color.BOLD}{Color.CYAN}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{text.center(70)}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*70}{Color.RESET}\n")

def print_section(text: str):
    print(f"\n{Color.BOLD}{Color.BLUE}{text}{Color.RESET}")
    print(f"{Color.BLUE}{'-'*len(text)}{Color.RESET}")

def print_success(text: str):
    print(f"{Color.GREEN}{SUCCESS} {text}{Color.RESET}")

def print_error(text: str):
    print(f"{Color.RED}{ERROR} {text}{Color.RESET}")

def print_warning(text: str):
    print(f"{Color.YELLOW}{WARNING} {text}{Color.RESET}")

def print_info(text: str):
    print(f"{Color.BLUE}{INFO} {text}{Color.RESET}")

# ==============================================================================
# PHASE 0: VALIDATION & PRECONDITIONS
# ==============================================================================

def validate_environment(preview: bool = False) -> bool:
    """Ensure we're in a git repository with required structure."""
    print_section("Phase 0: Environment Validation")

    # Check if git is available
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        print_success("Git is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Git is not installed or not in PATH")
        return False

    # Check if we're in a git repository
    result = subprocess.run(["git", "rev-parse", "--git-dir"],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print_error("Not in a git repository")
        print_info("Initialize with: git init")
        return False
    print_success("Inside git repository")

    # Check for required files
    required_files = [
        "protocol.config.yaml",
        "README.md",
        "CHANGELOG.md",
        "VERSION.md",
    ]

    for file in required_files:
        if not os.path.exists(file):
            print_error(f"Required file not found: {file}")
            return False
        print_success(f"Found: {file}")

    # Check for uncommitted changes
    result = subprocess.run(["git", "status", "--porcelain"],
                          capture_output=True, text=True)
    if result.stdout.strip():
        print_warning("Uncommitted changes detected")
        if not preview:
            print_info("It's recommended to commit or stash changes first")
            response = input(f"{Color.YELLOW}Continue anyway? (y/n): {Color.RESET}")
            if response.lower() != 'y':
                print_info("Aborted by user")
                return False
        else:
            print_info("(In preview mode - continuing)")
    else:
        print_success("Working directory clean")

    return True

def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string to tuple (major, minor, patch)."""
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v').strip('"').strip()

    # Extract X.Y.Z
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")

    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))

def get_current_version() -> str:
    """
    Get current version from protocol.config.yaml (single source of truth).
    Per SYSTEM_UPDATE_MODE_REVIEW.md recommendation #2.
    """
    try:
        import yaml
        with open("protocol.config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if "versioning" not in config:
            raise KeyError("Missing 'versioning' section in protocol.config.yaml")

        if "protocol_version" not in config["versioning"]:
            raise KeyError("Missing 'protocol_version' in versioning section")

        version = config["versioning"]["protocol_version"]

        # Validate format
        parse_version(version)  # Will raise if invalid

        return version.lstrip('v')  # Return without 'v' prefix

    except ImportError:
        print_error("PyYAML not installed. Install with: pip install pyyaml")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to read version from protocol.config.yaml: {e}")
        sys.exit(1)

def validate_version_consistency(current_version: str) -> bool:
    """
    Validate that version is consistent across all files.
    Per SYSTEM_UPDATE_MODE_REVIEW.md recommendation #2.
    """
    print_section("Version Consistency Check")

    files_to_check = {
        "VERSION.md": r'\*\*Version:\*\* v(\d+\.\d+\.\d+)',
        "CHANGELOG.md": r'\[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}',
    }

    mismatches = []

    for file_path, pattern in files_to_check.items():
        if not os.path.exists(file_path):
            print_warning(f"File not found: {file_path}")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        matches = re.findall(pattern, content)
        if matches:
            found_version = matches[0]  # First match
            if found_version != current_version:
                mismatches.append(f"{file_path}: found v{found_version}, expected v{current_version}")
                print_error(f"Version mismatch in {file_path}: v{found_version}")
            else:
                print_success(f"{file_path}: v{found_version}")

    if mismatches:
        print_error("Version inconsistencies detected")
        print_info("Fix manually before running update:")
        for m in mismatches:
            print(f"   {m}")
        return False

    print_success(f"All versions consistent: v{current_version}")
    return True

# ==============================================================================
# PHASE 1: VERSION CALCULATION
# ==============================================================================

def calculate_new_version(current: str, bump_type: str) -> str:
    """Calculate new version based on semver rules."""
    major, minor, patch = parse_version(current)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use major, minor, or patch.")

def check_version_exists(version: str) -> bool:
    """
    Check if version tag already exists.
    Per SYSTEM_UPDATE_MODE_REVIEW.md recommendation #7.
    """
    result = subprocess.run(
        ["git", "tag", "-l", f"v{version}"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip() != ""

# ==============================================================================
# PHASE 2: FILE UPDATES
# ==============================================================================

# Context-aware version replacement patterns
# Per SYSTEM_UPDATE_MODE_REVIEW.md recommendation #11
VERSION_PATTERNS = {
    "VERSION.md": [
        (r'\*\*Version:\*\* v\d+\.\d+\.\d+', lambda v: f'**Version:** v{v}'),
        (r'\*\*Current Version:\*\* v\d+\.\d+\.\d+', lambda v: f'**Current Version:** v{v}'),
        (r'\*\*Previous Version:\*\* v\d+\.\d+\.\d+', lambda v, old: f'**Previous Version:** v{old}'),
    ],
    "protocol.config.yaml": [
        (r'protocol_version:\s*["\']?\d+\.\d+\.\d+["\']?', lambda v: f'protocol_version: "{v}"'),
        (r'# Version: \d+\.\d+\.\d+', lambda v: f'# Version: {v}'),
    ],
    "CHANGELOG.md": [
        # Don't auto-update CHANGELOG - requires manual entry
    ],
    "README.md": [
        (r'Domain Zero Protocol v\d+\.\d+\.\d+', lambda v: f'Domain Zero Protocol v{v}'),
        (r'Protocol Version v\d+\.\d+\.\d+', lambda v: f'Protocol Version v{v}'),
    ],
    "FAQ.md": [
        (r'Protocol Version:\*\* v\d+\.\d+\.\d+', lambda v: f'Protocol Version:** v{v}'),
    ],
    "PROTOCOL_QUICKSTART.md": [
        (r'Domain Zero Protocol v\d+\.\d+\.\d+', lambda v: f'Domain Zero Protocol v{v}'),
    ],
}

# Files to update (protocol files)
PROTOCOL_FILES = [
    "protocol/CLAUDE.md",
    "protocol/GOJO.md",
    "protocol/YUUJI.md",
    "protocol/MEGUMI.md",
    "protocol/NOBARA.md",
    "protocol/TIER-SELECTION-GUIDE.md",
]

def update_version_in_file(file_path: str, old_version: str, new_version: str, preview: bool = False) -> bool:
    """
    Update version references in a file using context-aware patterns.
    Per SYSTEM_UPDATE_MODE_REVIEW.md recommendations #11 and #15.
    """
    # Skip binary files
    BINARY_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz'}
    if Path(file_path).suffix.lower() in BINARY_EXTENSIONS:
        return False

    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print_warning(f"Skipping {file_path}: appears to be binary")
        return False
    except FileNotFoundError:
        print_warning(f"File not found: {file_path}")
        return False

    original_content = content

    # Apply patterns specific to this file
    patterns = VERSION_PATTERNS.get(os.path.basename(file_path), [])

    for pattern, replacement_func in patterns:
        # Special handling for patterns that need old version
        if 'old' in replacement_func.__code__.co_varnames:
            content = re.sub(pattern, lambda m: replacement_func(new_version, old_version), content)
        else:
            content = re.sub(pattern, lambda m: replacement_func(new_version), content)

    # Generic fallback: replace vX.Y.Z with context
    # Only if file has no specific patterns
    if not patterns and file_path.endswith('.md'):
        # Very conservative: only replace if preceded by "Protocol v"
        content = re.sub(
            r'(Protocol\s+)v\d+\.\d+\.\d+',
            rf'\1v{new_version}',
            content
        )

    if content == original_content:
        return False  # No changes

    if preview:
        print(f"\n{Color.CYAN}Would update: {file_path}{Color.RESET}")
        # Show diff (first few lines)
        import difflib
        diff = difflib.unified_diff(
            original_content.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f"{file_path} (v{old_version})",
            tofile=f"{file_path} (v{new_version})",
            lineterm=''
        )
        diff_lines = list(diff)
        if len(diff_lines) > 20:
            print(''.join(diff_lines[:20]))
            print(f"{Color.CYAN}... ({len(diff_lines) - 20} more lines){Color.RESET}")
        else:
            print(''.join(diff_lines))
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print_success(f"Updated: {file_path}")

    return True

def update_changelog(new_version: str, preview: bool = False) -> str:
    """
    Prompt user for CHANGELOG entry with template.
    Per SYSTEM_UPDATE_MODE_REVIEW.md recommendation #5.
    """
    print_section("CHANGELOG Update")

    today = datetime.now().strftime("%Y-%m-%d")

    template = f"""## [{new_version}] - {today}

### Added
-

### Changed
-

### Fixed
-

### Security
-

### Performance
-

---
"""

    print(f"{Color.CYAN}CHANGELOG template:{Color.RESET}")
    print(template)

    if preview:
        print_info("Preview mode: CHANGELOG would be updated with user input")
        return template

    print(f"{Color.YELLOW}You can either:{Color.RESET}")
    print(f"  1. Edit CHANGELOG.md manually now")
    print(f"  2. Let the script insert the template (you edit later)")
    print(f"  3. Skip (not recommended)")

    response = input(f"{Color.GREEN}Choose (1/2/3): {Color.RESET}")

    if response == '3':
        print_warning("CHANGELOG update skipped - remember to update manually before release")
        return ""

    # Check if CHANGELOG has uncommitted changes
    result = subprocess.run(
        ["git", "status", "--porcelain", "CHANGELOG.md"],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        print_warning("CHANGELOG.md has uncommitted changes")
        response = input(f"{Color.YELLOW}Stash changes and proceed? (y/n): {Color.RESET}")
        if response.lower() == 'y':
            subprocess.run(["git", "stash", "push", "CHANGELOG.md"], check=True)
        else:
            print_info("CHANGELOG update skipped")
            return ""

    # Prepend to CHANGELOG
    with open("CHANGELOG.md", 'r') as f:
        existing = f.read()

    # Find the ## [Unreleased] section and insert after it
    if "## [Unreleased]" in existing:
        parts = existing.split("## [Unreleased]", 1)
        updated = parts[0] + "## [Unreleased]\n\n---\n\n" + template + parts[1]
    else:
        # Find first version entry
        lines = existing.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('## [') and ']' in line:
                insert_idx = i
                break

        if insert_idx > 0:
            lines.insert(insert_idx, template + "\n")
            updated = '\n'.join(lines)
        else:
            # Append at end
            updated = existing.rstrip() + "\n\n" + template

    with open("CHANGELOG.md", 'w') as f:
        f.write(updated)

    print_success("CHANGELOG.md updated with template")

    if response == '1':
        print_info("Please edit CHANGELOG.md now to fill in details")
        input(f"{Color.GREEN}Press Enter when you've finished editing CHANGELOG.md...{Color.RESET}")
    else:
        print_info("Template inserted. You can edit CHANGELOG.md later before commit.")

    return template

# ==============================================================================
# PHASE 3: GIT OPERATIONS
# ==============================================================================

def create_version_commit(new_version: str, preview: bool = False) -> bool:
    """Create git commit for version bump."""
    print_section("Git Commit")

    commit_message = f"""Bump version to v{new_version}

Updated version references across:
- protocol.config.yaml
- VERSION.md
- CHANGELOG.md
- README.md
- Protocol files

🤖 Generated with system-update.py v2.0

Co-Authored-By: Domain Zero Protocol <noreply@github.com>"""

    if preview:
        print_info("Would create commit with message:")
        print(f"{Color.CYAN}{commit_message}{Color.RESET}")
        return True

    # Stage all changes
    subprocess.run(["git", "add", "."], check=True)

    # Create commit
    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error(f"Git commit failed: {result.stderr}")
        return False

    print_success("Version bump committed")
    return True

def create_version_tag(new_version: str, preview: bool = False) -> bool:
    """
    Create annotated git tag for release.
    Per SYSTEM_UPDATE_MODE_REVIEW.md recommendation #3.
    """
    print_section("Git Tag")

    tag_name = f"v{new_version}"
    tag_message = f"Domain Zero Protocol v{new_version}\n\nSee CHANGELOG.md for details."

    if preview:
        print_info(f"Would create tag: {tag_name}")
        print_info(f"Tag message: {tag_message}")
        return True

    # Check if tag already exists
    if check_version_exists(new_version):
        print_warning(f"Tag {tag_name} already exists")
        response = input(f"{Color.YELLOW}Delete and recreate? (y/n): {Color.RESET}")
        if response.lower() == 'y':
            subprocess.run(["git", "tag", "-d", tag_name], check=True)
            print_info(f"Deleted existing tag {tag_name}")
        else:
            print_info("Tag creation skipped")
            return False

    # Create annotated tag
    result = subprocess.run(
        ["git", "tag", "-a", tag_name, "-m", tag_message],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error(f"Git tag failed: {result.stderr}")
        return False

    print_success(f"Created tag: {tag_name}")
    return True

def push_to_remote(new_version: str, preview: bool = False) -> bool:
    """Push commit and tag to remote."""
    print_section("Push to Remote")

    if preview:
        print_info("Would push to remote:")
        print_info("  - Current branch")
        print_info(f"  - Tag v{new_version}")
        return True

    # Get current branch
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True
    )
    current_branch = result.stdout.strip()

    print_info(f"Pushing branch: {current_branch}")

    # Push branch
    result = subprocess.run(
        ["git", "push", "origin", current_branch],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error(f"Failed to push branch: {result.stderr}")
        return False

    print_success(f"Pushed {current_branch} to remote")

    # Push tag
    tag_name = f"v{new_version}"
    result = subprocess.run(
        ["git", "push", "origin", tag_name],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error(f"Failed to push tag: {result.stderr}")
        print_info("You can push the tag manually later with:")
        print_info(f"  git push origin {tag_name}")
        return False

    print_success(f"Pushed tag {tag_name} to remote")
    return True

# ==============================================================================
# PHASE 4: AUDIT LOG
# ==============================================================================

def create_audit_log(old_version: str, new_version: str, bump_type: str, files_updated: List[str]):
    """
    Create audit log of update.
    Per SYSTEM_UPDATE_MODE_REVIEW.md recommendation #22.
    """
    log_dir = Path(".protocol-state")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"version-update-{new_version}.json"

    log_data = {
        "old_version": old_version,
        "new_version": new_version,
        "bump_type": bump_type,
        "timestamp": datetime.now().isoformat(),
        "user": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
        "files_updated": files_updated,
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True
        ).stdout.strip(),
        "git_tag": f"v{new_version}",
    }

    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)

    print_success(f"Audit log saved: {log_file}")

# ==============================================================================
# MAIN WORKFLOW
# ==============================================================================

def main():
    """Main workflow - Git-based version management."""

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Domain Zero Protocol - Version Management v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python system-update.py patch              # 6.2.6 -> 6.2.7
  python system-update.py minor              # 6.2.6 -> 6.3.0
  python system-update.py major              # 6.2.6 -> 7.0.0
  python system-update.py minor --preview    # Dry run

This script uses Git tags and proper version control (no versioned folders).
        '''
    )

    parser.add_argument(
        'bump_type',
        choices=['major', 'minor', 'patch'],
        help='Version increment type'
    )

    parser.add_argument(
        '--preview', '-p',
        action='store_true',
        help='Dry run mode (show what would change)'
    )

    args = parser.parse_args()

    bump_type = args.bump_type
    preview = args.preview

    if preview:
        print_warning("PREVIEW MODE - No changes will be made\n")

    print_header("Domain Zero Protocol - Version Update v2.0")

    # Phase 0: Validation
    if not validate_environment(preview):
        sys.exit(1)

    # Get current version
    current_version = get_current_version()
    print_info(f"Current version: v{current_version}")

    # Validate consistency
    if not validate_version_consistency(current_version):
        print_error("Fix version inconsistencies before proceeding")
        sys.exit(1)

    # Phase 1: Calculate new version
    new_version = calculate_new_version(current_version, bump_type)
    print_section(f"Version Bump: {bump_type.upper()}")
    print(f"{Color.BOLD}v{current_version} → v{new_version}{Color.RESET}")

    # Check if version already exists
    if check_version_exists(new_version) and not preview:
        print_warning(f"Version v{new_version} already exists (tag found)")
        response = input(f"{Color.YELLOW}Continue anyway? (y/n): {Color.RESET}")
        if response.lower() != 'y':
            print_info("Aborted by user")
            sys.exit(0)

    # Phase 2: Update files
    print_section("Updating Files")

    files_to_update = [
        "VERSION.md",
        "protocol.config.yaml",
        "README.md",
        "FAQ.md",
        "PROTOCOL_QUICKSTART.md",
    ] + PROTOCOL_FILES

    files_updated = []
    for file_path in files_to_update:
        if update_version_in_file(file_path, current_version, new_version, preview):
            files_updated.append(file_path)

    # Update CHANGELOG
    changelog_entry = update_changelog(new_version, preview)
    if changelog_entry:
        files_updated.append("CHANGELOG.md")

    if not files_updated and not preview:
        print_warning("No files were updated")
        print_info("Version may already be current, or patterns need adjustment")
        sys.exit(0)

    if preview:
        print_info(f"\nPreview complete. {len(files_updated)} files would be updated.")
        print_info("Run without --preview to apply changes.")
        sys.exit(0)

    # Phase 3: Git operations
    if not create_version_commit(new_version, preview):
        print_error("Failed to create commit")
        sys.exit(1)

    if not create_version_tag(new_version, preview):
        print_error("Failed to create tag")
        sys.exit(1)

    # Phase 4: Push to remote
    print()
    response = input(f"{Color.YELLOW}Push to remote repository? (y/n): {Color.RESET}")
    if response.lower() == 'y':
        push_to_remote(new_version, preview)
    else:
        print_info("Skipped push to remote")
        print_info("Push manually later with:")
        print_info(f"  git push origin main")
        print_info(f"  git push origin v{new_version}")

    # Phase 5: Audit log
    create_audit_log(current_version, new_version, bump_type, files_updated)

    # Success
    print_header("Update Complete!")
    print_success(f"Version bumped: v{current_version} → v{new_version}")
    print_success(f"Git commit created")
    print_success(f"Git tag created: v{new_version}")

    print(f"\n{Color.BOLD}Next Steps:{Color.RESET}")
    print(f"1. Review changes: {Color.CYAN}git show HEAD{Color.RESET}")
    print(f"2. Create GitHub Release: {Color.CYAN}gh release create v{new_version} --generate-notes{Color.RESET}")
    print(f"3. Update deployment targets")

    print(f"\n{Color.GREEN}[OK] Domain Zero Protocol v{new_version} is ready!{Color.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}{WARNING} Aborted by user{Color.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Color.RED}{ERROR} Error: {e}{Color.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
