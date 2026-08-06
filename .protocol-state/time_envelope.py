#!/usr/bin/env python3
"""
Domain Zero Protocol - Clock Authority: Time Envelope (ADR D5, Toji gate 4)
Version: 9.12.0 (Wave A / A4)

Governing contract: docs/superpowers/specs/2026-08-04-clock-authority-adr.md
(revision 6, USER-signed-off, Sukuna-ratified) -- decision D5, and the
"Envelope schema (envelope_schema: 1)" section (field table + JSON example +
provider relay rule).
Governing audit: audits/2026-08-01-toji-session-time-authority-claude-codex.md
(AI-001, HIGH: "Claude and Codex lack an authoritative user-time context").

PURPOSE: build the single, versioned, provider-neutral time envelope emitted
by every session-lifecycle boundary (`start`, `status`, `check`, `resume`,
`transfer_begin`, `transfer_finalize`, `handoff`). This module is a PURE
builder -- it never reads the clock, the filesystem, or any persisted state
itself; every value it needs is passed in by the caller (session_monitor.py),
which already owns the `TimeProvider`/`TimingPolicyConfig`/`work_streak`
instances this module composes into the D5 schema. Keeping this module
side-effect-free makes it independently unit-testable with zero mocking of
I/O, and keeps it consumer-agnostic per ADR D22.4/§7.5's "the future domain
façade is just another consumer" constraint.

D5.6's `envelope_status` contract is implemented as two layers:
  - `build_envelope()` composes the envelope and determines `degraded` vs
    `complete` from its own inputs (an unresolved zone, or a clock-health
    anomaly on the boundary gap). It never raises for a merely DEGRADED
    input -- degraded is a normal, expected shape.
  - `build_envelope_safe()` wraps `build_envelope()` and is the function
    session_monitor.py actually calls. Any exception during composition
    (malformed input, a caller bug) is caught and converted into the D5.6
    `unavailable` minimal stub -- carrying only `envelope_schema`,
    `envelope_status`, `envelope_status_reasons`, and a best-effort
    `emitted_at_utc` -- rather than ever propagating a stack trace into a
    session-lifecycle command that must not fail SOLELY because the
    envelope could not be built.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
from time_provider import ClockHealth, TimeProvider, ZoneResolution, ZoneSource  # noqa: E402

# ADR D5.2: the schema version every envelope this module builds carries.
# Additive enum extensions (D5.5) do NOT bump this; only a breaking removal/
# rename/meaning-change of an existing enum value would.
ENVELOPE_SCHEMA_VERSION = 1


class EnvelopeStatus:
    """D5.6's three top-level `envelope_status` values."""

    COMPLETE = "complete"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

    ALL = (COMPLETE, DEGRADED, UNAVAILABLE)


class EnvelopeStatusReason:
    """D5.6's `envelope_status_reasons` enum. Combinable.

    v9.12.0 A6 (ADR D8.5 read-side gating, SEC-CLOCKADR-9.12.0-021):
    `AMBIGUOUS_TIMESTAMP` is an ADDITIVE enum extension per D5.5 (no
    `envelope_schema` bump) -- distinct from `CLOCK_ANOMALY` on purpose.
    `CLOCK_ANOMALY` means the CLOCK itself looked unhealthy (D3: skew or
    rollback) for a pair of otherwise-trusted instants. `AMBIGUOUS_TIMESTAMP`
    means the clock is not in question -- a boundary instant's PROVENANCE
    is unconfirmed (a still-ambiguous pre-migration record, or a new naive
    write from an unanticipated code path, per the read-side-gating design
    note). Conflating the two would misdescribe the anomaly to a consumer
    relying on D5.6's machine-checkable status."""

    ZONE_UNRESOLVED = "zone_unresolved"
    CLOCK_ANOMALY = "clock_anomaly"
    GENERATION_ERROR = "generation_error"
    AMBIGUOUS_TIMESTAMP = "ambiguous_timestamp"

    ALL = (ZONE_UNRESOLVED, CLOCK_ANOMALY, GENERATION_ERROR, AMBIGUOUS_TIMESTAMP)


class SessionBoundary:
    """The seven lifecycle boundaries D5.1 names as envelope emission points."""

    START = "start"
    STATUS = "status"
    CHECK = "check"
    RESUME = "resume"
    TRANSFER_BEGIN = "transfer_begin"
    TRANSFER_FINALIZE = "transfer_finalize"
    HANDOFF = "handoff"

    ALL = (START, STATUS, CHECK, RESUME, TRANSFER_BEGIN, TRANSFER_FINALIZE, HANDOFF)


