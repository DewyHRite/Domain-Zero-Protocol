<!-- [CORE FILE] - Domain Zero Protocol v9.12.1 -->
# Domain Zero Protocol - Version Information

**Version:** 9.12.1
**Release Date:** 2026-08-08
**Release Type:** PATCH Release (Release-gate self-enforcement — a new fail-closed pre-release/
pre-publish gate closing an 8-release-long disclosed SUKUNA-REPORT.md accumulation-policy gap,
stamp-linter alt-banner currency tightening, a distro-context secret-scanner false-alarm fix, a
platform-idiom fold-in, and first consumer delivery of `BUG-CORTEXTRIGGER-9.12.0-001`)

---

## Release Summary — v9.12.1 (PATCH)

v9.12.1 closes the disclosed enforcement gap in `protocol/SUKUNA-REPORT.md`'s own accumulation
policy (rule 4, added 2026-08-07 while closing `TOJI-DOCS-9.12.0-012`): 8 consecutive releases
(v9.9.5 → v9.12.0) shipped genuine patches with no manifest entry there, because rule 2 ("every
release shipping a patch gets a condensed entry") had no mechanical enforcement. Four independent
items (Batches A/B/C, `session_20260808_114849`), all Yuuji TDD + Megumi Tier-2 `@approved`, zero
P0/P1/P2. Full narrative and finding-by-finding detail: `CHANGELOG.md` `[9.12.1]`.

- **`IMPL-SUKUNAGATE-9.12.1-001`** — new `scripts/distro/check_sukuna_report_currency.py`, wired as
  a `required: true` step into both `pre-release` and `pre-publish` (both event-level
  `fail_soft: false`). Fails closed if `CHANGELOG.md` gains a `#### Fixed`/`#### Security` section
  for the current version with no matching `## vX.Y.Z ...` header in `protocol/SUKUNA-REPORT.md`.
  This release is the gate's own first enforcement target — proven wired via 4 dedicated tests
  reading the real YAML, RED before/GREEN after.
- **`IMPL-STAMPLINT-9.12.1-001`** — stamp-linter Type 15 gained sub-check 15c (`ALT-BANNER-STALE`):
  an alt-banner's named version is now currency-checked, not merely its presence. Found and fixed 11
  real stale banners (9 offline reference guides — content-reviewed, no staleness beyond the stamp —
  plus `protocol/skills/gojo/gojo-tier-validation.md`, which also had a genuine stale cross-reference
  fixed alongside).
- **`BUG-SCANTOP-9.12.1-001`** — `scan_protected_records.py`'s `.dzp-domain/domain.record.md`
  out-of-scope premise is true in the dev repo but false in the separate `distro/` publish worktree,
  which intentionally tracks it as a clean starter materialized byte-identical from its template at
  publish time. Fixed via a new `premise_broken_clean_starter` classification comparing both sides
  via autocrlf-safe `staged_blob()` reads — prints an informational line only on a verified exact
  match; any divergence or unreadable input still escalates exactly as before.
- **`SEC-STATE-9.12.1-001`** — `crypto.py::_harden_windows_acl()` (line 106) and its documented twin
  `attestation.py::_harden_windows_acl()` (line 161) folded from `sys.platform != "win32"` to
  `os.name != "nt"`, closing a live-spoof-immunity gap; companion `identity.py:86` `icacls` call
  gained `creationflags=subprocess.CREATE_NO_WINDOW`. An 11-site residual sweep was reviewed and
  deferred as a future SEC-STATE-class round (equivalence holds throughout; no active risk).
- **First consumer delivery of `BUG-CORTEXTRIGGER-9.12.0-001`** — the Windows detached-Cortex-chain
  console-window suppression fix (committed to this branch's parent after v9.12.0's own release
  cascade had already shipped) reaches consumers for the first time via this patch, plus AST
  fail-closed guard test hardening closing its own review's two non-blocking gaps.

**Test evidence**: independently re-run (Gojo, this cascade) — 1,744 passed / 31 skipped / 0 failed
across `tests/brain/` + `tests/distro/` + all touched suites; stamp linter OK, 0 violations, 531
files; `validate-protocol.py --check` OK, 34/34.

**Sukuna adversarial ratification**: see `.dzp-domain/domain.record.md` for the full trace.

---

## Release Summary — v9.12.0 (MINOR)

v9.12.0 answers the 2026-08-01 Toji session-time-authority audit (9 findings, 2 HIGH, overall risk
HIGH) that v9.11.0 deferred in full, per the USER's Phase-0 "Foundations release" scope ruling
(clock-authority bundle + macOS/Linux portability wave; browser UI deferred to v9.13.0). Full
narrative and finding-by-finding detail: `CHANGELOG.md` `[9.12.0]`.

- **A1 Clock-Authority ADR** — the design contract for the release (`docs/superpowers/specs/
  2026-08-04-clock-authority-adr.md`, revision 6). Yuuji draft → Megumi Tier-2 (1 P1 + 4 P2 + 4 P3,
  2 re-review rounds) → Sukuna ratified WITH CONDITIONS (closed a P1-equivalent legacy-fallback
  second door) → USER sign-off. 13 `SEC-CLOCKADR-9.12.0` rows, all closed `@approved`.
- **A2 TimeProvider + timing-policy primitives** — single clock-authority module + unified
  timing-policy loader; all 34 `datetime.now()` call sites in `session_monitor.py`/
  `project_state_manager.py` migrated, 6 bare-astimezone sites eliminated.
- **A3 work-streak/protection-window model** (gate 2) — rolling-streak authority + genuine two-phase
  break resolution (initiation vs. health-gated clearance), folds in CRPR115 #13.
- **A4 alert reason codes + structured time envelope** (ADR D5, gate 4) — machine-checkable
  `AlertReason` codes (new `CLOCK_ANOMALY`) + a relayed-not-recomputed time envelope for AI callers.
- **A5 versioned time-schema migrator** (gate 5) — `--dry-run`/`--execute`/`--rollback`, 3-bucket
  classification (known-local/ambiguous/synthetic-benchmark), single-source default-timezone
  resolution.
- **Option B ADR D8.5 read-side gating** (`IMPL-TIMESCHEMA-9.12.0-002`) — fail-closed/loud-degrade
  gating against un-migrated naive timestamps.
- **C1 riders** — EOL-normalized deep-verify (payload cross-check) + fcntl platform-poisoning root
  fix in test isolation.
- **Hardening package** (4 findings, all `@approved`) — `SEC-CLOCKADR-9.12.0-026` (adjudication
  bucket-scope refusal, the second `--execute` precondition), `SEC-STATE-9.12.0-001`/`-002`
  (platform-idiom unification, lock-release missing-module survival), `SEC-PAYLOAD-9.12.0-001`
  (binary-guard boundary, scoped/documented residual).
- **B1/B2 POSIX portability** — shared `python3` probe (`scripts/lib/python-probe.sh`) adopted by 6
  shipped `.sh` entry points; `BUG-PORTAB-9.12.0-001` (Windows cp1252 misdiagnosed as YAML syntax
  error) fixed; Toji's `CODE-002` (missing version floor) closed same-day.
- **B3 CI portability-matrix** — 4 required-green report-only lanes (Windows x64, Linux x64/arm64,
  macOS Apple Silicon).
- **B4 Cortex owner-only repair** (`brain repair-perms`) — symlink/junction/reparse-point rejection +
  TOCTOU-safe re-verification; live repair executed (8 repaired, idempotent re-run 8/8 ok);
  `BUG-CORTEXREPAIR-9.12.0-001` regression caught pre-live-run.
- **Live time-schema migration executed 2026-08-06**: 5 known-local + 9 adjudicated rows converted,
  2,000 synthetic rows permanently excluded, `time_schema=1`, D7.6 gating active, 0 TOCTOU
  mismatches on post-hoc verification.
- **Toji 2026-08-06 audit remediation wave** (`audits/2026-08-06-toji-v9-12-0-recent-work.md`, 13
  findings, overall risk HIGH, "not ready") — all 11 P2+P3 findings closed (`SEC-001`, `SEC-002`,
  `SEC-003`, `SEC-004` new, `DESIGN-001`..`-003`, `CODE-001`/`-002`, `IMPL-001`/`-002`, `AI-001`) +
  C2 advisory rider. **These `DESIGN-001`..`-003` IDs are local to this specific audit report and
  are unrelated to the still-OPEN `DESIGN-001` (git-clone cryptographic provenance, 2026-07-27
  supply-chain audit) documented in `SECURITY.md`** — Toji's per-audit finding IDs restart from
  `-001` each report and are not globally unique across audits. Megumi combined Tier-3 `@approved`
  10/10 + focused `@re-review` 4/4. Toji's
  delta re-review (`audits/2026-08-06-toji-v9-12-0-remediation-delta-rereview.md`, 4 findings)
  **lifted its release hold**; 2 LOW/P4 items (`CODE-003`, `IMPL-003`) dispositioned in writing,
  not fixed (append-only-history conflict; out-of-scope spec reconcile).
- **Manifest completeness finding (Sukuna cascade review, fixed same-day)**: 3 new v9.12.0 files
  (`time_envelope.py`, `migrate_time_schema_9_12.py`, `scripts/lib/python-probe.sh`) were absent from
  `publish-manifest.yaml` and outside the completeness gate's 7 scanned scopes — most severely,
  `session_monitor.py`'s unconditional import of `time_envelope` would have broken the MANDATORY
  session-monitoring module on every shipped install. Fixed before publish.
- **Deferred**: B3 remainder (report-only → gating), B4 remainder (keyring defined-failure, macOS
  storage/README — lane-blocked), B5 script parity + C2/C3 riders, C4 idgov backfill (~1,190 rows),
  A6 full cross-platform matrix, A7 full-scope close-out, browser control plane (design-only, spec
  in tree). SGI spec (v9.13.0-prep) committed on this branch as a design artifact only, no v9.12.0
  functional scope.
- **Accepted residual (LOW/P3)**: content-digest fallback narrow false-negative window, benign in
  practice.
- **Sukuna adversarial ratification**: complete 21-commit branch scope (`9e3e87f`..`5ddc303`)
  ratified 2026-08-06 — full trace in `.dzp-domain/domain.record.md`.
- Test evidence: post-remediation full-tree sweep **3,553 passed / 139 skipped / 0 failed**;
  `tests/brain/` 1,252 passed / 25 skipped / 0 failed.
- Sukuna-implemented cascade (System Update Adversary), Gojo-coordinated, USER-approved.

---

## Release Summary — v9.11.0 (MINOR)

v9.11.0 is a release-train MINOR shipping five planned increments (Session Transfer, Trigger 19-R,
prompt-weight reduction, docs content-currency review, Issue-ID Governance LL/SF families) plus a
full 8-commit remediation wave, executed as ONE release per the master plan's "increments first, one
release train at the end" sequencing. Full narrative and finding-by-finding detail: `CHANGELOG.md`
`[9.11.0]`.

- **`FEAT-TRANSFER-9.11.0-001`** — `/session transfer`: fail-closed handoff lifecycle event (9-step
  state machine, event-level `fail_soft: false`, 4 independent guard mechanisms M1-M4 against a
  partial transfer misreporting session state). Megumi Tier-3 remediation loop closed
  `SEC-TRANSFER-9.11.0-001..006` (incl. a P1 caller-identity spoof in `file_integrity.py`'s
  baseline-update authorization). Yuuji TDD (105 new tests).
- **`FEAT-TRIGGER19R-9.11.0-001`** — Trigger 19-R: first public decision-provenance edition, a
  fail-closed 3-detector sanitization gate wired into pre-commit + `dzp-publish`, shipping
  `docs/DESIGN-DECISIONS.md`. Megumi's Task 10 closure resolved `SEC-TRIGGER19R-9.11.0-001..006`;
  whole-branch review verdict CLEAN; backlog wave closed a Unicode/punctuation shingling-bypass class
  and (from Toji's own cross-check re-audit) an NTFS ADS containment gap in an unrelated Type-14
  helper (`SEC-STALEDOCS-9.11.0-004`).
- **Prompt-weight reduction** — `protocol/CLAUDE.md` collapsed 73,279 → 634 bytes (C1b compatibility
  stub); ROE + Tier System relocated to `protocol/skills/gojo/roe-and-tiers.md`; D2-ratified
  enforcement-theatre cuts (~2,000 bytes). Sukuna gate review APPROVED WITH CONDITIONS
  (`audits/2026-07-29-sukuna-inc3-prompt-reduction-review.md`); measured reduction ~45K → ~24.6K
  tokens repo-side always-on load. ~15.5K-token KEEP-as-voice backlog carried to v9.12.x candidate.
- **Docs content-currency review (standing process)** — `ISS-STALEDOCS-9.11.0-001` closed
  (`AI_INSTRUCTIONS.md`/`IMPLEMENTATION_GUIDE.md` body staleness); root cause institutionalized as a
  mandatory two-layer per-release review (`DISTRO_RELEASE_WORKFLOW.md` new §4b): stamp-linter Type
  14/14c (mechanical, manifest-derived ~120+-file scope, 3-round adversarially hardened) + a manual
  judgment sweep, every finding fixed or dispositioned in writing. Closed `ISS-STALEDOCS-9.11.0-002`
  (`REALITY_CHECK.md` full rewrite) and `-003` (`PROTOCOL_QUICKSTART.md` refresh) plus a ~44-citation
  gate-driven sweep.
- **`FEAT-IDGOV-003`** — `LL` (Gojo) and `SF` (Megumi) adopted as first-class Issue-ID Governance
  families, USER decision D1 (2026-07-28). No new key material minted; existing wrappers required no
  code change. **`FEAT-IDGOV-002`** — bounded mint-time corpus-collision advisory (fail-soft).
- **Backlog-wave closure (8 commits)** — all findings from
  `audits/2026-07-30-toji-main-v9-11-0-recent-work.md` + its cross-check re-audit; full WP1-WP6
  registry reconciliation (149 → 0 non-legacy open rows); `SEC-BRANCHISO-001` (branch-isolation
  publish gate, USER-ruled wiring), `SEC-SCANTOP-001` (file-scoped secret-scan allowlist, USER-ruled
  Option B), root `CLAUDE.md` brought under `FEAT-REQ-001` protection (a real bypass gap, same class
  as `BUG-HOOK-SELF-DISARM-001`), `SEC-CR-003` (Cortex lock TTL reap), `SEC-TESTGOV-008` (skip-
  enumeration governance guard), `SEC-AGENTVAL-001`, `SEC-IDGOVLEFT-001`, and repo-wide GitHub
  Actions supply-chain pinning.
- **`BUG-SESSION-005`** (timezone-boundary fix) + **`IMPL-SESSIONMON-001`** (idle-tracking honesty) +
  **`BUG-COORD-9.11.0-001`** (terminal-validator ordering + transfer-contract resync) — all Megumi
  `@approved`.
- **Deferred**: `ISS-TIMEAUTH-9.12.0-001` — the 2026-08-01 Toji session-time-authority audit (9
  findings, 2 HIGH) is deferred **in full** to a v9.12.0 clock-authority bundle per explicit USER
  ruling and the audit's own recommendation; `BUG-SESSION-005` (the family, not the fix above) stays
  open until those gates pass. `ISS-VALIDATION-9.11.0-001` (cosmetic timestamp-suffix doubling,
  backlog).
- **Fixed same-day**: `BUG-TESTGOV-001` (P2, found during Sukuna's own ratification sweep — one
  unenumerated, functionally-dead skip site in `SEC-TESTGOV-008`'s own completeness guard) was
  closed in this release (commit `18d07e8`, dead skip branch removed from
  `tests/test_session_transfer.py`; registry `open` → `approved` at `2026-08-03T21:55:41Z`,
  `attested_writer: yuuji`) — it is NOT an open item.
- **Sukuna adversarial ratification**: complete 45-commit branch scope (`8241d2e`..`8824394`)
  ratified 2026-08-03, zero P0/P1 found across the whole branch — full trace in
  `.dzp-domain/domain.record.md`.
- Test evidence: targeted core-suite sweep at ratification time 505/505 passed; new distro/
  security-gate suites 374/375 passed at that intermediate checkpoint (the 1 known failure was
  `BUG-TESTGOV-001`, closed same-day, above). Final gate re-verification at HEAD `18d07e8`: **full
  suite 3,148 passed / 90 skipped / 0 failed**; stamp linter 0 violations / 509 files;
  validate-protocol 29/29; assert_version 20/20.
- Sukuna-implemented cascade (System Update Adversary), Gojo-coordinated, USER-approved.

---

## Release Summary — v9.10.2 (PATCH)

**Versioning note (Sukuna adversarial ruling)**: this release ships a genuinely new capability
(`FEAT-PAYLOAD-9.10.2-001`) alongside a majority of remediation/closure work. Strict SemVer would
normally call a net-new feature a MINOR bump. The version number was fixed at v9.10.2 PATCH before
this cascade began — the release plan, branch name, and every issue ID minted this session
(`ISS-CLAUDEMD-9.10.2-001`, `SEC-PAYLOAD-9.10.2-001..005`, `FEAT-PAYLOAD-9.10.2-001` itself) already
bake `9.10.2` into their identifiers, and USER approval for "the v9.10.2 release plan" is on record.
Ruling: **PATCH**, dissent recorded — lock the version number before minting IDs on any future
release that might pick up a net-new FEAT-classified subsystem mid-cycle.

v9.10.2 closes all 3 findings from Toji's `audits/2026-07-20-toji-recent-work-audit.md`
(`AI-001` HIGH, `IMPL-001` MEDIUM, `IMPL-002` reconciliation), the `ISS-162` EOF-anchor procedure gap
in `protocol/toji.agent.md`, the v9.10.2 queue items 1-4 (idgov `audits/**` E5 exemption, the
dependency-scanner backup-crawl fix, the crbase §5b workflow doc, and stamp-linter Types 9-12), the
v9.10.2 item-5 carried notes (4 fixes: session-monitor UTC normalization, `dzp.py` dynamic `--help`
epilog, detached-log rotation, `load_registry()` structural guards), the CLAUDE.md changelog-retention
policy (`ISS-CLAUDEMD-9.10.2-001`), and ships the new `FEAT-PAYLOAD-9.10.2-001` release payload
subsystem (`scripts/distro/dzp_payload.py` builder + `scripts/verify-payload.py` consumer-facing
pinned-origin verifier) with its full 5-finding `SEC-PAYLOAD-9.10.2-001..005` remediation loop
(1 P1 CWE-345/CWE-829 forgeable-origin bypass, 2 P2, 2 P3 — all Megumi-reverified `@approved`).

- Megumi reviews this release: item-5 carried notes **@approved** (0 findings, 206/206 passed); Toji
  `AI-001`/`IMPL-001` remediations **@approved** (0 findings each, 1 accepted P3); `b090373`
  stamp-linter reconciliation **@approved** (0 P0/P1/P2, 2 accepted P3); `FEAT-PAYLOAD-9.10.2-001`
  **@remediation-required** (1 P1 + 2 P2 + 2 P3) → re-review **@approved** (228/228 passed).
- CLAUDE.md changelog retention: root `CLAUDE.md`'s duplication (~69 KB / 49% of the file) is now
  bounded — `Major Enhancements` carries only the current release; `Recent Version History` carries a
  hard cap of the 5 most recent releases. Zero information destroyed (full history remains in this
  file and `CHANGELOG.md`).
- Sukuna-implemented (System Update Adversary), Gojo-coordinated, USER-approved.

---

## Release Summary — v9.10.1 (PATCH)

v9.10.1 is a bundled remediation release closing the full 9-item queue deferred from the v9.10.0
Toji release-gate audit hold, plus a same-session Megumi Tier-3 bundle review (1 P1 + 4 P2, all
closed) and its own pre-audit reconciliation.

- **Block A (distro integrity)** — new fail-closed, NO-override `manifest_tracking_offenders()` gate
  in `scripts/distro/dzp_publish_core.py` verifies every manifest-shippable file staged under
  `distro/` is actually `git`-tracked after `git add -A`, closing `BUG-DISTRO-ORCH-TRIO-001`: a
  stale v9.2.0 "DEV-ONLY" ignore block in `scripts/distro/distro.gitignore` had silently caused every
  published `DZP-vX.Y.Z` branch to drop the orchestration trio (`dzp.py`,
  `.protocol-state/script_coordinator.py`, `.protocol-state/script_dependencies.yaml`) even though
  the manifest-text and on-disk staging gates both reported green. USER ruling: the trio now SHIPS
  (fulfills `ISS-084`/`ISS-085`).
- **Block B (idgov polish)** — closes all 4 findings Toji deferred from the v9.10.0 audit:
  `DESIGN-001` (sanctioned `residentid-{sukuna,gojo,yuuji}.{sh,ps1}` resident-mint wrappers for every
  non-Megumi authority family, full manifest/immutable-path/completeness-gate/test-suite coverage),
  the original `IMPL-001` + `AI-001` (new `scripts/check_toji_report_contract.py` mechanizing Toji's
  own report-contract requirements), and a report-only retro-mint exclusion audit trail
  (`audits/2026-07-19-retromint-b1-exclusions.md`).
- **Block C (idgov registry lock hardening)** — `scripts/idgov/registry.py`'s `Lock` gains a fresh
  in-lock re-validation before every append (`_validate_fresh_before_write()` + retryable
  `ConflictError`, closing a two-reaper race window, C1/P2) and a PID-recycle starvation backstop
  (10x-ttl hard age ceiling + human `Lock.force_break()` break-glass, C2/P3); `engine.mint()` gains a
  bounded 3-attempt retry loop with typed `DuplicateIdConflictError` fail-fast classification.
- **Block D (`brain.py` reset UX)** — `BUG-TEST-RESET-HANG-001`'s product-side fix: `brain reset
  --yes`'s preserving-snapshot path now calls `_escrow_passphrase(allow_prompt=False)`
  unconditionally, so it can never block on a `getpass` prompt regardless of TTY detection;
  complements the v9.10.0 test-harness-only fix as the genuine Part 2.
- **`SEC-GUARD-007`** (P1, CWE-345) — closes a stub-marker splice bypass in
  `scripts/check_protected_append_only.py`'s Toji-stub tripwire (a `[TOJI AUDIT LOG]` marker split
  across two no-trailing-newline commits could evade validation with zero warning); fixed via a
  full-staged-content rescan with exact-line HEAD-identity exemption.
- Megumi Tier-3 @approved twice (full bundle, 2 rounds — 1 P1 + 4 P2 → @approved; plus a focused
  standalone verification of the report-contract validator, @approved). Toji's pre-audit
  (`audits/2026-07-19-toji-v9-10-1-bundle-preaudit.md`) independently re-verified all 4 v9.10.0-deferred
  findings RESOLVED and raised 4 new findings against the bundle itself (3 MEDIUM, 1 LOW) — all 4
  closed in this release: a dedicated `security-review.md` entry now records the `SEC-GUARD-007`
  review directly (its own-namespace `SEC-001`); the `BUG-TEST-RESET-HANG-001` two-part attribution
  is reconciled between `domain.record.md` and `brain.py` (its own-namespace `IMPL-002`); and the
  report-contract validator's unrecognized-field-label check is now implemented (its own-namespace
  `IMPL-001`/`CODE-001`). Overall verdict: bundle READY for the release ceremony.
- Test evidence: 198/198 across the targeted remediation suites (0 regressions against the
  pre-session 187/187 baseline), `tests/test_check_toji_report_contract.py` 28/28, full repo sweep
  **2,376 passed / 4 skipped / 0 failed**.
- Sukuna-implemented (System Update Adversary, Gojo-coordinated, USER-approved).

---

## Release Summary — v9.10.0 (MINOR)

v9.10.0 ships the Issue-ID Governance System (FEAT-IDGOV-001) built and adversarially reviewed across
Phases A-H, plus a targeted version-cascade closure (IMPL-001) and a stamp-linter coverage extension
(BUGREPORT-009).

- **FEAT-IDGOV-001** (Issue-ID Governance System) — an all-families append-only JSONL registry
  (`.protocol-state/issue-registry.jsonl`) plus a shared minting/validation engine (`scripts/idgov/`)
  enforced by a fail-closed, full-mediation pre-commit/CI gate (`scripts/check_issue_ids.py`): mint-before-
  cite semantics, hard-block on malformed IDs, documented prose escapes, and an E5 digit-gate against
  accidental term collisions. Ships a mediated Megumi `secid` tool (`protocol/skills/megumi-secid.md`,
  signed-wrapper execution per the Phase D9 Sukuna-adversarial review) and a non-destructive historical
  backfill (`scripts/backfill_issue_registry.py`) that reconciled 1,229 legacy rows into 266 collision
  groups — including the discovery that `SEC-001` alone had been independently reused 76 times across the
  corpus with no registry ever having existed to prevent it. DZP Cortex gains a fail-soft registry-aware
  advisory. The gate is ACTIVE with a sixth, independent break-glass override,
  `DZP_ALLOW_MISSING_ISSUE_ID_GATE`. Yuuji TDD throughout; Megumi Tier-3 @approved every phase — including
  catching and structurally closing a P0 (SEC-IDGOV-F-001, a legacy mint-and-cite bypass in the backfill
  path). Sukuna led an adversarial Phase H pass over the whole subsystem; Toji delivered a full external
  audit 2026-07-18 (`audits/2026-07-18-toji-v9.10.0-idgov-full-audit.md`, 13 findings, remediation
  in-progress and explicitly NOT part of this release's code). Provenance:
  `audits/2026-07-13-sukuna-secid-governance-review.md` (the original Sukuna design self-review that
  first identified SEC-001's 5-meanings collision and staffed this mission).
- **IMPL-001** (version-cascade closure, IMPL-001-tagged in the Toji audit trail) — the un-cascaded
  v9.9.7→v9.9.8 stamp drift flagged as permanently mis-stamping registry rows is closed: every live
  version stamp across the repo (protocol files, docs, agent frontmatter, hooks, `AI_INSTRUCTIONS.md`,
  `dzp.py`, state) is cascaded to v9.10.0 in this release; historical/changelog references are
  deliberately left untouched. A pre-existing linter gap was also surfaced (not fixed in this release,
  report-only): `audits/2026-07-13-sukuna-secid-governance-review.md` carries a live-looking
  `[CORE FILE]` header despite being a historical, append-only audit artifact — `check_version_stamps.py`
  does not yet exclude `audits/**` the way it excludes `dev-notes.md`/`security-review.md`/
  `domain.record.md`, so this one stamp will re-flag as stale on every future cascade until that scope
  gap is closed.
- **BUGREPORT-009** (stamp-linter coverage) — `scripts/distro/check_version_stamps.py` gains a new Type 8
  check scoped tightly to the root `dzp.py` module-docstring line (`Domain Zero Protocol vX.Y.Z`), which
  previously had no linter coverage at all and had already drifted silently once (corrected in v9.9.5).
  TDD-verified: a stale stamp now fails the linter, a current stamp passes.
- Sukuna-implemented (System Update Adversary, Gojo-coordinated, USER-approved); Yuuji TDD for the Type 8
  linter addition; full verification suite green (`assert_version.py`, `check_version_stamps.py`,
  `validate-protocol.py --check`).

---

## Release Summary — v9.9.7 (PATCH)

v9.9.7 delivers the durable fix for the chronic Cortex session-end timeout (BUG-CORTEX-008), superseding
the v9.9.6-era R1 stopgap, plus a maintainer-side dirty-source publish guard that closes a silent-leak
path in `dzp-publish`.

- **BUG-CORTEX-008 R3** (durable fix) CLOSED — root cause was the SYNCHRONOUS full `--level high`
  re-embed + `export --snapshot` landing on top of the session's largest embedding-delta cost, not
  corpus size as R1 assumed. `session-end` now runs `cortex-medium` (`--level medium`, incremental, no
  export, 90s) instead of `cortex-high`, keeping the critical path fast and fail-soft. A new manual event
  `cortex-rebuild-full` (`python dzp.py event cortex-rebuild-full`) carries the full `--level high` + export
  off the critical path for periodic/manual invocation (no daemon — DZP remains no-daemon by design).
  The other 4 `cortex-high` steps (`pre-release`, `pre-publish`, `post-migration`, `post-rotation`) are
  unchanged and remain real gates at R1's 300s timeout. `cortex_trigger.py` unaffected — it already
  supported medium+export. Docs updated: `protocol/skills/session.md` (incl. a `toji-snapshot` event
  pointer, closes SEC-CORTEX-R3-001), `protocol/skills/session-check.md`'s session-end.md counterpart,
  `README.md`, `docs/guides/DZP_CORTEX.md`, `AI_INSTRUCTIONS.md`.
- **BUG-CORTEX-008 R1** (stopgap, folded in) — raised `timeout_seconds` 180→300 on all 5 `cortex-high`
  orchestration steps; the other 4 non-session-end steps keep this 300s timeout under R3.
- **BUG-DISTRO-DIRTY-SOURCE-001** (maintainer tooling) CLOSED — `dzp-publish` staged `distro/` by
  copying the dev source tree from disk, never from git, so a dirty working tree could silently ship
  uncommitted content publicly. Adds a fail-closed `dev_source_dirty_offenders()` guard (`git status
  --porcelain=v1 -z`, scoped to the same manifest-staged paths: `include_*` + `exclude_subpaths` +
  `distro_gitignore_source`) that aborts the publish on any genuinely dirty manifest-shippable path.
  `DZP_ALLOW_DIRTY_SOURCE=1` is a loud, non-silent override for confirmed-clean intentional dirt (rc==1
  only); a git-execution failure (rc==2, git missing/non-repo) hard-fails and is NOT overridable. POSIX +
  PowerShell parity; `docs/guides/DISTRO_RELEASE_WORKFLOW.md` §4a documents it. Closes SEC-DISTRO-DIRTY-001
  (P2, gitignore-source scope gap), -002 (P3, `-z` path parsing), -003 (P3, override-vs-execution-failure
  separation).
- Yuuji TDD throughout (Cortex R3 doc/config regression coverage; 17 dirty-source guard + 125 distro
  suite tests green); Megumi Tier-2/Tier-3 @approved both items; Sukuna-implemented and Gojo-verified.
- **Same-session governance note:** a Sukuna SEC-ID governance self-review was conducted this session
  (`audits/2026-07-13-sukuna-secid-governance-review.md`); its formal issue-tracker remediation is
  scheduled for v9.9.8 and is NOT part of this release's code changes.
- **Not in this release:** the v9.9.5 same-day Toji-audit addendum's CODE-001/SEC-001/BUG-SNAPSHOT-NULLFIELDS-001/MF-1/FEAT-REQ-002 items remain as documented under v9.9.5 below (unchanged carry-forward, already committed).

---

## Release Summary — v9.9.6 (PATCH)

v9.9.6 closes 5 P1 defects found by a Sukuna-led 4-front adversarial bug hunt across the security-gate
engine, the snapshot restore path, the Cortex key-recovery escrow, and the distro publish PII gate —
each with a committed regression test converted directly from its repro. Provenance:
`internal-docs/.../DZP-Sukuna-BugHunt-2026-07-11.md` (Toji-audited Rev 2).

- **BUG-HOOK-SELF-DISARM-001** (P1) CLOSED — the security-gate ENGINE scripts
  (`scan_protected_records.py`, `check_protected_append_only.py`, `validate-protocol.py`,
  `check_branch_record_isolation.py`, `distro/assert_version.py`, `distro/check_version_stamps.py`)
  are now themselves listed in `immutable_paths` — the prior hardening (F6) protected only the hook
  wrapper scripts, leaving the on-disk scanner engines themselves free for an unprivileged commit to
  neuter or `git rm`. The stage-3 append-only guard now FAILS CLOSED when a guard file is missing,
  with a new break-glass `DZP_ALLOW_MISSING_APPEND_GUARD` override (the guard's 4th override, always
  printed loud on use); the `DEFAULT_PATHS` fallback was brought to the same parity. Closes a
  self-disarm path that could have let a secret ship or protected history be silently rewritten.
- **BUG-RESTORE-CHECKSUM-NOOP-001** (P1) CLOSED — `restore-snapshot.py` now ACTUALLY compares the
  snapshot checksum against a recompute of the pre-image (it previously computed the checksum but
  never compared it, always printing a hardcoded "✅ verified" banner regardless of match).
  Verify-before-write ordering is fail-closed; `--force-unverified` remains as an explicit break-glass.
- **BUG-CORTEX-ESCROW-HOLLOW-001** + **-RAISE-002** (P1 ×2) CLOSED —
  `.protocol-state/brain/cortex/memory_export.py`'s key-recovery escrow capture is now re-pointed at
  the REAL content-addressed store (`content_refs ⋈ content WHERE source_type='memory'`); the phantom
  `cortex_memories` table and `cortex_entities.source` column it previously queried do not exist on any
  real `Store` brain, so escrow silently captured 0 memories (or hard-raised) on every genuine
  installation since introduction in v9.9.0. Restore now uses the production upsert path. The masking
  test fixtures that fabricated the phantom table — hiding this defect for 6 releases — were
  de-fabricated onto real `Store`-backed brains so the regression suite can no longer mask a recurrence.
- **BUG-DISTRO-PII-LEAK-001** (P1) CLOSED — the publish `content_audit` PII scan now scans EVERY
  staged file regardless of extension (was extension-gated, silently skipping unlisted types), decodes
  with a known-encoding chain falling back to `latin-1` (UTF-16 content was previously skipped
  entirely rather than scanned), and matches `IGNORECASE`. `_IGNORE_COPY` extended to editor/merge
  junk (`.orig`, `.rej`, `.swp`, `.swo`, `.tmp`, `~`, `.DS_Store`, `Thumbs.db`) so such files can no
  longer accidentally ship to the public distro carrying unaudited owner PII.
- Yuuji TDD throughout; Megumi Tier-3 @approved. New tests: hook self-disarm 14, restore-checksum 14,
  escrow 3 new + 4 de-fabricated suites re-pointed at real `Store` brains, distro PII-leak gate 8.
- **Accepted P3 residuals:** `.protocol-state/attestation.py` not yet added to `immutable_paths`
  (bounded — unattested drift is non-blocking, alert-only); content-audit substring boundary vs
  binary/compressed blobs (moot for this repo — no binary assets ship).
- **Deferred (not in this release):** 6 P2 + ~12 P3 findings from the same bug-hunt report remain open
  for a follow-on patch.

---

## Release Summary — v9.9.5 (PATCH)

v9.9.5 closes a confirmed, downstream-corroborated defect bundle in the DZP Cortex ingest secret-detector
(`BUG-CORTEX-INGEST-SECRET-FP-001`), reconciles a latent detection-weakening inconsistency between
the two independent secret-detectors, and closes a publish-manifest gap that had silently omitted
the SEC-001 protected-records secret scanner from every published `DZP-v9.9.4` distro branch.

- **Cortex ingest remediation** (`cortex/ingest.py`, ported byte-identical from a Megumi-@approved
  downstream fix) — **SEC-DZPUP-9.9.4-010** (heuristic drift) CLOSED: `_is_placeholder_value`
  gains a BOUNDED closed-vocabulary exact-match type-annotation recognizer (19 TS/JSON-schema
  tokens, fullmatch only) instead of widening the substring-matched `_PLACEHOLDER_WORDS` (which
  would have masked any value merely containing a type word, e.g. `password: correcthorse_string_x9`
  — the exact bypass class Megumi rejected). **SEC-DZPUP-9.9.4-012** (all-or-nothing drop) CLOSED:
  `chunk_file()`'s secret gate is now PER-CHUNK, not whole-file — a single secret-shaped chunk is
  redacted; sibling chunks in the same document survive (was `if contains_secret(text): return []`,
  a confirmed regression of a 2026-06-15 fix silently reverted by an intervening resync).
  **SEC-DZPUP-9.9.4-011** (silent failure) CLOSED: `index()` returns `files_dropped_secret` /
  `chunks_dropped_secret` counters and `chunk_file()` emits an unconditional
  `[cortex:ingest] REDACT ...` stderr line per dropped chunk. **SEC-DZPUP-9.9.4-013** CLOSED:
  restored the SEC-CORTEX-006 injection-pattern set from a silently-reverted 3-pattern list back to
  the full 6.
- **Scanner -005/-010 reconciliation** (`scripts/scan_protected_records.py`) — the scanner had
  independently "fixed" the identical type-annotation false-positive class via the UNSAFE
  substring-word approach (SEC-DZPUP-9.9.4-005). Moved onto the same closed-vocab exact-match
  recognizer as `cortex/ingest.py`, and additionally ported the scanner's own -006 (semver
  recognizer), -007 (length-capped ellipsis recognizer), and -008 (widened trailing-punctuation
  strip) value-side hardening, none of which had previously reached canonical. `SECRET_FORMAT_PATTERNS`
  and the keyword regex are untouched in both files — value-side fixes only. A new structural test
  (`tests/test_type_annotation_vocab_parity.py`) guards the two detectors' closed-vocab token sets
  against future drift.
- **Publish-manifest gap CLOSED** — `scripts/scan_protected_records.py`,
  `scripts/check_branch_record_isolation.py`, and `.github/secret_scanning.yml` existed in the
  v9.9.4 canonical working tree and were referenced by the v9.9.4 changelog, but were never added
  to `scripts/distro/publish-manifest.yaml` — so every published `DZP-v9.9.4` branch shipped
  WITHOUT the SEC-001 protected-records secret scanner. Independently confirmed by two downstream
  install issue reports (one covering `ISS-DZPUP-9.9.4-003`, the other from a second, independent
  downstream install). All three files added to the manifest.
- **Pre-commit hook hardening** — `scripts/git-hooks/pre-commit` (POSIX) gained the missing-scanner
  `else` warning branch that `scripts/git-hooks/pre-commit.ps1` already had; a missing scanner
  previously silently no-op'd the entire secret-scan gate with zero output.
- **`dzp.py`** — stale "Domain Zero Protocol v9.4.0" banner (2 stamps) corrected to v9.9.5.
- Yuuji TDD (41 new Cortex regression/observability/adversarial-bypass tests + 2 cross-detector
  vocab-parity tests, all green; 20 pre-existing scanner tests + 225 pre-existing brain/cortex tests
  unaffected). Megumi Tier-3 security-review handoff prepared (pending @approved before public
  re-publish). Public re-publish to `DZP-v9.9.5` is a separate, later, USER-authorized step — not
  part of this patch.

### Same-day addendum (2026-07-11) — Toji-audit v9.9.5 remediation + downstream snapshot P1 port

Gojo coordinated a same-day Toji audit of the v9.9.5 workflow above
(`audits/2026-07-11-toji-gojo-v9-9-5-workflow.md`; 2 MEDIUM findings, 0 Critical/High), plus a
downstream install bug-report port. Both are folded into this same v9.9.5 patch (no version bump).

- **CODE-001** (MED, Code Quality) CLOSED — `.protocol-state/brain/cortex/ingest.py::index()`
  telemetry was misleading: `files_dropped_secret` incremented for any file with **at least one**
  redacted chunk, even when clean sibling chunks remained indexed, contradicting the field's
  external name. Fix: added accurately-scoped `files_with_secret_redactions` (files with ≥1 redacted
  chunk) and `files_fully_omitted_secret` (strict subset — files with **zero** indexed chunks
  remaining); `files_dropped_secret` retained as a back-compat alias equal to
  `files_with_secret_redactions`. New contract tests distinguish partial retention from full
  omission.
- **SEC-001** (MED, CWE-184, Security) CLOSED — the SemVer placeholder recognizer added to
  `scripts/scan_protected_records.py` in the base v9.9.5 patch above admitted disguised secret
  entropy shaped like a version string. Closed across five adversarial review cycles, each forcing
  closure of a distinct entropy-smuggling channel: **SEC-DZPUP-9.9.5-SEMVER-MONOCASE-001** (P2,
  single monocase/2-class identifier bypass), **-CHAIN-001** (P1, alnum dot-chaining),
  **-DIGITCHAIN-001** (P1, unbounded chained ≤8-digit segments), **-DUALCOMPONENT-001** (P3,
  independent pre-release/build budgets doubling the effective allowance), and **-CORE-001** (P1,
  unbounded MAJOR.MINOR.PATCH core fields never budgeted at all). Final design: a single unified
  whole-value entropy budget (19 characters) spanning core + prerelease + build, counting all
  non-qualifier identifiers (digits included), a 9-word qualifier allowlist as the only zero-cost
  tokens, and a regex-level 8-digit cap on each core field; CalVer-safe. This supersedes the prior
  accepted `SEC-DZPUP-9.9.5-SEMVER-CAP` residual recorded above. `SECRET_FORMAT_PATTERNS` (provider
  credential-format detection) is untouched and remains unconditional throughout.
  **Accepted P3 residual (irreducible):** a ≤19-char sub-cap entropy channel remains — it cannot be
  tightened further without false-positiving the real, committed fixture
  `1.2.3-1+a1b2c3d.20260315` (exactly 19 characters, zero slack). Two non-blocking usability notes:
  `v`-prefixed version strings and cores with more than 8 digits now fail safe (flagged as
  non-placeholder; resolvable via the existing allowlist).
- **Downstream install report port** (a downstream self-filed resolution report):
  **BUG-SNAPSHOT-NULLFIELDS-001** (P1) CLOSED —
  `.protocol-state/create-snapshot.py::create_snapshot()` now emits a `reason` field (retaining the
  legacy `trigger` field for compatibility) and includes `metadata.description` only when a real
  string is supplied; previously, snapshot bodies (especially session-end snapshots) lacked `reason`
  and carried a null `description`, which failed the fail-CLOSED commit-gate schema and silently
  **blocked all commits** — a recurrence of the earlier BUG-SESSION-004 class, which had only fixed
  the manifest entry and not the snapshot body itself. **MF-1** (P1, Megumi) CLOSED — the `reason`
  enum in `protocol/validation-rules.yaml` (both the `snapshot` and `snapshot-manifest` schemas) was
  widened to add `pre-protected-edit`, `toji-snapshot`, and `pre_restore_backup`; `create-snapshot.py`
  gained a `VALID_TRIGGERS` allowlist plus an `argparse choices=` guard so an unknown trigger now
  fails fast before any write. The pre-existing stale live snapshot body was hand-repaired to match;
  `scripts/validate-protocol.py --check` now passes 13/13. **Flagged, not fixed:** a dead
  `pre_restore_backup` call site in `restore-snapshot.py` imports `create_snapshot` via a
  non-existent module path (silently swallowed by a broad `except`).
- Yuuji TDD (SemVer hardening: 163 passing on the required suites / 548 broader, zero regressions;
  snapshot gate-validation: 18/18). Megumi Tier-3 (SemVer) / Tier-2 (snapshot) @approved every phase.
  Not yet committed at the time of this entry — commit is pending explicit USER authorization.
- **FEAT-REQ-002** — `DZP_ALLOW_PROTOCOL_EDIT=1`, a per-invocation env override for the FEAT-REQ-001
  Cross-Agent Edit Restrictions protected-path pre-commit stage, mirroring the existing
  `DZP_ALLOW_PROTECTED_REWRITE` (FEAT-GUARD-001). Lets a Gojo/USER-authorized protocol change commit
  without `git commit --no-verify`, bypassing ONLY the FEAT-REQ-001 protected-path stage while the
  SEC-001 secret scan, the FEAT-GUARD-001 append-only guard, and `validate-protocol.py --check` all
  remain active. Loud unconditional stderr warning (never silent), non-persistent, exact-match `=1`
  trigger; POSIX (`scripts/git-hooks/pre-commit`) + PowerShell (`.ps1`) parity; documented as a new
  `override_env` key under `file_protection` in `protocol.config.yaml`. Yuuji TDD (6 real-subprocess
  hook tests, composability with `DZP_ALLOW_PROTECTED_REWRITE` proven); Megumi Tier-3 @approved as a
  net security improvement (strictly narrower than the `--no-verify` it replaces for authorized
  edits), 0 must-fix.

---

## Release Summary — v9.9.4 (PATCH)

v9.9.4 upgrades Toji (Sentinel) to v1.3.0 with standing read + scoped append-only audit-log write,
closes the findings from the 2026-07-09 Toji audit, and lands three Sukuna downstream-report canonical
items (attestation, publish-manifest completeness, and a report-only note).

- **Toji v1.3.0** — external auditor gains standing (always) read + append-only audit-log write to
  the two FEAT-GUARD-001-enforced protected records (`dev-notes.md`, `security-review.md`) via a
  scoped `edit` tool; full reports now written to a new `audits/` folder (2 existing reports
  migrated). `domain.record.md`'s stub is logged by Gojo instead — that file is gitignored and
  outside FEAT-GUARD-001's coverage, so Toji never writes it. CONSTRAINT_012 revised; tool-access
  matrices updated across root + protocol + global `CLAUDE.md`, the `~/.claude/agents/toji.md`
  stub, `AI_INSTRUCTIONS.md`, and `copilot-instructions.md`. Mechanical stub→report existence
  check added to the pre-commit guard. Megumi Tier-3 @approved (SEC-TOJI-101/102/103 closed).
- **Toji audit 2026-07-09** — **SEC-001** (MED): compensating protected-records secret scanner
  (`scripts/scan_protected_records.py`; allowlists only the historical Stripe docs literal,
  fails-closed on any other match; wired into pre-commit + CI; `.github/secret_scanning.yml`
  annotated Owner/Review-by). **IMPL-001** (MED): signed session-record reconciliation for
  `session_20260707_203626` appended to `dev-notes.md`/`security-review.md` (authoritative values
  sourced from `project-state.json`; the program-L record was ruled non-authoritative), a
  domain-record correction, plus `scripts/check_branch_record_isolation.py` (append-only-vs-merge-base
  and conflicting-terminal-records detector); program-L reconciliation itself deferred (USER
  decision). Megumi @approved.
- **Sukuna downstream-report canonical items** — **ISS-083** (P3): authorized-writer attestation
  (`.protocol-state/attestation.py` — side-channel HMAC ledger + monotonic sequence; sanctioned
  state writers are stamped; `validate-protocol --check` suppresses drift alerts for attested
  writes and alerts on unattested/forged/stale ones; non-blocking; Windows owner-only ACL on the
  key; local-integrity threat model documented). **ISS-084/085** (P2): root `dzp.py` added to the
  publish manifest + orchestration-trio completeness gate (Scope 5). **ISS-086** (P3): no
  canonical target exists (install-side `dzp-sync`); remains REPORT-ONLY.
- Yuuji TDD throughout; Megumi Tier-3 @approved every phase. Accepted P3: SEC-IMPL-001-RESIDUAL
  (branch-check Layer-2 fail-soft) + the attestation local-integrity boundary. New tests:
  attestation 55, distro completeness 11, secret scanner 20, branch-isolation 21, guard 46.

---

## Release Summary — v9.9.3 (PATCH)

v9.9.3 closes the accepted-P3 backlog remaining from the 2026-07-06 Toji audit remediation (v9.9.2)
plus the version-cascade-trap linter blind spot, all Megumi Tier-3 @approved (0 must-fix).

- **SEC-CORTEX-ENC-013** (P3, CWE-732) — CLOSED: `cortex/recovery.py` `write_owner_only()` now
  applies the Windows owner-only DACL to the O_EXCL empty file BEFORE the secret payload write,
  closing the success-path pre-hardening exposure window (fail-closed pre-write; the SEC-001
  post-write verification guard remains intact as defence-in-depth).
- **SEC-CORTEX-ENC-014** (P3, CWE-345) — CLOSED: `brain restore` emits a loud stderr conflict
  warning when `--verify` and `--force-unverified` are passed together (previously a silent
  override); `--verify` remains an accepted compat no-op; SEC-002 verify-by-default is unweakened.
- **SEC-CR101-004** (P3) — CLOSED: `migrate_state_9x.rollback()` restores `project-state.json` and
  `snapshot-manifest.json` via an atomic `_atomic_copy` (temp file + `os.replace`, same-directory),
  closing the crash-mid-copy corruption path that a direct `shutil.copy2` onto the live file left
  open.
- **Megumi UX finding** — CLOSED: `cortex_trigger` now emits a mandatory stderr warning plus an
  `export_skipped_reason` JSON field when the advisory snapshot export exits 9 (plaintext-export
  consent gate) on an encryption-enabled brain — previously a silent fail-soft skip that could read
  as "success" to automation watching only the exit code. The consent gate itself is unweakened.
- **TEST-001-RESIDUAL** — CLOSED: the last 4 Stripe docs-key literals (`tests/brain/
  test_recovery_write_owner_only.py`, `test_restore_encrypted.py`, `test_store_memory_ingest.py`,
  `test_v934_preflight.py`) replaced with a runtime-synthesized `'sk_live_' + 'Zz' * 12` token.
- **version-cascade-trap** — a new Type-7 `release_branch` stamp rule was added to
  `check_version_stamps.py`, closing the blind spot where `canonical_repository.release_branch`
  could silently drift out of sync with `protocol_version` on a version bump.

Accepted P3 residual: **SEC-CORTEX-ENC-015** (CWE-540) — the full Stripe public-docs example key
remains, as historical fact, in the append-only `.protocol-state/dev-notes.md` v9.9.2 entry (cannot
be scrubbed without violating FEAT-GUARD-001 append-only integrity). Handled at the tooling level via
`.github/secret_scanning.yml` `paths-ignore` + an admin alert dismissal, not a doc rewrite.

Megumi Tier-3 review: @approved, 0 must-fix, 1 accepted P3 (SEC-CORTEX-ENC-015). TEST-COV-001
(coverage gap on the plain-text-mode consent-gate warning) closed same-day. Yuuji TDD. Distro
re-synced byte-identical; no new publish-manifest entries required.

---

## Release Summary — v9.9.2 (PATCH)

v9.9.2 remediates the findings from the 2026-07-06 Toji audit
(`.protocol-state/toji-reports/2026-07-06-toji-audit-DZP-v9.8.0-to-v9.9.1.md`), all Megumi Tier-3
@approved (0 must-fix).

- **SEC-001** (HIGH, CWE-732) — CLOSED: `cortex/recovery.py` `write_owner_only()` is now fail-closed;
  a DACL-hardening failure unlinks the secret artifact then re-raises. All 3 callers audited (the
  journal was independently verified secret-free by Megumi). New test file (5 tests).
- **SEC-002** (HIGH, CWE-345) — CLOSED: `brain restore` verifies by DEFAULT (digest/key/integrity/
  schema); `--verify` kept as a no-op; `--force-unverified` break-glass with a loud warning and a
  mandatory pre-op backup. Restore tests 3 → 9.
- **IMPL-001** (MED) — CLOSED: `brain encrypt` forwards `--purge-backup`; purge is structurally
  unreachable on failed verification via both CLI paths. Encrypt-CLI tests 13 → 15.
- **CODE-001** (MED, CWE-391) — CLOSED: `cortex/memory_export.py` distinguishes table-absent from
  query failure (failures now FAIL the export instead of producing a hollow artifact); manifest
  gains backward-compatible `table_meta` counts. Export tests 4 → 11.
- **TEST-001** — CLOSED: Stripe docs-key literal replaced with a runtime synthetic token (still trips
  `contains_secret`); kills dev-repo secret-scanner false-positive noise.
- **Incidental** — BUG-TEST-WINLOCK-001: e2e WinError-5 flake fixed (unreleased Store handle).

Megumi Tier-3 review: @approved, 0 must-fix. Accepted residuals: SEC-CORTEX-ENC-013 (P3,
success-path pre-hardening window), SEC-CORTEX-ENC-014 (P3, flag-precedence silent win), and
TEST-001-RESIDUAL (2 test files keep the literal). Scoped tests 109 passed/1 skipped; engine
parity 19/19. Resilience suite verified 23/23 (restore/recovery/export all green).

---

## Release Summary — v9.9.1 (PATCH)

v9.9.1 closes the Track C encryption-debt residuals deferred from v9.9.0 (`d62d773` feat bundle +
`938c53f` protocol doc companion), all Megumi Tier-3 @approved (0 must-fix).

- **C1** — SEC-CR101-003 CLOSED: `migrate_state_9x.py` `_backup()`/`rollback()` now track and
  restore `snapshot-manifest.json` presence via `backup-meta.json`; rollback pre-flights manifest
  restore; legacy-backup fallback preserved. +6 TDD tests (19 green).
- **C2-1** — RISK-ENC-003: `--purge-backup` post-verify zero-overwrite shred (default OFF).
- **C2-2** — Windows salt-sidecar owner-only ACL via `icacls` (fail-soft, win32-only).
- **C2-3** — `--key-b64` now requires `--insecure-key-argv-ok`; `brain encrypt` in-process call
  fixed to match.
- **C2-5** — `requirements-enc.txt` hash-pinned (19 packages, 283 sha256 hashes;
  `cryptography==49.0.0`).
- **C2-4** — RISK-ENC-006: plaintext export is consent-gated (`--plaintext-ok`, exit 9) when
  encryption is enabled; escrow memory-export path unaffected; disabled (plaintext) path remains
  byte-identical.
- **Inherent boundaries** (keystore same-user access, no key zeroization) documented in the
  encryption-at-rest design spec §12 + `SECURITY.md`.
- **Rider** — BUG-CORTEX-STATUS-ENC-001 CLOSED-WITH-EVIDENCE: `brain status` text/json share one
  source dict; 3 parity regression tests added; zero code change required.

Megumi Tier-3 review: @approved, 0 must-fix. Accepted residuals: SEC-CORTEX-ENC-010/011/012 (P3) +
SEC-CR101-004 (P2). Engine parity 19/19.

---

## Release Summary — v9.9.0 (MINOR)

v9.9.0 ships the R1 Cortex Key-Recovery subsystem (PLAN-CORTEX-RECOVERY-001, 44 commits,
Megumi Tier-3 @approved) and the BUG-SESSION-001/002/003/004 session-lifecycle tooling fix.

- **R1a** — Escrow + manifest + key-matched restore: structured escrow files, integrity-checked
  manifest, and key-fingerprint validation before any restore attempt.
- **R1b** — `cortex/recover.py` (predicate/journal/probe/ladder) + `cortex/memory_export.py`
  (escrow-wrapped memory snapshot) + reset preserving/unrecoverable split + `brain recover`
  CLI (ladder/repair/finalize subcommands).
- **R1c** — `brain input`/`/input` UX + §17.7 access matrix + AI-001 structured output +
  slash registration (`/input` slash command).
- **BUG-SESSION-001/002/003/004** — session_monitor ISO last_updated + LF writes +
  `.gitattributes` + snapshot reason-enum + override-prohibition. Megumi Tier-3 @approved.
- **Deferred → v9.9.1**: Track C C1/C2 encryption debt (shared-brain key provisioning,
  key rotation, export encryption, key zeroization).

---

## Release Summary — v9.8.2 (PATCH)

v9.8.2 fixes a Windows-only encoding crash in `.protocol-state/script_coordinator.py`:
`_run_step()` captured subprocess output without forcing UTF-8, so any step emitting non-ASCII
(e.g. `custom_agent_monitor.py --list` printing `✅`) raised `UnicodeDecodeError`/`UnicodeEncodeError`
on cp1252 Windows consoles. The step was then incorrectly reported as `failure` despite completing
successfully. Fix: `PYTHONUTF8=1` injected into the child environment + `encoding="utf-8",
errors="replace"` on the `subprocess.run()` call. Fail-soft (did not block the overall `/session
update` sync); consumer-facing; low severity.

---

## Release Summary — v9.8.1 (PATCH)

v9.8.1 fixes a silent breakage in the v9.8.0 encryption migration: `sqlcipher_export()` drops
`PRAGMA user_version`, so any brain encrypted via `brain encrypt --execute` came up with
`availability: unavailable` (SEC-ACCESS-010 schema-guard fail-closed, user_version=0 vs
metadata.schema_version=4) despite all data being intact. Fix: `encrypt_brain()` and
`decrypt_brain()` now capture the source `PRAGMA user_version` and restore it on the destination;
the smoke-verify step ABORTS if the post-migration value does not match. No data loss; the
encrypted brain was simply unusable until rollback or manual repair. 11/11 migration tests pass.
Yuuji TDD.

---

## Release Summary — v9.8.0 (MINOR)

v9.8.0 adds **Cortex encryption-at-rest** (PLAN-CORTEX-ENC-001) and folds in a downstream-reported
**v9.7.2 upstream-upgrade bundle** plus the **orphan-GC** feature and its P1 security remediation.

- **Cortex encryption-at-rest (opt-in, default OFF)** — SQLCipher full-DB AES-256; Argon2id + OS-keyring
  hybrid key model (`DZP_CORTEX_KEY` `file:` fallback); reversible backup-first migration
  (`migrate_cortex_encrypt_9_8.py`, vec0/FTS5 smoke-verify, atomic replace, shared-brain ledger refusal);
  `brain key`/`brain encrypt` CLI; `brain status` `encryption_status` + posture advisory. Disabled path
  byte-for-byte unchanged. **SEC-CORTEX-ENC-001..009 CLOSED; Megumi Tier-3 @approved.** 7 accepted P3
  residuals → v9.9.x (shared-brain key provisioning + rotation, exports encryption, key zeroization).
- **`brain reset --scope orphans`** (BUG-CORTEX-PROLIF) — safe GC of orphaned Cortex install dirs:
  dry-run default; quarantine-to-`.trash-<UTC-ts>` on `--execute`; `--hard-delete` for permanent.
  P1 remediation **SEC-9720-008/009/010/011 CLOSED** (TOCTOU re-validation + symlink/junction reject;
  preserve graph/memories/recursive/unreadable; 30-day recency gate; quarantine default).
- **v9.7.2 upstream-upgrade bundle** (Groups A/C) — SEC-9720-001/004/006, C-1 engine preflight,
  STATE-LEGACY sanitizer, DRIFT-ENGINE engine-parity check, ONEDRIVE-LOCK + GUARD-FRICTION docs.
- **Tests**: 935 passed / 3 skipped (`tests/brain`); full suite green. Yuuji TDD throughout.
- **Note**: single-user encryption scope; shared-brain key provisioning + rotation deferred to v9.9.x.

---

## Release Summary — v9.7.2 (PATCH)

v9.7.2 closes two HIGH-severity defects that shipped silently in the public distribution from v9.4.0 through v9.7.0.

- **SEC-CORTEX-MEM-001 (HIGH/P1)** — Cortex memory-keying silent data loss: memories written via
  `brain remember` shared a generic `source_path`, causing live overwrites (each new memory silently
  replaced the previous one), `brain seed` loss (seed entries overwrote live memories), and v1→v2
  migration blocks (duplicate-key constraint failures). Fix: `memory.py` keys on
  `source_path=f"memory:{mem_id}"`; `migrate_cortex_storage_9_4.py` `_effective_storage_key` applied
  on insert loop with P2/P3/P4 parity; `brain.py:_seed()` unique `line_start` + truthful counter.
  Accepted P3: SEC-CORTEX-MEM-002 (theoretical key-collision edge case, advisory documented).
- **BUG-CORTEX-MIGRATE-001 (HIGH)** — `migrate_cortex_storage_9_4.py` was stub-only: no `sqlite_vec`
  extension load, no vec0 DDL, no vector blob copy, no dim/model resolution. Any user who attempted
  v1→v4 migration on a real brain would silently get an empty vector table. Fix (MV-1..8):
  `_open_db_vec` loads `sqlite_vec`; real `vec0 content_vectors` DDL with correct dim; direct
  byte-exact blob copy from source `vec0`; dim + model resolved from blob + config fallback.
  Accepted P3: SEC-MIGRATE-RV-001 (dim-mismatch detection advisory).
- **Note**: Both defects shipped silently in the public canonical from v9.4.0 through v9.7.0.
  All users of shared-brain or multi-install Cortex who relied on `brain remember` should re-run
  `brain seed` + `brain index` after upgrading.
- **Live brain validation**: DZ's own brain migrated v1→v4; 21/21 memories preserved; recall confirmed OK.
- **Tests**: 861 passed / 2 skipped / 0 failed.
- **Authorization**: Yuuji TDD + Megumi Tier-3 @approved.

---

## Previous Release — v9.7.1 (PATCH)

---

## Release Summary — v9.7.1 (PATCH)

v9.7.1 delivers PLAN-CORTEX-ACCESS-001 Cortex Access Hardening (CIA-triad).

- **Phase 1 — Destruction safety** (SEC-CORTEX-ACCESS-008): anti-destruction guard on shared brain
  — `cortex_installs` role/first_seen ledger; `brain reset --scope self|all` with
  `--shared-ok`/`--all-installs-acknowledged`/`--force-foreign` gate; foreign-install refusal;
  `_store()` proactive ledger stamping; `DZP_CORTEX_INSTALL_ID` validation. SEC-ELAST-002 (P3):
  LIKE-wildcard escape in `_protected_sql_clause`.
- **Phase 2 — Resilience** (SEC-CORTEX-ACCESS-009): pre-op `brain.db` backup to
  `<data_dir>/backups/` + retention + `PRAGMA integrity_check`/`foreign_key_check` +
  `integrity-fail.flag` + `brain restore --from --verify`. (SEC-CORTEX-ACCESS-010): graceful
  degradation — `brain status` `availability_status` ok/degraded/unavailable +
  `DZP_CORTEX_SKIP_RELEASE_GATE` release-gate escape + SchemaTooNew/Mismatch exit 0.
  SEC-ACCESS-008-NEW-001 (P3): read-op ledger stamp fail-soft on locked DB.
- **New config key**: `backup_retention_count` (default 3).
- **Deferred**: ACCESS-004/005/006 + 007/011 encryption + 012/013 to v9.8.x. CIA-triad design
  (ACCESS-008..013) recorded.
- **Tests**: 1140 passed. Yuuji TDD + Megumi Tier-3 @approved every phase.

---

## Previous Release — v9.7.0 (MINOR)

---

## Release Summary — v9.7.0 (MINOR)

v9.7.0 delivers Stage 3 Storage Elasticity (PLAN-CORTEX-UNIFIED-001 Stage 3, absorbed
PLAN-CORTEX-ELASTIC-001): per-install storage budgets with principled eviction, the `store.compact()`
orphan-sweep + VACUUM, and live storage reporting in `brain status --json` and
`cortex_trigger --level` output.

- **Schema v4** (Phase 1): `last_recalled_at` nullable column on `content_refs`; v4 schema dispatch
  (v1/v2/v3 DBs still run in-mode); `migrate_cortex_elastic_9_7.py` (v3→v4, backup-first,
  `cortex_installs` ledger gate).
- **Eviction engine** (Phase 1): `Store._evict_to_budget` with strict priority order
  (archives→untrusted→semi→LRU; NEVER evicts protected/trusted/live chunks; SQL-guarded);
  per-install `storage_budget_mb` config; ingest post-run eviction (fail-soft); LRU opt-in
  privacy flag `lru_eviction_enabled` (S3-RISK-004).
- **Compact + advisory** (Phase 2): `store.compact()` content-addressed orphan-sweep + VACUUM
  (`SEC-UNIFIED-004` `OperationalError` fail-soft; `S3-RISK-003` `index.lock` abort); `brain compact`
  CLI; `brain status --json` gains `"storage"` object; `cortex_trigger` RESERVE-D field now
  populated (ALWAYS advisory, never fail-closed even under `--strict`); `cortex-compact` lifecycle
  event wired.
- **Security**: `SEC-ELAST-001` (`include_protected` SQL guard) + `SEC-UNIFIED-004` closed.
  Deferred: `SEC-ELAST-002` (P3) + `PLAN-CORTEX-ACCESS-001` (write-authorization) +
  `SEC-CORTEX-ACCESS-007` (encryption-at-rest).
- **Test isolation fix**: `conftest.py` neutralizes ambient `DZP_CORTEX_DATA_DIR`/`INSTALL_GROUP`
  env vars (root-caused a shared-label live-brain mutation — the `<project>-shared` scenario).
- **Tests**: 1080 passed / 2 skipped / 0 failed.
- **Review**: Yuuji TDD + Megumi Tier-3 @approved each phase. Lever 5 (group-budget) deferred.

---

## Previous Release — v9.6.0 (MINOR)

---

## Release Summary — v9.6.0 (MINOR)

v9.6.0 delivers Stage 2 Graph Structured Recall (PLAN-CORTEX-GRAPH-001): a typed entity/edge graph
layer (schema v3), hybrid BM25+dense retrieval with true RRF re-ranking, and proactive surfacing via
`cortex_trigger.py --recall`.

- **Schema v3** (Phase 1): `cortex_entities`/`edges`/`query_cache`/BM25 FTS5 tables +
  `migrate_cortex_graph_9_6.py` (v2→v3, backup-first, `cortex_installs` ledger gate) +
  `brain entity`/`gnogo`/`release-check` CLI commands; `graph.py` typed entity/edge graph with
  go/no-go pack + query-time dual-filter trust.
- **Hybrid retrieval** (Phase 2): `cortex/retrieval.py` (BM25+dense, TRUE RRF, recency/trust
  re-rank, index_epoch query cache) + `Store.hybrid_search` + `brain query --hybrid` / `brain cache`.
- **Proactive surfacing** (Phase 3): `cortex_trigger.py --recall` (DATA-not-instructions boundary,
  trusted,semi floor, [SUSPECT] flag, stdout secret redaction) + `cortex/extractor.py`
  (SEC-ID/WI/Version/Decision entity extraction, schema-gated) + `brain distill` (propose-only) /
  `brain seed` / `brain recall` + advisory wiring to `pre-protected-edit`, `pre-release`,
  `session-end`.
- **Security**: SEC-GRAPH-001..005 P1 folded; SEC-GRAPH-NEW-001..004 + SEC-HYBRID-001..004 +
  SEC-GRAPH-009 + SEC-UNIFIED-003 closed.
- **Tests**: 1005 passed / 2 skipped / 0 failed.
- **Review**: Yuuji TDD + Megumi Tier-3 @approved every phase. Distro manifest + 4 new modules.

---

## Previous Release — v9.5.0 (MINOR)

---

## Release Summary — v9.5.0 (MINOR)

v9.5.0 delivers full Cortex Interconnectivity (Stage 1): a single shared `cortex_trigger.py` wrapper
replaces all ad-hoc Cortex calls; `brain.py` gains a lazy Embedder + `--full` flag (Phase 3); the
DZP event registry is rewired so all 10 lifecycle events route through the coordinator (Phase 4);
and lifecycle skills (`.claude/commands/*.md`) are updated to invoke `dzp.py event <name>` directly
(Phase 5b), closing the orphaned-event regression that caused `/session end` + `/session update` to
silently skip Cortex after Phase 4.

- **`cortex_trigger.py`** (Phase 2): shared wrapper used by every lifecycle event; eliminates the
  pre-v9.5.0 pattern of each script importing Cortex independently.
- **`brain.py` lazy Embedder + `--full`** (Phase 3): embedder initialised on first use only;
  `--full` forces a complete rebuild, bypassing the incremental-only guard.
- **Registry rewire + double-trigger removal** (Phase 4): `script_dependencies.yaml` updated to
  route all 7 pre-existing events through `cortex_trigger.py`; direct `_sync_cortex_index` calls
  in `session_monitor.py` removed to prevent double-fire.
- **10 lifecycle events total** (7 rewired + 3 net-new: `pre-publish`, `post-migration`,
  `post-rotation`). Coordinator is now the single Cortex entry point for all lifecycle paths.
- **Lifecycle skill → coordinator routing** (Phase 5b): `.claude/commands/` skill files route
  through `dzp.py event <name>` with PARITY CONSTRAINT (session-tracking, wellbeing-logging,
  and project-doc-sync preserved; Cortex fires exactly once via coordinator). Closes
  S1-RISK-012 (orphaned-event regression, HIGH).
- **Security**: SEC-P4-001..004 + SEC-UNIFIED-001 closed.
- **Tests**: 774 passed / 1 skipped / 0 failed (baseline raised from 745 at Stage-1 start).
- **Review**: Yuuji TDD Phases 2–5b + Megumi Tier-3 @approved (Phases 4, 5, 5b).

---

## Previous Release — v9.4.1 (PATCH)

---

## Release Summary — v9.4.1 (PATCH)

v9.4.1 productionizes the protected-document append-only guard (FEAT-GUARD-001), mechanizing the
"APPEND ONLY" rules already stated in the protocol. A pre-commit hook verifies via HEAD-blob
byte-prefix comparison that `.protocol-state/dev-notes.md`, `.protocol-state/security-review.md`,
and `.dzp-domain/domain.record.md` are never overwritten or truncated.

- **Guard (`scripts/check_protected_append_only.py`)**: reads `protected_documents` config block;
  skips cleanly if guard is disabled or file is unstaged; fails with a human-readable message on
  shrinkage. CRLF-hardened (Windows-safe byte comparison). `DZP_ALLOW_PROTECTED_REWRITE=1`
  environment variable allows authorized rewrites (file rotation, emergency restore).
- **Unified pre-commit hook** (`scripts/git-hooks/pre-commit` + `.ps1`): runs publish-skip →
  append-only guard → agent guard → validate-protocol in sequence (SEC-GUARD-003 — previously
  three separate hook files could conflict). Installer: `scripts/install-git-hooks.{sh,ps1}`.
- **Cortex stale `index.lock` self-heal**: mtime TTL guard prevents a stale lock from blocking
  all Cortex operations after an interrupted index run.
- **Distro**: `publish-manifest.yaml` ships `scripts/check_protected_append_only.py`,
  the unified hook scripts, and `scripts/install-git-hooks.*`.
- **Tests**: `tests/test_protected_append_only.py` (36 tests) + `tests/test_cortex_lock_staleness.py` (11 tests).
- **Security**: SEC-GUARD-001..006 all CLOSED — guard logic, CRLF hardening, hook unification,
  config size guard (SEC-GUARD-004), hooks python-absent warning (SEC-GUARD-005), override
  CI-scoping note (SEC-GUARD-006). All folded into v9.4.1.
- **Review**: Yuuji TDD (Phase 1) + Megumi Tier-2 @approved. SEC-GUARD-001..006 all CLOSED.

---

## Previous Release — v9.4.0 (MINOR)

---

## Release Summary — v9.4.0 (MINOR)

v9.4.0 replaces DZP Cortex's per-scope **chunk-addressed** storage (v1) with a
**content-addressed** model (v2): one vector per distinct `content_hash`, with N
reference-counted occurrence rows. This eliminates the ~55% vector duplication
measured in shared-brain installs (BUG-CORTEX-007) and closes the DESIGN-001
cross-scope orphan-cleanup corruption path.

- **Schema v2:** `content` / `content_vectors` / `content_refs` (+ indexes on
  `content_hash`, `storage_key`, `(content_hash,trust)`); deterministic `ref_id`;
  trust at the reference level (no cross-scope trust elevation).
- **Reversible migration:** `.protocol-state/migrate_cortex_storage_9_4.py`
  (`--check/--execute/--rollback`) — backup-first, single `BEGIN IMMEDIATE`,
  parity-gated (count invariants + public result contract + trust-filter set)
  before any table drop; idempotent; `cortex_installs` shared-DB version gate.
- **Engine:** `init_schema` dispatch (fresh→v2; legacy v1 kept on v1 until
  migrated — never auto-stamped; too-new/mismatch fail-closed on ALL ops) gated
  by the v9.3.4 preflight guard. End-to-end v2 ingest/query/memory with recall +
  trust-filter parity vs v1. `doctor`/`dedup` report v2 ref-counts + true dedup ratio.
- **Distro:** ships the migration utility + smoke-tested (IMPL-002).
- Built across 7 phases (each Yuuji TDD + Megumi Tier-3); Gojo-coordinated
  all-hands review (Megumi/Todo/Maki/Yuuji/Nobara). **Megumi final Tier-3
  @approved** — all 13 §8 acceptance criteria PASS; SEC-CORTEX-009..024 closed;
  accepted P3 SEC-CORTEX-016 (vec0 lastrowid integration-test gap). **350 passed
  / 1 skipped** brain + **21** distro tests; `assert_version` green at 20 sources.

---

## Release Summary — v9.3.4 (PATCH)

v9.3.4 is the **preflight + Cortex hardening** release that gates the v9.4.0 content-addressed
storage migration (PLAN-DESIGN-001 §0). It ships the schema-version guard to the v9.3.x engine
**before** any migration can run, so an old engine can never corrupt a migrated (v2) shared DB.

- **Schema-version guard:** `PRAGMA user_version` is the single canonical authority;
  `metadata.schema_version` is a diagnostic mirror. A too-new DB or a marker mismatch
  **fails closed on ALL operations** (`SchemaTooNewError`/`SchemaMismatchError`). The marker is
  never downgraded — fixing the pre-v9.3.4 unconditional `user_version=1` corruption vector.
- **`cortex_installs` membership ledger:** every engine run stamps its install id + version +
  last-seen, enabling the v9.4.0 shared-DB version gate.
- **Performance:** the schema guard is memoized per `Store` (no per-call overhead).
- **Security (all-hands Megumi):** SEC-CORTEX-009 (dim DDL validation), 010 (export secret
  re-filter), 011 (rglob `recurse_symlinks=False`, Py3.13+), 012 (PS1 hook stderr capture),
  013 (memory `remember()` injection suspect-flag).
- **UX (Nobara P1):** actionable schema-error messages (which install to upgrade, DB path,
  recovery commands, fail-soft note).
- Gojo-coordinated **all-hands Tier-3** review (Megumi/Todo/Maki/Yuuji/Nobara). **Megumi
  Tier-3 @approved.** **168 passed / 1 skipped** brain tests. Extended version gate passes.

---

## Release Summary — v9.3.3 (PATCH)

v9.3.3 remediates the **Toji Sentinel audit** (`internal-docs/Patch Report/BugReport3.md`, 7 findings).
Sukuna-led; **Megumi Tier-2 @approved** (3 accepted P3, zero blocking); **123/123** brain tests
(80 baseline + 43 new: Tier B + 3 review/P3 fixes); the extended version gate passes at 20 sources.

**Tier A — corrections (no behavior change):**
- **IMPL-002** — reconciled all 10 agent `protocol_version`/`[CORE FILE]` stamps + the nested
  `project-state.json` straggler (`9.2.1`) and core files to `9.3.3`; **extended `assert_version.py`**
  to scan agent frontmatter and ALL project-state version fields (the gate that previously passed
  blind on the drift). Negative test confirms it now catches it.
- **SEC-001** — `verify-protocol.ps1` reads `protocol.config.yaml` as explicit UTF-8 (fixes a Windows
  ANSI-codepage false-fail on the config's 128 non-ASCII bytes).
- **CODE-001** — `_SCOPED_PREFIX_RE` consolidated to one canonical definition in `store.py`, imported
  by `ingest.py` (no more two-declaration drift risk).
- **IMPL-001** — corrected a downstream issue report: interim relief is `brain dedup --report` (read-only) only;
  destructive de-dup rejected pending the content-addressed migration.

**Tier B — new functionality (Yuuji TDD, Megumi-reviewed):**
- **SEC-002** — positive `index_extensions` allowlist (augments the binary denylist), opt-in
  `max_file_chunks` per-file cap (default `0` = unlimited), and largest-file/outlier reporting.
- **IMPL-003** — read-only `brain dedup --report` and `brain doctor` diagnostics (duplicate ratio,
  chunks/rowmap/vectors integrity, trust distribution, engine-hash drift detector, largest files).
  No destructive operations.

**Deferred:** **DESIGN-001** (content-addressed / reference-counted shared-brain storage) → **v9.4.0
MINOR** with migration tests, rollback notes, and Megumi security review. Query-time dedup keeps
recall correct in the interim.

**Security:** Megumi @approved with three accepted P3 notes (SEC-CORTEX-DIAG-001 engine-hash is a
drift detector not tamper-proof; -002 `index_extensions` element-type validation gap; -003 dedup
`text_preview` info-disclosure bounded by `contains_secret`). No regression of SEC-CORTEX-001/002/003/004
or BUG-CORTEX-006.

---

## Release Summary — v9.3.2 (PATCH)

v9.3.2 **upstreams the Cortex engine hardening** that had only existed in downstream installs'
gitignored `.protocol-state/` files into the **canonical** `cortex/` engine — closing **SEC-CORTEX-003**
(the "next protocol sync silently reverts every patch" integrity gap, OWASP A08). Because the canonical
`cortex/` files are git-tracked, applying them here propagates the fixes to every install on its next sync.

**Engine changes (canonical + distro, byte-identical):**
- **SEC-CORTEX-003 / cap** — per-file index cap is now config-driven (`max_file_bytes`, default **6 MB**;
  previously a hardcoded `1_000_000`). `ingest._safe_candidate` reads `cfg["max_file_bytes"]`.
- **SEC-CORTEX-001 / trust** — `_trust_for` is now default-deny: only `protocol/`, `scripts/`, and the core
  root docs (`CLAUDE.md`, `AI_INSTRUCTIONS.md`, `README.md`) are `trusted`; **all other content → `semi`**.
- **SEC-CORTEX-002 / secrets** — placeholder-aware detection via a shared `contains_secret()` used by both
  `ingest.chunk_file` and `memory.remember`. High-confidence FORMATS (PEM, AKIA, GitHub, Slack, JWT, Bearer)
  always drop; `keyword[:=]value` drops **only** when the value is not an obvious placeholder
  (`[...]`/`<...>`/`${ENV}`, `xxxx`/`***` masks, placeholder words, `<6` chars).
- **SEC-CORTEX-004 / validation** — `config.validate()` rejects non-positive / non-int / bool `max_file_bytes`.
- **BUG-CORTEX-006 / dedup** — query-time content-hash de-duplication in `store.py` (`_overfetch_k` +
  `_dedupe_by_content`) applied to both the `sqlite_vec` and stub search paths. Trust filter runs in SQL
  **before** dedup, so dedup can never elevate or relabel trust.

**Verification:** `ast.parse` clean ×4; **93/93** Cortex unit tests pass (`tests/brain/` + `tests/test_cortex_sync.py`).
**Status:** Sukuna-led; **Megumi Tier-2 @approved** (0 findings, 0 publish blockers). **v9.3.1 skipped** (combined single carving per USER decision).
**Note:** This is the canonical-repo upstream; it does NOT pull in any install-specific scope folders
(e.g. a downstream install's `business-assets/`) — installs opt into expanded scope via their own `brain.config.yaml`.

---

## Release Summary — v9.3.0 (MINOR)

v9.3.0 is a **BugReport remediation bundle** (Sukuna-led, Megumi review pending) resolving the
downstream-consumer findings logged during the v8.13.0 → v9.2.1 upgrade sessions, plus one
feature request. Highlights:

- **BUG-SESSION-001 (HIGH, safety):** the wellbeing safety check crashed on tz-naive legacy
  `last_alert_time` (aware−naive subtraction), silently disabling the 4h/6h/8h alerts. Fixed
  with a centralized `_parse_utc()` normalizer across `session_monitor.py`.
- **BUG-MIGRATE-001:** new `migrate_state_9x.py` — additive 8.x→9.x state migration (injects
  `tier_settings`/`validation_state`/`agent_registry`) + naive-timestamp sanitizer, with
  `--check`/`--execute`/`--rollback`.
- **BUG-SCHEMA-001:** `validation-rules.yaml` no longer requires the deprecated
  `tier_usage_statistics` block.
- **BUG-VALIDATE-001/002:** validator false-negative hardened (unvalidatable/empty no longer
  reports SUCCESS); `requirements-dev.txt` declares `jsonschema`/`PyYAML`.
- **BUG-VERIFY-001:** `verify-installation.py` manifest reconciled with `publish-manifest.yaml`
  (dev-only SUF/review files made optional → green install from the published branch).
- **BUG-CORTEX-001/002/003/004/005:** first-class shared-brain (`install_group` /
  `DZP_CORTEX_INSTALL_GROUP`, no absolute-path leak) + **install-scoped source keys** so
  multi-install shared indexing no longer clobbers per-install protected docs (backward
  compatible; default unscoped behavior unchanged); OneDrive data-dir remediation hint;
  Windows symlink-warning suppression; `hf_xet` note.
- **BUG-DISTRO-001:** removed stray `.claude/commands/sukuna copy.md` + added a `* copy.*`
  publish-audit guard.
- **BUG-DOC-001:** `IMPLEMENTATION_GUIDE.md` refreshed to 9.x (Cortex setup + 8.x→9.x migration
  steps; version-agnostic copy examples).
- **FEAT-REQ-001:** opt-in, config-driven agent-file protection git hook
  (`scripts/git-hooks/` + `scripts/install-git-hooks.{sh,ps1}`) — ships for consumers, **not
  auto-installed and not active in the DZP dev repo**.

Out of scope: BUG-SYNC-001/002 (project-local `dzp-sync`, not part of canonical).

---

## Release Summary — v9.2.1 (FEATURE)

v9.2.1 ships the **Central DZP Script Orchestration System** (PATCH-ORCH-001): a root-level `dzp.py` entry-point, a `.protocol-state/script_coordinator.py` engine, and a `script_dependencies.yaml` event registry. The system wires 7 DZP lifecycle events (session-update, session-end, ts-start, ts-complete, pre-protected-edit, pre-release, toji-snapshot) to sequenced, dependency-aware script steps with per-event fail-soft vs fail-CLOSED gates. 11 SEC-ORCH security controls and SEC-COORD-001..005/005-EXT remediations applied; Megumi Tier-3 @approved (one P3 accepted-risk documented). Dev-only; distro-excluded. Builds on v9.1.1 base (v9.2.0 intentionally skipped per USER decision).

### Headline changes (PATCH-ORCH-001)
- **`dzp.py`** (root entry-point) — single CLI to run any registered DZP lifecycle event by name; dispatches to `script_coordinator.py`
- **`.protocol-state/script_coordinator.py`** (engine) — event-driven step sequencer with dependency resolution, per-step timeouts, fail-soft/fail-CLOSED classification, structured logging
- **`script_dependencies.yaml`** (registry) — 7 events mapped to ordered step lists with gate policy and dependency declarations (event->step only; no cross-event wiring)
- **44 tests passed / 1 skipped** — Yuuji Tier-3 test suite; Megumi Tier-3 @approved
- **Security** — SEC-ORCH-001..011 + SEC-COORD-001..005/005-EXT resolved; one P3 accepted-risk documented
- **Distro** — excluded from `dzp-publish` allowlist (dev-only tooling)

### Why FEATURE (not PATCH or MINOR)
Adds a new user-facing orchestration surface (dzp.py CLI + event engine) that does not exist in v9.1.1 and is intentionally numbered 9.2.1 per USER direction (9.2.0 skipped).

---

## Previous Release — v9.1.1 (PATCH)

**Version:** v9.1.1
**Release Date:** 2026-06-14
**Release Type:** PATCH Release (Cortex Stabilization — PATCH-STABILIZE-001)

---

## Release Summary — v9.1.1 (PATCH)

v9.1.1 is a **stabilization patch** (PATCH-STABILIZE-001) that fixes real defects in the published v9.1.0 Cortex engine, hardens the brain-index hooks, reconciles leftover version drift, and aligns documentation with actual fail-soft behavior.

### Headline changes (PATCH-STABILIZE-001)
- **Cortex core fixes** — `brain.py`: propagate `--allow-unsafe-data-dir` to `status` and `query` (PR#92:73); derive embedding dimension from model, not hard-coded 384 (PR#92:95). `cortex/ingest.py`: guard chunk/vector cardinality mismatch before upsert (PR#92:153). `cortex/paths.py`: anchor relative `data_dir` overrides to `repo_root` (PR#92:75).
- **Hook hardening** (same class as SEC-ORCH-002/006) — `.claude/settings.template.json`: add missing `$TimeoutSeconds = 30` definition (PowerShell hook was broken). `scripts/brain-index-hook.ps1` + `.sh`: pass repo path as argv data, not interpolated into `-c` source (prevents apostrophe/path-injection breakage); make lock acquisition atomic + ownership-safe (eliminates TOCTOU race from `Test-Path`→`New-Item` + overlapping index runs).
- **Dependency-scanner robustness** — `scripts/dependency-scanner.py`: confine `--export` path to repository root (PR#92:742).
- **Version-drift reconciliation** — `project-state.json`: `session_tracking.protocol_version` straggler (`8.11.0`) and a secondary `9.0.0` straggler both reconciled to `9.1.1`.
- **Documentation alignment** — `.claude/commands/session-update.md`: replace `&&`-chained shell snippet with fail-soft `if status { index } else { proceed }` to match `session_monitor._sync_cortex_index()`. `protocol/skills/session.md`: wire snapshot export into `/session end` or remove the promise. `protocol/skills/ts.md`: use default trust tier, keep Cortex failures visible. `protocol/SUKUNA-REPORT.md`: fix fast-path invocation note. `slash-commands/ts-codered.md`: make Cortex footer mandatory, not optional.
- **Sukuna live-bug fixes** — `.protocol-state/{tier-statistics,gojo-learn,sukuna-learn}.py`: insert `scripts/` on `sys.path` before `from verify_working_directory import …` (import failed from project root). `snapshot_integration.py`: fix runtime constant from `scripts/create-snapshot.py` to `.protocol-state/create-snapshot.py` (auto-snapshots were silently failing); update stale docs (`SNAPSHOT_INTEGRATION.md`, `DEPENDENCY_SCANNER_GUIDE.md`, `gojo-snapshot-integration-guide.md`).
- **Security** — Megumi @approved, zero new SEC-IDs. All findings are defects from the v9.1.0 Cortex merge, not new vulnerabilities.

### Why PATCH
Bug fixes in the published Cortex engine, hook hardening, and documentation corrections with full backward compatibility — no new features, no breaking changes.

---

## Previous Release — v9.1.0 (MINOR)

**Version:** v9.1.0
**Release Date:** 2026-06-14
**Release Type:** MINOR Release (DZP Cortex — Local Semantic Memory)

---

## Release Summary — v9.1.0 (MINOR)

v9.1.0 ships the **DZP Cortex** feature (PLAN-BRAIN-002): a local semantic-memory "separate brain" that was built and tested during the v9.0.0 cycle but deliberately held back from distribution until ready.

### Headline changes
- **DZP Cortex (PLAN-BRAIN-002)** — sqlite-vec + fastembed local embedding index, `/brain` slash command + skill (`protocol/skills/brain.md`, `.claude/commands/brain.md`), brain-index-hook scripts (`scripts/brain-index-hook.{sh,ps1}`), and `scripts/brain.{sh,ps1}` CLI wrappers. The **engine** (`.protocol-state/brain/`) is tracked + shipped; only the runtime **data** (DB, memories, model cache, snapshots) lives in the external dir `%LOCALAPPDATA%/dzp-cortex/<install-id>/` and is never committed or shipped.
- **Cortex distro shipping + workflow integration (PATCH-BRAIN-002)** — engine added to the distro allowlist (Megumi-cleared); SEC-BRAIN-012 forbid-token tripwire; `dzp-publish.ps1` audit-gate hardening; Cortex Integration Contract + RECALL/REMEMBER/INDEX hooks across `ts.md`/`session.md`/`dzp-roe.md` + all slash-command launchers (54 files); DZP↔Cortex gap closures (README onboarding incl. auto-index hook setup, Toji snapshot via `/session end` export). The `SessionEnd` auto-index hook is documented in README and installed locally; `.claude/settings.json` is gitignored, so the hook is not committed/shipped — it is per-install setup.
- **Security remediation** — SEC-BRAIN-007 (.gitignore backstops for model cache + sqlite index) and SEC-BRAIN-008 (AWS `access_key_id`/`secret_access_key` patterns in `cortex/ingest.py`; GCP/Azure coverage logged as future sweep, not yet implemented) both @approved by Megumi. SEC-BRAIN-012 @approved. No P0/P1 findings unresolved.
- **Performance gate** — no-daemon CLI targets: `query`/`remember` <3s, full index ≤5min, incremental no-op <5s; all pass. (No "sub-500ms" gate — that earlier figure was a documentation error; sub-1s warm latency is deferred to a future daemon.)
- **Phase 10 agent doc blocks** — all 10 `protocol/*.agent.md` files received Cortex context blocks (Phase 10 of PLAN-BRAIN-002) explaining when/how to hand off to the brain.
- **`/session update` full-sync orchestrator + Cortex-in-sync** — plain `update` now runs: timestamp → full project-document sync (project-state.json, domain.record.md, dev-notes.md, security-review.md, secret-scan, backups) → mandatory incremental Cortex re-index (fail-soft). `update --time-only` preserves the fast path. `/session end` triggers a full Cortex rebuild. Implemented via `_sync_cortex_index` / `_cli_update` in `session_monitor.py`.
- **Cortex pointer banners** — top + footer banners added to the 3 protected project documents and their 3 distro templates so fresh installs inherit Cortex workflow guidance.
- **Security hardening P3 (Snyk python/PT triage, Megumi @approved)** — 24 path-traversal findings reviewed: 21 false-positive (owner-supplied CLIs), 3 P3 defense-in-depth remediated: SEC-BRAIN-009 (`brain.py` snapshot `--out` confinement), SEC-SCRIPT-001 (`dependency-scanner.py` `--export` confinement), SEC-SCRIPT-002 (`assert_version.py` `--root` DZP-marker check). 0 true-positive. SEC-DOC-001 (`sync --time-only` → `update --time-only` doc correction) also applied.
- **Distro publication status** — test gate CLEARED (Cortex functionally tested by owner). `DZP-v9.1.0` publish branch created and committed locally via `dzp-publish.ps1 -ForceClean -NoPush`; not yet pushed to the public canonical. Public push pending explicit owner go-ahead. Distro dry-run passes all gates.

### Why MINOR
New feature addition (Cortex) with full backward compatibility; no breaking protocol changes; existing installations unaffected unless they opt in.

---

## Previous Release — v9.0.0 (MAJOR)

**Version:** v9.0.0
**Release Date:** 2026-06-13
**Release Type:** MAJOR Release (Distribution Architecture + Version Reconciliation)

---

## Release Summary — v9.0.0 (MAJOR)

v9.0.0 is a **structural release and version reconciliation**. It introduces the **Distro Publish Architecture** (a fundamental change to how DZP is distributed) and consolidates a backlog of un-versioned / under-documented work accumulated since v8.12.0.

### Headline changes
- **Distro Publish Architecture (PATCH-DISTRO-001)** — clean dev/distribution split: production files publish to the canonical GitHub repo via an orphan `release` branch checked out as a `distro/` git worktree, driven by an allowlist `dzp-publish` script. The dev workspace never reaches canonical. Includes identity scrub, **content-level PII scrub + audit** (personal email/name/local-path removal, fail-loud), a forbidden-path audit, and a hard version-consistency assertion now covering `project-state.json` (closes report ISSUE-DZP-006/007).
- **PATCH-TOJI-001 (CRITICAL)** — fixed the Toji External Auditor fabrication defect (ISSUE-DZP-001): rebound Toji from the non-binding `vscode/*` toolset to real Claude Code tools (report-only), added anti-fabrication constraints + tripwire, and registered Toji in the runtime `agent_registry` (ISSUE-DZP-003). Toji file → v1.2.1.
- **Version reconciliation** — re-stamped all version-bearing files + all 10 agent definitions to v9.0.0; caught the `project-state.json` straggler (was lagging at 8.12.0); folded in the previously under-documented **v8.13.0** body (Toji 10th agent, Session Monitoring Enhancement PATCH-SESSION-004/005/006, State Consolidation PATCH-STATE-001).

### Why MAJOR
The distribution-model change (repo↔canonical relationship, dev/distro separation, orphan `release` branch) is a fundamental protocol restructuring under the semver policy. v9.0.0 establishes a clean, fully-stamped baseline after version/tag drift (git tags had stopped at v8.3.0; `project-state.json` had lagged two minors).

> Deferred to **v9.1.0**: DZP Cortex (local semantic-memory "separate brain") — built and tested in dev, excluded from distribution until shipped.

---

## Previous Releases (v8.12.0 – v8.13.0)

This release closes a critical session monitoring coverage gap (70-85% → 85-90%) identified through adversarial analysis. PATCH-SESSION-004 implements 5 defensive layers to prevent context compaction and agent bypass from disabling safety systems.

**Additional Patches (2025-12-31):**
- **PATCH-SESSION-005-v2**: Critical bug fix restoring user safety systems (3 stale timestamp bugs) + state management extensions + Gojo permission system
- **PATCH-TS-001**: Unified troubleshooting session tracker with permanent historical analytics and tier effectiveness analysis

### Key Changes in v8.12.0

#### PATCH-SESSION-004 (Original Release - 2025-12-29)

- **Component 1: Configurable Debounce** - Adjustable alert frequency (15-60 min range) via protocol.config.yaml + CLI `--debounce` flag to prevent alert spam during rapid prototyping
- **Component 2: Compaction-Resistant Markers** - HTML comments protect AUTO-INVOKED section in gojo.agent.md from context compaction removal (5-10% coverage gap closed)
- **Component 3: Alert Tracking Dashboard** - `.protocol-state/session-monitoring-report.py` detects alert undercount and verifies AUTO-INVOKED section integrity
- **Component 4: Verification Script** - `scripts/verify-auto-invoked.py` for CI/CD validation (exit code 0/1) to prevent safety system removal
- **Component 5: Invocation Tracking** - Tracks agent bypass patterns (direct vs routed invocations) to detect 10-15% coverage gap from agent invocation without Gojo
- **Bug Fix: Windows Compatibility** - Replaced Unicode emojis with ASCII equivalents in session_monitor.py (20+ instances) for full Windows cmd support

#### PATCH-SESSION-005-v2 (2025-12-31) - P0-Critical User Safety Restoration

- **3 Critical Bugs Fixed** - All causing user safety system failures:
  1. `get_session_summary()` always displayed "0 minutes" for 15+ hour sessions (visibility failure)
  2. `_archive_session()` permanently stored "0 minutes" in historical data (data corruption)
  3. `should_block_operation()` NEVER blocked high-risk operations, even after 47+ hours (safety system complete failure)
- **Root Cause** - Methods read stale `metrics['total_duration_minutes']` from JSON instead of calculating live from timestamps
- **Fix** - Added `_calculate_current_duration()` and `_calculate_current_continuous_work()` helper methods (lines 942-995)
- **Extension 2: State Management** - 4 new methods to update project-state.json, dev-notes.md, domain.record.md on session events
- **Extension 3: Permission System** - Gojo-only access to domain.record.md via `DZP_AGENT=gojo` environment variable check
- **Files Modified** - session_monitor.py (+180 lines), session.md (updated with DZP_AGENT=gojo syntax)

#### PATCH-TS-001 (2025-12-31) - Unified Troubleshooting Tracker

- **Purpose** - Centralized tracking for all /ts tier commands with permanent historical analytics
- **Created** - troubleshooting_tracker.py (585 lines) with 6 commands: start, update, complete, escalate, status, stats
- **Key Features**:
  - Tier analysis: Success rates, average durations, escalation patterns per tier (1-5)
  - File frequency tracking: Identifies most commonly problematic files across sessions
  - Pattern recognition: Statistical analysis of tier effectiveness and escalation triggers
  - Permanent retention: All sessions kept indefinitely in troubleshooting-history.json
- **Integration** - Updated protocol/skills/ts.md with Step 0: Review historical stats before tier selection
- **Impact** - Data-driven tier selection, pattern learning, troubleshooting effectiveness tracking

#### PATCH-STATE-001 (2025-12-31) - State File Consolidation

- **Purpose** - Consolidate 4 fragmented state files into unified project-state.json with nested namespaces
- **Problem Solved** - Eliminated state fragmentation, tier statistics duplication, and race conditions across separate JSON files
- **Created** - ProjectStateManager class (788 lines) + migration script (494 lines) with automatic backups and rollback
- **Key Features**:
  - Nested namespace architecture: session_tracking, troubleshooting, tier_tracking, agent_invocation_tracking
  - Centralized state management with cross-platform file locking (Windows msvcrt + Unix fcntl)
  - Non-destructive migration with SHA-256 integrity verification and automatic rollback on failure
  - Backward compatibility via fallback to legacy files if consolidated state unavailable
  - Atomic write operations using tempfile pattern to prevent partial state corruption
- **Files Consolidated**:
  - session-state.json -> project-state.json::session_tracking
  - troubleshooting-history.json -> project-state.json::troubleshooting
  - agent-invocation-tracker.json -> project-state.json::agent_invocation_tracking
  - Deduplicated tier_usage_statistics + tier_statistics -> project-state.json::tier_tracking
- **Security** - 24 security issues identified by Megumi, 16 resolved by Sukuna including 3 P0 critical race conditions (SEC-016, SEC-019, SEC-024)
- **Performance** - P95 latency 8.44ms (23.7x better than 200ms target), 125 ops/sec throughput (12.5x better than target), 99%+ capacity headroom
- **UX** - 78/100 initial score improved to 85/100 after Priority 1 fixes (rollback documentation, actionable error messages, clear success output)
- **Testing** - 5-phase comprehensive testing (Unit, Integration, Edge Cases, E2E Workflows, Final Validation) with unanimous @approved from Megumi, Maki, and Nobara
- **Updated Scripts (8)** - session_monitor.py, troubleshooting_tracker.py, tier-statistics.py, tier-enforcement.py, gojo-learn.py, sukuna-learn.py, restore-snapshot.py, create-snapshot.py
- **Updated Documentation (5)** - session.md, ts.md, gojo.agent.md, AI_INSTRUCTIONS.md, CHANGELOG.md
- **Impact** - Single source of truth for all DZP state, eliminated data inconsistency, improved reliability with proper locking mechanisms

### Previous Release (v8.11.0)

- **Component 1: Session Management Skill** - 6 commands (`/session start|status|update|break|continue|end`) for unified work session lifecycle with checkpoint file syncing (dev-notes, project-state, domain.record, security-review, session-state)
- **Component 2: TS Troubleshooting Tier System** - 9 commands across 5-tier hybrid bug resolution workflow with auto-escalation (`/ts_tier1|tier2|tier3|tier4|codered|status|history|escalate|complete`)
- **Component 3: DZP ROE v2.0.0** - 40% size reduction (510→306 lines), streamlined to 5-step workflow with parallel enforcement, anti-pattern examples
- **Component 4: State Schema Updates** - Added troubleshooting_session and troubleshooting_statistics to project-state.json, new troubleshooting-history.json for session archival
- **Component 5: Skill Registry Update** - SKILL_REGISTRY.md v3.0.0 → v3.2.0 with session and ts skills (both Gojo-owned with domain.record.md write access)

### Previous Release (v8.9.0)

- **Component 1: Claude Skills Integration** - 16 Anthropic skills (pdf, docx, xlsx, pptx, frontend-design, web-artifacts-builder, webapp-testing, mcp-builder, skill-creator, brand-guidelines, canvas-design, doc-coauthoring, internal-comms, theme-factory, algorithmic-art, slack-gif-creator) mapped to all 9 agents
- **Component 2: Implementation Restrictions** - Nobara, Todo, Maki, Panda, Inumaki now route all code implementation through Yuuji; edit/bash tools removed from these agents
- **Component 3: File Rotation System** - scripts/file-rotate.py for dev-notes.md and security-review.md rotation at 25k character threshold
- **Component 4: OWASP Cheatsheet Integration** - Megumi updated with comprehensive OWASP Cheatsheet Series references (Tier 1/2/3 organization)
- **Updated Skill Registry** - SKILL_REGISTRY.md and AGENT_SKILLS_MAP.yaml v3 with complete skill mappings

### Previous Release (v8.8.0)

- **Component 1: Tier Validation System** - Active pwd verification, tier-defaults.yaml (18KB config), all 9 agents updated with tier validation sections, 30-day backward compatibility grace period
- **Component 2: Tier Statistics** - Automatic tier usage tracking, compliance monitoring, markdown/JSON reporting for Trigger 19 integration
- **Component 3: Dual Learning Systems** - Sukuna learns from protocol updates, Gojo learns from tier selections, comprehensive USER + PROJECT protection, opt-in by default
- **Comprehensive Safety** - Kill Switch integration, sanitized data, project isolation, confidence thresholds (80%+, 3+ samples), instant disable capability
- **Migration Guide** - 500+ line MIGRATION_v8.7_to_v8.8.md with step-by-step upgrade instructions

### Previous Release (v8.7.0)

- **Custom Agent Security Framework** - Pre-invocation validation (440 lines), runtime monitoring (650+ lines), audit logging, and registry system
- **8 Critical Vulnerabilities Fixed** - Agent name collision, self-declared tool permissions, YAML injection, agent self-modification, zero Gojo oversight, rate limiting, file immutability
- **Comprehensive Test Coverage** - 60+ test cases for session monitoring, 110+ tests total for security features
- **Agent Banner Compliance** - Fixed emoji consistency and added missing banner for Sukuna (protocol/AGENT_SELF_IDENTIFICATION_STANDARD.md compliance)

### Previous Release (v8.6.0)

- **Nine-Agent System** - Sukuna formalized as the 9th agent; all documentation updated from "eight-agent" to "nine-agent"
- **Full Documentation Update** - README, FAQ, PROTOCOL_QUICKSTART, VERSION, CLAUDE.md, gojo.agent.md all reflect 9-agent architecture
- **Distribution Update** - core-files-v8.5.1/ updated to core-files-v8.6.0/ standard

### Previous Release (v8.5.1)

- **Sukuna System Update Adversary** - Ryomen Sukuna integrated as adversarial-but-aligned system update specialist, invocable only via Gojo or User
- **Cross-Agent Edit Restrictions** - Non-Gojo agents now have READ-ONLY access to all `.agent.md` files; changes require User or Gojo authorization
- **JJK Character Reference** - Full Sukuna character reference added to `.protocol-state/jjk-character-reference/`
- **Slash Command Rename** - `/system-update` renamed to `/sukuna` with JJK character integration
- **Work Session Management** - Enhanced enforcement across all agents
- **Gojo Template Extraction** - Extracted OUTPUT TEMPLATES to `.protocol-state/gojo-templates/OUTPUT_TEMPLATES.md` (~9% size reduction)

### Previous Release (v8.5.0)

- **Kill Switch Protocol** - Emergency stop mechanism with immediate halt, checkpoint creation, and project protection
- **User Technical Level System** - Beginner/Intermediate/Expert modes that adapt agent communication style
- **Gojo Mission Control Option 4** - New "Resume from Emergency Stop" option for checkpoint recovery

### Previous Release (v8.4.1)

- **Agent File Cleanup** - Removed verbose Gojo Awareness sections for cleaner separation of concerns
- **JJK Character References** - Added character context sections to all 9 agent files
- **Research Mode Expansion** - Updated to support all 9 agents with role-specific research focus

---

## What's New in v8.4.1

### Changed

#### 1. **Agent File Cleanup**

Removed verbose "Gojo Awareness" sections from all non-Gojo agent files:
- `protocol/yuuji.agent.md` - Replaced with concise "Mission Control: Gojo" reference
- `protocol/megumi.agent.md` - Replaced with concise "Mission Control: Gojo" reference
- `protocol/nobara.agent.md` - Replaced with concise "Mission Control: Gojo" reference
- `protocol/todo.agent.md` - Added "Mission Control: Gojo" reference
- `protocol/maki.agent.md` - Added "Mission Control: Gojo" reference
- `protocol/panda.agent.md` - Added "Mission Control: Gojo" reference
- `protocol/inumaki.agent.md` - Added "Mission Control: Gojo" reference

#### 2. **JJK Character Reference Additions**

Added character context sections to all 9 agent files linking to:
- Canon series information (Jujutsu Kaisen)
- Character wiki references
- Cursed technique mappings to agent specializations
- Domain expansion parallels

#### 3. **Research Mode Expansion**

Updated `protocol/RESEARCH_MODE.md` to support all 9 agents:
- Added role-specific research focus for Extended Four agents
- Defined operational cadences per agent type
- Integrated staleness monitoring for all agents

#### 4. **Handoff Specification Updates**

Updated `protocol/HANDOFF_SPECIFICATION.md`:
- Changed example handoffs from `mission_control` to `gojo` for schema compliance
- Ensured all agent identifiers match JSON schema enum

---

## Files Modified

**Protocol Agent Files (8 files):**
- `protocol/gojo.agent.md` - JJK Character Reference added
- `protocol/yuuji.agent.md` - Gojo Awareness cleanup, JJK Character Reference added
- `protocol/megumi.agent.md` - Gojo Awareness cleanup, JJK Character Reference added
- `protocol/nobara.agent.md` - Gojo Awareness cleanup, JJK Character Reference added
- `protocol/todo.agent.md` - Mission Control reference, JJK Character Reference added
- `protocol/maki.agent.md` - Mission Control reference, JJK Character Reference added
- `protocol/panda.agent.md` - Mission Control reference, JJK Character Reference added
- `protocol/inumaki.agent.md` - Mission Control reference, JJK Character Reference added

**Core Protocol Files:**
- `protocol/CLAUDE.md` - Updated to 9-agent system, new invocations
- `protocol/gojo.agent.md` - Domain supervision for all 9 agents
- `protocol/yuuji.agent.md` - Version sync to 8.4.1
- `protocol/megumi.agent.md` - Version sync to 8.4.1
- `protocol/nobara.agent.md` - Version sync to 8.4.1

**Configuration:**
- `protocol.config.yaml` - Added 4 new agent configurations
- `protocol/skills/AGENT_SKILLS_MAP.yaml` - Extended with new agent skills

**State:**
- `.protocol-state/project-state.json` - Version 8.4.1

---

## Configuration

No new configuration required. All changes are backward compatible.

**New Agent Invocations:**
```bash
# Todo - Database & Backend
"Read protocol/todo.agent.md and design database schema for [feature]"

# Maki - Performance
"Read protocol/maki.agent.md and optimize [component/page]"

# Panda - Build & Integration
"Read protocol/panda.agent.md and configure CI/CD for [project]"

# Inumaki - API & Communication
"Read protocol/inumaki.agent.md and design API for [feature]"
```

---

## Upgrade Notes

### For Existing Users

**No Action Required:**
- All changes are backward compatible
- Existing four-agent workflows unchanged
- New agents are optional extensions

**Optional: Use Extended Agents:**
```bash
# Database design
"Read protocol/todo.agent.md and design schema for user management"

# Performance optimization
"Read protocol/maki.agent.md and run Lighthouse audit"

# CI/CD setup
"Read protocol/panda.agent.md and create GitHub Actions workflow"

# API design
"Read protocol/inumaki.agent.md and design REST API for orders"
```

### For New Users

1. Review `IMPLEMENTATION_GUIDE.md` for agent overview
2. Start with core four agents (Gojo, Yuuji, Megumi, Nobara)
3. Add extended agents as needed for specialized tasks

---

## Key Principles Established

1. **Nine-agent system** - Specialized expertise across all development domains
2. **Consistent format** - All agents use .agent.md with YAML frontmatter
3. **Domain supervision** - Gojo coordinates all agents with declarative handoffs
4. **Escape paths** - All agents have fallback patterns (never hang)
5. **Skill assignments** - Each agent has specialized skills in AGENT_SKILLS_MAP.yaml

---

## Breaking Changes

**None.** This is a backward-compatible patch release.

---

## Documentation

**Agent Files:**
- `protocol/todo.agent.md` - Database & Backend Specialist
- `protocol/maki.agent.md` - Performance Optimization Specialist
- `protocol/panda.agent.md` - Build & Integration Specialist
- `protocol/inumaki.agent.md` - API & Communication Specialist

**Updated Files:**
- `protocol/CLAUDE.md` - System overview with 9 agents
- `protocol/gojo.agent.md` - Domain supervision diagram

**Skills:**
- `protocol/skills/AGENT_SKILLS_MAP.yaml` - Agent-skill mapping

---

## Known Issues

**None identified.**

---

## Contributors

- Domain Zero Protocol Team
- Claude Code

---

**Previous Version:** v8.3.1 (Agent-Specific Escape Paths)
**Next Planned:** TBD (See roadmap in README.md)
