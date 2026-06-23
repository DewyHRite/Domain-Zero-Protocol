#!/usr/bin/env python3
"""DZP full-repo version-stamp linter (v9.8.1+).

Scans the repository for the stamp types that must equal the current
protocol version (read from protocol.config.yaml):

  1. CORE FILE headers  <!-- [CORE FILE] - Domain Zero Protocol vX.Y.Z -->
  2. Bold footers       **Domain Zero Protocol vX.Y.Z**
  3. Frontmatter        protocol_version: "X.Y.Z"  (YAML / Markdown front matter)
  4. Git-hook inline    # Domain Zero Protocol - ... Hook (FEAT-GUARD-001, vX.Y.Z)
  5. Body headings      ## Domain Zero Protocol vX.Y.Z  (protocol/ scope only)
  6. Metadata fields    **Protocol Version**: [v]X.Y.Z  (protocol/, docs/,
                          .protocol-state/jjk-character-reference/ scope only)

Exits 0 when all discovered stamps equal the current version.
Exits 1 listing every stale stamp (file:line — found vs expected).
Exits 2 on setup error (bad root, config unreadable, no version found).

Wired into:
  - script_dependencies.yaml  pre-release + pre-publish events
  - .github/workflows/validate-protocol.yml  DZP pre-release gate step
  - dzp-publish  stamp-drift gate

Usage:
  python scripts/distro/check_version_stamps.py [--root PATH] [--verbose]
"""

import argparse
import fnmatch
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Stamp regexes
# ---------------------------------------------------------------------------
# Type 1: <!-- [CORE FILE] - Domain Zero Protocol vX.Y.Z -->
_CORE_HEADER_RX = re.compile(
    r"<!--\s*\[CORE FILE\]\s*-\s*Domain Zero Protocol\s+v(\d+\.\d+\.\d+)\s*-->",
    re.IGNORECASE,
)
# Type 2: **Domain Zero Protocol vX.Y.Z** (bold footer / inline bold branding)
_BOLD_FOOTER_RX = re.compile(
    r"\*\*Domain Zero Protocol\s+v(\d+\.\d+\.\d+)\*\*",
    re.IGNORECASE,
)
# Type 3: protocol_version: "X.Y.Z"  or  protocol_version: X.Y.Z  (col-0 YAML key)
_PROTOCOL_VER_RX = re.compile(
    r'^protocol_version:\s*"?(\d+\.\d+\.\d+)"?',
    re.MULTILINE,
)
# Type 4: Git-hook inline version comment (WI-CR-6, v9.7.2)
# Matches the header line in pre-commit / pre-commit.ps1:
#   # Domain Zero Protocol - ... Hook (FEAT-GUARD-001, vX.Y.Z)
# Scoped to lines that contain "Domain Zero Protocol" AND the (FEAT-GUARD-001, vX.Y.Z)
# parenthetical so changelog/prose references are not false-positived.
_GIT_HOOK_VER_RX = re.compile(
    r"Domain Zero Protocol\b.*?\(FEAT-GUARD-\d+,\s*v(\d+\.\d+\.\d+)\)",
    re.IGNORECASE,
)
# Type 5: Protocol-version-tracking body headings (v9.8.1+)
# Matches Markdown H2 lines of the form:
#   ## Domain Zero Protocol vX.Y.Z
# (with an optional subtitle appended after the version, separated by whitespace/dash).
# Scoped to protocol/**/*.md ONLY via _BODY_HEADING_PATH_PREFIX below — so
# feature-attribution headings in docs/, .pr-description.md, .protocol-state/ are
# NOT in scope and will never be falsely flagged.
#
# Intentional exclusions WITHIN protocol/ that carry a historical heading
# (none currently; add here if a future file needs one frozen):
_BODY_HEADING_RX = re.compile(
    r"^##\s+Domain Zero Protocol\s+v(\d+\.\d+\.\d+)",
    re.IGNORECASE,
)
# Only files whose repo-relative POSIX path starts with this prefix are subject
# to the body-heading check.  All other files are silently skipped for Type 5.
_BODY_HEADING_PATH_PREFIX = "protocol/"
# Per-file allowlist for files inside _BODY_HEADING_PATH_PREFIX that legitimately
# keep a non-current body heading (feature attributions, frozen historical docs).
# Use repo-relative POSIX paths.
_BODY_HEADING_ALLOWLIST: frozenset[str] = frozenset(
    {
        # Add entries here if a protocol/ file ever needs a frozen historical heading.
        # Example: "protocol/modules/SOME_LEGACY_MODULE.md"
    }
)

