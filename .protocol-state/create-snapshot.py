#!/usr/bin/env python3
"""
Domain Zero Protocol - Context Snapshot Creation System

Version: 1.0.0
Created: 2025-12-06
Part of: DZP v8.8.0 Validation Framework - Phase 2

This script creates compressed snapshots of DZP state for cold-start recovery.

Features:
- Tier-based automatic snapshots
- Manual snapshot creation
- Gzip compression (target: 70% size reduction)
- SHA-256 integrity checksums
- <30 second restoration target
- Snapshot manifest management

Usage:
    python .protocol-state/create-snapshot.py --manual [--description "desc"]
    python .protocol-state/create-snapshot.py --auto --tier 2 --trigger operation_count
    python .protocol-state/create-snapshot.py --list
"""

import argparse
import gzip
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# PATCH-STATE-001: Import centralized state manager
try:
    # Add .protocol-state to path for importing ProjectStateManager
    protocol_state_dir = Path(__file__).parent.parent / ".protocol-state"
    if str(protocol_state_dir) not in sys.path:
        sys.path.insert(0, str(protocol_state_dir))

    from project_state_manager import ProjectStateManager
    STATE_MANAGER_AVAILABLE = True
except ImportError:
    STATE_MANAGER_AVAILABLE = False
    # Silent fallback for create-snapshot (optional dependency)

# ISS-083: local write-attestation (fail-soft; module lives alongside this
# one in .protocol-state/). Absence must never break snapshot creation.
try:
    from attestation import record_write as _attest_record_write
    _ATTESTATION_AVAILABLE = True
except ImportError:
    _ATTESTATION_AVAILABLE = False

# =============================================================================
# Constants
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / ".protocol-state"
SNAPSHOTS_DIR = STATE_DIR / "snapshots"
MANIFEST_FILE = SNAPSHOTS_DIR / "snapshot-manifest.json"

_VERSION_RE = re.compile(r"\*\*Version:\*\*\s*v?(\d+\.\d+\.\d+)")


def _protocol_version() -> str:
    """Current protocol_version, read from VERSION.md (same source
    scripts/distro/assert_version.py treats as authoritative; mirrors the
    scripts/issue_id.py::_protocol_version() pattern). Never hardcoded here so
    every snapshot's embedded stamp doesn't drift stale across version bumps
    (BUG-SNAPSHOT-STALE-VERSION-001 cousin of BUG-SNAPSHOT-NULLFIELDS-001 —
    the literal "8.8.0" here was frozen at the script's v8.8.0 introduction
    and never updated on any subsequent release).

    Finding 15 (CodeRabbit PR#112, P2): a version-source read/parse failure
    used to silently embed the placeholder "0.0.0-unknown" into every
    snapshot body. Now raises instead, so create_snapshot() aborts rather
    than persisting an unknown-version artifact; callers (main()'s broad
    except, and restore-snapshot.py's create_pre_restore_backup()'s own
    broad except) already turn this into a clean, loud failure -- see both
    call sites' docstrings/comments for how each one degrades."""
    version_md = PROJECT_ROOT / "VERSION.md"
    try:
        text = version_md.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"could not read {version_md} to determine the authoritative "
            f"protocol_version ({e}); refusing to create a snapshot with unknown "
            "version metadata baked in permanently"
        ) from e
    m = _VERSION_RE.search(text)
    if not m:
        raise RuntimeError(
            f"{version_md} did not contain a recognizable '**Version:** vX.Y.Z' stamp; "
            "refusing to create a snapshot with unknown version metadata baked in "
            "permanently"
        )
    return m.group(1)
MEMORIES_DIR = PROJECT_ROOT / "memories"

# PATCH-STATE-001: Initialize ProjectStateManager
if STATE_MANAGER_AVAILABLE:
    _state_manager = ProjectStateManager(PROJECT_ROOT)
else:
    _state_manager = None

# Retention limits by tier
RETENTION_LIMITS = {
    1: 10,   # Tier 1: Manual only
    2: 30,   # Tier 2: Every 10 operations
    3: 50    # Tier 3: Continuous
}

# Storage warning threshold (200 MB)
STORAGE_WARNING_BYTES = 200 * 1024 * 1024

