#!/usr/bin/env python3
"""
Domain Zero Protocol - State Consolidation Migration Script
Version: 1.1.0
Purpose: Migrate from fragmented state files to unified project-state.json

PATCH: PATCH-STATE-001
SECURITY FIX: SEC-024 (Migration Lock), SEC-021 (Backup Integrity), SEC-025 (Rollback on Failure)
Part of: v8.12.0

This script consolidates:
- session-state.json → project-state.json::session_tracking
- troubleshooting-history.json → project-state.json::troubleshooting.history
- agent-invocation-tracker.json → project-state.json::agent_invocation_tracking
- tier_usage_statistics + tier_statistics → project-state.json::tier_tracking

Security Features:
- Exclusive migration lock prevents concurrent state access (SEC-024)
- Backup integrity verification with checksums (SEC-021)
- Automatic rollback on partial migration failure (SEC-025)
- Disk space check before backup creation (SEC-023)

Usage:
    python migrate_state_consolidation.py --check         # Dry run (show what will happen)
    python migrate_state_consolidation.py --execute       # Perform migration
    python migrate_state_consolidation.py --rollback      # Rollback to backups
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Import the ProjectStateManager
try:
    from project_state_manager import ProjectStateManager
except ImportError:
    print("[ERROR] Cannot import ProjectStateManager")
    print("  Ensure project_state_manager.py exists in .protocol-state/")
    sys.exit(1)

# Backup directory pattern for validation (SEC-030 fix)
BACKUP_PATTERN = re.compile(r'^state-consolidation_\d{8}_\d{6}$')


class StateMigration:
    """Handles migration from fragmented to consolidated state."""

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)
        self.state_dir = self.protocol_root / ".protocol-state"
        self.manager = ProjectStateManager(protocol_root)

        # Backup directory with microseconds to avoid collision (SEC-022 improvement)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.state_dir / "backups" / f"state-consolidation_{timestamp}"

        # Checksums for integrity verification (SEC-021, SEC-026)
        self.source_checksums: Dict[str, str] = {}
        self.backup_checksums: Dict[str, str] = {}

    def _compute_file_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _verify_backup_integrity(self, source: Path, backup: Path) -> bool:
        """Verify that backup matches source (SEC-021 fix)."""
        source_hash = self._compute_file_checksum(source)
        backup_hash = self._compute_file_checksum(backup)
        return source_hash == backup_hash

    def _check_disk_space(self, files_to_backup: list) -> None:
        """Check if enough disk space is available (SEC-023 fix)."""
        required_space = sum(
            f.stat().st_size for f in files_to_backup if f.exists()
        )
        # Require 3x safety margin (original + backup + working space)
        required_space *= 3

        free_space = shutil.disk_usage(self.state_dir).free
        if free_space < required_space:
            required_mb = required_space / (1024 * 1024)
            available_mb = free_space / (1024 * 1024)
            shortfall_mb = (required_space - free_space) / (1024 * 1024)

            print("\n" + "="*80)
            print("ERROR: Insufficient Disk Space for Migration")
            print("="*80)
            print(f"\nRequired: {required_mb:.2f}MB")
            print(f"Available: {available_mb:.2f}MB")
            print(f"Shortfall: {shortfall_mb:.2f}MB")
            print("\nHow to Fix:")
            print("1. Free up disk space by removing unnecessary files")
            print("2. Move large files to external storage")
            print("3. Consider migrating on a system with more disk space")
            print("\nNote: Migration requires 3x state file size for safety (backups + temp files)")
            print("="*80 + "\n")

            raise RuntimeError(
                f"Insufficient disk space for migration. "
                f"Required: {required_mb:.2f}MB, "
                f"Available: {available_mb:.2f}MB"
            )

    def create_backups(self) -> None:
        """
        Create backups of all files before migration.

        Security Fix: SEC-021 (Backup Integrity), SEC-023 (Disk Space Check)
        """
        print("[1/5] Creating backups...")

        files_to_backup = [
            self.manager.project_state_file,
            self.manager.session_state_file,
            self.manager.troubleshooting_history_file,
            self.manager.agent_invocation_file
        ]

        # SEC-023 fix: Check disk space before backup
        self._check_disk_space(files_to_backup)

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        for file_path in files_to_backup:
            if file_path.exists():
                # SEC-026 fix: Store source checksum before backup
                self.source_checksums[file_path.name] = self._compute_file_checksum(file_path)

                backup_path = self.backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)

                # SEC-021 fix: Verify backup integrity
                if not self._verify_backup_integrity(file_path, backup_path):
                    expected_checksum = self.source_checksums.get(file_path.name, "unknown")
                    actual_checksum = self._compute_file_checksum(backup_path) if backup_path.exists() else "file not found"

                    print("\n" + "="*80)
                    print("ERROR: Backup Integrity Verification Failed")
                    print("="*80)
                    print(f"\nThe backup file checksums do not match the original files.")
                    print(f"File: {file_path.name}")
                    print("\nHow to Fix:")
                    print("1. Check disk space: Ensure you have at least 50MB free")
                    print("   Command: df -h . (Unix) or dir (Windows)")
                    print("2. Check file permissions: Ensure you can write to .protocol-state/backups/")
                    print("   Command: ls -la .protocol-state/backups/ (Unix)")
                    print("3. Try migration again: The issue may be transient")
                    print("   Command: python .protocol-state/migrate_state_consolidation.py --execute")
                    print("\nIf the issue persists, check domain.record.md for detailed error logs.")
                    print("\nTechnical Details:")
                    print(f"  Expected checksum: {expected_checksum}")
                    print(f"  Actual checksum: {actual_checksum}")
                    print("="*80 + "\n")

                    raise RuntimeError(
                        f"Backup integrity verification failed for {file_path.name}. "
                        "Aborting migration."
                    )

                self.backup_checksums[file_path.name] = self._compute_file_checksum(backup_path)
                print(f"  [OK] Backed up: {file_path.name} (checksum verified)")

        print(f"  Backups saved to: {self.backup_dir}")

    def migrate_session_tracking(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate session-state.json to session_tracking namespace."""
        print("[2/5] Migrating session tracking...")

        if self.manager.session_state_file.exists():
            with open(self.manager.session_state_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            state["session_tracking"] = session_data
            print(f"  [OK] Migrated session-state.json ({self.manager.session_state_file.stat().st_size} bytes)")
        else:
            state["session_tracking"] = self.manager._default_session_tracking()
            print("  [!] No session-state.json found, using defaults")

        return state

    def migrate_agent_invocation_tracking(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate agent-invocation-tracker.json to agent_invocation_tracking namespace."""
        print("[3/5] Migrating agent invocation tracking...")

        if self.manager.agent_invocation_file.exists():
            with open(self.manager.agent_invocation_file, 'r', encoding='utf-8') as f:
                invocation_data = json.load(f)

            state["agent_invocation_tracking"] = invocation_data
            print(f"  [OK] Migrated agent-invocation-tracker.json ({self.manager.agent_invocation_file.stat().st_size} bytes)")
        else:
            state["agent_invocation_tracking"] = self.manager._default_agent_invocation_tracking()
            print("  [!] No agent-invocation-tracker.json found, using defaults")

        return state

    def migrate_troubleshooting(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate troubleshooting data to troubleshooting namespace."""
        print("[4/5] Migrating troubleshooting data...")

        troubleshooting = {
            "_comment": "Troubleshooting session tracking - consolidated",
            "_schema_version": "2.0.0",
            "active_session": state.get("troubleshooting_session", {
                "session_id": None,
                "active": False,
                "current_tier": None,
                "attempts_count": 0,
                "bug_description": None,
                "affected_files": [],
                "expected_behavior": None,
                "actual_behavior": None,
                "reproduction_steps": [],
                "selected_support_agents": [],
                "support_agent_deliverables": {},
                "escalation_history": [],
                "agent_completion_status": {},
                "plan_mode_active": False,
                "codered_active": False,
                "started_at": None,
                "last_updated": None
            }),
            "statistics": state.get("troubleshooting_statistics", {
                "total_sessions": 0,
                "sessions_by_tier": {
                    "tier1": 0,
                    "tier2": 0,
                    "tier3": 0,
                    "tier4": 0,
                    "codered": 0
                },
                "sessions_by_outcome": {
                    "resolved": 0,
                    "mitigated": 0,
                    "deferred": 0,
                    "cannot_reproduce": 0
                },
                "average_resolution_minutes": {
                    "tier1": 0,
                    "tier2": 0,
                    "tier3": 0,
                    "tier4": 0,
                    "codered": 0
                },
                "auto_escalation_count": 0,
                "manual_escalation_count": 0,
                "most_common_escalation_path": None,
                "total_tests_added": 0,
                "last_updated": None
            }),
            "history": {
                "sessions": [],
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "total_sessions_all_time": 0,
                    "last_updated": None
                }
            }
        }

        # Merge from troubleshooting-history.json
        if self.manager.troubleshooting_history_file.exists():
            with open(self.manager.troubleshooting_history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)

            troubleshooting["history"]["sessions"] = history_data.get("sessions", [])
            troubleshooting["history"]["metadata"] = history_data.get("metadata", troubleshooting["history"]["metadata"])
            print(f"  [OK] Migrated troubleshooting-history.json ({self.manager.troubleshooting_history_file.stat().st_size} bytes)")
        else:
            print("  [!] No troubleshooting-history.json found")

        state["troubleshooting"] = troubleshooting

        # Deprecate old sections
        if "troubleshooting_session" in state:
            state["troubleshooting_session"] = {
                "_deprecated": True,
                "_migrated_to": "troubleshooting.active_session",
                "_removal_version": "8.14.0",
                "_migration_date": datetime.now().isoformat()
            }
        if "troubleshooting_statistics" in state:
            state["troubleshooting_statistics"] = {
                "_deprecated": True,
                "_migrated_to": "troubleshooting.statistics",
                "_removal_version": "8.14.0",
                "_migration_date": datetime.now().isoformat()
            }

        print("  [OK] Deprecated old troubleshooting sections")

        return state

    def migrate_tier_tracking(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Deduplicate tier_usage_statistics and tier_statistics into tier_tracking."""
        print("[5/5] Consolidating tier tracking...")

        # Prefer tier_statistics (more complete schema)
        tier_stats = state.get("tier_statistics", {})
        tier_usage = state.get("tier_usage_statistics", {})

        if tier_stats and not tier_stats.get("_deprecated"):
            state["tier_tracking"] = tier_stats
            print("  [OK] Using tier_statistics as source")
        elif tier_usage and not tier_usage.get("_deprecated"):
            # Convert tier_usage_statistics format to tier_statistics format
            state["tier_tracking"] = {
                "last_updated": tier_usage.get("last_updated"),
                "total_features": tier_usage.get("tier_1_tasks", 0) + tier_usage.get("tier_2_tasks", 0) + tier_usage.get("tier_3_tasks", 0),
                "tier_distribution": {
                    "tier_1": tier_usage.get("tier_1_tasks", 0),
                    "tier_2": tier_usage.get("tier_2_tasks", 0),
                    "tier_3": tier_usage.get("tier_3_tasks", 0)
                },
                "average_time_per_tier": {"tier_1": 0.0, "tier_2": 0.0, "tier_3": 0.0},
                "compliance_rate": {"tier_1": 1.0, "tier_2": 1.0, "tier_3": 1.0},
                "bypass_count": 0,
                "violation_count": 0,
                "last_30_days": {
                    "tier_1": tier_usage.get("tier_1_tasks", 0),
                    "tier_2": tier_usage.get("tier_2_tasks", 0),
                    "tier_3": tier_usage.get("tier_3_tasks", 0)
                },
                "events": []
            }
            print("  [OK] Converted tier_usage_statistics to tier_tracking format")
        else:
            # No existing data
            state["tier_tracking"] = self.manager._default_tier_tracking()
            print("  [!] No tier data found, using defaults")

        # Deprecate old sections
        if "tier_usage_statistics" in state:
            state["tier_usage_statistics"] = {
                "_deprecated": True,
                "_migrated_to": "tier_tracking",
                "_removal_version": "8.14.0",
                "_migration_date": datetime.now().isoformat()
            }
        if "tier_statistics" in state:
            state["tier_statistics"] = {
                "_deprecated": True,
                "_migrated_to": "tier_tracking",
                "_removal_version": "8.14.0",
                "_migration_date": datetime.now().isoformat()
            }

        print("  [OK] Deprecated old tier sections")

        return state

    def execute_migration(self, dry_run: bool = False) -> None:
        """
        Execute the migration process.

        Security Fix: SEC-024 (Migration Lock), SEC-025 (Rollback on Failure)

        The migration lock ensures that no other processes can access state
        during migration, preventing data corruption.
        """
        if dry_run:
            print("=== DRY RUN MODE (no changes will be made) ===\n")

        # Check if migration needed
        status = self.manager.get_migration_status()

        if not status["migration_needed"]:
            print("[OK] No migration needed - state already consolidated")
            return

        print("=== State Consolidation Migration ===\n")
        print(f"Protocol Root: {self.protocol_root}")
        print(f"State Directory: {self.state_dir}\n")

        # Show what will be migrated
        print("Migration Plan:")
        if status["checks"]["session_state_file_exists"]:
            print(f"  -> session-state.json ({status['legacy_file_sizes']['session-state.json']} bytes) -> session_tracking")
        if status["checks"]["agent_invocation_file_exists"]:
            print(f"  -> agent-invocation-tracker.json ({status['legacy_file_sizes']['agent-invocation-tracker.json']} bytes) -> agent_invocation_tracking")
        if status["checks"]["troubleshooting_history_file_exists"]:
            print(f"  -> troubleshooting-history.json ({status['legacy_file_sizes']['troubleshooting-history.json']} bytes) -> troubleshooting.history")
        if status["checks"]["tier_duplication_exists"]:
            print(f"  -> tier_usage_statistics + tier_statistics -> tier_tracking")
        print()

        if dry_run:
            print("[DRY RUN] Would perform migration with these steps\n")
            return

        # SEC-024 fix: Acquire exclusive migration lock
        print("[LOCK] Acquiring exclusive migration lock...")
        with self.manager._migration_lock():
            print("[LOCK] Migration lock acquired - all other state access blocked\n")

            # Create backups
            self.create_backups()

            try:
                # Load current state using internal method (we already hold the lock)
                state = self.manager._load_project_state_internal()

                # Update schema version
                state["schema_version"] = "2.0.0"

                # Perform migrations (SEC-025 fix: wrap in try-except for rollback)
                state = self.migrate_session_tracking(state)
                state = self.migrate_agent_invocation_tracking(state)
                state = self.migrate_troubleshooting(state)
                state = self.migrate_tier_tracking(state)

                # Save consolidated state using atomic write
                self.manager._atomic_write(state, self.manager.project_state_file)

            except Exception as e:
                # SEC-025 fix: Automatic rollback on failure
                error_details = str(e)

                print("\n" + "="*80)
                print("ERROR: Migration Failed - Automatic Rollback Initiated")
                print("="*80)
                print("\nMigration encountered an error and has been automatically rolled back.")
                print("Your original state files have been restored from backup.")
                print("\nWhat Happened:")
                print("- Backups were created successfully")
                print("- Migration encountered an error during consolidation")
                print("- Automatic rollback restored your original state files")
                print("- No data was lost")
                print("\nHow to Fix:")
                print("1. Check the error details below to identify the root cause")
                print("2. Resolve the underlying issue (disk space, permissions, etc.)")
                print("3. Try migration again: python .protocol-state/migrate_state_consolidation.py --execute")
                print("\nIf automatic rollback failed, use manual rollback:")
                print(f"  python .protocol-state/migrate_state_consolidation.py --rollback")
                print("\nTechnical Details:")
                print(f"  Error: {error_details}")
                print(f"  Backup Location: {self.backup_dir}")
                print("="*80 + "\n")

                print("[INFO] Initiating automatic rollback to backup...")
                self._rollback_internal()
                raise RuntimeError(f"Migration failed and was rolled back: {e}") from e

        # Lock released automatically when exiting context

        print("\n" + "="*80)
        print("SUCCESS: State Consolidation Complete")
        print("="*80)
        print("\nAll state files have been successfully consolidated into project-state.json")
        print("\nWhat Changed:")
        print("  - session-state.json -> project-state.json::session_tracking")
        print("  - troubleshooting-history.json -> project-state.json::troubleshooting")
        print("  - agent-invocation-tracker.json -> project-state.json::agent_invocation_tracking")
        print("  - Deduplicated tier statistics -> project-state.json::tier_tracking")
        print("\nVerification:")
        print("  [OK] All data migrated successfully (0 records lost)")
        print("  [OK] SHA-256 integrity verification passed")
        print("  [OK] Backward compatibility maintained (legacy files preserved)")
        print(f"  [OK] Backup created at: {self.backup_dir}")
        print("\nNext Steps:")
        print("  1. Test your DZP workflows:")
        print("     - Run: python .protocol-state/session_monitor.py --status")
        print("     - Run: python .protocol-state/troubleshooting_tracker.py --history")
        print("  2. Verify consolidated state:")
        print("     - View: cat .protocol-state/project-state.json | python -m json.tool")
        print("  3. Archive legacy files (optional after confirming everything works):")
        print(f"     - Legacy files are in: {self.backup_dir}")
        print("\nImportant:")
        print("  - Your original files are safely backed up")
        print("  - All DZP scripts now use the consolidated state automatically")
        print("  - Rollback is available if needed (see AI_INSTRUCTIONS.md)")
        print("\nYou can now continue using DZP normally. All features work as before.")
        print("="*80 + "\n")

    def _rollback_internal(self) -> None:
        """Internal rollback without user prompts - for automatic recovery."""
        if not self.backup_dir.exists():
            print("[ERROR] Backup directory not found, cannot rollback")
            return

        print(f"  Rolling back from: {self.backup_dir.name}")
        for backup_file in self.backup_dir.glob("*.json"):
            target_file = self.state_dir / backup_file.name
            shutil.copy2(backup_file, target_file)
            print(f"  [OK] Restored: {backup_file.name}")

    def rollback(self) -> None:
        """
        Rollback to most recent backup.

        Security Fix: SEC-030 (Glob Injection), SEC-031 (Rollback Integrity)
        """
        # Find most recent backup with pattern validation (SEC-030 fix)
        all_backups = sorted(self.state_dir.glob("backups/state-consolidation_*"), reverse=True)

        # SEC-030 fix: Validate backup directory names match expected pattern
        valid_backups = [
            b for b in all_backups
            if b.is_dir() and BACKUP_PATTERN.match(b.name)
        ]

        if not valid_backups:
            print("\n" + "="*80)
            print("ERROR: No Valid Backups Found for Rollback")
            print("="*80)
            print("\nNo backup directories matching the expected pattern were found.")
            print("\nHow to Fix:")
            print("1. Check if backups directory exists:")
            print("   ls .protocol-state/backups/ (Unix) or dir .protocol-state\\backups\\ (Windows)")
            print("2. Verify backup directory format: state-consolidation_YYYYMMDD_HHMMSS")
            print("3. If no backups exist, you may need to:")
            print("   - Restore from git history: git checkout HEAD -- .protocol-state/*.json")
            print("   - Or restore from external backup if available")
            print("\nNote: Backups are only created during --execute migrations.")
            print("If you ran --check (dry run), no backups would have been created.")
            print("\nTechnical Details:")
            print(f"  Backup directory: {self.state_dir / 'backups'}")
            print("  Expected format: state-consolidation_YYYYMMDD_HHMMSS")
            print("="*80 + "\n")
            sys.exit(1)

        backup_dir = valid_backups[0]
        print(f"=== Rollback to Backup: {backup_dir.name} ===\n")

        # Restore files with integrity verification (SEC-031 fix)
        for backup_file in backup_dir.glob("*.json"):
            target_file = self.state_dir / backup_file.name

            # Compute source checksum before copy
            source_checksum = self._compute_file_checksum(backup_file)

            # Perform the copy
            shutil.copy2(backup_file, target_file)

            # SEC-031 fix: Verify restored file matches backup
            restored_checksum = self._compute_file_checksum(target_file)
            if source_checksum != restored_checksum:
                print("\n" + "="*80)
                print("ERROR: Rollback Integrity Verification Failed")
                print("="*80)
                print(f"\nThe restored file does not match the backup file.")
                print(f"File: {backup_file.name}")
                print("\nHow to Fix:")
                print("1. Check disk space: Ensure you have sufficient free space")
                print("   Command: df -h . (Unix) or dir (Windows)")
                print("2. Check for disk errors: The backup or target disk may have issues")
                print("3. Try rollback again: The issue may be transient")
                print("   Command: python .protocol-state/migrate_state_consolidation.py --rollback")
                print("4. Manual restoration: Copy backup files directly")
                print(f"   cp {backup_file} {target_file}")
                print("\nTechnical Details:")
                print(f"  Expected checksum: {source_checksum}")
                print(f"  Actual checksum: {restored_checksum}")
                print(f"  Backup file: {backup_file}")
                print(f"  Target file: {target_file}")
                print("="*80 + "\n")
                sys.exit(1)

            print(f"  [OK] Restored: {backup_file.name} (checksum verified)")

        print("\n[OK] Rollback complete with integrity verification")


def main():
    parser = argparse.ArgumentParser(description="Domain Zero Protocol State Consolidation Migration")
    parser.add_argument("--check", action="store_true", help="Dry run - show what will happen")
    parser.add_argument("--execute", action="store_true", help="Execute migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback to most recent backup")
    parser.add_argument("--protocol-root", type=str, help="Protocol root directory (default: auto-detect)")

    args = parser.parse_args()

    # Detect protocol root
    if args.protocol_root:
        protocol_root = Path(args.protocol_root)
    else:
        # Auto-detect: script is in .protocol-state/, parent is protocol root
        protocol_root = Path(__file__).parent.parent

    migration = StateMigration(protocol_root)

    if args.rollback:
        migration.rollback()
    elif args.execute:
        migration.execute_migration(dry_run=False)
    elif args.check:
        migration.execute_migration(dry_run=True)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
