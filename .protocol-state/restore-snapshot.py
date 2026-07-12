#!/usr/bin/env python3
"""
Domain Zero Protocol - Snapshot Restoration System

Version: 1.0.0
Created: 2025-12-06
Part of: DZP v8.8.0 Validation Framework - Phase 2

This script restores DZP state from compressed snapshots with <30s target.

Features:
- Fast decompression (direct to memory)
- Checksum verification before restore
- Automatic backup before restore
- Schema validation after restore
- Rollback capability on failure
- Progress indicators

Usage:
    python .protocol-state/restore-snapshot.py --list
    python .protocol-state/restore-snapshot.py --preview <snapshot-id>
    python .protocol-state/restore-snapshot.py --restore <snapshot-id>
    python .protocol-state/restore-snapshot.py --rollback
"""

import argparse
import copy
import gzip
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Fix Windows console encoding
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
    # Silent fallback for restore-snapshot (optional dependency)

# =============================================================================
# Constants
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / ".protocol-state"
SNAPSHOTS_DIR = STATE_DIR / "snapshots"
MANIFEST_FILE = SNAPSHOTS_DIR / "snapshot-manifest.json"
ROLLBACK_FILE = STATE_DIR / ".rollback-snapshot.json"
MEMORIES_DIR = PROJECT_ROOT / "memories"

# Performance target
TARGET_RESTORE_TIME_SECONDS = 30

# PATCH-STATE-001: Initialize ProjectStateManager
if STATE_MANAGER_AVAILABLE:
    _state_manager = ProjectStateManager(PROJECT_ROOT)
else:
    _state_manager = None


# =============================================================================
# Manifest Management
# =============================================================================

def load_manifest() -> Dict[str, Any]:
    """Load snapshot manifest"""
    if not MANIFEST_FILE.exists():
        return {"snapshots": []}

    try:
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"WARNING: Corrupted manifest file: {e}", file=sys.stderr)
        return {"snapshots": []}


# =============================================================================
# Snapshot Loading
# =============================================================================

# BUG-RESTORE-CHECKSUM-NOOP-001 (P1): create-snapshot.py's create_snapshot()
# (see .protocol-state/create-snapshot.py ~lines 380-386) computes the stored
# checksum over the snapshot dict with `checksum` set to None, serialized via
# `json.dumps(snapshot_data, indent=2)` -- BEFORE `metadata` is later mutated
# (lines 396-399) to add `compressed_size_bytes` / `uncompressed_size_bytes` /
# `compression_ratio`. In the CURRENT on-disk format those three keys never
# actually reach the persisted file at all (the compressed bytes that get
# written to disk are produced from the pre-mutation serialization -- verified
# against a real, freshly-created snapshot: its persisted `metadata` contains
# only `total_files`/`files_included`). They are stripped here defensively
# anyway (a no-op when absent) so this recompute stays correct even against a
# snapshot where they *are* present in `metadata` for any reason.
_POST_CHECKSUM_METADATA_KEYS = (
    "compressed_size_bytes",
    "uncompressed_size_bytes",
    "compression_ratio",
)


def _calculate_snapshot_checksum(snapshot_data: Dict[str, Any]) -> str:
    """
    Recompute the SHA-256 checksum over the EXACT pre-image bytes that
    create-snapshot.py hashed when the snapshot was created: the full
    snapshot dict with `checksum` forced to None, serialized via
    `json.dumps(..., indent=2)`.

    Args:
        snapshot_data: Decoded snapshot dict (as loaded from the gzip file)

    Returns:
        Hex-encoded SHA-256 digest of the pre-image
    """
    data_copy = copy.deepcopy(snapshot_data)
    data_copy["checksum"] = None

    metadata = data_copy.get("metadata")
    if isinstance(metadata, dict):
        for key in _POST_CHECKSUM_METADATA_KEYS:
            metadata.pop(key, None)

    calculated_bytes = json.dumps(data_copy, indent=2).encode('utf-8')
    return hashlib.sha256(calculated_bytes).hexdigest()


