#!/usr/bin/env python3
"""FEAT-IDGOV-001 engine — mint/check/list/transition/validate over the JSONL ledger.
Writer identity is DERIVED from the per-wrapper signature (never caller-supplied).
mint/transition do read->decide->append atomically under one reentrant registry.Lock."""
import datetime
from idgov import grammar, registry, identity

STATES = frozenset({"open", "reserved", "remediation-required", "re-review", "approved",
                    "accepted-p3", "deferred", "superseded"})
ALLOWED = {
    "open": {"remediation-required", "re-review", "approved", "accepted-p3", "deferred", "superseded"},
    "remediation-required": {"re-review", "deferred", "superseded"},
    "re-review": {"remediation-required", "approved", "accepted-p3", "deferred", "superseded"},
    "reserved": {"open", "deferred"},
    "approved": {"re-review", "superseded"},
    "accepted-p3": {"re-review", "superseded"},
    "deferred": {"re-review", "superseded"},
    "superseded": set(),
}

def is_legal_transition(frm, to) -> bool:
    return to in ALLOWED.get(frm, set())

AUTHORITY = {
    "SEC": {"megumi"}, "CODE": {"megumi"},
    "BUG": {"yuuji", "sukuna"},
    "FEAT": {"sukuna"}, "IMPL": {"sukuna", "yuuji"},
    "ISS": {"sukuna", "gojo"},
    # MF = "Megumi Finding" (Gojo decision, Phase C review P2-1); TEST = test-scoped
    "TEST": {"megumi", "yuuji"}, "MF": {"megumi"},
}

def is_authorized(writer, family) -> bool:
    return writer in AUTHORITY.get(family, set())

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def mint(reg_path, family, subsystem, title, *, version=None, tag=None, reserved=False,
         reported_by=None, signature, nonce, protocol_version, origin, **audit) -> str:
    if family not in grammar.FAMILIES:
        raise ValueError(f"unknown family {family!r}")
    who = identity.derive_writer(signature, nonce)
    if who is None:
        raise PermissionError("unattested writer (no matching per-wrapper token)")
    attested_writer, writer_token_id = who
    if not is_authorized(attested_writer, family):
        raise PermissionError(f"{attested_writer} not authorized for family {family}")
    with registry.Lock(reg_path):
        events = registry.read_events(reg_path)
        seq = registry.max_seq(events, (family, subsystem, version, tag)) + 1
        new_id = grammar.format_id(family, subsystem, seq, version=version, tag=tag)
        if new_id in registry.all_ids(events):
            raise ValueError(f"collision: {new_id} already exists")
        ev = {
            "schema": registry.SCHEMA_VERSION, "event": "assign", "id": new_id, "rev": 1,
            "family": family, "subsystem": subsystem, "version": version, "tag": tag, "seq": seq,
            "attested_writer": attested_writer, "writer_token_id": writer_token_id,
            "reported_by": reported_by, "assigned_at": _now(),
            "protocol_version": protocol_version, "origin": origin, "title": title,
            "state": "reserved" if reserved else "open", "prev_state": None,
            "cwe": audit.get("cwe"), "owasp": audit.get("owasp"), "location": audit.get("location"),
            "supersedes": None, "superseded_by": None, "review_ref": audit.get("review_ref"),
            "legacy": False, "legacy_id": None, "collision_group": None,
        }
        registry.append(reg_path, ev)
    return new_id

def check(reg_path, id_):
    return registry.project_latest(registry.read_events(reg_path)).get(id_)

def list_ids(reg_path, *, family=None, subsystem=None, state=None, origin=None):
    rows = list(registry.project_latest(registry.read_events(reg_path)).values())
    def keep(r):
        return ((family is None or r.get("family") == family)
                and (subsystem is None or r.get("subsystem") == subsystem)
                and (state is None or r.get("state") == state)
                and (origin is None or r.get("origin") == origin))
    return sorted((r for r in rows if keep(r)), key=lambda r: r["id"])