# MF-1 (BUG-SNAPSHOT-NULLFIELDS-001 remediation, Megumi Tier-2, v9.9.x):
# defense-in-depth allowlist for --trigger. This MUST mirror the `reason`
# enum in protocol/validation-rules.yaml (both the `snapshot` and
# `snapshot-manifest` schemas) EXACTLY -- an unknown trigger must fail LOUD
# here (argparse rejects it before any snapshot is written) rather than
# silently producing a body the commit-gate schema rejects later.
#
# Call-site audit (2026-07-11) of every place that passes --trigger to this
# script or calls create_snapshot() directly -- all 8 values below are drawn
# from real callers, none invented:
#   .protocol-state/script_dependencies.yaml:45   --trigger session-end
#   .protocol-state/script_dependencies.yaml:119  --trigger pre-protected-edit
#   .protocol-state/script_dependencies.yaml:180  --trigger toji-snapshot
#   .protocol-state/snapshot_integration.py:177,264  trigger="operation_count" (subprocess --trigger)
#   .protocol-state/snapshot_integration.py:285      trigger="tier_change"    (subprocess --trigger)
#   argparse default / any bare `--manual`          trigger defaults to "manual"
#   protocol/validation-rules.yaml (pre-existing)    "session-start" (schema-reserved;
#                                                     no live CLI emitter found yet, kept
#                                                     for schema parity)
#   .protocol-state/restore-snapshot.py:217          trigger="pre_restore_backup" (direct
#                                                     create_snapshot() Python call, NOT
#                                                     via this argparse CLI -- that call site
#                                                     is currently DEAD/unreachable due to an
#                                                     unrelated wrong-import-path bug, tracked
#                                                     separately; included here defensively so
#                                                     repairing that import will not reintroduce
#                                                     BUG-SNAPSHOT-NULLFIELDS-001)
VALID_TRIGGERS = [
    "manual",
    "operation_count",
    "tier_change",
    "session-end",
    "session-start",
    "pre-protected-edit",
    "toji-snapshot",
    "pre_restore_backup",
]


# =============================================================================
# Snapshot Manifest Management
# =============================================================================

def load_manifest() -> Dict[str, Any]:
    """
    Load snapshot manifest or create new one

    Returns:
        Manifest dictionary
    """
    if not MANIFEST_FILE.exists():
        return {
            "total_snapshots": 0,
            "last_snapshot_created": None,
            "retention_policy": {
                "tier_1_max": RETENTION_LIMITS[1],
                "tier_2_max": RETENTION_LIMITS[2],
                "tier_3_max": RETENTION_LIMITS[3],
                "cleanup_strategy": "oldest_first"
            },
            "snapshots": []
        }

    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_manifest(manifest: Dict[str, Any]) -> None:
    """
    Save snapshot manifest

    Args:
        manifest: Manifest dictionary to save
    """
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    # ISS-083: attest this sanctioned write of snapshot-manifest.json.
    # Fail-soft, best-effort -- never blocks snapshot creation.
    if _ATTESTATION_AVAILABLE:
        try:
            content = MANIFEST_FILE.read_bytes()
            _attest_record_write(STATE_DIR, MANIFEST_FILE.name, content, writer="create-snapshot")
        except Exception:
            pass


# =============================================================================
# State File Discovery
# =============================================================================

def discover_state_files() -> Dict[str, Any]:
    """
    Discover all DZP state files to include in snapshot

    PATCH-STATE-001: Uses ProjectStateManager when available to read consolidated state.

    Returns:
        Dictionary mapping logical keys to:
        - Path objects for core state files, and
        - Nested dicts of agent → {relative_path → Path} for "agent_memories".
    """
    state_files = {}
    _state_manager_failed = False  # Initialize flag to avoid undefined variable error

    # PATCH-STATE-001: Use ProjectStateManager if available for consolidated state
    if _state_manager:
        try:
            # Read consolidated project-state.json using ProjectStateManager
            project_state = _state_manager.load_project_state()

            # Include full project state
            state_files["project_state"] = {"_data": project_state}

            # Extract session tracking from consolidated state
            if "session_tracking" in project_state:
                state_files["session_state"] = {"_data": project_state["session_tracking"]}

            # Validation state still stored separately (not consolidated)
            validation_state_path = STATE_DIR / "validation" / "validation-state.json"
            if validation_state_path.exists():
                state_files["validation_state"] = validation_state_path
        except Exception as e:
            print(f"[WARN] ProjectStateManager failed, falling back to legacy file discovery: {e}", file=sys.stderr)
            # Fall through to legacy file I/O
            _state_manager_failed = True
    else:
        _state_manager_failed = True

    # Legacy file I/O (backward compatibility)
    if not _state_manager or _state_manager_failed:
        core_files = {
            "project_state": STATE_DIR / "project-state.json",
            "session_state": STATE_DIR / "session-state.json",
            "validation_state": STATE_DIR / "validation" / "validation-state.json",
        }

        for key, path in core_files.items():
            if path.exists():
                state_files[key] = path

    # Memory files (agent-specific) - always use file discovery
    if MEMORIES_DIR.exists():
        agent_memories = {}
        for agent_dir in MEMORIES_DIR.glob("agents/*"):
            if agent_dir.is_dir():
                agent_name = agent_dir.name
                agent_files = {}

                for memory_file in agent_dir.rglob("*.json"):
                    relative_path = memory_file.relative_to(agent_dir)
                    agent_files[str(relative_path)] = memory_file

                if agent_files:
                    agent_memories[agent_name] = agent_files

        if agent_memories:
            state_files["agent_memories"] = agent_memories

    return state_files