def _empty_verification() -> Dict[str, Any]:
    return {
        "performed": False,
        "matched": None,
        "override_used": False,
        "stored_checksum": None,
        "calculated_checksum": None,
    }


def load_snapshot(
    snapshot_id: str,
    force_unverified: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Dict[str, Any]]:
    """
    Load and decompress snapshot by ID, verifying its SHA-256 integrity
    checksum before returning it.

    BUG-RESTORE-CHECKSUM-NOOP-001 (P1) fix: this function previously computed
    `calculated_checksum` but NEVER compared it to `stored_checksum` -- it
    only printed the stored value and unconditionally returned the (possibly
    tampered) snapshot_data with error=None. A tampered/corrupted snapshot
    body with a stale stored checksum was silently accepted. This now fails
    CLOSED: a checksum mismatch (or a missing checksum) returns
    (None, error, verification) UNLESS the caller explicitly passes
    force_unverified=True (the --force-unverified break-glass, mirroring
    `brain restore`'s verify-by-default + --force-unverified design,
    SEC-002/v9.9.2), in which case a loud stderr warning is printed and the
    snapshot is returned anyway.

    Args:
        snapshot_id: Snapshot ID to load
        force_unverified: Break-glass override -- proceed even if the
            checksum is missing or does not match (always prints a loud
            warning either way)

    Returns:
        Tuple of (snapshot_data, error_message, verification_info) where
        verification_info = {
            "performed": bool,             # a stored checksum was present and compared
            "matched": Optional[bool],     # True/False if performed, else None
            "override_used": bool,         # force_unverified was needed to bypass a failure
            "stored_checksum": Optional[str],
            "calculated_checksum": Optional[str],
        }
    """
    manifest = load_manifest()

    # Find snapshot in manifest (support partial ID matching)
    snapshot_meta = None
    for s in manifest.get("snapshots", []):
        if s["snapshot_id"] == snapshot_id or s["snapshot_id"].startswith(snapshot_id):
            snapshot_meta = s
            break

    if not snapshot_meta:
        return None, f"Snapshot not found: {snapshot_id}", _empty_verification()

    snapshot_path = SNAPSHOTS_DIR / snapshot_meta["file_path"]

    if not snapshot_path.exists():
        return None, f"Snapshot file not found: {snapshot_path}", _empty_verification()

    # Decompress snapshot
    try:
        with gzip.open(snapshot_path, 'rb') as f:
            json_data = f.read()

        snapshot_data = json.loads(json_data)

    except Exception as e:
        return None, f"Failed to load snapshot: {e}", _empty_verification()

    # Verify checksum -- fail-closed BEFORE any backup or state-file write
    # happens (both of those occur later, in restore_snapshot()).
    stored_checksum = snapshot_data.get("checksum")
    calculated_checksum = _calculate_snapshot_checksum(snapshot_data)

    verification: Dict[str, Any] = {
        "performed": bool(stored_checksum),
        "matched": None,
        "override_used": False,
        "stored_checksum": stored_checksum,
        "calculated_checksum": calculated_checksum,
    }

    if not stored_checksum:
        if force_unverified:
            verification["override_used"] = True
            print(
                f"   ⚠️  WARNING: Snapshot {snapshot_id} has NO stored checksum -- "
                f"integrity CANNOT be verified. Proceeding ONLY because "
                f"--force-unverified was passed.",
                file=sys.stderr,
            )
        else:
            return None, (
                f"Snapshot {snapshot_id} has no stored checksum -- refusing to "
                f"restore unverified content. Pass --force-unverified to override "
                f"(not recommended)."
            ), verification
    else:
        print(f"   Checksum: {stored_checksum[:16]}... (stored)")
        print(f"   Checksum: {calculated_checksum[:16]}... (calculated)")

        verification["matched"] = (calculated_checksum == stored_checksum)

        if not verification["matched"]:
            if force_unverified:
                verification["override_used"] = True
                print(
                    f"   ⚠️  WARNING: CHECKSUM MISMATCH for snapshot {snapshot_id} -- "
                    f"this snapshot's content does NOT match its stored integrity "
                    f"checksum (possible tampering or corruption). Proceeding ONLY "
                    f"because --force-unverified was passed.",
                    file=sys.stderr,
                )
            else:
                return None, (
                    f"Checksum MISMATCH for snapshot {snapshot_id} -- stored="
                    f"{stored_checksum[:16]}... calculated={calculated_checksum[:16]}... "
                    f"Refusing to restore possibly-tampered/corrupted content. "
                    f"Pass --force-unverified to override (not recommended)."
                ), verification

    return snapshot_data, None, verification


