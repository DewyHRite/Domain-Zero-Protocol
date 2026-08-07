#!/usr/bin/env python3
"""
Domain Zero Protocol - Work Session Monitoring System
Version: 9.3.0
Purpose: Actual implementation of work session tracking and safety alerts

This module provides REAL enforcement of work session monitoring, replacing
the prompt-based theater identified by Sukuna's red team assessment.

Usage:
    From Gojo agent: Read and execute functions to track session state
    From verification scripts: Validate session health and issue alerts
"""

import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import zoneinfo
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# SEC-TRANSFER-9.11.0-005 (P3, CWE-22): session ids flow into filenames
# (handoff archive copies) and must be restricted to a safe charset BEFORE
# any path is built anywhere in this module.
_SESSION_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')


def _is_valid_session_id(value: Optional[str]) -> bool:
    """True only for a non-empty string matching the safe session-id charset
    (letters, digits, underscore, hyphen). Rejects None, empty strings, and
    anything containing path separators / traversal sequences / other
    metacharacters -- e.g. '../../evil' is rejected outright."""
    return bool(value) and bool(_SESSION_ID_PATTERN.fullmatch(value))


# IMPL-001 remediation (Toji audit 2026-07-29): the ordered set of required
# transfer steps that must ALL be recorded complete in the .INCOMPLETE marker
# before it is cleared. Previously handoff_write() cleared the marker on its
# own success -- before the mandatory end-snapshot step even ran -- so a
# failing snapshot left no durable evidence of the incomplete transfer. See
# SessionMonitor._mark_transfer_step_complete() / transfer_finalize().
_TRANSFER_REQUIRED_STEPS = ("handoff-write", "end-snapshot")

# PATCH-STATE-001: Import centralized state manager
try:
    from project_state_manager import ProjectStateManager
    STATE_MANAGER_AVAILABLE = True
except ImportError:
    STATE_MANAGER_AVAILABLE = False
    # Silent fallback to legacy file I/O for backward compatibility

# v9.12.0 A2 phase (b) (ADR docs/superpowers/specs/2026-08-04-clock-authority-adr.md,
# governing audit audits/2026-08-01-toji-session-time-authority-claude-codex.md):
# the D1-D4 clock-authority primitives, wired into every datetime.now()/bare
# astimezone() call site below (CODE-001/DESIGN-001/IMPL-002). Deliberately
# NOT wrapped fail-soft like ProjectStateManager/attestation above -- both
# modules are core v9.12.0 files always present alongside this one, and
# load_timing_policy() raising InvalidTimezoneConfigError on a genuinely
# malformed `user.timezone` is the INTENDED behavior (ADR D4.1.1: a hard,
# surfaced config error, never a silent fallback).
from time_provider import TimeProvider  # noqa: E402
from timing_policy import load_timing_policy  # noqa: E402

# v9.12.0 A4 (ADR D5/D6.4/D6.5, Toji gate 4; governing audit findings AI-001
# HIGH and IMPL-001 MEDIUM): the D5 time-envelope builder and the D6.5 alert
# reason-code vocabulary. Same "always present, never fail-soft-wrapped"
# posture as the time_provider/timing_policy imports above -- these are core
# v9.12.0 files always present alongside this one.
from time_envelope import (  # noqa: E402
    ENVELOPE_SCHEMA_VERSION,
    AlertReason,
    EnvelopeStatus,
    EnvelopeStatusReason,
    SessionBoundary,
    build_envelope_safe,
)

# ISS-083: local write-attestation (fail-soft; module lives alongside this
# one in .protocol-state/). Absence must never break session monitoring.
try:
    from attestation import record_write as _attest_record_write
    _ATTESTATION_AVAILABLE = True
except ImportError:
    _ATTESTATION_AVAILABLE = False

# Session duration limits (PATCH-SEC-005 - SEC-DZP-008 remediation)
MAX_BREAK_DURATION = 480  # 8 hours
MIN_BREAK_DURATION = 1    # 1 minute
MAX_SESSION_DURATION = 1440  # 24 hours

# Cortex index.lock staleness threshold (seconds).
# An orphaned lock older than this is reaped so automatic re-indexing is never
# permanently blocked.  600 s is far above any real index run (hooks cap at 30 s).
_CORTEX_LOCK_STALE_SECONDS = 600


def _lock_is_stale(lock_path: Path, now: Optional[float] = None) -> bool:
    """Return True if *lock_path* exists and its mtime is older than
    _CORTEX_LOCK_STALE_SECONDS.

    Args:
        lock_path: Path to the lock file being tested.
        now:       Current epoch time; defaults to time.time().  Inject for tests.

    Returns:
        True  — lock exists AND age > threshold (stale, safe to reap).
        False — lock does not exist, OR lock is fresh (another indexer running).
    """
    import time as _time
    try:
        if not lock_path.exists():
            return False
        mtime = lock_path.stat().st_mtime
        age = (now if now is not None else _time.time()) - mtime
        return age > _CORTEX_LOCK_STALE_SECONDS
    except Exception:
        return False


