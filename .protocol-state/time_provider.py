#!/usr/bin/env python3
"""
Domain Zero Protocol - Clock Authority: TimeProvider
Version: 9.12.0 (Wave A / A2 phase (a))

Governing contract: docs/superpowers/specs/2026-08-04-clock-authority-adr.md
(revision 6, USER-signed-off, Sukuna-ratified) -- decisions D1-D4.
Governing audit: audits/2026-08-01-toji-session-time-authority-claude-codex.md
(AI-001, SEC-001, CODE-001, DESIGN-001, IMPL-001..004).

PURPOSE: a single, provider-neutral clock-authority primitive that:
  - D1: treats an aware UTC instant as the sole authority for stored/
    persisted time. Session IDs and formatted wall-clock strings are display
    artifacts only -- this module never derives a policy value from either.
  - D2: exposes `time.monotonic()` for in-process, single-invocation elapsed
    measurement, and keeps it clearly separated from UTC-instant subtraction
    (which remains the correct tool for cross-process/persisted durations).
  - D3: evaluates clock health (ok / skew-suspected / rollback-detected) for
    any UTC-instant gap used in a policy decision, including the D3.1 narrow
    same-process monotonic-vs-wall skew-diagnostic cross-check.
  - D4: resolves the user's IANA display/policy zone through exactly one
    precedence order (explicit config > DZP_USER_TIMEZONE env > OS-detected
    > unresolved), with every resolution carrying a recorded provenance
    value so a consumer can tell a confirmed zone from an execution-host
    guess (D4.2/D4.3) or a fully-unresolved state (D4.4).

SCOPE NOTE (phase (a)): this module is a STANDALONE primitive. It is
deliberately NOT wired into `.protocol-state/session_monitor.py`'s call
sites in this phase -- that migration (replacing the ~20 scattered
`datetime.now()` reads and the hardcoded 30/22/6 literals) is phase (b),
per the ADR's A2 Consequences section. `session_monitor.py` is unmodified by
this file's introduction.

D5 (time envelope), D7 (work-streak state), and D8 (versioned legacy
migration) are OUT OF SCOPE for this module -- they are phase A3-A5 per the
ADR's Consequences section.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# D4.4: tzdata (PyPI package) is a defensive, optional runtime dependency --
# CPython does not bundle IANA tzdata on Windows. Importing it here (even
# though nothing in this module calls into it directly) makes its presence
# on sys.path discoverable to `zoneinfo.ZoneInfo(...)` lookups, and the
# defensive try/except means a host WITHOUT it degrades gracefully (a
# `zoneinfo.ZoneInfo(...)` call for an otherwise-valid IANA name may then
# raise `zoneinfo.ZoneInfoNotFoundError` on that host, which
# `_validate_iana_zone()` below already treats as "zone did not validate",
# not as a crash).
try:  # pragma: no cover - presence/absence both exercised indirectly
    import tzdata  # noqa: F401
    _TZDATA_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TZDATA_AVAILABLE = False

try:  # pragma: no cover - presence/absence both exercised indirectly
    import zoneinfo
    _ZONEINFO_AVAILABLE = True
except ImportError:  # pragma: no cover - Python floor is 3.9+, always present
    zoneinfo = None  # type: ignore[assignment]
    _ZONEINFO_AVAILABLE = False

# D4.1.3/D4.4 problem 2: Windows does not natively expose an IANA zone name
# for its currently configured OS zone. `tzlocal` is the OS-zone-detection
# dependency evaluated by the ADR for that path -- optional, defensively
# imported, and used ONLY by the OS-fallback resolution step (never by the
# config/env steps, which already carry validated IANA names).
try:  # pragma: no cover - presence/absence both exercised indirectly
    import tzlocal
    _TZLOCAL_AVAILABLE = True
except ImportError:  # pragma: no cover
    tzlocal = None  # type: ignore[assignment]
    _TZLOCAL_AVAILABLE = False


# ---------------------------------------------------------------------------
# D4 -- zone provenance
# ---------------------------------------------------------------------------

class ZoneSource:
    """The four terminal `zone_source` values defined by ADR D4.2/D4.4.
    Deliberately a plain class of string constants (not `enum.Enum`) so a
    `ZoneResolution.source` value serializes directly into the D5 envelope's
    `user_zone.source` enum field without an extra `.value` unwrap -- the
    ADR's envelope schema names these exact four strings."""

    CONFIG = "config"
    ENV = "env"
    OS_FALLBACK = "os-fallback"
    UNRESOLVED = "unresolved"

    ALL = (CONFIG, ENV, OS_FALLBACK, UNRESOLVED)