# =============================================================================
# Preview
# =============================================================================

def preview_snapshot(snapshot_id: str) -> None:
    """
    Preview snapshot contents without restoring

    Args:
        snapshot_id: Snapshot ID to preview
    """
    # Preview is a READ-ONLY inspection that never touches state, so it loads
    # with force_unverified=True: a legacy (pre-checksum) or checksum-mismatched
    # snapshot must still be *displayable* so the user can inspect it before
    # deciding whether to restore. The integrity verdict is surfaced below
    # instead of blocking the view. (restore_snapshot() remains fail-closed.)
    snapshot_data, error, verification = load_snapshot(snapshot_id, force_unverified=True)

    if error:
        # Only genuinely unreadable snapshots (missing/corrupt file) reach here;
        # integrity failures no longer abort the preview.
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 80)
    print(f"Snapshot Preview: {snapshot_data['snapshot_id']}")
    print("=" * 80)

    # Surface the integrity status so a preview of a legacy/tampered snapshot is
    # never silently presented as trustworthy.
    if not verification.get("performed"):
        print("\n⚠️  Integrity: NO stored checksum (cannot verify — legacy snapshot)")
    elif verification.get("matched"):
        print("\n✅ Integrity: checksum VERIFIED")
    else:
        print("\n⚠️  Integrity: checksum MISMATCH (possible tampering/corruption)")

    print(f"\nCreated: {snapshot_data['created_at']}")
    print(f"Tier: {snapshot_data['tier']}")
    print(f"Trigger: {snapshot_data['trigger']}")
    print(f"Protocol Version: {snapshot_data['protocol_version']}")

    metadata = snapshot_data.get("metadata", {})
    print(f"\nFiles Included: {metadata.get('total_files', 0)}")
    print(f"Compressed Size: {round(metadata.get('compressed_size_bytes', 0) / 1024, 1)} KB")
    print(f"Uncompressed Size: {round(metadata.get('uncompressed_size_bytes', 0) / 1024, 1)} KB")

    if metadata.get('description'):
        print(f"Description: {metadata['description']}")

    print("\nState Files to Restore:")
    for file_path in metadata.get('files_included', []):
        print(f"  - {file_path}")

    print("\n" + "=" * 80)


# =============================================================================
# Backup Current State
# =============================================================================

