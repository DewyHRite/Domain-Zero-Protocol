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
            state["tier_settings"] = _default_tier_settings(); applied += 1
        if "validation_state" not in state:
            state["validation_state"] = _default_validation_state(); applied += 1
        if "agent_registry" not in state:
            state["agent_registry"] = _default_agent_registry(); applied += 1
        return applied

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
        total = len(key_changes) + len(ts_changes)
        print(f"\nTotal changes that WOULD be applied: {total}")
        print("Run with --execute to apply (a timestamped backup is created first).")
        return 0 if total >= 0 else 1

    def execute(self) -> int:
        state = self.load()
        key_changes = self.plan_key_injections(state)
        ts_changes = self.plan_timestamp_fixes(state)
        total = len(key_changes) + len(ts_changes)
        if total == 0:
            print("[OK] State already conforms to 9.x shape. Nothing to do.")
            return 0
        backup = self._backup()
        print(f"[BACKUP] {backup}")
        applied_keys = self.apply_key_injections(state)
        applied_ts = self.apply_timestamp_fixes(state)
        self._atomic_write(state)
        print(f"[OK] Injected {applied_keys} key(s); repaired {applied_ts} timestamp(s).")
        print(f"[OK] Wrote {self.state_file}")
        print("     Verify with: python scripts/validate-protocol.py --check")
        return 0

    def rollback(self) -> int:
        backup = self.latest_backup()
        src = backup / "project-state.json"
        if not src.exists():
            print(f"[ERROR] Backup missing project-state.json: {src}", file=sys.stderr)
            return 2
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