@dataclass(frozen=True)
class ZoneResolution:
    """Result of `TimeProvider.resolve_user_zone()`.

    Attributes:
        iana: The resolved IANA zone identifier (e.g. "America/Detroit"), or
            None when `source == ZoneSource.UNRESOLVED` (ADR D4.4 -- no local
            time may be asserted in this state).
        source: One of `ZoneSource.ALL` -- D4.2's mandatory provenance value.
    """

    iana: Optional[str]
    source: str

    def __post_init__(self) -> None:
        if self.source not in ZoneSource.ALL:
            raise ValueError(f"Invalid zone source {self.source!r}; must be one of {ZoneSource.ALL}")
        if self.source == ZoneSource.UNRESOLVED and self.iana is not None:
            raise ValueError("ZoneResolution.iana must be None when source is 'unresolved' (ADR D4.4)")
        if self.source != ZoneSource.UNRESOLVED and not self.iana:
            raise ValueError(f"ZoneResolution.iana must be set when source is {self.source!r}")


class InvalidTimezoneConfigError(ValueError):
    """D4.1.1/D4.1.2: an explicit config or env zone value that fails IANA
    validation is a HARD config error surfaced to the user -- never a silent
    fallback to the next precedence tier. Raised by `resolve_user_zone()`
    only for the config/env tiers; the OS-fallback tier degrades to
    `ZoneSource.UNRESOLVED` instead of raising (D4.4), because there is no
    "next tier" left for it to hand the error to."""


# ---------------------------------------------------------------------------
# D3 -- clock health
# ---------------------------------------------------------------------------

class ClockHealth:
    """The three clock-health states defined by ADR D3.1. Plain string
    constants for the same envelope-serialization reason as `ZoneSource`."""

    OK = "ok"
    SKEW_SUSPECTED = "skew-suspected"
    ROLLBACK_DETECTED = "rollback-detected"

    ALL = (OK, SKEW_SUSPECTED, ROLLBACK_DETECTED)


@dataclass(frozen=True)
class ClockHealthResult:
    """Result of `TimeProvider.evaluate_clock_health()`.

    Attributes:
        state: One of `ClockHealth.ALL`.
        gap_seconds: The computed `(later - earlier)` gap in seconds, or None
            when the state precludes trusting the gap for policy purposes
            (D3.2: "consumers MUST NOT silently compute a duration ... from
            the anomalous pair"). `skew-suspected` from an implausible-but-
            non-negative gap still carries the (untrusted-for-policy, but
            diagnostically useful) computed value; `rollback-detected` never
            does, because a negative/future pair has no meaningful magnitude
            to report.
        reason: Short, machine-stable explanation string.
    """

    state: str
    gap_seconds: Optional[float]
    reason: str

    def __post_init__(self) -> None:
        if self.state not in ClockHealth.ALL:
            raise ValueError(f"Invalid clock health state {self.state!r}; must be one of {ClockHealth.ALL}")

    @property
    def is_ok(self) -> bool:
        return self.state == ClockHealth.OK


# Defaults mirror the ADR's proposed `protocol.config.yaml` values
# (D3.1 / config-object-spec section) -- the ONE place these numbers are
# defined as code defaults. `.protocol-state/timing_policy.py`'s loader
# supplies config-resolved overrides; nothing else should hardcode these.
DEFAULT_IMPLAUSIBLE_GAP_DAYS = 30
DEFAULT_SKEW_TOLERANCE_SECONDS = 5.0

_SECONDS_PER_DAY = 86400


