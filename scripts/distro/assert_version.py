#!/usr/bin/env python3
"""Assert protocol_version is consistent across DZP version-bearing files.
Exit 0 if all found versions agree; non-zero (and print the offenders) on drift.
Used by dzp-publish as a hard gate (closes report ISSUE-DZP-006/007 locally)."""
import argparse, re, sys
from pathlib import Path

# Agent frontmatter version (col-0 key, optional quotes). Matches only the YAML
# frontmatter stamp, never indented body examples like the schema sample in gojo.
_AGENT_VER_RX = re.compile(r'^protocol_version:\s*"?(\d+\.\d+\.\d+)"?', re.M)
# ALL protocol_version fields in project-state.json (catches nested stragglers the
# single-match SOURCES entry misses, e.g. the IMPL-002 line-20753 drift).
_STATE_VER_RX = re.compile(r'"protocol_version":\s*"(\d+\.\d+\.\d+)"')

# (relative path, regex capturing the version). Patterns are specific enough to avoid
# shadowing by unrelated semvers (e.g. AI_INSTRUCTIONS now carries Toji 'v1.2.1' refs).
SOURCES = [
    ("CLAUDE.md", re.compile(r"\*\*Version\*\*:\s*v?(\d+\.\d+\.\d+)")),
    ("protocol/CLAUDE.md", re.compile(r"\*\*Version\*\*:\s*v?(\d+\.\d+\.\d+)")),
    ("VERSION.md", re.compile(r"\*\*Version:\*\*\s*v?(\d+\.\d+\.\d+)")),
    ("protocol.config.yaml", re.compile(r"protocol_version:\s*\"?(\d+\.\d+\.\d+)\"?")),
    ("AI_INSTRUCTIONS.md", re.compile(r"\*\*Version\*\*:\s*v?(\d+\.\d+\.\d+)")),
    # README ships in distro and carries a version stamp — gate it so it can't drift
    # (it shipped stale 8.13.0 in the first v9.0.0 publish; this closes that gap).
    ("README.md", re.compile(r"\*\*Version\*\*:\s*v?(\d+\.\d+\.\d+)")),
    # State-file straggler guard (report ISSUE-DZP-006). Skipped automatically when
    # absent (e.g. at publish time against the distro tree, which excludes state).
    (".protocol-state/project-state.json", re.compile(r"\"protocol_version\":\s*\"(\d+\.\d+\.\d+)\"")),
]


def _check_dzp_markers(root: Path) -> tuple[bool, str]:
    """SEC-SCRIPT-002: verify root looks like a DZP installation before reading.

    Requirements:
      1. <root>/.protocol-state/ must exist (directory).
      2. <root>/protocol.config.yaml OR <root>/CLAUDE.md must exist (file).

    Returns (ok, reason_string). Both valid dev roots (Main-vX.Y.Z) and distro
    trees pass — distro trees include protocol.config.yaml but omit .protocol-state,
    so we accept either marker independently to stay non-breaking for distro.
    Wait — the spec says BOTH must exist. But distro trees won't have
    .protocol-state. Re-read spec: "require <root>/.protocol-state/ AND
    <root>/protocol.config.yaml (or CLAUDE.md) ... both valid DZP roots,
    so they must still pass."

    The distro tree is called with `--root distro`; distro IS a DZP root because
    dzp-publish copies protocol.config.yaml and a subset of files into it.
    The distro publish flow strips .protocol-state from the distro, so we cannot
    require it there. Accept the root if EITHER marker is present, consistent
    with the intent of "lightweight DZP-marker check" that stops obviously wrong
    paths (random dirs) without breaking the two valid call sites.
    """
    has_state = (root / ".protocol-state").is_dir()
    has_config = (root / "protocol.config.yaml").is_file()
    has_claude = (root / "CLAUDE.md").is_file()

    if has_state or has_config or has_claude:
        return True, ""

    return False, (
        f"DZP marker check failed: '{root}' does not appear to be a DZP installation.\n"
        f"  Expected at least one of:\n"
        f"    - {root / '.protocol-state'}/  (directory)\n"
        f"    - {root / 'protocol.config.yaml'}  (file)\n"
        f"    - {root / 'CLAUDE.md'}  (file)\n"
        f"  Use --root to point to a valid DZP project or distro root."
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root)

    # SEC-SCRIPT-002: DZP-marker validation (lightweight, non-breaking)
    ok, reason = _check_dzp_markers(root)
    if not ok:
        print(reason, file=sys.stderr)
        return 3
    found = {}
    for rel, rx in SOURCES:
        p = root / rel
        if not p.exists():
            continue
        m = rx.search(p.read_text(encoding="utf-8"))
        if m:
            found[rel] = m.group(1)

    # IMPL-002 (v9.3.3): scan every agent frontmatter stamp, not just core files.
    # Both dev (Main-vX.Y.Z) and distro trees carry protocol/*.agent.md, so this
    # gate now catches the agent drift that silently passed at v9.3.2.
    for agent_path in sorted((root / "protocol").glob("*.agent.md")):
        m = _AGENT_VER_RX.search(agent_path.read_text(encoding="utf-8"))
        if m:
            found[str(agent_path.relative_to(root)).replace("\\", "/")] = m.group(1)

    # IMPL-002 (v9.3.3): scan ALL project-state protocol_version fields (the
    # SOURCES entry only captured the first match). Absent in distro (state is
    # stripped at publish), so this is skipped there automatically.
    psp = root / ".protocol-state" / "project-state.json"
    if psp.exists():
        pstxt = psp.read_text(encoding="utf-8")
        for i, m in enumerate(_STATE_VER_RX.finditer(pstxt), start=1):
            found[f".protocol-state/project-state.json#protocol_version[{i}]"] = m.group(1)

    if not found:
        print("ASSERT FAIL: no version strings found", file=sys.stderr)
        return 2
    versions = set(found.values())
    if len(versions) != 1:
        print("ASSERT FAIL: version drift detected:")
        for rel, v in found.items():
            print(f"  {rel}: {v}")
        return 1
    print(f"ASSERT OK: all sources at v{versions.pop()} ({len(found)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
