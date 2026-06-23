<!-- [CORE FILE] - Domain Zero Protocol v9.8.1 -->
# Domain Zero Protocol - Version Information

**Version:** 9.8.1
**Release Date:** 2026-06-23
**Release Type:** PATCH Release (BUG-CORTEX-ENC-UV-001 — encryption migration user_version fix)

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
  env vars (root-caused the rhs-shared live-brain mutation).
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
- **IMPL-001** — corrected the RHS report: interim relief is `brain dedup --report` (read-only) only;
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
(e.g. JamWebStudio's `business-assets/`) — installs opt into expanded scope via their own `brain.config.yaml`.

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
