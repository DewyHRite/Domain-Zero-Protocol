<!-- [CORE FILE] - Domain Zero Protocol v9.12.1 -->
# Resident Mint Wrappers — Issue-ID Governance (Sukuna / Gojo / Yuuji)

**Name:** resident-mint
**Category:** Security / Issue-ID Governance
**Introduced:** v9.10.1 (Toji DESIGN-001 remediation, Sukuna Block B2)
**Risk Level:** Medium (executes local Python via a signed wrapper; append-only ledger writes)
**Agents:** Sukuna, Gojo, and Yuuji each EXECUTE their own wrapper directly — unlike Megumi, all
three already have Bash access (root/protocol `CLAUDE.md` tool-access matrix), so no mediated
execution is needed here. See "Why three wrappers, not one" below for why this is NOT a shared
`--writer` flag.
**Toji:** READ-only `check`/`list` to author collision-free ids; **Toji writes nothing** (proxy-mint,
same pattern as `protocol/skills/megumi-secid.md` § Toji proxy-mint).

---

## Purpose

`residentid-<writer>` are Sukuna's, Gojo's, and Yuuji's scoped front-ends to the DZP Issue-ID
registry (FEAT-IDGOV-001) — the parity fix for Toji's `DESIGN-001` finding
(`audits/2026-07-18-toji-dzp-9-10-0-audit.md`): "the authority matrix permits Yuuji, Sukuna, and Gojo
to mutate several issue-ID families, but only Megumi has repository-provided signed wrappers and a
documented skill workflow." Before this, a non-Megumi authorized mint had no sanctioned tool at all
and depended on ad hoc direct library invocation (see `AI-001` in the same audit, which found the
feature's OWN `FEAT-IDGOV-001` registry row was minted exactly this way).

Each wrapper mints, looks up, lists, and transitions issue IDs against the same single append-only
JSONL ledger (`.protocol-state/issue-registry.jsonl`) Megumi's `secid` uses — see
`protocol/skills/megumi-secid.md` for the shared engine, commands, mint-before-cite discipline, and
lifecycle-state model, all of which apply identically here and are **not repeated in full below**.

- `scripts/residentid-sukuna.sh` / `.ps1` — stamps `attested_writer: sukuna`
- `scripts/residentid-gojo.sh` / `.ps1` — stamps `attested_writer: gojo`
- `scripts/residentid-yuuji.sh` / `.ps1` — stamps `attested_writer: yuuji`

---

## Why three wrappers, not one (D11 parity, decided)

`scripts/idgov/identity.py` derives `attested_writer` from **which per-wrapper token signed the
call**, never from a caller-supplied flag (`derive_writer()` iterates `.protocol-state/.idgov-tokens/
*.token` and returns whichever token's HMAC matches). A single generic `residentid.sh --writer
<name>` wrapper was considered and **rejected**: if one shared script accepted an arbitrary writer
name on argv and then called `identity.provision(writer)` / signed with that writer's token, ANY
caller of that one script could choose to mint as `sukuna`, `gojo`, **or** `yuuji` simply by passing a
different flag value. That breaks the "identity = which file you invoke" model `scripts/secid.sh`
already established for Megumi (a hardcoded `identity.provision("megumi")`, no flag) and reintroduces
a classic confused-deputy risk: the wrapper's own identity would no longer be a reliable signal of
who actually ran it.

Megumi's mediated-execution model (`protocol/skills/megumi-secid.md` § "Mediated-execution note") is
a **different** answer to a **different** problem: Megumi has no Bash access at all, so a bash-capable
mediator must run `secid.sh` on her behalf — but `secid.sh` is still hardcoded to `"megumi"`, never
parameterized. Sukuna, Gojo, and Yuuji all already have full Bash access (see the tool-access matrix
in root/protocol `CLAUDE.md`), so no mediation is needed — each simply gets its own hardcoded-identity
wrapper, exactly mirroring `secid.sh`'s design, just three files instead of one.

**Honest residual (unchanged from D11):** a process running as the same OS user can read any of the
four token files (`.idgov-tokens/{megumi,sukuna,gojo,yuuji}.token`) and forge that writer. This is
**local integrity, not cross-agent non-repudiation** — identical to the boundary
`protocol/skills/megumi-secid.md` and `.protocol-state/attestation.py` already document. Splitting
into three files does not change this residual; it only removes the *additional*, avoidable
confused-deputy surface a shared `--writer` flag would have introduced on top of it.

---

## Commands

Exact invocations — always through the matching wrapper for your identity, never `issue_id.py`
directly (direct calls have no signature and are refused for `new`/`state`):

```bash
# Sukuna — authorized for BUG, FEAT, IMPL, ISS
scripts/residentid-sukuna.sh new FEAT --subsystem IDGOV --title "resident mint wrappers" --review-ref audits/2026-07-18-toji-dzp-9-10-0-audit.md
scripts/residentid-sukuna.sh state BUG-SNAPSHOT-010 approved

# Gojo — authorized for ISS, LL
scripts/residentid-gojo.sh new ISS --subsystem PROTOCOL --title "..."
scripts/residentid-gojo.sh new LL --subsystem TRIGGER19 --title "..."

# Yuuji — authorized for BUG, IMPL, TEST
scripts/residentid-yuuji.sh new IMPL --subsystem CORTEX --title "..."
```

PowerShell parity (`.ps1` in place of `.sh`, identical arguments):

```powershell
scripts/residentid-sukuna.ps1 new FEAT --subsystem IDGOV --title "..."
scripts/residentid-gojo.ps1 new ISS --subsystem PROTOCOL --title "..."
scripts/residentid-gojo.ps1 new LL --subsystem TRIGGER19 --title "..."
scripts/residentid-yuuji.ps1 new IMPL --subsystem CORTEX --title "..."
```

Subcommands (`check`/`list`/`new`/`state`/`validate`), flags, exit codes, and the mint-before-cite
discipline are **identical** to `secid` — see `protocol/skills/megumi-secid.md` § "Subcommand
reference" and § "Mint-before-cite (mandatory)". `check`/`list`/`validate` are read-only and never
sign (SEC-IDGOV-D-003 parity — no token provisioning side effect on a plain read).

---

## Writer authority (unchanged from the engine — reference only)

| Family | Authorized minter(s) | Resident wrapper |
|---|---|---|
| `SEC`, `CODE`, `MF` | Megumi (sole) | `scripts/secid.{sh,ps1}` only |
| `SF` (Security Framework, v9.11.0 `FEAT-IDGOV-003`) | Megumi (sole) | `scripts/secid.{sh,ps1}` only |
| `TEST` | Megumi, Yuuji | `scripts/secid.{sh,ps1}` (Megumi) or `residentid-yuuji` |
| `BUG` | Yuuji, Sukuna | `residentid-yuuji` or `residentid-sukuna` |
| `FEAT` | Sukuna (sole) | `residentid-sukuna` |
| `IMPL` | Sukuna, Yuuji | `residentid-sukuna` or `residentid-yuuji` |
| `ISS` | Sukuna, Gojo | `residentid-sukuna` or `residentid-gojo` |
| `LL` (Lessons Learned, v9.11.0 `FEAT-IDGOV-003`) | Gojo (sole) | `residentid-gojo` only |

Minting/transitioning a family your wrapper is not authorized for fails closed with `error: <writer>
not authorized for family <family>` (engine-enforced, exit `2`) — no wrapper pre-filters; the
`AUTHORITY` table in `scripts/idgov/engine.py` is the single source of truth.

---

## Rules & boundaries

Identical to `protocol/skills/megumi-secid.md` § "Rules & boundaries": append-only ledger, derived
(never asserted) writer identity, fresh nonce per call, the `DZP_ALLOW_ISSUE_ID_OVERRIDE=1` break-glass
(backfill/migration/authorized exception only), and the two-tier (pre-commit early-feedback / CI
authoritative) enforcement model — all apply here without modification.

---

## See also

- Spec: `docs/superpowers/specs/2026-07-13-issue-id-governance-design.md` (v3, §4 identity, §7 tool/authority)
- Megumi's front-end + shared background: `protocol/skills/megumi-secid.md`
- Engine: `scripts/idgov/engine.py` · Identity: `scripts/idgov/identity.py` · CLI: `scripts/issue_id.py`
- Wrappers: `scripts/secid.{sh,ps1}` (Megumi), `scripts/residentid-{sukuna,gojo,yuuji}.{sh,ps1}` (this doc)
- Gate (Phase E): `scripts/check_issue_ids.py`
- Origin finding: `audits/2026-07-18-toji-dzp-9-10-0-audit.md` § `DESIGN-001`