class ContinuityClass:
    """`continuity.class` -- exactly two values (ADR revision 6 / Sukuna C3):
    `undetermined_clock_anomaly` was deliberately dropped. An anomaly-forced
    label is always `fresh_session`; `clock_health` (already
    skew-suspected/rollback-detected) is what distinguishes "confirmed
    fresh" from "anomaly forced this label" -- see the field table note."""

    SAME_STREAK_CONTINUATION = "same_streak_continuation"
    FRESH_SESSION = "fresh_session"

    ALL = (SAME_STREAK_CONTINUATION, FRESH_SESSION)


class AlertReason:
    """D6.5's alert reason codes -- combinable, carried in `alert.reasons`."""

    DURATION_INITIAL = "duration_initial"
    DURATION_ESCALATED = "duration_escalated"
    DURATION_CRITICAL = "duration_critical"
    DURATION_MAXIMUM = "duration_maximum"
    LATE_NIGHT = "late_night"
    # Toji audit 2026-08-06 (CODE-001, MEDIUM): additive enum extension
    # (D5.5 -- no `envelope_schema` bump required) for `check_alert_needed()`'s
    # own CODE-001 fail-closed policy: when a clock-health anomaly
    # (skew-suspected/rollback-detected) makes the primary session-duration
    # gap untrustworthy, the conservative choice for a WELLBEING safety
    # check is to surface an alert rather than silently under-alert.
    CLOCK_ANOMALY = "clock_anomaly"

    ALL = (
        DURATION_INITIAL,
        DURATION_ESCALATED,
        DURATION_CRITICAL,
        DURATION_MAXIMUM,
        LATE_NIGHT,
        CLOCK_ANOMALY,
    )


