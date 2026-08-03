#!/usr/bin/env python3
"""FEAT-IDGOV-001 engine — mint/check/list/transition/validate over the JSONL ledger.
Writer identity is DERIVED from the per-wrapper signature (never caller-supplied).
mint/transition do read->decide->append atomically under one reentrant registry.Lock."""
import datetime
import sys
from pathlib import Path
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
    # FEAT-IDGOV-003 (v9.11.0 Increment 4, USER decision D1 2026-07-28 22:34
    # UTC, domain.record.md session_20260728_015655 "Approved for all"):
    # LL = "Lessons Learned" (Gojo/Mission Control's observational-output
    # domain -- Trigger 19 reports, session intelligence); SF = "Security
    # Framework" (Megumi's security-framework domain). Both writers already
    # hold provisioned per-wrapper tokens from their existing families (Gojo:
    # ISS; Megumi: SEC/CODE/MF/TEST) -- no new key material was minted for
    # this adoption. Existing wrappers (residentid-gojo.{sh,ps1} for LL,
    # secid.{sh,ps1} for SF) require no code change: they stamp writer
    # identity only and never pre-filter families -- this AUTHORITY table is
    # the single source of truth they defer to.
    "LL": {"gojo"}, "SF": {"megumi"},
}

def is_authorized(writer, family) -> bool:
    return writer in AUTHORITY.get(family, set())

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# D2 (v9.10.1 Block D): retry budget for registry.ConflictError (Block C's
# _validate_fresh_before_write() freshness check). 3 TOTAL attempts (1 initial
# + 2 retries), each against a freshly re-read ledger.
_MAX_APPEND_ATTEMPTS = 3

# FEAT-IDGOV-002 (v9.11.0 WP5 Item 5): pre-mint corpus-collision advisory.
# mint()'s ledger-uniqueness check (registry.all_ids(), below) is blind to a
# pre-governance BARE-TEXT meaning of the same id string already sitting in
# prose/code corpus (e.g. a hand-written "SEC-013" mention in dev-notes.md
# that was never actually minted). A fresh per-subsystem -001 can silently
# collide with that established unrelated meaning, creating an ambiguous
# citation once the id IS minted. This check is ADVISORY ONLY: the ledger is
# the sole authority for whether an id is free, so a corpus hit never blocks
# or fails the mint -- it prints a loud stderr warning naming file:line so
# the writer can catch and disambiguate before the id propagates further.
#
# Bounded, non-recursive file set (kept fast; NOT a repo-wide scan): the two
# guard-enforced protected records, CHANGELOG.md, and every *.md directly
# under audits/ (Toji's report output -- flat directory, no need to recurse).
_CORPUS_COLLISION_RELATIVE_FILES = (
    ".protocol-state/dev-notes.md",
    ".protocol-state/security-review.md",
    "CHANGELOG.md",
)
_CORPUS_COLLISION_GLOB_DIRS = ("audits",)


def _corpus_collision_hits(new_id: str, repo_root) -> list:
    """Return a list of 'relative/path:lineno' strings where `new_id` already
    appears verbatim as a substring in the bounded prose corpus under
    `repo_root`. Best-effort / fail-soft: a missing file, an unreadable file,
    or an unresolvable repo_root all simply yield no hits -- this is an
    advisory, never a gate, and must never raise or block a mint."""
    hits: list = []
    try:
        root = Path(repo_root).resolve()
    except (OSError, RuntimeError, TypeError):
        return hits

    paths = [root / rel for rel in _CORPUS_COLLISION_RELATIVE_FILES]
    for d in _CORPUS_COLLISION_GLOB_DIRS:
        try:
            paths.extend(sorted((root / d).glob("*.md")))
        except OSError:
            pass

    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if new_id in line:
                try:
                    rel = path.relative_to(root)
                except ValueError:
                    rel = path
                hits.append(f"{rel.as_posix()}:{lineno}")
    return hits


def _warn_corpus_collision(new_id: str, repo_root) -> None:
    """Fail-soft wrapper: any unexpected exception inside the collision scan
    itself must never abort a mint -- the ledger check already decided the
    id is free; this is purely advisory noise reduction, not a safety gate."""
    try:
        hits = _corpus_collision_hits(new_id, repo_root)
    except Exception:
        return
    if not hits:
        return
    print(
        f"[idgov] WARNING (FEAT-IDGOV-002): candidate id {new_id!r} is free in "
        f"the registry ledger but already appears verbatim in the prose/code "
        f"corpus at: {', '.join(hits)}. This may be a pre-governance bare-text "
        "mention unrelated to this mint, or a genuine ambiguous citation -- "
        "minting proceeds (advisory only); verify the existing occurrence(s) "
        "before relying on this id being unambiguous.",
        file=sys.stderr,
    )