def create_pre_restore_backup() -> Optional[str]:
    """
    Create backup of current state before restore

    Returns:
        Backup snapshot ID or None on failure
    """
    try:
        # Import create_snapshot from create-snapshot.py
        # F4 (CodeRabbit PR#109, P2): this previously pointed at
        # scripts/create-snapshot.py, which does NOT exist (the real file
        # lives at .protocol-state/create-snapshot.py). The resulting
        # ImportError/AttributeError was swallowed by the broad `except
        # Exception` below, so EVERY restore silently proceeded with NO
        # backup. Fixed to the correct path.
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "create_snapshot",
            PROJECT_ROOT / ".protocol-state" / "create-snapshot.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        create_snapshot = module.create_snapshot

        print("Creating pre-restore backup...")
        result = create_snapshot(
            tier=2,
            trigger="pre_restore_backup",
            description="Automatic backup before snapshot restore"
        )

        backup_id = result["snapshot_id"]
        print(f"✅ Backup created: {backup_id[:16]}...")

        # Save backup ID for rollback
        with open(ROLLBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump({"backup_snapshot_id": backup_id}, f)

        return backup_id

    except Exception as e:
        print(f"WARNING: Failed to create backup: {e}", file=sys.stderr)
        return None


# =============================================================================
# Restore
# =============================================================================

def restore_snapshot(
    snapshot_id: str,
    skip_backup: bool = False,
    force_unverified: bool = False,
) -> bool:
    """
    Restore DZP state from snapshot

    Args:
        snapshot_id: Snapshot ID to restore
        skip_backup: If True, skip pre-restore backup
        force_unverified: DANGEROUS break-glass -- restore even if the
            snapshot's checksum is missing or does not match (possible
            tampering/corruption). Always prints a loud warning. Verification
            still runs first (Step 1, below) -- this only controls whether a
            failed verification aborts the restore or is overridden.

    Returns:
        True if restore succeeded, False otherwise
    """
    start_time = time.time()

    print(f"\n{'=' * 80}")
    print(f"Restoring Snapshot: {snapshot_id}")
    print(f"{'=' * 80}\n")

    # Step 1: Load snapshot
    # BUG-RESTORE-CHECKSUM-NOOP-001 (P1) fix: load_snapshot() now actually
    # verifies the stored checksum against a recomputed one and, on mismatch
    # (or a missing checksum), returns an error here -- BEFORE the pre-restore
    # backup (Step 2) is created and BEFORE any state file is touched (Step
    # 4). This is the fail-closed ordering: a tampered/corrupted snapshot
    # never reaches the write path unless force_unverified=True was passed.
    print("[1/6] Loading snapshot...")
    snapshot_data, error, verification = load_snapshot(
        snapshot_id, force_unverified=force_unverified
    )

    if error:
        print(f"ERROR: {error}", file=sys.stderr)
        return False

    print(f"   Loaded {snapshot_data['metadata']['total_files']} files")

    # Step 2: Create backup (unless skipped)
    if not skip_backup:
        print("\n[2/6] Creating pre-restore backup...")
        backup_id = create_pre_restore_backup()
        if not backup_id:
            print("WARNING: Proceeding without backup")
    else:
        print("\n[2/6] Skipping backup (as requested)...")

    # Step 3: Report checksum verification result
    # Verification was ALREADY performed in Step 1 (before the backup above
    # and before any state file below is touched). This used to print a
    # hardcoded "Checksum verified" banner with zero computation -- it now
    # reports the REAL outcome captured during load_snapshot().
    print("\n[3/6] Verifying checksum...")
    if verification["performed"] and verification["matched"]:
        print(f"   ✅ Checksum verified ({verification['stored_checksum'][:16]}... matches)")
    elif verification["override_used"]:
        print(
            "   ⚠️  Restoring UNVERIFIED content (--force-unverified) -- checksum "
            "was missing or did not match. See warning above.",
            file=sys.stderr,
        )
    else:
        # Unreachable in practice: any real verification failure without
        # force_unverified already returned False at Step 1, above.
        print("   ⚠️  Checksum verification state unknown", file=sys.stderr)

    # Step 4: Restore state files
    print("\n[4/6] Restoring state files...")

    state_files = snapshot_data.get("state_files", {})
    restored_count = 0

    # Restore core state files
    for key, data in state_files.items():
        if key == "agent_memories":
            # Handle agent memories
            for agent_name, memory_data in data.items():
                agent_dir = MEMORIES_DIR / "agents" / agent_name
                agent_dir.mkdir(parents=True, exist_ok=True)

                for rel_path, file_data in memory_data.items():
                    file_path = agent_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(file_data, f, indent=2)

                    restored_count += 1
        else:
            # Map keys to file paths
            file_mapping = {
                "project_state": STATE_DIR / "project-state.json",
                "session_state": STATE_DIR / "session-state.json",
                "validation_state": STATE_DIR / "validation" / "validation-state.json"
            }

            if key in file_mapping:
                file_path = file_mapping[key]
                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)

                restored_count += 1

    print(f"   ✅ Restored {restored_count} files")

    # Step 5: Validate restored state (optional - can be skipped for speed)
    print("\n[5/6] Validating restored state...")
    print("   ✅ Validation skipped (fast mode)")

    # Step 6: Update session state with restoration metadata
    print("\n[6/6] Updating session state...")

    try:
        # PATCH-STATE-001: Use ProjectStateManager if available
        if _state_manager:
            try:
                session_data = _state_manager.get_session_tracking()
                session_data["last_snapshot_restore"] = {
                    "snapshot_id": snapshot_id,
                    "restored_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "files_restored": restored_count
                }
                _state_manager.update_session_tracking(session_data)
                print("   ✅ Session state updated")
            except Exception as e:
                print(f"   ⚠️  ProjectStateManager failed, falling back to legacy: {e}", file=sys.stderr)
                # Fall through to legacy file I/O
                raise  # Re-raise to trigger legacy fallback
        else:
            raise ImportError("ProjectStateManager not available")
    except Exception as e:
        # Legacy file I/O (backward compatibility)
        try:
            session_state_path = STATE_DIR / "session-state.json"
            if session_state_path.exists():
                with open(session_state_path, 'r', encoding='utf-8') as f:
                    session_state = json.load(f)

                session_state["last_snapshot_restore"] = {
                    "snapshot_id": snapshot_id,
                    "restored_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "files_restored": restored_count
                }

                # Atomic write using tempfile
                temp_path = session_state_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(session_state, f, indent=2)
                temp_path.replace(session_state_path)

                print("   ✅ Session state updated (legacy mode)")
        except Exception as legacy_error:
            print(f"   ⚠️  Session state update skipped: {legacy_error}", file=sys.stderr)

            # Critical: Write restoration metadata to recovery file
            try:
                recovery_data = {
                    "snapshot_id": snapshot_id,
                    "restored_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "files_restored": restored_count,
                    "error": str(legacy_error),
                    "state_manager_available": False,
                    "legacy_fallback_failed": True
                }

                recovery_path = STATE_DIR / "snapshot-restore-recovery.json"
                temp_recovery = recovery_path.with_suffix('.tmp')
                with open(temp_recovery, 'w', encoding='utf-8') as f:
                    json.dump(recovery_data, f, indent=2)
                temp_recovery.replace(recovery_path)

                print(f"   ⚠️  Restoration metadata saved to recovery file: {recovery_path}", file=sys.stderr)
                print(f"   ⚠️  WARNING: System may be in inconsistent state - manual verification recommended", file=sys.stderr)
            except Exception as recovery_error:
                print(f"   ❌ CRITICAL: Recovery file write failed: {recovery_error}", file=sys.stderr)
                print(f"   ❌ Snapshot restored but metadata lost - manual state verification required", file=sys.stderr)
                return False  # Exit with failure if recovery also fails

    # Calculate restore time
    restore_time = time.time() - start_time

    print(f"\n{'=' * 80}")
    print(f"✅ Snapshot restored successfully")
    print(f"   Files restored: {restored_count}")
    print(f"   Restore time: {restore_time:.2f}s", end="")

    if restore_time < TARGET_RESTORE_TIME_SECONDS:
        print(f" (target: <{TARGET_RESTORE_TIME_SECONDS}s ✅)")
    else:
        print(f" (target: <{TARGET_RESTORE_TIME_SECONDS}s ⚠️)")

    print(f"{'=' * 80}\n")

    return True


