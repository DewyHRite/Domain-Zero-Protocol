#!/usr/bin/env python3
"""
Domain Zero Protocol - Centralized Project State Manager
Version: 1.1.0
Purpose: Unified state access with atomic operations and backward compatibility

PATCH: PATCH-STATE-001 (State File Consolidation)
SECURITY FIX: SEC-016, SEC-019 (Race Condition Remediation)
Part of: v8.12.0

This module provides a centralized interface for reading and writing all
project state data, with automatic fallback to legacy files during migration.

Security Features:
- Cross-platform file locking (Windows msvcrt, Unix fcntl)
- Atomic read-modify-write operations with exclusive locks
- Lock timeout with retry logic to prevent deadlocks
- Migration lock support for safe concurrent access during migration
"""

import json
import os
import sys
import tempfile
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

# ISS-083: local write-attestation (fail-soft; module lives alongside this
# one in .protocol-state/). Absence must never break state read/write.
try:
    from attestation import record_write as _attest_record_write
    _ATTESTATION_AVAILABLE = True
except ImportError:
    _ATTESTATION_AVAILABLE = False

# Lock configuration constants
LOCK_TIMEOUT_SECONDS = 30
LOCK_RETRY_DELAY_SECONDS = 0.1
LOCK_MAX_RETRIES = 300  # 30 seconds / 0.1 second delay