def mint(reg_path, family, subsystem, title, *, version=None, tag=None, reserved=False,
         reported_by=None, signature, nonce, protocol_version, origin,
         repo_root=None, **audit) -> str:
    if family not in grammar.FAMILIES:
        raise ValueError(f"unknown family {family!r}")
    who = identity.derive_writer(signature, nonce)
    if who is None:
        raise PermissionError("unattested writer (no matching per-wrapper token)")
    attested_writer, writer_token_id = who
    if not is_authorized(attested_writer, family):
        raise PermissionError(f"{attested_writer} not authorized for family {family}")
    # FEAT-IDGOV-002: repo_root for the corpus-collision advisory. Callers
    # (e.g. scripts/issue_id.py) should pass it explicitly for correctness;
    # when omitted, best-effort derive from reg_path's grandparent (mirrors
    # the canonical <repo_root>/.protocol-state/issue-registry.jsonl layout).
    # Wrong or unresolvable in a non-canonical layout simply yields zero
    # corpus hits (fail-soft) -- never affects minting.
    _collision_repo_root = repo_root if repo_root is not None else Path(reg_path).parent.parent
    # D2: authority is checked once above -- it depends only on (attested_writer,
    # family), never on ledger contents, so it needs no re-check across retries.
    # seq/new_id DO depend on ledger state and must be recomputed from a FRESH
    # read on every attempt (that is the whole point of retrying).
    last_exc: "registry.ConflictError | None" = None
    for _attempt in range(1, _MAX_APPEND_ATTEMPTS + 1):
        with registry.Lock(reg_path):
            events = registry.read_events(reg_path)
            # BUG-IDGOVSEQ-001 (P2): max_seq() is OCCUPANCY-aware -- it counts
            # governed rows UNION parseable backfilled `legacy_id` occupancy for
            # this counter key. Before that, backfilled rows (subsystem/seq =
            # null) were invisible to the counter while all_ids() below DID know
            # their legacy_id, so any subsystem whose -001 existed only as a
            # legacy row derived seq 1, collided, and raised here -- outside the
            # ConflictError retry loop, so no retry could ever clear it. The
            # collision check below is deliberately RETAINED as the backstop that
            # proves this derivation is right; with the fix it must not fire for
            # legacy-occupied keys. See registry.max_seq()/legacy_seq_floors()
            # for the MAX-OCCUPIED (not first-free) design choice.
            seq = registry.max_seq(events, (family, subsystem, version, tag)) + 1
            new_id = grammar.format_id(family, subsystem, seq, version=version, tag=tag)
            if new_id in registry.all_ids(events):
                raise ValueError(f"collision: {new_id} already exists")
            # FEAT-IDGOV-002: advisory only -- runs after the ledger has
            # confirmed new_id is free, never blocks/raises.
            _warn_corpus_collision(new_id, _collision_repo_root)
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
            try:
                registry.append(reg_path, ev)
                return new_id
            except registry.ConflictError as exc:
                last_exc = exc
                # P2-a (Megumi Tier-3 bundle review, v9.10.1): classify by
                # TYPE (isinstance), never by parsing the exception message.
                # The prior `"already assigned" in str(exc)` string-match was
                # brittle -- any rewording of registry.py's message text,
                # even a purely cosmetic one, would have silently
                # misclassified a genuine duplicate-id conflict as
                # retryable. registry.DuplicateIdConflictError is a
                # dedicated ConflictError subclass raised ONLY for this
                # exact case; a reworded message on that same exception type
                # still classifies correctly.
                if isinstance(exc, registry.DuplicateIdConflictError):
                    # Duplicate-id conflict: another writer landed the EXACT id
                    # string we just tried to assign. Treated as a distinct,
                    # NON-retryable failure mode -- fail fast with a clearly
                    # distinguishable message instead of burning the retry
                    # budget on a case the design ruling says cannot be
                    # resolved by retrying.
                    raise RuntimeError(
                        f"mint conflict (duplicate-id): {new_id} was concurrently "
                        f"assigned by another writer; this cannot be resolved by "
                        f"retrying -- original conflict: {exc}"
                    ) from exc
                # Stale-seq conflict: another writer minted in this counter key
                # concurrently. Retryable -- loop back and recompute seq/new_id
                # from a fresh read on the next attempt.
                continue
    raise RuntimeError(
        f"mint failed after {_MAX_APPEND_ATTEMPTS} attempts due to repeated concurrent "
        f"writer conflicts for {family}/{subsystem} (last conflict: {last_exc})"
    ) from last_exc

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
    # D2: unlike mint()'s authority check (invariant across retries), transition's
    # authority AND legality checks both depend on the id's CURRENT ledger state
    # (family/cur_state from `latest`) -- both must be re-run against a fresh read
    # on every attempt, never skipped/reused from a stale prior attempt.
    last_exc: "registry.ConflictError | None" = None
    for _attempt in range(1, _MAX_APPEND_ATTEMPTS + 1):
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
            try:
                registry.append(reg_path, ev)
                return
            except registry.ConflictError as exc:
                last_exc = exc
                # append()'s freshness check has no "duplicate assign" case for
                # `transition` events (only stale-rev) -- always retryable: loop
                # back and re-derive rev + re-run authority/legality above
                # against the fresh `latest` on the next attempt.
                continue
    raise RuntimeError(
        f"transition failed after {_MAX_APPEND_ATTEMPTS} attempts due to repeated "
        f"concurrent writer conflicts for {id_} (last conflict: {last_exc})"
    ) from last_exc

