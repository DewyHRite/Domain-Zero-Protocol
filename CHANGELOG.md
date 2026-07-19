# Changelog - Domain Zero Protocol

All notable changes to the Domain Zero Protocol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Released]

## [9.10.0] - 2026-07-18

### MINOR — FEAT-IDGOV-001 Issue-ID Governance System + IMPL-001 version-cascade closure + BUGREPORT-009 stamp-linter coverage

#### Added
- **`FEAT-IDGOV-001`** (Issue-ID Governance System) — all-families append-only JSONL registry
  (`.protocol-state/issue-registry.jsonl`) + shared minting/validation engine (`scripts/idgov/`) +
  fail-closed full-mediation pre-commit/CI gate (`scripts/check_issue_ids.py`: mint-before-cite,
  malformed-id hard block, documented prose escapes, E5 digit-gate). Megumi `secid` tool
  (`protocol/skills/megumi-secid.md`, mediated signed-wrapper execution per the Phase D9
  Sukuna-adversarial review). Non-destructive 1,229-row historical backfill
  (`scripts/backfill_issue_registry.py`; 266 collision groups; `SEC-001` alone reused 76×). Cortex
  fail-soft registry advisory. Gate ACTIVE with a 6th independent override,
  `DZP_ALLOW_MISSING_ISSUE_ID_GATE`. Yuuji TDD + Megumi Tier-3 @approved every phase (P0
  `SEC-IDGOV-F-001` legacy mint-and-cite bypass caught + structurally closed); Sukuna-led adversarial
  Phase H; Toji full audit 2026-07-18 (13 findings; remediation scheduled, not part of this release).
  Provenance: `audits/2026-07-13-sukuna-secid-governance-review.md`.
- **`BUGREPORT-009`** — `scripts/distro/check_version_stamps.py` Type 8 check for the root `dzp.py`
  module-docstring `Domain Zero Protocol vX.Y.Z` stamp (previously had zero linter coverage; had
  already drifted silently once, corrected in v9.9.5). Yuuji TDD (positive + negative regression).

#### Fixed
- **`IMPL-001`** — closed the un-cascaded v9.9.7 version drift (flagged in the Toji audit trail as
  permanently mis-stamping append-only registry rows). Full repo-wide stamp cascade to v9.10.0 across
  protocol files, docs, agent frontmatter, hooks, `AI_INSTRUCTIONS.md`, `dzp.py`, and state; historical/
  changelog references deliberately preserved. `.protocol-state/create-snapshot.py`'s hardcoded
  `protocol_version: "8.8.0"` snapshot-body literal (frozen since the script's v8.8.0 introduction, never
  updated on any subsequent release) is now read dynamically from `VERSION.md`, mirroring the reviewed
  `scripts/issue_id.py::_protocol_version()` pattern.

#### Notes
- Sukuna-implemented (System Update Adversary), Gojo-coordinated, USER-approved. Full verification
  suite green: `assert_version.py`, `check_version_stamps.py` (1 pre-existing, out-of-scope, report-only
  residual — see the version-cascade-trap lesson below), `validate-protocol.py --check`.
- **Adversarial observation (report-only, not fixed this release)**: `check_version_stamps.py` does not
  exclude `audits/**` the way it excludes the 3 FEAT-GUARD-001 protected records, so
  `audits/2026-07-13-sukuna-secid-governance-review.md`'s live-looking `[CORE FILE]` header will
  re-flag as stale on every future cascade. Recommend adding `audits/` to the linter's exclusion list
  in a follow-up change, since that document is a historical, append-only artifact and must not be
  rewritten to chase the current version.

## [9.9.7] - 2026-07-13

### PATCH — BUG-CORTEX-008 R3 durable session-end fix (supersedes R1) + dirty-source publish guard

#### Fixed
- **`BUG-CORTEX-008` R3** (durable fix) — root-caused the chronic Cortex session-end timeout to the
  SYNCHRONOUS full `--level high` re-embed + `export --snapshot` landing on top of the session's
  largest embedding-delta cost (content-addressed storage cost is delta-bound, not corpus-size-bound,
  correcting R1's assumption). `session-end` now runs `cortex-medium` (`--level medium`, incremental,
  no export, 90s) instead of `cortex-high` — fast and stays fail-soft. New manual/periodic event
  `cortex-rebuild-full` (`python dzp.py event cortex-rebuild-full`) carries the full `--level high` +
  export off the critical path (no daemon — DZP remains no-daemon by design). The other 4 `cortex-high`
  steps (`pre-release`, `pre-publish`, `post-migration`, `post-rotation`) are unchanged and remain real
  gates. `cortex_trigger.py` unaffected (medium+export already supported). Docs updated:
  `protocol/skills/session.md` (incl. a `toji-snapshot` event pointer, closes SEC-CORTEX-R3-001),
  session-end docs, `README.md`, `docs/guides/DZP_CORTEX.md`, `AI_INSTRUCTIONS.md`.
- **`BUG-CORTEX-008` R1** (stopgap, folded in) — raised `timeout_seconds` 180→300 on all 5
  `cortex-high` orchestration steps; the other 4 non-session-end steps keep this 300s under R3.
- **`BUG-DISTRO-DIRTY-SOURCE-001`** (maintainer tooling) — `dzp-publish` staged `distro/` by copying
  the dev source tree from disk, never from git, so a dirty working tree could silently ship
  uncommitted content publicly. Adds a fail-closed `dev_source_dirty_offenders()` guard
  (`git status --porcelain=v1 -z`, scoped to the same manifest-staged paths) that aborts the publish
  on any genuinely dirty manifest-shippable path. `DZP_ALLOW_DIRTY_SOURCE=1` is a loud, non-silent
  override (confirmed-clean-dirt only, rc==1); a git-execution failure (rc==2) hard-fails and is NOT
  overridable. POSIX + PowerShell parity; `docs/guides/DISTRO_RELEASE_WORKFLOW.md` §4a documents it.
  Closes SEC-DISTRO-DIRTY-001 (P2, gitignore-source scope gap), -002 (P3, `-z` path parsing), -003
  (P3, override-vs-execution-failure separation).

#### Notes
- Yuuji TDD throughout (Cortex R3 doc/config regression coverage; 17 dirty-source guard + 125 distro
  suite tests green); Megumi Tier-2/Tier-3 @approved both items; Sukuna-implemented, Gojo-verified.
- **Same-session governance note:** a Sukuna SEC-ID governance self-review was conducted this session
  (`audits/2026-07-13-sukuna-secid-governance-review.md`, report-only); its formal issue-tracker
  remediation is scheduled for **v9.9.8** and is explicitly NOT part of this release's code changes.

## [9.9.6] - 2026-07-11

### PATCH — Sukuna adversarial bug-hunt remediation (5 P1s closed)

#### Fixed
- **`BUG-HOOK-SELF-DISARM-001`** (P1) — the security-gate ENGINE scripts
  (`scan_protected_records.py`, `check_protected_append_only.py`, `validate-protocol.py`,
  `check_branch_record_isolation.py`, `distro/assert_version.py`, `distro/check_version_stamps.py`)
  are now themselves listed in `immutable_paths` (a prior hardening pass protected only the hook
  wrapper scripts, leaving the on-disk scanner engines free for an unprivileged commit to neuter or
  `git rm`). The stage-3 append-only guard now fails CLOSED on a missing guard file, with a new
  break-glass `DZP_ALLOW_MISSING_APPEND_GUARD` override (always printed loud); the `DEFAULT_PATHS`
  fallback brought to parity.
- **`BUG-RESTORE-CHECKSUM-NOOP-001`** (P1) — `restore-snapshot.py` now actually compares the
  snapshot checksum against a recompute of the pre-image (previously computed but never compared,
  with a hardcoded "verified" banner regardless of match). Verify-before-write is fail-closed;
  `--force-unverified` remains as an explicit break-glass.
- **`BUG-CORTEX-ESCROW-HOLLOW-001`** + **`-RAISE-002`** (P1 ×2) — `cortex/memory_export.py`'s
  key-recovery escrow capture re-pointed at the real content-addressed store
  (`content_refs ⋈ content WHERE source_type='memory'`); the phantom `cortex_memories` table and
  `cortex_entities.source` column it previously queried never existed on a real `Store` brain, so
  escrow silently captured 0 memories (or hard-raised) on every genuine installation since v9.9.0.
  Restore uses the production upsert path. The masking test fixtures that fabricated the phantom
  table were de-fabricated onto real `Store` brains.
- **`BUG-DISTRO-PII-LEAK-001`** (P1) — publish `content_audit` now scans every staged file
  regardless of extension, with a known-encoding→`latin-1` fallback (UTF-16 was previously skipped
  entirely) and `IGNORECASE` matching; `_IGNORE_COPY` extended to editor/merge junk (`.orig`, `.rej`,
  `.swp`, `.swo`, `.tmp`, `~`, `.DS_Store`, `Thumbs.db`).