class ProjectStateManager:
    """
    Centralized manager for all Domain Zero Protocol state files.

    Provides:
    - Atomic read/write with file locking
    - Namespace-based access (session_tracking, tier_tracking, troubleshooting, agent_invocation_tracking)
    - Backward compatibility fallback to legacy files
    - Validation integration
    - Migration detection and warnings
    """

    def __init__(self, protocol_root: Path):
        """
        Initialize state manager.

        Args:
            protocol_root: Path to project root (parent of .protocol-state/)
        """
        self.protocol_root = Path(protocol_root)
        self.state_dir = self.protocol_root / ".protocol-state"

        # Primary unified state file
        self.project_state_file = self.state_dir / "project-state.json"

        # Legacy files (for fallback during migration)
        self.session_state_file = self.state_dir / "session-state.json"
        self.troubleshooting_history_file = self.state_dir / "troubleshooting-history.json"
        self.agent_invocation_file = self.state_dir / "agent-invocation-tracker.json"

        # Platform detection
        self.is_windows = platform.system() == "Windows"

        # Lock file for exclusive state access (SEC-016, SEC-019)
        self.lock_file_path = self.state_dir / ".state.lock"

        # Migration lock file (SEC-024)
        self.migration_lock_path = self.state_dir / ".migration.lock"

    @contextmanager
    def _file_lock(self, file_path: Path, mode: str = 'r'):
        """
        Cross-platform file locking context manager.

        Args:
            file_path: Path to lock
            mode: File open mode ('r' or 'w')

        Yields:
            Open file handle with exclusive lock

        Note: This method is kept for backward compatibility but
        _exclusive_lock() should be used for atomic operations.
        """
        file_handle = None
        lock_acquired = False
        lock_size = None  # Store lock size for Windows unlock

        try:
            file_handle = open(file_path, mode, encoding='utf-8')

            # Retry loop with timeout (SEC-009 fix)
            for attempt in range(LOCK_MAX_RETRIES):
                try:
                    if self.is_windows:
                        import msvcrt
                        # Lock entire file, not just 1 byte (SEC-008 fix)
                        # Seek to beginning and lock a large region
                        file_handle.seek(0, 2)  # Seek to end to get size
                        file_size = file_handle.tell()
                        file_handle.seek(0)  # Seek back to beginning
                        lock_size = max(file_size, 1024 * 1024)  # At least 1MB, store for unlock
                        msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, lock_size)
                    else:
                        import fcntl
                        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    lock_acquired = True
                    break
                except (IOError, OSError) as e:
                    if attempt < LOCK_MAX_RETRIES - 1:
                        time.sleep(LOCK_RETRY_DELAY_SECONDS)
                    else:
                        raise TimeoutError(
                            f"Could not acquire file lock on {file_path} after "
                            f"{LOCK_TIMEOUT_SECONDS} seconds"
                        ) from e

            yield file_handle

        except Exception:
            # SEC-010 fix: Ensure file is closed on lock acquisition failure
            if file_handle and not lock_acquired:
                file_handle.close()
            raise

        finally:
            # CRITICAL: Unlock BEFORE closing on Windows
            if file_handle and lock_acquired:
                try:
                    if self.is_windows:
                        import msvcrt
                        # Use stored lock_size from acquisition (fixes fragility bug)
                        file_handle.seek(0)
                        msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, lock_size)
                    else:
                        import fcntl
                        fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
                except (OSError, ValueError):
                    # File already closed or lock already released - safe to ignore
                    pass
                finally:
                    file_handle.close()

    @contextmanager
    def _exclusive_lock(self):
        """
        Acquire exclusive lock for atomic read-modify-write operations.

        This lock ensures that the entire read-modify-write cycle is atomic,
        preventing race conditions between concurrent processes.

        Security Fix: SEC-016, SEC-019

        Yields:
            None (lock is held during context)

        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        # Check for migration lock first - block during migration (SEC-024)
        if self.migration_lock_path.exists():
            raise RuntimeError(
                "Migration in progress. State access blocked until migration completes. "
                "Wait for migration to finish or check for stale lock file."
            )

        lock_file = None
        lock_acquired = False

        try:
            # Create lock file if it doesn't exist
            self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Open lock file (create if not exists)
            lock_file = open(self.lock_file_path, 'w', encoding='utf-8')

            # Retry loop with timeout
            for attempt in range(LOCK_MAX_RETRIES):
                try:
                    if self.is_windows:
                        import msvcrt
                        # Use LK_NBLCK for non-blocking, retry manually
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    lock_acquired = True
                    break
                except (IOError, OSError):
                    if attempt < LOCK_MAX_RETRIES - 1:
                        time.sleep(LOCK_RETRY_DELAY_SECONDS)
                    else:
                        raise TimeoutError(
                            f"Could not acquire exclusive state lock after "
                            f"{LOCK_TIMEOUT_SECONDS} seconds. Another process may be "
                            "holding the lock."
                        )

            # Write PID to lock file for debugging
            lock_file.write(f"{os.getpid()}\n{datetime.now().isoformat()}\n")
            lock_file.flush()

            yield

        finally:
            if lock_file:
                try:
                    if lock_acquired:
                        if self.is_windows:
                            import msvcrt
                            lock_file.seek(0)
                            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                        else:
                            import fcntl
                            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                except (OSError, ValueError):
                    pass
                finally:
                    lock_file.close()

    @contextmanager
    def _migration_lock(self):
        """
        Acquire migration lock that blocks all other state access.

        This lock is used during migration to prevent data corruption
        from concurrent access by other processes (session_monitor,
        troubleshooting_tracker, etc.).

        Security Fix: SEC-024

        Yields:
            None (lock is held during context)

        Raises:
            TimeoutError: If lock cannot be acquired within timeout
            RuntimeError: If migration is already in progress
        """
        lock_file = None
        lock_acquired = False

        try:
            # Check for existing migration lock
            if self.migration_lock_path.exists():
                raise RuntimeError(
                    "Migration already in progress. Another migration process "
                    "holds the lock. Wait for it to complete or remove stale lock."
                )

            # Create migration lock directory if needed
            self.migration_lock_path.parent.mkdir(parents=True, exist_ok=True)

            # Create and lock migration file
            lock_file = open(self.migration_lock_path, 'w', encoding='utf-8')

            # Acquire lock with retry
            for attempt in range(LOCK_MAX_RETRIES):
                try:
                    if self.is_windows:
                        import msvcrt
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    lock_acquired = True
                    break
                except (IOError, OSError):
                    if attempt < LOCK_MAX_RETRIES - 1:
                        time.sleep(LOCK_RETRY_DELAY_SECONDS)
                    else:
                        raise TimeoutError(
                            f"Could not acquire migration lock after "
                            f"{LOCK_TIMEOUT_SECONDS} seconds."
                        )

            # Write migration info
            lock_file.write(f"Migration started: {datetime.now().isoformat()}\n")
            lock_file.write(f"PID: {os.getpid()}\n")
            lock_file.flush()

            yield

        finally:
            if lock_file:
                try:
                    if lock_acquired:
                        if self.is_windows:
                            import msvcrt
                            lock_file.seek(0)
                            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                        else:
                            import fcntl
                            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                except (OSError, ValueError):
                    pass
                finally:
                    lock_file.close()

            # Remove migration lock file
            try:
                if self.migration_lock_path.exists():
                    self.migration_lock_path.unlink()
            except OSError:
                pass

    def _atomic_write(self, data: Dict[str, Any], target_file: Path) -> None:
        """
        Atomically write JSON data to file.

        Args:
            data: Dictionary to write
            target_file: Target file path

        Security Fix: SEC-014 (fsync before replace), SEC-015 (temp file cleanup)

        Note: This method should be called within an _exclusive_lock() context
        to ensure atomic read-modify-write operations.
        """
        tmp_path = None
        try:
            # Write to temp file first
            with tempfile.NamedTemporaryFile(
                'w',
                encoding='utf-8',
                delete=False,
                dir=target_file.parent,
                suffix='.tmp'
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                # SEC-014 fix: Flush and fsync before atomic replace
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                tmp_path = tmp_file.name

            # Atomic replace
            os.replace(tmp_path, target_file)
        except Exception:
            # SEC-015 fix: Clean up temp file on error
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise

        # ISS-083: stamp a local write-attestation for this sanctioned
        # write. This runs AFTER the write has already succeeded above and
        # is strictly best-effort observability for drift detection -- any
        # failure here must never surface as a failure of the state write
        # itself (hence the isolated try/except and no re-raise).
        self._attest_write(target_file)

    def _attest_write(self, target_file: Path) -> None:
        """
        Best-effort ISS-083 write attestation for a just-completed atomic
        write to *target_file*.

        Reads back the exact bytes now on disk (rather than re-serializing
        the in-memory dict) so the recorded content hash always matches
        reality, and stamps a signed ledger entry keyed by the file's
        basename -- the same key scripts/validate-protocol.py's drift
        detection uses (Path(result.file).name).

        Never raises: attestation is advisory metadata for drift detection,
        not a correctness requirement of the state write itself (which has
        already completed by the time this runs).

        CodeRabbit PR#108: when `_ATTESTATION_AVAILABLE` is False (module
        absent), we return SILENTLY -- that's an expected, common
        deployment shape (attestation.py just isn't present) and not worth
        warning about on every write. When attestation IS available but a
        runtime failure occurs during the actual stamp attempt (corrupt
        ledger, permission error, unexpected exception, etc.), that's a
        DIFFERENT and more actionable condition -- print a concise stderr
        warning identifying the target file and the exception so an
        operator can tell "module absent" (silent, expected) apart from
        "attestation attempted and failed" (warned, worth investigating).
        Still fully fail-soft: never re-raises, never blocks the caller.

        SEC-ATTEST-PSM-001 (Megumi, P2, CWE-532): REDACTED -- only the
        file's basename (never the full `target_file` path) and the
        exception's TYPE name (never `str(e)`) are printed. For the
        OSError family in particular, `str(e)` commonly embeds the full
        absolute path that failed (e.g. `C:\\Users\\<user>\\...`), which
        would leak the local username/path layout to stderr/CI logs/
        transcripts. Mirrors the same redaction already applied to
        `session_monitor.py::_attest_write` (Megumi @approved there).
        """
        if not _ATTESTATION_AVAILABLE:
            return
        try:
            content = target_file.read_bytes()
            _attest_record_write(self.state_dir, target_file.name, content, writer="ProjectStateManager")
        except Exception as e:
            print(
                f"[WARN] Write attestation failed for {target_file.name} ({type(e).__name__})",
                file=sys.stderr,
            )

    def load_project_state(self) -> Dict[str, Any]:
        """
        Load complete project state with file locking.

        Returns:
            Complete project state dictionary

        Security Fix: SEC-013 (TOCTOU race condition)
        """
        # SEC-013 fix: Remove exists check, handle FileNotFoundError from open
        try:
            with self._file_lock(self.project_state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"project-state.json not found: {self.project_state_file}")

    def _load_project_state_internal(self) -> Dict[str, Any]:
        """
        Internal load without locking - for use within _exclusive_lock context.

        Returns:
            Complete project state dictionary

        Note: Creates default state on fresh install (fixes FileNotFoundError on update methods)
        """
        try:
            with open(self.project_state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fresh install - create default state structure
            return {
                "protocol_version": "8.12.0",
                "session_tracking": {},
                "troubleshooting": {"sessions": [], "metadata": {"total_sessions_all_time": 0}},
                "agent_invocation_tracking": {},
                "tier_tracking": {}
            }

    def save_project_state(self, state: Dict[str, Any]) -> None:
        """
        Save complete project state atomically with exclusive lock.

        Args:
            state: Complete project state dictionary

        Security Fix: SEC-016 (No lock during save operation)

        Note: This method acquires an exclusive lock before writing.
        For read-modify-write operations, use the update_* methods instead
        which hold the lock through the entire operation.
        """
        with self._exclusive_lock():
            self._atomic_write(state, self.project_state_file)

    # =========================================================================
    # NAMESPACE-SPECIFIC METHODS
    # =========================================================================

    def get_session_tracking(self) -> Dict[str, Any]:
        """
        Get session tracking data with fallback to legacy file.

        Returns:
            Session tracking namespace data

        Security Fix: SEC-017 (legacy file read with lock)
        """
        state = self.load_project_state()

        # Check for new consolidated format
        if "session_tracking" in state and not state["session_tracking"].get("_deprecated"):
            return state["session_tracking"]

        # Fallback to legacy session-state.json with locking (SEC-017 fix)
        if self.session_state_file.exists():
            print(f"Tell /Sukuna[WARN] Using legacy session-state.json (migration pending)")
            with self._file_lock(self.session_state_file, 'r') as f:
                legacy_data = json.load(f)
            return legacy_data

        # Return empty structure
        return self._default_session_tracking()

    def update_session_tracking(self, session_data: Dict[str, Any]) -> None:
        """
        Update session tracking data atomically.

        Args:
            session_data: Updated session tracking data

        Security Fix: SEC-019 (Read-modify-write race condition)
        Lock is held through entire read-modify-write cycle.
        """
        with self._exclusive_lock():
            state = self._load_project_state_internal()
            state["session_tracking"] = session_data
            state["session_tracking"]["last_updated"] = datetime.now().isoformat()
            self._atomic_write(state, self.project_state_file)

    def get_agent_invocation_tracking(self) -> Dict[str, Any]:
        """
        Get agent invocation tracking with fallback to legacy file.

        Returns:
            Agent invocation tracking namespace data

        Security Fix: SEC-017 (legacy file read with lock)
        """
        state = self.load_project_state()

        # Check for new consolidated format
        if "agent_invocation_tracking" in state and not state["agent_invocation_tracking"].get("_deprecated"):
            return state["agent_invocation_tracking"]

        # Fallback to legacy agent-invocation-tracker.json with locking (SEC-017 fix)
        if self.agent_invocation_file.exists():
            print(f"Tell /Sukuna[WARN] Using legacy agent-invocation-tracker.json (migration pending)")
            with self._file_lock(self.agent_invocation_file, 'r') as f:
                legacy_data = json.load(f)
            return legacy_data

        # Return empty structure
        return self._default_agent_invocation_tracking()

    def update_agent_invocation_tracking(self, invocation_data: Dict[str, Any]) -> None:
        """
        Update agent invocation tracking atomically.

        Args:
            invocation_data: Updated agent invocation data

        Security Fix: SEC-019 (Read-modify-write race condition)
        Lock is held through entire read-modify-write cycle.
        """
        with self._exclusive_lock():
            state = self._load_project_state_internal()
            state["agent_invocation_tracking"] = invocation_data
            state["agent_invocation_tracking"]["_last_updated"] = datetime.now().isoformat()
            self._atomic_write(state, self.project_state_file)

    def get_troubleshooting(self) -> Dict[str, Any]:
        """
        Get troubleshooting data with fallback to legacy file and old sections.

        Returns:
            Troubleshooting namespace data

        Security Fix: SEC-017 (legacy file read with lock)
        """
        state = self.load_project_state()

        # Check for new consolidated format
        if "troubleshooting" in state and not state["troubleshooting"].get("_deprecated"):
            return state["troubleshooting"]

        # Build from legacy sections + file
        troubleshooting_data = {
            "_comment": "Troubleshooting session tracking - consolidated",
            "_schema_version": "2.0.0",
            "active_session": state.get("troubleshooting_session", {}),
            "statistics": state.get("troubleshooting_statistics", {}),
            "history": {
                "sessions": [],
                "metadata": {}
            }
        }

        # Merge history from troubleshooting-history.json with locking (SEC-017 fix)
        if self.troubleshooting_history_file.exists():
            print(f"Tell /Sukuna[WARN] Using legacy troubleshooting-history.json (migration pending)")
            with self._file_lock(self.troubleshooting_history_file, 'r') as f:
                legacy_history = json.load(f)
            troubleshooting_data["history"] = {
                "sessions": legacy_history.get("sessions", []),
                "metadata": legacy_history.get("metadata", {})
            }

        return troubleshooting_data

    def update_troubleshooting(self, troubleshooting_data: Dict[str, Any]) -> None:
        """
        Update troubleshooting data atomically.

        Args:
            troubleshooting_data: Updated troubleshooting data

        Security Fix: SEC-019 (Read-modify-write race condition)
        Lock is held through entire read-modify-write cycle.
        """
        with self._exclusive_lock():
            state = self._load_project_state_internal()
            state["troubleshooting"] = troubleshooting_data
            if "statistics" in troubleshooting_data:
                state["troubleshooting"]["statistics"]["last_updated"] = datetime.now().isoformat()
            self._atomic_write(state, self.project_state_file)

    def get_tier_tracking(self) -> Dict[str, Any]:
        """
        Get tier tracking data (deduplicated from tier_usage_statistics and tier_statistics).

        Returns:
            Tier tracking namespace data
        """
        state = self.load_project_state()

        # Check for new consolidated format
        if "tier_tracking" in state and not state["tier_tracking"].get("_deprecated"):
            return state["tier_tracking"]

        # Merge from old duplicated sections
        tier_stats = state.get("tier_statistics", {})
        tier_usage = state.get("tier_usage_statistics", {})

        # Prefer tier_statistics (more complete), fallback to tier_usage_statistics
        if tier_stats and not tier_stats.get("_deprecated"):
            return tier_stats
        elif tier_usage and not tier_usage.get("_deprecated"):
            return tier_usage
        else:
            return self._default_tier_tracking()

    def update_tier_tracking(self, tier_data: Dict[str, Any]) -> None:
        """
        Update tier tracking data atomically.

        Args:
            tier_data: Updated tier tracking data

        Security Fix: SEC-019 (Read-modify-write race condition)
        Lock is held through entire read-modify-write cycle.
        """
        with self._exclusive_lock():
            state = self._load_project_state_internal()
            state["tier_tracking"] = tier_data
            state["tier_tracking"]["last_updated"] = datetime.now().isoformat()
            self._atomic_write(state, self.project_state_file)

    # =========================================================================
    # DEFAULT STRUCTURES
    # =========================================================================

    def _default_session_tracking(self) -> Dict[str, Any]:
        """Return default session tracking structure."""
        return {
            "_comment": "Work session state tracking - migrated from session-state.json",
            "_schema_version": "1.0.0",
            "current_session": {
                "session_id": None,
                "session_active": False,
                "start_time": None,
                "last_interaction_time": None,
                "last_alert_time": None,
                "alert_count": 0,
                "escalation_level": 0,
                "user_last_choice": None,
                "break_acknowledged": False,
                "high_risk_operations_blocked": False
            },
            "session_metrics": {
                "total_duration_minutes": 0,
                "continuous_work_minutes": 0,
                "break_timestamps": [],
                "total_breaks": 0,
                "alerts_issued": 0,
                "alerts_ignored": 0,
                "continues_chosen": 0,
                "breaks_chosen": 0
            },
            "thresholds": {
                "initial_alert_minutes": 240,
                "escalated_alert_minutes": 45,
                "critical_session_minutes": 360,
                "max_continuous_minutes": 480,
                "late_night_hour": 22,
                "minimum_break_minutes": 15
            },
            "session_history": [],
            "last_updated": None,
            "protocol_version": "8.12.0"
        }

    def _default_agent_invocation_tracking(self) -> Dict[str, Any]:
        """Return default agent invocation tracking structure."""
        return {
            "_comment": "Agent invocation patterns - migrated from agent-invocation-tracker.json",
            "_purpose": "Track agent invocation patterns to detect session monitoring bypass",
            "_version": "1.0.0",
            "_last_updated": None,
            "tracking_enabled": True,
            "invocations": {
                "gojo": {"total_count": 0, "last_invocation": None, "description": "Mission Control & Protocol Guardian"},
                "yuuji": {"total_count": 0, "direct_invocations": 0, "routed_invocations": 0, "last_invocation": None, "description": "Implementation Specialist"},
                "megumi": {"total_count": 0, "direct_invocations": 0, "routed_invocations": 0, "last_invocation": None, "description": "Security & Performance Analyst"},
                "nobara": {"total_count": 0, "direct_invocations": 0, "routed_invocations": 0, "last_invocation": None, "description": "Creative Strategy & UX Specialist"},
                "todo": {"total_count": 0, "direct_invocations": 0, "routed_invocations": 0, "last_invocation": None, "description": "Database & Backend Specialist"},
                "maki": {"total_count": 0, "direct_invocations": 0, "routed_invocations": 0, "last_invocation": None, "description": "Performance Optimization Specialist"},
                "panda": {"total_count": 0, "direct_invocations": 0, "routed_invocations": 0, "last_invocation": None, "description": "Build & Integration Specialist"},
                "inumaki": {"total_count": 0, "direct_invocations": 0, "routed_invocations": 0, "last_invocation": None, "description": "API & Communication Specialist"},
                "sukuna": {"total_count": 0, "direct_invocations": 0, "last_invocation": None, "description": "System Update Adversary"}
            },
            "bypass_detection": {
                "enabled": True,
                "threshold_minutes": 30,
                "bypass_alerts": []
            },
            "session_correlation": {
                "enabled": True,
                "track_duration_at_invocation": True,
                "_comment": "Correlates agent invocations with session duration"
            }
        }

    def _default_tier_tracking(self) -> Dict[str, Any]:
        """Return default tier tracking structure."""
        return {
            "_comment": "Unified tier statistics - replaces tier_usage_statistics and tier_statistics",
            "last_updated": datetime.now().isoformat(),
            "total_features": 0,
            "tier_distribution": {
                "tier_1": 0,
                "tier_2": 0,
                "tier_3": 0
            },
            "average_time_per_tier": {
                "tier_1": 0.0,
                "tier_2": 0.0,
                "tier_3": 0.0
            },
            "compliance_rate": {
                "tier_1": 1.0,
                "tier_2": 1.0,
                "tier_3": 1.0
            },
            "bypass_count": 0,
            "violation_count": 0,
            "last_30_days": {
                "tier_1": 0,
                "tier_2": 0,
                "tier_3": 0
            },
            "events": []
        }

    # =========================================================================
    # MIGRATION SUPPORT
    # =========================================================================

    def is_migration_needed(self) -> bool:
        """
        Check if state consolidation migration is needed.

        Returns:
            True if migration required, False otherwise
        """
        state = self.load_project_state()

        # Check for new namespaces
        has_session_tracking = "session_tracking" in state and not state.get("session_tracking", {}).get("_deprecated")
        has_agent_invocation = "agent_invocation_tracking" in state and not state.get("agent_invocation_tracking", {}).get("_deprecated")
        has_tier_tracking = "tier_tracking" in state and not state.get("tier_tracking", {}).get("_deprecated")
        has_troubleshooting = "troubleshooting" in state and not state.get("troubleshooting", {}).get("_deprecated")

        # Check for old files
        has_old_session_file = self.session_state_file.exists()
        has_old_troubleshooting_file = self.troubleshooting_history_file.exists()
        has_old_agent_invocation_file = self.agent_invocation_file.exists()

        # Check for old sections
        has_tier_duplication = ("tier_usage_statistics" in state or "tier_statistics" in state) and not has_tier_tracking

        # Migration needed if:
        # 1. Old files exist OR
        # 2. New namespaces missing OR
        # 3. Tier duplication exists
        return (
            has_old_session_file or
            has_old_troubleshooting_file or
            has_old_agent_invocation_file or
            not has_session_tracking or
            not has_agent_invocation or
            not has_tier_tracking or
            not has_troubleshooting or
            has_tier_duplication
        )

    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get detailed migration status for reporting.

        Returns:
            Migration status dictionary with details
        """
        state = self.load_project_state()

        return {
            "migration_needed": self.is_migration_needed(),
            "checks": {
                "session_tracking_present": "session_tracking" in state and not state.get("session_tracking", {}).get("_deprecated"),
                "agent_invocation_present": "agent_invocation_tracking" in state and not state.get("agent_invocation_tracking", {}).get("_deprecated"),
                "tier_tracking_present": "tier_tracking" in state and not state.get("tier_tracking", {}).get("_deprecated"),
                "troubleshooting_present": "troubleshooting" in state and not state.get("troubleshooting", {}).get("_deprecated"),
                "session_state_file_exists": self.session_state_file.exists(),
                "troubleshooting_history_file_exists": self.troubleshooting_history_file.exists(),
                "agent_invocation_file_exists": self.agent_invocation_file.exists(),
                "tier_duplication_exists": ("tier_usage_statistics" in state or "tier_statistics" in state) and "tier_tracking" not in state
            },
            "legacy_file_sizes": {
                "session-state.json": self.session_state_file.stat().st_size if self.session_state_file.exists() else 0,
                "troubleshooting-history.json": self.troubleshooting_history_file.stat().st_size if self.troubleshooting_history_file.exists() else 0,
                "agent-invocation-tracker.json": self.agent_invocation_file.stat().st_size if self.agent_invocation_file.exists() else 0
            }
        }


# Usage example
if __name__ == "__main__":
    import sys

    # Detect protocol root (script is in .protocol-state/, parent is root)
    protocol_root = Path(__file__).parent.parent

    manager = ProjectStateManager(protocol_root)

    # Check migration status
    status = manager.get_migration_status()

    print("=== Domain Zero Protocol - State Manager ===\n")
    print(f"Protocol Root: {protocol_root}")
    print(f"Migration Needed: {status['migration_needed']}\n")

    if status['migration_needed']:
        print("Migration Checks:")
        for check, result in status['checks'].items():
            symbol = "[X]" if result else "[ ]"
            print(f"  {symbol} {check}")

        print("\nLegacy File Sizes:")
        for file, size in status['legacy_file_sizes'].items():
            if size > 0:
                print(f"  {file}: {size} bytes")

        print("\nRun migration: python .protocol-state/migrate_state_consolidation.py --execute")
    else:
        print("[OK] State already consolidated - no migration needed")