# =============================================================================
# Snapshot Creation
# =============================================================================

def read_json_file(file_path: Path) -> Any:
    """
    Read and parse JSON file

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON content
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_snapshot(
    tier: int = 2,
    trigger: str = "manual",
    description: Optional[str] = None,
    operation_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a new DZP context snapshot

    Args:
        tier: Current tier (1, 2, or 3)
        trigger: Snapshot trigger reason
        description: Optional user description
        operation_count: Current operation count (if applicable)

    Returns:
        Snapshot metadata dictionary
    """
    # F1 (CodeRabbit PR#109, P2): VALID_TRIGGERS was previously enforced ONLY
    # via argparse `choices=` in main() (the CLI path, see below). Direct
    # Python callers of create_snapshot() -- e.g. restore-snapshot.py's
    # create_pre_restore_backup(), which dynamically imports this module and
    # calls create_snapshot() directly -- bypass argparse entirely and had NO
    # validation at all. Enforce the same allowlist here, at the function
    # boundary, so every caller (CLI or direct) is protected.
    if trigger not in VALID_TRIGGERS:
        raise ValueError(
            f"Invalid snapshot trigger {trigger!r}. Must be one of: {', '.join(VALID_TRIGGERS)} "
            "(mirrors protocol/validation-rules.yaml `reason` enum). Direct Python callers of "
            "create_snapshot() are not protected by argparse and must pass validation here too."
        )

    snapshot_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)
    timestamp_str = timestamp.isoformat().replace('+00:00', 'Z')
    timestamp_file = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")

    # Discover state files
    state_files_paths = discover_state_files()

    # Build snapshot data structure
    # BUG-SNAPSHOT-NULLFIELDS-001 (v9.9.x): the commit-gate schema
    # (protocol/validation-rules.yaml::snapshot) REQUIRES a `reason` key at
    # the body root and types `metadata.description` as `string` (not
    # nullable). Emit `reason` alongside the legacy `trigger` key (back-compat
    # for any consumer still reading `trigger`), and build `metadata` without
    # a `description` key at all when none was supplied -- add it below only
    # when a real string was provided, mirroring the manifest-entry guard.
    metadata: Dict[str, Any] = {
        "total_files": 0,
        "files_included": [],
    }
    if description is not None:
        metadata["description"] = description

    snapshot_data = {
        "snapshot_id": snapshot_id,
        "created_at": timestamp_str,
        "tier": tier,
        "trigger": trigger,
        "reason": trigger,
        "operation_count": operation_count,
        "protocol_version": _protocol_version(),
        "state_files": {},
        "metadata": metadata,
        "checksum": None  # Will be calculated after serialization
    }

    # Embed state file contents
    file_count = 0

    # Core state files
    for key, value in state_files_paths.items():
        if key == "agent_memories":
            # Handle agent memories separately
            agent_memories = {}
            for agent_name, memory_files in value.items():
                agent_data = {}
                for rel_path, file_path in memory_files.items():
                    try:
                        agent_data[rel_path] = read_json_file(file_path)
                        file_count += 1
                        snapshot_data["metadata"]["files_included"].append(f"memories/agents/{agent_name}/{rel_path}")
                    except Exception:
                        # Skip files that can't be read
                        pass
                if agent_data:
                    agent_memories[agent_name] = agent_data

            if agent_memories:
                snapshot_data["state_files"]["agent_memories"] = agent_memories
        else:
            # PATCH-STATE-001: Handle both Path objects and data dictionaries
            try:
                if isinstance(value, dict) and "_data" in value:
                    # Data already loaded by ProjectStateManager
                    snapshot_data["state_files"][key] = value["_data"]
                    file_count += 1
                    snapshot_data["metadata"]["files_included"].append(f".protocol-state/{key}.json")
                else:
                    # Legacy: Path object, read from file
                    snapshot_data["state_files"][key] = read_json_file(value)
                    file_count += 1
                    snapshot_data["metadata"]["files_included"].append(str(value.relative_to(PROJECT_ROOT)))
            except Exception:
                # Skip files that can't be read
                pass

    snapshot_data["metadata"]["total_files"] = file_count

    # Serialize to JSON (uncompressed)
    json_bytes = json.dumps(snapshot_data, indent=2).encode('utf-8')
    uncompressed_size = len(json_bytes)

    # Calculate checksum before compression
    checksum = hashlib.sha256(json_bytes).hexdigest()
    snapshot_data["checksum"] = checksum

    # Re-serialize with checksum
    json_bytes = json.dumps(snapshot_data, indent=2).encode('utf-8')

    # Compress with gzip
    compressed_bytes = gzip.compress(json_bytes, compresslevel=6)
    compressed_size = len(compressed_bytes)
    compression_ratio = compressed_size / uncompressed_size

    # Update metadata
    snapshot_data["metadata"]["compressed_size_bytes"] = compressed_size
    snapshot_data["metadata"]["uncompressed_size_bytes"] = uncompressed_size
    snapshot_data["metadata"]["compression_ratio"] = round(compression_ratio, 2)

    # Save compressed snapshot
    snapshot_filename = f"snapshot-{timestamp_file}.json.gz"
    snapshot_path = SNAPSHOTS_DIR / snapshot_filename

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(snapshot_path, 'wb') as f:
        f.write(compressed_bytes)

    # Update manifest
    manifest = load_manifest()
    manifest["total_snapshots"] += 1
    manifest["last_snapshot_created"] = timestamp_str
    # BUG-SESSION-004 (v9.9.x Track C): `description` must be a string (not null)
    # when present; omit the key entirely rather than writing null so that the
    # snapshot-manifest schema validator never sees a type violation.
    manifest_entry: Dict[str, Any] = {
        "snapshot_id": snapshot_id,
        "created_at": timestamp_str,
        "tier": tier,
        "reason": trigger,
        "file_path": snapshot_filename,
        "size_bytes": compressed_size,
        "tagged": False,  # Can be tagged later for preservation
    }
    if description is not None:
        manifest_entry["description"] = description
    manifest["snapshots"].append(manifest_entry)

    save_manifest(manifest)

    # Enforce retention policy
    enforce_retention_policy(tier)

    return {
        "snapshot_id": snapshot_id,
        "snapshot_path": str(snapshot_path.relative_to(PROJECT_ROOT)),
        "timestamp": timestamp_str,
        "tier": tier,
        "trigger": trigger,
        "files_included": file_count,
        "compressed_size": compressed_size,
        "uncompressed_size": uncompressed_size,
        "compression_ratio": compression_ratio,
        "checksum": checksum
    }


