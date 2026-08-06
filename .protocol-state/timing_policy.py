#!/usr/bin/env python3
"""
Domain Zero Protocol - Clock Authority: Timing-Policy Configuration
Version: 9.12.0 (Wave A / A2 phase (a))

Governing contract: docs/superpowers/specs/2026-08-04-clock-authority-adr.md
(revision 6, USER-signed-off, Sukuna-ratified) -- decision D6 (Toji gate 3)
and the "Config object spec" section.
Governing audit: audits/2026-08-01-toji-session-time-authority-claude-codex.md
(IMPL-002, IMPL-004).

PURPOSE: exactly ONE validated loader for ALL session timing policy --
duration alert thresholds, the late-night window, the session-continuation
gap, the minimum qualifying break, and clock-health tolerances (ADR D6.1).
Defaults for every one of these fields are defined in exactly one place (this
module's `_DEFAULTS` map), closing the four-independently-drifting-copies
problem IMPL-004 identified (`_default_state()`, `project_state_manager.py`,
`validation-rules.yaml`, and the alert template each currently hardcode their
own copy).

`protocol.config.yaml::safety.boundaries.late_night_threshold` and
`safety.session_tracking.session_continuation_threshold_minutes` are
DECLARED but currently UNREAD by `session_monitor.py` (IMPL-002). THIS
loader reads both -- that is the direct, testable acceptance criterion for
closing IMPL-002 (ADR D6.2). Editing either key in `protocol.config.yaml` and
re-running `load_timing_policy()` changes the resolved value; this module
does not yet change ENFORCED runtime behavior in session_monitor.py, because
wiring session_monitor.py's call sites onto this loader is phase (b) (out of
scope for this increment, per the ADR's A2 Consequences section) -- the
sibling characterization suite
(tests/test_session_monitor_time_characterization.py) freezes today's
pre-migration behavior for that reason.

SCOPE NOTE (phase (a)): D6.4/D6.5 (late-night as an independent alert reason
code, `alert.reasons` as a list rather than a single `alert_level` string)
are session_monitor.py CALL-SITE behavior changes and are explicitly OUT OF
SCOPE here -- this module only loads and validates the CONFIGURATION values
those call sites will consume in phase (b)/A3. `protocol/validation-rules.yaml`
reconciliation (adding `late_night_end_hour` to the required schema list) is
explicitly D8.6/A5 scope, not phase (a); this loader tolerates its absence
from validation-rules.yaml exactly as `_is_late_night()` already does via
`.get(..., default)`.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Mapping, Optional

sys.path.insert(0, str(Path(__file__).parent))
from time_provider import (  # noqa: E402
    DEFAULT_IMPLAUSIBLE_GAP_DAYS,
    DEFAULT_SKEW_TOLERANCE_SECONDS,
    InvalidTimezoneConfigError,
    TimeProvider,
    ZoneResolution,
    ZoneSource,
)

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover - PyYAML is a declared dep (requirements-dev.txt)
    yaml = None  # type: ignore[assignment]
    _YAML_AVAILABLE = False


# ---------------------------------------------------------------------------
# D6.1: the single default map. Every field this loader resolves has EXACTLY
# ONE default, defined HERE and nowhere else in this module.
# ---------------------------------------------------------------------------

_DEFAULTS: Dict[str, object] = {
    "initial_alert_minutes": 240,        # 4 hours
    "escalated_alert_minutes": 45,
    "critical_session_minutes": 360,     # 6 hours
    "max_continuous_minutes": 480,       # 8 hours
    "late_night_hour": 22,
    "late_night_end_hour": 6,
    "session_continuation_threshold_minutes": 30,
    "minimum_break_minutes": 15,
    "clock_health_implausible_gap_days": DEFAULT_IMPLAUSIBLE_GAP_DAYS,
    "clock_health_skew_tolerance_seconds": DEFAULT_SKEW_TOLERANCE_SECONDS,
}

# Validation ranges, reusing the same "reject out-of-range, loud fallback to
# default" pattern session_monitor.py's existing _load_alert_thresholds()
# already uses (ADR config-object-spec item 2: "reusing the existing
# per-field range-check pattern"). (min, max) inclusive.
_RANGES: Dict[str, tuple] = {
    "initial_alert_minutes": (120, 720),          # 2-12 hours, matches existing hours-based validation
    "escalated_alert_minutes": (15, 120),
    "critical_session_minutes": (240, 960),        # 4-16 hours
    "max_continuous_minutes": (360, 1440),         # 6-24 hours
    "late_night_hour": (0, 23),
    "late_night_end_hour": (0, 23),
    "session_continuation_threshold_minutes": (1, 1440),  # 1 minute .. 24h (MAX_SESSION_DURATION parity)
    "minimum_break_minutes": (1, 480),             # 1 minute .. 8h (MAX_BREAK_DURATION parity)
    "clock_health_implausible_gap_days": (1, 3650),  # 1 day .. 10 years
    "clock_health_skew_tolerance_seconds": (0, 300),  # 0 .. 5 minutes
}

_LATE_NIGHT_THRESHOLD_PATTERN = re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$")

# ---------------------------------------------------------------------------
# v9.12.0 A5 (ADR D6.1/D8.6, IMPL-004 full closure): public, read-only export
# of `_DEFAULTS` for OTHER modules that need the SAME literal default values
# without needing `load_timing_policy()`'s YAML-parsing/env/zoneinfo
# machinery. `project_state_manager.py`'s `_default_session_tracking()`
# previously hardcoded its own second copy of these same 7 literals
# (240/45/360/480/22/6-missing/15) -- exactly the "four independently
# drifting copies" pattern IMPL-004 named, just for the OTHER 6 fields
# `_default_state()`'s dict literal was already fixed for in A2 phase (b).
# `project_state_manager.py` deliberately does not call
# `load_timing_policy()` itself (see its own module-level import comment --
# it is a low-level, always-on module that must not gain a YAML-parsing/
# `InvalidTimezoneConfigError` coupling just to read default literals), so
# this dict -- not the full loader -- is the shared single source those
# defaults sync onto. `_DEFAULTS` itself remains the module-private,
# MUTABLE name used throughout the rest of this file; `TIMING_POLICY_DEFAULTS`
# is a `MappingProxyType` VIEW over the exact same underlying dict, never a
# copy, so the two can never drift relative to each other -- reads through
# either name always agree.
#
# v9.12.0 A5 remediation (SEC-CLOCKADR-9.12.0-023, P3, Megumi gate-5 review):
# originally exported as the SAME live mutable dict object. A shared mutable
# global exported publicly is fragile against a future regression -- any
# later code doing `TIMING_POLICY_DEFAULTS[k] = v` or `.update(...)` would
# silently corrupt the single source of truth for the entire process,
# defeating the exact "one place, not four drifting copies" property this
# increment exists to establish. `MappingProxyType` turns that class of
# mistake into a loud `TypeError` at the mutation site instead of silent
# corruption, at zero cost to the two current consumers (both read-only).
TIMING_POLICY_DEFAULTS: Mapping[str, object] = MappingProxyType(_DEFAULTS)


class ConfigSource:
    """Provenance values for a single resolved field (ADR D6.3 -- "the
    source each was resolved from" recorded alongside the value, the same
    provenance discipline as D4 applied to policy values generally)."""

    CONFIG = "config"
    ENV = "env"
    DEFAULT = "default"

    ALL = (CONFIG, ENV, DEFAULT)


@dataclass(frozen=True)
class TimingPolicyConfig:
    """The single resolved timing-policy object (ADR D6.1). Every field
    listed in `_DEFAULTS` appears here, plus the resolved user zone (D4,
    folded in per the ADR's config-object-spec item 3) and a per-field
    provenance map (D6.3)."""

    initial_alert_minutes: int
    escalated_alert_minutes: int
    critical_session_minutes: int
    max_continuous_minutes: int
    late_night_hour: int
    late_night_end_hour: int
    session_continuation_threshold_minutes: int
    minimum_break_minutes: int
    clock_health_implausible_gap_days: int
    clock_health_skew_tolerance_seconds: float
    user_zone: ZoneResolution
    sources: Dict[str, str] = field(default_factory=dict)

    def make_time_provider(self) -> TimeProvider:
        """Convenience constructor: a `TimeProvider` configured with THIS
        object's clock-health tolerances, so callers never have to thread
        the two raw numbers through separately."""
        return TimeProvider(
            implausible_gap_days=self.clock_health_implausible_gap_days,
            skew_tolerance_seconds=self.clock_health_skew_tolerance_seconds,
        )


def _validated(key: str, raw_value, *, warn: bool = True) -> object:
    """Range-check `raw_value` for `key` against `_RANGES`. On failure,
    print the existing loud `[!] Invalid ... Using default: ...` pattern and
    return the default. Never raises -- malformed config is always a loud,
    logged fallback, never a silent one or a crash (matches the existing
    session_monitor.py convention this loader is unifying)."""
    lo, hi = _RANGES[key]
    default = _DEFAULTS[key]
    try:
        numeric = type(default)(raw_value)
    except (TypeError, ValueError):
        if warn:
            print(f"[!] Invalid {key}: {raw_value!r} (not numeric). Using default: {default}")
        return default
    if not (lo <= numeric <= hi):
        if warn:
            print(f"[!] Invalid {key}: {numeric}. Must be {lo}-{hi}. Using default: {default}")
        return default
    return numeric


def _parse_late_night_threshold(raw_value: str) -> Optional[int]:
    """Parse `safety.boundaries.late_night_threshold` (e.g. "22:00") into an
    hour integer. Returns None on malformed input (caller falls back to
    default with a loud warning) -- this is the IMPL-002 closure: this key
    was previously declared but never read by any loader at all."""
    if not isinstance(raw_value, str):
        return None
    match = _LATE_NIGHT_THRESHOLD_PATTERN.match(raw_value.strip())
    if not match:
        return None
    return int(match.group(1))


def _load_yaml_config(config_path: Optional[Path]) -> Dict:
    """Load and parse `config_path` as YAML. Returns {} (never raises) when
    the file is missing, unreadable, empty, or fails to parse -- every
    resolved field then falls through to its default with a loud warning at
    the point of use, exactly like the existing per-field loaders in
    session_monitor.py already do for a missing/broken config file."""
    if config_path is None or not _YAML_AVAILABLE:
        return {}
    try:
        if not config_path.exists():
            return {}
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        return loaded if isinstance(loaded, dict) else {}
    except Exception as e:
        print(f"[!] Failed to load timing policy config from {config_path}: {e}")
        print("    Using all built-in defaults.")
        return {}


def load_timing_policy(
    protocol_root: Optional[Path] = None,
    config_path: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    time_provider: Optional[TimeProvider] = None,
) -> TimingPolicyConfig:
    """The ONE validated loader for all session timing policy (ADR D6.1).

    Args:
        protocol_root: Project root; `config_path` defaults to
            `protocol_root / "protocol.config.yaml"` when not given
            explicitly. At least one of `protocol_root`/`config_path` should
            normally be supplied; omitting both resolves every field to its
            built-in default (useful for unit tests of the default shape
            itself).
        config_path: Explicit path to the YAML config file, overrides the
            `protocol_root`-derived path when both are given.
        env: Optional environment mapping override for zone-resolution
            testing (passed through to `TimeProvider.resolve_user_zone()`'s
            `_env` seam). Defaults to the real `os.environ` when omitted.
        time_provider: Optional pre-constructed `TimeProvider` for zone
            resolution. When omitted, a temporary default-tolerance
            `TimeProvider` is used ONLY for the zone-resolution call (the
            returned `TimingPolicyConfig.make_time_provider()` is the
            correctly-tolerance-configured provider for actual clock-health
            use afterward -- resolving the zone does not depend on the
            clock-health tolerances at all, so this ordering is safe).

    Returns:
        TimingPolicyConfig -- one object carrying every resolved value AND
        its provenance source, ready to be consumed by (in phase (b)/A3, not
        this increment) `_default_state()`, `check_alert_needed()`,
        `_is_late_night()`, `start_session()`'s continuation-gap check, and
        the D5 envelope builder (ADR config-object-spec item 4).
    """
    if config_path is None and protocol_root is not None:
        config_path = Path(protocol_root) / "protocol.config.yaml"

    raw_config = _load_yaml_config(config_path)
    safety = raw_config.get("safety", {}) if isinstance(raw_config, dict) else {}
    if not isinstance(safety, dict):
        safety = {}
    boundaries = safety.get("boundaries", {})
    if not isinstance(boundaries, dict):
        boundaries = {}
    session_tracking = safety.get("session_tracking", {})
    if not isinstance(session_tracking, dict):
        session_tracking = {}
    alert_thresholds_raw = session_tracking.get("alert_thresholds", {})
    if not isinstance(alert_thresholds_raw, dict):
        alert_thresholds_raw = {}
    clock_health_raw = session_tracking.get("clock_health", {})
    if not isinstance(clock_health_raw, dict):
        clock_health_raw = {}
    thresholds_raw = session_tracking.get("thresholds", {})
    if not isinstance(thresholds_raw, dict):
        thresholds_raw = {}

    resolved: Dict[str, object] = {}
    sources: Dict[str, str] = {}

    # -- Duration alert thresholds. Config stores these in HOURS for the
    # first three (existing convention, unified.py preserves it for
    # backward-compatible config-file shape); minutes for escalated.
    def _resolve_hours_field(config_key: str, out_key: str, hours_to_minutes: bool = True) -> None:
        if config_key in alert_thresholds_raw:
            raw = alert_thresholds_raw[config_key]
            try:
                raw_numeric = float(raw)
            except (TypeError, ValueError):
                print(
                    f"[!] Invalid {config_key}: {raw!r} (not numeric). "
                    f"Using default: {_DEFAULTS[out_key]}"
                )
                resolved[out_key] = _DEFAULTS[out_key]
                sources[out_key] = ConfigSource.DEFAULT
                return
            raw_minutes = raw_numeric * 60 if hours_to_minutes else raw_numeric
            resolved[out_key] = _validated(out_key, raw_minutes)
            sources[out_key] = (
                ConfigSource.CONFIG if resolved[out_key] == raw_minutes else ConfigSource.DEFAULT
            )
        else:
            resolved[out_key] = _DEFAULTS[out_key]
            sources[out_key] = ConfigSource.DEFAULT

    _resolve_hours_field("initial_alert_hours", "initial_alert_minutes")
    _resolve_hours_field("critical_session_hours", "critical_session_minutes")
    _resolve_hours_field("max_continuous_hours", "max_continuous_minutes")
    _resolve_hours_field("escalated_alert_minutes", "escalated_alert_minutes", hours_to_minutes=False)

    # -- Late-night window. `late_night_hour` comes from the DECLARED-BUT-
    # PREVIOUSLY-UNREAD `safety.boundaries.late_night_threshold` (IMPL-002
    # closure) -- "HH:MM" string, parsed to an hour. `late_night_end_hour`
    # comes from the NEW `safety.session_tracking.thresholds.late_night_end_hour`
    # key proposed by the ADR's config-object-spec section.
    if "late_night_threshold" in boundaries:
        parsed_hour = _parse_late_night_threshold(boundaries["late_night_threshold"])
        if parsed_hour is None:
            print(
                f"[!] Invalid late_night_threshold: {boundaries['late_night_threshold']!r}. "
                f"Expected 'HH:MM'. Using default: {_DEFAULTS['late_night_hour']}:00"
            )
            resolved["late_night_hour"] = _DEFAULTS["late_night_hour"]
            sources["late_night_hour"] = ConfigSource.DEFAULT
        else:
            resolved["late_night_hour"] = _validated("late_night_hour", parsed_hour)
            sources["late_night_hour"] = (
                ConfigSource.CONFIG if resolved["late_night_hour"] == parsed_hour else ConfigSource.DEFAULT
            )
    else:
        resolved["late_night_hour"] = _DEFAULTS["late_night_hour"]
        sources["late_night_hour"] = ConfigSource.DEFAULT

    if "late_night_end_hour" in thresholds_raw:
        raw = thresholds_raw["late_night_end_hour"]
        resolved["late_night_end_hour"] = _validated("late_night_end_hour", raw)
        sources["late_night_end_hour"] = (
            ConfigSource.CONFIG if resolved["late_night_end_hour"] == raw else ConfigSource.DEFAULT
        )
    else:
        resolved["late_night_end_hour"] = _DEFAULTS["late_night_end_hour"]
        sources["late_night_end_hour"] = ConfigSource.DEFAULT

    # -- Session continuation gap. DECLARED-BUT-PREVIOUSLY-UNREAD
    # `safety.session_tracking.session_continuation_threshold_minutes`
    # (IMPL-002 closure, second key).
    if "session_continuation_threshold_minutes" in session_tracking:
        raw = session_tracking["session_continuation_threshold_minutes"]
        resolved["session_continuation_threshold_minutes"] = _validated(
            "session_continuation_threshold_minutes", raw
        )
        sources["session_continuation_threshold_minutes"] = (
            ConfigSource.CONFIG
            if resolved["session_continuation_threshold_minutes"] == raw
            else ConfigSource.DEFAULT
        )
    else:
        resolved["session_continuation_threshold_minutes"] = _DEFAULTS[
            "session_continuation_threshold_minutes"
        ]
        sources["session_continuation_threshold_minutes"] = ConfigSource.DEFAULT

    # -- Minimum qualifying break (existing key, already read by
    # session_monitor.py's _default_state() literal today -- this loader
    # unifies it, but no bug was previously reported for this specific key).
    if "minimum_break_minutes" in thresholds_raw:
        raw = thresholds_raw["minimum_break_minutes"]
        resolved["minimum_break_minutes"] = _validated("minimum_break_minutes", raw)
        sources["minimum_break_minutes"] = (
            ConfigSource.CONFIG if resolved["minimum_break_minutes"] == raw else ConfigSource.DEFAULT
        )
    else:
        resolved["minimum_break_minutes"] = _DEFAULTS["minimum_break_minutes"]
        sources["minimum_break_minutes"] = ConfigSource.DEFAULT

    # -- Clock-health tolerances (ADR D3.1 / config-object-spec).
    if "implausible_gap_days" in clock_health_raw:
        raw = clock_health_raw["implausible_gap_days"]
        resolved["clock_health_implausible_gap_days"] = _validated("clock_health_implausible_gap_days", raw)
        sources["clock_health_implausible_gap_days"] = (
            ConfigSource.CONFIG
            if resolved["clock_health_implausible_gap_days"] == raw
            else ConfigSource.DEFAULT
        )
    else:
        resolved["clock_health_implausible_gap_days"] = _DEFAULTS["clock_health_implausible_gap_days"]
        sources["clock_health_implausible_gap_days"] = ConfigSource.DEFAULT

    if "skew_tolerance_seconds" in clock_health_raw:
        raw = clock_health_raw["skew_tolerance_seconds"]
        resolved["clock_health_skew_tolerance_seconds"] = _validated(
            "clock_health_skew_tolerance_seconds", raw
        )
        sources["clock_health_skew_tolerance_seconds"] = (
            ConfigSource.CONFIG
            if resolved["clock_health_skew_tolerance_seconds"] == raw
            else ConfigSource.DEFAULT
        )
    else:
        resolved["clock_health_skew_tolerance_seconds"] = _DEFAULTS["clock_health_skew_tolerance_seconds"]
        sources["clock_health_skew_tolerance_seconds"] = ConfigSource.DEFAULT

    # -- D4 user zone, folded into this same loader per the ADR's
    # config-object-spec item 3 ("Resolves user.timezone per the D4
    # precedence order ... Returns one object carrying every resolved value
    # AND its source").
    user_config = raw_config.get("user", {}) if isinstance(raw_config, dict) else {}
    if not isinstance(user_config, dict):
        user_config = {}
    config_timezone = user_config.get("timezone") or None

    zone_provider = time_provider or TimeProvider()
    try:
        user_zone = zone_provider.resolve_user_zone(config_timezone=config_timezone, _env=env)
    except InvalidTimezoneConfigError:
        # D4.1.1: a hard config error is surfaced to the user -- this loader
        # re-raises rather than silently downgrading, so a caller building a
        # `status`/`start` surface can decide how to present it (D5's
        # `envelope_status: "degraded"` machinery is phase A3; here we
        # simply do not swallow the error).
        raise
    sources["user_zone"] = user_zone.source

    return TimingPolicyConfig(
        initial_alert_minutes=resolved["initial_alert_minutes"],
        escalated_alert_minutes=resolved["escalated_alert_minutes"],
        critical_session_minutes=resolved["critical_session_minutes"],
        max_continuous_minutes=resolved["max_continuous_minutes"],
        late_night_hour=resolved["late_night_hour"],
        late_night_end_hour=resolved["late_night_end_hour"],
        session_continuation_threshold_minutes=resolved["session_continuation_threshold_minutes"],
        minimum_break_minutes=resolved["minimum_break_minutes"],
        clock_health_implausible_gap_days=resolved["clock_health_implausible_gap_days"],
        clock_health_skew_tolerance_seconds=resolved["clock_health_skew_tolerance_seconds"],
        user_zone=user_zone,
        sources=sources,
    )