def _parse_utc(timestamp: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO-8601 timestamp string and return a timezone-AWARE datetime in UTC.

    BUG-SESSION-001 (v9.3.0): Centralized timestamp parsing for the safety path.
    Legacy / pre-9.x state files (and externally edited state) can carry naive
    timestamps with no UTC offset (e.g. "2026-02-14T21:51:18.445590"). Subtracting
    a naive datetime from an aware `datetime.now(timezone.utc)` raises
    `TypeError: can't subtract offset-naive and offset-aware datetimes`, which used
    to crash `check_alert_needed()` and silently DISABLE the wellbeing safety check.

    This helper normalizes every parse: naive -> assume UTC; aware -> convert to UTC.
    Returns None if the string is missing or unparseable (callers treat None as
    "no usable timestamp" rather than crashing).

    Note: `datetime.fromisoformat()` on Python 3.11+ accepts a trailing 'Z'; on
    older versions it does not, so we normalize 'Z' to '+00:00' defensively.
    """
    if not timestamp:
        return None
    try:
        normalized = timestamp.strip()
        if normalized.endswith('Z'):
            normalized = normalized[:-1] + '+00:00'
        dt = datetime.fromisoformat(normalized)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def _timestamp_is_naive(timestamp: Optional[str]) -> bool:
    """v9.12.0 A6 (ADR D8.5 read-side gating, SEC-CLOCKADR-9.12.0-021):
    True iff `timestamp` is a non-empty, syntactically parseable ISO-8601
    string with NO UTC offset (naive). A purely SYNTACTIC check -- it never
    coerces or normalizes, unlike `_parse_utc()` -- so it can run BEFORE
    that helper's own naive -> assume-UTC tolerance is applied, to decide
    whether this specific value needs D8.5 anomaly treatment first. Returns
    False (never naive) for missing/unparseable/'Z'-suffixed/explicit-offset
    values -- 'Z' and an explicit offset are both aware by definition, and
    an unparseable string is `_parse_utc()`'s own "no usable timestamp"
    case, not a provenance question this gate is responsible for."""
    if not timestamp:
        return False
    try:
        normalized = timestamp.strip()
        if normalized.endswith('Z'):
            return False  # 'Z' is an explicit UTC designator -- aware.
        dt = datetime.fromisoformat(normalized)
    except (ValueError, TypeError):
        return False
    return dt.tzinfo is None


def _is_d85_gated(timestamp: Optional[str], time_schema: Optional[int]) -> bool:
    """v9.12.0 A6 (ADR D8.5 read-side gating, SEC-CLOCKADR-9.12.0-021,
    per the read-side-gating design note's Option B,
    docs/superpowers/specs/2026-08-05-timeschema-read-side-gating-design-note.md):
    True iff `timestamp` is naive AND the enclosing project state has
    already been migrated (`time_schema` present and >= 1).

    Under a migrated file, ANY remaining naive value is either a
    still-ambiguous pre-migration record (ADR D8.5: "MUST NOT feed
    continuity classification, alerting, or work-streak accumulation") or a
    new naive write from an unanticipated future code path -- both cases
    receive the IDENTICAL conservative treatment here, deliberately: D8.5's
    own text does not ask the two to be distinguished, only that neither is
    silently trusted.

    `time_schema` absent or falsy (a genuinely pre-migration file) ALWAYS
    returns False -- today's tolerant "naive -> assume UTC" behavior is
    UNCHANGED for that case, matching the Migration Policy's own
    absent-vs-present tolerance precedent (ADR D8.1/D8.6, and the identical
    precedent already established by
    `ProjectStateManager.get_work_streak()`'s D7.6 fail-closed gate).

    Callers at CONTINUITY-CRITICAL sites (feeding continuity classification,
    the time envelope, or work-streak accumulation) MUST check this before
    calling `_parse_utc()` and route a True result through their own
    anomaly-handling branch -- NEVER simply treat it as an unparseable/
    missing value, which for several call sites would silently take the
    WRONG conservative direction (see the read-side-gating design note and
    this increment's dev-notes.md call-site audit for why each gated site's
    specific anomaly branch was chosen)."""
    if not time_schema or time_schema < 1:
        return False
    return _timestamp_is_naive(timestamp)


def _local_now(utc_dt: datetime, zone_info: Optional[zoneinfo.ZoneInfo] = None) -> datetime:
    """
    Convert an aware UTC datetime to local wall-clock time.

    v9.12.0 A2 phase (b) (DESIGN-001 closure, ADR D4): `zone_info` is the
    caller's ADR D4-resolved user zone -- a `zoneinfo.ZoneInfo` built from
    `SessionMonitor._user_zone_info`, itself derived from
    `timing_policy.load_timing_policy()`'s `config > DZP_USER_TIMEZONE env >
    OS-fallback > unresolved` precedence (D4.1). Previously this function
    called the EXECUTION HOST's OS zone via a bare, no-argument
    `utc_dt.astimezone()` unconditionally -- silently substituting host
    locality for user locality, the exact DESIGN-001 defect the audit
    identified. It no longer does so: omitting `zone_info` (or passing None
    -- the D4.4 "unresolved" terminal state, reached only when config, env,
    AND OS-fallback all fail to produce a validated IANA zone) now returns
    `utc_dt` UNCHANGED (still UTC) rather than falling back to a bare
    host-zone conversion. ADR D4.3 forbids that silent substitution, and
    D4.4 requires the "unresolved" state to display UTC only, never a
    guessed local time.

    BUG-SESSION-005: kept as its own function (rather than inlining the
    conversion at every call site) so tests can monkeypatch this single seam
    and inject a deterministic local time/zone without depending on the real
    system timezone of whatever machine runs the test suite.
    """
    if zone_info is None:
        return utc_dt
    return utc_dt.astimezone(zone_info)


def _is_late_night(local_dt: datetime, thresholds: Dict) -> bool:
    """
    BUG-SESSION-005: single implementation for every "is it late night"
    computation site in this module.

    Two defects fixed here:
    (a) previously computed from UTC hour (`now.hour >= late_night_hour`
        where `now = datetime.now(timezone.utc)`) instead of local wall-clock
        hour -- for a non-UTC user this both false-positived (UTC evening
        hours misread as local late-night) and false-negatived (real local
        late-night hours landing on a low UTC hour never tripped the check).
    (b) `hour >= late_night_hour` alone has no midnight wrap: 00:00-05:59 was
        never flagged in ANY timezone. `late_night_end_hour` (default 06:00)
        closes the wrap.

    `.get(..., default)` on both threshold keys means a legacy on-disk
    thresholds dict (minted before `late_night_end_hour` existed) is
    tolerated without requiring a state-file migration.
    """
    late_night_hour = thresholds.get('late_night_hour', 22)
    late_night_end_hour = thresholds.get('late_night_end_hour', 6)
    local_hour = local_dt.hour
    return local_hour >= late_night_hour or local_hour < late_night_end_hour


def _default_work_streak_shape() -> Dict:
    """v9.12.0 A3 (ADR D7, Toji gate 2 / SEC-001 HIGH direct fix): the
    default/empty work-streak record shape.

    This mirrors `ProjectStateManager._default_work_streak()` field-for-field
    -- the single normative shape lives there (it owns persistence). It is
    duplicated here ONLY for the degenerate path where ProjectStateManager
    itself is unavailable or raises (SessionMonitor._get_work_streak()),
    per ADR D7.6's `-011` extension: that failure is treated IDENTICALLY to
    an absent/corrupt work_streak block -- fail closed, never a silent
    fallback to a legacy file (this namespace, introduced in v9.12.0, has
    none to fall back to).

    CodeRabbit round-1 (PR #116): the FIELD LIST above is the justified
    duplication (documented "ProjectStateManager unavailable" path). The
    SCHEMA VERSION NUMBER is different -- it is read from
    `ProjectStateManager._WORK_STREAK_SCHEMA_VERSION` (the normative owner)
    through the SAME `STATE_MANAGER_AVAILABLE` optional-import guard that
    already gates `ProjectStateManager` itself, so a future schema bump
    there does not silently leave this fallback shape emitting a stale
    `1` (which `_work_streak_is_internally_consistent()` would then reject
    as inconsistent). The literal `1` below is kept ONLY as the
    last-resort value for the genuinely-unavailable case this function
    exists for in the first place.
    """
    schema_version = (
        ProjectStateManager._WORK_STREAK_SCHEMA_VERSION if STATE_MANAGER_AVAILABLE else 1
    )
    return {
        "work_streak_schema": schema_version,
        "streak_start_utc": None,
        "accumulated_protected_work_minutes": 0,
        "last_qualifying_break_utc": None,
        "last_qualifying_break_duration_minutes": None,
        "high_risk_block_active": False,
        "last_trusted_boundary_utc": None,
        "_streak_session_baseline_minutes": 0,
        "last_updated": None,
    }


class SessionMonitor:
    """
    Work session monitoring with real time tracking and enforcement.
    """

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)

        # PATCH-STATE-001: Initialize centralized state manager
        if STATE_MANAGER_AVAILABLE:
            self.state_manager = ProjectStateManager(protocol_root)
        else:
            self.state_manager = None

        # Legacy file paths (kept for backward compatibility)
        self.state_file = self.protocol_root / ".protocol-state" / "session-state.json"
        self.template_file = self.protocol_root / ".protocol-state" / "work-session-alert.template.md"
        self.config_file = self.protocol_root / "protocol.config.yaml"
        self.invocation_tracker_file = self.protocol_root / ".protocol-state" / "agent-invocation-tracker.json"

        # v9.12.0 A2 phase (b) (ADR D6.1, D6.2/IMPL-002 closure): the ONE
        # resolved timing-policy object -- late-night window, session-
        # continuation gap, clock-health tolerances, and the D4-resolved
        # user zone, each with recorded provenance. This is the loader that
        # makes `safety.boundaries.late_night_threshold` and
        # `safety.session_tracking.session_continuation_threshold_minutes`
        # (previously declared-but-unread) actually govern enforced
        # behavior -- see _default_state()'s thresholds and
        # start_session()'s continuation-gap check below. It does NOT
        # replace `self.alert_thresholds`/`_load_alert_thresholds()` below,
        # which already correctly reads the 4 duration-alert fields this
        # loader also resolves (no bug there to fix) -- both loaders read
        # the same config keys and agree by construction.
        self.timing_policy = load_timing_policy(protocol_root=self.protocol_root)
        # D1/D2: the sole clock-authority instance for this monitor,
        # configured with the resolved clock-health tolerances (D3.1).
        self.time_provider = self.timing_policy.make_time_provider()
        # DESIGN-001 closure (D4): a concrete zoneinfo.ZoneInfo for
        # _local_now() to convert into, or None in the D4.4 "unresolved"
        # terminal state -- never a bare, unlabeled host-zone substitution.
        self._user_zone_info = self._resolve_zoneinfo(self.timing_policy.user_zone)

        # FEAT-TRANSFER-9.11.0-001 (v9.11.0 Increment 2): /session transfer
        # handoff artifacts. Deliberately NOT protected documents (see
        # protocol/skills/session.md § /session transfer) -- regenerable
        # derived state, overwritten each transfer, gitignored, never shipped.
        self.handoff_file = self.protocol_root / ".protocol-state" / "session-handoff.md"
        self.handoff_marker_file = self.protocol_root / ".protocol-state" / "session-handoff.INCOMPLETE"
        self.handoff_archive_dir = self.protocol_root / ".protocol-state" / "archive" / "handoff"
        self.handoff_notes_file = self.protocol_root / ".protocol-state" / "session-handoff-notes.md"
        # CODE-001 remediation (Toji audit 2026-07-29): once handoff_write()
        # successfully consumes the staged notes file into a written brief,
        # it is moved here (single-use) so a later transfer can never
        # silently reuse stale notes -- see _archive_and_clear_handoff_notes().
        self.handoff_notes_archive_dir = self.protocol_root / ".protocol-state" / "handoff-notes-archive"

        # Load high-risk operation literals (no regex, safer and faster)
        self._high_risk_literals = self._load_high_risk_literals()

        # Load configuration (v8.13.0 - Configuration Enhancements)
        self.enabled = self._load_enabled_flag()
        self.alert_thresholds = self._load_alert_thresholds()
        self.alert_customization = self._load_alert_customization()

        self._ensure_state_file()

    def _check_gojo_invocation(self) -> bool:
        """
        Check if current invocation is from Gojo agent.

        EXTENSION 3: Permission System (PATCH-SESSION-005)
        Domain.record.md should only be updated when invoked by Gojo to maintain
        strategic protocol integrity. Other agents/users can update other state files.

        Returns:
            True if invoked by Gojo (DZP_AGENT=gojo env var), False otherwise
        """
        return os.environ.get('DZP_AGENT', '').lower() == 'gojo'

    @staticmethod
    def _resolve_zoneinfo(zone_resolution) -> Optional[zoneinfo.ZoneInfo]:
        """
        v9.12.0 A2 phase (b) (DESIGN-001 closure, ADR D4): convert a
        `time_provider.ZoneResolution` (already IANA-validated by
        `TimeProvider.resolve_user_zone()`) into a concrete
        `zoneinfo.ZoneInfo` for `_local_now()` to convert into.

        Returns None for the D4.4 "unresolved" terminal state
        (`zone_resolution.iana is None`) -- this is an EXPECTED, valid
        result, not an error: `_local_now()` treats None as "no confirmed
        zone, display UTC" rather than silently substituting the execution
        host's zone (the exact DESIGN-001 defect). Also returns None (rather
        than raising) on any unexpected `zoneinfo.ZoneInfo(...)` construction
        failure here -- `resolve_user_zone()` already validated the name via
        the same lookup, so this is a defense-in-depth guard, not the
        primary validation path.
        """
        if zone_resolution.iana is None:
            return None
        try:
            return zoneinfo.ZoneInfo(zone_resolution.iana)
        except Exception:
            return None

    def _load_high_risk_literals(self) -> List[str]:
        """
        Load high-risk operation literal strings from config file.

        Uses literal string matching instead of regex to avoid ReDoS vulnerabilities.
        Matching is case-insensitive via .lower() comparison.

        Returns:
            List of lowercase literal strings to match
        """
        # Default fallback literals (safe, no regex)
        # Each entry is a substring; if it appears anywhere in the command (case-insensitive)
        # the command is classified as high-risk.  Short-form variants (without 'origin')
        # are intentionally included alongside the long-form equivalents so that both
        # 'git push main' and 'git push origin main' are caught.
        default_literals = [
            # git push — long form (with remote name)
            'git push origin production',
            'git push origin main',
            'git push origin master',
            # git push — short form (without remote name, still high-risk)
            'git push production',
            'git push main',
            'git push master',
            # git push — force flags
            'git push --force',
            'git push -f',
            # deploy variants
            'deploy to production',
            'deploy production',
            'deploy --production',
            # destructive filesystem
            'rm -rf',
            # SQL DDL / DML
            'drop table',
            'drop database',
            'delete from',
            'alter table',
            'truncate table',
            # package publishing
            'npm publish',
            # container / orchestration
            'docker push',
            'docker production',
            'docker-compose up production',
            'docker-compose production',
            'kubectl delete',
            'kubectl delete namespace',
            'kubectl production',
            'kubectl apply production',
            # infrastructure-as-code
            'terraform destroy',
            'terraform apply -auto-approve',
            # cloud platform destructive ops
            'heroku destroy',
            'firebase delete',
            'aws s3 rm',
            'gcloud delete',
        ]

        # Try to load literals from config file
        if self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # Extract literals from config
                safety_config = config.get('safety', {})
                session_tracking = safety_config.get('session_tracking', {})
                high_risk_ops = session_tracking.get('high_risk_operations', {})
                configured_literals = high_risk_ops.get('literals', [])

                if configured_literals:
                    # Return configured literals (lowercase for case-insensitive matching)
                    return [lit.lower() for lit in configured_literals]

            except Exception as e:
                # Silent fallback to defaults (no warning spam)
                pass

        # Fall back to defaults if config unavailable or empty
        return default_literals

    def _load_debounce_config(self, cli_override: int = None) -> int:
        """
        Load debounce threshold from config file or CLI argument.

        Debounce prevents alert spam by skipping alerts if last alert was < threshold ago.
        v8.13.0 - PATCH-SESSION-004

        Args:
            cli_override: CLI --debounce argument (takes precedence)

        Returns:
            Debounce threshold in minutes (default: 30, range: 15-60)
        """
        # CLI argument takes precedence
        if cli_override is not None:
            # Validate range
            if 15 <= cli_override <= 60:
                return cli_override
            else:
                print(f"[!] Invalid debounce value {cli_override}. Must be 15-60 minutes.")
                print(f"    Falling back to default: 30 minutes")
                return 30

        # Try to load from config file
        if self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                safety_config = config.get('safety', {})
                session_tracking = safety_config.get('session_tracking', {})
                debounce_threshold = session_tracking.get('debounce_threshold_minutes')

                if debounce_threshold is not None:
                    # Validate range
                    if 15 <= debounce_threshold <= 60:
                        return debounce_threshold
                    else:
                        print(f"[!] Invalid debounce_threshold_minutes in config: {debounce_threshold}")
                        print(f"    Must be 15-60. Falling back to default: 30 minutes")
                        return 30

            except Exception as e:
                # Silent fallback to default
                pass

        # Default fallback
        return 30

    def _load_enabled_flag(self) -> bool:
        """
        Load session monitoring enabled flag from protocol.config.yaml.

        v8.13.0 - Configuration Enhancement
        Master toggle for session monitoring system.

        Returns:
            True if session monitoring is enabled, False otherwise (default: True)
        """
        # Default: enabled
        default = True

        # Try to load from config file
        if self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                safety_config = config.get('safety', {})
                session_tracking = safety_config.get('session_tracking', {})
                enabled = session_tracking.get('enabled')

                if enabled is not None:
                    return bool(enabled)

            except Exception as e:
                # Silent fallback to default
                pass

        # Default fallback
        return default

    def _load_alert_thresholds(self) -> Dict:
        """
        Resolve alert threshold configuration.

        v9.12.0 A5 (ADR D6.1, IMPL-004 full closure): this used to be an
        entirely separate re-implementation of the same 4 duration fields
        `self.timing_policy` (constructed earlier in `__init__`, ADR D6
        unified loader) already resolves -- its own YAML parse, its own
        range validation (2-12h/4-16h/6-24h/15-120min, IDENTICAL to
        timing_policy.py's 120-720/240-960/360-1440/15-120-minute ranges),
        its own "[!] Invalid ..." messages -- independently re-deriving
        values that could only "agree by construction" (the exact
        four-independently-drifting-copies pattern IMPL-004 named) rather
        than by having one source of truth. Now delegates entirely to
        `self.timing_policy`, which resolves these same 4 fields from the
        same `safety.session_tracking.alert_thresholds.*` config keys. The
        public return shape (exactly these 4 keys) is unchanged, so every
        existing consumer (`_default_state()`, `check_alert_needed()`,
        `get_session_summary()`) needs no changes --
        tests/test_defaults_single_source_9_12.py locks in the equivalence.

        Returns:
            Dict with threshold values in minutes:
            {
                'initial_alert_minutes': 240,      # 4 hours
                'critical_session_minutes': 360,   # 6 hours
                'max_continuous_minutes': 480,      # 8 hours
                'escalated_alert_minutes': 45      # 45 minutes
            }
        """
        return {
            'initial_alert_minutes': self.timing_policy.initial_alert_minutes,
            'critical_session_minutes': self.timing_policy.critical_session_minutes,
            'max_continuous_minutes': self.timing_policy.max_continuous_minutes,
            'escalated_alert_minutes': self.timing_policy.escalated_alert_minutes,
        }

    def _load_alert_customization(self) -> Dict:
        """
        Load custom alert messages from protocol.config.yaml.

        v8.13.0 - Configuration Enhancement
        Allows customization of alert messages for company/team context.

        Returns:
            Dict with custom messages (None values mean use defaults):
            {
                'company_policy': str or None,
                'break_recommendation': str or None,
                'late_night_warning': str or None,
                'critical_warning': str or None
            }
        """
        # Default: all None (use built-in messages)
        defaults = {
            'company_policy': None,
            'break_recommendation': None,
            'late_night_warning': None,
            'critical_warning': None
        }

        # Try to load from config file
        if self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                safety_config = config.get('safety', {})
                session_tracking = safety_config.get('session_tracking', {})
                customization = session_tracking.get('alert_customization', {})

                if customization:
                    # Extract custom messages (preserving None for unset values)
                    return {
                        'company_policy': customization.get('company_policy'),
                        'break_recommendation': customization.get('break_recommendation'),
                        'late_night_warning': customization.get('late_night_warning'),
                        'critical_warning': customization.get('critical_warning')
                    }

            except Exception as e:
                # Silent fallback to defaults
                pass

        # Default fallback
        return defaults

    def _ensure_state_file(self):
        """Ensure session state file exists with proper schema."""
        if not self.state_file.exists():
            print(f"[!] Session state file not found at {self.state_file}")
            print("    Creating default session state...")
            try:
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.state_file, 'w') as f:
                    json.dump(self._default_state(), f, indent=2)
                self._attest_write(self.state_file)
            except (IOError, OSError) as e:
                raise RuntimeError(f"Failed to create session state file at {self.state_file}: {e}")

    def _default_state(self) -> Dict:
        """Return default session state structure (v8.13.0 - uses loaded thresholds).

        BUG-SESSION-002 (v9.9.x Track C): `last_updated` MUST be a valid ISO-8601
        string, never null.  The session-state schema requires `type: string` for
        `last_updated`; a null value causes `validate-protocol.py --check` to fail
        with a type error which in turn blocks every repo commit via the pre-commit
        hook.  We now initialise it to the current UTC timestamp at construction time
        so that every reset/default path produces a schema-valid file.
        """
        return {
            "_comment": "Domain Zero Protocol - Work Session State Tracking (v8.13.0)",
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
                "high_risk_operations_blocked": False,
                # Toji audit 2026-08-06 (IMPL-001/SEC-002): see
                # start_session()'s new-session literal for the full
                # rationale. Defaulted here too so a freshly-reset/legacy
                # state file always has these keys present.
                "streak_contribution_start_time": None,
                "pending_break_started_utc": None,
                "pending_break_reported_minutes": None,
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
                "initial_alert_minutes": self.alert_thresholds['initial_alert_minutes'],
                "escalated_alert_minutes": self.alert_thresholds['escalated_alert_minutes'],
                "critical_session_minutes": self.alert_thresholds['critical_session_minutes'],
                "max_continuous_minutes": self.alert_thresholds['max_continuous_minutes'],
                # v9.12.0 A2 phase (b) (IMPL-002 closure, ADR D6.2): previously
                # hardcoded literals (22/6) that made
                # `safety.boundaries.late_night_threshold` and the
                # `late_night_end_hour` config key have NO EFFECT on enforced
                # behavior no matter what they were edited to. Now sourced
                # from the single timing_policy.py loader, which DOES read
                # both keys -- editing either in protocol.config.yaml now
                # changes this value.
                "late_night_hour": self.timing_policy.late_night_hour,
                # BUG-SESSION-005: midnight-wrap end of the late-night window
                # (local hour < this counts as late night too). .get()'d with
                # a fallback everywhere it's read, so legacy state files
                # without this key are never broken -- see _is_late_night().
                "late_night_end_hour": self.timing_policy.late_night_end_hour,
                # SEC-CLOCKADR-9.12.0-016 (P2, CWE-1188, Megumi Tier-3 gate-2
                # review): previously a hardcoded `15` -- the same class of
                # IMPL-002 config-drift bug the two lines above this were
                # already fixed for, in the exact same dict literal.
                # record_break() reads this materialized value (never
                # re-resolving self.timing_policy afterward), so under a
                # non-default, STRICTER configured minimum_break_minutes the
                # hardcoded 15 silently let record_break() close the
                # work-streak protection window on a weaker break than the
                # user configured. Now sourced from the same D6.1 loader.
                "minimum_break_minutes": self.timing_policy.minimum_break_minutes
            },
            "session_history": [],
            # BUG-SESSION-002: Must be a string (ISO-8601), never null.
            "last_updated": self.time_provider.utc_now().isoformat(),
            "protocol_version": "8.13.0"
        }

    def load_state(self) -> Dict:
        """
        Load current session state from JSON.

        PATCH-STATE-001: Uses ProjectStateManager when available for unified state access.
        Falls back to legacy file I/O for backward compatibility.
        """
        # PATCH-STATE-001: Use ProjectStateManager if available
        if self.state_manager:
            try:
                return self.state_manager.get_session_tracking()
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O

        # Legacy file I/O (backward compatibility)
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[!] Session state file not found. Returning default state.")
            return self._default_state()
        except json.JSONDecodeError as e:
            print(f"[!] Corrupted session state file: {e}. Returning default state.")
            return self._default_state()

    def save_state(self, state: Dict):
        """
        Save session state to JSON with atomic write (SEC-002 FIX).

        PATCH-STATE-001: Uses ProjectStateManager when available for unified state access.
        Falls back to legacy file I/O for backward compatibility.
        """
        state['last_updated'] = self.time_provider.utc_now().isoformat()

        # PATCH-STATE-001: Use ProjectStateManager if available
        if self.state_manager:
            try:
                self.state_manager.update_session_tracking(state)
                return
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O

        # Legacy atomic write pattern (backward compatibility)
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False,
                                              dir=self.state_file.parent,
                                              suffix='.tmp') as tmp_file:
                json.dump(state, tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic replace (POSIX rename guarantees atomicity)
            os.replace(tmp_path, self.state_file)
        except (IOError, OSError) as e:
            # If atomic write fails, try cleanup and re-raise
            try:
                if 'tmp_path' in locals() and Path(tmp_path).exists():
                    os.unlink(tmp_path)
            except OSError:
                pass  # Cleanup failure is non-critical
            raise IOError(f"Failed to save session state: {e}")

        # ISS-083: attest this sanctioned (legacy-path) write. Only reached
        # when ProjectStateManager is unavailable/failed above; the
        # ProjectStateManager path already attests project-state.json itself.
        self._attest_write(self.state_file)

    def _attest_write(self, target_file: Path, writer: str = "SessionMonitor") -> None:
        """
        Best-effort ISS-083 write attestation for a just-completed write to
        *target_file*.

        Reads back the exact bytes now on disk so the recorded content hash
        always matches reality, and stamps a signed ledger entry keyed by
        the file's basename (the same key scripts/validate-protocol.py's
        drift detection uses).

        Never raises: attestation is advisory metadata for drift detection,
        not a correctness requirement of the write itself (which has
        already completed by the time this runs).

        CodeRabbit PR#108: `_ATTESTATION_AVAILABLE` False (module absent) is
        an expected, common deployment shape and stays SILENT. A runtime
        failure during the actual stamp attempt is a different, more
        actionable condition and now emits a concise stderr warning -- but
        REDACTED: only the file's basename (never the full `target_file`
        path, which can embed a user's home directory / project layout)
        and the exception's TYPE name (never `str(e)`, which for OSError-
        family exceptions commonly embeds the full path that failed, and
        could in principle echo other incidental detail). No key material
        or file contents are ever in scope here to begin with -- attestation
        only ever handles the HMAC key file and ledger internally, never
        this method's own locals.

        CodeRabbit PR#108 round 2: `record_write()` is fail-soft internally
        -- it can return False (e.g. lock never acquired, ledger save
        failed) WITHOUT raising. The exception handler alone missed that
        path. A False return now gets the same class of stderr warning as
        an exception (basename + a fixed reason token only, no path/
        exception detail); a True return stays silent (the common case).
        """
        if not _ATTESTATION_AVAILABLE:
            return
        try:
            content = target_file.read_bytes()
            attested = _attest_record_write(
                target_file.parent, target_file.name, content, writer=writer
            )
            if not attested:
                print(
                    f"[WARN] Write attestation returned failure for {target_file.name} "
                    "(record_write returned False)",
                    file=sys.stderr,
                )
        except Exception as e:
            print(
                f"[WARN] Write attestation failed for {target_file.name} ({type(e).__name__})",
                file=sys.stderr,
            )

    # -------------------------------------------------------------------
    # v9.12.0 A3 -- work-streak / protection-window state (ADR D7, Toji
    # gate 2; governing audit finding SEC-001, HIGH: "Session lifecycle
    # reset bypasses rolling active-protection state"). Durable rolling
    # protected-work state that survives start/end/transfer/archive/
    # handoff/process-restart, and closes ONLY after a verified qualifying
    # break. See docs/superpowers/specs/2026-08-04-clock-authority-adr.md
    # D7 for the full normative spec this section implements.
    # -------------------------------------------------------------------

    def _get_time_schema(self) -> Optional[int]:
        """v9.12.0 A6 (ADR D8.5 read-side gating, SEC-CLOCKADR-9.12.0-021):
        the top-level `time_schema` stamp (ADR D8.1), read directly from the
        FULL project-state.json.

        Deliberately NOT `self.load_state()` -- that method (via
        `ProjectStateManager.get_session_tracking()`) intentionally scopes
        down to the `session_tracking` sub-namespace only, so it can never
        see this sibling top-level key. Every `_is_d85_gated()` call site in
        this class calls this method (or receives its result threaded
        through) rather than trying to read `time_schema` off
        `load_state()`'s return value, which would silently always resolve
        to None (an unconditional false-negative on the gate) regardless of
        the file's actual migration state.

        Fail-soft: `ProjectStateManager` unavailable or raising, or the key
        genuinely absent, all return None -- and `_is_d85_gated()` treats
        None identically to "pre-migration file" (today's tolerant
        behavior), matching `ProjectStateManager.get_work_streak()`'s own
        D7.6 absent-`time_schema` tolerance precedent for the same field."""
        if self.state_manager is None:
            return None
        try:
            state = self.state_manager.load_project_state()
        except Exception:
            return None
        return state.get("time_schema")

    def _carry_work_streak_forward(self, work_streak: Dict) -> Dict:
        """D7.5/D3.2 conservative-under-anomaly (shared by BOTH the
        skew-suspected/rollback-detected clock-health branch in
        `_classify_and_carry_work_streak()` below AND the v9.12.0 A6 ADR
        D8.5 read-side gate on `last_trusted_boundary_utc` itself): an
        anomalous or unconfirmed-provenance read can NEVER be used to CLOSE
        the streak, only to leave it open. The streak carries FORWARD
        unchanged; only this session's baseline is seeded."""
        carried = dict(work_streak)
        carried.pop("_fail_closed", None)
        carried["_streak_session_baseline_minutes"] = carried.get("accumulated_protected_work_minutes") or 0
        return carried

    def _get_work_streak(self) -> Dict:
        """ADR D7.6 read, routed through ProjectStateManager.get_work_streak()
        (the fail-closed rule itself lives there). Per D7.6's `-011`
        extension: if ProjectStateManager is unavailable or its accessor
        raises, this is treated IDENTICALLY to an absent/corrupt
        work_streak block -- fail closed, never a silent fallback to a
        legacy file (this namespace has none)."""
        if self.state_manager is not None:
            try:
                return self.state_manager.get_work_streak()
            except Exception as e:
                print(
                    f"[!] SEC-CLOCKADR-9.12.0-001/-011: ProjectStateManager."
                    f"get_work_streak() raised ({type(e).__name__}); failing "
                    "CLOSED per ADR D7.6.",
                    file=sys.stderr,
                )
        else:
            print(
                "[!] SEC-CLOCKADR-9.12.0-001/-011: ProjectStateManager "
                "unavailable; failing CLOSED per ADR D7.6 (no legacy-file "
                "fallback exists for work_streak).",
                file=sys.stderr,
            )
        fail_closed = _default_work_streak_shape()
        fail_closed["high_risk_block_active"] = True
        fail_closed["_fail_closed"] = True
        return fail_closed

    def _update_work_streak(self, work_streak: Dict) -> None:
        """Persist an updated work_streak record. Fail-soft in the sense
        that a persistence failure never raises out to a caller mid
        session-lifecycle-op (matching this module's existing save_state()
        posture), but ALWAYS loud on stderr -- a discarded update must never
        look identical to a successful one."""
        if self.state_manager is None:
            print(
                "[!] SEC-CLOCKADR-9.12.0-001/-011: ProjectStateManager "
                "unavailable; work_streak update DISCARDED (fail closed -- "
                "no legacy-file fallback exists for this namespace).",
                file=sys.stderr,
            )
            return
        try:
            self.state_manager.update_work_streak(work_streak)
        except Exception as e:
            print(
                f"[!] SEC-CLOCKADR-9.12.0-001/-011: ProjectStateManager."
                f"update_work_streak() raised ({type(e).__name__}); update "
                "DISCARDED (fail closed).",
                file=sys.stderr,
            )

    def _rolling_streak_minutes(self, work_streak: Dict, current_session_elapsed_minutes: float) -> float:
        """ADR consequence (wellbeing alerts must consume the ROLLING
        work-streak duration, not just the active session's own elapsed
        time -- the directly observable effect of the SEC-001 fix).

        Reduces to exactly `current_session_elapsed_minutes` whenever there
        is no prior streak contribution (baseline 0 -- the first session
        ever, or a streak that was just freshly opened/closed), so
        single-session behavior is BYTE-FOR-BYTE unchanged from pre-A3.
        """
        baseline = work_streak.get("_streak_session_baseline_minutes") or 0
        try:
            baseline = float(baseline)
        except (TypeError, ValueError):
            baseline = 0.0
        if baseline < 0:
            baseline = 0.0
        return baseline + current_session_elapsed_minutes

    # -------------------------------------------------------------------
    # Toji audit 2026-08-06 (CODE-001, MEDIUM): "Clock-health checks remain
    # absent from primary safety-policy arithmetic." `evaluate_clock_health()`
    # (ADR D2.2/D3.1/D3.2) was wired into exactly one call site
    # (`_classify_and_carry_work_streak()` above). Every OTHER
    # policy-bearing persisted-UTC subtraction in this module -- the
    # continuation gap, the two `update_interaction()` durations, all three
    # `check_alert_needed()` gaps, and `_archive_session()`'s final duration
    # -- computed a raw `(later - earlier)` directly, trusting a future
    # timestamp, a clock rollback, or an implausibly large gap without
    # question. This ONE shared operation is now the single place every one
    # of those call sites routes through; each call site still decides its
    # OWN fail-closed behavior on an anomaly (D3.2 does not mandate one
    # global policy), but none of them can skip the health check itself.
    #
    # SCOPE NOTE (CodeRabbit round-1, PR #116): "every OTHER policy-bearing
    # subtraction" above is deliberately scoped to the CODE-001 finding's
    # own enumerated call sites, not a claim that ALL raw `(now - start)`
    # arithmetic in this module was migrated. `_calculate_current_duration()`
    # and `_calculate_current_continuous_work()` (below) still compute a
    # raw duration -- a REVIEWED, not accidental, omission: they answer "how
    # long has the live wall-clock session been running RIGHT NOW" for
    # human-facing display (`get_session_summary()`) and for
    # `should_block_operation()`'s `max_continuous_minutes` gate, where
    # `_health_gated_minutes()` returning `None` on ANY clock anomaly would
    # either blank a status display outright or (for the blocking gate)
    # remove the one signal `should_block_operation()` uses -- it already
    # takes `max(live_duration, stored_duration)` specifically so a clock
    # rollback cannot LOWER the reported duration below the last persisted
    # metric, and a future-dated `start_time` only ever OVER-blocks, never
    # under-blocks. Gating these two would trade a working fail-SAFE
    # (over-block on anomaly) for a fail-BLANK (skip the block on anomaly)
    # in the one path where erring toward MORE blocking, not less, is the
    # correct direction. See
    # tests/test_work_streak.py::TestLiveDurationHelpersDeliberatelyUngated
    # for the direct regression proof of this reasoning.
    # -------------------------------------------------------------------

    def _health_gated_minutes(
        self,
        earlier: Optional[datetime],
        later: datetime,
        *,
        now: Optional[datetime] = None,
    ):
        """Evaluate `later - earlier` through `TimeProvider.evaluate_clock_health()`
        and return `(minutes, health)`.

        `minutes` is `None` whenever the pair is not clock-health `ok`
        (D3.2: "consumers MUST NOT silently compute a duration ... from the
        anomalous pair") -- this deliberately covers BOTH `skew-suspected`
        and `rollback-detected`; only the caller's own fail-closed policy
        decides what to do with a `None`. `minutes` is also `None` (with
        `health` also `None`) when `earlier` itself is missing -- distinct
        from an earlier that parsed but produced an anomalous gap.

        Args:
            earlier: The chronologically-earlier labeled instant, or None
                if there is nothing to compare against yet.
            later: The chronologically-later labeled instant (typically
                `now`).
            now: The authoritative current instant for the future-timestamp
                rejection rule (D3.1). Defaults to `later` when omitted --
                the common case where `later` itself IS "now".

        Returns:
            `(minutes: Optional[float], health: Optional[ClockHealthResult])`
        """
        if earlier is None:
            return None, None
        health = self.time_provider.evaluate_clock_health(
            earlier=earlier, later=later, now=now if now is not None else later
        )
        if not health.is_ok:
            return None, health
        return health.gap_seconds / 60.0, health

    def _classify_and_carry_work_streak(self, now: datetime, time_schema: Optional[int] = None) -> Dict:
        """ADR D7.3/D7.4: run ONLY when a genuinely NEW session is about to
        start (never on the "continue the still-active session" branch of
        start_session(), which is a separate, shorter-fused DISPLAY/session-
        level concept governed by session_continuation_threshold_minutes,
        not this function).

        Compares `now` against `work_streak.last_trusted_boundary_utc` --
        the SEC-001 fix: NEVER against the just-reset/about-to-be-recreated
        `current_session` object -- and decides whether the existing streak
        carries forward unchanged, or a verified qualifying break closes it.

        Args:
            now: The authoritative current instant (D1).
            time_schema: v9.12.0 A6 (ADR D8.5). The caller's already-resolved
                `_get_time_schema()` result, threaded in rather than
                re-fetched here so a single `start_session()` call only
                reads the top-level state once. Defaults to None (treated as
                "pre-migration/unknown" -- today's tolerant behavior) so
                direct unit-test callers that don't care about D8.5 are
                unaffected.

        Returns the work_streak dict the caller must persist (via
        `_update_work_streak()`) for the session about to start.
        """
        work_streak = self._get_work_streak()
        last_boundary_raw = work_streak.get("last_trusted_boundary_utc")

        if _is_d85_gated(last_boundary_raw, time_schema):
            # v9.12.0 A6 (ADR D8.5, SEC-CLOCKADR-9.12.0-021): a naive
            # `last_trusted_boundary_utc` in a migrated file is treated
            # EXACTLY like a D3.2 clock-health anomaly, NOT like "no prior
            # boundary at all" (the `last_boundary is None` branch below).
            # Those two cases produce OPPOSITE outcomes: "no prior boundary"
            # OPENS a fresh streak (resets accumulated_protected_work_minutes
            # to 0), while an anomalous/unconfirmed boundary must CARRY the
            # existing streak FORWARD unchanged (D7.5) -- silently routing
            # through the "no prior boundary" branch here would have reset a
            # real, currently-open wellbeing protection window purely
            # because its provenance was unconfirmed, which is the opposite
            # of the conservative direction D7.5/D3.2 require.
            print(
                "[!] SEC-CLOCKADR-9.12.0-021: work_streak.last_trusted_boundary_utc "
                "is naive in a migrated (time_schema >= 1) state file -- ADR "
                "D8.5 gate engaged. Treating as an unconfirmed-provenance "
                "anomaly: streak carried FORWARD unchanged, never reset.",
                file=sys.stderr,
            )
            return self._carry_work_streak_forward(work_streak)

        last_boundary = _parse_utc(last_boundary_raw)

        if last_boundary is None:
            # No prior trusted boundary at all: first session ever (or a
            # never-initialized/fail-closed record with no boundary to
            # compare against) -- open a fresh streak starting now.
            opened = _default_work_streak_shape()
            opened["streak_start_utc"] = now.isoformat()
            opened["last_trusted_boundary_utc"] = now.isoformat()
            # D7.6 fail-closed carries high_risk_block_active=True forward
            # even into a freshly-opened streak -- conservative, never
            # silently cleared by the mere act of opening a new streak.
            opened["high_risk_block_active"] = bool(work_streak.get("high_risk_block_active"))
            return opened

        health = self.time_provider.evaluate_clock_health(earlier=last_boundary, later=now, now=now)
        minimum_break_minutes = self.timing_policy.minimum_break_minutes

        if health.is_ok and health.gap_seconds is not None and (health.gap_seconds / 60) >= minimum_break_minutes:
            # D7.4: a verified qualifying break -- close the window. Ending
            # a session and IMMEDIATELY starting a new one (the exact
            # SEC-001 exploit) produces a near-zero gap here, which is below
            # minimum_break_minutes, so it does NOT reach this branch.
            closed = _default_work_streak_shape()
            closed["streak_start_utc"] = now.isoformat()
            closed["last_trusted_boundary_utc"] = now.isoformat()
            closed["last_qualifying_break_utc"] = now.isoformat()
            closed["last_qualifying_break_duration_minutes"] = health.gap_seconds / 60
            closed["high_risk_block_active"] = False
            return closed

        # D7.5/D3.2 conservative-under-anomaly: `skew-suspected` /
        # `rollback-detected` fall here too -- an anomalous clock can NEVER
        # be used to CLOSE the streak, only to leave it open. The streak
        # carries FORWARD unchanged; only this session's baseline is seeded.
        return self._carry_work_streak_forward(work_streak)

    # -------------------------------------------------------------------
    # v9.12.0 A4 -- ADR D5 time envelope (Toji gate 4; governing audit
    # finding AI-001, HIGH: "Claude and Codex lack an authoritative user-time
    # context"). One method assembles every input `time_envelope.py`'s pure
    # builder needs from THIS monitor's own already-resolved state (the D1-D4
    # TimeProvider/timing_policy from A2, the D7 work-streak record from A3)
    # -- callers (the CLI `--json` branches in `main()`, below) never touch
    # `time_envelope.py` directly.
    # -------------------------------------------------------------------

    def _build_envelope(
        self,
        boundary: str,
        *,
        session_id: Optional[str] = None,
        previous_end_utc: Optional[datetime] = None,
        current_start_utc: Optional[datetime] = None,
        alert_needed: Optional[bool] = None,
        alert_reasons: Optional[List[str]] = None,
        is_late_night: Optional[bool] = None,
        ambiguous_boundary_timestamp: bool = False,
    ) -> Dict:
        """Build one D5 time envelope for `boundary` (one of
        `time_envelope.SessionBoundary.ALL`). Never raises -- any composition
        failure degrades to the D5.6 `unavailable` stub via
        `build_envelope_safe()`, exactly as a session-lifecycle command must
        never fail SOLELY because the envelope could not be built.

        `previous_end_utc`/`current_start_utc` are optional: pass both to
        get a `gap`/`continuity` classification (e.g. `start`, comparing the
        just-archived session's end against the new start); omit both for
        boundaries with no meaningful boundary-gap concept (e.g. `status`,
        `check` -- `continuity.class` then degrades to the documented
        "no previous session boundary available" fresh_session default).

        `ambiguous_boundary_timestamp`: v9.12.0 A6 (ADR D8.5 read-side
        gating, SEC-CLOCKADR-9.12.0-021). The caller (currently only the
        `start --json` CLI branch in `main()`) sets this True when it
        withheld BOTH `previous_end_utc`/`current_start_utc` (passing both
        None) specifically because the D8.5 gate (`_is_d85_gated()`) fired
        on the raw value -- forwarded verbatim to `time_envelope.build_envelope()`,
        which is what actually renders the distinct `ambiguous_timestamp`
        status reason (see that function's docstring). This method never
        evaluates the gate itself -- it has no access to the raw string,
        only the caller's already-parsed-or-withheld `datetime` values.

        SEC-CLOCKADR-9.12.0-017 (P1, A04:2021) remediation: `is_late_night`/
        `alert_needed`/`alert_reasons` are `Optional` and default to `None`
        (NOT `False`/`[]`) so this method can distinguish "the caller did not
        supply a value" from "the caller computed False/[] explicitly" (e.g.
        `check`'s CLI branch, which already has `check_alert_needed()`'s full
        authoritative result including duration-based reasons that require
        active-session state this method does not otherwise need). When
        `is_late_night` is omitted, THIS method computes it itself --
        `_is_late_night()` is a cheap, session-state-independent computation
        needing only `now` + the resolved user zone + thresholds, all of
        which this method already gathers below -- so EVERY boundary reports
        the genuine value, never the prior hardcoded `False`/`[]` default
        that made a `start --json` envelope at 2am affirmatively (and
        `envelope_status: "complete"`-ly) claim "not late night, no alert."
        Per ADR D6.4 ("late night... can set alert_needed = True on its
        own"), when the (explicit-or-computed) `is_late_night` is true,
        `alert_needed` is forced True and `"late_night"` is folded into
        `alert_reasons` REGARDLESS of boundary or whether the caller already
        included it (idempotent for `check`, which already includes it).
        Duration-based reasons remain `check`/`check-and-record`-only --
        computing those requires `check_alert_needed()`'s own active-session
        arithmetic, which this method does not reproduce.
        """
        # D5.6: gathering these inputs (state load, work-streak read) can
        # itself raise (e.g. a corrupt ProjectStateManager) -- that failure
        # must degrade to the SAME "unavailable" stub build_envelope_safe()
        # already produces for a composition-time failure, not propagate out
        # of this method. build_envelope_safe() alone only guards exceptions
        # raised INSIDE build_envelope() itself; input gathering happens
        # BEFORE that call, so this method wraps BOTH steps in one guard.
        try:
            now = self.time_provider.utc_now()
            state = self.load_state()
            thresholds = state.get('thresholds', {})
            late_night_hour = thresholds.get('late_night_hour', self.timing_policy.late_night_hour)
            late_night_end_hour = thresholds.get('late_night_end_hour', self.timing_policy.late_night_end_hour)

            # SEC-CLOCKADR-9.12.0-017: compute the genuine late-night state
            # for THIS boundary's emission instant whenever the caller did
            # not already supply it -- the direct fix for the 6-of-7-
            # boundaries-hardcoded-false defect. Uses the SAME `now` passed
            # to build_envelope_safe() below (not a second, potentially
            # divergent `utc_now()` read) so `local_wall_time`/
            # `authoritative_instant_utc` and `late_night.is_late_night`
            # are always evaluated against one consistent instant.
            if is_late_night is None:
                late_night_thresholds = {
                    'late_night_hour': late_night_hour,
                    'late_night_end_hour': late_night_end_hour,
                }
                is_late_night = _is_late_night(_local_now(now, self._user_zone_info), late_night_thresholds)
            if alert_reasons is None:
                alert_reasons = []
            if alert_needed is None:
                alert_needed = False
            # D6.4: late night is an independent trigger, regardless of
            # boundary. Idempotent when the caller (e.g. `check`) already
            # included it via check_alert_needed()'s own result.
            if is_late_night:
                alert_needed = True
                if AlertReason.LATE_NIGHT not in alert_reasons:
                    alert_reasons = list(alert_reasons) + [AlertReason.LATE_NIGHT]

            return build_envelope_safe(
                boundary=boundary,
                time_provider=self.time_provider,
                zone_resolution=self.timing_policy.user_zone,
                user_zone_info=self._user_zone_info,
                session_id=session_id,
                now=now,
                previous_end_utc=previous_end_utc,
                current_start_utc=current_start_utc,
                session_continuation_threshold_minutes=self.timing_policy.session_continuation_threshold_minutes,
                work_streak=self._get_work_streak(),
                late_night_hour=late_night_hour,
                late_night_end_hour=late_night_end_hour,
                is_late_night=is_late_night,
                alert_needed=alert_needed,
                alert_reasons=alert_reasons,
                ambiguous_boundary_timestamp=ambiguous_boundary_timestamp,
            )
        except Exception:
            try:
                emitted_at_utc = self.time_provider.utc_now().isoformat()
            except Exception:
                emitted_at_utc = None
            return {
                "envelope_schema": ENVELOPE_SCHEMA_VERSION,
                "envelope_status": EnvelopeStatus.UNAVAILABLE,
                "envelope_status_reasons": [EnvelopeStatusReason.GENERATION_ERROR],
                "emitted_at_utc": emitted_at_utc,
            }

    def start_session(self, session_id: Optional[str] = None) -> Dict:
        """
        Start a new work session or continue existing one.

        v8.13.0 - Respects enabled flag

        Returns:
            Updated state with session initialized, or default state if disabled

        Raises:
            ValueError: if an explicit `session_id` is supplied and does not
                match the safe session-id charset (SEC-TRANSFER-9.11.0-005,
                CWE-22) -- this id later flows into handoff archive filenames,
                so it is rejected at creation time, before any state mutation.
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        # SEC-TRANSFER-9.11.0-005 (P3, CWE-22): validate a caller-supplied id
        # BEFORE anything else -- this parameter is not currently exposed via
        # the CLI, but the API itself must not accept an unsafe value that
        # would later be embedded in a handoff archive filename.
        if session_id is not None and not _is_valid_session_id(session_id):
            raise ValueError(
                f"Invalid session_id {session_id!r}: must match "
                f"{_SESSION_ID_PATTERN.pattern} (SEC-TRANSFER-9.11.0-005)."
            )

        # FEAT-TRANSFER-9.11.0-001 (v9.11.0 Increment 2): checked BEFORE
        # anything else mutates state, per the master plan's "/session start
        # integration" requirement -- these are read-only advisories, never
        # blocking, and must never raise (a broken marker/handoff file must
        # not prevent starting a session).
        self._warn_if_transfer_incomplete()
        self._point_to_fresh_handoff_brief()

        state = self.load_state()
        now = self.time_provider.utc_now()

        # v9.12.0 A2 phase (b) (IMPL-002 closure, ADR D6.2): previously a
        # hardcoded `30` that made
        # `safety.session_tracking.session_continuation_threshold_minutes`
        # have NO EFFECT on enforced behavior no matter what it was edited
        # to. Now sourced from the single timing_policy.py loader -- editing
        # this key in protocol.config.yaml now changes the actual
        # continuation boundary.
        continuation_threshold_minutes = self.timing_policy.session_continuation_threshold_minutes

        # Check if there's an active session from < continuation_threshold_minutes ago
        if state['current_session']['session_active']:
            # v9.10.2 item-5 carried note: normalize via _parse_utc (BUG-SESSION-001
            # precedent) instead of a bare datetime.fromisoformat(). A naive legacy
            # timestamp (no UTC offset) used to raise TypeError here, caught by the
            # except below and treated as an EXPIRED session -- silently discarding
            # a still-continuing legacy session instead of continuing it.
            last_time = _parse_utc(state['current_session']['last_interaction_time'])
            if last_time is not None:
                # Toji audit 2026-08-06 (CODE-001, MEDIUM): route this
                # policy-bearing subtraction through the shared health-gated
                # operation instead of a raw `(now - last_time)`. Fail-closed
                # choice for THIS consumer: an anomalous gap (future
                # timestamp / rollback / implausible) must never be trusted
                # to mean "still within the continuation window" -- treat it
                # as expired. This routes the session through the SAME
                # conservative-under-anomaly machinery
                # `_classify_and_carry_work_streak()` already applies to an
                # anomalous `last_trusted_boundary_utc` gap (D7.5: never
                # closes the streak on an anomaly either) instead of a
                # second, divergent anomaly policy for this specific gap.
                gap_minutes, health = self._health_gated_minutes(last_time, now, now=now)
                if gap_minutes is None:
                    print(
                        f"[!] CODE-001: continuation-gap clock health "
                        f"{health.state if health else 'unknown'} "
                        f"({health.reason if health else 'n/a'}) -- treating "
                        "session as expired rather than trusting the "
                        "anomalous gap.",
                        file=sys.stderr,
                    )
                    gap_minutes = float('inf')
            else:
                # Missing/unparseable timestamp - treat as expired session
                print(f"[!] Invalid timestamp in session state. Starting new session.")
                gap_minutes = float('inf')

            if gap_minutes < continuation_threshold_minutes:
                # Continue existing session
                print(f"[STATUS] Continuing active session (gap: {gap_minutes:.1f} minutes)")
                state['current_session']['last_interaction_time'] = now.isoformat()
                self.save_state(state)
                return state
            else:
                # Session expired, archive it
                print(f"[PAUSED] Previous session expired ({gap_minutes:.1f} min gap). Starting new session.")
                # Toji audit 2026-08-06 (DESIGN-001, HIGH direct fix, ADR
                # D7.3-D7.5): pass the session's own last REAL measured
                # interaction instant as the archive's trusted end boundary
                # -- NOT a fresh observation instant. See
                # `_archive_session()`'s `end_override` docstring for why:
                # using `utc_now()` here (the pre-fix behavior) silently
                # converted the entire idle gap into "work" AND erased it
                # from ever being evaluated as a qualifying break. `last_time`
                # is still the best available "last real activity" boundary
                # even when the gap FROM it was itself just flagged
                # health-anomalous above (that anomaly is about trusting the
                # ELAPSED time, not about `last_time`'s own validity as an
                # instant) -- the conservative D7.5 carry-forward machinery
                # downstream handles a subsequently-anomalous boundary
                # correctly either way.
                self._archive_session(state, end_override=last_time)

        # v9.12.0 A3 (ADR D7.3, SEC-001 direct fix): classify against the
        # durable work_streak record -- NEVER against the just-reset/
        # about-to-be-recreated current_session object below (that
        # comparison is the SEC-001 defect itself). Runs for BOTH the
        # "session expired, archive it" branch above and the "nothing was
        # active at all" case that falls straight through to here.
        work_streak = self._classify_and_carry_work_streak(now, time_schema=self._get_time_schema())
        self._update_work_streak(work_streak)

        # Start new session
        session_id = session_id or f"session_{now.strftime('%Y%m%d_%H%M%S')}"

        state['current_session'] = {
            "session_id": session_id,
            "session_active": True,
            "start_time": now.isoformat(),
            "last_interaction_time": now.isoformat(),
            "last_alert_time": None,
            "alert_count": 0,
            "escalation_level": 0,
            "user_last_choice": None,
            "break_acknowledged": False,
            # SEC-001 direct fix: restore the high-risk block across the
            # session-lifecycle boundary from the durable work_streak record,
            # instead of unconditionally resetting it to False as pre-A3
            # code did (the exact defect the audit identified).
            "high_risk_operations_blocked": bool(work_streak.get("high_risk_block_active")),
            # Toji audit 2026-08-06 (IMPL-001, MEDIUM direct fix): this
            # session's own streak-contribution baseline. Left None (NOT
            # `now.isoformat()`) by design -- `update_interaction()`/
            # `_archive_session()` fall back to the session's CURRENT
            # `start_time` whenever this is None, which correctly tracks a
            # `start_time` mutated after session creation (e.g. a
            # continuation-threshold test backdating it). It is set to a
            # concrete instant ONLY by `_resolve_pending_break()`, at the
            # moment a qualifying break is verified -- from that point on,
            # this session's streak contribution is measured from the break
            # completion instant, never unconditionally from `start_time`
            # again (the fix for "reaccumulation of all pre-break work").
            "streak_contribution_start_time": None,
            # SEC-002 direct fix: break-initiation/completion pair state.
            # None until `record_break()` initiates a pending break;
            # `_resolve_pending_break()` (called from `update_interaction()`)
            # is the only place that resolves and clears it.
            "pending_break_started_utc": None,
            "pending_break_reported_minutes": None,
        }

        state['session_metrics'] = self._default_state()['session_metrics']

        print(f"[OK] New session started: {session_id}")
        self.save_state(state)
        return state

    def _resolve_pending_break(self, state: Dict, now: datetime) -> None:
        """Toji audit 2026-08-06 (SEC-002, HIGH direct fix; ADR
        D3.1/D7.4/D7.5's lifecycle-event contract: "the existing break ->
        continue lifecycle is the natural pair"). Called at the top of
        `update_interaction()` -- i.e. on every `continue`/`resume` and any
        auto-started interaction -- to resolve a break `record_break()`
        INITIATED but never itself completes.

        `record_break()` no longer clears `high_risk_operations_blocked` /
        the `work_streak` from a caller-REPORTED duration alone (that was
        the SEC-002 defect: a claimed duration, with no elapsed-time
        verification, immediately cleared protection). It only records
        `pending_break_started_utc` -- the break-INITIATION instant. THIS
        method is where the break actually QUALIFIES: it measures the REAL
        elapsed gap between that instant and `now`, health-gated
        (CODE-001), and clears protection ONLY when that measured gap is
        itself clock-health `ok` and meets `minimum_break_minutes`.

        On any other outcome -- no pending break, an unhealthy gap
        (rollback-detected/skew-suspected), or a healthy-but-too-short gap
        -- protection is PRESERVED (SEC-002's explicit requirement:
        "Preserve the block on missing, future, rollback, implausible, or
        incomplete break evidence"). The pending marker is always cleared
        once evaluated -- a resolved question, answered either way -- so a
        single `break` call is never silently re-evaluated against an
        ever-growing gap on every future interaction indefinitely.

        Also implements the IMPL-001 direct fix (ADR D7.2/D7.4): on a
        VERIFIED qualifying break, `current_session.streak_contribution_
        start_time` is advanced to `now` -- the explicit baseline
        `update_interaction()` (below) measures this session's OWN streak
        contribution from, instead of unconditionally re-measuring from the
        session's original `start_time` and silently restoring all
        pre-break work into the just-closed streak.

        Mutates `state` in place. Never raises -- a broken pending-break
        marker must never crash the interaction path that calls this.
        """
        pending_raw = state['current_session'].get('pending_break_started_utc')
        if not pending_raw:
            return

        pending_started = _parse_utc(pending_raw)
        minimum_break_minutes = state.get('thresholds', {}).get(
            'minimum_break_minutes', self.timing_policy.minimum_break_minutes
        )
        break_minutes, health = self._health_gated_minutes(pending_started, now, now=now)

        if break_minutes is not None and break_minutes >= minimum_break_minutes:
            # SEC-002 direct fix: a VERIFIED (measured, health-gated)
            # qualifying break -- clear protection now, for real.
            state['current_session']['high_risk_operations_blocked'] = False
            # IMPL-001 direct fix: explicit baseline at the qualifying-break
            # boundary -- see docstring above.
            state['current_session']['streak_contribution_start_time'] = now.isoformat()
            closed = _default_work_streak_shape()
            closed['streak_start_utc'] = now.isoformat()
            closed['last_trusted_boundary_utc'] = now.isoformat()
            closed['last_qualifying_break_utc'] = now.isoformat()
            closed['last_qualifying_break_duration_minutes'] = break_minutes
            closed['high_risk_block_active'] = False
            self._update_work_streak(closed)
            print(
                f"[OK] SEC-002: qualifying break verified ({break_minutes:.1f} "
                f"min measured, >= {minimum_break_minutes} min required) -- "
                "protection cleared."
            )
        else:
            if pending_started is None:
                reason = "pending break start timestamp missing/unparseable"
            elif health is not None:
                reason = health.reason
            else:
                reason = "insufficient elapsed time"
            print(
                f"[!] SEC-002: break not verified as qualifying ({reason}) -- "
                "protection status unchanged (preserved on missing/future/"
                "rollback/implausible/incomplete break evidence).",
                file=sys.stderr,
            )

        state['current_session']['pending_break_started_utc'] = None
        state['current_session']['pending_break_reported_minutes'] = None

    def update_interaction(self, _retry_count: int = 0, _max_retries: int = 1) -> Dict:
        """
        Record a new interaction in the current session.

        v8.13.0 - Respects enabled flag

        Args:
            _retry_count: Internal retry counter (do not set manually)
            _max_retries: Maximum retries for session reset (default: 1)

        Returns:
            Updated state with interaction timestamp, or default state if disabled

        Raises:
            RuntimeError: If session cannot be started/reset after max retries
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        if _retry_count > _max_retries:
            raise RuntimeError("Exceeded maximum retries to reset session. Session state may be corrupted.")

        state = self.load_state()

        if not state['current_session']['session_active']:
            # Auto-start session if not active
            try:
                return self.start_session()
            except Exception as e:
                raise RuntimeError(f"Failed to start session: {e}")

        now = self.time_provider.utc_now()

        # Toji audit 2026-08-06 (SEC-002/IMPL-001 direct fix): resolve any
        # pending break BEFORE computing this call's durations -- a
        # just-qualified break must already be reflected in both
        # `high_risk_operations_blocked` and the streak-contribution
        # boundary the flush below reads.
        self._resolve_pending_break(state, now)

        state['current_session']['last_interaction_time'] = now.isoformat()

        # Calculate duration
        start_time = state['current_session'].get('start_time')
        if not start_time:
            print("[!] Session start_time is missing. Resetting session.")
            try:
                return self.update_interaction(_retry_count=_retry_count + 1, _max_retries=_max_retries)
            except Exception as e:
                raise RuntimeError(f"Failed to reset session (missing start_time): {e}")

        # v9.10.2 item-5 carried note: use the shared _parse_utc() normalizer
        # (BUG-SESSION-001 precedent) instead of a bare datetime.fromisoformat()
        # plus a hand-rolled, naive-only tzinfo guard (PATCH-SESSION-006). The
        # old guard covered naive timestamps but not the 'Z'-suffix / aware-
        # non-UTC normalization _parse_utc already handles centrally.
        start = _parse_utc(start_time)
        if start is None:
            print("[!] Invalid session start_time format. Resetting session.")
            try:
                return self.update_interaction(_retry_count=_retry_count + 1, _max_retries=_max_retries)
            except Exception as e:
                raise RuntimeError(f"Failed to reset session (invalid start_time format): {e}")

        # Toji audit 2026-08-06 (CODE-001, MEDIUM): health-gate this
        # policy-bearing subtraction instead of a raw `(now - start)`.
        # Fail-closed choice for THIS consumer: an anomalous gap must never
        # silently produce a fabricated (possibly negative/inflated)
        # duration -- retain the last PERSISTED value instead of trusting
        # the anomalous one.
        duration_minutes, duration_health = self._health_gated_minutes(start, now, now=now)
        if duration_minutes is None:
            print(
                f"[!] CODE-001: session duration clock health "
                f"{duration_health.state if duration_health else 'unknown'} "
                f"({duration_health.reason if duration_health else 'n/a'}) -- "
                "retaining last known total_duration_minutes rather than "
                "trusting the anomalous gap.",
                file=sys.stderr,
            )
            duration_minutes = float(state['session_metrics'].get('total_duration_minutes') or 0)
        else:
            state['session_metrics']['total_duration_minutes'] = int(duration_minutes)

        # Update continuous work time (time since last break)
        # v9.10.2 item-5 carried note: this branch previously had NO try/except
        # at all -- a naive or malformed break timestamp raised ValueError/
        # TypeError uncaught, crashing update_interaction() (called on every
        # interaction). _parse_utc() normalizes naive->UTC and returns None on
        # anything unparseable, so we fail soft to duration_minutes instead.
        if state['session_metrics']['break_timestamps']:
            last_break = _parse_utc(state['session_metrics']['break_timestamps'][-1])
            if last_break is None:
                continuous_minutes = duration_minutes
            else:
                # CODE-001: same health-gated treatment as the total
                # duration above.
                continuous_gap, continuous_health = self._health_gated_minutes(last_break, now, now=now)
                if continuous_gap is None:
                    print(
                        f"[!] CODE-001: continuous-work clock health "
                        f"{continuous_health.state if continuous_health else 'unknown'} "
                        f"({continuous_health.reason if continuous_health else 'n/a'}) "
                        "-- retaining last known continuous_work_minutes "
                        "rather than trusting the anomalous gap.",
                        file=sys.stderr,
                    )
                    continuous_minutes = float(state['session_metrics'].get('continuous_work_minutes') or 0)
                else:
                    continuous_minutes = continuous_gap
        else:
            continuous_minutes = duration_minutes

        state['session_metrics']['continuous_work_minutes'] = int(continuous_minutes)

        # v9.12.0 A3 (ADR D7.7) + Toji audit 2026-08-06 (IMPL-001, MEDIUM
        # direct fix): flush the incremental accumulated-minutes delta on
        # every recorded interaction, piggybacking on this function's
        # existing last_interaction_time persistence path (D7.7's explicit
        # mechanism) rather than only at end_session(). IMPL-001 fix: this
        # session's OWN contribution to the streak is measured from
        # `streak_contribution_start_time` (set to `start_time` at session
        # start by `start_session()`, and advanced to the qualifying-break
        # completion instant by `_resolve_pending_break()` above) -- NEVER
        # from the session's original `start_time` unconditionally, which
        # is what silently restored all pre-break work into a just-closed
        # streak. `.get(...) or start_time` keeps this backward compatible
        # with any already-active session predating this field.
        contribution_start_raw = state['current_session'].get('streak_contribution_start_time')
        contribution_start = _parse_utc(contribution_start_raw) if contribution_start_raw else None
        if contribution_start is None or contribution_start < start:
            # Not set (no qualifying break yet this session), unparseable,
            # or somehow predating the session's own (possibly since-
            # mutated) `start_time` -- fall back to `start` ITSELF, freshly
            # parsed above from the session's CURRENT `start_time`. This
            # correctly tracks a `start_time` that was mutated after session
            # creation (e.g. backdated) -- exactly today's pre-IMPL-001
            # behavior for a session with no qualifying break yet.
            contribution_start = start

        # CODE-001: health-gate the streak-flush subtraction too.
        streak_minutes, streak_health = self._health_gated_minutes(contribution_start, now, now=now)
        if streak_minutes is not None:
            work_streak = self._get_work_streak()
            baseline = work_streak.get('_streak_session_baseline_minutes') or 0
            new_total = baseline + streak_minutes
            if new_total > (work_streak.get('accumulated_protected_work_minutes') or 0):
                work_streak['accumulated_protected_work_minutes'] = new_total
                self._update_work_streak(work_streak)
        elif streak_health is not None:
            # CODE-001 fail-closed: never silently flush an anomalous gap
            # into the safety-critical accumulated total -- skip this
            # flush; the next healthy interaction catches up (D7.7's
            # already-accepted bounded residual).
            print(
                f"[!] CODE-001: work-streak flush skipped this interaction "
                f"-- clock health {streak_health.state} ({streak_health.reason}).",
                file=sys.stderr,
            )

        # Log to security review (EXTENSION 3: PATCH-SESSION-005)
        self._log_session_to_security_review('session_update', state)

        self.save_state(state)
        return state

    def check_alert_needed(self, debounce_override: int = None) -> Tuple[bool, str, Dict]:
        """
        Check if a work session alert should be issued.

        v8.13.0 - Respects enabled flag

        Args:
            debounce_override: CLI --debounce argument (v8.13.0)

        Returns:
            (should_alert, alert_level, alert_context)
            alert_level: "standard", "escalated", "critical"
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return False, None, {}

        state = self.load_state()

        if not state['current_session']['session_active']:
            return False, None, {}

        now = self.time_provider.utc_now()
        start_time = state['current_session'].get('start_time')
        if not start_time:
            print("[!] Session start_time is missing. Cannot check alert.")
            return False, None, {}

        # BUG-SESSION-001 (v9.3.0): normalize naive->aware via _parse_utc so the
        # aware/naive subtraction below can never raise (safety-critical path).
        start = _parse_utc(start_time)
        if start is None:
            print("[!] Invalid session start_time format. Cannot check alert.")
            return False, None, {}

        # Toji audit 2026-08-06 (CODE-001, MEDIUM): health-gate the primary
        # duration subtraction. Fail-closed choice for THIS consumer: a
        # WELLBEING safety check must never silently UNDER-alert because a
        # gap could not be trusted -- an anomaly forces an alert (with its
        # own `clock_anomaly` reason code) rather than being ignored.
        duration_minutes, duration_health = self._health_gated_minutes(start, now, now=now)
        clock_anomaly = duration_minutes is None
        if clock_anomaly:
            print(
                f"[!] CODE-001: session duration clock health "
                f"{duration_health.state if duration_health else 'unknown'} "
                f"({duration_health.reason if duration_health else 'n/a'}) -- "
                "cannot trust elapsed duration for alert thresholds; forcing "
                "an alert rather than silently under-alerting.",
                file=sys.stderr,
            )
            duration_minutes = float(state['session_metrics'].get('total_duration_minutes') or 0)

        # v9.12.0 A3 (ADR D7 consequence, SEC-001 direct fix): wellbeing
        # alert thresholds MUST consume the ROLLING work-streak duration,
        # not just this session's own elapsed time -- otherwise a rapid
        # end+restart (SEC-001's exact exploit) resets the alert clock right
        # alongside the state it bypassed. Reduces to duration_minutes
        # exactly (rolling == current) whenever there is no prior streak
        # contribution, so single-session behavior is unchanged.
        work_streak = self._get_work_streak()
        rolling_minutes = self._rolling_streak_minutes(work_streak, duration_minutes)

        # Debounce check (v8.13.0 - PATCH-SESSION-004)
        # Skip alert if last alert was too recent (prevents spam during rapid prototyping)
        debounce_threshold = self._load_debounce_config(cli_override=debounce_override)
        last_alert_time = state['current_session'].get('last_alert_time')

        last_alert_dt = _parse_utc(last_alert_time)
        if last_alert_dt is not None:
            # CODE-001: same fail-closed direction as above -- an anomalous
            # gap must never silently SUPPRESS a needed alert via debounce.
            minutes_since_last_alert, debounce_health = self._health_gated_minutes(last_alert_dt, now, now=now)
            if minutes_since_last_alert is None:
                print(
                    f"[!] CODE-001: debounce-gap clock health "
                    f"{debounce_health.state if debounce_health else 'unknown'} "
                    f"({debounce_health.reason if debounce_health else 'n/a'}) "
                    "-- not suppressing via debounce.",
                    file=sys.stderr,
                )
            elif minutes_since_last_alert < debounce_threshold:
                # Alert debounced - too soon since last alert
                return False, None, {}

        thresholds = state['thresholds']
        escalation_level = state['current_session']['escalation_level']

        # Determine if alert is needed
        alert_needed = False
        alert_level = "standard"
        # v9.12.0 A4 (ADR D6.5, IMPL-001 direct fix): structured, combinable
        # reason codes -- late-night and every duration threshold are each
        # independently detectable, so a result can carry MULTIPLE
        # simultaneous causes (e.g. ["duration_critical", "late_night"]),
        # which a single `alert_level` string can never represent. The
        # trigger CONDITIONS below are otherwise UNCHANGED from pre-A4
        # (byte-for-byte non-regression) -- reason codes are appended
        # alongside each existing `alert_needed = True` assignment; the one
        # NEW independent trigger is late-night, appended after this block.
        reasons: List[str] = []

        # Check if first alert threshold reached (4 hours) -- against the
        # ROLLING streak duration (v9.12.0 A3), not just this session's own.
        if rolling_minutes >= thresholds['initial_alert_minutes'] and state['current_session']['alert_count'] == 0:
            alert_needed = True
            alert_level = "standard"
            reasons.append(AlertReason.DURATION_INITIAL)

        # Check if escalated alert needed (user chose continue + time passed)
        elif escalation_level > 0:
            # BUG-SESSION-001 (v9.3.0): this branch previously parsed last_alert_time
            # with a bare datetime.fromisoformat() and NO naive->aware guard (and no
            # try/except), so a naive legacy timestamp here crashed the entire
            # check-and-record path, silently disabling the wellbeing safety alerts.
            escalation_last_alert = _parse_utc(state['current_session'].get('last_alert_time'))
            if escalation_last_alert is not None:
                # CODE-001: same fail-closed direction -- an anomalous gap
                # must never silently SUPPRESS a due escalated alert.
                minutes_since_alert, escalation_health = self._health_gated_minutes(
                    escalation_last_alert, now, now=now
                )

                if minutes_since_alert is None:
                    print(
                        f"[!] CODE-001: escalation-gap clock health "
                        f"{escalation_health.state if escalation_health else 'unknown'} "
                        f"({escalation_health.reason if escalation_health else 'n/a'}) "
                        "-- treating escalated alert as due.",
                        file=sys.stderr,
                    )
                    alert_needed = True
                    alert_level = "escalated"
                    reasons.append(AlertReason.DURATION_ESCALATED)
                elif minutes_since_alert >= thresholds['escalated_alert_minutes']:
                    alert_needed = True
                    alert_level = "escalated"
                    reasons.append(AlertReason.DURATION_ESCALATED)

        # Check if critical threshold reached (6+ hours) -- rolling duration.
        if rolling_minutes >= thresholds['critical_session_minutes']:
            alert_needed = True
            alert_level = "critical"
            reasons.append(AlertReason.DURATION_CRITICAL)

        # Check if maximum continuous work threshold reached (8+ hours) --
        # rolling duration. This is the absolute maximum - enforce stricter
        # read-only mode.
        if rolling_minutes >= thresholds['max_continuous_minutes']:
            alert_needed = True
            alert_level = "maximum"  # Highest severity level
            reasons.append(AlertReason.DURATION_MAXIMUM)

        # BUG-SESSION-005: is_late_night must be computed from LOCAL wall-clock
        # time (with midnight wrap), never from the UTC `now` above -- see
        # _is_late_night() for the single implementation and rationale.
        #
        # v9.12.0 A4 (ADR D6.4, IMPL-001 direct fix): late night is now an
        # INDEPENDENT alert reason -- it can set alert_needed=True on its
        # own, exactly as the duration thresholds already do, instead of
        # only ever being attached to context as inert metadata. A fresh
        # (0-minute) session starting at/after late_night_hour local now
        # produces a checkpoint.
        is_late = _is_late_night(_local_now(now, self._user_zone_info), thresholds)
        if is_late:
            alert_needed = True
            reasons.append(AlertReason.LATE_NIGHT)

        # Toji audit 2026-08-06 (CODE-001, MEDIUM): the primary duration gap
        # was clock-health anomalous (see above) -- surface it as its own
        # independent alert trigger, same pattern as late-night.
        if clock_anomaly:
            alert_needed = True
            reasons.append(AlertReason.CLOCK_ANOMALY)

        # Build alert context
        context = {
            "duration_minutes": int(duration_minutes),
            # v9.12.0 A3: the ROLLING work-streak duration that actually
            # drove the threshold comparisons above -- equals
            # duration_minutes when there is no prior streak contribution.
            "rolling_streak_minutes": int(rolling_minutes),
            "duration_formatted": self._format_duration(duration_minutes),
            "alert_level": alert_level,
            # v9.12.0 A4 (ADR D6.5): the combinable reason-code list. Never
            # absent -- always a list (possibly empty), even when
            # alert_needed is False, so a caller can safely iterate it
            # without a None-guard.
            "alert_reasons": reasons,
            "is_late_night": is_late,
            "continuous_minutes": state['session_metrics']['continuous_work_minutes'],
            "alert_count": state['current_session']['alert_count']
        }

        return alert_needed, alert_level, context

    def format_no_alert_message(self, state: Dict = None) -> str:
        """
        Build the CLI message for the "no alert needed" case (`check` /
        `check-and-record`).

        2026-08-01 UX-honesty fix (Toji session-time-authority audit
        follow-up, audits/2026-08-01-toji-session-time-authority-claude-codex.md):
        previously both commands printed the bare "[OK] No alert needed" line
        whenever check_alert_needed() returned no alert -- even when NO
        session was active at all (check_alert_needed() bails out early on
        the `session_active` guard, same state this method reads). That is
        technically true (no alert fired) but misleading: wellbeing/duration
        tracking is idle, not merely quiet between thresholds. This adds an
        ASCII-only [INFO] line recommending the user start a session, while
        leaving the active-session output byte-for-byte unchanged.

        Args:
            state: Optional pre-loaded session state (as returned by
                load_state()). Callers that already have the state in hand
                (e.g. check_alert_needed()'s caller) can pass it directly to
                avoid a redundant reload; if omitted, load_state() (fail-soft,
                never raises) is called.

        Returns:
            The message to print. Active session: exactly "[OK] No alert
            needed" (unchanged from pre-fix behavior). No active session:
            that same line plus an appended "[INFO] ..." line, ASCII only.
        """
        if state is None:
            state = self.load_state()

        lines = ["[OK] No alert needed"]

        session_active = state.get('current_session', {}).get('session_active', False)
        if not session_active:
            lines.append(
                "[INFO] No active session - wellbeing tracking is idle. "
                "Start one for accurate duration/alert tracking: "
                "/session start (or: python .protocol-state/session_monitor.py start)"
            )

        return "\n".join(lines)

    def render_alert(self, context: Dict) -> str:
        """
        Render work session alert with actual data.

        v8.13.0 - Enhanced with custom message injection

        Args:
            context: Alert context from check_alert_needed()

        Returns:
            Rendered alert text with placeholders replaced and custom messages injected
        """
        if not self.template_file.exists():
            # Return minimal fallback template with custom messages
            custom_msg = self._inject_custom_messages(context)

            return f"""
[!] Extended Work Session Detected

**Duration:** {context.get('duration_formatted', 'Unknown')}
**Project:** {self._get_project_name()}

{custom_msg if custom_msg else 'You have been working for an extended period. Consider taking a break to maintain productivity and reduce errors.'}

**Options:**
1. Save progress and take a break (recommended)
2. Continue working (proceed with caution)
3. Or run /session transfer to end this session safely with a handoff brief so the next session resumes with full context

Template file not found at: {self.template_file}
"""

        with open(self.template_file, 'r', encoding='utf-8') as f:
            template = f.read()

        now = self.time_provider.utc_now()
        state = self.load_state()

        # BUG-SESSION-005 (BUG C): {DATE} was rendering a bare, unlabeled UTC
        # timestamp into a user-facing alert. Label local+UTC, same pattern
        # as get_session_summary()'s Current Time/Started fields.
        now_local = _local_now(now, self._user_zone_info)
        date_display = f"{now_local.strftime('%Y-%m-%d %H:%M %Z')} ({now.strftime('%Y-%m-%d %H:%M')} UTC)"

        # Build replacement values
        replacements = {
            '{DATE}': date_display,
            '{DURATION}': context.get('duration_formatted', 'Unknown'),
            '{PROJECT_NAME}': self._get_project_name(),
            '{LATE_NIGHT_FLAG}': '[LATE] YES - Late night work detected' if context.get('is_late_night') else '[DAY] No',
            '{CONTINUOUS_FLAG}': f"[!] {context.get('continuous_minutes', 0)} minutes without break" if context.get('continuous_minutes', 0) > 120 else '[OK] Recent breaks taken',
            # v9.12.0 A4 (ADR D6.5): the combinable reason-code list built by
            # check_alert_needed() (context['alert_reasons']), e.g.
            # "duration_critical, late_night". `.get(..., [])` keeps this
            # backward compatible with any pre-A4 caller/test fixture that
            # constructs a context dict without the key -- renders as an
            # empty string rather than raising.
            '{ALERT_REASONS}': ', '.join(context.get('alert_reasons') or []),
            '{BREAK_RECOMMENDATION}': self._get_break_recommendation(context),
            '{LATE_NIGHT_THRESHOLD}': f"{state['thresholds']['late_night_hour']}:00",
            # v9.12.0 A5 (IMPL-004 template-sync closure): the template's
            # "wraps past midnight until early morning" phrasing previously
            # had no parameterized end-hour to point at (only the START hour
            # was ever substituted). `.get(..., self.timing_policy...)`
            # mirrors the exact fallback pattern already established for
            # `late_night_end_hour` everywhere else it is read (BUG-SESSION-005),
            # so legacy state files predating this field are never broken.
            '{LATE_NIGHT_END_THRESHOLD}': (
                f"{state['thresholds'].get('late_night_end_hour', self.timing_policy.late_night_end_hour)}:00"
            ),
            # FEAT-TRANSFER-9.11.0-001 (v9.11.0 Increment 2, USER scope addition):
            # every wellness checkpoint (standard/escalated/critical/maximum)
            # renders through this same template, so this placeholder appears
            # at every alert level without needing per-level branching here.
            '{SESSION_TRANSFER_TIP}': self._get_session_transfer_tip(),
        }

        # Replace all placeholders
        rendered = template
        for placeholder, value in replacements.items():
            rendered = rendered.replace(placeholder, str(value))

        # Inject custom messages (v8.13.0)
        custom_msg = self._inject_custom_messages(context)
        if custom_msg:
            # Append custom messages after the standard template
            rendered += f"\n\n---\n\n{custom_msg}"

        return rendered

    def record_user_choice(self, choice: str) -> Dict:
        """
        Record user's response to work session alert.

        v8.13.0 - Respects enabled flag

        Args:
            choice: "save_and_break" or "continue"

        Returns:
            Updated state, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        # Validate input
        if choice not in ["save_and_break", "continue"]:
            raise ValueError(f"Invalid choice '{choice}'. Must be 'save_and_break' or 'continue'.")

        state = self.load_state()
        now = self.time_provider.utc_now()

        state['current_session']['user_last_choice'] = choice
        state['current_session']['last_alert_time'] = now.isoformat()
        state['current_session']['alert_count'] += 1
        state['session_metrics']['alerts_issued'] += 1

        if choice == "save_and_break":
            state['session_metrics']['breaks_chosen'] += 1
            state['current_session']['break_acknowledged'] = True
        elif choice == "continue":
            state['session_metrics']['continues_chosen'] += 1
            state['current_session']['escalation_level'] += 1

            # Toji audit 2026-08-06 (SEC-001, HIGH direct fix, CWE-841):
            # this branch used to compare the CACHED, per-current-session
            # `session_metrics.total_duration_minutes` against the critical
            # threshold -- a DIFFERENT authority than the one
            # `check_alert_needed()` actually used to decide the critical
            # alert that led here (the ROLLING work-streak duration, D7).
            # That field can be near-zero right after a restart (SEC-001's
            # own exploit) or simply stale within a long session, letting a
            # user receive a genuine critical alert, choose "continue", and
            # NOT have the block activate. Block activation now consumes
            # the EXACT SAME rolling-streak authority `check_alert_needed()`
            # consumes (`_rolling_streak_minutes()`), recomputed here from
            # the current session's OWN measured elapsed time (health-gated,
            # CODE-001) plus the durable streak baseline -- never the cached
            # per-session counter alone.
            work_streak = self._get_work_streak()
            start_time = state['current_session'].get('start_time')
            start = _parse_utc(start_time) if start_time else None
            session_elapsed_minutes, _health = self._health_gated_minutes(start, now, now=now)
            if session_elapsed_minutes is None:
                # No usable session start, or a clock-health anomaly on it
                # (CODE-001 fail-closed for this consumer): never let an
                # untrusted/absent elapsed reading silently UNDERSTATE the
                # rolling duration -- fall back to the durable streak's own
                # already-accumulated baseline alone (0 additional minutes
                # from this session), which is still the rolling authority,
                # just without this session's (untrustworthy) contribution.
                session_elapsed_minutes = 0.0
            rolling_minutes = self._rolling_streak_minutes(work_streak, session_elapsed_minutes)

            if rolling_minutes >= state['thresholds']['critical_session_minutes']:
                state['current_session']['high_risk_operations_blocked'] = True
                # v9.12.0 A3 (ADR D7.2's high_risk_block_active mirrors
                # current_session.high_risk_operations_blocked, SEC-001
                # direct fix): persist the block to the durable work_streak
                # record too, so it survives the lifecycle boundary this
                # local flag alone does not.
                work_streak['high_risk_block_active'] = True
                self._update_work_streak(work_streak)

        self.save_state(state)
        return state

    def record_break(self, duration_minutes: Optional[int] = None) -> Dict:
        """
        Record that a break STARTED.

        Toji audit 2026-08-06 (SEC-002, HIGH direct fix; ADR D3.1/D7.4/D7.5's
        lifecycle-event contract). Pre-fix, this method treated a
        caller-SUPPLIED `duration_minutes` as sufficient, on its own, to
        immediately clear both `current_session.high_risk_operations_blocked`
        and the persisted `work_streak` protection window -- an unverified
        CLAIM, not a measured elapsed-time pair. It no longer does either.

        This is now purely the BREAK-INITIATION half of a two-instant
        lifecycle pair (D7.4: "the existing break -> continue lifecycle is
        the natural pair"): it records `pending_break_started_utc` (THIS
        call's own authoritative instant) plus bookkeeping metrics (break
        count/timestamp history, continuous-work-timer reset, escalation
        reset), but makes NO protection decision. The COMPLETION half --
        the actual qualification check, measured against two authoritative,
        clock-health-gated instants -- happens the next time
        `update_interaction()` runs (the `continue`/`resume` CLI command, or
        any other interaction): see `_resolve_pending_break()`.

        `duration_minutes` (the CLI's still-accepted `break [minutes]`
        surface -- backward-compat requirement) is recorded ONLY as an
        informational NOTE (`pending_break_reported_minutes`) -- it is NEVER
        used to authorize clearing protection. Silence here (no protection
        change) is deliberate: no decision is made until
        `_resolve_pending_break()` later measures the real elapsed gap, so
        the block is preserved on missing, future, rollback-detected,
        implausible, or incomplete break evidence (SEC-002's explicit
        requirement) by construction -- there is no "claim" code path left
        to make that mistake.

        v8.13.0 - Respects enabled flag

        Args:
            duration_minutes: Caller-REPORTED (unverified) break duration --
                note-only; see docstring above. Never authorizes clearing
                protection.

        Returns:
            Updated state, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        state = self.load_state()
        now = self.time_provider.utc_now()

        state['session_metrics']['break_timestamps'].append(now.isoformat())
        state['session_metrics']['total_breaks'] += 1
        state['current_session']['escalation_level'] = 0  # Reset escalation
        state['current_session']['break_acknowledged'] = False

        # Reset continuous work timer
        state['session_metrics']['continuous_work_minutes'] = 0

        # SEC-002 direct fix: INITIATE, never COMPLETE, the break here. The
        # caller-reported duration is a NOTE ONLY (never authorization) --
        # see `_resolve_pending_break()` for the actual measured
        # qualification check.
        state['current_session']['pending_break_started_utc'] = now.isoformat()
        state['current_session']['pending_break_reported_minutes'] = duration_minutes

        # BUG-SESSION-005 (BUG C): label local+UTC instead of a bare unlabeled UTC time.
        print(
            f"[OK] Break started at {_local_now(now, self._user_zone_info).strftime('%H:%M %Z')} "
            f"({now.strftime('%H:%M')} UTC) -- SEC-002: protection clears only after a "
            "VERIFIED qualifying break is measured on your next interaction "
            "(e.g. 'continue'/'resume'), never from a reported duration alone."
        )
        self.save_state(state)
        return state

    def end_session(self) -> Dict:
        """
        End the current work session and archive it.

        v8.13.0 - Respects enabled flag

        Returns:
            Updated state with session ended, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        state = self.load_state()

        if state['current_session']['session_active']:
            self._archive_session(state)
            print("[OK] Session ended and archived")

            # Get archived session data (last entry in history)
            if state['session_history']:
                archived_session = state['session_history'][-1]

                # EXTENSION 2: State Management (PATCH-SESSION-005)
                # Update all protocol state files with session completion data
                self._update_project_state_on_session_end(archived_session)
                self._log_session_end_to_dev_notes(archived_session)
                self._log_session_end_to_domain_record(archived_session)

                # EXTENSION 3: Security Review (PATCH-SESSION-005)
                self._log_session_to_security_review('session_end', archived_session)
        else:
            # FEAT-TRANSFER-9.11.0-001 (v9.11.0 Increment 2, requirement 4):
            # 'end' (bare, or as the session-end step inside a 'transfer'
            # event run with no active session) must degrade gracefully with
            # a clear message -- never a traceback, and never silence either.
            print("[INFO] No active session to end (already ended, or never started). Nothing to do.")

        self.save_state(state)

        # NOTE: Cortex rebuild on session end is now coordinator-owned (v9.5.0, WI-15).
        # The coordinator fires cortex_trigger.py --level high --export via the
        # session-end registry event.  Direct _sync_cortex_index() call removed here.

        return state

    def is_high_risk_operation(self, command: Optional[str]) -> bool:
        """
        Check if a command is considered high-risk using literal string matching.

        v8.13.0 - Respects enabled flag

        Non-string or empty commands are treated as not high-risk.

        Args:
            command: Command string to check (None or empty treated as non-high-risk)

        Returns:
            True if command is high-risk, False if disabled or non-high-risk
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return False

        # Guard: Treat None, non-string, or empty/whitespace as non-high-risk
        if not isinstance(command, str) or not command.strip():
            return False

        # Normalize command for case-insensitive matching
        command_lower = command.lower()

        # Use literal string matching (faster and safer than regex)
        for literal in self._high_risk_literals:
            if literal in command_lower:
                return True

        return False

    def should_block_operation(self, operation: Optional[str]) -> Tuple[bool, str]:
        """
        Check if an operation should be blocked due to session state.

        Args:
            operation: Operation description or command (None or empty treated as non-high-risk)

        Returns:
            (should_block, reason) - reason is empty string if not blocked
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return False, ""

        state = self.load_state()

        if not state['current_session']['session_active']:
            return False, ""

        # Calculate live duration (BUG FIX: PATCH-SESSION-005 - SESSION-003)
        # Fixes CRITICAL bug where high-risk blocking never activated due to stale duration.
        # live_duration: computed from wall-clock start_time (accurate for running sessions).
        # stored_duration: total_duration_minutes recorded in state metrics — used in reason
        #   strings because it represents the duration that caused the blocking flag to be set
        #   (e.g. via record_user_choice) and is the value tests and humans expect to see.
        live_duration = self._calculate_current_duration(state)
        stored_duration = state['session_metrics'].get('total_duration_minutes', live_duration)
        # Use whichever is larger: live clock or stored metric (guards against clock skew in tests)
        duration_minutes = max(live_duration, stored_duration)
        thresholds = state['thresholds']

        # Check if 8-hour maximum continuous work threshold reached - BLOCK ALL OPERATIONS
        if duration_minutes >= thresholds['max_continuous_minutes']:
            reason = (
                f"🛑 [BLOCKED] MAXIMUM WORK LIMIT REACHED: {duration_minutes} minutes "
                f"({duration_minutes // 60}+ hours). You MUST take a break. "
                f"Session is now read-only."
            )
            return True, reason

        # Check if 6-hour critical threshold reached - block high-risk operations only
        if state['current_session']['high_risk_operations_blocked']:
            if self.is_high_risk_operation(operation):
                reason = (
                    f"🛑 High-risk operation blocked: Extended session "
                    f"({duration_minutes} min). Take a break first."
                )
                return True, reason

        return False, ""

    def get_session_summary(self) -> str:
        """
        Get human-readable session summary.

        Returns:
            Formatted session summary
        """
        state = self.load_state()

        if not state['current_session']['session_active']:
            return "No active session"

        metrics = state['session_metrics']
        current = state['current_session']

        # Validate start_time exists
        start_time = current.get('start_time')
        if not start_time:
            return "[!] Session state corrupted: start_time missing"

        # v9.10.2 item-5 carried note: use _parse_utc for consistency with the
        # rest of this module (also picks up 'Z'-suffix normalization); display
        # only, so no arithmetic risk either way, but keeping every timestamp
        # parse on the same centralized helper avoids future drift.
        #
        # BUG-SESSION-005 (BUG C): the stored `start_time` stays UTC (never
        # changed -- it is persisted, parsed elsewhere, and IDs derived from
        # it must remain stable/sortable). Only the DISPLAY string changes:
        # local wall-clock time with an explicit zone abbreviation, plus the
        # UTC value in parentheses for cross-reference.
        start_dt = _parse_utc(start_time)
        if start_dt is not None:
            start_local = _local_now(start_dt, self._user_zone_info)
            start_formatted = (
                f"{start_local.strftime('%Y-%m-%d %H:%M %Z')} "
                f"({start_dt.strftime('%Y-%m-%d %H:%M')} UTC)"
            )
        else:
            start_formatted = "Invalid timestamp"

        # Calculate live duration (BUG FIX: PATCH-SESSION-005 - SESSION-001)
        # Fixes bug where status command showed 0 minutes for long-running sessions
        current_duration = self._calculate_current_duration(state)
        current_continuous = self._calculate_current_continuous_work(state)
        # BUG-SESSION-005 (BUG C): same local+UTC labeling as `start_formatted`
        # above -- previously this printed a bare, unlabeled UTC timestamp.
        current_time_utc = self.time_provider.utc_now()
        current_time_local = _local_now(current_time_utc, self._user_zone_info)
        current_time = (
            f"{current_time_local.strftime('%Y-%m-%d %H:%M %Z')} "
            f"({current_time_utc.strftime('%Y-%m-%d %H:%M')} UTC)"
        )

        summary = f"""
[STATUS] **Work Session Summary**

**Current Time:** {current_time}
**Duration:** {self._format_duration(current_duration)}
**Continuous Work:** {self._format_duration(current_continuous)} since last break
**Breaks Taken:** {metrics['total_breaks']}
**Alerts Issued:** {metrics['alerts_issued']}
**Escalation Level:** {current['escalation_level']}
**High-Risk Blocking:** {'[BLOCKED] ENABLED' if current['high_risk_operations_blocked'] else '[OK] Disabled'}

**Session ID:** {current['session_id']} (UTC-stamped)
**Started:** {start_formatted}
"""
        return summary.strip()

    def _archive_session(self, state: Dict, end_override: Optional[datetime] = None):
        """Archive current session to history.

        Args:
            end_override: Toji audit 2026-08-06 (DESIGN-001, HIGH direct
                fix, ADR D7.3-D7.5). When archiving is triggered by IDLE
                EXPIRY (`start_session()`'s "session expired, archive it"
                branch), the caller passes the session's own
                `last_interaction_time` here -- the last REAL measured
                activity -- instead of leaving this method read a fresh
                `utc_now()` for BOTH the archived end AND the next
                `last_trusted_boundary_utc`. Using a fresh observation
                instant for both fields was the DESIGN-001 defect: it
                silently converted the ENTIRE idle gap into "work" (the
                fabricated end backdated the archived duration all the way
                to observation time) AND erased the idle gap from ever
                being evaluated as a qualifying break (the boundary this
                method just wrote was ~0 seconds away from the very next
                `start_session()` call that reads it). Passing the true
                last-interaction instant here means: (1) the archived
                `total_duration_minutes` reflects only genuinely measured
                active time (start -> last_interaction), and (2)
                `last_trusted_boundary_utc` is set to that SAME real
                instant, so the next `_classify_and_carry_work_streak()`
                call compares against it and evaluates the REAL idle
                interval (now - last interaction) through clock health -- a
                qualifying idle period can finally close the streak,
                exactly as a qualifying inter-session gap already does.
                Omitted (None, the default) for every other caller
                (`end_session()`'s explicit end, and any other direct
                `_archive_session()` call) -- those retain the EXISTING,
                unflagged behavior of a fresh `utc_now()` observation
                instant, unchanged.
        """
        if state['current_session']['session_active']:
            # Toji audit 2026-08-06 (CODE-001, MEDIUM): one fresh
            # authoritative "now" read, reused for every clock-health
            # evaluation in this method (never re-read mid-method, which
            # could itself introduce a spurious skew between two calls).
            health_now = self.time_provider.utc_now()

            # Calculate final duration from start to end (BUG FIX: PATCH-SESSION-005 - SESSION-002)
            # Fixes bug where archived sessions showed 0 minutes duration
            # v9.10.2 item-5 carried note: use _parse_utc (BUG-SESSION-001
            # precedent) so a naive legacy start_time computes the real elapsed
            # duration instead of silently falling back to the (possibly stale)
            # stored total_duration_minutes metric.
            end = end_override if end_override is not None else health_now
            start = _parse_utc(state['current_session']['start_time'])
            if start is not None:
                # CODE-001: health-gate this policy-bearing subtraction
                # instead of trusting a raw (end - start) unconditionally.
                gap_minutes, health = self._health_gated_minutes(start, end, now=health_now)
                if gap_minutes is not None:
                    actual_duration = int(gap_minutes)
                else:
                    # Fail-closed for archival (CODE-001): an anomalous
                    # start->end pair must never silently produce a
                    # fabricated (possibly negative/inflated) duration.
                    print(
                        f"[!] CODE-001: archive duration clock health "
                        f"{health.state if health else 'unknown'} "
                        f"({health.reason if health else 'n/a'}) -- falling "
                        "back to last known total_duration_minutes rather "
                        "than trusting the anomalous gap.",
                        file=sys.stderr,
                    )
                    actual_duration = state['session_metrics']['total_duration_minutes']
            else:
                # Fallback to stored value if timestamp invalid (shouldn't happen)
                actual_duration = state['session_metrics']['total_duration_minutes']

            archived = {
                "session_id": state['current_session']['session_id'],
                "start_time": state['current_session']['start_time'],
                "end_time": end.isoformat(),
                "total_duration_minutes": actual_duration,
                "total_breaks": state['session_metrics']['total_breaks'],
                "alerts_issued": state['session_metrics']['alerts_issued'],
                "continues_chosen": state['session_metrics']['continues_chosen']
            }

            state['session_history'].append(archived)

            # Keep only last 30 sessions
            if len(state['session_history']) > 30:
                state['session_history'] = state['session_history'][-30:]

            # v9.12.0 A3 (ADR D7 Lifecycle-event contract, SEC-001 direct
            # fix): reconcile any residual delta since the last
            # update_interaction() flush into accumulated_protected_work_minutes
            # (D7.7), and record this trusted END boundary for the NEXT
            # start_session()'s D7.3 comparison. Does NOT zero the streak --
            # only a verified qualifying break (D7.4, evaluated at the NEXT
            # start_session()) can do that.
            #
            # Toji audit 2026-08-06 (IMPL-001, MEDIUM direct fix, this
            # method is a SECOND call site of the same defect
            # `update_interaction()` already fixes): the residual reconciled
            # here must ALSO be measured from `streak_contribution_start_time`
            # (advanced past a mid-session qualifying break by
            # `_resolve_pending_break()`), never from the full session
            # `actual_duration` unconditionally -- otherwise a session that
            # had a mid-session qualifying break would have its already
            # correctly-limited accumulated total OVERWRITTEN, right here at
            # archive time, with the full pre+post-break duration.
            contribution_start_raw = state['current_session'].get('streak_contribution_start_time')
            contribution_start = _parse_utc(contribution_start_raw) if contribution_start_raw else None
            if contribution_start is None or (start is not None and contribution_start < start):
                # Not set, unparseable, or predating `start` -- fall back to
                # `start` itself (freshly parsed above from the CURRENT
                # `start_time`), same reasoning as update_interaction()'s
                # identical fallback.
                contribution_start = start

            work_streak = self._get_work_streak()
            baseline = work_streak.get('_streak_session_baseline_minutes') or 0
            if contribution_start is not None:
                streak_gap_minutes, streak_health = self._health_gated_minutes(
                    contribution_start, end, now=health_now
                )
            else:
                streak_gap_minutes, streak_health = None, None

            if streak_gap_minutes is not None:
                # int()-truncated to match this method's pre-existing
                # `actual_duration` precision (a sub-minute residual, e.g. an
                # end()-called-immediately-after-start() test, must round to
                # 0 here exactly as it always has -- a raw float would leak
                # a non-zero fractional value into a field every other
                # caller/test treats as whole minutes).
                final_total = baseline + int(streak_gap_minutes)
                if final_total > (work_streak.get('accumulated_protected_work_minutes') or 0):
                    work_streak['accumulated_protected_work_minutes'] = final_total
            elif streak_health is not None:
                print(
                    f"[!] CODE-001: final work-streak reconciliation skipped "
                    f"-- clock health {streak_health.state} ({streak_health.reason}).",
                    file=sys.stderr,
                )
            work_streak['last_trusted_boundary_utc'] = end.isoformat()
            work_streak['high_risk_block_active'] = bool(
                state['current_session'].get('high_risk_operations_blocked')
            )
            self._update_work_streak(work_streak)

            # Reset current session
            state['current_session'] = self._default_state()['current_session']

    def _format_duration(self, minutes: float) -> str:
        """Format duration in human-readable format."""
        hours = int(minutes // 60)
        mins = int(minutes % 60)

        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"
        else:
            return f"{mins} minutes"

    def _calculate_current_duration(self, state: Dict) -> int:
        """
        Calculate current session duration without updating state.

        PATCH-SESSION-005 (BUG FIX: SESSION-001)
        Calculates duration on-the-fly from start_time instead of reading stale metrics.

        CodeRabbit round-1 (PR #116): deliberately NOT routed through
        `_health_gated_minutes()` -- see the SCOPE NOTE on that method's
        own docstring block for the full reasoning (this is a live
        wall-clock read for display + `should_block_operation()`'s
        fail-SAFE blocking gate, where gating on anomaly would remove the
        blocking signal rather than strengthen it).

        Args:
            state: Session state dictionary

        Returns:
            Current session duration in minutes (0 if not active or invalid)
        """
        if not state['current_session']['session_active']:
            return 0

        start_time = state['current_session'].get('start_time')
        if not start_time:
            return 0

        # v9.10.2 item-5 carried note: use _parse_utc (BUG-SESSION-001 precedent).
        # The prior bare datetime.fromisoformat() + broad except silently
        # returned 0 minutes for any naive legacy start_time -- a session that
        # had genuinely run for hours would report "0 minutes" instead of
        # crashing, which is a worse failure mode (silently wrong, not visibly
        # broken) than the crash BUG-SESSION-001 fixed elsewhere.
        start = _parse_utc(start_time)
        if start is None:
            return 0  # Fallback on unparseable/missing timestamp
        now = self.time_provider.utc_now()
        return int((now - start).total_seconds() / 60)

    def _calculate_current_continuous_work(self, state: Dict) -> int:
        """
        Calculate continuous work duration without updating state.

        PATCH-SESSION-005 (BUG FIX: SESSION-001)
        Calculates time since last break on-the-fly.

        Args:
            state: Session state dictionary

        Returns:
            Continuous work duration in minutes (0 if not active or invalid)
        """
        if not state['current_session']['session_active']:
            return 0

        # v9.10.2 item-5 carried note: use _parse_utc (BUG-SESSION-001
        # precedent) so a naive legacy break timestamp is correctly normalized
        # instead of silently falling back to _calculate_current_duration()
        # (which reports a DIFFERENT, larger quantity -- total session
        # duration, not time-since-last-break).
        if state['session_metrics']['break_timestamps']:
            last_break = _parse_utc(state['session_metrics']['break_timestamps'][-1])
            if last_break is not None:
                now = self.time_provider.utc_now()
                return int((now - last_break).total_seconds() / 60)
            return self._calculate_current_duration(state)
        else:
            return self._calculate_current_duration(state)

    def _get_project_name(self) -> str:
        """Get current project name from protocol root."""
        return self.protocol_root.name

    def _get_break_recommendation(self, context: Dict) -> str:
        """Generate break recommendation based on context."""
        # Use custom message if configured (v8.13.0)
        if self.alert_customization['break_recommendation']:
            return self.alert_customization['break_recommendation']

        # Default recommendations
        duration = context.get('duration_minutes', 0)
        is_late = context.get('is_late_night', False)

        if duration >= 360:  # 6+ hours
            return "[STOP] STRONGLY RECOMMENDED - End session and rest"
        elif duration >= 300:  # 5 hours
            return "[!] Take 15-minute break minimum"
        elif duration >= 240:  # 4 hours
            return "[TIP] 5-10 minute break suggested"
        elif is_late:
            return "[LATE] Late night work - consider ending session"
        else:
            return "Continue with awareness"

    def _get_session_transfer_tip(self) -> str:
        """FEAT-TRANSFER-9.11.0-001 (v9.11.0 Increment 2, USER scope addition):
        recommend `/session transfer` alongside the existing wellness-alert
        recommendations (save & break / continue). Additive, not a
        replacement -- keeps both options and adds a third that ends the
        session safely with a regenerable handoff brief so the next session
        resumes with full context instead of losing the 'why'.

        Same fixed wording at every alert level (standard/escalated/critical/
        maximum) -- the recommendation to preserve continuity applies
        regardless of how severe the current alert is.
        """
        return (
            "Or run `/session transfer` to end this session safely with a "
            "handoff brief so the next session resumes with full context."
        )

    def _inject_custom_messages(self, context: Dict) -> str:
        """
        Inject custom alert messages from configuration.

        v8.13.0 - Configuration Enhancement

        Args:
            context: Alert context with duration_minutes, is_late_night, etc.

        Returns:
            Formatted custom message string, or empty string if no custom messages
        """
        messages = []
        duration_hours = context.get('duration_minutes', 0) / 60
        is_late = context.get('is_late_night', False)
        is_critical = duration_hours >= (self.alert_thresholds['critical_session_minutes'] / 60)

        # Company policy message
        if self.alert_customization['company_policy']:
            messages.append(f"**Company Policy:** {self.alert_customization['company_policy']}")

        # Late night warning
        if is_late and self.alert_customization['late_night_warning']:
            messages.append(f"**Late Night Alert:** {self.alert_customization['late_night_warning']}")

        # Critical warning (overrides break recommendation if critical)
        if is_critical and self.alert_customization['critical_warning']:
            # Replace {hours} placeholder
            critical_msg = self.alert_customization['critical_warning'].replace('{hours}', f"{duration_hours:.1f}")
            messages.append(f"**CRITICAL:** {critical_msg}")

        return "\n\n".join(messages) if messages else ""

    def record_agent_invocation(self, agent_name: str, is_direct: bool = True) -> Dict:
        """
        Record an agent invocation for bypass detection.

        v8.13.0 - PATCH-SESSION-004 Component 5

        Args:
            agent_name: Name of agent invoked (gojo, yuuji, megumi, etc.)
            is_direct: True if direct invocation, False if routed via Gojo

        Returns:
            Updated invocation tracker state
        """
        # Validate agent name
        valid_agents = ['gojo', 'yuuji', 'megumi', 'nobara', 'todo', 'maki', 'panda', 'inumaki', 'sukuna']
        agent_name_lower = agent_name.lower()

        if agent_name_lower not in valid_agents:
            raise ValueError(f"Invalid agent name: {agent_name}. Must be one of: {', '.join(valid_agents)}")

        # PATCH-STATE-001: Load tracker state using ProjectStateManager
        if self.state_manager:
            try:
                tracker = self.state_manager.get_agent_invocation_tracking()
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O
                tracker = None

        if not self.state_manager or tracker is None:
            # Legacy file I/O (backward compatibility)
            if not self.invocation_tracker_file.exists():
                print(f"[!] Agent invocation tracker not found at {self.invocation_tracker_file}")
                print("    Using default schema")
                # File should exist from PATCH-SESSION-004, but handle gracefully
                return {}

            try:
                with open(self.invocation_tracker_file, 'r', encoding='utf-8') as f:
                    tracker = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"[ERROR] Cannot read invocation tracker: {e}")
                return {}

        if not tracker.get('tracking_enabled', True):
            # Tracking disabled, silently skip
            return tracker

        # Update invocation counts
        now = self.time_provider.utc_now().isoformat()
        agent_data = tracker['invocations'].get(agent_name_lower, {})

        agent_data['total_count'] = agent_data.get('total_count', 0) + 1
        agent_data['last_invocation'] = now

        if agent_name_lower != 'gojo':
            # Track direct vs routed for non-Gojo agents
            if is_direct:
                agent_data['direct_invocations'] = agent_data.get('direct_invocations', 0) + 1
            else:
                agent_data['routed_invocations'] = agent_data.get('routed_invocations', 0) + 1

        tracker['invocations'][agent_name_lower] = agent_data
        tracker['_last_updated'] = now

        # Bypass detection (direct invocations of non-Gojo agents)
        if agent_name_lower != 'gojo' and is_direct and tracker.get('bypass_detection', {}).get('enabled', True):
            # Get current session duration
            session_state = self.load_state()
            if session_state.get('current_session', {}).get('session_active'):
                start_time_str = session_state['current_session'].get('start_time')
                if start_time_str:
                    # v9.10.2 item-5 carried note: use _parse_utc (BUG-SESSION-001
                    # precedent). The prior bare datetime.fromisoformat() + broad
                    # except silently SKIPPED bypass detection entirely for any
                    # naive legacy start_time -- a security-relevant detection
                    # going blind on legacy state is itself a defect.
                    start_time = _parse_utc(start_time_str)
                    if start_time is not None:
                        duration_minutes = int((self.time_provider.utc_now() - start_time).total_seconds() / 60)

                        # Detect bypass if session is long-running (>= threshold)
                        threshold = tracker.get('bypass_detection', {}).get('threshold_minutes', 30)
                        if duration_minutes >= threshold:
                            bypass_alert = {
                                "timestamp": now,
                                "agent": agent_name_lower,
                                "session_duration_minutes": duration_minutes,
                                "message": f"Direct {agent_name_lower} invocation during {duration_minutes}-minute session (bypasses Gojo monitoring)"
                            }
                            tracker['bypass_detection']['bypass_alerts'].append(bypass_alert)

        # PATCH-STATE-001: Save updated tracker using ProjectStateManager
        if self.state_manager:
            try:
                self.state_manager.update_agent_invocation_tracking(tracker)
                return tracker
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O

        # Legacy save (SEC-001 FIX: atomic write)
        try:
            # Atomic write pattern
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False,
                                              dir=self.invocation_tracker_file.parent,
                                              suffix='.tmp') as tmp_file:
                json.dump(tracker, tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic replace (POSIX rename guarantees atomicity)
            os.replace(tmp_path, self.invocation_tracker_file)
        except (IOError, OSError) as e:
            print(f"[ERROR] Cannot save invocation tracker: {e}")

        return tracker

    def _update_project_state_on_session_end(self, session_data: Dict):
        """
        Update project-state.json with session completion data.

        EXTENSION 2: State Management (PATCH-SESSION-005)
        Logs session metrics to project-state for aggregate tracking.

        Args:
            session_data: Archived session data with duration, breaks, alerts, etc.
        """
        project_state_file = self.protocol_root / ".protocol-state" / "project-state.json"

        if not project_state_file.exists():
            print(f"[WARN] project-state.json not found at {project_state_file}")
            return

        try:
            with open(project_state_file, 'r', encoding='utf-8') as f:
                project_state = json.load(f)

            # Update session tracking metrics
            tracking = project_state.setdefault('session_tracking', {})
            tracking['last_session_end'] = session_data['end_time']
            tracking['total_sessions'] = tracking.get('total_sessions', 0) + 1
            tracking['total_work_minutes'] = tracking.get('total_work_minutes', 0) + session_data['total_duration_minutes']

            # Atomic write
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False,
                                              dir=project_state_file.parent,
                                              suffix='.tmp') as tmp_file:
                json.dump(project_state, tmp_file, indent=2)
                tmp_path = tmp_file.name

            os.replace(tmp_path, project_state_file)
            print(f"[OK] Updated project-state.json with session metrics")

            # ISS-083: this write bypasses ProjectStateManager entirely (direct
            # read-modify-write of project-state.json), so it must attest itself
            # -- ProjectStateManager's own attestation hook never runs for this
            # code path.
            self._attest_write(project_state_file)

        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"[ERROR] Failed to update project-state.json: {e}")

    def _log_session_end_to_dev_notes(self, session_data: Dict):
        """
        Log session end to dev-notes.md.

        EXTENSION 2: State Management (PATCH-SESSION-005)
        Provides human-readable development log of work sessions.

        Args:
            session_data: Archived session data
        """
        dev_notes_file = self.protocol_root / ".protocol-state" / "dev-notes.md"

        if not dev_notes_file.exists():
            print(f"[WARN] dev-notes.md not found at {dev_notes_file}")
            return

        try:
            entry = f"""
## Work Session Ended - {session_data['end_time']}

**Session ID:** {session_data['session_id']}
**Duration:** {self._format_duration(session_data['total_duration_minutes'])}
**Breaks Taken:** {session_data['total_breaks']}
**Alerts Issued:** {session_data['alerts_issued']}
**Continues Chosen:** {session_data['continues_chosen']}

"""
            # BUG-SESSION-003: newline="\n" forces LF on Windows so that the
            # staged index blob (always LF under core.autocrlf=true) matches
            # the working-tree file.  Eliminates CRLF churn warnings and removes
            # any residual excuse for the DZP_ALLOW_PROTECTED_REWRITE override.
            with open(dev_notes_file, 'a', encoding='utf-8', newline="\n") as f:
                f.write(entry)

            print(f"[OK] Logged session end to dev-notes.md")

        except (IOError, OSError) as e:
            print(f"[ERROR] Failed to write to dev-notes.md: {e}")

    def _log_session_end_to_domain_record(self, session_data: Dict):
        """
        Log session end to domain.record.md (Gojo permission only).

        EXTENSION 3: Permission System (PATCH-SESSION-005)
        Strategic protocol tracking - only accessible when invoked by Gojo.

        Args:
            session_data: Archived session data
        """
        # Permission check: Only Gojo can update domain.record.md
        if not self._check_gojo_invocation():
            print(f"[SKIP] domain.record.md update skipped (requires Gojo invocation)")
            return

        domain_record_file = self.protocol_root / ".dzp-domain" / "domain.record.md"

        if not domain_record_file.exists():
            print(f"[WARN] domain.record.md not found at {domain_record_file}")
            return

        try:
            entry = f"""
### Session Completed - {session_data['end_time']}

- **Session ID:** {session_data['session_id']}
- **Duration:** {self._format_duration(session_data['total_duration_minutes'])}
- **Wellbeing Metrics:** {session_data['total_breaks']} breaks, {session_data['alerts_issued']} alerts, {session_data['continues_chosen']} continues
- **Session Pattern:** {'Extended session' if session_data['total_duration_minutes'] > 360 else 'Standard session'}

"""
            # BUG-SESSION-003: newline="\n" — see _log_session_end_to_dev_notes.
            with open(domain_record_file, 'a', encoding='utf-8', newline="\n") as f:
                f.write(entry)

            print(f"[OK] Logged session end to domain.record.md (Gojo permission)")

        except (IOError, OSError) as e:
            print(f"[ERROR] Failed to write to domain.record.md: {e}")

    def _log_session_to_security_review(self, event_type: str, session_data: Dict):
        """
        Log session events to security-review.md for audit trail.

        EXTENSION 3: Permission System (PATCH-SESSION-005)
        Tracks session lifecycle events for security monitoring and protocol compliance.

        Args:
            event_type: "session_update" or "session_end"
            session_data: Session state or archived session data
        """
        security_review_file = self.protocol_root / ".protocol-state" / "security-review.md"

        if not security_review_file.exists():
            print(f"[WARN] security review file not found at {security_review_file}")
            return

        try:
            now = self.time_provider.utc_now().strftime('%Y-%m-%d %H:%M:%S')

            if event_type == "session_update":
                duration = self._calculate_current_duration(session_data)
                entry = f"""
## Security Review - Session Update - {now}

**Event:** User interaction recorded
**Session Duration:** {self._format_duration(duration)}
**Safety Status:** {'[ALERT] Extended session' if duration > 360 else '[OK] Normal'}

"""
            elif event_type == "session_end":
                entry = f"""
## Security Review - Session End - {now}

**Event:** Work session ended
**Session ID:** {session_data['session_id']}
**Total Duration:** {self._format_duration(session_data['total_duration_minutes'])}
**Wellbeing Compliance:** {session_data['total_breaks']} breaks taken, {session_data['alerts_issued']} alerts acknowledged

"""
            else:
                return

            # BUG-SESSION-003: newline="\n" — see _log_session_end_to_dev_notes.
            with open(security_review_file, 'a', encoding='utf-8', newline="\n") as f:
                f.write(entry)

            print(f"[OK] Logged {event_type} to security review")

        except (IOError, OSError) as e:
            print(f"[ERROR] Failed to write security review: {e}")

    def sync_all_project_documents(self, include_git_operations: bool = True) -> Dict[str, any]:
        """
        Comprehensive sync of all project documents with secret scanning and git operations.

        This method performs a full checkpoint of all project documentation:
        1. Updates project-state.json via ProjectStateManager
        2. Prepares checkpoint content for domain.record.md, dev-notes.md,
           security-review.md in memory (SEC-SU-002: no TOCTOU gap)
        3. Scans prepared content for production secrets BEFORE writing
        4. Writes content to files only if scan passes (with backups per SEC-SU-003)
        5. Commits and pushes with user approval

        Args:
            include_git_operations: If True, performs git commit/push with approval

        Returns:
            Dict with sync results and status
        """
        results = {
            'success': False,
            'documents_updated': [],
            'secrets_found': [],
            'git_operations': {'attempted': False, 'success': False},
            'errors': []
        }

        print("[SYNC] Starting comprehensive project document sync...")

        # Step 1: Update project-state.json using ProjectStateManager
        try:
            if self.state_manager:
                state = self.state_manager.load_project_state()
                # Update last_updated timestamp
                state['project_metadata']['last_updated'] = self.time_provider.utc_now().isoformat()
                self.state_manager.save_project_state(state)
                results['documents_updated'].append('project-state.json')
                print("[OK] project-state.json synced via ProjectStateManager")
            else:
                results['errors'].append("ProjectStateManager not available")
                print("[WARN] ProjectStateManager not available, skipping project-state.json sync")
        except Exception as e:
            results['errors'].append(f"project-state.json sync failed: {e}")
            print(f"[ERROR] Failed to sync project-state.json: {e}")

        # SEC-SU-002 REMEDIATION: Prepare content in memory FIRST, scan BEFORE writing.
        # This eliminates the TOCTOU gap where files could be modified between
        # write and scan. Content is generated, scanned, then written only if clean.

        # Step 2: Prepare checkpoint content for all documents (in-memory)
        pending_writes = []  # List of (filepath, content, doc_name) tuples
        content_map = {}     # filename -> content for in-memory scanning

        # Prepare domain.record.md content
        if self._check_gojo_invocation():
            try:
                result = self._prepare_domain_record_content()
                if result:
                    pending_writes.append((result[0], result[1], 'domain.record.md'))
                    content_map['domain.record.md'] = result[1]
                    print("[PREP] domain.record.md content prepared (Gojo permission)")
            except Exception as e:
                results['errors'].append(f"domain.record.md prep failed: {e}")
                print(f"[ERROR] Failed to prepare domain.record.md: {e}")
        else:
            print("[SKIP] domain.record.md sync skipped (requires Gojo permission)")

        # Prepare dev-notes.md content
        try:
            result = self._prepare_dev_notes_content()
            if result:
                pending_writes.append((result[0], result[1], 'dev-notes.md'))
                content_map['dev-notes.md'] = result[1]
                print("[PREP] dev-notes.md content prepared")
        except Exception as e:
            results['errors'].append(f"dev-notes.md prep failed: {e}")
            print(f"[ERROR] Failed to prepare dev-notes.md: {e}")

        # Prepare security-review.md content
        try:
            result = self._prepare_security_review_content()
            if result:
                pending_writes.append((result[0], result[1], 'security-review.md'))
                content_map['security-review.md'] = result[1]
                print("[PREP] security-review.md content prepared")
        except Exception as e:
            results['errors'].append(f"security-review.md prep failed: {e}")
            print(f"[ERROR] Failed to prepare security-review.md: {e}")

        # Step 3: Scan prepared content for secrets BEFORE writing
        doc_names = [name for _, _, name in pending_writes]
        if doc_names:
            print("[SCAN] Scanning prepared content for production secrets (pre-write)...")
            secrets_found = self._scan_for_secrets(doc_names, content_map=content_map)
            results['secrets_found'] = secrets_found

            # Filter to high-confidence findings that should block writes
            high_confidence_secrets = [s for s in secrets_found if s.get('confidence') == 'high']

            if high_confidence_secrets:
                print(f"[WARNING] Found {len(high_confidence_secrets)} HIGH confidence secrets in prepared content!")
                for secret in high_confidence_secrets:
                    print(f"  - {secret['file']}: {secret['type']} at line {secret['line']} [{secret['confidence']}]")
                print("[ABORT] Blocking file writes due to high-confidence secret detection")
                results['errors'].append(f"Write blocked: {len(high_confidence_secrets)} high-confidence secrets detected in content")
            else:
                if secrets_found:
                    print(f"[INFO] Found {len(secrets_found)} potential findings (none high-confidence)")
                    for secret in secrets_found:
                        print(f"  - {secret['file']}: {secret['type']} at line {secret['line']} [{secret.get('confidence', 'unknown')}]")
                else:
                    print("[OK] No secrets detected in prepared content")

                # Step 4: Write content to files (scan passed)
                for filepath, content, doc_name in pending_writes:
                    try:
                        self._write_checkpoint(filepath, content)
                        results['documents_updated'].append(doc_name)
                        print(f"[OK] {doc_name} synced")
                    except Exception as e:
                        results['errors'].append(f"{doc_name} write failed: {e}")
                        print(f"[ERROR] Failed to write {doc_name}: {e}")

        # Step 5: Git operations with user approval
        if include_git_operations and results['documents_updated']:
            try:
                git_result = self._git_commit_and_push_with_approval(
                    files=results['documents_updated'],
                    secrets_found=results['secrets_found']
                )
                results['git_operations'] = git_result
            except Exception as e:
                results['errors'].append(f"Git operations failed: {e}")
                print(f"[ERROR] Git operations failed: {e}")

        results['success'] = len(results['documents_updated']) > 0 and len(results['errors']) == 0

        # NOTE: Cortex index after sync is now coordinator-owned (v9.5.0, WI-15).
        # The coordinator fires cortex_trigger.py --level medium via the
        # session-update registry event.  Direct _sync_cortex_index() call removed here.

        print(f"[SYNC] Sync completed. {len(results['documents_updated'])} documents updated.")
        return results

    # -----------------------------------------------------------------------
    # Workstream B helpers
    # -----------------------------------------------------------------------

    def _cortex_index_lock_exists(self) -> bool:
        """Return True if a *fresh* brain index.lock file exists (another indexer running).

        Lock path mirrors brain-index-hook.ps1: <data_dir>/index.lock.
        Computed dynamically so we don't hard-code the install-id hash.

        Staleness guard (v9.4.0): if the lock is older than _CORTEX_LOCK_STALE_SECONDS
        it is treated as orphaned (e.g. from a killed hook), reaped best-effort, and
        this method returns False so the caller proceeds to re-index.

        Fail-soft: any error resolving the path → return False (let indexer try).

        # DEPRECATED in v9.5.0 — Cortex sync now coordinator-owned. Remove in v9.6.0.
        """
        try:
            import subprocess as _sp
            brain_py = self.protocol_root / ".protocol-state" / "brain" / "brain.py"
            if not brain_py.exists():
                return False
            # Ask brain.py for its data_dir via a status --json call
            result = _sp.run(
                [sys.executable, str(brain_py), "--repo", str(self.protocol_root), "status", "--json"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return False
            import json as _json
            data = _json.loads(result.stdout)
            db_path = Path(data.get("db", ""))
            lock_path = db_path.parent / "index.lock"

            if not lock_path.exists():
                return False

            # Staleness guard: reap orphaned lock and allow indexing to proceed.
            if _lock_is_stale(lock_path):
                try:
                    lock_path.unlink()
                except Exception:
                    pass  # best-effort; still return False so indexing can attempt
                return False

            return True
        except Exception:
            return False

    def _sync_cortex_index(self, full: bool = False) -> Dict:
        """Incrementally (or fully) re-index DZP Cortex after a document sync.

        Workstream B implementation — always fail-soft (never raises).

        # DEPRECATED in v9.5.0 — Cortex sync now coordinator-owned (WI-15).
        # Direct callers should migrate to: dzp.py event session-update / session-end.
        # This method is retained as a stub for backward compatibility.
        # Scheduled for removal in v9.6.0.

        Args:
            full: If True, perform a full rebuild (no --incremental flag).
                  If False (default), add --incremental for faster updates.

        Returns:
            dict with keys: attempted, skipped, status, [error], [exit_code]
        """
        import subprocess as _sp

        result: Dict = {"attempted": True, "skipped": False, "status": "unknown"}

        brain_py = self.protocol_root / ".protocol-state" / "brain" / "brain.py"
        if not brain_py.exists():
            result.update({"skipped": True, "status": "unavailable",
                           "reason": "brain.py not found"})
            return result

        try:
            # Status gate: verify Cortex is operational before indexing.
            status_proc = _sp.run(
                [sys.executable, str(brain_py), "--repo", str(self.protocol_root), "status"],
                capture_output=True, text=True, timeout=30,
            )
            if status_proc.returncode != 0:
                result.update({"skipped": True, "status": "status_failed",
                               "reason": (status_proc.stderr or "status non-zero")[:200]})
                return result

            # Lock check: another indexer may be running.
            if self._cortex_index_lock_exists():
                result.update({"skipped": True, "status": "locked",
                               "reason": "index.lock exists; another indexer is running"})
                return result

            # Build index command.
            index_cmd = [sys.executable, str(brain_py), "--repo", str(self.protocol_root), "index"]
            if not full:
                index_cmd.append("--incremental")

            index_proc = _sp.run(
                index_cmd,
                capture_output=True, text=True, timeout=120,
            )
            result.update({
                "skipped": False,
                "status": "ok" if index_proc.returncode == 0 else "error",
                "exit_code": index_proc.returncode,
                "summary": (index_proc.stdout or "")[:400],
            })
            return result

        except _sp.TimeoutExpired as exc:
            result.update({"skipped": True, "status": "timeout",
                           "error": f"indexer timed out after {exc.timeout}s"})
            return result
        except Exception as exc:
            result.update({"skipped": True, "status": "error",
                           "error": str(exc)[:200]})
            return result

    def _cli_update(self, time_only: bool = False) -> None:
        """Shared logic for the 'update' CLI command.

        Workstream B: rewires 'update' to be the full-sync orchestrator.

        Args:
            time_only: If True, only record the interaction timestamp (fast,
                       for internal/automated callers). If False (default),
                       run full sync (timestamp + doc sync + cortex index).
        """
        state = self.update_interaction()
        print(f"[OK] Session updated: {state['session_metrics']['total_duration_minutes']} minutes")

        if not time_only:
            include_git = True  # git remains approval-gated inside sync
            results = self.sync_all_project_documents(include_git_operations=include_git)

            print("\n[SYNC RESULTS]")
            print(f"Documents updated: {len(results['documents_updated'])}")
            for doc in results['documents_updated']:
                print(f"  + {doc}")

            # NOTE: Cortex index step is coordinator-owned (v9.5.0, WI-15).
            # [CORTEX] logging is emitted by cortex_trigger.py via the coordinator.

            if results['errors']:
                print(f"[WARN] {len(results['errors'])} sync error(s):")
                for err in results['errors']:
                    print(f"  - {err}")

    def _backup_before_append(self, filepath: Path) -> Optional[Path]:
        """
        SEC-SU-003 REMEDIATION: Create timestamped backup before append operations.

        Satisfies Protection Rule 4: BACKUP BEFORE EDIT for all project documents.

        Args:
            filepath: Path to the file being appended to

        Returns:
            Path to backup file, or None if backup failed
        """
        if not filepath.exists():
            return None

        timestamp = self.time_provider.utc_now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.protocol_root / ".protocol-state" / "backups" / f"session-sync_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / filepath.name

        try:
            shutil.copy2(filepath, backup_file)
            return backup_file
        except (IOError, OSError) as e:
            print(f"[WARN] Failed to create backup of {filepath.name}: {e}")
            return None

    def _prepare_domain_record_content(self) -> Optional[Tuple[Path, str]]:
        """
        Generate domain.record.md checkpoint content without writing.

        SEC-SU-002 REMEDIATION: Content is generated in memory for
        pre-write secret scanning (eliminates TOCTOU gap).

        Returns:
            Tuple of (filepath, content_string) or None if file not found
        """
        domain_record_file = self.protocol_root / ".dzp-domain" / "domain.record.md"

        if not domain_record_file.exists():
            print(f"[WARN] domain.record.md not found at {domain_record_file}")
            return None

        state = self.load_state()
        now = self.time_provider.utc_now()

        # Calculate session duration
        start_time = state['current_session'].get('start_time')
        start = _parse_utc(start_time)  # BUG-SESSION-001 (v9.3.0): naive->aware guard
        if start is not None:
            duration_minutes = (now - start).total_seconds() / 60
            duration_formatted = f"{int(duration_minutes // 60)}h {int(duration_minutes % 60)}m"
        else:
            duration_formatted = "Unknown"

        # Read recent entries from dev-notes for strategic context
        dev_notes_file = self.protocol_root / ".protocol-state" / "dev-notes.md"
        strategic_context = "No recent implementation notes"
        if dev_notes_file.exists():
            try:
                with open(dev_notes_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Get last 5 non-empty lines
                    recent_lines = [l.strip() for l in lines[-10:] if l.strip() and not l.startswith('#')]
                    if recent_lines:
                        strategic_context = ' | '.join(recent_lines[:3])
            except Exception:
                pass

        checkpoint_entry = f"""
---
## Session Checkpoint - {now.strftime('%Y-%m-%d %H:%M:%S')} UTC

**Session Duration**: {duration_formatted}
**Alert Status**: {state['current_session'].get('alert_count', 0)} alerts | Escalation Level {state['current_session'].get('escalation_level', 0)}
**Strategic Context**: {strategic_context}

"""
        return (domain_record_file, checkpoint_entry)

    def _prepare_dev_notes_content(self) -> Optional[Tuple[Path, str]]:
        """
        Generate dev-notes.md checkpoint content without writing.

        SEC-SU-002 REMEDIATION: Content is generated in memory for
        pre-write secret scanning (eliminates TOCTOU gap).

        Returns:
            Tuple of (filepath, content_string) or None if file not found
        """
        dev_notes_file = self.protocol_root / ".protocol-state" / "dev-notes.md"

        if not dev_notes_file.exists():
            print(f"[WARN] dev-notes.md not found at {dev_notes_file}")
            return None

        state = self.load_state()
        now = self.time_provider.utc_now()

        # Calculate session duration
        start_time = state['current_session'].get('start_time')
        start = _parse_utc(start_time)  # BUG-SESSION-001 (v9.3.0): naive->aware guard
        if start is not None:
            duration_minutes = (now - start).total_seconds() / 60
            duration_formatted = f"{int(duration_minutes // 60)}h {int(duration_minutes % 60)}m"
        else:
            duration_formatted = "Unknown"

        checkpoint_entry = f"""
---
## {now.strftime('%Y-%m-%d %H:%M:%S')} - Session Checkpoint

**Session Duration**: {duration_formatted}
**Continuous Work**: {state['session_metrics'].get('continuous_work_minutes', 0)} minutes
**Breaks Taken**: {state['session_metrics'].get('total_breaks', 0)}

### Active Work
- Session checkpoint sync completed
- All project documents updated

"""
        return (dev_notes_file, checkpoint_entry)

    def _prepare_security_review_content(self) -> Optional[Tuple[Path, str]]:
        """
        Generate security-review.md checkpoint content without writing.

        SEC-SU-002 REMEDIATION: Content is generated in memory for
        pre-write secret scanning (eliminates TOCTOU gap).

        Returns:
            Tuple of (filepath, content_string) or None if file not found
        """
        security_review_file = self.protocol_root / ".protocol-state" / "security-review.md"

        if not security_review_file.exists():
            print(f"[WARN] security-review.md not found at {security_review_file}")
            return None

        now = self.time_provider.utc_now()

        checkpoint_entry = f"""
---
## {now.strftime('%Y-%m-%d %H:%M:%S')} - Security Checkpoint

**Event**: Session checkpoint sync
**Status**: Project documents synced and secret scan completed

"""
        return (security_review_file, checkpoint_entry)

    def _write_checkpoint(self, filepath: Path, content: str):
        """
        Write checkpoint content to file with backup.

        SEC-SU-003: Creates timestamped backup before append.
        SEC-SU-002: Called only AFTER content passes secret scan.

        Args:
            filepath: Target file path
            content: Checkpoint content string to append
        """
        # SEC-SU-003: Create timestamped backup before append
        self._backup_before_append(filepath)

        try:
            # BUG-SESSION-003: newline="\n" forces LF on Windows.
            with open(filepath, 'a', encoding='utf-8', newline="\n") as f:
                f.write(content)
        except (IOError, OSError) as e:
            raise Exception(f"Failed to write to {filepath.name}: {e}")

    # Legacy wrappers for backward compatibility (used by external callers)
    def _sync_domain_record(self):
        """Sync domain.record.md - legacy wrapper."""
        result = self._prepare_domain_record_content()
        if result:
            self._write_checkpoint(result[0], result[1])

    def _sync_dev_notes(self):
        """Sync dev-notes.md - legacy wrapper."""
        result = self._prepare_dev_notes_content()
        if result:
            self._write_checkpoint(result[0], result[1])

    def _sync_security_review(self):
        """Sync security-review.md - legacy wrapper."""
        result = self._prepare_security_review_content()
        if result:
            self._write_checkpoint(result[0], result[1])

    def _scan_for_secrets(self, files: List[str], content_map: Optional[Dict[str, str]] = None) -> List[Dict]:
        """
        Scan project documents for production secrets.

        SEC-SU-001 REMEDIATION: Reports ALL findings with confidence levels
        instead of silently skipping suspected false positives.

        SEC-SU-002 REMEDIATION: Accepts optional content_map for in-memory
        scanning before files are written (eliminates TOCTOU gap).

        SEC-SU-004 REMEDIATION: Secret previews are redacted to prevent
        leaking secret material to stdout/logs.

        SEC-SU-005 REMEDIATION: CONNECTION_STRING regex uses [^@\\s]+ before
        the @ to prevent quadratic backtracking. Lines > 500 chars are
        skipped to mitigate ReDoS on adversarial input.

        Detects:
        - AWS keys (AKIA...)
        - GitHub tokens (ghp_...)
        - Connection strings (mongodb://, postgres://, mysql://)
        - Password assignments
        - Generic API key patterns (high-entropy 32+ char strings)

        Args:
            files: List of filenames to scan
            content_map: Optional dict mapping filename -> content string
                         for in-memory pre-write scanning

        Returns:
            List of detected secrets with file, line, type, and confidence
        """
        import re

        secrets_found = []

        # SEC-SU-005: Narrowed API_KEY pattern and fixed CONNECTION_STRING
        # to prevent ReDoS via [^@\s]+ before the @ separator
        patterns = {
            'AWS_KEY': re.compile(r'AKIA[0-9A-Z]{16}'),
            'GITHUB_TOKEN': re.compile(r'ghp_[A-Za-z0-9]{36}'),
            'CONNECTION_STRING': re.compile(r'(mongodb|postgres|mysql|redis)://[^@\s]+@[^\s]+'),
            'PASSWORD_ASSIGNMENT': re.compile(r'password\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
            'API_KEY': re.compile(r'(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{32,}', re.IGNORECASE),
        }

        # Low-confidence indicator words (SEC-SU-001: still report, just lower confidence)
        low_confidence_indicators = ['example', 'placeholder', 'test', 'sample', 'dummy', 'fake', 'mock']

        for filename in files:
            # Determine content source: in-memory map or file on disk
            lines_to_scan = None

            if content_map and filename in content_map:
                # SEC-SU-002: Scan from in-memory content before write
                lines_to_scan = content_map[filename].splitlines(keepends=True)
            else:
                # Fall back to reading file from disk
                if filename == 'project-state.json':
                    filepath = self.protocol_root / ".protocol-state" / "project-state.json"
                elif filename == 'domain.record.md':
                    filepath = self.protocol_root / ".dzp-domain" / "domain.record.md"
                elif filename == 'dev-notes.md':
                    filepath = self.protocol_root / ".protocol-state" / "dev-notes.md"
                elif filename == 'security-review.md':
                    filepath = self.protocol_root / ".protocol-state" / "security-review.md"
                else:
                    continue

                if not filepath.exists():
                    continue

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines_to_scan = f.readlines()
                except Exception as e:
                    print(f"[WARN] Failed to read {filepath} for scanning: {e}")
                    continue

            # Scan lines
            for line_num, line in enumerate(lines_to_scan, 1):
                # SEC-SU-005: Skip very long lines to prevent ReDoS
                if len(line) > 500:
                    secrets_found.append({
                        'file': filename,
                        'line': line_num,
                        'type': 'LONG_LINE_SKIPPED',
                        'confidence': 'info',
                        'preview': f'[SKIPPED - line length {len(line)} exceeds 500 char limit]'
                    })
                    continue

                for secret_type, pattern in patterns.items():
                    if pattern.search(line):
                        # SEC-SU-001: Determine confidence level instead of
                        # silently skipping. ALL matches are reported.
                        line_lower = line.lower()
                        confidence = 'high'

                        if any(indicator in line_lower for indicator in low_confidence_indicators):
                            confidence = 'low'
                        elif secret_type == 'API_KEY':
                            # Generic API key pattern is inherently medium confidence
                            confidence = 'medium'

                        # SEC-SU-004: Redact preview to prevent secret leakage
                        secrets_found.append({
                            'file': filename,
                            'line': line_num,
                            'type': secret_type,
                            'confidence': confidence,
                            'preview': f'[REDACTED {secret_type}]'
                        })

        return secrets_found

    def _git_commit_and_push_with_approval(self, files: List[str], secrets_found: List[Dict]) -> Dict:
        """
        Commit and push project documents with user approval.

        BUG-SESSION-001 (v9.9.x Track C): This method MUST NEVER set
        DZP_ALLOW_PROTECTED_REWRITE=1 in the environment before running git.
        The append-only guard (FEAT-GUARD-001, SEC-GUARD-002) already normalises
        CRLF, so pure EOF appends always pass without the override.  Routinely
        bypassing the guard disarms the exact mechanism that exists to catch
        accidental overwrites of protected project memory.  Reserve the override
        strictly for authorised rotation/restore (scoped to that one invocation
        and explicitly announced to the user).

        Args:
            files: List of filenames to commit
            secrets_found: List of detected secrets

        Returns:
            Dict with operation results
        """
        result = {
            'attempted': True,
            'success': False,
            'committed': False,
            'pushed': False,
            'user_approved': False,
            'secrets_override': False
        }

        # Map short filenames to full paths
        file_paths = []
        for filename in files:
            if filename == 'project-state.json':
                file_paths.append('.protocol-state/project-state.json')
            elif filename == 'domain.record.md':
                file_paths.append('.dzp-domain/domain.record.md')
            elif filename == 'dev-notes.md':
                file_paths.append('.protocol-state/dev-notes.md')
            elif filename == 'security-review.md':
                file_paths.append('.protocol-state/security-review.md')

        if not file_paths:
            print("[WARN] No files to commit")
            return result

        # Check for secrets
        if secrets_found:
            print(f"\n[WARNING] {len(secrets_found)} potential secrets detected!")
            print("Secrets should not be committed to git.")
            print("\nOptions:")
            print("  1) Abort commit (recommended)")
            print("  2) Review and clean secrets manually, then commit")
            print("  3) Override and commit anyway (NOT RECOMMENDED)")

            # For now, abort if secrets found (can enhance with user input later)
            print("\n[ABORT] Aborting commit due to detected secrets")
            return result

        # User approval for commit
        print(f"\n[GIT] Ready to commit {len(file_paths)} files:")
        for fp in file_paths:
            print(f"  - {fp}")

        print("\nCommit message: 'chore(session): Project documents checkpoint sync'")
        print("\nOptions:")
        print("  1) Commit and push to remote (default)")
        print("  2) Commit locally only")
        print("  3) Skip git operations")

        # For now, return with 'user_approved': False
        # In production, this would prompt for user input
        print("\n[INFO] Git operations require explicit user approval")
        print("[INFO] Run '/session commit' to complete git operations")

        return result

    # -----------------------------------------------------------------------
    # FEAT-TRANSFER-9.11.0-001 (v9.11.0 Increment 2) - /session transfer
    #
    # See internal-docs/Patch Report/DZP-MASTER-PLAN-2026-07-28.md Workstream B
    # and protocol/skills/session.md § /session transfer for the full design.
    #
    # `.protocol-state/script_dependencies.yaml`'s new `session-transfer` event
    # is fail-closed (event-level fail_soft: false) and chains:
    #   0 transfer-begin (required) -> 1 session-update (required) ->
    #   2 session-end (required) -> 3 handoff-write (required) ->
    #   4 end-snapshot (required) -> 5 transfer-finalize (required) ->
    #   6 cortex-medium / 7 cortex-distill / 8 validation-refresh
    #   (optional AND non_blocking -- cannot fail or block this event)
    #
    # M1 (event fail-closed) + M4 (this `handoff` retry subcommand) live
    # outside this module (registry + CLI). M2 (positive identity predicate)
    # and M3 (incomplete-transfer marker) are implemented below.
    #
    # M3 note: ScriptCoordinator (.protocol-state/script_coordinator.py) has NO
    # mechanism to pass a value computed by one step into a later step's
    # command list (each step is a static, YAML-declared subprocess
    # invocation). transfer_begin() therefore PERSISTS the expected session id
    # in the .INCOMPLETE marker file itself; handoff_write() reads it back
    # from there when the caller (the coordinator's yaml step) does not pass
    # --expect-session-id explicitly. Direct/manual/test invocations MAY still
    # pass --expect-session-id explicitly -- both paths are supported.
    #
    # IMPL-001 remediation (Toji audit 2026-07-29): handoff_write() success no
    # longer clears the marker directly -- it only records 'handoff-write'
    # complete via _mark_transfer_step_complete(). transfer_finalize() (step 5
    # above) records 'end-snapshot' complete and clears the marker ONLY once
    # every step in _TRANSFER_REQUIRED_STEPS is recorded. Because this event is
    # fail-closed, a failing end-snapshot breaks the loop BEFORE
    # transfer-finalize ever runs, so the marker correctly survives with only
    # 'handoff-write' recorded -- durable, visible evidence that the mandatory
    # snapshot (not just the handoff) is what remains outstanding.
    # -----------------------------------------------------------------------

    def transfer_begin(self) -> Dict:
        """M3: write the incomplete-transfer marker BEFORE anything else in
        the transfer chain mutates state (this is step 0, required, of the
        session-transfer event -- it runs before session-update/session-end).

        Captures the CURRENTLY active session's id -- the same id
        session-end (step 2) is about to archive -- so handoff-write (step 3)
        can later assert identity against session_history[-1] even though
        the coordinator cannot pass this value between steps directly.

        Never raises. Returns dict:
            {"success": bool, "session_id": str | None, "reason": str}
        A caller (CLI) surfaces failure via a printed message and non-zero
        exit code -- never a traceback (requirement 4: graceful degradation
        when the transfer event runs with no active session).
        """
        state = self.load_state()
        current = state.get('current_session', {})
        session_id = current.get('session_id')
        active = current.get('session_active')

        if not active or not session_id:
            return {
                "success": False,
                "session_id": None,
                "reason": (
                    "No active session to transfer. Start a session first "
                    "('/session start') before running '/session transfer'."
                ),
            }

        # SEC-TRANSFER-9.11.0-005 (P3, CWE-22): defense-in-depth. session_id
        # normally comes from start_session()'s own now-validated id, but a
        # hand-edited state file could still smuggle an unsafe value through
        # this read. Reject before the marker (or any path) is built.
        if not _is_valid_session_id(session_id):
            return {
                "success": False,
                "session_id": session_id,
                "reason": (
                    f"Active session id {session_id!r} has an invalid format "
                    f"(must match {_SESSION_ID_PATTERN.pattern}); refusing to "
                    "begin transfer (SEC-TRANSFER-9.11.0-005)."
                ),
            }

        # SEC-TRANSFER-9.11.0-004 (P3, CWE-459): do not silently overwrite a
        # marker left behind by a DIFFERENT, still-incomplete transfer -- that
        # would discard M3's visible-evidence guarantee for whatever session
        # that marker was protecting. A re-begin for the SAME session id
        # already in progress is idempotent and allowed to proceed.
        existing_marker = self._read_transfer_marker()
        if existing_marker is not None:
            existing_id = existing_marker.get('session_id')
            if existing_id and existing_id != session_id:
                return {
                    "success": False,
                    "session_id": session_id,
                    "reason": (
                        f"Refusing to start a new transfer: an incomplete "
                        f"transfer marker already exists for a DIFFERENT "
                        f"session {existing_id!r}. Resolve it first -- retry "
                        f"with: python .protocol-state/session_monitor.py "
                        f"handoff --session-id {existing_id}"
                    ),
                }

        now = self.time_provider.utc_now()
        marker = {
            "_comment": (
                "Domain Zero Protocol - Incomplete Session Transfer Marker "
                "(FEAT-TRANSFER-9.11.0-001). This artifact is NOT a protected "
                "document -- it is regenerable runtime state, gitignored, "
                "never shipped. Its presence means a '/session transfer' "
                "began but did not finish. Retry with: "
                f"python .protocol-state/session_monitor.py handoff --session-id {session_id}"
            ),
            "session_id": session_id,
            "start_time": now.isoformat(),
        }

        try:
            self.handoff_marker_file.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                'w', encoding='utf-8', delete=False,
                dir=self.handoff_marker_file.parent, suffix='.tmp',
            ) as tmp_file:
                json.dump(marker, tmp_file, indent=2)
                tmp_file.write('\n')
                tmp_path = tmp_file.name
            os.replace(tmp_path, self.handoff_marker_file)
        except (IOError, OSError) as e:
            return {
                "success": False,
                "session_id": session_id,
                "reason": f"Failed to write transfer marker: {e}",
            }

        print(f"[OK] Transfer marker written for session {session_id!r}")
        return {"success": True, "session_id": session_id, "reason": ""}

    def _read_transfer_marker(self) -> Optional[Dict]:
        """Read the .INCOMPLETE marker if present. Returns None if absent,
        corrupted, OR structurally the wrong shape (fail-soft read -- any of
        these is treated the same as a missing marker; the caller's own
        identity check is the real guard).

        SEC-TRANSFER-9.11.0-003 (P2, CWE-20): previously only IOError/OSError/
        JSONDecodeError were caught. A marker file containing VALID JSON that
        is not an object (e.g. a bare list `[1, 2, 3]` or a bare string) was
        not caught here -- it passed through as whatever json.load() returned,
        and every caller (transfer_begin(), handoff_write(),
        _warn_if_transfer_incomplete()) then calls `.get(...)` on it
        unconditionally. `_warn_if_transfer_incomplete()` runs at EVERY
        `/session start`, so this shape crashed session start entirely rather
        than degrading gracefully as designed."""
        if not self.handoff_marker_file.exists():
            return None
        try:
            with open(self.handoff_marker_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (IOError, OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        return data

    def _clear_transfer_marker_if_matches(self, session_id: str) -> None:
        """Clear the marker only if it belongs to the session just written --
        never blindly, so an unrelated retry (M4) cannot mask a different,
        still-incomplete transfer."""
        marker = self._read_transfer_marker()
        if marker is not None and marker.get('session_id') == session_id:
            try:
                self.handoff_marker_file.unlink()
            except OSError:
                pass

    def _mark_transfer_step_complete(self, session_id: str, step_name: str) -> None:
        """IMPL-001 remediation (Toji audit 2026-07-29): record that
        `step_name` (one of _TRANSFER_REQUIRED_STEPS) has completed for the
        transfer identified by `session_id`, WITHOUT clearing the marker --
        the marker's durable presence/absence is now the state machine for
        the whole required prefix, not just the handoff write. No-op if no
        marker exists or it belongs to a different session (mirrors
        _clear_transfer_marker_if_matches's existing match-only-if-belongs-
        to-this-session guard -- an unrelated M4 retry must never mutate a
        different, still-incomplete transfer's marker).

        Fail-soft: a write failure here must never turn an otherwise
        successful step (handoff-write, end-snapshot) into a reported
        failure -- the marker is bookkeeping, not the source of truth for
        whether the step itself succeeded."""
        marker = self._read_transfer_marker()
        if marker is None or marker.get('session_id') != session_id:
            return
        steps_completed = marker.get('steps_completed')
        if not isinstance(steps_completed, list):
            steps_completed = []
        if step_name not in steps_completed:
            steps_completed.append(step_name)
        marker['steps_completed'] = steps_completed
        try:
            with tempfile.NamedTemporaryFile(
                'w', encoding='utf-8', delete=False,
                dir=self.handoff_marker_file.parent, suffix='.tmp',
            ) as tmp_file:
                json.dump(marker, tmp_file, indent=2)
                tmp_file.write('\n')
                tmp_path = tmp_file.name
            os.replace(tmp_path, self.handoff_marker_file)
        except (IOError, OSError):
            pass

    def _verify_end_snapshot_recorded(self, marker: Dict) -> Tuple[bool, str]:
        """CRPR115 #13 (2026-08-03 PR#115 CodeRabbit round-1 triage, folded
        into v9.12.0 A3 per the release plan): positively verify a real
        end-snapshot exists in `.protocol-state/snapshots/snapshot-manifest.json`
        BEFORE `transfer_finalize()` is allowed to mark the 'end-snapshot'
        step complete.

        Prior to this check, `transfer_finalize()` marked 'end-snapshot'
        complete UNCONDITIONALLY -- sound on the normal coordinator path
        (the step only runs after `create-snapshot.py` itself succeeded,
        since session-transfer is fail-closed), but the manual
        `transfer-finalize --session-id` retry path (M4) could forge
        completion even after a snapshot that never ran or failed.

        Looks for a manifest entry with `reason` (or the legacy `trigger`
        key create-snapshot.py also emits) of `"session-transfer"`, whose
        `created_at` is at or after the marker's own `start_time` (not a
        stale leftover from some earlier, unrelated transfer), AND whose
        `session_id` matches this marker's own `session_id` exactly.

        SEC-CLOCKADR-9.12.0-015 (P2, CWE-346, Megumi Tier-3 gate-2 review):
        the `reason`+`created_at` checks alone do not bind an entry to the
        SPECIFIC transfer being finalized -- a different session's
        session-transfer snapshot landing chronologically after this
        transfer's `marker_start` would otherwise satisfy the check too
        (cross-transfer forgery). `create-snapshot.py` now embeds the
        active transfer's session id (read from the SAME `.INCOMPLETE`
        marker this method receives) into the manifest entry when
        `trigger == "session-transfer"`; this method requires that value to
        equal `marker['session_id']` exactly.

        Identity is FAIL-CLOSED by design: an entry with no `session_id` at
        all (a pre-fix manifest, or a `create-snapshot.py` invocation with
        no active transfer marker to read from) is NEVER treated as
        verified, even if `reason`/`created_at` otherwise match. This does
        NOT break the honest M4 manual-retry path -- `create-snapshot.py`'s
        marker read succeeds for any REAL in-progress transfer (the marker
        persists from `transfer_begin()` until `transfer_finalize()` itself
        clears it, so it is still present throughout any retry), meaning a
        legitimate retry always produces a `session_id`-bearing entry.
        Tolerating an unbound entry instead would reopen the exact
        ambiguity CRPR115 #13 was written to close, one layer removed.

        Returns (True, "") if verified, else (False, <reason>). Never
        raises -- a missing/corrupt manifest is treated as "not verified",
        the same fail-closed posture as every other check in this method.
        """
        manifest_path = self.protocol_root / ".protocol-state" / "snapshots" / "snapshot-manifest.json"
        if not manifest_path.exists():
            return False, f"No snapshot manifest found at {manifest_path}."

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except (IOError, OSError, json.JSONDecodeError) as e:
            return False, f"Snapshot manifest at {manifest_path} is unreadable/corrupt: {e}."

        entries = manifest.get('snapshots') if isinstance(manifest, dict) else None
        if not isinstance(entries, list):
            return False, f"Snapshot manifest at {manifest_path} has no 'snapshots' list."

        marker_start = _parse_utc(marker.get('start_time'))
        marker_session_id = marker.get('session_id')

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            reason = entry.get('reason') or entry.get('trigger')
            if reason != "session-transfer":
                continue
            created_at = _parse_utc(entry.get('created_at'))
            if created_at is None:
                continue
            if marker_start is not None and created_at < marker_start:
                # A snapshot exists, but it predates THIS transfer's begin
                # -- a stale leftover from an earlier, unrelated transfer,
                # not evidence this transfer's own end-snapshot ran.
                continue
            # SEC-CLOCKADR-9.12.0-015: identity binding, fail-closed. Both
            # sides must be truthy AND equal -- an absent marker_session_id
            # (should not happen; transfer_finalize() already validated it
            # before calling this method) never matches an absent entry
            # session_id by accident.
            if not marker_session_id or entry.get('session_id') != marker_session_id:
                continue
            return True, ""

        return False, (
            f"No verified end-snapshot found for this transfer (session_id="
            f"{marker_session_id!r}) in {manifest_path} (no matching "
            "'session-transfer' entry created at/after this transfer's "
            "start AND bound to this exact session id -- SEC-CLOCKADR-9.12.0-015)."
        )

    def transfer_finalize(self, session_id: Optional[str] = None) -> Dict:
        """IMPL-001 remediation (Toji audit 2026-07-29): the LAST step of the
        session-transfer required prefix (wired into script_dependencies.yaml
        immediately after end-snapshot, required: true). Records 'end-snapshot'
        complete in the marker and clears the marker if and ONLY IF every step
        in _TRANSFER_REQUIRED_STEPS has now been recorded -- i.e. the mandatory
        snapshot AND the handoff write both durably succeeded.

        Because the session-transfer event is fail-closed (fail_soft: false),
        a failing end-snapshot breaks the coordinator's loop before this step
        ever runs -- so the marker correctly survives, with only
        'handoff-write' recorded, as visible evidence of the still-incomplete
        transfer. Re-running just the snapshot and this command is the
        correct, minimal retry (see _warn_if_transfer_incomplete()).

        Never raises. Returns dict: {"success": bool, "reason": str}.
        """
        # SEC-TRANSFER-9.11.0-010 (P3, CWE-20): validate any caller-supplied
        # session_id BEFORE any marker lookup or comparison, mirroring
        # SEC-TRANSFER-9.11.0-005's rule -- already applied to every other
        # externally-supplied session-id entry point in this module
        # (transfer_begin()'s active-session read, handoff_write()'s
        # session_id/expect_session_id parameters). transfer_finalize() does
        # not currently build a filesystem path from this value, but the
        # established defense-in-depth posture is "validate at every
        # session-id entry point, not only the ones that build paths today."
        if session_id is not None and not _is_valid_session_id(session_id):
            return {
                "success": False,
                "reason": (
                    f"Invalid session_id {session_id!r}: must match "
                    f"{_SESSION_ID_PATTERN.pattern} (SEC-TRANSFER-9.11.0-010)."
                ),
            }
        marker = self._read_transfer_marker()
        if marker is None:
            return {
                "success": False,
                "reason": "No transfer marker found; nothing to finalize.",
            }
        target_id = session_id or marker.get('session_id')
        if not target_id or marker.get('session_id') != target_id:
            return {
                "success": False,
                "reason": (
                    f"Marker session_id {marker.get('session_id')!r} does not "
                    f"match {target_id!r}; refusing to finalize."
                ),
            }
        # CRPR115 #13: positively verify a real end-snapshot exists BEFORE
        # marking the step complete -- never forge completion (fail closed
        # with a distinct, actionable error, not silent success).
        snapshot_verified, snapshot_reason = self._verify_end_snapshot_recorded(marker)
        if not snapshot_verified:
            return {
                "success": False,
                "reason": (
                    f"Refusing to mark 'end-snapshot' complete for {target_id!r}: "
                    f"{snapshot_reason} Run: python .protocol-state/create-snapshot.py "
                    "--auto --tier 2 --trigger session-transfer, then retry "
                    "transfer-finalize (CRPR115 #13)."
                ),
            }
        self._mark_transfer_step_complete(target_id, "end-snapshot")
        refreshed = self._read_transfer_marker()
        steps_completed = set((refreshed or {}).get('steps_completed', []) or [])
        missing = [s for s in _TRANSFER_REQUIRED_STEPS if s not in steps_completed]
        if not missing:
            self._clear_transfer_marker_if_matches(target_id)
            print(f"[OK] Session transfer finalized for {target_id!r}; marker cleared")
            return {"success": True, "reason": ""}
        return {
            "success": False,
            "reason": (
                f"Transfer for {target_id!r} not yet complete; missing required "
                f"step(s): {missing}. Marker retained."
            ),
        }

    def _find_archived_session(self, session_id: str) -> Optional[Dict]:
        """Find an archived session_history record by id (search full
        history, most recent first -- used by the M4 retry path, which may
        target any past session, not only the last one)."""
        state = self.load_state()
        history = state.get('session_history', []) or []
        for record in reversed(history):
            if record.get('session_id') == session_id:
                return record
        return None

    def _history_last(self) -> Optional[Dict]:
        state = self.load_state()
        history = state.get('session_history', []) or []
        return history[-1] if history else None

    def handoff_write(
        self,
        *,
        session_id: Optional[str] = None,
        expect_session_id: Optional[str] = None,
    ) -> Dict:
        """Regenerate the session-handoff brief.

        Three modes, in precedence order:
          1. `session_id` given (M4 retry path): regenerate for that
             SPECIFIC archived session, found anywhere in session_history.
             No identity assertion against history[-1] -- the caller is
             deliberately naming a session to (re)generate a brief for.
          2. `expect_session_id` given (explicit M2 path): assert
             history[-1].session_id == expect_session_id; refuse to write on
             mismatch.
          3. Neither given (the automated session-transfer event's
             handoff-write step): read the expected id from the .INCOMPLETE
             marker transfer_begin() wrote (M3 fallback for the coordinator's
             lack of inter-step value passing), then behave as mode 2.

        Idempotent and keyed to the resolved session id -- re-running with
        the same id/marker regenerates the same two artifacts.

        Never raises. Returns dict:
            {"success": bool, "reason": str, "path": str | None, "session_id": str | None}
        """
        # SEC-TRANSFER-9.11.0-005 (P3, CWE-22): validate any caller-supplied
        # session id BEFORE any lookup, secret scan, or path is built --
        # rejects path-traversal-style values (e.g. "../../evil") up front,
        # at the exact site the archive filename would otherwise be
        # constructed from an unvalidated value.
        for _label, _value in (("session_id", session_id), ("expect_session_id", expect_session_id)):
            if _value is not None and not _is_valid_session_id(_value):
                return {
                    "success": False,
                    "reason": (
                        f"Invalid {_label} {_value!r}: must match "
                        f"{_SESSION_ID_PATTERN.pattern} (SEC-TRANSFER-9.11.0-005)."
                    ),
                    "path": None,
                    "session_id": None,
                }

        marker = self._read_transfer_marker()

        if session_id is not None:
            record = self._find_archived_session(session_id)
            if record is None:
                return {
                    "success": False,
                    "reason": f"No archived session found with id {session_id!r}.",
                    "path": None,
                    "session_id": session_id,
                }
            target_id = session_id
        else:
            if expect_session_id is None:
                if marker is None:
                    return {
                        "success": False,
                        "reason": (
                            "No --expect-session-id given and no transfer marker "
                            f"found at {self.handoff_marker_file}. Cannot verify "
                            "session identity; refusing to write a handoff brief."
                        ),
                        "path": None,
                        "session_id": None,
                    }
                expect_session_id = marker.get('session_id')
                if not expect_session_id:
                    return {
                        "success": False,
                        "reason": "Transfer marker is missing a session_id; refusing to write.",
                        "path": None,
                        "session_id": None,
                    }
                # SEC-TRANSFER-9.11.0-005: defense-in-depth -- the marker is
                # local trusted state normally written by transfer_begin()
                # (which itself now validates), but a hand-edited marker file
                # must not smuggle an unsafe value through to the archive
                # filename construction below either.
                if not _is_valid_session_id(expect_session_id):
                    return {
                        "success": False,
                        "reason": (
                            f"Transfer marker contains an invalid session_id "
                            f"{expect_session_id!r} (must match "
                            f"{_SESSION_ID_PATTERN.pattern}); refusing to write "
                            "(SEC-TRANSFER-9.11.0-005)."
                        ),
                        "path": None,
                        "session_id": None,
                    }

            last = self._history_last()
            actual_id = last.get('session_id') if last else None
            if last is None or actual_id != expect_session_id:
                return {
                    "success": False,
                    "reason": (
                        f"Identity check failed: expected session {expect_session_id!r} "
                        f"but the last archived session is {actual_id!r}. Refusing "
                        "to write a handoff brief for the wrong session "
                        "(FEAT-TRANSFER-9.11.0-001 M2)."
                    ),
                    "path": None,
                    "session_id": expect_session_id,
                }
            record = last
            target_id = expect_session_id

        content = self._build_handoff_content(record)

        # Handoff content summarizes protected docs -- it must pass the same
        # secret scan those docs get before any write (Risk table, B4).
        secrets_found = self._scan_for_secrets(
            ['session-handoff.md'], content_map={'session-handoff.md': content}
        )
        high_confidence = [s for s in secrets_found if s.get('confidence') == 'high']
        if high_confidence:
            return {
                "success": False,
                "reason": (
                    f"Refusing to write handoff brief: {len(high_confidence)} "
                    "high-confidence secret(s) detected in generated content."
                ),
                "path": None,
                "session_id": target_id,
            }

        archive_path = self.handoff_archive_dir / f"session-handoff-{target_id}.md"
        try:
            self.handoff_file.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                'w', encoding='utf-8', delete=False,
                dir=self.handoff_file.parent, suffix='.tmp', newline="\n",
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            os.replace(tmp_path, self.handoff_file)

            self.handoff_archive_dir.mkdir(parents=True, exist_ok=True)
            with open(archive_path, 'w', encoding='utf-8', newline="\n") as f:
                f.write(content)
        except (IOError, OSError) as e:
            return {
                "success": False,
                "reason": f"Failed to write handoff artifacts: {e}",
                "path": None,
                "session_id": target_id,
            }

        # IMPL-001 remediation (Toji audit 2026-07-29): do NOT clear the
        # marker here anymore -- only record that 'handoff-write' completed.
        # The marker is now cleared exclusively by transfer_finalize(), and
        # only once 'end-snapshot' has ALSO been recorded complete. This is
        # a no-op if no marker exists (M4 explicit retries commonly run with
        # no marker present) or it belongs to a different session.
        self._mark_transfer_step_complete(target_id, "handoff-write")

        # CODE-001 remediation (Toji audit 2026-07-29): the staged notes file
        # (if any) has now been consumed into a durably-written brief -- move
        # it out of the well-known staging path so a later transfer can never
        # silently reuse it without deliberate restaging.
        self._archive_and_clear_handoff_notes(target_id)

        print(f"[OK] Session handoff brief written for {target_id!r}: {self.handoff_file}")
        return {"success": True, "reason": "", "path": str(self.handoff_file), "session_id": target_id}

    def _archive_and_clear_handoff_notes(self, session_id: str) -> None:
        """CODE-001 remediation (Toji audit 2026-07-29): _build_handoff_content()
        reads optional freeform staged notes from
        `.protocol-state/session-handoff-notes.md`, but previously nothing
        ever consumed/cleared/archived that staging file afterward -- a LATER
        transfer that did not restage notes would silently reuse the SAME
        stale content (blocking gates, next queue, START HERE pointer, etc.)
        as if it were current.

        Called only from handoff_write()'s success path (i.e. AFTER both
        durable handoff artifacts -- session-handoff.md and the per-session
        archive copy -- have already been written), this MOVES (not copies)
        the staging file into a per-session, timestamped archive so the
        well-known staging path is single-use: it cannot be read again as
        'current' staged notes by any subsequent transfer unless an operator
        deliberately restages it.

        Fail-soft by design (mirrors _clear_transfer_marker_if_matches /
        _mark_transfer_step_complete): any error here must never turn an
        already-successful handoff write into a reported failure. A no-op if
        the staging file does not exist or is empty (nothing was consumed,
        so there is nothing stale to retire)."""
        try:
            if not self.handoff_notes_file.exists():
                return
            if self.handoff_notes_file.stat().st_size == 0:
                return
        except OSError:
            return
        try:
            self.handoff_notes_archive_dir.mkdir(parents=True, exist_ok=True)
            timestamp = self.time_provider.utc_now().strftime('%Y%m%dT%H%M%S%fZ')
            archive_target = (
                self.handoff_notes_archive_dir
                / f"session-handoff-notes-{session_id}-{timestamp}.md"
            )
            # Move, not copy: the staging path itself must become unavailable
            # so a later transfer that forgets to restage cannot read it.
            os.replace(self.handoff_notes_file, archive_target)
        except OSError:
            pass

    def _build_handoff_content(self, record: Dict) -> str:
        """Build the deterministic, machine-generated handoff brief content
        for an archived session_history `record`. Freeform prose (blocking
        gates, next queue, known drift, traps hit, START HERE pointer -- all
        Gojo-authored, per the design) is confined to a single clearly marked
        section at the end, sourced from an optional staging file
        (`.protocol-state/session-handoff-notes.md`) so this method itself
        stays fully deterministic and testable."""
        now = self.time_provider.utc_now()
        session_id = record.get('session_id', 'unknown')
        start_time = record.get('start_time')
        end_time = record.get('end_time')
        duration = record.get('total_duration_minutes', 0)
        breaks = record.get('total_breaks', 0)
        alerts = record.get('alerts_issued', 0)
        continues = record.get('continues_chosen', 0)

        # Cross-session continuity: gap between the PREVIOUS archived
        # session's end and THIS session's start, recorded as data (never as
        # an instruction) -- this is exactly the signal a per-session
        # duration counter structurally cannot see (B1).
        state = self.load_state()
        history = state.get('session_history', []) or []
        idx = None
        for i, rec in enumerate(history):
            if rec.get('session_id') == session_id:
                idx = i
        prev_gap_minutes = None
        prev_gap_gated = False
        if idx is not None and idx > 0:
            prev_end_raw = history[idx - 1].get('end_time')
            time_schema = self._get_time_schema()
            # v9.12.0 A6 (ADR D8.5, SEC-CLOCKADR-9.12.0-021): a naive
            # session_history end/start timestamp in a migrated file is
            # EXACTLY the field class the D8.5 gap this increment closes --
            # never silently trusted into a "CONTINUATION" claim below. If
            # EITHER side is gated, the whole comparison is withheld (a
            # partial comparison would still assert a false confidence).
            if _is_d85_gated(prev_end_raw, time_schema) or _is_d85_gated(start_time, time_schema):
                prev_gap_gated = True
            else:
                prev_end = _parse_utc(prev_end_raw)
                this_start = _parse_utc(start_time)
                if prev_end is not None and this_start is not None:
                    prev_gap_minutes = (this_start - prev_end).total_seconds() / 60

        branch = self._git_query(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        head_sha = self._git_query(["git", "rev-parse", "--short", "HEAD"])
        status_summary = self._git_status_summary()
        protocol_version = self._read_protocol_version()
        cortex_summary = self._cortex_status_summary()
        domain_record_summary = self._domain_record_line_summary()

        agent_notes = ""
        if self.handoff_notes_file.exists():
            try:
                agent_notes = self.handoff_notes_file.read_text(encoding='utf-8').strip()
            except (IOError, OSError):
                agent_notes = ""
        if not agent_notes:
            agent_notes = (
                "_No agent notes were staged for this transfer "
                "(`.protocol-state/session-handoff-notes.md` absent or empty). "
                "Gojo should populate that file with blocking gates and exit "
                "criteria, the next queue in order, known drift accepted-but-"
                "unfixed, traps hit this session, and a `START HERE:` pointer "
                "before invoking `/session transfer` for these to appear here._"
            )

        lines = [
            "<!-- FEAT-TRANSFER-9.11.0-001 - Domain Zero Protocol Session Handoff -->",
            "# Session Handoff Brief",
            "",
            "> **Contract**: this artifact is REGENERABLE derived state, NOT "
            "an append-only protected document. It is overwritten on every "
            "`/session transfer` and is gitignored -- never committed, never "
            "shipped. The permanent record lives in `dev-notes.md` / "
            "`security-review.md` / `domain.record.md`.",
            "",
            f"Generated: {now.isoformat()}",
            "",
            "## Machine-Generated Summary",
            "",
            f"- **Session ID**: {session_id}",
            f"- **Start**: {start_time or 'unknown'}",
            f"- **End**: {end_time or 'unknown'}",
            f"- **Duration**: {self._format_duration(duration)}",
            f"- **Breaks taken**: {breaks}",
            f"- **Alerts issued**: {alerts}",
            f"- **Continues chosen (escalations)**: {continues}",
            "",
            "### Cross-Session Continuity",
            "",
        ]
        if prev_gap_gated:
            # v9.12.0 A6 (ADR D8.5): DISPLAYED (per D8.5's own "may still be
            # displayed... labeled as unconfirmed provenance"), but NEVER
            # feeding a CONTINUATION/fresh-start classification the way the
            # trusted branch below does.
            lines.append(
                "- Gap since previous archived session's end: **unavailable** "
                "-- a boundary timestamp has unconfirmed provenance under ADR "
                "D8.5 (a still-ambiguous pre-migration record pending USER "
                "adjudication, or a naive write from an unexpected code path). "
                "Excluded from continuity classification; never silently "
                "assumed."
            )
        elif prev_gap_minutes is not None:
            lines.append(f"- Gap since previous archived session's end: {prev_gap_minutes:.1f} minutes")
            if prev_gap_minutes < 30:
                lines.append(
                    "- **Rolling continuous-work window**: under 30 minutes since "
                    "the previous session ended -- this is a CONTINUATION, not a "
                    "fresh start, even though the per-session counter resets to zero."
                )
        else:
            lines.append("- No prior archived session found for continuity comparison.")
        lines.extend([
            "",
            "### Repository State",
            "",
            f"- **Branch**: {branch or 'unavailable'}",
            f"- **HEAD**: {head_sha or 'unavailable'}",
            f"- **Working tree**: {status_summary}",
            "",
            "### Protocol State",
            "",
            f"- **Protocol version**: {protocol_version or 'unknown'}",
            f"- **Cortex**: {cortex_summary}",
            f"- **domain.record.md**: {domain_record_summary}",
            "",
            "## Agent Notes (freeform -- Gojo-authored)",
            "",
            agent_notes,
            "",
        ])
        return "\n".join(lines) + "\n"

    def _git_query(self, args: List[str]) -> Optional[str]:
        """Fail-soft git query -- never raises, returns None on any error."""
        try:
            import subprocess as _sp
            proc = _sp.run(
                args, cwd=self.protocol_root, capture_output=True, text=True, timeout=5,
            )
            if proc.returncode != 0:
                return None
            return proc.stdout.strip() or None
        except Exception:
            return None

    def _git_status_summary(self) -> str:
        output = self._git_query(["git", "status", "--porcelain"])
        if output is None:
            return "unavailable"
        changed = [l for l in output.splitlines() if l.strip()]
        return "clean (0 changed paths)" if not changed else f"{len(changed)} changed path(s)"

    def _read_protocol_version(self) -> Optional[str]:
        """Best-effort protocol version lookup from protocol.config.yaml's
        versioning.protocol_version key. Fail-soft -- returns None on any
        error (missing file, missing key, parse failure)."""
        if not self.config_file.exists():
            return None
        try:
            import yaml
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            version = (config.get('versioning') or {}).get('protocol_version')
            return str(version) if version else None
        except Exception:
            return None

    def _cortex_status_summary(self) -> str:
        """Best-effort Cortex status summary via `brain.py status --json`.
        Fail-soft (mirrors `_sync_cortex_index`'s status-gate pattern) --
        Cortex being unavailable must never block a handoff write."""
        brain_py = self.protocol_root / ".protocol-state" / "brain" / "brain.py"
        if not brain_py.exists():
            return "unavailable (brain.py not found)"
        try:
            import subprocess as _sp
            proc = _sp.run(
                [sys.executable, str(brain_py), "--repo", str(self.protocol_root), "status", "--json"],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode != 0:
                return "unavailable (status check failed)"
            data = json.loads(proc.stdout)
            chunks = data.get("chunks", data.get("chunk_count", "unknown"))
            last_index = data.get("last_index", data.get("last_indexed", "unknown"))
            return f"ok, chunks={chunks}, last_index={last_index}"
        except Exception:
            return "unavailable"

    def _domain_record_line_summary(self) -> str:
        """Best-effort domain.record.md line count vs its configured rotation
        threshold (protocol.config.yaml domain_record.rotation.threshold_lines,
        default 5000 -- see .dzp-domain/.rotation-metadata.json)."""
        domain_record_file = self.protocol_root / ".dzp-domain" / "domain.record.md"
        if not domain_record_file.exists():
            return "unavailable (domain.record.md not found)"
        try:
            with open(domain_record_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
        except (IOError, OSError):
            return "unavailable (read failed)"

        threshold = 5000
        try:
            import yaml
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                threshold = (
                    (config.get('domain_record') or {}).get('rotation', {}).get('threshold_lines', threshold)
                )
        except Exception:
            pass

        return f"{line_count} lines (rotation threshold: {threshold})"

    def _warn_if_transfer_incomplete(self) -> None:
        """`/session start` integration, requirement: warn LOUDLY, before
        anything else, if a previous `/session transfer` did not finish.
        Read-only advisory; never raises.

        IMPL-001 remediation (Toji audit 2026-07-29): the retry command now
        depends on WHICH required step(s) the marker shows outstanding.
        Previously this always pointed at `handoff --session-id`, even when
        the handoff itself had already succeeded and only the mandatory
        end-snapshot (+ transfer-finalize) remained -- a retry that could
        never actually complete the missing snapshot.

        SEC-TRANSFER-9.11.0-008 (P3, CWE-696) remediation: a THIRD state is
        possible and was previously mishandled -- a crash between
        `_mark_transfer_step_complete(target_id, "end-snapshot")` and the
        marker clear a few lines later in `transfer_finalize()` leaves a
        marker where EVERY entry of `_TRANSFER_REQUIRED_STEPS` is already
        recorded, yet the marker itself was never cleared. That state used
        to fall into the generic `else` branch below and print
        `handoff --session-id`, which is idempotent and can never clear a
        marker whose required steps are already complete -- a permanent
        false-positive warning at every future `/session start`. This is now
        its own branch, checked first, pointing directly at the one command
        that can actually finish the job: `transfer-finalize` (no
        `--session-id` needed -- it reads the marker's own session id)."""
        marker = self._read_transfer_marker()
        if marker is None:
            return
        session_id = marker.get('session_id', 'unknown')
        steps_completed = marker.get('steps_completed')
        if not isinstance(steps_completed, list):
            steps_completed = []
        print("")
        print("[!] INCOMPLETE SESSION TRANSFER DETECTED")
        print(f"    A previous '/session transfer' for session {session_id!r} did not finish.")
        if all(step in steps_completed for step in _TRANSFER_REQUIRED_STEPS):
            print("    Every required step (handoff-write, end-snapshot) is already recorded, but")
            print("    the marker was never cleared -- the process likely stopped right before")
            print("    that final step. Finish it with:")
            print("      python .protocol-state/session_monitor.py transfer-finalize")
        elif "handoff-write" in steps_completed and "end-snapshot" not in steps_completed:
            print("    The handoff brief was already written successfully -- only the mandatory")
            print("    end-of-transfer snapshot did not complete. Retry with:")
            print("      python .protocol-state/create-snapshot.py --auto --tier 2 --trigger session-transfer")
            print("      python .protocol-state/session_monitor.py transfer-finalize")
        else:
            print(f"    Retry it with: python .protocol-state/session_monitor.py handoff --session-id {session_id}")
        print("")

    def _point_to_fresh_handoff_brief(self) -> None:
        """`/session start` integration: if session-handoff.md exists and
        postdates the last recorded session start, point to it before reading
        the large protocol documents (cheapest high-value context in the
        tree). Read-only advisory; never raises."""
        if not self.handoff_file.exists():
            return
        try:
            mtime = datetime.fromtimestamp(self.handoff_file.stat().st_mtime, tz=timezone.utc)
        except OSError:
            return

        state = self.load_state()
        start_raw = state.get('current_session', {}).get('start_time')
        # v9.12.0 A6 (ADR D8.5, SEC-CLOCKADR-9.12.0-021): one of Megumi's 3
        # confirmed at-risk call sites. Gated explicitly (not just relying on
        # `_parse_utc()`'s own tolerance) for auditability, even though the
        # gated and ungated outcomes are IDENTICAL at this specific site --
        # both a gated result and a genuinely-missing `start_time` fall to
        # `last_start is None`, which already takes this method's single
        # conservative branch (show the tip). Documented, not assumed: see
        # this increment's dev-notes.md call-site audit.
        if _is_d85_gated(start_raw, self._get_time_schema()):
            last_start = None
        else:
            last_start = _parse_utc(start_raw)
        if last_start is None or mtime > last_start:
            print(f"[TIP] A session handoff brief is available: {self.handoff_file}")
            print("      Read it first for warm context from the prior session.")


def main():
    """Command-line interface for session monitoring."""
    import sys
    import io

    # Fix Windows console encoding for emojis
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    protocol_root = Path.cwd()

    try:
        monitor = SessionMonitor(protocol_root)
    except Exception as e:
        print(f"[ERROR] Failed to initialize SessionMonitor: {e}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python session_monitor.py <command>")
        print("")
        print("Session Management:")
        print("  start, new-session         Start a new work session")
        print("  update                     Full sync: timestamp + doc sync + Cortex index")
        print("  update --time-only         Timestamp only (fast, for internal callers)")
        print("  sync                       Comprehensive project documents sync (domain.record, dev-notes, security-review, project-state)")
        print("  sync --no-git              Sync documents without git operations")
        print("  end                        End the current session")
        print("  reset                      Reset session state (clear all data)")
        print("")
        print("Session Transfer (v9.11.0, FEAT-TRANSFER-9.11.0-001):")
        print("  transfer-begin             Step 0 of 'python dzp.py event session-transfer' - writes .INCOMPLETE marker")
        print("  handoff                    Regenerate session-handoff.md (auto mode: reads expected id from marker)")
        print("  handoff --expect-session-id <id>  Explicit identity check before writing")
        print("  handoff --session-id <id>  Retry: regenerate brief for a specific archived session (no identity check)")
        print("  transfer-finalize          Last required step: marks end-snapshot complete + clears .INCOMPLETE marker")
        print("                             only once handoff-write AND end-snapshot are both recorded (IMPL-001)")
        print("")
        print("Monitoring & Alerts:")
        print("  check                      Check if alert is needed")
        print("  check --debounce=N         Check with custom debounce threshold (15-60 min)")
        print("  check-and-record           Check for alert AND auto-record if detected")
        print("  check-and-record --json    Emit the ADR D5 structured envelope instead of prose (AI-001)")
        print("  record-choice <choice>     Record user's alert response (save_and_break|continue)")
        print("  status, summary            Show current session summary")
        print("")
        print("Break Management:")
        print("  break [minutes]            Record a break (default: 15 minutes)")
        print("  continue, resume           Resume work after break")
        print("")
        print("Agent Invocation Tracking (v8.13.0):")
        print("  record-invocation <agent>  Record agent invocation for bypass detection")
        print("                             Use --routed flag if invocation was routed via Gojo")
        print("")
        print("Utilities:")
        print("  test                       Test alert rendering")
        print("  help                       Show this help message")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start" or command == "new-session":
        # v9.12.0 A4 (ADR D5, Toji gate 4): `--json` emits the structured
        # time envelope INSTEAD OF the default prose (never alongside it --
        # a provider consuming the envelope must get exactly one parseable
        # JSON document on stdout, per D5.3's relay-verbatim contract).
        # Omitting `--json` leaves the existing prose output byte-for-byte
        # unchanged (backward compatibility for existing consumers -- see
        # tests/test_session_monitor_json_flag_characterization.py).
        if "--json" in sys.argv:
            with contextlib.redirect_stdout(io.StringIO()):
                state = monitor.start_session()
            # The most recently ARCHIVED session (history[-1], if any) is
            # the one whose end_time compares against this new start -- NOT
            # the current session itself, which is not (yet) in history.
            # build_envelope() requires both boundary instants or neither
            # (a partial pair raises -- see time_envelope.py), so only pass
            # current_start_utc when a genuine previous boundary exists to
            # pair it with.
            history = state.get('session_history') or []
            prev_end_raw = history[-1]['end_time'] if history else None
            # v9.12.0 A6 (ADR D8.5, SEC-CLOCKADR-9.12.0-021): THE confirmed
            # exploit path -- Megumi's review named this exact site as "the
            # same class of field that caused the original July 30 incident."
            # A naive `end_time` in a migrated file must NEVER silently feed
            # `gap`/`continuity.class`, which D5.3 obligates Claude/Codex to
            # relay verbatim. When gated, BOTH instants are withheld (never a
            # partial pair -- `build_envelope()` requires both-or-neither
            # anyway) and `ambiguous_boundary_timestamp=True` is forwarded so
            # the envelope surfaces the anomaly explicitly instead of
            # degrading to the neutral "no previous session boundary"
            # default, which would understate what actually happened.
            ambiguous_boundary = _is_d85_gated(prev_end_raw, monitor._get_time_schema())
            if ambiguous_boundary:
                previous_end_utc = None
                current_start_utc = None
            else:
                previous_end_utc = _parse_utc(prev_end_raw) if history else None
                current_start_utc = (
                    _parse_utc(state.get('current_session', {}).get('start_time'))
                    if previous_end_utc is not None
                    else None
                )
            envelope = monitor._build_envelope(
                SessionBoundary.START,
                session_id=state.get('current_session', {}).get('session_id'),
                previous_end_utc=previous_end_utc,
                current_start_utc=current_start_utc,
                ambiguous_boundary_timestamp=ambiguous_boundary,
            )
            print(json.dumps(envelope))
        else:
            monitor.start_session()
    elif command == "update":
        # Workstream B: 'update' is now the full-sync orchestrator.
        # --time-only flag preserves the OLD timestamp-only behaviour for fast/internal callers.
        # check-and-record / continue / resume are unaffected (they call update_interaction directly).
        time_only = "--time-only" in sys.argv
        monitor._cli_update(time_only=time_only)
    elif command == "sync":
        # PATCH-SESSION-UPDATE: Comprehensive project documents sync
        include_git = "--no-git" not in sys.argv
        results = monitor.sync_all_project_documents(include_git_operations=include_git)

        print("\n[SYNC RESULTS]")
        print(f"Documents updated: {len(results['documents_updated'])}")
        for doc in results['documents_updated']:
            print(f"  ✅ {doc}")

        if results['secrets_found']:
            print(f"\n⚠️  Secrets found: {len(results['secrets_found'])}")
            for secret in results['secrets_found']:
                print(f"  - {secret['file']}:{secret['line']} ({secret['type']})")

        if results['errors']:
            print(f"\n❌ Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")

        if results['success']:
            print("\n✅ Sync completed successfully")
        else:
            print("\n⚠️  Sync completed with errors")
            sys.exit(1)
    elif command == "check":
        # v8.13.0 - PATCH-SESSION-004: Support --debounce CLI argument
        debounce_override = None
        if len(sys.argv) > 2 and sys.argv[2].startswith('--debounce'):
            try:
                # Parse --debounce=15 or --debounce 15
                if '=' in sys.argv[2]:
                    debounce_override = int(sys.argv[2].split('=')[1])
                elif len(sys.argv) > 3:
                    debounce_override = int(sys.argv[3])
            except (ValueError, IndexError):
                print("[!] Invalid --debounce format. Use: --debounce=15 or --debounce 15")

        needed, level, context = monitor.check_alert_needed(debounce_override=debounce_override)
        if "--json" in sys.argv:
            # v9.12.0 A4: JSON mode never runs the prose render/format
            # paths at all (no redirect_stdout needed here -- unlike
            # 'start', check_alert_needed() itself is silent).
            envelope = monitor._build_envelope(
                SessionBoundary.CHECK,
                session_id=monitor.load_state().get('current_session', {}).get('session_id'),
                alert_needed=needed,
                alert_reasons=context.get('alert_reasons'),
                is_late_night=context.get('is_late_night'),
            )
            print(json.dumps(envelope))
        elif needed:
            print(f"[!] Alert needed: {level}")
            print(monitor.render_alert(context))
        else:
            print(monitor.format_no_alert_message())
    elif command == "summary" or command == "status":
        # 'status' is an alias for 'summary' (industry standard expectation)
        if "--json" in sys.argv:
            session_id = monitor.load_state().get('current_session', {}).get('session_id')
            envelope = monitor._build_envelope(SessionBoundary.STATUS, session_id=session_id)
            print(json.dumps(envelope))
        else:
            print(monitor.get_session_summary())
    elif command == "end":
        monitor.end_session()
    elif command == "transfer-begin":
        # FEAT-TRANSFER-9.11.0-001 (v9.11.0 Increment 2): step 0 of the
        # session-transfer coordinator event. Writes the .INCOMPLETE marker
        # BEFORE session-update/session-end run.
        #
        # CodeRabbit round-1 (PR #116): `transfer_begin()` prints its own
        # "[OK] Transfer marker written..." prose BEFORE returning --
        # `start`/`resume` already guard their own lifecycle call the same
        # way for exactly this reason (see those branches above). Without
        # it, `--json` mode's stdout was that prose line followed by the
        # envelope -- `json.loads(stdout)` fails, breaking the "exactly one
        # parseable JSON document on stdout" contract this module states
        # (see the `start`/`--json` comment above) and
        # `protocol/skills/session.md` restates. The prose itself is
        # unaffected in non-`--json` mode (see
        # test_transfer_begin_without_json_flag_still_prints_prose).
        _json_mode = "--json" in sys.argv
        if _json_mode:
            with contextlib.redirect_stdout(io.StringIO()):
                result = monitor.transfer_begin()
        else:
            result = monitor.transfer_begin()
        if not result["success"]:
            print(f"[ERROR] {result['reason']}", file=sys.stderr)
            sys.exit(1)
        if _json_mode:
            envelope = monitor._build_envelope(
                SessionBoundary.TRANSFER_BEGIN, session_id=result.get("session_id")
            )
            print(json.dumps(envelope))
    elif command == "handoff":
        # FEAT-TRANSFER-9.11.0-001: regenerate the session-handoff brief.
        #   handoff                              -- auto mode: read expected
        #                                            id from the .INCOMPLETE
        #                                            marker (coordinator step 3)
        #   handoff --expect-session-id <id>     -- explicit identity check (M2)
        #   handoff --session-id <id>            -- retry a specific archived
        #                                            session, no identity check (M4)
        expect_session_id = None
        explicit_session_id = None
        handoff_args = sys.argv[2:]
        i = 0
        while i < len(handoff_args):
            arg = handoff_args[i]
            if arg == "--expect-session-id" and i + 1 < len(handoff_args):
                expect_session_id = handoff_args[i + 1]
                i += 2
            elif arg.startswith("--expect-session-id="):
                expect_session_id = arg.split("=", 1)[1]
                i += 1
            elif arg == "--session-id" and i + 1 < len(handoff_args):
                explicit_session_id = handoff_args[i + 1]
                i += 2
            elif arg.startswith("--session-id="):
                explicit_session_id = arg.split("=", 1)[1]
                i += 1
            else:
                i += 1

        # CodeRabbit round-1 (PR #116): same prose-before-envelope gap as
        # transfer-begin above -- `handoff_write()` prints its own
        # "[OK] Session handoff brief written..." line before returning.
        _json_mode = "--json" in sys.argv
        if _json_mode:
            with contextlib.redirect_stdout(io.StringIO()):
                result = monitor.handoff_write(session_id=explicit_session_id, expect_session_id=expect_session_id)
        else:
            result = monitor.handoff_write(session_id=explicit_session_id, expect_session_id=expect_session_id)
        if not result["success"]:
            print(f"[ERROR] {result['reason']}", file=sys.stderr)
            sys.exit(1)
        if _json_mode:
            envelope = monitor._build_envelope(SessionBoundary.HANDOFF, session_id=result.get("session_id"))
            print(json.dumps(envelope))
    elif command == "transfer-finalize":
        # IMPL-001 remediation (Toji audit 2026-07-29): final required step
        # of the session-transfer event, wired in immediately after
        # end-snapshot. Records 'end-snapshot' complete and clears the
        # .INCOMPLETE marker only once 'handoff-write' is ALSO recorded.
        #   transfer-finalize                 -- auto mode: read session_id
        #                                         from the .INCOMPLETE marker
        #   transfer-finalize --session-id <id>  -- explicit target (manual retry)
        explicit_session_id = None
        finalize_args = sys.argv[2:]
        i = 0
        while i < len(finalize_args):
            arg = finalize_args[i]
            if arg == "--session-id" and i + 1 < len(finalize_args):
                explicit_session_id = finalize_args[i + 1]
                i += 2
            elif arg.startswith("--session-id="):
                explicit_session_id = arg.split("=", 1)[1]
                i += 1
            else:
                i += 1

        # CodeRabbit round-1 (PR #116): same prose-before-envelope gap as
        # transfer-begin/handoff above -- `transfer_finalize()` prints its
        # own "[OK] Session transfer finalized..." line before returning.
        _json_mode = "--json" in sys.argv
        if _json_mode:
            with contextlib.redirect_stdout(io.StringIO()):
                result = monitor.transfer_finalize(session_id=explicit_session_id)
        else:
            result = monitor.transfer_finalize(session_id=explicit_session_id)
        if not result["success"]:
            print(f"[ERROR] {result['reason']}", file=sys.stderr)
            sys.exit(1)
        if _json_mode:
            envelope = monitor._build_envelope(
                SessionBoundary.TRANSFER_FINALIZE, session_id=result.get("session_id")
            )
            print(json.dumps(envelope))
    elif command == "break":
        # Record break with optional duration argument
        # PATCH-SEC-005: Validate duration to prevent DoS via infinite loops
        duration = 15  # default
        if len(sys.argv) > 2:
            try:
                duration = int(sys.argv[2])
                if duration < MIN_BREAK_DURATION or duration > MAX_BREAK_DURATION:
                    print(
                        f"[ERROR] Break duration must be between {MIN_BREAK_DURATION}-{MAX_BREAK_DURATION} minutes",
                        file=sys.stderr
                    )
                    print(f"        You requested: {duration} minutes", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print(f"[ERROR] Invalid duration: {sys.argv[2]} (must be a number)", file=sys.stderr)
                sys.exit(1)
        monitor.record_break(duration)
    elif command == "continue" or command == "resume":
        # Resume work after break (just update interaction timestamp)
        # PATCH-SEC-007 (SEC-004): Add error handling
        try:
            if "--json" in sys.argv:
                with contextlib.redirect_stdout(io.StringIO()):
                    state = monitor.update_interaction()
                envelope = monitor._build_envelope(
                    SessionBoundary.RESUME,
                    session_id=state.get('current_session', {}).get('session_id'),
                )
                print(json.dumps(envelope))
            else:
                state = monitor.update_interaction()
                # BUG-SESSION-005 (BUG C): label local+UTC instead of a bare unlabeled UTC time.
                timestamp_utc = monitor.time_provider.utc_now()
                timestamp = f"{_local_now(timestamp_utc, monitor._user_zone_info).strftime('%H:%M %Z')} ({timestamp_utc.strftime('%H:%M')} UTC)"
                print(f"[OK] Work resumed at {timestamp}")
                print(f"    Total session time: {state['session_metrics']['total_duration_minutes']} minutes")
        except Exception as e:
            print(f"[ERROR] Failed to resume session: {e}", file=sys.stderr)
            print(f"        Try starting a new session with 'start' or 'new-session'", file=sys.stderr)
            sys.exit(1)
    elif command == "reset":
        # Reset session state completely
        # PATCH-SEC-007: Atomic reset with backup verification
        if monitor.state_file.exists():
            try:
                # Create timestamped backup
                backup_timestamp = monitor.time_provider.utc_now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f"session-state.backup.{backup_timestamp}.json"
                backup_path = monitor.state_file.parent / backup_filename

                # Copy to backup location
                shutil.copy2(monitor.state_file, backup_path)

                # CRITICAL: Verify backup integrity before deletion
                if not backup_path.exists() or backup_path.stat().st_size == 0:
                    raise IOError("Backup verification failed: file missing or empty")

                # Verify backup is valid JSON
                with open(backup_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # Will raise exception if corrupted

                print(f"[OK] Backup created and verified: {backup_filename}")

                # PATCH-SEC-007 (SEC-003): Clean up old backups (keep last 10)
                backup_pattern = monitor.state_file.parent.glob('session-state.backup.*.json')
                backups = sorted(backup_pattern, key=lambda p: p.stat().st_mtime)
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()
                    print(f"[INFO] Cleaned up {len(backups) - 10} old backup(s)")

                # Only delete after verified backup exists
                monitor.state_file.unlink()
                print(f"[DELETE] Removed: {monitor.state_file.name}")

                # Recreate with default state
                monitor._ensure_state_file()
                print("[OK] Session state reset successfully")
                print(f"     New state file created at: {monitor.state_file}")

            except (IOError, OSError, PermissionError) as e:
                print(f"[ERROR] Backup failed: {e}", file=sys.stderr)
                print(f"        Session state NOT reset (original preserved)", file=sys.stderr)
                sys.exit(1)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Backup verification failed: Invalid JSON ({e})", file=sys.stderr)
                print(f"        Session state NOT reset (original preserved)", file=sys.stderr)
                # Clean up corrupted backup
                if backup_path.exists():
                    backup_path.unlink()
                sys.exit(1)
        else:
            print("[INFO] No session state file found (already reset)")
            print("       Use 'start' or 'new-session' to begin a new work session")
    elif command == "record-choice":
        # PATCH-SESSION-003: Record user's alert response choice
        # Enables Gojo to record user decisions via CLI
        if len(sys.argv) < 3:
            print("Usage: python session_monitor.py record-choice <save_and_break|continue>", file=sys.stderr)
            print("", file=sys.stderr)
            print("This command records the user's response to a work session alert.", file=sys.stderr)
            print("It increments alert counters and updates escalation state.", file=sys.stderr)
            sys.exit(1)

        choice = sys.argv[2]
        try:
            state = monitor.record_user_choice(choice)
            print(f"[OK] User choice '{choice}' recorded successfully")
            print(f"    Alert count: {state['current_session']['alert_count']}")
            print(f"    Escalation level: {state['current_session']['escalation_level']}")
            if state['current_session']['high_risk_operations_blocked']:
                print("[!] High-risk operations now blocked (6+ hours with 'continue')")
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
    elif command == "check-and-record":
        # PATCH-SESSION-003: Check for alert AND auto-record if detected
        # Provides defense-in-depth (alerts recorded even if user choice workflow fails)
        #
        # Toji audit 2026-08-06 (AI-001, HIGH direct fix): this is the
        # MANDATORY auto-invoked safety path (protocol/skills/session-check.md
        # Step 1, run on EVERY Gojo Mission Control activation) and, unlike
        # 'check', previously had NO --json branch at all -- a provider
        # following the documented default command could only ever receive
        # prose, never the structured D5 envelope the binding provider relay
        # rule depends on. `--json` emits the envelope INSTEAD OF the prose
        # below (never alongside it, same one-parseable-document contract as
        # every other `--json` boundary); side effects (counter increments)
        # are unchanged either way.
        needed, level, context = monitor.check_alert_needed()
        if needed:
            # Auto-increment alert counters when alert detected
            state = monitor.load_state()
            state['current_session']['alert_count'] += 1
            state['current_session']['last_alert_time'] = monitor.time_provider.utc_now().isoformat()
            state['session_metrics']['alerts_issued'] += 1
            monitor.save_state(state)

            if "--json" in sys.argv:
                envelope = monitor._build_envelope(
                    SessionBoundary.CHECK,
                    session_id=state.get('current_session', {}).get('session_id'),
                    alert_needed=needed,
                    alert_reasons=context.get('alert_reasons'),
                    is_late_night=context.get('is_late_night'),
                )
                print(json.dumps(envelope))
            else:
                print(f"[!] Alert detected and recorded: {level}")
                print(f"    Alert count: {state['current_session']['alert_count']}")
                print("")
                print(monitor.render_alert(context))
        else:
            if "--json" in sys.argv:
                envelope = monitor._build_envelope(
                    SessionBoundary.CHECK,
                    session_id=monitor.load_state().get('current_session', {}).get('session_id'),
                    alert_needed=needed,
                    alert_reasons=context.get('alert_reasons'),
                    is_late_night=context.get('is_late_night'),
                )
                print(json.dumps(envelope))
            else:
                print(monitor.format_no_alert_message())
    elif command == "record-invocation":
        # PATCH-SESSION-004 Component 5: Record agent invocation for bypass detection
        if len(sys.argv) < 3:
            print("Usage: python session_monitor.py record-invocation <agent_name> [--routed]", file=sys.stderr)
            print("", file=sys.stderr)
            print("This command records agent invocations for bypass detection.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Arguments:", file=sys.stderr)
            print("  agent_name    Name of agent (gojo, yuuji, megumi, nobara, todo, maki, panda, inumaki, sukuna)", file=sys.stderr)
            print("  --routed      Flag to indicate invocation was routed via Gojo (default: direct)", file=sys.stderr)
            print("", file=sys.stderr)
            print("Examples:", file=sys.stderr)
            print("  python session_monitor.py record-invocation yuuji", file=sys.stderr)
            print("  python session_monitor.py record-invocation yuuji --routed", file=sys.stderr)
            sys.exit(1)

        agent_name = sys.argv[2]
        is_direct = "--routed" not in sys.argv

        try:
            tracker = monitor.record_agent_invocation(agent_name, is_direct=is_direct)
            invocation_type = "direct" if is_direct else "routed"
            print(f"[OK] Recorded {invocation_type} invocation of {agent_name}")

            # Show current stats
            agent_data = tracker.get('invocations', {}).get(agent_name.lower(), {})
            print(f"    Total invocations: {agent_data.get('total_count', 0)}")
            if agent_name.lower() != 'gojo':
                print(f"    Direct: {agent_data.get('direct_invocations', 0)}, Routed: {agent_data.get('routed_invocations', 0)}")

            # Check for bypass alerts
            bypass_alerts = tracker.get('bypass_detection', {}).get('bypass_alerts', [])
            if bypass_alerts:
                recent_alerts = [a for a in bypass_alerts if a.get('agent') == agent_name.lower()][-3:]
                if recent_alerts:
                    print(f"    [!] Recent bypass alerts: {len(recent_alerts)}")
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
    elif command == "test":
        # Test alert rendering
        test_context = {
            "duration_minutes": 250,
            "duration_formatted": "4 hours 10 minutes",
            "alert_level": "standard",
            "is_late_night": False,
            "continuous_minutes": 250,
            "alert_count": 1
        }
        print(monitor.render_alert(test_context))
    elif command == "help" or command == "--help" or command == "-h":
        # Show help
        print("Domain Zero Protocol - Work Session Monitor v8.13.0")
        print("")
        print("Usage: python session_monitor.py <command>")
        print("")
        print("Session Management:")
        print("  start, new-session         Start a new work session")
        print("  update                     Record an interaction (updates duration)")
        print("  end                        End the current session")
        print("  reset                      Reset session state (clear all data)")
        print("")
        print("Session Transfer (v9.11.0, FEAT-TRANSFER-9.11.0-001):")
        print("  transfer-begin             Step 0 of 'python dzp.py event session-transfer' - writes .INCOMPLETE marker")
        print("  handoff                    Regenerate session-handoff.md (auto mode: reads expected id from marker)")
        print("  handoff --expect-session-id <id>  Explicit identity check before writing")
        print("  handoff --session-id <id>  Retry: regenerate brief for a specific archived session (no identity check)")
        print("  transfer-finalize          Last required step: marks end-snapshot complete + clears .INCOMPLETE marker")
        print("                             only once handoff-write AND end-snapshot are both recorded (IMPL-001)")
        print("")
        print("Monitoring & Alerts:")
        print("  check                      Check if alert is needed")
        print("  check --debounce=N         Check with custom debounce threshold (15-60 min)")
        print("  check-and-record           Check for alert AND auto-record if detected")
        print("  check-and-record --json    Emit the ADR D5 structured envelope instead of prose (AI-001)")
        print("  record-choice <choice>     Record user's alert response (save_and_break|continue)")
        print("  status, summary            Show current session summary")
        print("")
        print("Break Management:")
        print("  break [minutes]            Record a break (default: 15 minutes)")
        print("  continue, resume           Resume work after break")
        print("")
        print("Agent Invocation Tracking (v8.13.0):")
        print("  record-invocation <agent>  Record agent invocation for bypass detection")
        print("                             Use --routed flag if invocation was routed via Gojo")
        print("")
        print("Utilities:")
        print("  test                       Test alert rendering")
        print("  help                       Show this help message")
        print("")
        print("Examples:")
        print("  python session_monitor.py start              # Start new session")
        print("  python session_monitor.py status             # Check current status")
        print("  python session_monitor.py check              # Check for alerts")
        print("  python session_monitor.py check --debounce=20  # Check with 20-min debounce")
        print("  python session_monitor.py break 15           # Take 15-min break")
        print("  python session_monitor.py continue           # Resume after break")
        print("  python session_monitor.py record-invocation yuuji  # Record Yuuji invocation")
        print("  python session_monitor.py end                # End session")
    else:
        print(f"Unknown command: {command}")
        print(f"Run 'python session_monitor.py help' for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