def transition(reg_path, id_, new_state, *, signature, nonce, note=None) -> None:
    if new_state not in STATES:
        raise ValueError(f"unknown state {new_state!r}")
    who = identity.derive_writer(signature, nonce)
    if who is None:
        raise PermissionError("unattested writer")
    attested_writer, writer_token_id = who
    with registry.Lock(reg_path):
        events = registry.read_events(reg_path)
        latest = registry.project_latest(events).get(id_)
        if latest is None:
            raise ValueError(f"unknown id {id_}")
        family = latest.get("family")
        if family is None:
            raise ValueError(f"{id_}: cannot determine family (record missing 'family')")
        if not is_authorized(attested_writer, family):
            raise PermissionError(f"{attested_writer} not authorized for family {family}")
        cur_state = latest.get("state")
        if not is_legal_transition(cur_state, new_state):
            raise ValueError(f"illegal transition {cur_state} -> {new_state} for {id_}")
        ev = {"schema": registry.SCHEMA_VERSION, "event": "transition", "id": id_,
              "rev": int(latest.get("rev", 0)) + 1, "attested_writer": attested_writer,
              "writer_token_id": writer_token_id, "state": new_state, "prev_state": cur_state,
              "assigned_at": _now(), "note": note}
        registry.append(reg_path, ev)