def validate(reg_path) -> list:
    events = registry.read_events(reg_path)
    violations = []
    seen_assign = {}          # id -> True (first assign)
    seq_by_key = {}           # counter_key -> max seq seen (in file order)
    prior_rev = {}            # id -> last-seen rev (0 = none yet)
    running_state = {}        # id -> RECONSTRUCTED current state (not self-reported prev_state)
    family_of = {}            # id -> family (recorded at assign; transitions never carry family)
    # BUG-IDGOVSEQ-001: computed ONCE (not per row) -- a per-row call would make
    # this validator O(rows^2) with a regex parse per pair over a 1,300+ row ledger.
    legacy_floors = registry.legacy_seq_floors(events)
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
                # BUG-IDGOVSEQ-001 (P2): this check HAD to learn about legacy
                # occupancy too. Once mint() derives its seq clear of backfilled
                # `legacy_id` occupancy (registry.max_seq()), the very first
                # governed row in a legacy-occupied key legitimately starts ABOVE
                # 1 -- e.g. SEC-CORTEX-026. Left as-is, this check would have
                # flagged that row and made the ledger INVALID, and the
                # pre-commit/CI gate (scripts/check_issue_ids.py, stage E2) runs
                # engine.validate() over the candidate registry, so the fix would
                # have traded an un-mintable subsystem for an un-committable one.
                #
                # The accepted set is EXACTLY TWO values -- the ordinary next
                # governed value, OR the one-time jump clear of pre-governance
                # occupancy. Deliberately NOT relaxed to "any strictly greater
                # value": that would silently permit arbitrary seq skips forever
                # (see test_validate_rejects_an_arbitrary_seq_jump_beyond_legacy_floor).
                #
                # Why an ADDITIONAL accepted value rather than a hard floor
                # (max(governed, legacy) + 1): 78 governed rows already in the
                # canonical ledger were minted into keys legacy occupancy also
                # claims (SEC-GUARD-001..007 alongside legacy SEC-GUARD-001..007
                # etc.) -- all written before the SEC-IDGOV-001 all_ids union
                # existed, and all preceded in file order by the entire 1,229-row
                # backfill block. A hard floor would retroactively flag every one
                # of them; ids are never retro-renamed, so the rule must accept
                # the history it already has. Guarded by
                # test_validate_still_clean_over_live_registry.
                legacy_next = legacy_floors.get(key, 0) + 1
                seq_val = ev.get("seq")
                if seq_val != expected and seq_val != legacy_next:
                    violations.append(
                        f"line {i}: {eid} seq {seq_val} != expected {expected}"
                        + (f" (or {legacy_next}, the next value clear of pre-governance "
                           f"legacy occupancy)" if legacy_next > 1 else "")
                        + f" for {key}"
                    )
                # Only a genuine integer may advance the running counter. A
                # non-int seq (corrupt/hand-written row -- already reported just
                # above, and by the id<->field binding check) previously poisoned
                # seq_by_key, so the NEXT row in the same key raised TypeError on
                # `None + 1` and CRASHED validate() -- taking the gate down with
                # an unhandled traceback instead of reporting the violation.
                if isinstance(seq_val, int) and not isinstance(seq_val, bool):
                    seq_by_key[key] = seq_val
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