# =============================================================================
# Retention Policy
# =============================================================================

def enforce_retention_policy(tier: int) -> List[str]:
    """
    Enforce snapshot retention policy by deleting oldest snapshots

    Args:
        tier: Current tier to enforce policy for

    Returns:
        List of deleted snapshot IDs
    """
    manifest = load_manifest()
    max_snapshots = RETENTION_LIMITS.get(tier, RETENTION_LIMITS[2])

    # Filter untagged snapshots for this tier
    tier_snapshots = [
        s for s in manifest["snapshots"]
        if s["tier"] == tier and not s.get("tagged", False)
    ]

    deleted = []

    if len(tier_snapshots) > max_snapshots:
        # Sort by created_at (oldest first)
        sorted_snapshots = sorted(tier_snapshots, key=lambda s: s["created_at"])

        # Delete oldest snapshots
        to_delete = sorted_snapshots[:len(tier_snapshots) - max_snapshots]

        for snapshot in to_delete:
            snapshot_path = SNAPSHOTS_DIR / snapshot["file_path"]
            if snapshot_path.exists():
                snapshot_path.unlink()

            # Remove from manifest
            manifest["snapshots"] = [
                s for s in manifest["snapshots"]
                if s["snapshot_id"] != snapshot["snapshot_id"]
            ]

            manifest["total_snapshots"] -= 1
            deleted.append(snapshot["snapshot_id"])

        save_manifest(manifest)

    return deleted


# =============================================================================
# Storage Monitoring
# =============================================================================

def calculate_total_storage() -> Dict[str, Any]:
    """
    Calculate total snapshot storage usage

    Returns:
        Dictionary with storage statistics
    """
    total_size = 0
    snapshot_count = 0

    if SNAPSHOTS_DIR.exists():
        for snapshot_file in SNAPSHOTS_DIR.glob("snapshot-*.json.gz"):
            total_size += snapshot_file.stat().st_size
            snapshot_count += 1

    return {
        "total_bytes": total_size,
        "total_mb": round(total_size / (1024 * 1024), 2),
        "snapshot_count": snapshot_count,
        "warning_threshold_mb": round(STORAGE_WARNING_BYTES / (1024 * 1024), 2),
        "exceeds_threshold": total_size > STORAGE_WARNING_BYTES
    }