#### Notes
- Provenance: Sukuna 4-front adversarial bug hunt, externally audited by Toji
  (`audits/2026-07-11-toji-sukuna-bughunt-report.md`, Rev 2). Each fix ships with its
  repro converted to a committed regression test. New tests: hook self-disarm 14, restore-checksum
  14 (+4 preview-display regression tests, CodeRabbit PR #110), escrow 3 new + 4 de-fabricated
  suites, distro PII-leak gate 8. Yuuji TDD + Megumi Tier-3 @approved.
- **Accepted P3 residuals:** `.protocol-state/attestation.py` not yet in `immutable_paths` (bounded,
  non-blocking); content-audit substring boundary vs binary/compressed blobs (moot — no binary
  assets ship).
- **Deferred:** 6 P2 + ~12 P3 findings from the same bug-hunt report are not part of this release.

## [9.9.5] - 2026-07-11

### PATCH — Cortex ingest secret-detector false-positive/observability remediation + scanner reconciliation + publish-manifest gap closure + same-day Toji-audit remediation + RHS snapshot P1 port

#### Fixed
- **`BUG-CORTEX-INGEST-SECRET-FP-001`** (Cortex ingest secret-detector, ported byte-identical from
  a Megumi-@approved downstream fix) — **SEC-DZPUP-9.9.4-010** (heuristic drift) CLOSED:
  `cortex/ingest.py::_is_placeholder_value` gains a bounded, closed-vocabulary exact-match
  type-annotation recognizer (19 TS/JSON-schema tokens, fullmatch only) instead of widening the
  substring-matched placeholder-word list, which would have masked any value merely *containing* a
  type word (e.g. `password: correcthorse_string_x9`). **SEC-DZPUP-9.9.4-012** (all-or-nothing drop)
  CLOSED: the secret gate in `chunk_file()` is now per-chunk, not whole-file — a single
  secret-shaped chunk is redacted while sibling chunks in the same document survive (previously a
  confirmed regression silently reverted an earlier fix and discarded entire legitimate documents
  over a handful of false-positive lines). **SEC-DZPUP-9.9.4-011** (silent failure) CLOSED:
  `index()` now returns `files_dropped_secret`/`chunks_dropped_secret` counters and emits an
  unconditional `[cortex:ingest] REDACT ...` stderr line per dropped chunk. **SEC-DZPUP-9.9.4-013**
  CLOSED: restored the SEC-CORTEX-006 injection-detection pattern set from a silently-reverted
  3-pattern list back to the full 6.
- **Scanner `-005`/`-010` reconciliation** — `scripts/scan_protected_records.py` had independently
  "fixed" the identical type-annotation false-positive class via an unsafe substring-word approach
  (SEC-DZPUP-9.9.4-005). Moved onto the same closed-vocabulary exact-match recognizer as
  `cortex/ingest.py`, plus ported the scanner's own `-006`/`-007`/`-008` value-side hardening
  (semver recognizer, length-capped ellipsis recognizer, widened trailing-punctuation strip) that
  had never reached canonical. `SECRET_FORMAT_PATTERNS` and the secret-keyword regex are untouched
  in both files (value-side fixes only).
- **Publish-manifest gap** — `scripts/scan_protected_records.py`,
  `scripts/check_branch_record_isolation.py`, and `.github/secret_scanning.yml` existed in the
  v9.9.4 canonical working tree and were described in the v9.9.4 changelog, but were never added to
  `scripts/distro/publish-manifest.yaml` — every published `DZP-v9.9.4` distro branch shipped
  **without** the SEC-001 protected-records secret scanner. Independently confirmed by two
  downstream reports. All three files added to the manifest.
- **`scripts/git-hooks/pre-commit`** (POSIX) hardened with the missing-scanner `else` warning
  branch that the `.ps1` template already had (a missing scanner previously no-op'd the scan gate
  silently).
- **`dzp.py`** — stale "Domain Zero Protocol v9.4.0" banner (2 stamps) corrected.

#### Added
- **`tests/test_type_annotation_vocab_parity.py`** — structural test guarding the two independent
  secret-detectors' closed-vocabulary token sets against future drift.

#### Notes
- Yuuji TDD (41 new Cortex regression/observability/adversarial-bypass tests + 2 cross-detector
  vocab-parity tests, all green; 20 pre-existing scanner tests + 225 pre-existing brain/cortex tests
  unaffected). Megumi Tier-3 security-review handoff prepared for the base patch above.
- Public re-publish to `DZP-v9.9.5` is a separate, later, USER-authorized step — not part of this
  patch.

### Same-day addendum (2026-07-11) — Toji-audit v9.9.5 remediation + RHS snapshot P1 port

A same-day Toji audit of this v9.9.5 workflow (`audits/2026-07-11-toji-gojo-v9-9-5-workflow.md`; 2
MEDIUM findings, 0 Critical/High) plus a downstream RHS bug-report port are folded into this same
patch (no version bump).

#### Fixed
- **CODE-001** (MED, Code Quality) — `.protocol-state/brain/cortex/ingest.py::index()` telemetry
  was misleadingly named: `files_dropped_secret` incremented for any file with at least one
  redacted chunk, even when clean sibling chunks remained indexed. Added accurately-scoped
  `files_with_secret_redactions` (≥1 chunk redacted) and `files_fully_omitted_secret` (strict
  subset — zero chunks remain indexed); `files_dropped_secret` retained as a back-compat alias.
- **SEC-001** (MED, CWE-184) — the SemVer placeholder recognizer added to
  `scripts/scan_protected_records.py` in the base patch above admitted disguised secret entropy
  shaped like a version string. Closed across five adversarial review cycles
  (`SEC-DZPUP-9.9.5-SEMVER-MONOCASE-001`/`-CHAIN-001`/`-DIGITCHAIN-001`/`-DUALCOMPONENT-001`/`-CORE-001`,
  all CLOSED) to a single unified whole-value entropy budget (19 characters) across
  core+prerelease+build, with a regex-level 8-digit core cap and a 9-word qualifier allowlist;
  CalVer-safe. Supersedes the prior accepted `SEC-DZPUP-9.9.5-SEMVER-CAP` residual.
- **`BUG-SNAPSHOT-NULLFIELDS-001`** (P1, RHS-report port) — `.protocol-state/create-snapshot.py`
  now emits a `reason` field (retaining legacy `trigger`) and includes `metadata.description` only
  when a real string is supplied; previously null/missing fields failed the fail-CLOSED
  commit-gate schema and silently blocked all commits.
- **MF-1** (P1, Megumi, RHS-report port) — the `reason` enum in
  `protocol/validation-rules.yaml` (both `snapshot` and `snapshot-manifest` schemas) widened to add
  `pre-protected-edit`, `toji-snapshot`, `pre_restore_backup`; `create-snapshot.py` gained a
  `VALID_TRIGGERS` allowlist plus an `argparse choices=` guard. Pre-existing stale live snapshot
  body hand-repaired to match; `scripts/validate-protocol.py --check` now passes 13/13.

#### Added
- **FEAT-REQ-002** — `DZP_ALLOW_PROTOCOL_EDIT=1`, a scoped per-invocation env override for the
  FEAT-REQ-001 Cross-Agent Edit Restrictions protected-path pre-commit stage, mirroring the
  existing `DZP_ALLOW_PROTECTED_REWRITE` (FEAT-GUARD-001). Lets a Gojo/USER-authorized protocol
  change commit without `git commit --no-verify`, bypassing ONLY that stage while the SEC-001
  secret scan, the FEAT-GUARD-001 append-only guard, and `validate-protocol.py --check` all remain
  active. Loud, unconditional, never-silent stderr warning; non-persistent; exact-match `=1`
  trigger; POSIX + PowerShell hook parity; documented `override_env` key in
  `protocol.config.yaml`. Yuuji TDD (6 real-subprocess hook tests); Megumi Tier-3 @approved — a net
  security improvement over the `--no-verify` it replaces for authorized edits, 0 must-fix.

#### Notes
- **Accepted P3 residual:** an irreducible ≤19-char sub-cap entropy channel in the SemVer
  recognizer, pinned by the real committed fixture `1.2.3-1+a1b2c3d.20260315` (exactly 19 chars,
  zero slack). Two non-blocking usability notes: `v`-prefixed versions and >8-digit numeric cores
  now fail safe (flagged; resolvable via the existing allowlist).
- **Flagged follow-up, not fixed:** a dead `pre_restore_backup` call site in `restore-snapshot.py`
  imports `create_snapshot` via a non-existent module path (silently swallowed by a broad
  `except`).
- Yuuji TDD (SemVer hardening: 163 passing on the required suites / 548 broader, zero regressions;
  snapshot gate-validation: 18/18). Megumi Tier-3 (SemVer) / Tier-2 (snapshot) @approved every
  phase.
- Not yet committed at the time of this entry — commit is pending explicit USER authorization.

## [9.9.4] - 2026-07-09

### PATCH — Toji external-auditor capability upgrade + Toji-audit-2026-07-09 remediation + Sukuna RHS-report canonical items

#### Added
- **Toji v1.3.0 (external auditor)** — standing (always) read across all Domain Zero records; a
  scoped `edit` tool that may append exactly one signed Record Log Entry stub per audit to the two
  FEAT-GUARD-001-enforced protected records (`.protocol-state/dev-notes.md`,
  `.protocol-state/security-review.md`); full audit reports now written to a new `audits/` folder
  (naming convention `audits/YYYY-MM-DD-toji-<scope>.md`; 2 existing reports migrated out of
  `.protocol-state/toji-reports/`, which now carries a pointer `README.md`).
  `.dzp-domain/domain.record.md` is gitignored and outside FEAT-GUARD-001's coverage, so Toji never
  writes it directly — Gojo logs the equivalent stub there on Toji's behalf. CONSTRAINT_012 revised
  to reflect the append-only-but-scoped write. Tool-access matrices updated across root + protocol +
  global `CLAUDE.md`, the `~/.claude/agents/toji.md` runtime stub, `AI_INSTRUCTIONS.md`, and
  `.github/copilot-instructions.md`. Megumi Tier-3 @approved (SEC-TOJI-101/102/103 closed).
- **`scripts/scan_protected_records.py`** (SEC-001, MED) — compensating secret scanner for the three
  protected records; allowlists only the one known historical Stripe docs-example literal in
  `dev-notes.md`, fails closed on any other match. Wired into pre-commit + CI.
- **`scripts/check_branch_record_isolation.py`** (part of IMPL-001) — append-only-vs-merge-base and
  conflicting-terminal-records detector for the protected records across branches.
- **`.protocol-state/attestation.py`** (ISS-083, P3) — authorized-writer attestation: a side-channel
  HMAC ledger with a monotonic sequence number; sanctioned state writers are stamped on write;
  `validate-protocol --check` suppresses drift alerts for attested writes and alerts on
  unattested/forged/stale ones. Non-blocking. Windows owner-only ACL on the HMAC key. Local-integrity
  threat model documented (not tamper-proof against a fully compromised local account).

#### Fixed
- **IMPL-001** (MED, Toji audit 2026-07-09) — signed session-record reconciliation for
  `session_20260707_203626`, appended to `dev-notes.md`/`security-review.md` with authoritative
  values sourced from `project-state.json`; the parallel program-L record was ruled non-authoritative
  for this session and a domain-record correction was logged. Program-L reconciliation itself is
  deferred pending a separate USER decision.
- **ISS-084/085** (P2, Sukuna RHS report) — root `dzp.py` added to the publish manifest and the
  orchestration-trio publish-manifest-completeness gate (Scope 5), closing a gap where the root
  entry-point could ship without its coordinator dependencies.

#### Notes
- **ISS-086** (P3, Sukuna RHS report) — no canonical target exists for this item (it concerns the
  install-side `dzp-sync` tooling, which is intentionally out of canonical scope); remains
  REPORT-ONLY.
- Accepted P3 residuals: **SEC-IMPL-001-RESIDUAL** (branch-isolation check's Layer-2 detector is
  fail-soft, not fail-closed) and the attestation subsystem's inherent local-integrity boundary
  (same-user-account threat model; no protection against a fully compromised OS account).
- Yuuji TDD throughout; Megumi Tier-3 @approved every phase.

#### Tests
- New: `tests/` coverage for attestation (55), distro publish-manifest completeness (11), the
  protected-records secret scanner (20), branch-record isolation (21), and the extended
  protected-append-only guard (46).

## [9.8.2] - 2026-06-23

### PATCH — cp1252 coordinator UTF-8 capture fix (Windows `/session update`)

#### Fixed
- **Windows `UnicodeDecodeError`/`UnicodeEncodeError` in `.protocol-state/script_coordinator.py`**:
  `_run_step()` did not force UTF-8 on the subprocess capture path, so any coordinator step that
  emitted non-ASCII output (e.g. `custom_agent_monitor.py --list` printing `✅`) raised an
  encoding error on Windows cp1252 consoles. The step was then reported as `failure` even though
  it completed successfully. Fix: `PYTHONUTF8=1` injected into the child environment and
  `subprocess.run(…, encoding="utf-8", errors="replace")` used for capture. Fail-soft (did not
  block the overall `/session update` sync); low severity for single-user installs. Affects
  Windows consumers only; Linux/macOS unaffected. Consumer-facing via `/session update`.
- Other commits on this branch (session-update churn `804d8b1`, validation-baseline refresh
  `d7adf8f`) are dev-state housekeeping, not consumer content changes.

#### Tests
- No new test file (coordinator test infra is dev-only / distro-excluded); the fix is a
  targeted env+encoding change verified manually on Windows.

## [9.8.1] - 2026-06-23

### PATCH — BUG-CORTEX-ENC-UV-001: Encryption migration user_version preservation

#### Fixed
- **BUG-CORTEX-ENC-UV-001**: The v9.8.0 encryption migration (`migrate_cortex_encrypt_9_8.py`)
  silently shipped broken — SQLCipher `sqlcipher_export()` drops `PRAGMA user_version`, so an
  encrypted brain surfaced `availability: unavailable` (`user_version=0` vs
  `metadata.schema_version=4` → SEC-ACCESS-010 schema-guard fail-closed) despite all data being
  intact. Any public v9.8.0 consumer who enabled encryption would hit this on every startup after
  migration. Fix: `encrypt_brain()` and `decrypt_brain()` now capture the source
  `PRAGMA user_version` and restore it on the destination before verification; the migration
  smoke-verify step ABORTS if the post-migration `user_version` does not match the source.
  Shipped silently broken in public v9.8.0; no data loss, but the encrypted brain was effectively
  unusable until rollback or manual `PRAGMA user_version` repair. Yuuji TDD: 11/11 migration
  tests pass.

#### Tests
- 11/11 `tests/brain/test_migrate_encrypt_9_8.py` assertions pass (user_version round-trip
  verified for both encrypt and decrypt paths).

#### Notes
- Other commits on this branch (`008d73f` distro neutralizer, `2fc143a` recovery-design docs,
  `5139e44` local brain.config.yaml enable) are maintainer-tooling / distro-excluded / not
  consumer-facing content changes.

## [9.8.0] - 2026-06-22

### MINOR — Cortex Encryption-at-Rest (PLAN-CORTEX-ENC-001) + v9.7.2 upstream-upgrade fold-in

#### Added
- **Cortex encryption-at-rest (opt-in, default OFF)** — SQLCipher full-DB AES-256 with an
  Argon2id + OS-keyring hybrid key model (`DZP_CORTEX_KEY` `file:` URI fallback). Reversible,
  backup-first migration `migrate_cortex_encrypt_9_8.py` (vec0/FTS5 smoke-verify, atomic replace,
  ledger refusal on shared brains). `brain key`/`brain encrypt` CLI; `brain status` reports
  `encryption_status` + posture advisory. Plaintext (disabled) path byte-for-byte unchanged.
- **`brain reset --scope orphans`** (BUG-CORTEX-PROLIF) — safe GC of orphaned Cortex install dirs;
  dry-run default, quarantine-to-`.trash-*` on `--execute`, `--hard-delete` for permanent removal.

#### Fixed (v9.7.2 upstream-upgrade bundle — downstream-reported, folded into this MINOR)
- **Group A**: SEC-9720-001 (migration path-traversal guard), SEC-9720-006 (YAML inline-comment
  parse), C-1 (Cortex-engine preflight on migration), SEC-9720-004 (placeholder contact → WARN not
  hard ERROR), STATE-LEGACY (session-state sanitizer for legacy `pause`).
- **Group C**: DRIFT-ENGINE (engine-parity release check), SEC-9720-005 (hook auto-install docs),
  ONEDRIVE-LOCK + GUARD-FRICTION documentation.
- **Orphan-GC P1 remediation**: SEC-9720-008 (execute-path TOCTOU re-validation + symlink/junction/
  reparse/path-escape rejection), SEC-9720-009 (preserve graph rows/memories/recursive/unreadable/
  missing-table), SEC-9720-010 (30-day recency gate + `--older-than-days`), SEC-9720-011
  (quarantine-default; `--hard-delete` opt-in).

#### Security
- SEC-CORTEX-ENC-001..009 CLOSED; SEC-9720-008/009/010/011 CLOSED. Megumi Tier-3 @approved
  (encryption + orphan-GC). 7 accepted P3 residuals deferred to v9.9.x (shared-brain key
  provisioning + rotation, exports encryption, in-memory key zeroization).

#### Tests
- 935 passed, 3 skipped (`tests/brain`); full suite green.

## [9.7.2] - 2026-06-18

### PATCH — SEC-CORTEX-MEM-001 + BUG-CORTEX-MIGRATE-001 (silent data-loss exposure v9.4.0–v9.7.0)

Closes two HIGH-severity defects that shipped silently in the public distribution from v9.4.0
through v9.7.0. All users of shared-brain or multi-install Cortex who relied on `brain remember`
should re-run `brain seed` + `brain index` after upgrading.

### Fixed
- **SEC-CORTEX-MEM-001 (HIGH/P1)**: Memory-keying silent data loss — memories written via
  `brain remember` shared a generic `source_path`, causing live overwrites (each new memory
  silently replaced the previous one), `brain seed` loss, and v1→v2 migration duplicate-key
  constraint failures. Fix: `memory.py` keys on `source_path=f"memory:{mem_id}"`; migration
  script `_effective_storage_key` applied on insert loop; `brain.py:_seed()` unique `line_start`.
  Accepted P3: SEC-CORTEX-MEM-002 (theoretical key-collision edge case, advisory documented).
- **BUG-CORTEX-MIGRATE-001 (HIGH)**: `migrate_cortex_storage_9_4.py` was stub-only — no
  `sqlite_vec` extension load, no vec0 DDL, no vector blob copy, no dim/model resolution. Any
  user attempting v1→v4 migration on a real brain silently got an empty vector table. Fix (MV-1..8):
  `_open_db_vec` loads `sqlite_vec`; real `vec0 content_vectors` DDL with correct dim; direct
  byte-exact blob copy from source `vec0`; dim + model resolved from blob + config fallback.
  Accepted P3: SEC-MIGRATE-RV-001 (dim-mismatch detection advisory).
- Note: Both defects shipped silently from v9.4.0 through v9.7.0. v9.4.0–v9.7.0 silent-data-loss
  exposure documented.

### Verified
- DZ's own brain migrated v1→v4; 21/21 memories preserved; recall confirmed OK.
- Tests: **861 passed / 2 skipped / 0 failed**. Yuuji TDD + Megumi Tier-3 @approved.

---

## [9.7.1] - 2026-06-18

### PATCH — PLAN-CORTEX-ACCESS-001 Cortex Access Hardening (CIA-triad, Phases 1–2)

### Added
- **SEC-CORTEX-ACCESS-008 (P0)**: Anti-destruction guard on shared brain — `cortex_installs`
  role/first_seen ledger; `brain reset --scope self|all` with `--shared-ok` /
  `--all-installs-acknowledged` / `--force-foreign` gate; foreign-install refusal;
  `_store()` proactive ledger stamping; `DZP_CORTEX_INSTALL_ID` validation.
- **SEC-ELAST-002 (P3)**: LIKE-wildcard escape in `_protected_sql_clause`.
- **SEC-CORTEX-ACCESS-009 (P1)**: Pre-op `brain.db` backup to `<data_dir>/backups/` + retention +
  `PRAGMA integrity_check`/`foreign_key_check` + `integrity-fail.flag` + `brain restore --from --verify`.
- **SEC-CORTEX-ACCESS-010 (P1)**: Graceful degradation — `brain status` `availability_status`
  ok/degraded/unavailable + `DZP_CORTEX_SKIP_RELEASE_GATE` release-gate escape +
  SchemaTooNew/Mismatch exit 0.
- **SEC-ACCESS-008-NEW-001 (P3)**: Read-op ledger stamp fail-soft on locked DB.
- New config key: `backup_retention_count` (default 3).

### Deferred
- ACCESS-004/005/006 + 007/011 encryption + 012/013 → v9.8.x. CIA-triad design recorded.

### Verified
- Tests: **1140 passed**. Yuuji TDD + Megumi Tier-3 @approved every phase.

---

## [9.7.0] - 2026-06-18

### MINOR — Stage 3 Storage Elasticity (PLAN-CORTEX-UNIFIED-001)

### Added
- **Schema v4**: `last_recalled_at` nullable column on `content_refs`; v4 dispatch (v1/v2/v3 run
  in-mode); `migrate_cortex_elastic_9_7.py` (v3→v4, backup-first, `cortex_installs` ledger gate).
- **Eviction engine** (`Store._evict_to_budget`): strict priority (archives→untrusted→semi→LRU;
  NEVER evicts protected/trusted/live; SQL-guarded); per-install `storage_budget_mb` config;
  ingest post-run eviction (fail-soft); LRU opt-in privacy (`S3-RISK-004`).
- **Compact + advisory**: `store.compact()` content-addressed orphan-sweep + VACUUM
  (SEC-UNIFIED-004 fail-soft; S3-RISK-003 lock abort); `brain compact` CLI; `brain status --json`
  gains `"storage"` object; `cortex_trigger` RESERVE-D advisory (never fail-closed); `cortex-compact`
  lifecycle event.

### Fixed
- Test isolation: `conftest.py` neutralizes ambient `DZP_CORTEX_DATA_DIR`/`INSTALL_GROUP` env vars
  (root-caused rhs-shared live-brain mutation).

### Security
- SEC-ELAST-001 (`include_protected` SQL guard) + SEC-UNIFIED-004 closed.
- Deferred: SEC-ELAST-002 + PLAN-CORTEX-ACCESS-001 + SEC-CORTEX-ACCESS-007 (encryption-at-rest).

### Verified
- Tests: **1080 passed / 2 skipped / 0 failed**. Yuuji TDD + Megumi Tier-3 @approved each phase.

---

## [9.6.0] - 2026-06-17

### MINOR — Stage 2 Graph Structured Recall (PLAN-CORTEX-GRAPH-001)

### Added
- **Schema v3**: `cortex_entities`/`edges`/`query_cache`/BM25 FTS5 tables; `graph.py` typed
  entity/edge graph (go/no-go pack, query-time dual-filter trust); `brain entity`/`gnogo`/
  `release-check` CLI; `migrate_cortex_graph_9_6.py` (v2→v3, backup-first).
- **Hybrid retrieval** (`cortex/retrieval.py`): BM25+dense, TRUE RRF re-ranking, recency/trust
  re-rank, index_epoch query cache; `Store.hybrid_search`; `brain query --hybrid` / `brain cache`.
- **Proactive surfacing**: `cortex_trigger.py --recall` (DATA-not-instructions boundary; trusted,semi
  floor; [SUSPECT] flag; stdout secret redaction); `cortex/extractor.py` (SEC-ID/WI/Version/Decision
  entity extraction, schema-gated); `brain distill` (propose-only) / `brain seed` / `brain recall`;
  advisory wiring to `pre-protected-edit`, `pre-release`, `session-end`.

### Security
- SEC-GRAPH-001..005 P1 folded; SEC-GRAPH-NEW-001..004 + SEC-HYBRID-001..004 +
  SEC-GRAPH-009 + SEC-UNIFIED-003 closed.

### Verified
- Tests: **1005 passed / 2 skipped / 0 failed**. Yuuji TDD + Megumi Tier-3 @approved every phase.
  Distro manifest + 4 new modules.

---

## [9.5.0] - 2026-06-16

### MINOR — Cortex Interconnectivity (PLAN-CORTEX-UNIFIED-001 Stage 1)

### Added
- **`cortex_trigger.py`** (Phase 2): single shared wrapper for all lifecycle events; eliminates
  per-script Cortex imports.
- **`brain.py` lazy Embedder + `--full`** (Phase 3): embedder initialised on first use; `--full`
  forces complete rebuild.
- **Registry rewire + double-trigger removal** (Phase 4): `script_dependencies.yaml` routes all
  7 pre-existing events through `cortex_trigger.py`; direct `_sync_cortex_index` calls in
  `session_monitor.py` removed.
- **10 lifecycle events total**: 7 rewired + 3 net-new (`pre-publish`, `post-migration`, `post-rotation`).
- **Lifecycle skill → coordinator routing** (Phase 5b): `.claude/commands/` skills invoke
  `dzp.py event <name>` directly (closes S1-RISK-012 orphaned-event regression HIGH).

### Security
- SEC-P4-001..004 + SEC-UNIFIED-001 closed.

### Verified
- Tests: **774 passed / 1 skipped / 0 failed**. Yuuji TDD + Megumi Tier-3 @approved.

---

## [9.4.1] - 2026-06-16

### PATCH — Protected-Document Append-Only Enforcement (FEAT-GUARD-001)

### Added
- **Pre-commit guard** (`scripts/check_protected_append_only.py`): HEAD-blob byte-prefix invariant
  blocks truncation/overwrite of the three protected documents. CRLF-hardened.
  `DZP_ALLOW_PROTECTED_REWRITE=1` for authorized rewrites (rotation, restore).
- **Unified pre-commit hook** (`scripts/git-hooks/pre-commit` + `.ps1`): publish-skip →
  append-only guard → agent guard → validate-protocol in sequence (SEC-GUARD-003).
  Installer: `scripts/install-git-hooks.{sh,ps1}`.
- **Cortex stale `index.lock` self-heal**: mtime TTL guard prevents a stale lock blocking Cortex.
- Distro ships the guard scripts and hook installer.

### Security
- SEC-GUARD-001..006 all CLOSED.

### Verified
- Tests: 36 guard + 11 lock. Yuuji TDD + Megumi Tier-2 @approved.

---

## [9.4.0] - 2026-06-16

### MINOR — Content-Addressed Cortex Storage (PLAN-DESIGN-001)

Replaces per-scope chunk-addressed storage (v1) with a content-addressed model (v2): one vector
per distinct `content_hash`, reference-counted occurrences. Eliminates the ~55% shared-install
vector duplication (BUG-CORTEX-007) and closes the DESIGN-001 cross-scope orphan-cleanup
corruption path. Built across 7 phases (each Yuuji TDD + Megumi Tier-3); Gojo-coordinated
all-hands review. **Megumi final Tier-3 @approved** — all 13 §8 acceptance criteria PASS.
**350 passed / 1 skipped** brain + **21** distro tests; `assert_version` green (20 sources).

### Added
- v2 schema in `cortex/store.py`: `content` / `content_vectors` / `content_refs` with indexes
  on `content_hash`, `storage_key`, `(content_hash,trust)`; deterministic
  `ref_id = sha256(storage_key:line_start:content_hash)[:16]`.
- `init_schema` dispatch: fresh→v2; legacy v1 kept on v1 (never auto-stamped); v2→idempotent;
  >2→`SchemaTooNewError`; mismatch→`SchemaMismatchError`.
- Content-addressed upsert (one vector per hash), ref-count delete (`NOT EXISTS`, cross-scope
  shared vector preserved), v2 search (trust filter in SQL before dedup).
- `.protocol-state/migrate_cortex_storage_9_4.py` — reversible, parity-gated migration
  (`--check/--execute/--rollback`): backup-first, single `BEGIN IMMEDIATE`, pre-flight
  duplicate-key scan, parity gate before drop, idempotent; `cortex_installs` shared-DB version gate.
- v2 `doctor`/`dedup` diagnostics (ref-counts + true dedup ratio); distro ships + smoke-tests the
  migration utility (IMPL-002).

### Security
- SEC-CORTEX-009..024 closed across the feature. Accepted residual: SEC-CORTEX-016 (P3, vec0
  `lastrowid` integration-test gap — production fix in place, real-backend CI test deferred).
- Lock discipline: `busy_timeout` + `BEGIN IMMEDIATE` on all v2 write paths. Trust at reference
  level (no cross-scope trust elevation). Recall + trust-filter parity vs v1 proven by tests.

## [9.3.4] - 2026-06-16

### PATCH — Cortex Preflight + Hardening (PLAN-DESIGN-001 §0)

Gates the v9.4.0 content-addressed storage migration by shipping the schema-version guard to the
v9.3.x engine first. Gojo-coordinated **all-hands Tier-3** review (Megumi/Todo/Maki/Yuuji/Nobara).
**Megumi Tier-3 @approved.** **168 passed / 1 skipped** brain tests; version gate green (20 sources).

### Added
- Schema-version guard in `cortex/store.py`: `PRAGMA user_version` canonical authority +
  `metadata.schema_version` mirror; `SchemaTooNewError`/`SchemaMismatchError` **fail closed on ALL
  operations**; marker never downgraded (fixes the pre-v9.3.4 unconditional `user_version=1`
  corruption vector). New `errors.py` exception classes (exit codes 5/6).
- `cortex_installs` membership ledger (per PLAN-DESIGN-001 §0) to enable the v9.4.0 shared-DB
  version gate.
- Tests: `tests/brain/test_schema_guard.py`, `tests/brain/test_v934_preflight.py`.

### Security
- SEC-CORTEX-009 (dim DDL validation), SEC-CORTEX-010 (export secret re-filter),
  SEC-CORTEX-011 (rglob `recurse_symlinks=False`, Py3.13+), SEC-CORTEX-012 (PS1 hook stderr
  capture), SEC-CORTEX-013 (memory `remember()` injection suspect-flag).

### Performance
- Schema guard memoized per `Store` (eliminates per-call `init_schema` overhead);
  `search()` empty-check collapsed from a `COUNT(*)` to `SELECT 1 LIMIT 1`.

### UX
- Nobara P1: actionable `SchemaTooNewError`/`SchemaMismatchError` messages (which install to
  upgrade, DB path, recovery commands, fail-soft note).

### Changed
- PLAN-DESIGN-001 (v9.4.0) amended: deterministic `ref_id`, `content_refs` indexes,
  `cortex_installs` shared-DB gate, trust-filter parity, `NOT EXISTS` delete.

## [9.3.3] - 2026-06-15

### PATCH — Toji Audit Remediation (BugReport3 / PATCH-CORTEX-DIAG-001)

Sukuna-led remediation of the Toji Sentinel audit (`internal-docs/Patch Report/BugReport3.md`,
7 findings). **Megumi Tier-2 @approved** (3 accepted P3, zero blocking); **123/123 brain tests**
(80 baseline + 40 new); extended version gate green at 20 sources.

### Fixed
- **IMPL-002 — version reconciliation:** all 10 agent frontmatter stamps and the nested
  `project-state.json` straggler were stuck at `9.2.1` while the gate passed at `9.3.2`.
  All agent `[CORE FILE]`/`protocol_version` stamps, the gojo schema example, and every
  `project-state.json` `protocol_version` field reconciled to `9.3.3`. `scripts/distro/assert_version.py`
  **extended** to scan `protocol/*.agent.md` frontmatter and ALL project-state version fields
  (was 7 core files; now catches agent + nested drift — verified by a negative test).
- **SEC-001 — `verify-protocol.ps1`:** YAML validation now reads `protocol.config.yaml` as
  explicit UTF-8, fixing a Windows ANSI-codepage false-fail on the config's 128 non-ASCII bytes.
- **CODE-001 — `_SCOPED_PREFIX_RE`:** the scoped-key pattern was declared twice (ingest + store);
  consolidated to a single canonical definition in `store.py`, imported by `ingest.py`, so the two
  modules can never drift on the scoped-key format.
- **IMPL-001 — RHS report:** withdrew the "low-risk one-shot physical de-dup" framing; interim
  relief is now `brain dedup --report` (read-only) only. Destructive de-dup is gated behind the
  future content-addressed migration (DESIGN-001 / v9.4.0).

### Added
- **SEC-002 — indexable-extension allowlist:** ingest now requires a positive `index_extensions`
  allowlist (config-driven) in addition to the binary denylist (defense in depth), plus an opt-in
  per-file `max_file_chunks` cap (default `0` = unlimited) and largest-file/outlier reporting. The
  default allowlist is **project-agnostic (74 extensions** across docs/scripting/config/web/systems
  languages) so Cortex indexes any user project out-of-the-box, not just protocol files; scope stays
  user-configurable via `include_folders`/`include_code` in `brain.config.yaml`.
- **IMPL-003 — read-only Cortex diagnostics:** `brain dedup --report` (duplicate ratio by
  scope/content-hash) and `brain doctor` (chunks/rowmap/vectors integrity, trust distribution,
  engine-hash drift detector, largest indexed files). Both strictly read-only — no row/vector
  deletion (destructive de-dup formally rejected for this patch).

### Security (post-review hardening — all three P3s resolved)
- **SEC-CORTEX-DIAG-001:** `brain doctor` labels the engine hash as drift-detection-only (not tamper-proof).
- **SEC-CORTEX-DIAG-002:** `config.validate()` rejects non-string `index_extensions` entries.
- **SEC-CORTEX-DIAG-003:** `dedup_report()` redacts any `text_preview` flagged by `contains_secret`
  (dependency-injected redactor) so the report never re-discloses a credential to stdout.
- Regression tests added for each; **123** brain tests pass. v9.3.3 ships with zero open SEC findings.

### Deferred
- **DESIGN-001 — content-addressed / reference-counted Cortex storage:** the real fix for
  shared-brain physical duplication changes the storage model and requires migration handling;
  scheduled for **v9.4.0 MINOR** with migration tests, rollback notes, and Megumi review. Query-time
  dedup (BUG-CORTEX-006) keeps recall correct in the interim.

---

## [9.3.2] - 2026-06-15

### PATCH — Cortex Engine Hardening Upstream (PATCH-CORTEX-SCOPE-001)

Upstreams the Cortex engine hardening from downstream gitignored `.protocol-state/` files into the
**canonical** `cortex/` engine, closing **SEC-CORTEX-003** (next-sync-reverts-every-patch integrity
gap, OWASP A08). **93/93** Cortex tests; **Megumi Tier-2 @approved** (0 findings). v9.3.1 skipped
(combined single carving per USER).

### Fixed
- **SEC-CORTEX-003:** per-file index cap is config-driven (`max_file_bytes`, default 6 MB; was a
  hardcoded 1 MB).
- **SEC-CORTEX-001:** `_trust_for` is default-deny — only `protocol/`, `scripts/`, and core root docs
  are `trusted`; all other content → `semi`.
- **SEC-CORTEX-002:** placeholder-aware secret detection via shared `contains_secret()` (ingest +
  memory); high-confidence token formats always drop, `keyword[:=]value` drops only non-placeholder values.
- **SEC-CORTEX-004:** `config.validate()` rejects non-positive / non-int / bool `max_file_bytes`.
- **BUG-CORTEX-006:** query-time content-hash de-duplication in `store.py` across both search paths
  (trust filter precedes dedup).

---

## [9.3.0] - 2026-06-15

### MINOR — BugReport Remediation Bundle (PATCH-BUGREPORT-001)

A consumer-driven remediation release resolving 14 findings logged during downstream
v8.13.0 → v9.2.1 upgrades, plus one feature request. Sukuna-led; **Megumi Tier-3 @approved
(zero SEC-IDs)**; 63 brain + 36 session-monitor tests green; version-consistency and
PII/path publish gates passing.

### Fixed
- **BUG-SESSION-001 (HIGH, safety):** `session_monitor.py` crashed on timezone-naive legacy
  `last_alert_time` (aware−naive subtraction), silently disabling the 4h/6h/8h wellbeing
  alerts. Fixed with a centralized `_parse_utc()` normalizer across all timestamp parses.
- **BUG-SCHEMA-001:** `validation-rules.yaml` no longer requires the deprecated
  `tier_usage_statistics` block (migrated to `tier_tracking`).
- **BUG-VALIDATE-001:** `validate-protocol.py` no longer reports SUCCESS for an
  unvalidatable/empty run (false-negative hardened; exit codes are CI-sound).
- **BUG-VERIFY-001:** `verify-installation.py` manifest reconciled with
  `publish-manifest.yaml` — a fresh canonical install verifies green.
- **BUG-CORTEX-002/003/004:** actionable data-dir remediation hint for OneDrive/synced
  projects; Windows `huggingface_hub` symlink-warning suppressed by default; `hf_xet`
  noted as an optional faster-download dependency.
- **BUG-DISTRO-001:** removed a stray `.claude/commands/sukuna copy.md` editor duplicate and
  added a `* copy.*` publish-audit guard.

### Added
- **BUG-CORTEX-001/005 — first-class shared brain:** `install_group` (config) /
  `DZP_CORTEX_INSTALL_GROUP` (env) share one Cortex across nested installs without leaking an
  absolute machine path; **install-scoped source keys** make multi-install shared indexing
  non-destructive (no cross-install clobber of protected docs). Default single-install
  behavior is byte-identical — no DB migration required.
- **BUG-MIGRATE-001:** `migrate_state_9x.py` — additive 8.x → 9.x state migration
  (injects `tier_settings` / `validation_state` / `agent_registry`, repairs naive
  timestamps) with `--check` / `--execute` / `--rollback`.
- **BUG-VALIDATE-002:** `requirements-dev.txt` declares `jsonschema` / `PyYAML` for the
  protocol validation tooling.
- **FEAT-REQ-001:** opt-in, config-driven agent-file protection pre-commit hook
  (`scripts/git-hooks/` + `scripts/install-git-hooks.{sh,ps1}`), driven by
  `custom_agent_security.file_protection.immutable_paths`. Ships for consumers; not
  auto-installed.

### Changed
- **BUG-DOC-001:** `docs/installation/IMPLEMENTATION_GUIDE.md` refreshed to 9.x (DZP Cortex
  setup, 8.x → 9.x migration steps, version-agnostic copy examples).

### Notes
- Out of scope: BUG-SYNC-001/002 (project-local `dzp-sync` tooling, not part of canonical).

## [9.2.1] - 2026-06-14

### FEATURE — Central DZP Script Orchestration (PATCH-ORCH-001)

Adds a root-level `dzp.py` entry-point, a `.protocol-state/script_coordinator.py` engine, and a `script_dependencies.yaml` event registry that wire 7 DZP lifecycle events to sequenced, dependency-aware script steps. Builds on v9.1.1 base (v9.2.0 intentionally skipped per USER direction). Megumi Tier-3 @approved; 44 tests passed / 1 skipped; dev-only (distro-excluded).

#### A. New Files (dev-only, not shipped)
- **`dzp.py`** (root) — single CLI entry-point to run any registered DZP lifecycle event by name; dispatches to `script_coordinator.py`
- **`.protocol-state/script_coordinator.py`** — event-driven step sequencer with dependency resolution, per-step timeouts, fail-soft vs fail-CLOSED classification, structured logging
- **`script_dependencies.yaml`** — event registry mapping 7 lifecycle events to ordered step lists with gate policy and dependency declarations (event->step only)

#### B. 7 Registered Lifecycle Events
- `session-update` — orchestrates project-document sync + Cortex re-index (fail-soft)
- `session-end` — full Cortex rebuild + snapshot export (fail-soft)
- `ts-start` — troubleshooting session initialization steps (fail-soft)
- `ts-complete` — troubleshooting session completion + analytics (fail-soft)
- `pre-protected-edit` — pre-flight checks before protected document edits (fail-CLOSED)
- `pre-release` — release gate checks including assert_version + PII scrub (fail-CLOSED)
- `toji-snapshot` — Cortex snapshot export for Toji audit sessions (fail-soft)

#### C. Security (Megumi Tier-3 @approved)
- **SEC-ORCH-001..011** — 11 security controls applied to orchestration surface (input validation, path confinement, privilege separation, timeout enforcement, log sanitization, etc.)
- **SEC-COORD-001..005** — script_coordinator.py remediations (injection prevention, event allowlist, step enumeration guard, output capture sandboxing, error message sanitization)
- **SEC-COORD-005-EXT** — extended coverage for dynamic step resolution edge cases
- **One P3 accepted-risk** — documented in security-review.md; no P0/P1/P2 open

#### D. Test Coverage (Yuuji Tier-3)
- 44 tests passed / 1 skipped across unit + integration + E2E suites
- Coverage: event dispatch, step sequencing, dependency resolution, fail-soft/fail-CLOSED gates, timeout handling, concurrent execution guards

#### E. Distro Gate
- `dzp.py`, `script_coordinator.py`, `script_dependencies.yaml` are excluded from `dzp-publish` allowlist (dev-only tooling; end-user installations do not receive this layer)

#### Version Cascade
- All 7 assert_version-gated files bumped to `9.2.1`: `CLAUDE.md` x2, `VERSION.md`, `protocol.config.yaml`, `AI_INSTRUCTIONS.md`, `README.md`, `project-state.json`
- All 10 agent `protocol_version` stamps updated to `9.2.1`
- `python scripts/distro/assert_version.py --root .` — PASS

---

## [9.1.1] - 2026-06-14

### PATCH — Cortex Stabilization (PATCH-STABILIZE-001)

Stabilizes the published v9.1.0 DZP Cortex engine, hardens the brain-index hooks, reconciles leftover version drift, and aligns documentation with actual fail-soft behavior. Megumi @approved; zero new SEC-IDs. All findings are defects inherited from the v9.1.0 Cortex merge.

#### A. Cortex Core Bug Fixes (PR#92 CodeRabbit)
- **brain.py** (PR#92:73) — propagate `--allow-unsafe-data-dir` flag consistently to `status` and `query` commands; it was previously applied only on initialization, leaving the flag silently ignored for those subcommands.
- **brain.py** (PR#92:95) — derive the embedding vector dimension from the loaded model at runtime instead of hard-coding 384; mismatched dimensions caused silent upsert corruption when a non-default model was configured.
- **cortex/ingest.py** (PR#92:153) — guard against chunk/vector count mismatch before upsert; previously a cardinality mismatch would cause an unhandled exception mid-batch, leaving the index in a partial state.
- **cortex/paths.py** (PR#92:75) — anchor relative `data_dir` override paths to `repo_root`; they were previously resolved against the process CWD, which broke invocations from any directory other than the project root.

#### B. Hook Hardening (same class as orchestration SEC-ORCH-002/006)
- **`.claude/settings.template.json`** (Critical) — add missing `$TimeoutSeconds = 30` definition before the PowerShell hook body; without this the hook threw `TerminatingError: $TimeoutSeconds not recognized` and the session-end index was never run.
- **`scripts/brain-index-hook.ps1` + `.sh`** — replace repo-path interpolation into the `python -c` heredoc with argv-data passing (`python script.py "$repoPath"`); paths containing apostrophes or special characters were breaking the inline source string.
- **`scripts/brain-index-hook.ps1` + `.sh`** — make lock acquisition atomic using a create-exclusive pattern instead of the `Test-Path`→`New-Item` two-step (TOCTOU race); tie lock ownership to the invoking PID so cleanup cannot remove a lock held by a concurrent legitimate process.

#### C. Robustness
- **`scripts/dependency-scanner.py`** (PR#92:742) — confine the `--export` output path to the repository root; previously it accepted any filesystem path, creating a potential write-outside-repo vector.

#### D. Version-Drift Reconciliation
- **`.protocol-state/project-state.json`** — reconcile two nested straggler `protocol_version` fields (`session_tracking.protocol_version` and `tier_tracking.metadata.protocol_version`) to `9.1.1`; these were left at pre-9.1.0 values by the v9.1.0 cascade.

#### E. Documentation Alignment
- **`.claude/commands/session-update.md`** — replace `&&`-chained shell snippet in the Cortex re-index step with a fail-soft `if status { index } else { proceed }` pattern to match the actual `session_monitor._sync_cortex_index()` fail-soft implementation.
- **`protocol/skills/session.md`** — wire the Cortex snapshot export into `/session end` step or remove the promise from docs; the gap between documented behavior and implementation was a source of confusion.
- **`protocol/skills/ts.md`** — use the default trust tier for Cortex query calls in troubleshooting flows; keep Cortex failures visible (not silenced) so agents can report index staleness.
- **`protocol/SUKUNA-REPORT.md`** — correct the fast-path invocation note (was referencing the `sync` subcommand; correct subcommand is `update`).
- **`slash-commands/ts-codered.md`** — make the Cortex footer banner mandatory, not optional; Code Red sessions must always surface Cortex recall state.

#### F. Sukuna Live-Bug Fixes (pre-existing v9.1.0 defects)
- **`.protocol-state/tier-statistics.py`, `gojo-learn.py`, `sukuna-learn.py`** — insert `scripts/` onto `sys.path` before the `from verify_working_directory import …` statement; the import was failing with `ModuleNotFoundError` when scripts were invoked from the project root (the only normal invocation path).
- **`.protocol-state/snapshot_integration.py`** (line 54) — correct the runtime constant from `scripts/create-snapshot.py` to `.protocol-state/create-snapshot.py`; auto-snapshots were silently failing because the path did not exist. Also updated `SNAPSHOT_INTEGRATION.md`, `DEPENDENCY_SCANNER_GUIDE.md`, and `gojo-snapshot-integration-guide.md` to remove the stale path references.

#### G. Session-Monitor Safety Defect (discovered during stabilization)
- **`.protocol-state/session_monitor.py`** — `is_high_risk_operation()` was silently returning `False` for the common short-form production push commands (`git push main`, `git push master`, `git push production`) as well as `deploy to production`, `docker-compose up production`, and `kubectl apply production`. With the 6h+ `high_risk_operations_blocked` flag set, those operations were **NOT being blocked** — a real gap in the Absolute Safety enforcement. Added the missing literals so the safety blocker covers them.
- **`.protocol-state/session_monitor.py`** — `should_block_operation()` now includes the `🛑` marker and reports the authoritative stored duration (not just live wall-clock) in the block reason.
- **`tests/test_session_monitor.py`** — corrected one stale test (`test_handles_very_long_operations`) that assumed regex word-boundary matching. Full suite now 104/104 pass; `verify-auto-invoked.py` reports safety enforcement FUNCTIONAL.

#### Version Cascade
- All 7 assert_version-gated files bumped to `9.1.1`: `CLAUDE.md` ×2, `VERSION.md`, `protocol.config.yaml`, `AI_INSTRUCTIONS.md`, `README.md`, `project-state.json`.
- All 10 agent `protocol_version` stamps updated to `9.1.1`.
- `python scripts/distro/assert_version.py --root .` — PASS.

---

## [9.1.0] - 2026-06-14

### MINOR — DZP Cortex: Local Semantic Memory (PLAN-BRAIN-002)

#### PLAN-BRAIN-002: DZP Cortex Brain Feature
- Local semantic-memory index using sqlite-vec + fastembed (no external API after first model download). The Cortex **engine** lives at `.protocol-state/brain/` (`brain.py` + `cortex/*.py` + `requirements-brain.txt`) and is **tracked + shipped**. Only the runtime **data** (DB, memories, model cache, logs, snapshots) lives in the external dir `%LOCALAPPDATA%/dzp-cortex/<install-id>/` (XDG equivalent on macOS/Linux) and is never committed.
- `/brain` slash command (`.claude/commands/brain.md`) and skill (`protocol/skills/brain.md`) for query, index, remember, status, and export operations.
- `scripts/brain-index-hook.{sh,ps1}` — incremental index hook (fail-soft, lock-guarded, 30s timeout).
- `scripts/brain.{sh,ps1}` — CLI wrappers for direct brain use without invoking the full agent stack.
- `tests/brain/` — unit + integration tests for brain indexing and retrieval (excluded from distro).
- **Phase 10 agent doc blocks**: all 10 `protocol/*.agent.md` files updated with Cortex context sections (when/how to invoke brain retrieval during agent workflows).

#### Cortex Distro Shipping + Workflow Integration
- **Engine now ships in the distro**: `scripts/distro/publish-manifest.yaml` allowlists the `.protocol-state/brain/` engine + `scripts/brain*.{ps1,sh}` wrappers/hooks (security-cleared by Megumi). Previously the docs shipped without the engine — a publish-readiness defect caught by the distro dry-run.
- **SEC-BRAIN-012** (@approved): `tests/brain` added as an explicit `forbid_tokens` tripwire (its `__pycache__` `.pyc` bytecode bakes owner filesystem paths). Scoped to `tests/brain` (not bare `tests`) to avoid collision with vendored `node_modules/.../tests`.
- **Publish-gate hardening**: `scripts/dzp-publish.ps1` now checks `$LASTEXITCODE` after the audit stage and both `assert_version` calls — a failed PII/exclude/version audit can no longer reach `git commit`/`push` (previously the gate did not block on a native non-zero exit).
- **Cortex Integration Contract** added to `protocol/skills/brain.md` — canonical fail-soft / status-gated / trust-level rules referenced by all skills and launchers.
- **Workflow integration**: RECALL/REMEMBER/INDEX hooks added to `protocol/skills/{ts,session,dzp-roe}.md`; a Cortex pointer footer added to all slash-command launchers (28 in `.claude/commands/` + 26 in `slash-commands/` = 54 files); `brain.md`/`dzp-roe.md` added to the `slash-commands/` mirror.
- **DZP↔Cortex gap closures** (red-team): `/session end` now runs `export --snapshot` so Toji's read-only snapshot exists; Cortex onboarding (install deps, first index, model-download note, **and the auto-index hook setup**) added to `README.md`.
- **Sanitized settings template ships**: new `.claude/settings.template.json` (PII-free starter pre-wiring the `SessionEnd` auto-index hook + `brain` command allow-list) is git-tracked (via `.gitignore` negation) and shipped in the distro (manifest `include_files`). Users `cp` it to `.claude/settings.json` to enable auto-indexing. The **real** `.claude/settings.json` stays gitignored (local paths + personal permission allowlist) and never commits/ships. This makes GAP-01 a shipped artifact, not just documentation.

#### Security Remediation (Cortex)
- **SEC-BRAIN-007** (@approved): `.gitignore` backstop entries (model cache, `*.db`, memories, snapshot) confirmed in `.protocol-state/brain/.gitignore` and `scripts/distro/distro.gitignore`.
- **SEC-BRAIN-008** (@approved): AWS secret patterns (`access_key_id` / `secret_access_key`) added to the Cortex ingest scrub in `.protocol-state/brain/cortex/ingest.py` (shared with the memory write path). Residual secret-format coverage (GCP/Azure/bare tokens) logged as a future non-blocking sweep — **not yet implemented**.
- **SEC-BRAIN-011** (P3, accepted): `brain-index-hook.sh` inline-Python shell-metachar hardening — future non-blocking item.

#### Performance Gate (no-daemon CLI)
- Targets formally defined for the no-daemon CLI: `query`/`remember` <3s, full index ≤5min, incremental no-op <5s. Canonical benchmarks pass; STUB p95 (k=5) = 0.270s. Sub-1s warm latency deferred to a future daemon. (Supersedes an earlier "sub-500ms" figure, which was a documentation error.)

#### /session update — Full-Sync Orchestrator + Cortex-in-Sync Integration
- **`/session update` promoted to CORE full-sync orchestrator.** Plain `update` now runs: timestamp → full project-document sync (project-state.json, domain.record.md [Gojo-gated], dev-notes.md, security-review.md, secret-scan-before-write, timestamped backups) → **mandatory Cortex incremental re-index** (fail-soft, status-gated). Git commit/push remains approval-gated. `update --time-only` preserves the original fast timestamp-only path unchanged. `check-and-record` / `continue` / `resume` subcommands unchanged.
- **Cortex re-index is now a mandatory step of the project-document sync.** Incremental (`--incremental`) on every `/session update`; full rebuild on `/session end`. Status-gated before the re-index call; fail-soft if Cortex is unavailable (never blocks the sync). Implemented in `.protocol-state/session_monitor.py` via `_sync_cortex_index`, `_cortex_index_lock_exists`, and `_cli_update` methods.
- **Cortex pointer banners** (top + footer) added to the three protected project documents (`dev-notes.md`, `security-review.md`, `domain.record.md`) and their three distro templates, ensuring fresh installations inherit the Cortex workflow guidance.

#### Security Hardening (P3 path-traversal defense-in-depth + doc fix)
- **Snyk python/PT triage (24 findings, Megumi @approved):** 21 findings classified as false-positive (local single-user CLIs; argv/env inputs are owner-supplied). 3 classified P3 defense-in-depth and remediated; 0 true-positive.
- **SEC-BRAIN-009** (@approved, P3): `brain.py` snapshot `--out` argument now rejects writes targeting `protocol/`, `.claude/`, `scripts/`, or the 5 root core `.md` files. Confinement prevents accidental overwrite of CORE files via the export path.
- **SEC-SCRIPT-001** (@approved, P3): `dependency-scanner.py` `--export` path confined to cwd; rejects paths containing `..` traversal or absolute paths outside the project root.
- **SEC-SCRIPT-002** (@approved, P3): `assert_version.py` `--root` argument now checks for the DZP marker file (`protocol.config.yaml`) before proceeding, preventing silent misfire against unrelated directories.
- **SEC-DOC-001** (@applied): corrected three `/session update` doc files that described the fast path as `session_monitor.py sync --time-only`; the correct invocation is `session_monitor.py update --time-only` (`--time-only` is parsed in the `update` branch, not `sync`).

### Distro Publication Status (updated)
- **Test gate: CLEARED** — Cortex has been functionally tested by the owner; the "GATED on user acceptance testing" gate is cleared.
- **`DZP-v9.1.0` publish branch**: created and committed **locally** via `dzp-publish.ps1 -ForceClean -NoPush`. Branch exists locally; **not yet pushed** to the public canonical. Public push pending explicit owner go-ahead.
- Distro **dry-run passes all gates** (stage/identity/content scrub, PII audit, path audit, version assert at v9.1.0).

---

## [9.0.0] - 2026-06-13

### MAJOR — Distribution Architecture + Version Reconciliation

#### PATCH-DISTRO-001: Distro Publish Architecture
- Clean dev/distribution split. Production files publish to the canonical GitHub repo via an orphan `release` branch checked out as a `distro/` git worktree, driven by an allowlist `dzp-publish.{sh,ps1}` script — the dev workspace never reaches canonical.
- Pipeline: allowlist stage → identity scrub (`protocol.config.yaml`) → **content-level PII scrub** (personal email → GitHub Security Advisories link; real name → `DewyHRite`; local `C:\Users\…` paths → placeholder) → **content-PII audit (fail-loud)** → forbidden-path audit → **version-consistency assertion** across `CLAUDE.md` ×2, `VERSION.md`, `protocol.config.yaml`, `AI_INSTRUCTIONS.md`, and `project-state.json`.
- New: `scripts/distro/{publish-manifest.yaml, assert_version.py, dzp_publish_core.py, distro.gitignore}`, `scripts/dzp-publish.{sh,ps1}`, `tests/distro/test_publish_core.py` (9 tests). Deprecates `scripts/sync-release.ps1`.
- Security: full Megumi Tier-3 pre-publication audit; SEC-001..007 remediated (PII removed; two internal review docs excluded).

#### PATCH-TOJI-001: Toji External Auditor fabrication fix (CRITICAL)
- Closes ISSUE-DZP-001: Toji rebound from the non-binding `vscode/*` toolset to real Claude Code tools (report-only) so it binds and stops fabricating audits. Anti-fabrication constraints (CONSTRAINT_016–018) + a `tool_uses=0` tripwire. Registered Toji in the runtime `agent_registry` (ISSUE-DZP-003). Toji file v1.2.0 → v1.2.1.

#### Version reconciliation
- All version-bearing files + all 10 agent definitions stamped to **v9.0.0**.
- Caught `project-state.json` straggler (lagging at 8.12.0). Folded in the previously under-documented **v8.13.0** (Toji 10th agent, Session Monitoring Enhancement PATCH-SESSION-004/005/006, State Consolidation PATCH-STATE-001).
- Added `project-state.json` `protocol_version` to the version-consistency gate (closes ISSUE-DZP-006/007).

### Deferred
- DZP Cortex (local semantic-memory "separate brain") → **v9.1.0** (built and tested in dev; excluded from distribution until shipped).

---

## [8.12.0] - 2025-12-29

### Added

#### **PATCH-SESSION-004: Session Monitoring Enhancement** - Coverage gap remediation (70-85% → 85-90%)

**Purpose**: Close critical session monitoring coverage gaps identified through adversarial analysis. PATCH-SESSION-003 provided only 70-85% coverage (not 95% as claimed) due to context compaction, agent bypass, and prompt non-compliance.

1. **Component 1: Configurable Debounce Threshold**
   - Added `debounce_threshold_minutes` to `protocol.config.yaml` (configurable 15-60 range, default: 30)
   - Added `allow_runtime_override: true` for CLI `--debounce` flag support
   - Implemented `_load_debounce_config()` method in `session_monitor.py`
   - Modified `check_alert_needed()` to use configurable debounce from YAML or CLI
   - Reduces false negatives during rapid prototyping sessions

2. **Component 2: Compaction-Resistant Markers**
   - Added Critical Sections Index to `protocol/gojo.agent.md` (lines 199-211)
   - Wrapped AUTO-INVOKED section with HTML comment markers (lines 618-639)
   - Markers: `<!-- CRITICAL: DO NOT REMOVE - SAFETY SYSTEM (PATCH-SESSION-004) -->`
   - Protects AUTO-INVOKED section from context compaction removal (closes 5-10% gap)

3. **Component 3: Alert Tracking Dashboard**
   - Created `.protocol-state/session-monitoring-report.py` (~200 lines)
   - Functions: `check_auto_invoked_integrity()`, `calculate_expected_alerts()`, `analyze_alert_effectiveness()`, `generate_report()`
   - Detects alert undercount by comparing actual vs expected alerts
   - JSON output mode support (`--json` flag)
   - Usage: `python .protocol-state/session-monitoring-report.py`

4. **Component 4: AUTO-INVOKED Verification Script**
   - Created `scripts/verify-auto-invoked.py` (~170 lines)
   - 6 validation checks: section existence, HTML markers, required keywords, minimum length
   - CI/CD integration with exit codes (0 = pass, 1 = fail)
   - Verbose mode support (`--verbose` or `-v`)
   - Prevents AUTO-INVOKED section removal in automated workflows

5. **Component 5: Agent Invocation Tracking**
   - Created `.protocol-state/agent-invocation-tracker.json`
   - Schema tracks direct vs routed invocations for all 9 agents
   - Added `record_agent_invocation()` method to `session_monitor.py`
   - Bypass detection: Logs direct agent invocations during long sessions (>= 30 min)
   - CLI command: `python session_monitor.py record-invocation <agent_name> [--routed]`
   - Detects 10-15% coverage gap from agent bypass patterns

#### **PATCH-STATE-001: State File Consolidation** (2025-12-31)
- **Purpose**: Consolidate 4 fragmented state files into unified `project-state.json` with nested namespaces
- **Problem**: State fragmentation across `session-state.json`, `troubleshooting-history.json`, `agent-invocation-tracker.json`, and duplicated tier statistics caused data inconsistency and maintenance overhead
- **Solution**: Created centralized `ProjectStateManager` class with consolidated namespaces and non-destructive migration system
- **Key Changes**:
  1. **Consolidated Namespaces**:
     - `session-state.json` → `project-state.json::session_tracking`
     - `troubleshooting-history.json` → `project-state.json::troubleshooting`
     - `agent-invocation-tracker.json` → `project-state.json::agent_invocation_tracking`
     - Deduplicated `tier_usage_statistics` + `tier_statistics` → `project-state.json::tier_tracking`
  2. **ProjectStateManager** (`.protocol-state/project_state_manager.py`, 558 lines):
     - Centralized state access for all DZP components
     - Automatic fallback to legacy files if consolidated namespaces unavailable
     - Cross-platform file locking (Windows msvcrt, Unix fcntl)
     - Atomic writes using tempfile pattern
  3. **Migration System** (`.protocol-state/migrate_state_consolidation.py`, 368 lines):
     - Automatic backup creation with timestamps
     - Dry-run mode for safety
     - Migration status detection
     - Rollback capability
  4. **Updated Scripts** (8 total):
     - `session_monitor.py`, `troubleshooting_tracker.py`, `tier-statistics.py`, `tier-enforcement.py`
     - `gojo-learn.py`, `sukuna-learn.py`, `restore-snapshot.py`, `create-snapshot.py`
     - All use ProjectStateManager with backward compatibility
  5. **Updated Documentation**:
     - `protocol/skills/session.md` (v1.0.0 → PATCH-STATE-001)
     - `protocol/skills/ts.md` (v1.0.0 → v1.1.0)
     - `protocol/gojo.agent.md` (added Option 6: Migrate State Consolidation)
- **Migration Path**:
  ```bash
  # Check if migration needed
  python .protocol-state/migrate_state_consolidation.py --status

  # Dry run (no changes)
  python .protocol-state/migrate_state_consolidation.py --dry-run

  # Execute migration (with automatic backups)
  python .protocol-state/migrate_state_consolidation.py --execute
  ```
- **Backward Compatibility**: All scripts fallback to legacy files if consolidated namespaces unavailable. No breaking changes.
- **Impact**: Reduced file count from 4 to 1, eliminated tier statistics duplication, improved data consistency, single source of truth for DZP state
- **Files Created**: `project_state_manager.py`, `migrate_state_consolidation.py`
- **Files Modified**: 8 Python scripts + 3 documentation files (session.md, ts.md, gojo.agent.md)

#### **PATCH-TS-001: Unified Troubleshooting Session Tracker** (2025-12-31)
- **Purpose**: Centralized tracking system for all /ts tier commands with permanent historical analytics
- **Problem**: No historical data on troubleshooting patterns, tier effectiveness, or escalation frequencies
- **Solution**: Created `.protocol-state/troubleshooting_tracker.py` (585 lines) with permanent session storage
- **Key Features**:
  1. **Session Management**: start, update, complete, escalate, status commands
  2. **Tier Analysis**: Success rates, average durations, escalation patterns per tier (1-5)
  3. **File Frequency Tracking**: Identifies most commonly problematic files across sessions
  4. **Pattern Recognition**: Statistical analysis of tier effectiveness and escalation triggers
  5. **Permanent Retention**: All sessions kept indefinitely in `troubleshooting-history.json`
- **Commands Added**:
  - `python troubleshooting_tracker.py start <tier> "<description>" "<files>"`
  - `python troubleshooting_tracker.py update <session_id> "<status>"`
  - `python troubleshooting_tracker.py complete <session_id> "<resolution>"`
  - `python troubleshooting_tracker.py escalate <session_id> <new_tier> "<reason>"`
  - `python troubleshooting_tracker.py status [session_id]`
  - `python troubleshooting_tracker.py stats` (NEW - historical analytics)
- **Integration**: Updated `protocol/skills/ts.md` to review stats before tier selection
- **Files Created**: troubleshooting_tracker.py, troubleshooting-history.json
- **Files Modified**: protocol/skills/ts.md (added Step 0 - stats review)
- **Impact**: Data-driven tier selection, pattern learning, troubleshooting effectiveness tracking

### Fixed

#### **Windows Compatibility: Unicode Encoding Error**
- **Issue**: `UnicodeEncodeError` in Windows command prompt when displaying emoji characters
- **Root Cause**: Windows cmd.exe (cp1252 encoding) cannot display Unicode emojis
- **Fix**: Replaced 20+ Unicode emojis with ASCII equivalents in `session_monitor.py`
  - `⚠️` → `[!]`, `✅` → `[OK]`, `📊` → `[STATUS]`, `⏸️` → `[PAUSED]`
  - `🛑` → `[BLOCKED]`, `❌` → `[ERROR]`, `ℹ️` → `[INFO]`, `🗑️` → `[DELETE]`
  - `💡` → `[TIP]`, `🌙` → `[LATE]`
- **Testing**: All commands tested on Windows cmd.exe with no encoding errors

#### **PATCH-SESSION-005-v2: Complete Stale Timestamp Fix + State Management + Permission System** (2025-12-31)
- **Priority**: P0-Critical (User Safety)
- **Discoverer**: Sukuna (System Update Adversary)
- **Issue**: Three critical stale timestamp bugs completely disabled user safety systems
- **Bugs Fixed**:
  1. **Status Display Failure**: `get_session_summary()` always showed "0 minutes" for 15+ hour sessions
  2. **Historical Data Corruption**: `_archive_session()` permanently stored sessions with "0 minutes" duration
  3. **Safety System Complete Failure**: `should_block_operation()` NEVER blocked high-risk operations, even after 47+ hours
- **Root Cause**: Methods read stale `metrics['total_duration_minutes']` from JSON state instead of calculating live duration from timestamps
- **Fix**: Added `_calculate_current_duration()` and `_calculate_current_continuous_work()` helper methods (lines 942-995)
- **Extensions Added**:
  - **Extension 2 - State Management**: 4 new methods to update project-state.json, dev-notes.md, domain.record.md on session events
  - **Extension 3 - Permission System**: Gojo-only access to domain.record.md via `DZP_AGENT=gojo` environment variable
- **Files Modified**: session_monitor.py (+180 lines), session.md (updated with `DZP_AGENT=gojo`)
- **Impact**: User safety systems RESTORED - high-risk blocking now functional, duration display accurate, data integrity preserved

### Changed

- `protocol.config.yaml`: Added `safety.session_tracking.debounce_threshold_minutes` (default: 30)
- `protocol/gojo.agent.md`: Added Critical Sections Index and HTML safety markers
- `.protocol-state/session_monitor.py`: Debounce config loader, invocation tracking, Unicode fixes
- `VERSION.md`: Updated to v8.12.0 with comprehensive release notes
- `project-state.json`: Protocol version 8.11.0 → 8.12.0

### Documentation

- `VERSION.md`: Updated to v8.12.0 with 5-component breakdown
- `CHANGELOG.md`: This entry
- `docs/getting-started.html`: Updated with v8.12.0 features (session monitoring enhancements)
- `protocol/SUKUNA-REPORT.md`: Added PATCH-SESSION-004 comprehensive documentation

### Security

- Megumi security review conducted on all new scripts:
  - `scripts/verify-auto-invoked.py`
  - `.protocol-state/session-monitoring-report.py`
  - Agent invocation tracking logic in `session_monitor.py`
- Review scope: File I/O security, input validation, information disclosure, code injection, state integrity

---

## [8.10.0] - 2025-12-25

### Added

#### **DZP Rules of Engagement (ROE)** - Post-compaction recovery system

**Purpose**: Solve user pain point of repeatedly explaining DZP protocol rules after context compaction. Provides single-command context restoration.

1. **DZP ROE Skill** (`protocol/skills/dzp-roe.md`)
   - 9-step workflow for complete protocol recovery
   - Step 1: Read current project state
   - Step 2: Output DZP protocol summary (9 agents, roles, restrictions)
   - Step 3: Update project-state.json (compaction recovery tracking)
   - Step 4: Log to domain.record.md (Gojo/Sukuna only)
   - Step 5: Update dev-notes.md (continuity note)
   - Step 6: Run protocol validation (scripts/validate-protocol.py)
   - Step 7: Verify agent compliance (all 9 agents)
   - Step 8: Output parallel workflow guidance
   - Step 9: **Prompt agent to continue tasks** with proper DZP workflow

2. **Slash Command** (`.claude/commands/dzp-roe.md`)
   - User-invocable via `/dzp-roe`
   - Optional context argument: `/dzp-roe working on authentication`
   - Invokes dzp-roe skill programmatically

3. **State Schema Update** (`.protocol-state/project-state.json`)
   - Added `compaction_recovery` top-level key
   - Fields: `last_recovery_timestamp`, `recovery_count`, `recovery_history[]`
   - Tracks all ROE invocations with timestamps and context

4. **Skill Registry Updates**
   - `SKILL_REGISTRY.md` v3.0.0 - Added dzp-roe to Custom Skills Registry and Meta Skills category
   - `AGENT_SKILLS_MAP.yaml` v4 - Mapped dzp-roe to ALL 9 agents (gojo, yuuji, megumi, nobara, todo, maki, panda, inumaki, sukuna)

5. **Task Continuation Feature**
   - Step 9 extracts last 10 dev-notes.md entries to provide context
   - Prompts agent to resume previous work
   - Provides implementation routing guidance (5 agents → Yuuji)
   - Reinforces parallel vs sequential workflow patterns

### Changed

- `project-state.json`: Protocol version 8.9.0 → 8.10.0
- All skill-related files updated to reference v8.10.0

### Documentation

- `VERSION.md`: Updated to v8.10.0 with release summary
- `CHANGELOG.md`: This entry
- `README.md`: Added `/dzp-roe` to key features
- `SLASH_COMMANDS_INSTALLATION.md`: Added `/dzp-roe` installation instructions
- `AI_INSTRUCTIONS.md`: Added post-compaction recovery workflow
- `SUKUNA-REPORT.md`: Documented UPDATE-2025-12-25-002

---

## [8.9.0] - 2025-12-22

### Added

#### **Claude Skills Integration** - 16 Anthropic skills mapped to all 9 agents

**Purpose**: Integrate official Claude Skills from Anthropic repository for enhanced document creation, testing, and design capabilities.

1. **Anthropic Skills (16 total)**
   - Document Skills: `pdf`, `docx`, `xlsx`, `pptx`
   - Design Skills: `frontend-design`, `canvas-design`, `brand-guidelines`, `theme-factory`
   - Development Skills: `web-artifacts-builder`, `webapp-testing`, `mcp-builder`
   - Meta Skills: `skill-creator`, `doc-coauthoring`
   - Communication: `internal-comms`, `slack-gif-creator`, `algorithmic-art`

2. **Skill Mapping** (`protocol/skills/AGENT_SKILLS_MAP.yaml` v3)
   - Gojo: skill-creator, pptx, internal-comms, doc-coauthoring
   - Yuuji: web-artifacts-builder, webapp-testing, mcp-builder, skill-creator
   - Megumi: pdf, webapp-testing, doc-coauthoring
   - Nobara: pdf, docx, pptx, frontend-design, web-artifacts-builder, brand-guidelines, canvas-design, theme-factory, algorithmic-art, slack-gif-creator
   - Todo: xlsx, doc-coauthoring
   - Maki: xlsx, theme-factory, doc-coauthoring
   - Panda: xlsx, mcp-builder, doc-coauthoring
   - Inumaki: pdf, docx, internal-comms, doc-coauthoring
   - Sukuna: skill-creator, doc-coauthoring

3. **Skill Registry Update** (`protocol/skills/SKILL_REGISTRY.md` v2.0.0)
   - Added Anthropic Skills table with all 16 skills
   - Added Sukuna skills section
   - Risk levels documented per skill

---

#### **Implementation Restrictions** - 5 agents now route code changes through Yuuji

**Purpose**: Ensure code implementation is centralized through Yuuji for quality control.

1. **Restricted Agents** (Cannot use Edit/Bash for code)
   - Nobara: Removed `edit` tool (already no bash)
   - Todo: Removed `edit`, `bash` tools
   - Maki: Removed `edit`, `bash` tools
   - Panda: Removed `edit`, `bash` tools
   - Inumaki: Removed `edit`, `bash` tools

2. **Allowed Actions for Restricted Agents**
   - Create documentation and reports (Write tool)
   - Design specifications and schemas
   - Analyze code and provide recommendations
   - Invoke Yuuji for implementation via `@implementation` handoff

3. **Preserved Capabilities**
   - Megumi: Original restrictions maintained (no edit, no bash)
   - Yuuji: Full implementation access (edit, bash)
   - Gojo: Full access for protocol management
   - Sukuna: Full access for system updates

---

#### **File Rotation System** - Generalized rotation for dev-notes.md and security-review.md

**Purpose**: Prevent agent state files from exceeding size limits.

1. **New Script** (`scripts/file-rotate.py`)
   - Supports dev-notes.md and security-review.md
   - 25k character threshold (configurable)
   - Archives to `.protocol-state/archive/{filename}/`
   - Keeps last 10 archives
   - Preserves header section after rotation

2. **Usage**
   - Check: `python scripts/file-rotate.py --file dev-notes --check`
   - Rotate: `python scripts/file-rotate.py --file dev-notes --rotate`
   - List supported files: `python scripts/file-rotate.py --list`

---

#### **OWASP Cheatsheet Integration** - Megumi enhanced with comprehensive security references

**Purpose**: Equip Megumi with OWASP Cheatsheet Series for security reviews.

1. **Tier 1 - Critical** (Always Reference)
   - Authentication, Session Management, Password Storage
   - SQL Injection, Input Validation, Query Parameterization
   - XSS Prevention, DOM XSS Prevention, CSRF Prevention

2. **Tier 2 - High Priority**
   - Cryptographic Storage, Key Management, Secrets Management
   - Content Security Policy, Clickjacking Defense
   - REST Security, GraphQL Security

3. **Tier 3 - Context-Specific**
   - Docker Security, Kubernetes Security
   - NodeJS, Java, Django, DotNet Security

4. **Security Review Format**
   - Findings now include OWASP cheatsheet references
   - Direct links to relevant cheatsheets per vulnerability type

---

### Changed

- **All 9 Agent Files**: Updated to v8.9.0, added `skill` tool
- **Nobara, Todo, Maki, Panda, Inumaki**: Removed edit/bash tools, added implementation restriction comments
- **AGENT_SKILLS_MAP.yaml**: Updated to v3 with complete Anthropic skill mapping
- **SKILL_REGISTRY.md**: Updated to v2.0.0 with Anthropic skills table
- **Megumi**: Added OWASP Cheatsheet Quick Reference section

### Security

- Implementation restrictions prevent unauthorized code modifications by design-focused agents
- File rotation preserves audit trail in timestamped archives
- OWASP cheatsheet integration provides standardized security reference

---

## [8.8.0] - 2025-12-06

### Added

#### **Domain Record System** - Shared notes repository for Gojo and Sukuna

**Purpose**: Prevent agent files from exceeding 25k token limit while enabling crash recovery

1. **File Structure** (`.dzp-domain/`)
   - `domain.record.md` - Shared notes repository (Gojo + Sukuna ONLY access)
   - `archive/` - Rotated archives (auto-rotation at 5,000 lines)
   - `.rotation-metadata.json` - Rotation history tracking

2. **Content Types**
   - Session notes and observations
   - Strategic decisions with rationale
   - Protocol update tracking
   - Learning patterns across sessions
   - Crash recovery checkpoints

3. **Access Control** (9 agent files updated)
   - Gojo: Full READ/WRITE access with operational documentation
   - Sukuna: Full READ/WRITE access with update-focused documentation
   - All other agents: DENIED (yuuji, megumi, nobara, todo, maki, panda, inumaki)
   - File access restrictions added to all 7 non-Gojo/Sukuna agent files

4. **Auto-Rotation Script** (`scripts/domain-record-rotate.py`)
   - Check size: `python scripts/domain-record-rotate.py --check`
   - Force rotation: `python scripts/domain-record-rotate.py --rotate`
   - Archives at 5,000 line threshold
   - Keeps last 10 rotations (configurable)
   - Windows-compatible output (no emoji encoding errors)

5. **Configuration** (`protocol.config.yaml`)
   - Added `domain_record` section with rotation, access, and git tracking settings
   - Conditional git tracking (gitignored by default, user-configurable)
   - Integrity monitoring enabled

6. **File Protection** (`.protocol-state/system-update-framework/file-classifications.json`)
   - Domain record added to `project_state_protected` (NEVER_OVERWRITE during updates)
   - Archives protected from system updates

7. **Validation Integration** (`scripts/validate-protocol.py`)
   - Added `validate_domain_record()` function
   - Checks line count against threshold
   - Integrated into `--check` workflow
   - Windows-compatible output

8. **File Integrity** (`.protocol-state/security/file-integrity.json`)
   - SHA-256 hash tracking for domain.record.md
   - Integrity monitoring enabled

**Documentation Updated**:
- README.md - Added domain record to v8.8.0 key features and file structure
- docs/FAQ.md - Added 3 Q&A entries (what is domain.record.md, why access restricted, how to rotate)
- PROTOCOL_QUICKSTART.md - Added to file structure and key concepts
- docs/installation/IMPLEMENTATION_GUIDE.md - Added configuration section with usage examples

---

#### **Phase 4: Tier Validation System + Dual Learning Systems** - Intelligent tier workflow completion

This release completes the tier system evolution with active validation, automatic statistics tracking, and opt-in learning capabilities for continuous protocol improvement.

**Component 1: Tier Validation System**
1. **Working Directory Verification** (`scripts/verify_working_directory.py`)
   - Validates pwd before operations (prevents accidental cross-project modifications)
   - Integrated into all Phase 4 scripts (tier-statistics.py, sukuna-learn.py, gojo-learn.py)
   - Safety-first approach: fail fast if not in correct project

2. **Tier Configuration** (`protocol/tier-defaults.yaml`)
   - 18KB comprehensive tier profile configuration
   - Tier 1 (Rapid): No tests, no security review, minimal docs
   - Tier 2 (Standard): TDD + security review, 80% coverage [DEFAULT]
   - Tier 3 (Critical): Enhanced tests + dual review, 95% coverage
   - Snapshot frequency, validation rules, typical use cases per tier

3. **Agent Tier Validation** (All 9 .agent.md files updated)
   - Added `## ✅ TIER VALIDATION (v8.8.0+)` sections to all agents
   - Step-by-step tier determination process (user flag → session state → default)
   - Tier requirements verification before task execution
   - Sukuna: Special tier-exempt status (system updates inherently Tier 3)

4. **Backward Compatibility** (`protocol.config.yaml`)
   - 30-day migration grace period (migration_start_date: 2025-12-06)
   - Legacy mode support for gradual adoption
   - allow_tier_bypass configuration option

**Component 2: Tier Statistics**
1. **Statistics Tracking** (`scripts/tier-statistics.py`)
   - 426-line utility for automatic tier usage tracking
   - Records 5 event types: tier_selected, tier_completed, tier_bypassed, tier_violated, tier_transitioned
   - Tracks compliance rates, average duration per tier, bypass/violation counts
   - Rolling event log (last 100 events)

2. **Reporting Capabilities**
   - Text, Markdown, and JSON output formats
   - Markdown format integrated with Trigger 19 intelligence reports
   - Last 30 days usage statistics
   - Tier distribution analysis

3. **Input Sanitization** (Added during adversarial testing)
   - Filters non-alphanumeric characters from agent/feature names
   - Prevents SQL injection and path traversal data pollution
   - 100-character limit enforcement
   - Warnings on sanitized input

**Component 3: Dual Learning Systems** - USER + PROJECT Protected
1. **Sukuna Learning System** (`scripts/sukuna-learn.py`)
   - Learns from protocol update patterns (file dependencies, duration, rollback triggers)
   - 590-line implementation with comprehensive safety checks
   - Project isolation via 8-char hash in filename (sukuna-patterns-{hash}.json)
   - Confidence threshold: 80%+ with 3+ sample minimum
   - Sensitive data pattern detection (passwords, API keys, emails, etc.)
   - Security-weakening pattern rejection (bypass validation, disable auth, etc.)
   - Opt-in by default (learning.enabled: false)

2. **Gojo Learning System** (`scripts/gojo-learn.py`)
   - Learns from tier selection patterns (feature keywords → tier recommendations)
   - 680-line implementation with USER protection guarantees
   - Feedback mechanism: "Was this helpful?" with auto-dismiss after 3x "not helpful"
   - Exploitative pattern rejection (user fatigue, stress exploitation, etc.)
   - Suggestions only (never automatic actions)
   - Fixed CLI messaging to accurately report when learning is disabled

3. **USER Protection Guarantees**
   - Suggestions only, never automatic actions
   - Instant disable capability (no confirmation required)
   - No pressure tactics or manipulation
   - Easy dismiss mechanism
   - Remember dismissals (don't re-suggest)
   - Kill Switch integration (learning pauses during emergencies)
   - No exploitation of user vulnerabilities

4. **PROJECT Protection Guarantees**
   - Project isolation (separate learning DB per project)
   - Sensitive data sanitization
   - No security-weakening patterns accepted
   - No quality-reduction patterns accepted
   - Confidence threshold enforcement (80%+)
   - Minimum sample size enforcement (3+)
   - No automatic code execution
   - Privacy-first (local-only, gitignored, instantly clearable)

**Documentation**
- `MIGRATION_v8.7_to_v8.8.md`: 500+ line comprehensive migration guide
- `.protocol-state/system-update-framework/learning-systems-verification-checklist.md`: 35 test cases for dual learning systems
- Updated `protocol.config.yaml` with 60+ lines of learning system configuration

**Safety & Testing**
- Sukuna adversarial testing completed (all 3 components tested)
- No critical issues found (minor polish items addressed)
- Comprehensive USER + PROJECT protection verified
- Kill Switch integration tested

### Changed

- **protocol.config.yaml**: Version 8.7.0 → 8.8.0
  - Added `backward_compatibility` section for tier validation migration
  - Added `learning` section (60+ lines) with Sukuna + Gojo learning configs
  - Updated `versioning.protocol_version: "8.8.0"`

- **All 9 Agent Files**: Added tier validation sections
  - `protocol/yuuji.agent.md`: Tier validation workflow
  - `protocol/megumi.agent.md`: Tier validation workflow
  - `protocol/nobara.agent.md`: Tier validation workflow
  - `protocol/gojo.agent.md`: Tier coordination workflow
  - `protocol/todo.agent.md`: Tier validation workflow
  - `protocol/maki.agent.md`: Tier validation workflow
  - `protocol/panda.agent.md`: Tier validation workflow
  - `protocol/inumaki.agent.md`: Tier validation workflow
  - `protocol/sukuna.agent.md`: Tier-exempt status documentation

- **.gitignore**: Added learning patterns exclusions
  - `.protocol-state/learning/` directory
  - `*-patterns-*.json` files
  - `sukuna-patterns-*.json` and `gojo-patterns-*.json` specifically
  - `metadata.json` for learning systems

### Fixed

- **gojo-learn.py**: Fixed misleading CLI success messages
  - `record_tier_selection()` now returns boolean (True/False)
  - CLI checks return value before displaying success message
  - Accurate "[INFO] Learning disabled" message when not recording
  - Helpful enable instructions provided

- **tier-statistics.py**: Added input sanitization
  - New `_sanitize_input()` method filters malicious input
  - Blocks SQL injection attempts (e.g., `'; DROP TABLE`)
  - Blocks path traversal attempts (e.g., `../../../etc/passwd`)
  - 100-character length limit
  - Warnings displayed when input is sanitized

- **sukuna.agent.md**: Added missing tier validation section
  - Documented tier-exempt status (system updates are inherently Tier 3)
  - Explained why Sukuna doesn't follow standard tier workflow
  - Clarified Sukuna's role in validating tier requirements in user code

## [8.7.0] - 2025-12-03

> **📌 Release Note**: This release bundles two milestones:
> Nine-Agent System Formalization (completed 2025-12-02) and the Custom Agent Security Framework (completed 2025-12-03).
> Both are published together here for streamlined deployment.

### Added

#### **Custom Agent Security Framework** - Comprehensive security for user-created agents

Sukuna's red team assessment identified critical vulnerabilities in the custom agent system (CUST-CRIT-001 through CUST-CRIT-008). This release implements comprehensive security enforcement to protect against malicious custom agents.

**New Security Components**:
1. **Pre-Invocation Validation** (`scripts/validate-custom-agents.py`)
   - Namespace protection (prevents core agent impersonation)
   - YAML sanitization (blocks code injection patterns)
   - Tool permission validation
   - File integrity checks

2. **Runtime Monitoring System** (`.protocol-state/custom_agent_monitor.py`)
   - Tracks all custom agent invocations
   - Enforces tool permission filtering
   - Detects file modifications via SHA-256 hashing
   - Identifies anomalous behavior patterns
   - Automatic quarantine for policy violations

3. **Audit Logging** (`.protocol-state/authorization/custom-agent-audit.log`)
   - Tamper-evident activity logs
   - Tool usage tracking
   - Validation failures
   - Quarantine events

4. **Registry System** (`.protocol-state/custom-agent-registry.json`)
   - Centralized custom agent database
   - Invocation history (last 10 per agent)
   - File modification tracking
   - Quarantine status

**Security Policies Enforced**:
- **Namespace Protection** (CUST-CRIT-002): Custom agents must use `custom-` prefix
- **Tool Permissions** (CUST-CRIT-003): Three-tier permission system (default/approval/forbidden)
- **YAML Sanitization** (CUST-CRIT-004): Blocks `__proto__`, `eval:`, `exec:`, template injection
- **File Immutability** (CUST-CRIT-008): Prevents self-modification and protocol file tampering
- **Rate Limiting** (CUST-HIGH-001): Max 10 invocations/minute per agent
- **Gojo Oversight** (CUST-CRIT-006): Complete visibility into custom agent activity

**Documentation**:
- `docs/security/CUSTOM_AGENT_SECURITY_POLICY.md` - User-facing security policy
- `.protocol-state/gojo-custom-agent-security-guide.md` - Gojo integration guide
- Updated `docs/guides/CREATING_CLAUDE_AGENTS.md` with security warnings

**Configuration**:
- Added `custom_agent_security` section to `protocol.config.yaml`
  - Configurable tool permissions
  - Namespace rules
  - Rate limiting settings
  - Monitoring options

### Changed

- **protocol.config.yaml**: Version 8.7.0 → 8.7.0, config_version 2.6 → 2.7
- **CREATING_CLAUDE_AGENTS.md**: Added comprehensive security warning section
- **.gitignore**: Added custom agent registry and audit log exclusions

### Fixed

#### **CodeRabbit + GitHub Copilot Review Fixes** (PR #59)

Addressed all code review feedback from automated PR review:

1. **session_monitor.py**: Fixed type inconsistency in `should_block_operation()`
   - Changed return type from `Tuple[bool, Optional[str]]` → `Tuple[bool, str]`
   - Changed all `return False, None` → `return False, ""`
   - Ensures consistent string semantics (tests expected empty string, not None)

2. **session_monitor.py**: Fixed infinite loop bug in `update_interaction()`
   - Added retry counter with max retries (default: 1)
   - Added proper error handling with `RuntimeError` exceptions
   - Prevents infinite recursion via circuit breaker pattern
   - Protects against session state corruption

3. **session_monitor.py**: Added regex pattern validation (ReDoS prevention)
   - Added `_load_high_risk_patterns()` method with validation
   - Added `_is_safe_regex()` validator checking for catastrophic backtracking
   - Pre-compiles and caches validated patterns at initialization
   - Falls back to safe defaults if config unavailable
   - **Security**: Prevents ReDoS attacks via malicious config patterns

4. **validate-custom-agents.py**: Added path traversal validation
   - Added path resolution and validation before file access
   - Checks that resolved path is within `.claude/agents/` directory
   - Returns error if path traversal detected
   - **Security**: Prevents malicious agents from accessing arbitrary files

5. **custom_agent_monitor.py**: Persisted rate limit timestamps
   - Added `rate_limit_timestamps` field to `AgentRegistryEntry` dataclass
   - Modified `validate_rate_limit()` to load/save timestamps from registry JSON
   - Removed in-memory `_invocation_timestamps` dict
   - **Security**: Enforces rate limiting across process restarts

6. **tests/test_session_monitor.py**: Fixed spelling error in docstring
   - Changed "stop emoji" → "🛑 emoji (stop sign)" for clarity

7. **session_monitor.py**: Fixed None handling crash in `is_high_risk_operation()`
   - Changed parameter type from `str` to `Optional[str]`
   - Added type guard to handle None, non-string, and empty inputs

8. **IMPLEMENTATION_GUIDE.md**: Updated all v8.5.1 → v8.7.0 version references
   - Fixed in-place upgrade paths
   - Updated Claude Code/GitHub Copilot setup instructions
   - Changed "eight agents" → "nine agents" + added Sukuna
   - Updated system prompt with complete 9-agent list
   - Fixed safety config (`work_session_monitoring` → `session_tracking`)

9. **tests/test_session_monitor.py**: Updated test comment to reflect actual guard behavior

#### **New Test Coverage**

- **tests/test_custom_agent_monitor.py** (60+ test cases)
  - Registry operations
  - Rate limiting with persistence
  - Tool permissions validation
  - Agent registration and invocation tracking
  - File integrity monitoring
  - Quarantine functionality
  - Anomaly detection
  - Invocation history
  - Audit logging

- **tests/test_validate_custom_agents.py** (50+ test cases)
  - Configuration loading
  - File size validation
  - Agent name validation
  - YAML structure validation
  - YAML content security validation
  - Tool permissions validation
  - Path traversal protection
  - File extension validation
  - Validation result reporting

#### **Nine-Agent System Formalization** - Sukuna recognized as 9th agent

**Full Documentation Update:**
- All external-facing documentation updated from "eight-agent" to "nine-agent" system
- Sukuna (System Update Adversary) formalized in version history
- Complete architecture diagram updated to reflect 9 agents

**Key Changes**:
- **VERSION.md** - Updated to reflect Nine-Agent System (Core Three + Gojo + Extended Four + Sukuna)
- **README.md** - All agent count references updated to "nine-agent"
- **PROTOCOL_QUICKSTART.md** - Quick start guide updated to 9-agent system
- **protocol/CLAUDE.md** - Main protocol file updated to reflect 9-agent architecture
- **protocol/gojo.agent.md** - Domain diagram updated to show all 9 agents
- **docs/FAQ.md** - FAQ updated with 9-agent references
- **AI_INSTRUCTIONS.md** - System overview updated

**Sukuna's Role Clarified**:
- System Update Adversary (Gojo-Invoked Only)
- Adversarial-but-aligned reviews for protocol updates
- Only Gojo or User may invoke Sukuna
- Relationship to Gojo: Enemies by design, allies by purpose

### Changed

- **protocol.config.yaml**: Version 8.7.0 → 8.7.0, config_version 2.6 → 2.7
- **CREATING_CLAUDE_AGENTS.md**: Added comprehensive security warning section
- **.gitignore**: Added custom agent registry and audit log exclusions
- All references to "eight-agent system" replaced with "nine-agent system"
- Architecture documentation updated to explicitly include Sukuna as 9th agent
- Version consistency enforced across all CORE files

### Security

- **11 Critical/High Vulnerabilities Fixed** (CVSS 8.5-9.8):

**Custom Agent Security (Initial Implementation)**:
  - CUST-CRIT-002: Agent name collision (CVSS 9.1) ✅ FIXED
  - CUST-CRIT-003: Self-declared tool permissions (CVSS 8.7) ✅ FIXED
  - CUST-CRIT-004: YAML injection (CVSS 9.0) ✅ FIXED
  - CUST-CRIT-008: Agent self-modification (CVSS 9.2) ✅ FIXED
  - CUST-CRIT-006: Zero Gojo oversight (CVSS 8.9) ✅ FIXED

**Code Review Security Fixes**:
  - Path Traversal Vulnerability: Agent file path validation (CRITICAL) ✅ FIXED
  - Regex Injection (ReDoS): High-risk pattern validation (CRITICAL) ✅ FIXED
  - Rate Limit Bypass: Timestamp persistence across restarts (HIGH) ✅ FIXED
  - Infinite Loop Bug: Circuit breaker in update_interaction (HIGH) ✅ FIXED
  - Type Safety: Consistent return types in should_block_operation (MEDIUM) ✅ FIXED
  - None Handling: Type guard in is_high_risk_operation (MEDIUM) ✅ FIXED

**Threat Model**: Protects against malicious custom agents, compromised agent files, privilege escalation, supply chain attacks, path traversal, ReDoS attacks, and rate limit bypass.

**Attack Scenarios Mitigated**:
1. ❌ Core agent impersonation (Gojo hijack)
2. ❌ Arbitrary code execution via bash tool
3. ❌ Self-modification for privilege escalation
4. ❌ YAML code injection
5. ❌ Protocol file tampering
6. ❌ Unmonitored agent activity
7. ❌ Tool permission bypass
8. ❌ Path traversal to arbitrary files
9. ❌ ReDoS attacks via malicious regex patterns
10. ❌ Rate limit bypass via process restart

**Enforcement**: Pre-Invocation Validation + Runtime Monitoring + Path Validation + Regex Sanitization + Automatic Quarantine

---

## [8.5.1] - 2025-11-26

### Added

#### **Modular Protocol Architecture** - Token optimization through shared modules

**New Directory:** `protocol/modules/`

Contains 7 reusable module files that define shared protocol behaviors:
- `EMERGENCY_STOP_PROTOCOL.md` - Kill switch behavior for all agents
- `USER_LEVEL_ADAPTATION.md` - Beginner/Intermediate/Expert adaptation
- `MASK_MODE_BEHAVIOR.md` - JJK theme toggle behavior
- `MISSION_CONTROL_ISOLATION.md` - Identity boundaries for non-Gojo agents
- `ESCAPE_PATH_PROTOCOL.md` - Stuck workflow guidance
- `BINDING_OATH.md` - Agent commitment to protocol
- `SAFETY_FIRST.md` - Safety-first principles

**Token Reduction:**
- Replaced ~1,755 lines of duplicated content across 8 agents with module references
- Each agent now includes condensed ~60-line domain-specific addendums
- Estimated 40-60% reduction in agent file token counts

**Module Reference Pattern:**
```markdown
## ⛔ EMERGENCY STOP PROTOCOL (v8.5.1+)

**Full Protocol**: See `protocol/modules/EMERGENCY_STOP_PROTOCOL.md`

**My Domain-Specific Behavior** (Agent Name):
| Aspect | My Specifics |
|--------|--------------|
| **Domain Work** | [Agent-specific work] |
| **What I Halt** | [Agent-specific halt behavior] |
```

### Changed

- **All 8 protocol agent files** - Updated to v8.5.1, replaced verbose sections with module references
- **All 8 JJK Edition agent files** - Updated to v8.5.1
- **CLAUDE.md** - Updated to v8.5.1
- **README.md** - Updated version references and key features
- **VERSION.md** - Updated with v8.5.1 release information

### Technical Details

**Why Modular Architecture:**
- gojo.agent.md was at 89% token limit, megumi.agent.md at 84%
- Further feature additions were blocked by token constraints
- Shared sections were duplicated 8 times across agents

**Module Benefits:**
- Single source of truth for shared behaviors
- Easier maintenance (update one file, all agents benefit)
- Reduced token consumption per agent invocation
- Cleaner agent files focused on domain expertise

---

## [8.5.0] - 2025-11-26

### Added

#### **Kill Switch Protocol** - Emergency stop with project protection

**New Emergency Stop Mechanism:**
- Instant halt on keywords: STOP, ABORT, CANCEL, EMERGENCY STOP, KILL SWITCH, HALT, SHUTDOWN
- Automatic checkpoint creation to `.dzp-killswitch/checkpoint.json`
- Project protection mode: blocks all deletions during emergency
- Gojo coordinates kill switch activation and recovery
- New Mission Control Option 4: "Resume from Emergency Stop"

**Configuration:**
- `protocol.config.yaml` - New `kill_switch:` section with keyword setup, stop behavior, project protection
- `.dzp-killswitch/` directory - State storage (gitignored, agent-hidden)
- All 8 agent files updated with Emergency Stop Protocol section

#### **User Technical Level System** - Adaptive agent behavior

**Three User Levels:**
- **Beginner**: Detailed explanations, simplified terminology, guided autonomy
- **Intermediate** (default): Balanced explanations, standard terminology
- **Expert**: Minimal explanations, full jargon, maximum autonomy

**Agent Adaptation:**
- All 8 agents adapt communication style based on `user.technical_level.current`
- Gojo prompts for level selection at first invocation if not set
- Users can change level anytime: "Change my level to [beginner/intermediate/expert]"

**Configuration:**
- `protocol.config.yaml` - New `user.technical_level:` and `technical_level_presets:` sections

#### **Token Optimization** - Gojo modularization

**Modular Procedures:**
- Created `protocol/gojo-procedures/OPERATIONAL_PROCEDURES.md`
- Extracted detailed procedures from gojo.agent.md
- Reduced gojo.agent.md from ~27K to ~24.5K tokens (under 25K limit)

### Changed

- **protocol.config.yaml** - Added kill_switch, user.technical_level, technical_level_presets sections
- **All 8 agent files** - Added Emergency Stop Protocol and User Level Adaptation sections
- **gojo.agent.md** - Added Kill Switch Coordination, Option 4, User Level prompting, modular procedures reference
- **CLAUDE.md** - Added Kill Switch Protocol and User Technical Level System documentation sections

---

## [8.4.1] - 2025-11-25

### Changed

#### **Agent File Cleanup** - Cleaner separation of concerns

**Removed from Non-Gojo Agents:**
- Removed verbose "Gojo Awareness" sections from Yuuji, Megumi, Nobara, Todo, Maki, Panda, and Inumaki agent files
- Replaced with concise `**Mission Control**: Gojo (Protocol Guardian & Domain Supervisor)` reference
- Each agent now focuses purely on its own domain expertise while maintaining awareness of hierarchy

**Rationale:**
- Reduces cognitive overhead in agent files
- Cleaner separation of concerns - agents focus on their specialization
- Mission Control (Gojo) handles coordination; individual agents handle execution
- Maintains team structure awareness without verbose deference patterns

#### **JJK Character Reference Added** - Enhanced character context

**Added to All 8 Protocol Agent Files:**
- New `## 📍 JJK CHARACTER REFERENCE` section with Canon Series, Character Wiki, Cursed Technique, Domain Expansion, and Agent Adaptation mapping

**Added to Core Four DZA Files:**
- YUUJI.md, MEGUMI.md, NOBARA.md, GOJO.md now have JJK Character Reference sections matching Extended Four format

#### **Research Mode Updated** - Full 8-agent support

**RESEARCH_MODE.md expanded to include:**
- Todo, Maki, Panda, Inumaki added to allowed_agents
- Cadence settings for Extended Four agents
- Directory structure and JSON schema for Extended Four research folders
- Role-specific focus table entries for all 8 agents

**Files Updated:**
- All 8 `protocol/*.agent.md` files
- All 8 `Domain Zero Agents - Full JJK Edition/*.md` files
- `protocol/RESEARCH_MODE.md`

---

## [8.4.0] - 2025-11-25

### Added

#### **Full 8-Agent Integration** - Expand from four-agent to eight-agent system

**New Agent Files Created:**
- `protocol/todo.agent.md` - Database & Backend Specialist (Boogie Woogie)
- `protocol/maki.agent.md` - Performance Optimization Specialist (Heavenly Restriction)
- `protocol/panda.agent.md` - Build & Integration Specialist (Multi-Core System)
- `protocol/inumaki.agent.md` - API & Communication Specialist (Cursed Speech)

**Agent Capabilities:**
- **Todo**: Schema design, data migrations, query optimization, ORM configuration
- **Maki**: Lighthouse audits, bundle analysis, profiling, zero-overhead optimization
- **Panda**: CI/CD pipelines, GitHub Actions, Docker, multi-core build modes (Panda/Gorilla/Triceratops)
- **Inumaki**: REST API design, GraphQL schemas, WebSocket protocols, OpenAPI specs

**Each Agent Includes:**
- YAML frontmatter with 7 required fields (target, name, description, argument-hint, model, tools, handoffs)
- Tool Access Matrix with full/conditional/prohibited permissions
- Declarative handoff definitions for agent-to-agent transitions
- Role-specific escape path patterns (soft requirements, progressive fallback, graceful degradation)
- JJK-themed domain banners and terminology

#### **Extended Agent Skills** - New skills in AGENT_SKILLS_MAP.yaml

**Todo Skills:**
- `schema-design` - Database schema design
- `migration-planning` - Data migration strategies
- `query-optimization` - SQL/ORM query optimization

**Maki Skills:**
- `lighthouse-audit` - Web performance audits
- `bundle-analysis` - JavaScript bundle optimization
- `profiling-tools` - Runtime profiling

**Panda Skills:**
- `github-actions` - CI/CD workflow creation
- `docker-compose` - Container orchestration
- `build-optimization` - Build pipeline optimization

**Inumaki Skills:**
- `openapi-design` - OpenAPI/Swagger specification
- `graphql-schema` - GraphQL schema design
- `websocket-protocol` - Real-time communication

### Changed

#### **protocol/CLAUDE.md** - Updated to 8-agent system

**System Overview:**
- Changed "four-agent" to "eight-agent" throughout
- Added "The Eight Agents" section with Core Four + Extended Four
- Added invocation patterns for Todo, Maki, Panda, Inumaki
- Updated token efficiency table to include all 8 agents (~29,500 tokens, ~14.8%)

#### **protocol/gojo.agent.md** - Domain supervision for all 8 agents

**New Handoff Triggers:**
- `@brief-database` → Todo
- `@brief-performance` → Maki
- `@brief-build` → Panda
- `@brief-api` → Inumaki

**Updated Domain Diagram:**
- Visual hierarchy showing all 8 agents under Gojo's supervision
- Core four (Yuuji, Megumi, Nobara) with extended four underneath

#### **protocol.config.yaml** - Extended configuration

**New Entries:**
- `roles.enabled` - Now includes all 8 agents
- `output_style` - Styling for new agents
- `unmasked_names` - Professional mode names for new agents
- `self_identification.agents` - Emoji/domain/subtitle for new agents
- `paths` - File paths for new agent files

#### **All Core Agent Files** - Version sync

**Updated:**
- `protocol/yuuji.agent.md` - protocol_version: 8.4.0, agent_file_version: 1.1.0
- `protocol/megumi.agent.md` - protocol_version: 8.4.0, agent_file_version: 1.1.0
- `protocol/nobara.agent.md` - protocol_version: 8.4.0, agent_file_version: 1.1.0
- `protocol/gojo.agent.md` - protocol_version: 8.4.0

### Documentation

**Files Created:**
- `protocol/todo.agent.md` (~310 lines)
- `protocol/maki.agent.md` (~320 lines)
- `protocol/panda.agent.md` (~315 lines)
- `protocol/inumaki.agent.md` (~330 lines)

**Files Modified:**
- `protocol/CLAUDE.md` - 8-agent system documentation (~160 lines added)
- `protocol/gojo.agent.md` - Domain supervision (~100 lines added)
- `protocol/skills/AGENT_SKILLS_MAP.yaml` - New agent skills (~50 lines added)
- `protocol.config.yaml` - Agent configurations (~40 lines added)

### No Breaking Changes

- All changes are backward compatible
- Existing four-agent workflows unchanged
- New agents are optional extensions
- Invocation patterns follow existing conventions

### Upgrade Notes

**No action required** - This is a backward-compatible minor release.

**Optional: Use Extended Agents**
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

---

## [8.3.1] - 2025-11-24

### Added

#### **Agent-Specific Escape Path Protocol** - Tailored guidance per agent

**Files Updated:**
- `protocol/yuuji.agent.md` - New "🚨 ESCAPE PATH PROTOCOL (v8.3.1)" section
- `protocol/megumi.agent.md` - New "🚨 ESCAPE PATH PROTOCOL (v8.3.1)" section
- `protocol/nobara.agent.md` - New "🚨 ESCAPE PATH PROTOCOL (v8.3.1)" section
- `protocol/gojo.agent.md` - New "🚨 ESCAPE PATH PROTOCOL (v8.3.1)" section

**Each Section Includes:**
- Role-specific explanation of why escape paths matter
- Four escape path patterns tailored to agent function
- Scenario-specific fallback guidance
- Commitment statements (what agents will NEVER and ALWAYS do)

### Verified

#### **Instruction Confirmation Protocol** - Confirmed implementation

All four agents now have the "🔁 INSTRUCTION CONFIRMATION LOOP" section properly implemented, referencing `docs/INSTRUCTION_CONFIRMATION_PROTOCOL.md`.

### Changed

- Updated all agent file headers to v8.3.1
- Updated CLAUDE.md version to v8.3.1
- Updated VERSION.md with v8.3.1 release information
- **Version Consistency** - Updated all public-facing documents to v8.3.1

---

## [8.3.0] - 2025-11-22

### Added

#### **Subagent Escape Paths** - Critical subagent resilience system

**Problem Addressed:**
- Subagents (spawned via Task tool) could hang, fail silently, or output "Done" without results
- Hard requirements with no fallback caused infinite loops or silent failures
- Missing information with no recovery path led to unhelpful outputs

**Escape Path Patterns:**
- **Pattern 1: Soft Requirements** - Preferred over hard MUST requirements
  - Example: Check if file exists (PREFERRED) with fallback if missing
- **Pattern 2: Progressive Fallback** - Try A, if not B, if not C, if not use defaults
- **Pattern 3: Graceful Degradation** - Provide partial results when full completion impossible
- **Pattern 4: Clear "I'm Blocked" Output** - Structured template for when truly stuck

**Agent-Specific Escape Paths:**
- **Yuuji**: Test framework unknown → ask user; backup fails → warn and confirm
- **Megumi**: Code inaccessible → ask for paths; no findings → explicitly state scope
- **Gojo**: No state file → create new; corrupted state → ask user to reset

**Implementation in Task Tool:**
- All Task tool prompts should include escape instructions
- Never hang silently or output "Done" without results
- BLOCKED template provided for clear communication

#### **Skill-Builder Skill** - Rapid skill creation tool

**New File:** `protocol/skills/skill-builder.md`

**Purpose:** Create properly formatted skills quickly with consistent structure

**Features:**
- Template for consistent skill format
- Mandatory escape path requirements for all skills
- AskUserQuestion integration patterns
- Quality checklist (8 items) for new skills
- Meta escape paths (handles own uncertainty)

**Skill Creation Workflow:**
1. Gather requirements via AskUserQuestion
2. Generate skill template with proper structure
3. Add escape paths for all requirements
4. Register in AGENT_SKILLS_MAP.yaml

#### **Skills Token Efficiency Guide** - Best practices for skill usage

**Documentation Added to IMPLEMENTATION_GUIDE.md:**
- Why skills matter (token savings, consistency, reduced context)
- Skill types (Example, Document, Custom)
- Recommended skills by agent (Yuuji, Megumi, Nobara, Gojo)
- Skill invocation pattern: `skill: "skill-name"`

**Skill Recommendations:**
- **Yuuji**: webapp-testing, tdd-checklist, async-patterns, testing-fixtures
- **Megumi**: owasp-checklist, threat-modeling, jwt-audit, secrets-review
- **Nobara**: a11y-review, ux-writing, onboarding-flows
- **Gojo**: skill-builder, protocol-verify, release-briefing, version-audit

#### **AskUserQuestion Integration Guide** - Enhanced user interaction

**Why AskUserQuestion is Essential:**
- Nice UI: Multiple-choice options instead of free-form text
- Reduced Ambiguity: Users select from defined choices
- Better UX: Clear decision points in workflow
- Token Efficiency: Shorter, more focused responses

**When to Use (ALWAYS):**
- Tier selection (rapid/standard/critical)
- Approach decisions (multiple valid paths)
- Missing information (what framework? what database?)
- User preferences (strict mode? verbose output?)
- Confirmation before destructive actions
- Clarifying ambiguous requirements

**AskUserQuestion Patterns:**
- Pattern 1: Tier Selection (3 options with descriptions)
- Pattern 2: Approach Decision (e.g., JWT vs Session vs OAuth)
- Pattern 3: Missing Information (e.g., test framework)
- Pattern 4: Multi-Select (e.g., security checks to include)

**Agent-Specific Guidance:**
- **Yuuji**: Test framework, tier, database/ORM, API design, error handling
- **Megumi**: Review scope, risk tolerance, compliance requirements, external tools
- **Nobara**: User persona, WCAG level, design system, brand guidelines
- **Gojo**: Project initialization, tier preferences, team config, monitoring

**Best Practices:**
- Max 4 options per question
- Clear, concise labels (1-5 words)
- Helpful descriptions explaining consequences
- Multi-select only when choices aren't mutually exclusive
- Ask early (don't wait until stuck)

#### **Updated Add-to-Memory Prompts** - Copy-paste ready

**Claude.ai/API Prompt** (enhanced):
```
Add to memory: Domain Zero Protocol
[...includes key features: skills, AskUserQuestion, escape paths...]
```

**ChatGPT Custom Instructions** (enhanced):
```
Key features:
- Use skills for common operations (saves tokens)
- Ask clarifying questions frequently (better than guessing)
- All instructions should have escape paths (what to do if blocked)
```

**Claude Code Instructions** (enhanced):
- Same structure with protocol file locations

### Changed

#### **IMPLEMENTATION_GUIDE.md** - Major expansion

**New Sections Added (400+ lines):**
- Subagent Escape Paths (CRITICAL) - Complete escape path system
- Using Skills for Token Efficiency - Skill usage best practices
- AskUserQuestion Integration (CRITICAL) - Enhanced user interaction
- Add-to-Memory Prompts (Copy-Paste Ready) - Updated prompts
- Quick Reference Card - Agent invocation, tier flags, key principles

#### **README.md** - Updated add-to-memory prompts

**Claude Prompt Updates:**
- Added key features section (skills, AskUserQuestion, escape paths)
- Fixed file extension reference (.agent.md)

**ChatGPT Instructions Updates:**
- Added key features section with practical tips

#### **protocol/skills/AGENT_SKILLS_MAP.yaml** - Added skill-builder

**Gojo Custom Skills:**
- Added `skill-builder` - Create new skills rapidly with proper structure

### Documentation

**Files Modified:**
- `IMPLEMENTATION_GUIDE.md` - 400+ new lines with 4 major sections
- `README.md` - Updated add-to-memory prompts (2 sections)
- `protocol/skills/AGENT_SKILLS_MAP.yaml` - Added skill-builder skill

**Files Created:**
- `protocol/skills/skill-builder.md` - Complete skill creation tool (250+ lines)

### No Breaking Changes

- ✅ All changes are backward compatible
- ✅ Existing workflows unchanged
- ✅ Optional enhancements (escape paths improve but don't require changes)
- ✅ Skills system extends but doesn't replace existing patterns

### Key Principles Documented

1. **Always ask rather than guess** - Use AskUserQuestion
2. **Always have an escape path** - Never hang or fail silently
3. **Use skills for common operations** - Save tokens
4. **Test-first for Tier 2/3** - TDD is non-negotiable
5. **User safety first** - Above all other objectives

---

## [8.2.0] - 2025-11-18

### Added

#### **Research Mode Enhancement** - Active agent research implementation

**Agent Research Capabilities:**
- All 4 agents (Yuuji, Megumi, Nobara, Gojo) can now conduct domain-specific research
- Invocation pattern: `"Read [agent].agent.md --research and investigate [topic]"`
- Research Mode specification (v7.2.0) now fully implemented with active invocation

**Research Focus Areas by Agent:**
- **Yuuji (Weekly):** Implementation patterns, TDD tooling, test isolation, async patterns, build performance
- **Megumi (Weekly):** OWASP updates, emerging vulnerabilities, cryptographic standards, CVE trends, compliance standards
- **Nobara (Biweekly):** WCAG guidelines, usability heuristics, onboarding flows, accessibility tooling, inclusive design
- **Gojo (Monthly):** Meta trends, coordination tooling, risk landscape, protocol governance, process optimization

**Research Output Structure:**
- Directory: `.protocol-state/research/` with agent subdirectories
- Structured summaries: `[agent]/[timestamp].summary.md`
- Raw notes: `[agent]/[timestamp].raw.log` (gitignored for privacy)
- Global index: `research-index.json` tracking last session timestamps

**Summary Template Features:**
- Focus questions (3-5 specific research questions)
- Key findings table with sources and confidence indicators (High/Medium/Low)
- Actionable recommendations (experiments, not mandates)
- Source citations with OWASP/WCAG/RFC/CVE mappings
- Privacy protection (raw notes never committed)

**Quality Gates:**
- Minimum 3 primary sources required (OWASP, NIST, W3C, RFC, peer-reviewed)
- High confidence findings require 2+ source corroboration
- Security items mapped to OWASP/CVE/NIST (Megumi only)
- WCAG criterion mapping with A/AA/AAA levels (Nobara only)

**Staleness Monitoring (Gojo enforces):**
- Standard warning: 14+ days without research
- Critical escalation: 7+ days for security/auth/crypto topics (Megumi)
- Research currency status shown in Mission Control interface
- Reminders issued during context restoration

**Research → Implementation Integration:**
- Research findings documented in structured summaries
- User reviews recommendations and approves approach
- Standard tier workflows apply (Tier 1/2/3) for implementation
- Implementation uses current best practices from research

**Example Invocations:**
```bash
"Read yuuji.agent.md --research and investigate pytest fixture best practices"
"Read megumi.agent.md --research and investigate OWASP Top 10 2025 changes"
"Read nobara.agent.md --research and investigate WCAG 2.2 success criteria"
"Read gojo.agent.md --research and investigate multi-agent orchestration patterns"
```

### Changed

#### **protocol/CLAUDE.md** - Mode 4: Research Mode added

**Operational Modes Section:**
- Added comprehensive Research Mode overview (Mode 4)
- Documented research focus by agent with cadence schedules
- Included quality gates and staleness monitoring details
- Added "When to Use" guidance (before critical implementations, periodic updates, standard updates)

**Agent Invocation Patterns:**
- Added research mode examples for all 4 agents (Yuuji, Megumi, Nobara, Gojo)
- Included research flag usage patterns
- Added Nobara invocation section (was missing)

#### **All 4 Agent Files** - Research mode sections added

**yuuji.agent.md (lines 1318-1462):**
- Purpose: Stay current on implementation patterns and TDD tooling
- Research focus: Implementation patterns, TDD tooling, test isolation, async patterns
- Invocation examples: pytest fixtures, async test isolation, FastAPI testing
- Output template and integration with implementation workflows

**megumi.agent.md (lines 2043-2229):**
- Purpose: Maintain OWASP knowledge and track emerging vulnerabilities
- Research focus: OWASP updates, emerging vulnerabilities, cryptography, CVE trends
- Security-specific source prioritization (NIST, CVE database, RFC security specs)
- CVE/NIST cross-reference requirements and risk assessment

**nobara.agent.md (lines 561-739):**
- Purpose: Stay current on WCAG and usability best practices
- Research focus: WCAG guidelines, usability heuristics, onboarding flows, accessibility
- User-centered research prioritization (W3C/WAI, Nielsen Norman Group)
- WCAG criterion mapping with A/AA/AAA compliance levels

**gojo.agent.md (lines 1952-2148):**
- Purpose: Strategic awareness of meta trends and coordination patterns
- Research focus: Meta trends, coordination tooling, risk landscape, protocol governance
- Strategic synthesis with cross-domain insights
- Agent research monitoring responsibilities (staleness detection for all agents)

### Updated

**Core Protocol:**
- `protocol.config.yaml` - Version 8.2.0, config_version 2.2
- `protocol/CLAUDE.md` - Version 8.2.0, Mode 4: Research Mode operational mode
- `.protocol-state/project-state.json` - protocol_version 8.2.0

**Agent Files:**
- `protocol/yuuji.agent.md` - Research mode section (145 lines)
- `protocol/megumi.agent.md` - Research mode section (187 lines)
- `protocol/nobara.agent.md` - Research mode section (179 lines)
- `protocol/gojo.agent.md` - Research mode section (197 lines)

**State Management:**
- `.protocol-state/research/` - Directory structure created with agent subdirectories
- `.protocol-state/research/research-index.json` - Initial index with agent metadata
- `.gitignore` - Already configured for raw.log exclusions (v7.2.0)

### Configuration

Research mode controlled via `protocol.config.yaml`:

```yaml
research:
  enabled: true
  allowed_agents: ["yuuji", "megumi", "nobara", "gojo"]
  cadence:
    yuuji: "weekly"
    megumi: "weekly"
    nobara: "biweekly"
    gojo: "monthly"
  max_session_minutes: 25
  source_policy:
    max_sources: 12
    min_primary_sources: 3
  escalation:
    stale_days_warning: 14
    critical_domain_stale_days: 7
```

### No Breaking Changes

- ✅ Research mode is optional (enabled by default but not required)
- ✅ Existing workflows unchanged (agents function normally without research)
- ✅ All changes are backward compatible
- ✅ Tier system unchanged (1/2/3 workflows still work as before)
- ✅ Invocation patterns extended (research flag added as option)

### Upgrade Notes

**No action required** - This is a backward-compatible minor release.

**Optional: Use Research Mode**
```bash
# Research before critical implementations
"Read megumi.agent.md --research and investigate OWASP Top 10 2025 changes"

# Then implement with current knowledge
"Read yuuji.agent.md --tier critical and implement JWT authentication"
```

**Research Benefits:**
- Stay current with evolving standards (OWASP, WCAG, TDD best practices)
- Evidence-based recommendations with citations
- Reduced risk of implementing outdated patterns
- Structured knowledge updates with confidence indicators

---

## [8.1.0] - 2025-11-18

### Added

#### **Playwright E2E Testing Infrastructure** - Complete end-to-end testing setup

**New Directory Structure:**
- `tests/e2e/` - Complete Playwright test infrastructure
  - `package.json` - Playwright dependencies and test scripts
  - `playwright.config.ts` - Multi-browser configuration (Chromium, Firefox, WebKit)
  - `specs/counter.spec.ts` - Visual demo test with interactive counter
  - `specs/web_smoke.spec.ts` - External site smoke test examples
  - `.gitignore` - Excludes test artifacts (reports, traces, videos)

**NPM Scripts:**
- `npm test` - Run all tests in headless mode
- `npm run test:headed` - Run tests in visible browser window
- `npm run test:ui` - Interactive UI mode for debugging
- `npm run test:debug` - Debug mode with breakpoints
- `npm run report` - Show HTML test report
- `npm run install:browsers` - Install Playwright browsers

**Tier System Integration:**
- **Tier 1 (Rapid):** Optional - Use E2E tests locally for demos only, no security review
- **Tier 2 (Standard):** Recommended - Add E2E smoke tests for critical user flows, Megumi reviews results
- **Tier 3 (Critical):** Required - Comprehensive E2E coverage with traces/videos, run in CI, Megumi examines security flows

**Agent Role Extensions:**
- **Yuuji (Implementation):** Creates/updates E2E tests, ensures repeatability, documents in dev-notes.md
- **Megumi (Security):** Reviews test coverage for OWASP risks, validates traces for auth/payment flows
- **Gojo (Mission Control):** Wires CI to run Playwright on PRs, gates merges, tracks skipped reviews

**VS Code Integration:**
- Tasks configured in `.vscode/tasks.json`:
  - `E2E: Install Playwright Browsers`
  - `E2E: Run (headed)`
  - `E2E: UI Mode`
  - `E2E: Show Report`

**Test Specifications:**
- `counter.spec.ts` - Visual demo with interactive counter (renders HTML, clicks buttons, verifies increments)
- `web_smoke.spec.ts` - External site smoke tests (Playwright docs, GitHub) with app-specific template

**Multi-Browser Support:**
- Chromium (Desktop Chrome)
- Firefox (Desktop Firefox)
- WebKit (Desktop Safari)
- Optional: Mobile viewport testing (commented out, ready to enable)

**Test Artifacts:**
- HTML reports in `playwright-report/`
- Traces captured on first retry
- Screenshots on failure
- Videos retained on failure

### Changed

#### **Documentation**
- ✅ `docs/playwright.md` - Complete Playwright integration guide added
- ✅ Protocol mapping for Tier 1/2/3 documented
- ✅ Agent role documentation updated with E2E responsibilities
- ✅ Setup instructions for Windows PowerShell
- ✅ Visual testing guidance (headed mode, UI mode, reports)

### No Breaking Changes

- ✅ Existing workflows unchanged
- ✅ Agent files unchanged (yuuji.agent.md, megumi.agent.md, gojo.agent.md)
- ✅ Tier system unchanged (1/2/3 workflows still work as before)
- ✅ Invocation patterns unchanged
- ✅ Optional enhancement (not required for existing users)

### Upgrade Notes

**No action required** - This is a backward-compatible release.

**Optional: Enable Playwright E2E Testing**
```powershell
cd "tests/e2e"
npm install
npm run install:browsers
npm run test:headed  # Watch tests in real browser
```

**Integration:**
- Tier 2: Yuuji creates E2E smoke tests → Megumi reviews coverage
- Tier 3: Yuuji creates comprehensive E2E → Megumi examines traces → Run in CI

**CI Integration (Optional):**
Add GitHub Action to run Playwright tests and upload reports as PR artifacts.

---

## [8.0.0] - 2025-11-18

### Breaking Changes

#### 🔴 Agent File Format Migration
- **Old Format**: `protocol/YUUJI.md`, `protocol/MEGUMI.md`, `protocol/NOBARA.md`, `protocol/GOJO.md`
- **New Format**: `protocol/yuuji.agent.md`, `protocol/megumi.agent.md`, `protocol/nobara.agent.md`, `protocol/gojo.agent.md`
- **Impact**: All agent file references must be updated across documentation, scripts, and invocation patterns

#### 🔴 Invocation Pattern Changes
- **Old**: `"Read YUUJI.md and implement feature"`
- **New**: `"Read yuuji.agent.md and implement feature"`
- **Impact**: User invocation commands must use new lowercase .agent.md file names
- **Migration**: Update all scripts, documentation, and workflow references

#### 🔴 YAML Frontmatter Required
- **Requirement**: All .agent.md files MUST include YAML frontmatter with 7 required fields
- **Fields**: `target`, `name`, `description`, `argument-hint`, `model`, `tools`, `handoffs`
- **Impact**: Custom agents must be migrated to include structured metadata
- **Validation**: Use `scripts/validate-agents.ps1` to verify format compliance

### Added

#### 1. **.agent.md File Format** - Structured agent metadata system
- **YAML Frontmatter**: Structured configuration header for all agent files
  - `target` field: Environment targeting (`vscode` | `github`)
  - `name` field: Agent full name with role
  - `description` field: Brief agent description
  - `argument-hint` field: Usage instruction/example
  - `model` field: AI model ID (e.g., `claude-3-5-sonnet-20241022`)
  - `tools` array: List of available tools
  - `handoffs` array: Agent transition definitions

#### 2. **Tool Access Matrix** - Formalized permissions table
- **Structure**: Markdown table in every agent file showing tool permissions
- **Access Levels**:
  - ✅ Full Access (unrestricted use)
  - ⚠️ Conditional Access (restricted/requires authorization)
  - ❌ Prohibited (tool not available)
- **Columns**: Tool name, Access Level, Usage description
- **Purpose**: Clear, auditable tool permissions for security and transparency

#### 3. **Declarative Handoff Mechanism** - Agent-to-agent transitions
- **YAML Configuration**: Handoffs defined in frontmatter
- **Trigger Keywords**: `@security-review`, `@remediation-required`, `@approved`, etc.
- **Context Transfer**: Automatic payload passing between agents
  - `files_modified` - Modified file list
  - `tier_level` - Tier 1/2/3 specification
  - `implementation_scope` - Feature scope description
  - `test_coverage` - Test coverage metrics
  - `security_findings` - SEC-IDs from reviews
- **Orchestration**: Mission Control (Gojo) coordinates all handoffs
- **Documentation**: `protocol/HANDOFF_SPECIFICATION.md` (15KB comprehensive spec)

#### 4. **Environment Targeting** - VS Code vs GitHub Copilot compatibility
- **`target` Field**: Specifies agent environment in YAML frontmatter
- **VS Code Target** (`target: vscode`):
  - ✅ Full MCP integration
  - ✅ All tools available
  - ✅ Automated handoffs
  - ✅ Persistent state management
- **GitHub Copilot Target** (`target: github`):
  - ❌ No MCP integration
  - ⚠️ Limited tool set
  - ⚠️ Manual handoffs
  - ❌ No persistent state
- **Documentation**: `protocol/ENVIRONMENT_TARGETING.md` (detailed environment guide)

#### 5. **MCP Integration Support** - Model Context Protocol server connections
- **Purpose**: Enable agents to connect to external data sources and services
- **Examples**:
  - Yuuji → Database MCP server → Query project schema
  - Megumi → CVE database MCP → Check vulnerability databases
  - Gojo → Jira MCP server → Sync project status
- **Configuration**: MCP servers defined in `~/.config/claude-code/mcp.json`
- **Benefits**:
  - Real-time data access during agent execution
  - Extend agent capabilities beyond built-in tools
  - Standardized connection management
- **Documentation**: `protocol/MCP_INTEGRATION.md` (comprehensive MCP guide)

#### 6. **Agent Validation Script** - Automated .agent.md format validation
- **File**: `scripts/validate-agents.ps1` (271 lines, 17 validation checks)
- **Phase 1**: Agent file existence (new .agent.md files present)
- **Phase 2**: Old agent file cleanup (old .md files removed)
- **Phase 3**: YAML frontmatter validation (parsing and required fields)
- **Phase 4**: Tool Access Matrix presence check
- **Phase 5**: Content integrity validation (minimum length requirements)
- **Phase 6**: Documentation reference scanning (no old .md references)
- **Features**:
  - Quick mode for fast verification
  - Comprehensive error reporting
  - Documentation reference validation
  - Exit codes for CI/CD integration

#### 7. **Comprehensive Specification Documents** - Complete guides
- **protocol/HANDOFF_SPECIFICATION.md** (15KB):
  - Complete handoff mechanism guide
  - Context transfer protocols
  - Agent-specific handoff patterns
  - Security considerations
  - Testing handoffs
  - Complete example: Tier 2 JWT Authentication workflow
- **protocol/MCP_INTEGRATION.md** (comprehensive):
  - What is MCP and how it works
  - MCP server configuration examples
  - Agent MCP capabilities
  - Example integrations (database, GitHub, Jira)
  - Security best practices
  - Troubleshooting guide
  - Creating custom MCP servers
- **protocol/ENVIRONMENT_TARGETING.md** (detailed):
  - VS Code vs GitHub Copilot targeting
  - Feature comparison matrix
  - Migration guides (Copilot → VS Code, VS Code → Copilot)
  - Multi-target support
  - Best practices

### Changed

#### 1. **protocol/CLAUDE.md** - Main protocol file updates
- ✅ Added comprehensive ".AGENT.MD FORMAT (v8.0.0+)" section
- ✅ Updated all agent file references (YUUJI.md → yuuji.agent.md)
- ✅ Updated all invocation pattern examples
- ✅ Added YAML frontmatter field documentation
- ✅ Added Tool Access Matrix explanation
- ✅ Added handoff mechanism documentation
- ✅ Added MCP integration overview
- ✅ Added environment targeting overview
- ✅ Added links to new specification documents
- ✅ Updated version to v8.0.0
- ✅ Updated major enhancements to highlight .agent.md format

#### 2. **README.md** - User-facing documentation
- ✅ Updated all agent file references (protocol/*.md → protocol/*.agent.md)
- ✅ Updated invocation pattern examples throughout
- ✅ Added links to .agent.md format documentation
- ✅ Updated quick start instructions
- ✅ Updated troubleshooting section with new file names

#### 3. **protocol.config.yaml** - Configuration file
- ✅ Updated agent file paths:
  - `yuuji_md: "protocol/yuuji.agent.md"`
  - `megumi_md: "protocol/megumi.agent.md"`
  - `nobara_md: "protocol/nobara.agent.md"`
  - `gojo_md: "protocol/gojo.agent.md"`
- ✅ Updated `protocol_version` to `8.0.0`
- ✅ Updated `config_version` to `2.0`
- ✅ Updated `last_updated` to `2025-11-18`

#### 4. **All Agent Files** - Migrated to .agent.md format
- **protocol/yuuji.agent.md**:
  - ✅ YAML frontmatter with all required fields
  - ✅ Tool Access Matrix section
  - ✅ Handoff definitions (to Megumi and Gojo)
  - ✅ Complete agent documentation preserved
  - ✅ Target: vscode (full MCP support)

- **protocol/megumi.agent.md**:
  - ✅ YAML frontmatter with security-specific configuration
  - ✅ Tool Access Matrix with security tools
  - ✅ Handoff definitions (to Yuuji and Gojo)
  - ✅ OWASP Top 10 review process documented
  - ✅ Target: vscode (CVE database MCP integration)

- **protocol/nobara.agent.md**:
  - ✅ YAML frontmatter with UX/creative configuration
  - ✅ Tool Access Matrix with design tools
  - ✅ Handoff definitions (to Yuuji and Megumi)
  - ✅ Design thinking methodology documented
  - ✅ Target: vscode (design tool MCP integration)

- **protocol/gojo.agent.md** (2060 lines):
  - ✅ YAML frontmatter with mission control configuration
  - ✅ Tool Access Matrix with special CLAUDE.md permissions
  - ✅ Handoff definitions (briefing all agents)
  - ✅ Passive observation system documented
  - ✅ Protocol guardian role formalized
  - ✅ Target: vscode (Jira/project management MCP integration)

### Removed

#### 1. **Old Agent Files** - Deleted and replaced
- ❌ `protocol/YUUJI.md` (replaced by `protocol/yuuji.agent.md`)
- ❌ `protocol/MEGUMI.md` (replaced by `protocol/megumi.agent.md`)
- ❌ `protocol/NOBARA.md` (replaced by `protocol/nobara.agent.md`)
- ❌ `protocol/GOJO.md` (replaced by `protocol/gojo.agent.md`)
- **Deletion Method**: `git rm` to ensure clean git history

### Migration Guide

#### Step 1: Update Agent File References
```bash
# Find and replace old references in your codebase
# Old: protocol/YUUJI.md → New: protocol/yuuji.agent.md
# Old: protocol/MEGUMI.md → New: protocol/megumi.agent.md
# Old: protocol/NOBARA.md → New: protocol/nobara.agent.md
# Old: protocol/GOJO.md → New: protocol/gojo.agent.md
```

#### Step 2: Update Invocation Patterns
**Old pattern**:
```bash
"Read YUUJI.md and implement feature"
```

**New pattern**:
```bash
"Read yuuji.agent.md and implement feature"
```

#### Step 3: Verify Agent Files Exist
```bash
# Check that new agent files are present
ls protocol/*.agent.md

# Should see:
# protocol/yuuji.agent.md
# protocol/megumi.agent.md
# protocol/nobara.agent.md
# protocol/gojo.agent.md
```

#### Step 4: Run Validation
```powershell
# Validate all agent files
./scripts/validate-agents.ps1

# Expected: All 17 checks pass
```

#### Step 5: Update Custom Agents (if any)
If you created custom agents, update them to .agent.md format:
1. Add YAML frontmatter (see examples in protocol/*.agent.md)
2. Add Tool Access Matrix section
3. Define handoffs in YAML
4. Rename file to *.agent.md

#### Step 6: Test Invocation
```bash
# Test each agent
"Read yuuji.agent.md and implement test feature"
"Read megumi.agent.md and review test feature"
"Read nobara.agent.md and design test UX"
"Read gojo.agent.md" → Select Option 1 (Resume)

# Verify:
# ✅ Agent responds correctly
# ✅ Tools work as expected
# ✅ Handoffs function properly
```

#### Step 7: Optional - Enable MCP Integration
```bash
# Create MCP configuration (if desired)
mkdir -p ~/.config/claude-code
cat > ~/.config/claude-code/mcp.json <<EOF
{
  "mcpServers": {
    "database": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://localhost:5432/mydb"
      }
    }
  }
}
EOF

# See protocol/MCP_INTEGRATION.md for more examples
```

### Breaking Change Impact Assessment

**High Impact**:
- ✅ Agent file names changed (all references must update)
- ✅ Invocation patterns changed (scripts/docs must update)
- ✅ File path references in automation scripts

**Medium Impact**:
- ✅ Custom agents need .agent.md migration
- ✅ YAML frontmatter structure learning curve
- ✅ Tool Access Matrix formalization

**Low Impact**:
- ✅ MCP integration (optional feature, can enable later)
- ✅ Environment targeting (defaults to vscode, works transparently)
- ✅ Handoff mechanism (enhances existing workflow patterns)

### No Action Required (Backward Compatible Behavior)

- ✅ Core agent behavior unchanged (Yuuji still implements, Megumi still reviews)
- ✅ Tier system unchanged (Rapid/Standard/Critical still work)
- ✅ Dual workflow unchanged (implementation → security review)
- ✅ Protocol philosophy unchanged (Zero defects, Perfect collaboration)
- ✅ Safety principles unchanged (User safety first)
- ✅ Backup requirements unchanged (Always required)

### Upgrade Support Resources

**Having trouble upgrading?**

1. **Read specification docs**:
   - `protocol/HANDOFF_SPECIFICATION.md`
   - `protocol/MCP_INTEGRATION.md`
   - `protocol/ENVIRONMENT_TARGETING.md`

2. **Run validation script**:
   ```powershell
   ./scripts/validate-agents.ps1 -Verbose
   ```

3. **Check for old references**:
   ```powershell
   # Search for old agent file references
   grep -r "YUUJI\.md\|MEGUMI\.md\|NOBARA\.md\|GOJO\.md" .
   ```

4. **Review example agent files**:
   - `protocol/yuuji.agent.md` - See complete .agent.md example
   - Compare old vs new format

### Version Compatibility

- **Requires**: Claude Code or VS Code with Claude extension for full MCP support
- **Compatible with**: GitHub Copilot (limited feature set, see ENVIRONMENT_TARGETING.md)
- **Minimum Protocol Version**: v8.0.0 (breaking changes from v7.x.x)
- **Recommended Migration Path**: v7.2.0 → v8.0.0 (follow all 7 migration steps)

### Performance & Quality

- ✅ Validation script runs 17 checks in <5 seconds
- ✅ YAML parsing overhead: <100ms per agent file
- ✅ Tool Access Matrix lookup: O(1) constant time
- ✅ Handoff context transfer: <200ms per handoff
- ✅ MCP integration latency: Depends on MCP server response time

### Security Enhancements

- ✅ Formalized tool permissions in Tool Access Matrix
- ✅ Declarative handoff security boundaries
- ✅ MCP server authorization layer
- ✅ Environment targeting prevents feature leakage
- ✅ Validation script prevents malformed agent files

---

## [7.2.0] - 2025-11-09

### Added
- **Research Mode** - Structured agent knowledge updates on evolving best practices:
  - **protocol/RESEARCH_MODE.md** - Complete 265-line specification for agent research workflows
  - **Research Configuration** (protocol.config.yaml):
    - `research.enabled` - Master toggle for Research Mode
    - `research.cadence` - Per-agent research schedules (weekly/biweekly/monthly)
    - `research.source_policy` - Quality gates (min primary sources, freshness requirements)
    - `research.privacy` - Privacy protection settings (gitignore raw notes, redact PII)
    - `research.verification` - Dual-source corroboration, security cross-referencing
    - `research.escalation` - Staleness detection and notification thresholds
    - `research.role_focus` - Agent-specific research focus areas
  - **Research State Directory** (.protocol-state/research/):
    - `research-index.json` - Global research session tracking
    - `yuuji/`, `megumi/`, `nobara/`, `gojo/` - Per-agent research outputs
    - `README.md` - Research directory documentation
  - **.gitignore Updates** - Raw research logs (.raw.log) gitignored for privacy

**Agent-Specific Research Focus:**
  - **Yuuji** (Implementation Specialist): Implementation patterns, TDD tooling, test isolation (weekly cadence)
  - **Megumi** (Security Analyst): OWASP updates, emerging vulnerabilities, cryptography papers (weekly cadence)
  - **Nobara** (Creative Strategy/UX): WCAG guidelines, usability heuristics, accessibility tooling (biweekly cadence)
  - **Gojo** (Mission Control): Meta trends, coordination tooling, risk landscape (monthly cadence)

**Research Session Workflow:**
  1. **Initiation** (`@research-start`): Validate enabled, load last session for continuity
  2. **Scoping**: Form 3-5 focused research questions
  3. **Source Selection**: Build candidate list, filter via source policy (min 3 primary sources)
  4. **Collection**: Retrieve summaries/excerpts with timestamps
  5. **Triangulation**: Cross-check 2+ sources for each key claim, mark confidence (High/Medium/Low)
  6. **Synthesis** (`@research-update`): Produce structured summary with citations
  7. **Validation**: Agent-specific verification (security mapping, UX criteria, etc.)
  8. **Completion** (`@research-complete`): Persist curated summary, update index

**Privacy Features:**
  - Raw research notes gitignored (never committed)
  - Automatic PII redaction
  - URL-only storage (summaries, not full dumps)
  - GDPR-compliant data handling

### Changed
- **protocol.config.yaml**:
  - Updated version to v7.2.0
  - Updated config_version to 1.3
  - Updated last_updated to 2025-11-09
  - Added comprehensive `research` configuration section (85 lines)

- **VERSION.md**:
  - Updated to v7.2.0
  - Added "What's New in v7.2.0" section
  - Updated cumulative improvements
  - Updated assessment score

- **protocol/RESEARCH_MODE.md**:
  - Updated version reference to v7.2.0

### Security
- Research Mode includes security verification gates for Megumi
- Research outputs mapped to OWASP Top 10, CVE feeds, and NIST standards
- Privacy-first design with gitignored raw notes and PII redaction

### Performance
- Research sessions capped at 25 minutes to prevent fatigue
- Staleness detection ensures agents stay current (14-day warning, 7-day for critical domains)

---

## [7.1.1] - 2025-11-09

### Added
- **Comprehensive Agent Documentation System** - Complete agent building and usage guides:
  - `Domain Zero Agents/` - Generic agent building framework with templates
    - `AGENT_TEMPLATE.md` - Universal template for creating custom agents
    - `README.md` - Guide for building custom agents
    - `examples/KIRA_DOCUMENTATION_SPECIALIST.md` - Example custom agent
  - `Domain Zero Agents - Full JJK Edition/` - 8 complete character agents
    - Core Four: GOJO.md, YUUJI.md, MEGUMI.md, NOBARA.md
    - Extended: PANDA.md, MAKI.md, INUMAKI.md, TODO.md
    - JJK_AGENT_TEMPLATE.md - JJK-themed agent template
- **Core Documentation (3 comprehensive guides)**:
  - `AGENT_INVOCATION_GUIDE.md` - System prompts for all 8 agents (16 KB)
  - `AGENT_TOOLS_REFERENCE.md` - Tool permissions + advanced capabilities (32 KB)
  - `AGENT_MODEL_RECOMMENDATIONS.md` - Opus/Sonnet/Haiku selection guide (18 KB)
- **SYSTEM_UPDATE_COMPLETE_V7.1.0.md** - Complete v7.1.0 release documentation

### Changed
- **README.md** - Added Agent Documentation section (lines 154-160, 912-936)
  - Links to generic and JJK agent documentation
  - Integration examples and usage guidance
- **Protocol files** - Updated version references from v7.1.0 to v7.1.1
- **project-state.json** - Updated protocol_version to 7.1.1

### Fixed
- Version consistency across all protocol and documentation files

### Documentation
- Total: 16 new files, ~313 KB of agent documentation
- Coverage: System prompts, tool permissions, model recommendations, advanced capabilities
- Integration: Parallel execution, background processes, Jupyter notebooks

---


---

## [7.1.0] - 2025-11-08

### Breaking Changes
- **Dual Workflow Enforcement** (Tier 2/3 only):
  - Yuuji and Megumi CANNOT be invoked separately for Tier 2 (Standard) or Tier 3 (Critical) features
  - **Old pattern** (deprecated): User invokes Yuuji → user manually tags @security-review → user invokes Megumi separately
  - **New pattern** (v7.1.0): User invokes Yuuji once → Yuuji prompts for Megumi invocation after implementation complete
  - **Rationale**: Eliminate possibility of skipped security reviews for production code (Tier 2/3)
  - **Migration**: See DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md for step-by-step migration instructions
  - **Tier 1 exception**: Rapid prototyping (Tier 1) unchanged - Yuuji-only invocation still valid

### Added
- **Dual Workflow Enforcement Guide** (DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md):
  - Complete migration guide for new Yuuji-Megumi collaboration pattern
  - Old vs new invocation pattern comparison
  - Tier-specific examples (Tier 1/2/3)
  - Success criteria and validation checklist
  - Integration guidance for existing projects

- **Mask Mode Configuration** (protocol.config.yaml):
  - Master toggle: `mask_mode.enabled` (true = JJK theme, false = professional mode)
  - Granular settings: control banners, personality, terminology, emoji, and narrative framing independently
  - Unmasked names: professional agent titles when mask is OFF (Implementation Specialist, Security Analyst, etc.)
  - Unmasked terminology: standard translations for JJK terms (Domain Zero → Protocol Environment, etc.)

- **MASK_MODE.md** - Complete specification document:
  - What Mask Mode is and why it exists (presentation choice without functionality loss)
  - Truth about "agents" (same AI, different prompts - per REALITY_CHECK.md)
  - Behavior comparison tables (MASK ON vs MASK OFF)
  - Configuration reference with validation rules
  - Migration guide from v7.0.0
  - Use case guidance (personal vs professional contexts)
  - Examples demonstrating both modes

- **REALITY_CHECK.md** - Honest documentation:
  - What "agents" really are (prompt engineering, not true multi-agent)
  - What Domain Zero actually does (structured prompts for TDD, security, documentation)
  - When to use/not use Domain Zero (realistic assessment)
  - Customization advice (how to make it yours)
  - Success metrics to track (measure your own results)
  - Cost-benefit analysis and honest value proposition
  - Comparison with alternatives (Cursor rules, custom instructions, etc.)

### Changed
- **CLAUDE.md**:
  - Added Mask Mode section (v7.1.0+) explaining JJK theme vs professional mode
  - Added REALITY_CHECK.md to Additional Resources
  - Added MASK_MODE.md to Additional Resources
  - Updated version to v7.1.0
  - Updated major enhancements to highlight Mask Mode Toggle
  - Updated version history with v7.1.0 entry

- **protocol.config.yaml**:
  - Added complete `mask_mode` configuration section (40+ lines)
  - Updated protocol_version to 7.1.0
  - Updated config_version to 1.2
  - Updated last_updated to 2025-11-08

- **VERSION.md**:
  - Updated to v7.1.0 with complete release summary
  - Added "What's New in v7.1.0" section
  - Updated upgrade notes for mask mode
  - Added mask mode to cumulative improvements

- **Documentation Philosophy**:
  - REALITY_CHECK.md provides honest, no-marketing-fluff assessment
  - MASK_MODE.md separates presentation layer from core functionality
  - Clear acknowledgment that agents are prompt engineering, not magic
  - User empowerment through informed choice (mask ON/OFF)

### Implementation Approach
- **Presentation vs Functionality**: Mask Mode affects HOW agents communicate, not WHAT they enforce
- **No breaking changes to core functionality from Mask Mode**: Default behavior (MASK ON) preserves the JJK-themed experience. Note: Dual Workflow Enforcement is a breaking workflow change for Tier 2/3 (see Breaking Changes above).
- **User choice**: Toggle between engaging personality-driven responses and professional direct responses
- **Hybrid modes**: Granular settings allow custom combinations (e.g., keep emoji but use standard terminology)
- **Transparency**: REALITY_CHECK.md honestly explains what users are actually using

### Philosophy
- **Mask as choice, not requirement**: Users choose presentation style without sacrificing protocol structure
- **Security reviews are NOT optional**: Dual workflow ensures Tier 2/3 features receive mandatory security review
- **Honest documentation**: REALITY_CHECK.md acknowledges the truth about prompt engineering
- **User empowerment**: Informed users make better decisions about tool adoption and customization
- **Functionality preserved**: All TDD, tier, backup functionality unchanged regardless of mask setting
- **Tier 1 flexibility maintained**: Fast prototyping still skips security review (by design)

---

## [7.0.0] - 2025-11-07

### Added
- **AGENT_BINDING_OATH.md** - Formal commitment framework:
  - 10 binding principles: User Authority, Transparency, Safety Over Autonomy, Active Protection, Bounded Authority, Honest Communication, Non-Circumvention, Self-Awareness, Collective Responsibility, Continuous Improvement
  - Oath acknowledgment process for all agents
  - Violation consequences (learning-focused, not punitive)

- **DECISION_REASONING_TEMPLATE.md** - Transparency framework:
  - 9-section structured template: Decision, Objective, Reasoning, Alternatives Considered, Risk Assessment, Confidence Level, Dependencies, Implementation Complexity, Final Recommendation
  - Complete worked example included
  - Required for all non-trivial recommendations

- **Absolute Zero Protocol Core Principles** (CLAUDE.md):
  - Principle 1: Absolute User Authority
  - Principle 2: Transparency First
  - Principle 3: Safety Over Autonomy
  - Principle 4: Active Protection
  - Principle 5: Binding Commitment

### Changed
- **All Agent Files** (YUUJI, MEGUMI, NOBARA, GOJO):
  - Added Binding Oath acknowledgment sections
  - Updated to v7.0.0
  - Enhanced major enhancements with AZP commitment

- **protocol.config.yaml**:
  - Added `absolute_zero_protocol` enforcement section
  - Enabled decision reasoning requirements
  - Updated to v7.0.0

- **CLAUDE.md**:
  - Integrated AZP Core Principles section
  - Updated version history to track v7.0.0 as major release
  - Cross-referenced new AZP documents

### Implementation Approach
- **Augmentation, not replacement**: AZP formalizes existing DZP safety principles
- **No breaking changes**: Enhanced structure without changing agent behavior
- **Phase 1 Foundation**: Agent oaths, decision templates, core principles

---

## [6.2.8] - 2025-11-07

### Added
- **Copilot PR review fixes** - Addressed 20 comprehensive review comments

### Changed
- **Protocol files** - Removed inline HTML/CSS for better cross-platform Markdown rendering
- **GOJO.md ASCII art** - Fixed version alignment
- **VERSION.md and CHANGELOG.md** - Improved consistency

### Fixed
- **CODEOWNERS** - Removed gitignored path references
- **Script comments** - Improved accuracy and clarity in verify-protocol scripts
- **Version consistency** - Synchronized all version references across documentation

---

## [6.2.7] - 2025-11-07

### Added
- **Pre-push version verification requirements** - Mandatory comprehensive codebase review checklist:
  - Added CRITICAL PRE-PUSH REQUIREMENT section to system-update.py
  - Added Pre-Push Version Verification (MANDATORY) to protocol/CLAUDE.md
  - Extended VERSION_MANAGEMENT_GUIDE.md with complete verification checklist
  - Automated + manual verification workflow before any GitHub push
- **Enhanced verification script error handling**:
  - PyYAML error handling with graceful degradation
  - Yamllint fallback when PyYAML module missing
  - PowerShell Core (pwsh) detection for cross-platform support
  - Improved error messages with actionable guidance

### Changed
- **GitHub Actions workflows**:
  - Fixed CodeQL workflow manual build step (removed exit 1)
  - Added workflow_dispatch trigger to security-scan-example.yml
  - Corrected IaC scan condition to exclude workflow files
- **CODEOWNERS governance**:
  - Removed duplicate root CODEOWNERS file
  - Cleaned up gitignored file references
  - Added VERSION.md, SECURITY.md, FAQ.md to tracked files
  - Ensured CODEOWNERS not in .gitignore
- **Documentation cleanup**:
  - Removed all ANSI escape codes from protocol files
  - Filled protocol.config.yaml placeholder values
  - Updated version references across 14+ documentation files

### Fixed
- **Version consistency issues** - Synchronized all version references to v6.2.7:
  - FAQ.md, SECURITY.md, CHANGELOG.md version metadata
  - Protocol files (CLAUDE.md, GOJO.md, YUUJI.md, MEGUMI.md, NOBARA.md)
  - CANONICAL_SOURCE_ADOPTION.md, tier-system-specification.md
  - GOJO.md project-state.json initialization template
- **PowerShell script control flow** - Added return statements after successful checks
- **Workflow failures** - Fixed GitHub Actions workflow configurations
- **Markdown linting** - SECURITY.md link formatting and code block language identifiers

### Security
- **Enhanced OWASP Top 10 alignment** - MEGUMI security review process improvements
- **Credential management** - Updated .gitignore to protect sensitive state files
- **Script execution safety** - Improved error handling prevents silent failures

---


---

## [6.2.6] - 2025-11-07

### Added
- **Verification Script v2.0** - Major enhancements to both Bash and PowerShell scripts:
  - Dependency checking with new exit code 3 for missing tools
  - YAML syntax validation using Python or yamllint
  - Selective check execution (`--quick`, `--skip`, `--only`, `--list`)
  - Enhanced error messages with impact/action/documentation links
  - Graceful degradation on critical errors
- **Documentation for script options** - Updated README.md, FAQ.md, and PROTOCOL_QUICKSTART.md with new verification script features

### Changed
- **scripts/verify-protocol.sh** - Upgraded from v1.0 to v2.0 with all Phase 1 & 2 enhancements
- **scripts/verify-protocol.ps1** - Upgraded from v1.0 to v2.0 with feature parity to Bash version
- **Quick mode** - 60% faster verification by running only critical checks
- **Modular check system** - 8 checks organized by criticality (4 critical, 4 warning)

### Performance
- **60% faster** verification with `--quick` mode
- **75-85% faster** targeted debugging with `--only` flag
- **0% performance impact** in default mode (new checks are lightweight)

---

## [6.2.5] - 2025-11-07

### Added
- **FAQ.md** - Comprehensive FAQ covering getting started, tier system, agent behavior, configuration, security & privacy, integration, troubleshooting, and advanced topics (50+ questions)
- **TIER_TRANSITION_GUIDE.md** - Detailed guide for upgrading and downgrading tiers during workflows, including Gojo's role, validation workflows, and common scenarios
- **MIGRATION_GUIDE_TEMPLATE.md** - Template for creating migration guides between major versions, providing step-by-step processes for future upgrades
- **Troubleshooting section in README.md** - Comprehensive 300+ line troubleshooting guide covering configuration issues, agent behavior, tier system problems, verification scripts, git/GitHub integration, performance optimization, and common errors

### Changed
- **Documentation structure enhanced** - Added four major documentation resources to improve user experience and reduce support burden

---

## [6.2.4] - 2025-11-07

### Added
- **SECURITY.md** - Comprehensive vulnerability disclosure policy with coordinated disclosure timeline, CVSS-based severity levels, and safe harbor protections for security researchers

### Changed
- **Enhanced placeholder validation** - Verification scripts now fail (not warn) when configuration placeholders are detected
- **Improved error messages** - Added helpful "HOW TO FIX" guidance with examples when placeholders found
- **Updated PROTOCOL_QUICKSTART.md** - Added warning about placeholder validation requirement

### Fixed
- **Configuration placeholder detection** - Now treats placeholders as errors instead of warnings
- **PowerShell Unicode encoding** - Fixed Unicode symbol issues in verify-protocol.ps1

---

## [6.2.3] - 2025-11-07

### Changed
- **VERSION.md replaces VERSION file** - Now includes detailed release summary and change information instead of simple version string
- **Documentation structure improved** - Better version information visibility for users

### Fixed
- **Removed VERSION_UPDATE_CHECKLIST.md from releases** - Internal developer checklist no longer exposed in public releases

---

## [6.2.2] - 2025-11-07

### Added
- **CODEOWNERS file** for protocol protection - Enforces required approvals for changes to core protocol files (CLAUDE.md, agent files, configuration)
- **.gitignore file** for privacy protection - Prevents accidental commits of sensitive data (trigger-19.md, backups, internal docs)

### Fixed
- **GitHub Actions workflow conditional syntax** - Corrected `hashFiles()` condition format in security-scan-example.yml

### Security
- Privacy protection enhanced with .gitignore to prevent exposure of local intelligence data

---

## [6.2.1] - 2025-11-06

### Added
- **Interactive Work Session Alerts**: Gojo now presents users with explicit "Save Progress" or "Continue Working" options when extended work sessions are detected
- **Enhanced Enforcement Logic**: Gojo responds differently based on user choice:
  - Helps save and commit work if user chooses to take a break
  - Increases monitoring frequency (30-45 min intervals) if user continues
  - Blocks high-risk operations during extended sessions (configurable)
- **New Configuration Settings** in `protocol.config.yaml`:
  - `safety.enforcement.interactive_session_alerts` - Enable user choice in alerts
  - `safety.enforcement.block_until_response` - Block workflow until user responds
  - `safety.enforcement.escalate_on_continue` - Escalate monitoring if user continues
  - `safety.enforcement.block_high_risk_when_fatigued` - Block critical ops when fatigued
  - `safety.boundaries.alert_interval_minutes` - Initial alert interval (240 min)
  - `safety.boundaries.escalated_alert_interval_minutes` - Alert interval after continue (45 min)
  - `safety.boundaries.critical_session_hours` - Critical session threshold (6 hours)

### Changed
- **Work Session Alert Template** (`.protocol-state/work-session-alert.template.md`):
  - Restructured with clear "Decision Point" section
  - Added comprehensive guidance for each option
  - Included safety requirements and Gojo's response behavior
- **GOJO.md - Work Session Monitoring Section**:
  - Added "Work Session Alert Protocol (v6.2.7 Enhanced)"
  - Added "Enforcement Levels & User Choice" section
  - Added "How I Respond to User Choices" section with detailed workflows

### Fixed
- Version consistency across all protocol files (completed v6.2 update before v6.2.7)

---

## [6.2.0] - 2025-11-06

### Added
- **Absolute Safety Principles**: User safety and wellbeing established as highest priority
- **Version Control Enforcement**: Stricter version tracking and consistency checks
- **Work Session Monitoring**: Initial implementation of session duration tracking and alerts
- **Canonical Source Integration**: Protocol references canonical repository for updates

### Changed
- Safety hierarchy explicitly defined (Physical Safety > Wellbeing > Project Safety > Code Quality)
- All agents must respect safety boundaries and escalate concerns
- Enhanced `protocol.config.yaml` with comprehensive safety settings

---

## [6.1.0] - 2025-11-06

### Added
- **Canonical Source Adoption**: Protocol can reference and sync with canonical repository
- **Agent Self-Identification Standard**: All agents announce themselves with emoji and domain name
- **Session Continuity**: Agents re-identify after long sessions or absences
- `CANONICAL_SOURCE_ADOPTION.md` - Adoption and integration guide
- `AGENT_SELF_IDENTIFICATION_STANDARD.md` - Self-identification specification
- Version control scripts (`update-instructions.sh`, `verify-protocol.sh`)

### Changed
- Updated all agent files (YUUJI, MEGUMI, NOBARA, GOJO) with self-identification protocols
- Enhanced `protocol.config.yaml` with canonical repository configuration

---

## [6.0.0] - 2025-11-05

### Added
- **Adaptive Workflow Complexity (Tier System)**: Three-tier system (Rapid/Standard/Critical)
- **NOBARA Agent**: Creative Strategy & UX Specialist (four-agent system)
- **Tier Selection Guide**: Comprehensive guide for choosing appropriate tier
- Desktop application wrapper support (Electron-based)

### Changed
- Major workflow overhaul with tier-based requirements
- Security reviews now tier-adaptive (Tier 2+)
- Testing requirements vary by tier

### Breaking Changes
- Workflow structure changed from fixed to adaptive
- All agents must now operate within tier-specific constraints

---

## [5.1.0] - 2025-11-01

### Added
- **CLAUDE.md Protection System**: Tier 2 protection with authorized editors only
- **Backup & Rollback Requirements**: Mandatory backups before destructive operations
- Enhanced safety enforcement mechanisms

### Changed
- Only USER and GOJO (with authorization) can modify CLAUDE.md
- All destructive operations require backup confirmation

---

## [5.0.0] - 2025-10-28

### Added
- **Mission Control (GOJO)**: Fourth agent for project lifecycle management
- **Passive Observation**: Background monitoring and intelligence gathering
- **Three-Tier Enforcement**: Isolation, backups, quality gates
- **Trigger 19**: Full intelligence report system

### Changed
- Expanded from three-agent to four-agent architecture
- Protocol guardian role established with special privileges

---

## [4.0.0] - 2025-10-20

### Added
- **Custom Trigger System**: User-defined triggers for protocol actions
- Configurable trigger keywords and responses

---

## [3.0.0] - 2025-10-15

### Added
- **Dual Workflow Implementation**: Support for parallel workflows
- Enhanced agent coordination mechanisms

---

## [2.0.0] - 2025-10-10

### Added
- **Three-Agent Architecture**: YUUJI (Implementation), MEGUMI (Security), and basic coordination

### Changed
- Expanded from single-agent to three-agent system

---

## [1.0.0] - 2025-10-01

### Added
- Initial single-agent system
- Basic protocol structure
- Core implementation workflows

---

## Version Numbering Scheme

**Format**: vMAJOR.MINOR.PATCH

- **MAJOR** (Breaking changes, system overhauls)
- **MINOR** (New features, backward-compatible enhancements)
- **PATCH** (Bug fixes, documentation updates, minor corrections)

---

**Canonical Source**: <https://github.com/DewyHRite/Domain-Zero-Protocol>
**Maintainer**: Protocol Guardians
**Last Updated**: 2025-12-25