# Type 6: Markdown metadata field  **Protocol Version**: [v]X.Y.Z  (v9.8.1+)
# Matches the field in both v-prefixed and bare forms, e.g.:
#   **Protocol Version**: v9.8.1
#   **Protocol Version**: 9.8.1
# Also matches blockquote-prefixed variants:
#   > **Protocol Version**: v8.5.1
# Scoped to files whose repo-relative POSIX path starts with one of the
# _PROTOCOL_VER_FIELD_PATH_PREFIXES below — so docs that live outside those
# directories (copilot-instructions, Domain Zero Agents/, .pr-description.md,
# etc.) are silently skipped, never falsely flagged.
_PROTOCOL_VER_FIELD_RX = re.compile(
    r"^(?:>\s*)?\*\*Protocol Version\*\*:\s*v?(\d+\.\d+\.\d+)",
    re.IGNORECASE,
)
# Directory/path prefixes in scope for the Type-6 check.
_PROTOCOL_VER_FIELD_PATH_PREFIXES = (
    "protocol/",
    "docs/",
    ".protocol-state/jjk-character-reference/",
)
# Per-file allowlist for files inside the above prefixes whose **Protocol Version**
# field is a frozen historical/contextual note that must NOT be enforced/bumped.
# Use repo-relative POSIX paths.
_PROTOCOL_VER_FIELD_ALLOWLIST: frozenset[str] = frozenset(
    {
        # Transition narrative ("v6.2.8.x") written at the time of canonical-source
        # adoption; bumping it would destroy the historical context.
        "protocol/CANONICAL_SOURCE_ADOPTION.md",
        # Per-patch manifest records: each **Protocol Version** line names the
        # version the patch was introduced for — historical attribution, not a
        # current-version stamp.
        "protocol/SUKUNA-REPORT.md",
    }
)

# ---------------------------------------------------------------------------
# Exclusion rules  (mirrors the cascade rules from the v9.7.2 directive)
# ---------------------------------------------------------------------------
# Directory prefixes that are historical archives / tests / distro artifacts.
# All path comparisons use POSIX strings of paths relative to root.
_EXCLUDED_PATH_PREFIXES = (
    "core-files-v",        # core-files-v8.4.1/, core-files-v8.5.1/, ...
    "release/",            # gitignored release worktree
    "Patched/",            # gitignored patch bundles
    "internal-docs/",      # gitignored internal docs
    ".protocol-state/internal-docs/",
    ".protocol-state/backups/",
    ".protocol-state/archive/",
    ".protocol-state/system-update-framework/",  # INTERNAL: update plans + historical checklists
    "distro/",             # orphan distro worktree content
    ".git/",
    "tests/",              # test fixtures — never stamp-gated
    "docs/superpowers/plans/",   # design plans — historical
    "docs/migration/",           # migration docs — historical
)

# Specific files excluded regardless of path (historical / example content)
_EXCLUDED_FILENAMES = {
    "SUKUNA-REPORT.md",        # patch manifest with historical lines
    "SESSION_MONITOR_CLI_UPDATE_v8.8.0.md",
    "AI_INSTRUCTIONS.md",      # carries Toji component version v1.2.x — assert_version gates it
    "CHANGELOG.md",            # intentionally lists old version numbers in history entries
    # Protected append-only project documents (FEAT-GUARD-001): their first-line
    # [CORE FILE] stamp is part of the IMMUTABLE byte-prefix guarded by
    # check_protected_append_only.py. It CANNOT be cascaded without violating
    # append-only (would require DZP_ALLOW_PROTECTED_REWRITE), so the stamp is
    # intentionally frozen at its origin version and excluded from stamp linting.
    "dev-notes.md",
    "security-review.md",
    "domain.record.md",
    # The following are gitignored SYSTEM_UPDATE snapshots
}
_EXCLUDED_FILENAME_GLOBS = (
    "SYSTEM_UPDATE_*.md",      # gitignored update mode snapshots
    "RELEASE_NOTES_*.md",
    "*.bak",
    "*.bak-*",
    "*.bak*",
)

# Patterns in file content that indicate a line is an EXAMPLE / historical reference
# (not a live stamp). These lines are skipped even if they match a stamp regex.
_EXAMPLE_LINE_PATTERNS = (
    # AI_INSTRUCTIONS "# Update to new version" example
    "# Update to new version",
    # settings.json sed command examples
    "sed -i 's#",
    "Bash(sed",
    # History lines in documents that name old versions as facts
    "**Fix Applied**",
)

# ---------------------------------------------------------------------------
# Independent-version fields (NOT protocol stamps) — lines to skip
# ---------------------------------------------------------------------------
# agent_file_version, _schema_version, bare version:, component **Version**: lines
# These are identified by the patterns they match, which will NOT match our 3 stamp
# regexes anyway — but we document them here for clarity.

