#!/usr/bin/env python3
"""
Domain Zero Protocol - 8.x -> 9.x State Migration Script
Version: 1.0.0
Purpose: Bring a pre-9.x project-state.json up to the v9.x required shape.

PATCH: BUG-MIGRATE-001 + BUG-SESSION-001 (part 2) - v9.3.0

The v9.x project-state schema (protocol/validation-rules.yaml) requires three
top-level keys that pre-9.x state files lack:
    - tier_settings
    - validation_state
    - agent_registry
...plus the tier_usage_statistics counters (tier_1_tasks / tier_2_tasks /
tier_3_tasks). migrate_state_consolidation.py handles the 8.12 consolidation but
does NOT add these 9.x scaffolding keys, so a freshly-upgraded install reports
validation ERRORS until they are backfilled by hand.

This migration is ADDITIVE and IDEMPOTENT:
    - It only injects keys that are ABSENT. Existing user data is never overwritten.
    - It also sanitizes naive (offset-less) timestamp strings to timezone-aware UTC
      (BUG-SESSION-001 part 2): legacy state can carry values like
      "2026-02-14T21:51:18.445590" with no UTC offset, which crash the wellbeing
      safety check (aware - naive subtraction). We rewrite those to
      "...+00:00" so legacy state can't poison the safety path after upgrade.

Usage:
    python migrate_state_9x.py --check      # Dry run - report what WOULD change
    python migrate_state_9x.py --execute    # Apply (timestamped backup first)
    python migrate_state_9x.py --rollback   # Restore most recent backup

Safety:
    - A timestamped backup is written to .protocol-state/backups/ before any write.
    - Writes are atomic (temp file + os.replace).
    - --check makes no changes.
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Naive ISO-8601 timestamp: date + time, optional fractional seconds, NO tz offset
# and NO trailing 'Z'. These are the values that crash aware/naive subtraction.
_NAIVE_TS_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$')

# Keys whose values are timestamps and therefore eligible for naive->aware repair.
_TS_KEY_SUFFIXES = ('_time', '_timestamp', '_at')
_TS_KEY_NAMES = {
    'created', 'last_updated', 'last_validation', 'last_invoked', 'last_bypass',
    'timestamp', 'date', 'start', 'end',
}

BACKUP_PREFIX = 'state-9x-migration_'
BACKUP_PATTERN = re.compile(r'^state-9x-migration_\d{8}_\d{6}(_\d{6})?$')


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_timestamp_key(key: str) -> bool:
    if key in _TS_KEY_NAMES:
        return True
    return any(key.endswith(suf) for suf in _TS_KEY_SUFFIXES)


def _default_tier_settings() -> Dict[str, Any]:
    return {
        "default_tier": 2,
        "bypass_tracking": {
            "enabled": True,
            "current_month": datetime.now(timezone.utc).strftime('%Y-%m'),
            "bypass_count": 0,
        },
    }


def _default_validation_state() -> Dict[str, Any]:
    return {"enabled": True, "last_validation": None, "drift_detected": False}


def _default_agent_registry() -> Dict[str, Any]:
    agents = [
        "gojo", "yuuji", "megumi", "nobara", "todo",
        "maki", "panda", "inumaki", "sukuna", "toji",
    ]
    return {name: {"status": "active", "last_invoked": None} for name in agents}


class StateMigration9x:
    """Additive 8.x -> 9.x state migration with naive-timestamp sanitization."""

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)
        self.state_dir = self.protocol_root / ".protocol-state"
        self.state_file = self.state_dir / "project-state.json"
        self.backups_dir = self.state_dir / "backups"

    # -- locking ------------------------------------------------------------
    def _state_lock(self):
        """
        Cross-process exclusive lock for the read-modify-write cycle.

        Reuses ProjectStateManager's `.state.lock` (the same lock every other
        state writer uses) so this migration cannot race session_monitor /
        ProjectStateManager (TOCTOU / lost-update). We intentionally keep our OWN
        raw JSON read/write (not load_project_state) because the whole point of
        this migration is to repair pre-9.x state that the manager may reject —
        but we still hold its lock for the duration. Fail-soft: if the manager is
        unavailable (minimal/broken install), fall back to a no-op lock with a note.
        """
        try:
            sys.path.insert(0, str(self.state_dir))
            from project_state_manager import ProjectStateManager  # type: ignore
            return ProjectStateManager(self.protocol_root)._exclusive_lock()
        except Exception as exc:  # noqa: BLE001 - lock is best-effort
            print(f"[!] State lock unavailable ({exc}); proceeding without cross-process lock.",
                  file=sys.stderr)
            from contextlib import nullcontext
            return nullcontext()

    # -- loading ------------------------------------------------------------
    def load(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            raise FileNotFoundError(f"project-state.json not found at {self.state_file}")
        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # -- key injection ------------------------------------------------------
    def plan_key_injections(self, state: Dict[str, Any]) -> List[str]:
        """Return list of human-readable changes for missing required keys."""
        # Only the three keys the v9.x schema REQUIRES (BUG-SCHEMA-001 removed the
        # deprecated `tier_usage_statistics` from the required set, so we do not
        # inject that legacy block on upgrade).
        changes: List[str] = []
        required = {
            "tier_settings": _default_tier_settings,
            "validation_state": _default_validation_state,
            "agent_registry": _default_agent_registry,
        }
        for key in required:
            if key not in state:
                changes.append(f"inject top-level '{key}' (seed default)")
        return changes

    def apply_key_injections(self, state: Dict[str, Any]) -> int:
        applied = 0
        if "tier_settings" not in state:
            state["tier_settings"] = _default_tier_settings()
            applied += 1
        if "validation_state" not in state:
            state["validation_state"] = _default_validation_state()
            applied += 1
        if "agent_registry" not in state:
            state["agent_registry"] = _default_agent_registry()
            applied += 1
        return applied

    # -- STATE-LEGACY: invalid enum / missing manifest sanitization -----------

    # Valid values for session_tracking...user_last_choice:
    #   null / None — initial / cleared state
    #   "continue"  — session resumed
    #   "break"     — legacy alias (kept for backward compat)
    #   "save_and_break" — value written by session_monitor.py:869-875 (SEC-CR101-002)
    _VALID_USER_LAST_CHOICE = {None, "continue", "break", "save_and_break"}

    def _find_invalid_user_last_choice(self, state: Dict[str, Any]) -> List[str]:
        """Return list of dot-paths where user_last_choice holds an invalid value.

        STATE-LEGACY: legacy state can carry user_last_choice=="pause" which is
        not a valid enum member (valid set: continue|break|null).  Collecting
        paths lets us report them in --check without mutating state.
        """
        bad: List[str] = []
        tracking = state.get("session_tracking", {})
        val = tracking.get("user_last_choice")
        if val not in self._VALID_USER_LAST_CHOICE:
            bad.append(f"session_tracking.user_last_choice = {val!r} → null")
        # Also scan nested history entries.
        for i, entry in enumerate(tracking.get("history", [])):
            v = entry.get("user_last_choice")
            if v not in self._VALID_USER_LAST_CHOICE:
                bad.append(f"session_tracking.history[{i}].user_last_choice = {v!r} → null")
        return bad

    def apply_legacy_enum_fixes(self, state: Dict[str, Any]) -> int:
        """Null out any invalid user_last_choice values. Returns count of fixes."""
        fixed = 0
        tracking = state.get("session_tracking")
        if not isinstance(tracking, dict):
            return fixed
        if tracking.get("user_last_choice") not in self._VALID_USER_LAST_CHOICE:
            tracking["user_last_choice"] = None
            fixed += 1
        for entry in tracking.get("history", []):
            if isinstance(entry, dict) and entry.get("user_last_choice") not in self._VALID_USER_LAST_CHOICE:
                entry["user_last_choice"] = None
                fixed += 1
        return fixed

    def _ensure_snapshot_manifest(self) -> str | None:
        """Create a minimal snapshot-manifest.json if it is absent.

        STATE-LEGACY: some 8.x installs omit snapshot-manifest.json entirely,
        which can cause validate-protocol to fail.  We create a minimal stub so
        the validator finds the file.  Returns a description of the action taken,
        or None if the file already existed.
        """
        manifest = self.state_dir / "snapshot-manifest.json"
        if manifest.exists():
            return None
        stub = {
            "version": "1.0.0",
            "created": _now_iso(),
            "snapshots": [],
            "_note": "Auto-created by migrate_state_9x.py STATE-LEGACY sanitizer.",
        }
        # SEC-CR101-003: atomic write prevents partial-write corruption.
        # Write to a temp file in the same directory, then os.replace() atomically.
        tmp_path_str = None
        fd, tmp_path_str = tempfile.mkstemp(
            dir=str(self.state_dir), suffix=".tmp", prefix="snapshot-manifest-"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(stub, indent=2) + "\n")
            os.replace(tmp_path_str, str(manifest))
            tmp_path_str = None  # replaced successfully — nothing to clean up
        finally:
            if tmp_path_str is not None and os.path.exists(tmp_path_str):
                os.unlink(tmp_path_str)
        return f"created missing {manifest.name} (stub)"

    # -- timestamp sanitization --------------------------------------------
    def _walk_sanitize(self, node: Any, path: str,
                       changes: List[Tuple[str, str, str]], apply: bool) -> Any:
        if isinstance(node, dict):
            for k, v in list(node.items()):
                child_path = f"{path}.{k}" if path else k
                if isinstance(v, str) and _is_timestamp_key(k) and _NAIVE_TS_RE.match(v):
                    fixed = v + "+00:00"
                    changes.append((child_path, v, fixed))
                    if apply:
                        node[k] = fixed
                else:
                    self._walk_sanitize(v, child_path, changes, apply)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                self._walk_sanitize(v, f"{path}[{i}]", changes, apply)
        return node

    def plan_timestamp_fixes(self, state: Dict[str, Any]) -> List[Tuple[str, str, str]]:
        changes: List[Tuple[str, str, str]] = []
        self._walk_sanitize(state, "", changes, apply=False)
        return changes

    def apply_timestamp_fixes(self, state: Dict[str, Any]) -> int:
        changes: List[Tuple[str, str, str]] = []
        self._walk_sanitize(state, "", changes, apply=True)
        return len(changes)

    # -- backup / write -----------------------------------------------------
    # SEC-CR101-003-DEFER (v9.9.x): extend backup/rollback to also cover snapshot-manifest.json
    def _backup(self) -> Path:
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        dest = self.backups_dir / f"{BACKUP_PREFIX}{ts}"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.state_file, dest / "project-state.json")
        return dest

    def _atomic_write(self, state: Dict[str, Any]) -> None:
        fd, tmp = tempfile.mkstemp(dir=str(self.state_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                f.write("\n")
            os.replace(tmp, self.state_file)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def latest_backup(self) -> Path:
        if not self.backups_dir.exists():
            raise FileNotFoundError("No backups directory present.")
        candidates = sorted(
            (p for p in self.backups_dir.iterdir()
             if p.is_dir() and BACKUP_PATTERN.match(p.name)),
            key=lambda p: p.name,
        )
        if not candidates:
            raise FileNotFoundError("No 9.x migration backups found.")
        return candidates[-1]

    # -- orchestration ------------------------------------------------------
    def check(self) -> int:
        state = self.load()
        key_changes = self.plan_key_injections(state)
        ts_changes = self.plan_timestamp_fixes(state)
        enum_changes = self._find_invalid_user_last_choice(state)
        manifest_missing = not (self.state_dir / "snapshot-manifest.json").exists()
        print("=== 8.x -> 9.x State Migration (DRY RUN) ===")
        print(f"State file: {self.state_file}")
        print(f"\nRequired-key injections ({len(key_changes)}):")
        for c in key_changes:
            print(f"  + {c}")
        if not key_changes:
            print("  (none - all 9.x required keys already present)")
        print(f"\nNaive timestamp repairs ({len(ts_changes)}):")
        for path, old, new in ts_changes:
            print(f"  ~ {path}: {old} -> {new}")
        if not ts_changes:
            print("  (none - no naive timestamps detected)")
        print(f"\nSTATE-LEGACY enum fixes ({len(enum_changes)}):")
        for c in enum_changes:
            print(f"  ~ {c}")
        if not enum_changes:
            print("  (none - user_last_choice values are valid)")
        print(f"\nSnapshot-manifest: {'MISSING (will create stub)' if manifest_missing else 'present'}")
        total = len(key_changes) + len(ts_changes) + len(enum_changes) + (1 if manifest_missing else 0)
        print(f"\nTotal changes that WOULD be applied: {total}")
        print("Run with --execute to apply (a timestamped backup is created first).")
        return 0 if total >= 0 else 1

    def execute(self) -> int:
        # Hold the cross-process state lock across the whole read-modify-write so a
        # concurrent state writer can't cause a lost update (CodeRabbit/coding-guideline).
        with self._state_lock():
            state = self.load()
            key_changes = self.plan_key_injections(state)
            ts_changes = self.plan_timestamp_fixes(state)
            enum_changes = self._find_invalid_user_last_choice(state)
            manifest_missing = not (self.state_dir / "snapshot-manifest.json").exists()
            total = len(key_changes) + len(ts_changes) + len(enum_changes) + (1 if manifest_missing else 0)
            if total == 0:
                print("[OK] State already conforms to 9.x shape. Nothing to do.")
                return 0
            backup = self._backup()
            print(f"[BACKUP] {backup}")
            applied_keys = self.apply_key_injections(state)
            applied_ts = self.apply_timestamp_fixes(state)
            applied_enum = self.apply_legacy_enum_fixes(state)
            self._atomic_write(state)
        # Manifest is created outside the state lock (it's a separate file).
        manifest_action = self._ensure_snapshot_manifest()
        print(f"[OK] Injected {applied_keys} key(s); repaired {applied_ts} timestamp(s); "
              f"fixed {applied_enum} enum value(s).")
        if manifest_action:
            print(f"[OK] {manifest_action}")
        print(f"[OK] Wrote {self.state_file}")
        print("     Verify with: python scripts/validate-protocol.py --check")
        return 0

    def rollback(self) -> int:
        backup = self.latest_backup()
        src = backup / "project-state.json"
        if not src.exists():
            print(f"[ERROR] Backup missing project-state.json: {src}", file=sys.stderr)
            return 2
        with self._state_lock():
            shutil.copy2(src, self.state_file)
        print(f"[OK] Rolled back project-state.json from {backup}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Domain Zero 8.x -> 9.x state migration")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Dry run (no changes)")
    group.add_argument("--execute", action="store_true", help="Apply migration")
    group.add_argument("--rollback", action="store_true", help="Restore latest backup")
    parser.add_argument("--root", default=None,
                        help="Protocol root (default: parent of this script's dir)")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    migration = StateMigration9x(root)

    try:
        if args.check:
            return migration.check()
        if args.execute:
            return migration.execute()
        if args.rollback:
            return migration.rollback()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 - top-level guard for CLI
        print(f"[CRITICAL] Migration failed: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