# =============================================================================
# Listing & Display
# =============================================================================

def list_snapshots(tagged_only: bool = False) -> None:
    """
    List all available snapshots

    Args:
        tagged_only: If True, show only tagged snapshots
    """
    manifest = load_manifest()

    snapshots = manifest.get("snapshots", [])

    if tagged_only:
        snapshots = [s for s in snapshots if s.get("tagged", False)]

    if not snapshots:
        print("No snapshots available")
        return

    print(f"\nAvailable snapshots: {len(snapshots)}")
    print("=" * 80)

    for i, snapshot in enumerate(sorted(snapshots, key=lambda s: s["created_at"], reverse=True), 1):
        tagged_indicator = " [TAGGED]" if snapshot.get("tagged", False) else ""
        size_kb = round(snapshot["size_bytes"] / 1024, 1)

        print(f"\n{i}. {snapshot['file_path']}{tagged_indicator}")
        print(f"   ID: {snapshot['snapshot_id']}")
        print(f"   Created: {snapshot['created_at']}")
        print(f"   Tier: {snapshot['tier']}, Trigger: {snapshot['reason']}")
        print(f"   Size: {size_kb} KB")

        if snapshot.get("description"):
            print(f"   Description: {snapshot['description']}")

    print()

    # Show storage summary
    storage = calculate_total_storage()
    print(f"Total storage: {storage['total_mb']} MB / {storage['warning_threshold_mb']} MB")

    if storage["exceeds_threshold"]:
        print("⚠️  WARNING: Snapshot storage exceeds recommended threshold")
        print("   Consider cleaning up old snapshots or increasing storage limit")


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol - Snapshot Creation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --manual                             Create manual snapshot
  %(prog)s --manual --description "Before v8.9" Create with description
  %(prog)s --auto --tier 2 --trigger operation_count  Create automatic snapshot
  %(prog)s --list                               List all snapshots
  %(prog)s --list --tagged                      List tagged snapshots only

Retention Limits:
  Tier 1: 10 snapshots (manual only)
  Tier 2: 30 snapshots
  Tier 3: 50 snapshots
        """
    )

    parser.add_argument('--manual', action='store_true',
                        help='Create manual snapshot')
    parser.add_argument('--auto', action='store_true',
                        help='Create automatic snapshot (tier-based)')
    parser.add_argument('--tier', type=int, choices=[1, 2, 3], default=2,
                        help='Tier for automatic snapshot (default: 2)')
    parser.add_argument('--trigger', type=str, default='manual', choices=VALID_TRIGGERS,
                        help='Trigger reason for snapshot (must match the protocol/validation-rules.yaml '
                             '`reason` enum -- an unrecognized value is rejected here, loudly, before any '
                             'snapshot is written)')
    parser.add_argument('--description', '-d', type=str,
                        help='Optional description for manual snapshot')
    parser.add_argument('--operation-count', type=int,
                        help='Current operation count')
    parser.add_argument('--list', action='store_true',
                        help='List all available snapshots')
    parser.add_argument('--tagged', action='store_true',
                        help='Show only tagged snapshots (requires --list)')

    args = parser.parse_args()

    try:
        if args.list:
            list_snapshots(tagged_only=args.tagged)
            sys.exit(0)

        if not args.manual and not args.auto:
            parser.print_help()
            sys.exit(0)

        # Create snapshot
        print(f"\nCreating snapshot...")

        result = create_snapshot(
            tier=args.tier,
            trigger=args.trigger,
            description=args.description,
            operation_count=args.operation_count
        )

        print(f"✅ Snapshot created successfully")
        print(f"\nSnapshot ID: {result['snapshot_id']}")
        print(f"Path: {result['snapshot_path']}")
        print(f"Files included: {result['files_included']}")
        print(f"Size: {round(result['compressed_size'] / 1024, 1)} KB (compressed)")
        print(f"     {round(result['uncompressed_size'] / 1024, 1)} KB (uncompressed)")
        print(f"Compression: {round((1 - result['compression_ratio']) * 100, 1)}% size reduction")
        print(f"Checksum: {result['checksum'][:16]}...")

        # Show storage warning if needed
        storage = calculate_total_storage()
        if storage["exceeds_threshold"]:
            print(f"\n⚠️  WARNING: Total snapshot storage ({storage['total_mb']} MB) exceeds {storage['warning_threshold_mb']} MB")

        print()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
