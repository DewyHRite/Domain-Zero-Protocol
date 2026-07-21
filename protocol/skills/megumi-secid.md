<!-- [CORE FILE] - Domain Zero Protocol v9.10.2 -->
# Megumi `secid` Skill — Issue-ID Governance

**Name:** megumi-secid
**Category:** Security / Issue-ID Governance
**Introduced:** v9.10.0 (FEAT-IDGOV-001)
**Risk Level:** Medium (executes local Python via a signed wrapper; append-only ledger writes)
**Agent:** Megumi SPECIFIES the exact invocation (mediated execution, D9 — see below); a bash-capable
resident (Gojo primary; Yuuji, since implementation already routes through him) EXECUTES it on her
behalf. Megumi never runs `secid` herself. Other residents authorized for a given family (Yuuji, Sukuna,
Gojo) sign and invoke `scripts/issue_id.py` directly via their own process, never through this wrapper
(this wrapper stamps `attested_writer: megumi` unconditionally — see "Writer authority" below).
**Toji:** READ-only `check`/`list` to author collision-free ids; **Toji writes nothing** (proxy-mint, §Toji below).

---

## Purpose

`secid` is Megumi's scoped front-end to the DZP Issue-ID registry (FEAT-IDGOV-001). It mints, looks up,
lists, and transitions issue IDs (SEC / BUG / FEAT / IMPL / CODE / ISS / TEST / MF) against a single
append-only JSONL ledger (`.protocol-state/issue-registry.jsonl`) so an ID like `SEC-001` can never be
silently reused to mean five different things.

`secid` is a Megumi-signed wrapper (`scripts/secid.sh` / `scripts/secid.ps1`) over the shared engine
`scripts/idgov/engine.py`. The wrapper carries Megumi's per-wrapper secret and is the **only** path that
stamps `attested_writer: megumi` on a registry row.

> **Mediated-execution note (D9, ratified):** Megumi has **no Bash access and this skill grants none**.
> Sukuna-adversarial + Gojo-verified review (spec §7.1, Sukuna F4) considered a direct runtime tool grant
> for `secid` and **ratified mediated execution instead** — Megumi specifies the exact invocation in her
> finding/verdict; a bash-capable resident (Gojo primary, or Yuuji) executes it verbatim. This is a
> permanent workflow decision, not an interim state pending a future grant: `scripts/secid.sh` signs
> every mint/transition as `attested_writer: megumi` regardless of *which process* actually runs it, so
> mediated and direct execution produce an **identical registry row** — mediation costs nothing in
> registry fidelity and keeps a second reviewer's eyes on every command before it lands in an
> append-only ledger. See `protocol/megumi.agent.md` § Issue-ID Governance for the full rationale and
> Megumi's tool-list boundary (unchanged: read/write/grep/glob/todowrite/task/webfetch/websearch/
> askuserquestion only — zero Bash, zero Edit).

---

## Commands

These are the exact invocations Megumi specifies for her mediator to run verbatim — always through the
wrapper, never `issue_id.py` directly (direct calls have no signature and are refused for `new`/`state`):

```powershell
scripts/secid.ps1 check SEC-CORTEX-025
scripts/secid.ps1 list --state open
scripts/secid.ps1 new SEC --subsystem CORTEX --title "LIKE-wildcard escape gap" --cwe CWE-89 --location cortex/store.py:412
scripts/secid.ps1 state SEC-CORTEX-025 remediation-required --note "routed to Yuuji"
scripts/secid.ps1 validate
```

POSIX:

```bash
scripts/secid.sh check SEC-CORTEX-025
scripts/secid.sh list --state open
scripts/secid.sh new SEC --subsystem CORTEX --title "..." --review-ref security-review.md
scripts/secid.sh state SEC-CORTEX-025 approved
scripts/secid.sh validate
```

### Subcommand reference

| Command | Effect | Exit codes |
|---|---|---|
| `check <ID>` | Prints the latest-rev record as JSON if it exists; prints `free` otherwise. | `0` exists · `1` free |
| `list [--family F] [--subsystem S] [--state ST]` | Prints the latest-rev projection as a JSON array, optionally filtered (e.g. `--state open` = your `@re-review` queue). | `0` |
| `new <FAMILY> --subsystem <S> --title <T> [flags]` | Mints the next `<FAMILY>-<S>-NNN` id (attested `megumi`), appends an `assign` row, prints the id. | `0` success · `2` error/unauthorized |
| `state <ID> <NEW_STATE> [--note ...]` | Records a legal lifecycle transition (rev+1). | `0` success · `2` illegal/unauthorized |
| `validate` | Full ledger integrity check (grammar / uniqueness / seq monotonicity / rev continuity / transition legality / writer authority). | `0` clean · `1` violations |