def _format_gap_seconds(seconds: float) -> str:
    """Render a non-negative second count as `"6h 35m 21s"` (hours omitted
    when zero) -- matches the ADR's JSON example
    (`previous_end_utc`/`current_start_utc` 23721.778075s -> "6h 35m 21s")."""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def build_envelope(
    *,
    boundary: str,
    time_provider: TimeProvider,
    zone_resolution: ZoneResolution,
    user_zone_info: Optional[object] = None,
    session_id: Optional[str] = None,
    now: Optional[datetime] = None,
    previous_end_utc: Optional[datetime] = None,
    current_start_utc: Optional[datetime] = None,
    session_continuation_threshold_minutes: Optional[int] = None,
    work_streak: Optional[Dict] = None,
    late_night_hour: Optional[int] = None,
    late_night_end_hour: Optional[int] = None,
    is_late_night: Optional[bool] = None,
    alert_needed: bool = False,
    alert_reasons: Optional[List[str]] = None,
    ambiguous_boundary_timestamp: bool = False,
) -> Dict:
    """Compose one ADR D5 time envelope. Pure function -- no I/O.

    Args:
        boundary: One of `SessionBoundary.ALL`. Required.
        time_provider: The caller's `TimeProvider` (D1-D4), used ONLY for
            `utc_now()` (when `now` is omitted) and `evaluate_clock_health()`
            (when both boundary instants are supplied). Never mutated.
        zone_resolution: The caller's D4-resolved `ZoneResolution` (already
            IANA-validated and provenance-tagged by
            `TimeProvider.resolve_user_zone()`).
        user_zone_info: A concrete `zoneinfo.ZoneInfo` for `zone_resolution`
            (or None for the D4.4 unresolved terminal state) -- used to
            convert `now` into `local_wall_time`. Untyped in the signature to
            avoid a hard `zoneinfo` import dependency in this module beyond
            what `time_provider.py` already carries.
        session_id: The session id this envelope concerns, or None (e.g. a
            `check` with no active session). Always paired with
            `session_id_is_opaque: true` (D5.1's binding consumer rule).
        now: The authoritative instant. Defaults to `time_provider.utc_now()`.
        previous_end_utc / current_start_utc: The two instants D7/D3's gap
            comparison spans (e.g. the just-archived session's end and the
            new session's start). Omit either (or both) when no boundary gap
            applies to this emission (e.g. a `start` with no prior session)
            -- `gap`/`continuity` degrade gracefully rather than fabricating
            a comparison.
        session_continuation_threshold_minutes: The D6 timing-policy value
            used to classify `continuity.class`. Defaults to 30 (the ADR's
            documented default) when omitted.
        work_streak: The caller's current work-streak record (any dict
            subset of the D7.2 fields is tolerated via `.get(..., default)`).
        late_night_hour / late_night_end_hour: The resolved D6 late-night
            window, for the envelope's `late_night.threshold_local` /
            `threshold_end_local` transparency fields.
        is_late_night: The caller's already-computed `_is_late_night()`
            result (this module never recomputes it -- session_monitor.py
            owns the single implementation, per BUG-SESSION-005).
        alert_needed / alert_reasons: The caller's already-computed D6.5
            alert decision (this module never recomputes alert policy).
        ambiguous_boundary_timestamp: v9.12.0 A6 (ADR D8.5 read-side gating,
            SEC-CLOCKADR-9.12.0-021). The caller sets this True when it
            deliberately withheld `previous_end_utc`/`current_start_utc`
            (passing both as None) because the RAW value backing one of them
            was a naive timestamp in an already-migrated (`time_schema >= 1`)
            state file -- i.e. a still-ambiguous pre-migration record, or a
            new naive write from an unanticipated code path. This module
            never re-derives that condition itself (it has no access to
            `time_schema` or the raw string -- session_monitor.py's D8.5 gate
            runs upstream); it only renders the caller's already-made
            decision into the envelope: `envelope_status_reasons` gains
            `ambiguous_timestamp`, `envelope_status` becomes `degraded`, and
            `continuity.class` is forced to `fresh_session` with a reason
            naming the D8.5 gate specifically -- never silently identical to
            the genuine "no previous session boundary available" case, so a
            consumer can tell "there is no prior session" apart from "there
            IS a prior session but its timestamp is not trusted."

    Returns:
        A dict matching the ADR's `envelope_schema: 1` field table exactly.

    Raises:
        ValueError: `boundary` is not one of `SessionBoundary.ALL`, or
            exactly one (not both/neither) of `previous_end_utc` /
            `current_start_utc` is supplied. Callers use
            `build_envelope_safe()` to convert this into the D5.6
            `unavailable` stub instead of propagating it.
    """
    if boundary not in SessionBoundary.ALL:
        raise ValueError(f"Invalid boundary {boundary!r}; must be one of {SessionBoundary.ALL}")
    if (previous_end_utc is None) != (current_start_utc is None):
        raise ValueError(
            "previous_end_utc and current_start_utc must both be provided or both omitted "
            "(a partial boundary pair cannot be compared)."
        )

    if now is None:
        now = time_provider.utc_now()

    status_reasons: List[str] = []

    # -- D4: user zone + local wall time -----------------------------------
    if zone_resolution.source == ZoneSource.UNRESOLVED:
        status_reasons.append(EnvelopeStatusReason.ZONE_UNRESOLVED)
        user_zone_iana: Optional[str] = None
        local_wall_time: Optional[Dict] = None
    else:
        user_zone_iana = zone_resolution.iana
        if user_zone_info is not None:
            local_dt = now.astimezone(user_zone_info)
            local_wall_time = {
                "display": local_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "utc_offset": local_dt.strftime("%z"),
            }
        else:
            # Provenance says a zone WAS resolved, but the caller didn't hand
            # us a concrete ZoneInfo to convert into -- degrade rather than
            # silently asserting a local time we cannot actually compute.
            status_reasons.append(EnvelopeStatusReason.ZONE_UNRESOLVED)
            local_wall_time = None

    # -- D3: boundary gap + clock health, D7/D3.2 continuity ----------------
    gap: Optional[Dict] = None
    clock_health = ClockHealth.OK
    if previous_end_utc is not None and current_start_utc is not None:
        health = time_provider.evaluate_clock_health(
            earlier=previous_end_utc, later=current_start_utc, now=now
        )
        clock_health = health.state
        threshold = (
            session_continuation_threshold_minutes
            if session_continuation_threshold_minutes is not None
            else 30
        )
        if health.is_ok and health.gap_seconds is not None:
            gap = {
                "seconds": health.gap_seconds,
                "formatted": _format_gap_seconds(health.gap_seconds),
            }
            if (health.gap_seconds / 60) < threshold:
                continuity_class = ContinuityClass.SAME_STREAK_CONTINUATION
                continuity_reason = "gap under session_continuation_threshold_minutes"
            else:
                continuity_class = ContinuityClass.FRESH_SESSION
                continuity_reason = "gap exceeds session_continuation_threshold_minutes"
        else:
            # D3.2/D7.5: an anomalous clock is NEVER used to compute a
            # trusted gap/continuity -- forced conservative fresh_session
            # label; clock_health (already skew-suspected/rollback-detected)
            # is what distinguishes this from a confirmed-fresh boundary.
            status_reasons.append(EnvelopeStatusReason.CLOCK_ANOMALY)
            continuity_class = ContinuityClass.FRESH_SESSION
            continuity_reason = "clock anomaly forced conservative continuity classification"
    elif ambiguous_boundary_timestamp:
        # v9.12.0 A6 (ADR D8.5, SEC-CLOCKADR-9.12.0-021): the caller withheld
        # both boundary instants specifically because one was gated -- this
        # is NOT the neutral "no previous session boundary available" case
        # below (which never even had data to distrust). Surfaced as its own
        # distinct status reason (never conflated with D3.2's CLOCK_ANOMALY,
        # which describes a different failure class -- see
        # EnvelopeStatusReason's docstring) so `envelope_status_reasons`
        # tells a consumer WHY continuity could not be classified.
        status_reasons.append(EnvelopeStatusReason.AMBIGUOUS_TIMESTAMP)
        continuity_class = ContinuityClass.FRESH_SESSION
        continuity_reason = (
            "a boundary timestamp's provenance is unconfirmed under ADR D8.5 "
            "-- excluded from continuity classification, never silently "
            "trusted"
        )
    else:
        continuity_class = ContinuityClass.FRESH_SESSION
        continuity_reason = "no previous session boundary available for comparison"

    # -- D7: work-streak snapshot --------------------------------------------
    work_streak = work_streak or {}
    work_streak_out = {
        "accumulated_protected_work_minutes": work_streak.get("accumulated_protected_work_minutes", 0),
        "streak_start_utc": work_streak.get("streak_start_utc"),
        "high_risk_block_active": bool(work_streak.get("high_risk_block_active")),
    }

    # -- D6.4: late-night, transparency fields -------------------------------
    late_night_out = {
        "is_late_night": bool(is_late_night),
        "threshold_local": f"{late_night_hour if late_night_hour is not None else 22:02d}:00",
        "threshold_end_local": f"{late_night_end_hour if late_night_end_hour is not None else 6:02d}:00",
    }

    # -- D6.5: alert reasons --------------------------------------------------
    alert_out = {
        "alert_needed": bool(alert_needed),
        "reasons": list(alert_reasons or []),
    }

    envelope_status = EnvelopeStatus.DEGRADED if status_reasons else EnvelopeStatus.COMPLETE

    return {
        "envelope_schema": ENVELOPE_SCHEMA_VERSION,
        "envelope_status": envelope_status,
        "envelope_status_reasons": status_reasons,
        "emitted_at_utc": now.isoformat(),
        "session": {
            "session_id": session_id,
            "session_id_is_opaque": True,
            "boundary": boundary,
        },
        "authoritative_instant_utc": now.isoformat(),
        "user_zone": {"iana": user_zone_iana, "source": zone_resolution.source},
        "local_wall_time": local_wall_time,
        "session_boundaries": {
            "previous_end_utc": previous_end_utc.isoformat() if previous_end_utc else None,
            "current_start_utc": current_start_utc.isoformat() if current_start_utc else None,
        },
        "gap": gap,
        "continuity": {"class": continuity_class, "reason": continuity_reason},
        "work_streak": work_streak_out,
        "late_night": late_night_out,
        "alert": alert_out,
        "clock_health": clock_health,
    }


