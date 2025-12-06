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
    python scripts/create-snapshot.py --manual [--description "desc"]
    python scripts/create-snapshot.py --auto --tier 2 --trigger operation_count
    python scripts/create-snapshot.py --list
"""

import argparse
import gzip
import hashlib
import json
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

# =============================================================================
# Constants
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / ".protocol-state"
SNAPSHOTS_DIR = STATE_DIR / "snapshots"
MANIFEST_FILE = SNAPSHOTS_DIR / "snapshot-manifest.json"
MEMORIES_DIR = PROJECT_ROOT / "memories"

# Retention limits by tier
RETENTION_LIMITS = {
    1: 10,   # Tier 1: Manual only
    2: 30,   # Tier 2: Every 10 operations
    3: 50    # Tier 3: Continuous
}

# Storage warning threshold (200 MB)
STORAGE_WARNING_BYTES = 200 * 1024 * 1024


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


# =============================================================================
# State File Discovery
# =============================================================================

def discover_state_files() -> Dict[str, Path]:
    """
    Discover all DZP state files to include in snapshot

    Returns:
        Dictionary mapping file keys to file paths
    """
    state_files = {}

    # Core state files
    core_files = {
        "project_state": STATE_DIR / "project-state.json",
        "session_state": STATE_DIR / "session-state.json",
        "validation_state": STATE_DIR / "validation" / "validation-state.json",
    }

    for key, path in core_files.items():
        if path.exists():
            state_files[key] = path

    # Memory files (agent-specific)
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
    snapshot_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)
    timestamp_str = timestamp.isoformat().replace('+00:00', 'Z')
    timestamp_file = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")

    # Discover state files
    state_files_paths = discover_state_files()

    # Build snapshot data structure
    snapshot_data = {
        "snapshot_id": snapshot_id,
        "created_at": timestamp_str,
        "tier": tier,
        "trigger": trigger,
        "operation_count": operation_count,
        "protocol_version": "8.8.0",
        "state_files": {},
        "metadata": {
            "total_files": 0,
            "files_included": [],
            "description": description
        },
        "checksum": None  # Will be calculated after serialization
    }

    # Embed state file contents
    file_count = 0

    # Core state files
    for key, path in state_files_paths.items():
        if key == "agent_memories":
            # Handle agent memories separately
            agent_memories = {}
            for agent_name, memory_files in path.items():
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
            try:
                snapshot_data["state_files"][key] = read_json_file(path)
                file_count += 1
                snapshot_data["metadata"]["files_included"].append(str(path.relative_to(PROJECT_ROOT)))
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
    manifest["snapshots"].append({
        "snapshot_id": snapshot_id,
        "created_at": timestamp_str,
        "tier": tier,
        "reason": trigger,
        "file_path": snapshot_filename,
        "size_bytes": compressed_size,
        "description": description,
        "tagged": False  # Can be tagged later for preservation
    })

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
    parser.add_argument('--trigger', type=str, default='manual',
                        help='Trigger reason for snapshot')
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
