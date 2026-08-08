<!-- [CORE FILE] - Domain Zero Protocol v9.12.1 -->
# Trigger 19-R — Release Intelligence: Decision Provenance Report
## Sukuna-Exclusive Report Generation Skill

**Version**: 1.0.0
**Protocol Version**: 9.12.1
**Agent(s)**: Sukuna ONLY (generation); Toji (standing read of both editions)
**Category**: Reporting / Release
**Risk Level**: Medium (sources include the untracked domain.record.md; mitigated by a fail-closed mechanical gate)
**Tracking**: FEAT-TRIGGER19R-9.11.0-001
**Spec**: docs/superpowers/specs/2026-07-29-trigger19r-design.md

---

## Purpose

A public-facing report that lists the USER's recorded decisions and reasons through how each one
influenced the design of DZP: why the protocol was created, how the process evolved from the
beginning, and what each decision gives other users. One pipeline, two moments:

1. **On-demand** — Sukuna generates/refreshes it whenever the USER asks.
2. **Release-shipped** — each release, upon explicit USER approval, a refreshed public edition
   ships with the distribution (see the release checklist in `docs/guides/DISTRO_RELEASE_WORKFLOW.md`).

## Ownership and boundaries (non-negotiable)

- **Generation is SUKUNA-EXCLUSIVE.** Invoked by the USER directly (`/sukuna` + request) or via
  Gojo coordination. No other resident agent may generate or edit an edition.
  **Honest-coverage disclosure (SEC-TRIGGER19R-9.11.0-004)**: this exclusivity is enforced by
  convention and coordination, not mechanically — `docs/DESIGN-DECISIONS.md` is not in the
  FEAT-REQ-001 protected-path list and has no dedicated CODEOWNERS rule. What IS mechanical is the
  content gate: any commit or publish of the file passes the fail-closed sanitization checker
  regardless of who wrote it. (Same disclosure pattern as `domain.record.md`'s
  convention-only protection in root `CLAUDE.md`.)
- **Gojo's standard Trigger 19 is untouched** by this skill in every respect — different report,
  different owner, different output path (`.protocol-state/trigger-19.md` remains private/Gojo).
- **No new access is granted to anyone.** All sources are already within Sukuna's read surface.
- A public edition ships ONLY on explicit USER approval, and ONLY after
  `scripts/check_trigger19r_sanitization.py` exits 0 against it.

## Report contract

### Structure
1. **Narrative intro** — why DZP was created: the original problem, the philosophy (Domain/Zero,
   zero ≠ perfection, discipline as the strength), how the design grew. Written for an outside
   reader evaluating whether DZP can help them.
2. **Decision ledger** — one entry per recorded USER decision, chronological, each citing its
   source record and date. Fields (all six required per entry):

| Field | Content |
|---|---|
| Date | when ratified (from the record) |
| Release | version the decision landed in |
| Context | what problem was live when the decision was made |
| Decision | what the USER decided, paraphrased from the record |
| Design consequence | what changed in DZP because of it |
| Benefit to others | what a consumer/other user gains from that choice |

The ledger is regenerated from sources each edition (derived artifact), never hand-maintained.

### Sources (all records, gated — USER ruling 2026-07-29)
`domain.record.md` (ratification blocks — richest source, UNTRACKED), `CHANGELOG.md`/`VERSION.md`,
`audits/`, `.protocol-state/issue-registry.jsonl`, `.protocol-state/dev-notes.md`,
`.protocol-state/security-review.md`.

## Two editions

| Edition | Path | Tracked | Ships |
|---|---|---|---|
| Working | `internal-docs/trigger-19r/<YYYY-MM-DD>-working.md` | no (internal-docs, gitignored) | never |
| Public | `docs/DESIGN-DECISIONS.md` | yes | yes (via `publish-manifest.yaml`) |

**Workflow**: Sukuna authors the working edition (full detail) → USER reviews it (HARD GATE) →
Sukuna derives the paraphrased, sanitized public edition → the sanitization gate must exit 0 →
USER approves the public edition → commit/ship.

## The mechanical gate (load-bearing)

`scripts/check_trigger19r_sanitization.py --public docs/DESIGN-DECISIONS.md` — fail-closed,
three detectors; exit 0 pass / 1 violation / 2 execution error:

1. **Untracked-id refusal** — every id-shaped string cited must exist in the TRACKED issue
   registry; ids that live only in untracked records are refused.
2. **Secrets/PII** — live SEC-001 scanner patterns + the manifest's `forbid_content` PII literals
   (imported, never forked).
3. **Verbatim-leak** — no ≥12-consecutive-word verbatim overlap (after Unicode NFKC normalization,
   casefolding, and punctuation/hyphenation collapse — AI-001 hardening, 2026-07-30, see below)
   with ANY internal narrative corpus file: `domain.record.md`, `dev-notes.md`,
   `security-review.md`, and every rotated archive under
   `.protocol-state/archive/{dev-notes,security-review}/` (corpus extended per the
   SEC-TRIGGER19R-9.11.0-001 scope ruling). **What this actually enforces**: refusal of a
   normalized EXACT token-sequence match at that window length — NOT general paraphrase
   detection. Word-order rewrites, synonym substitution, and genuine rewording still pass the
   mechanical gate by design. Paraphrase is expected and reviewed by the USER at the
   working-edition gate (see "Two editions" below), but is not itself mechanically verified;
   explicit human review remains a required, separate defense that the mechanical gate does not
   supersede. **Degradation rule**: any corpus file unreadable or undecodable at check time gets
   its own LOUD per-run notice naming the path — that file DID NOT gate, the rest still do
   (detectors 1–2 always gate) — silent success and verified success must never look identical.

   > **AI-001 (Toji audit 2026-07-30)**: earlier revisions of this document stated that
   > "paraphrase is mechanically mandatory". That was stronger than the actual enforcement: the
   > pre-hardening detector split raw text and compared exact tuples, so a single case change,
   > punctuation edit, hyphenation change, or Unicode-compatibility substitution inside a 12-word
   > window defeated it while leaving the prose nearly verbatim. The gate now normalizes text
   > before comparison (see `scripts/check_trigger19r_sanitization.py::normalize_for_shingling()`),
   > closing those cosmetic bypasses, but remains an exact-match gate — not a paraphrase detector.

Enforced automatically at **pre-commit** (when `docs/DESIGN-DECISIONS.md` is staged; index-version
check; no override exists — the break-glass is unstaging the file) and in **both `dzp-publish`
drivers** (skip-if-absent; any nonzero exit aborts the publish, execution errors included).

## Invocation

```text
# On-demand refresh (USER or Gojo-coordinated)
/sukuna generate Trigger 19-R
"Read protocol/sukuna.agent.md and generate the Trigger 19-R decision-provenance report"

# Verify a public edition manually
python scripts/check_trigger19r_sanitization.py --public docs/DESIGN-DECISIONS.md
```

## Changelog

### 1.0.0 (2026-07-29)
- Initial release (FEAT-TRIGGER19R-9.11.0-001, v9.11.0 Increment 5): contract, two-edition
  pipeline, 3-detector fail-closed gate wired at pre-commit + dzp-publish, Sukuna-exclusive
  generation, USER hard gates at working-edition review and public-edition approval.

---

**Status**: Production-Ready
**Maintenance**: Update when the ledger contract, gate detectors, or edition paths change.