def validate(reg_path) -> list:
    events = registry.read_events(reg_path)
    violations = []
    seen_assign = {}          # id -> True (first assign)
    seq_by_key = {}           # counter_key -> max seq seen (in file order)
    prior_rev = {}            # id -> last-seen rev (0 = none yet)
    running_state = {}        # id -> RECONSTRUCTED current state (not self-reported prev_state)
    family_of = {}            # id -> family (recorded at assign; transitions never carry family)
    for i, ev in enumerate(events, 1):
        eid = ev.get("id")
        etype = ev.get("event")
        if not eid:
            violations.append(f"line {i}: missing id")
            continue
        # rev continuity: each event's rev must equal prior+1 (start 0).
        # A duplicate rev (no advance) OR a gap (skips ahead) both fail this check.
        rev = ev.get("rev")
        expected_rev = prior_rev.get(eid, 0) + 1
        if rev != expected_rev:
            violations.append(f"line {i}: {eid} rev {rev} != expected {expected_rev}")
        prior_rev[eid] = rev
        if etype == "assign":
            # Phase F0/F-remediation: legacy=True rows are non-destructive backfill
            # annotations of historical id reuse (§6), NOT live agent mints. They
            # deliberately carry a non-citable id and no agent authority -- but
            # (Megumi Phase F re-review, SEC-IDGOV-F-001/F-002 P0/P1, CWE-863) this
            # must be a BOUNDED, positively-checked substitute for the ordinary
            # grammar/authority checks, never an unconditional skip: an unbounded
            # exemption let a hand-forged {legacy:true, id:"SEC-CORTEX-099", ...}
            # row carry a clean, well-formed, CITABLE id and an arbitrary
            # attested_writer, defeating mint-before-cite entirely. Structural
            # integrity -- unique id (duplicate-assign, just below) and
            # rev-continuity (checked earlier, for ALL events) -- still applies to
            # legacy rows unconditionally, as before.
            # CRITICAL (CodeRabbit PR#112 finding 11, CWE-863): the id string
            # itself is the ONLY tamper-evident carrier of family/subsystem/
            # version/tag/seq once a row is appended -- the sibling fields
            # (`family`, etc.) are just self-reported JSON and were
            # previously trusted as-is for the writer-authority check below.
            # A row with id "SEC-XX-001" but family:"BUG" + attested_writer:
            # "yuuji" (BUG-authorized, NOT SEC-authorized) passed validate()
            # cleanly: `is_authorized(writer, family)` consulted the
            # SELF-REPORTED family ("BUG"), never the id-DERIVED one ("SEC").
            # Fix: for a non-legacy, grammar-wellformed id, parse the id and
            # require every derivable field to match the row's self-reported
            # value (hard violation on any mismatch); then bind the
            # authority check to the id-DERIVED family so authority can never
            # be satisfied by a merely-consistent-with-itself but
            # id-mismatched pair. (legacy rows are unaffected: they're
            # already bound to a non-citable LEGACY id shape + the single
            # sentinel writer by the F-001/F-002 checks above/below.)
            is_legacy = bool(ev.get("legacy"))
            id_derived_family = None
            if is_legacy:
                # SEC-IDGOV-F-001 (P0): the id MUST match the canonical
                # backfill.to_legacy_row() shape AND MUST NOT be grammar-wellformed
                # -- structurally guarantees a legacy row can never carry a clean,
                # citable id.
                if not (grammar.is_legacy_id(eid) and not grammar.is_wellformed(eid)):
                    violations.append(
                        f"line {i}: legacy row {eid!r} must have a canonical "
                        f"non-citable LEGACY id"
                    )
            else:
                if not grammar.is_wellformed(eid):
                    violations.append(f"line {i}: malformed id {eid!r} (grammar violation)")
                else:
                    # id<->field binding (finding 11): parse is safe here --
                    # is_wellformed() already confirmed ISSUE_ID_RE matches,
                    # and parse_id() uses the exact same production.
                    parsed = grammar.parse_id(eid)
                    id_derived_family = parsed["family"]
                    for f in ("family", "subsystem", "version", "tag", "seq"):
                        if ev.get(f) != parsed[f]:
                            violations.append(
                                f"line {i}: {eid} self-reported {f}={ev.get(f)!r} does not "
                                f"match id-derived {f}={parsed[f]!r}"
                            )
            if eid in seen_assign:
                violations.append(f"line {i}: duplicate assign for {eid}")
            seen_assign[eid] = True
            # monotonic seq per counter key (skip legacy rows -- they never carry
            # a seq; unaffected by the F-001/F-002 hardening above)
            if not is_legacy:
                key = (ev.get("family"), ev.get("subsystem"), ev.get("version"), ev.get("tag"))
                expected = seq_by_key.get(key, 0) + 1
                if ev.get("seq") != expected:
                    violations.append(f"line {i}: {eid} seq {ev.get('seq')} != expected {expected} for {key}")
                seq_by_key[key] = ev.get("seq")
            # §4.1 writer-authority check. Bound to the id-DERIVED family
            # (id_derived_family), not the self-reported ev["family"] --
            # finding 11: authority must be structurally anchored to the id
            # string itself, never to a merely-self-consistent JSON field
            # that could disagree with it (the mismatch is ALSO flagged
            # above, but authority additionally never trusts the disagreeing
            # self-reported value even if that check were somehow bypassed).
            writer = ev.get("attested_writer")
            family = id_derived_family if id_derived_family is not None else ev.get("family")
            if is_legacy:
                # SEC-IDGOV-F-002 (P1): legacy attested_writer MUST equal the
                # single-source sentinel, not an arbitrary unauthenticated value.
                if writer != registry.LEGACY_ATTESTED_WRITER:
                    violations.append(
                        f"line {i}: legacy row {eid} attested_writer must be "
                        f"{registry.LEGACY_ATTESTED_WRITER!r}"
                    )
            else:
                if not is_authorized(writer, family):
                    violations.append(f"line {i}: {writer!r} not authorized for family {family!r} ({eid})")
            # SEC-IDGOV-F-003 (P1): the initial assign state (legacy or not) must
            # be a state mint() can actually produce -- never a forged initial
            # state like "approved" that skips the transition-legality graph.
            state = ev.get("state")
            if state not in ("open", "reserved"):
                violations.append(f"line {i}: {eid} illegal initial assign state {state!r}")
            running_state[eid] = ev.get("state")
            # family_of feeds the `transition` branch's authority check below
            # -- must be the id-DERIVED family too, for the same reason.
            family_of[eid] = id_derived_family if id_derived_family is not None else ev.get("family")
        elif etype == "transition":
            if eid not in running_state:
                violations.append(f"line {i}: transition before assign for {eid}")
            else:
                frm, to = running_state[eid], ev.get("state")
                if not is_legal_transition(frm, to):
                    violations.append(f"line {i}: illegal transition {frm} -> {to} for {eid}")
                else:
                    running_state[eid] = to
                writer = ev.get("attested_writer")
                fam = family_of.get(eid)
                if not is_authorized(writer, fam):
                    violations.append(f"line {i}: {writer!r} not authorized for family {fam!r} ({eid})")
        else:
            violations.append(f"line {i}: unknown event type {etype!r}")
    return violations