_INDEPENDENT_VER_LINES = re.compile(
    r"agent_file_version:|_schema_version:|^\s*version:|_version:|Version:\s*\d+\.\d+\.\d+\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _is_excluded(rel_posix: str, filename: str) -> bool:
    """Return True if this path should be excluded from stamp scanning."""
    for prefix in _EXCLUDED_PATH_PREFIXES:
        if rel_posix.startswith(prefix):
            return True
    if filename in _EXCLUDED_FILENAMES:
        return True
    # glob-style filename exclusions (use fnmatch for full glob support)
    for pat in _EXCLUDED_FILENAME_GLOBS:
        if fnmatch.fnmatch(filename, pat):
            return True
    return False


def _is_example_line(line: str) -> bool:
    """Return True if the line is an example / historical reference, not a live stamp."""
    for pat in _EXAMPLE_LINE_PATTERNS:
        if pat in line:
            return True
    return False


_CONFIG_VER_RX = re.compile(
    r'protocol_version:\s*"?(\d+\.\d+\.\d+)"?',  # indent-agnostic for the config file
)


def _get_current_version(root: Path) -> str | None:
    """Read protocol_version from protocol.config.yaml (single source of truth).

    The key may be indented (e.g. under a 'versioning:' block), so we scan
    without requiring col-0 for the config file specifically.
    """
    config = root / "protocol.config.yaml"
    if not config.exists():
        return None
    text = config.read_text(encoding="utf-8")
    m = _CONFIG_VER_RX.search(text)
    return m.group(1) if m else None


def _scan_file(
    path: Path,
    root: Path,
    current: str,
    verbose: bool,
) -> list[str]:
    """Scan a single file for stale stamps. Returns a list of violation strings."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    violations: list[str] = []
    lines = text.splitlines()
    rel = str(path.relative_to(root)).replace("\\", "/")

    for lineno, line in enumerate(lines, start=1):
        if _is_example_line(line):
            continue

        for rx, stamp_type in (
            (_CORE_HEADER_RX, "CORE-HEADER"),
            (_BOLD_FOOTER_RX, "BOLD-FOOTER"),
            (_PROTOCOL_VER_RX, "PROTOCOL-VER"),
            (_GIT_HOOK_VER_RX, "GIT-HOOK"),
        ):
            for m in rx.finditer(line):
                found_ver = m.group(1)
                if found_ver != current:
                    msg = (
                        f"  STALE [{stamp_type}]  {rel}:{lineno}"
                        f"  found=v{found_ver}  expected=v{current}"
                    )
                    violations.append(msg)
                    if verbose:
                        print(msg)

        # Type 5: Protocol-version-tracking body headings.
        # Scoped to protocol/**/*.md only; feature-attribution headings in
        # docs/, .pr-description.md, .protocol-state/ are outside this prefix
        # and are intentionally NOT checked here.
        if (
            rel.startswith(_BODY_HEADING_PATH_PREFIX)
            and rel not in _BODY_HEADING_ALLOWLIST
        ):
            m5 = _BODY_HEADING_RX.match(line)
            if m5:
                found_ver = m5.group(1)
                if found_ver != current:
                    msg = (
                        f"  STALE [BODY-HEADING]  {rel}:{lineno}"
                        f"  found=v{found_ver}  expected=v{current}"
                    )
                    violations.append(msg)
                    if verbose:
                        print(msg)

        # Type 6: **Protocol Version**: [v]X.Y.Z metadata fields.
        # Scoped to protocol/, docs/, and .protocol-state/jjk-character-reference/
        # only.  Files in _PROTOCOL_VER_FIELD_ALLOWLIST are frozen historical
        # records and are explicitly excluded from enforcement.
        in_scope_t6 = any(
            rel.startswith(prefix) for prefix in _PROTOCOL_VER_FIELD_PATH_PREFIXES
        )
        if in_scope_t6 and rel not in _PROTOCOL_VER_FIELD_ALLOWLIST:
            m6 = _PROTOCOL_VER_FIELD_RX.match(line)
            if m6:
                found_ver = m6.group(1)
                if found_ver != current:
                    msg = (
                        f"  STALE [PROTOCOL-VERSION]  {rel}:{lineno}"
                        f"  found=v{found_ver}  expected=v{current}"
                    )
                    violations.append(msg)
                    if verbose:
                        print(msg)

    return violations


def _collect_files(root: Path) -> list[Path]:
    """Walk the root and collect scannable files, respecting exclusion rules."""
    extensions = {
        ".md", ".yaml", ".yml", ".html", ".json", ".txt", ".sh", ".ps1", ".py"
    }
    results: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in extensions:
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        if _is_excluded(rel, p.name):
            continue
        results.append(p)
    return results


def main() -> int:
    ap = argparse.ArgumentParser(
        description="DZP version-stamp linter: ensure all stamps match protocol.config.yaml"
    )
    ap.add_argument("--root", default=".", help="DZP project root (default: .)")
    ap.add_argument("--verbose", action="store_true", help="Print each violation as found")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR: root '{root}' is not a directory.", file=sys.stderr)
        return 2

    current = _get_current_version(root)
    if not current:
        print(
            f"ERROR: could not read protocol_version from {root / 'protocol.config.yaml'}",
            file=sys.stderr,
        )
        return 2

    print(f"DZP stamp linter — current version: v{current}  root: {root}")

    files = _collect_files(root)
    print(f"Scanning {len(files)} files ...")

    all_violations: list[str] = []
    for f in sorted(files):
        violations = _scan_file(f, root, current, args.verbose)
        all_violations.extend(violations)

    if not all_violations:
        print(f"STAMP LINTER OK: all stamps at v{current}  (0 violations)")
        return 0

    print(f"\nSTAMP LINTER FAIL: {len(all_violations)} stale stamp(s) found:")
    for v in all_violations:
        print(v)
    print(
        "\nFix: run the version cascade and update all listed stamps to"
        f" v{current} before publishing."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