# ---------------------------------------------------------------------------
# TimeProvider
# ---------------------------------------------------------------------------

class TimeProvider:
    """Provider-neutral clock-authority primitive (ADR D1-D4).

    Stateless with respect to any persisted record -- callers own state
    (session_monitor.py, project_state_manager.py, the future D5 envelope
    builder); this class only ever reads the system clock / environment /
    config values it is explicitly given and returns typed, provenance-
    carrying results. No method here mutates or persists anything.
    """

    def __init__(
        self,
        implausible_gap_days: int = DEFAULT_IMPLAUSIBLE_GAP_DAYS,
        skew_tolerance_seconds: float = DEFAULT_SKEW_TOLERANCE_SECONDS,
    ) -> None:
        if implausible_gap_days <= 0:
            raise ValueError(f"implausible_gap_days must be positive, got {implausible_gap_days}")
        if skew_tolerance_seconds < 0:
            raise ValueError(f"skew_tolerance_seconds must be non-negative, got {skew_tolerance_seconds}")
        self.implausible_gap_days = implausible_gap_days
        self.skew_tolerance_seconds = skew_tolerance_seconds

    # -- D1: UTC instant authority ---------------------------------------

    def utc_now(self) -> datetime:
        """The sole authoritative "now" for every persisted/policy read
        (ADR D1.1). Always aware, always UTC."""
        return datetime.now(timezone.utc)

    # -- D2: monotonic elapsed time ---------------------------------------

    def monotonic(self) -> float:
        """`time.monotonic()` passthrough for in-process, single-invocation
        elapsed measurement (ADR D2.1). Never persist this value and never
        compare it across process boundaries -- it is meaningless outside
        the process that produced it. The D3.1 skew-diagnostic exception
        (`evaluate_clock_health()`'s optional monotonic cross-check) is the
        ONLY sanctioned same-process comparison against a wall-clock delta.
        """
        return time.monotonic()

    # -- D3: clock-health evaluation ---------------------------------------

    def evaluate_clock_health(
        self,
        earlier: datetime,
        later: datetime,
        *,
        now: Optional[datetime] = None,
        mono_earlier: Optional[float] = None,
        mono_later: Optional[float] = None,
    ) -> ClockHealthResult:
        """Evaluate the clock-health state of the gap `later - earlier`
        (ADR D3.1). Both `earlier` and `later` MUST be aware UTC datetimes
        (D1.1); this method does not itself normalize naive input -- callers
        use `_parse_utc()`-equivalent normalization upstream (that remains
        `session_monitor.py`'s existing, ADR-approved helper; not
        duplicated here).

        Args:
            earlier: The chronologically-earlier labeled instant (e.g. a
                previous session's end, or a session's start_time).
            later: The chronologically-later labeled instant (e.g. the
                current start, or "now").
            now: The authoritative current instant used for the future-
                timestamp rejection rule (D3.1's rollback-detected clause
                "... is in the future relative to the current authoritative
                instant"). Defaults to `self.utc_now()`.
            mono_earlier / mono_later: Optional same-process
                `time.monotonic()` readings taken at the same two moments as
                `earlier`/`later`. When BOTH are supplied, the D3.1 narrow
                skew-diagnostic exception cross-checks the monotonic delta
                against the wall-clock delta and flags `skew-suspected` if
                they diverge beyond `skew_tolerance_seconds`. Omit both for
                a pure cross-process/persisted comparison (the common case);
                supplying only one is a caller error (raises).

        Returns:
            ClockHealthResult. Per D3.3, this method never mutates or
            "corrects" its inputs -- it is read-only metadata about the pair.
        """
        if (mono_earlier is None) != (mono_later is None):
            raise ValueError(
                "mono_earlier and mono_later must both be provided or both omitted "
                "(D3.1's monotonic cross-check needs both same-process readings)."
            )

        if earlier.tzinfo is None or later.tzinfo is None:
            raise ValueError(
                "evaluate_clock_health() requires aware UTC datetimes for both "
                "'earlier' and 'later' (ADR D1.1) -- normalize naive input before calling."
            )

        if now is None:
            now = self.utc_now()
        elif now.tzinfo is None:
            raise ValueError("evaluate_clock_health()'s 'now' must be an aware UTC datetime.")

        # D3.1 rollback-detected, clause 2: a labeled timestamp in the future
        # relative to the authoritative instant.
        if earlier > now or later > now:
            return ClockHealthResult(
                state=ClockHealth.ROLLBACK_DETECTED,
                gap_seconds=None,
                reason="future timestamp relative to authoritative now",
            )

        gap_seconds = (later - earlier).total_seconds()

        # D3.1 rollback-detected, clause 1: negative gap (later precedes earlier).
        if gap_seconds < 0:
            return ClockHealthResult(
                state=ClockHealth.ROLLBACK_DETECTED,
                gap_seconds=None,
                reason="negative gap: later-labeled instant precedes earlier-labeled instant",
            )

        implausible_ceiling_seconds = self.implausible_gap_days * _SECONDS_PER_DAY
        if gap_seconds > implausible_ceiling_seconds:
            return ClockHealthResult(
                state=ClockHealth.SKEW_SUSPECTED,
                gap_seconds=gap_seconds,
                reason=(
                    f"gap ({gap_seconds:.0f}s) exceeds the "
                    f"{self.implausible_gap_days}-day implausibility ceiling"
                ),
            )

        # D3.1's narrow, same-process skew-diagnostic exception: a monotonic
        # cross-check is the ONE case a monotonic reading is compared against
        # a wall-clock delta (never persisted, never used outside this check).
        if mono_earlier is not None and mono_later is not None:
            mono_delta = mono_later - mono_earlier
            divergence = abs(gap_seconds - mono_delta)
            if divergence > self.skew_tolerance_seconds:
                return ClockHealthResult(
                    state=ClockHealth.SKEW_SUSPECTED,
                    gap_seconds=gap_seconds,
                    reason=(
                        f"monotonic/wall divergence ({divergence:.3f}s) exceeds "
                        f"{self.skew_tolerance_seconds}s tolerance"
                    ),
                )

        return ClockHealthResult(state=ClockHealth.OK, gap_seconds=gap_seconds, reason="ok")

    # -- D4: user zone resolution ---------------------------------------

    def resolve_user_zone(
        self,
        config_timezone: Optional[str] = None,
        env_timezone: Optional[str] = None,
        _env: Optional[dict] = None,
    ) -> ZoneResolution:
        """Resolve the user's display/policy IANA zone per the exactly-one
        precedence order defined by ADR D4.1: explicit config > DZP_USER_TIMEZONE
        env > OS-detected > unresolved.

        Args:
            config_timezone: The value of `protocol.config.yaml::user.timezone`
                (None/empty means "not set" -- falls through, per the ADR's
                proposed config default of `null`).
            env_timezone: Explicit override for the env-tier value, for
                dependency-injected testing. When None, the real
                `DZP_USER_TIMEZONE` environment variable is read (via `_env`
                if supplied, else `os.environ`).
            _env: Optional environment mapping override (test seam only;
                defaults to `os.environ`). Ignored when `env_timezone` is
                explicitly supplied.

        Returns:
            ZoneResolution. Never returns a partially-resolved state --
            `source` is always exactly one of the four terminal values.

        Raises:
            InvalidTimezoneConfigError: an explicit config or env value that
                fails IANA validation (D4.1.1/D4.1.2 -- a hard error, not a
                silent fallback to the next tier).
        """
        # Tier 1: explicit config (D4.1.1).
        if config_timezone:
            zi = self._validate_iana_zone(config_timezone)
            if zi is None:
                raise InvalidTimezoneConfigError(
                    f"protocol.config.yaml::user.timezone={config_timezone!r} is not a "
                    "valid IANA zone identifier (ADR D4.1.1)."
                )
            return ZoneResolution(iana=config_timezone, source=ZoneSource.CONFIG)

        # Tier 2: DZP_USER_TIMEZONE environment override (D4.1.2).
        env_map = _env if _env is not None else os.environ
        resolved_env_value = env_timezone if env_timezone is not None else env_map.get("DZP_USER_TIMEZONE")
        if resolved_env_value:
            zi = self._validate_iana_zone(resolved_env_value)
            if zi is None:
                raise InvalidTimezoneConfigError(
                    f"DZP_USER_TIMEZONE={resolved_env_value!r} is not a valid IANA "
                    "zone identifier (ADR D4.1.2)."
                )
            return ZoneResolution(iana=resolved_env_value, source=ZoneSource.ENV)

        # Tier 3: OS-detected zone, last resort (D4.1.3/D4.4).
        os_zone = self._detect_os_zone()
        if os_zone is not None:
            return ZoneResolution(iana=os_zone, source=ZoneSource.OS_FALLBACK)

        # Tier 4: terminal unresolved state (D4.4) -- never raises; the
        # envelope (D5, phase A3) is the mechanism that surfaces this state
        # to a consumer, not an exception.
        return ZoneResolution(iana=None, source=ZoneSource.UNRESOLVED)

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _validate_iana_zone(zone_name: str) -> Optional["zoneinfo.ZoneInfo"]:  # type: ignore[name-defined]
        """Validate `zone_name` against the `zoneinfo` database (ADR D4.1.1).
        Returns the resolved `ZoneInfo` on success, None on any failure
        (unknown zone, missing tzdata source, malformed name) -- callers
        decide whether None is a hard error (config/env tiers) or a
        fall-through (OS-fallback tier)."""
        if not zone_name or not _ZONEINFO_AVAILABLE:
            return None
        try:
            return zoneinfo.ZoneInfo(zone_name)
        except Exception:
            # Covers zoneinfo.ZoneInfoNotFoundError (unknown zone / no tzdata
            # source available) and any other resolution failure -- never
            # raises out of this helper; see ADR D4.4 problem 1.
            return None

    def _detect_os_zone(self) -> Optional[str]:
        """OS-zone-detection fallback (ADR D4.1.3/D4.4). Tries `tzlocal`
        first (cross-platform IANA-name detection, including the Windows
        native-name mapping D4.4 problem 2 identifies as otherwise
        unsolved), then a POSIX `/etc/localtime` symlink inspection as a
        dependency-free secondary path. Returns None (never raises) when
        neither can produce a validated IANA zone -- the "doubly-degraded"
        case D4.4 requires resolve_user_zone() to report as `unresolved`
        rather than a broken partial `os-fallback`.
        """
        if _TZLOCAL_AVAILABLE:
            try:
                name = tzlocal.get_localzone_name()  # type: ignore[union-attr]
            except Exception:
                name = None
            if name and self._validate_iana_zone(name) is not None:
                return name

        posix_zone = self._detect_posix_zone_via_localtime_symlink()
        if posix_zone and self._validate_iana_zone(posix_zone) is not None:
            return posix_zone

        return None

    @staticmethod
    def _detect_posix_zone_via_localtime_symlink() -> Optional[str]:
        """Dependency-free POSIX fallback: `/etc/localtime` is conventionally
        a symlink into the system zoneinfo tree (e.g.
        `/usr/share/zoneinfo/America/Detroit`); the IANA name is the path
        segment(s) after `zoneinfo/`. Returns None on any platform/state
        where this convention doesn't hold (including all of Windows, which
        has no `/etc/localtime` at all -- `tzlocal` is the only path there).
        """
        localtime_path = Path("/etc/localtime")
        try:
            if not localtime_path.is_symlink():
                return None
            target = os.readlink(str(localtime_path))
        except (OSError, NotImplementedError):
            return None

        match = re.search(r"zoneinfo/(.+)$", target.replace("\\", "/"))
        if not match:
            return None
        candidate = match.group(1)
        # Guard against a symlink target that resolves outside the zoneinfo
        # tree's expected shape (defense-in-depth; _validate_iana_zone()
        # would reject it anyway, but avoid handing a malformed string further).
        if not re.fullmatch(r"[A-Za-z0-9_+\-]+(/[A-Za-z0-9_+\-]+)*", candidate):
            return None
        return candidate