`new` flags: `--version`, `--tag`, `--reserved` (mint in `reserved` state), `--cwe`, `--owasp`,
`--location`, `--review-ref`, `--reported-by` (see Toji proxy-mint).

---

## Mint-before-cite (mandatory)

**Mint the ID first; then cite it in prose.** Never write a new `SEC-*`/`CODE-*` id into
`security-review.md` (or any corpus file) before `secid new` has created its registry row. The Phase E
gate enforces this at commit/CI: a cited id with no matching row is blocked, and a bare/malformed id
(e.g. `SEC-013`) in new prose is a hard block. Cite the minted id, and record the review link with
`--review-ref` at mint time.

---

## Tag → state mapping

Megumi's review verdicts map 1:1 onto lifecycle transitions:

| Megumi verdict | `secid state` target | Legal from |
|---|---|---|
| `@remediation-required` | `remediation-required` | `open`, `re-review` |
| `@re-review` (Yuuji resubmits) | `re-review` | `remediation-required` (plus the reopen arcs: `open`, `approved`, `accepted-p3`, `deferred`) |
| `@approved` | `approved` | `open`, `re-review` |
| Accepted P3 residual | `accepted-p3` | `open`, `re-review` |
| Deferred to a later version | `deferred` | `open`, `reserved`, `remediation-required`, `re-review` |
| Superseded by a newer id | `superseded` | any non-terminal **except `reserved`** (a `reserved` id must go `reserved → open` first) |

States: `open`, `reserved`, `remediation-required`, `re-review`, `approved`, `accepted-p3`, `deferred`,
`superseded` (terminal). Illegal transitions (e.g. `remediation-required → approved` without a
`re-review` hop) are refused. `secid validate` is authoritative if you are unsure of a legal path.

---

## Writer authority

The gate enforces which `attested_writer` may mint each family (derived from the signing wrapper, never
from a flag):

| Family | Authorized minter |
|---|---|
| `SEC`, `CODE` | **Megumi** (sole) |
| `MF` (Megumi Finding) | **Megumi** (sole) |
| `TEST` | Megumi, Yuuji |
| `BUG` | Yuuji, Sukuna |
| `FEAT` | Sukuna |
| `IMPL` | Sukuna, Yuuji |
| `ISS` | Sukuna, Gojo |

If you try to mint a family you are not authorized for, `new` exits non-zero (`error: ... not authorized
for ...`). This is by design — it keeps SEC/CODE/MF findings attributable to Security.

---

## Toji proxy-mint (D10)

Toji is REPORT-ONLY with no execution. In an audit, Toji uses READ-only `check`/`list` to pick
correctly-grammared, non-colliding ids (subsystem `TOJI`, e.g. `SEC-TOJI-007`) and records them in the
audit report. On owner acceptance, **a resident authorized for the target family** mints the real row:

```bash
scripts/secid.sh new SEC --subsystem TOJI --title "Toji finding ..." --reported-by toji --review-ref audits/<report>.md
```

`--reported-by toji` is free-text provenance only — `attested_writer` remains the resident who signed
(e.g. `megumi`). Toji never signs, never writes to the registry; auditor independence is preserved.

---

## Rules & boundaries

- **Append-only, absolute.** The registry only grows; never rewrite or truncate a committed line. This
  mirrors the `dev-notes.md` / `security-review.md` / `domain.record.md` protection.
- **Writer identity is derived, never asserted.** `attested_writer` comes from the wrapper's per-wrapper
  secret. **Honest residual (D11):** a process running as the same OS user can read the token file and
  forge that writer — this is local integrity, **not** cross-agent non-repudiation. Do not overclaim it.
- **Fresh nonce per call.** The wrapper generates a new random nonce on every invocation
  (SEC-IDGOV-C-REPLAY-001 hygiene). Never reuse or hardcode a nonce.
- **Break-glass:** `DZP_ALLOW_ISSUE_ID_OVERRIDE=1` bypasses the commit/CI gate (backfill/migration only,
  loud on stderr). It is independent of the other DZP overrides and is not for routine minting.
- **Two-tier enforcement:** the local pre-commit hook is early feedback; the CI/publish gate is
  authoritative (Toji IMPL-002).

---

## See also

- Spec: `docs/superpowers/specs/2026-07-13-issue-id-governance-design.md` (v3, §4 identity, §7 tool/authority)
- Plan: `docs/superpowers/plans/2026-07-14-issue-id-governance.md`
- Engine: `scripts/idgov/engine.py` · CLI: `scripts/issue_id.py` · Wrappers: `scripts/secid.{sh,ps1}`
- Gate (Phase E): `scripts/check_issue_ids.py`