def build_envelope_safe(*, time_provider: Optional[TimeProvider] = None, **kwargs) -> Dict:
    """`build_envelope()` wrapped in the D5.6 `unavailable`-on-failure
    contract. This is the function session_monitor.py actually calls at
    every emission site -- a caller bug or malformed input degrades the
    ENVELOPE, never the session-lifecycle command that requested it.

    On any exception, returns the D5.6 minimal stub: only `envelope_schema`,
    `envelope_status: "unavailable"`, `envelope_status_reasons:
    ["generation_error"]`, and a best-effort `emitted_at_utc` (every other
    field omitted rather than fabricated).
    """
    try:
        return build_envelope(time_provider=time_provider, **kwargs)
    except Exception:
        emitted_at_utc = None
        try:
            now = kwargs.get("now")
            if now is not None:
                emitted_at_utc = now.isoformat()
            elif time_provider is not None:
                emitted_at_utc = time_provider.utc_now().isoformat()
        except Exception:
            emitted_at_utc = None
        return {
            "envelope_schema": ENVELOPE_SCHEMA_VERSION,
            "envelope_status": EnvelopeStatus.UNAVAILABLE,
            "envelope_status_reasons": [EnvelopeStatusReason.GENERATION_ERROR],
            "emitted_at_utc": emitted_at_utc,
        }