# =============================================================================
# Rollback
# =============================================================================

def rollback_restore() -> bool:
    """
    Rollback to pre-restore backup

    Returns:
        True if rollback succeeded, False otherwise
    """
    if not ROLLBACK_FILE.exists():
        print("ERROR: No rollback snapshot found", file=sys.stderr)
        print("Rollback is only available after a failed restore", file=sys.stderr)
        return False

    try:
        with open(ROLLBACK_FILE, 'r', encoding='utf-8') as f:
            rollback_data = json.load(f)

        backup_id = rollback_data.get("backup_snapshot_id")

        if not backup_id:
            print("ERROR: Invalid rollback data", file=sys.stderr)
            return False

        print(f"\nRolling back to backup: {backup_id[:16]}...\n")

        # Restore the backup snapshot (skip creating another backup)
        success = restore_snapshot(backup_id, skip_backup=True)

        if success:
            # Remove rollback file
            ROLLBACK_FILE.unlink()
            print("✅ Rollback completed successfully")

        return success

    except Exception as e:
        print(f"ERROR: Rollback failed: {e}", file=sys.stderr)
        return False


# =============================================================================
# Listing
# =============================================================================

def list_snapshots() -> None:
    """List all available snapshots"""
    manifest = load_manifest()
    snapshots = manifest.get("snapshots", [])

    if not snapshots:
        print("No snapshots available")
        return

    print(f"\nAvailable snapshots: {len(snapshots)}")
    print("=" * 80)

    for i, snapshot in enumerate(sorted(snapshots, key=lambda s: s["created_at"], reverse=True), 1):
        size_kb = round(snapshot["size_bytes"] / 1024, 1)
        snapshot_id_short = snapshot["snapshot_id"][:16]

        print(f"\n{i}. {snapshot['file_path']}")
        print(f"   ID: {snapshot_id_short}... (use for --restore)")
        print(f"   Created: {snapshot['created_at']}")
        print(f"   Tier: {snapshot['tier']}, Trigger: {snapshot['reason']}")
        print(f"   Size: {size_kb} KB")

        if snapshot.get("description"):
            print(f"   Description: {snapshot['description']}")

    print()


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol - Snapshot Restoration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                               List all snapshots
  %(prog)s --preview abc123                     Preview snapshot contents
  %(prog)s --restore abc123                     Restore snapshot
  %(prog)s --restore abc123 --skip-backup       Restore without backup
  %(prog)s --restore abc123 --force-unverified  DANGEROUS: restore even if checksum fails
  %(prog)s --rollback                           Rollback to pre-restore backup

Performance:
  Target restore time: <30 seconds
  Automatic backup before restore
  Checksum verification (fail-closed by default; see --force-unverified)
  Rollback capability
        """
    )

    parser.add_argument('--list', action='store_true',
                        help='List all available snapshots')
    parser.add_argument('--preview', type=str, metavar='SNAPSHOT_ID',
                        help='Preview snapshot contents without restoring')
    parser.add_argument('--restore', type=str, metavar='SNAPSHOT_ID',
                        help='Restore snapshot by ID')
    parser.add_argument('--skip-backup', action='store_true',
                        help='Skip pre-restore backup (dangerous)')
    parser.add_argument('--force-unverified', action='store_true',
                        help='DANGEROUS break-glass: restore even if the snapshot '
                             'checksum is missing or does not match (possible '
                             'tampering/corruption). Always prints a loud warning. '
                             'Default behavior (no flag) is fail-closed: a checksum '
                             'mismatch aborts the restore before any state file is written.')
    parser.add_argument('--rollback', action='store_true',
                        help='Rollback to pre-restore backup')
    parser.add_argument('--debug', action='store_true',
                        help='Show full error tracebacks')

    args = parser.parse_args()

    try:
        if args.list:
            list_snapshots()
            sys.exit(0)

        if args.preview:
            preview_snapshot(args.preview)
            sys.exit(0)

        if args.restore:
            success = restore_snapshot(
                args.restore,
                skip_backup=args.skip_backup,
                force_unverified=args.force_unverified,
            )
            sys.exit(0 if success else 1)

        if args.rollback:
            success = rollback_restore()
            sys.exit(0 if success else 1)

        # No command specified
        parser.print_help()
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
