<!-- [CORE FILE] - Domain Zero Protocol v9.12.1 -->
# Canonical Source Adoption & Repository Referencing Strategy
## Repository: <https://github.com/DewyHRite/Domain-Zero-Protocol>

**Date**: 2025-11-06
**Protocol Version**: v6.2.8.x (Transition from distributed copies to canonical reference)
**Status**: **ADOPTED** — live since v6.2.8/v8.x, evolved further in v9.11.0 (see "Current State" below)
**Owner**: Protocol Guardian (Gojo) / Repository Admins

---

## 0. Current State (added 2026-08-07 — read this first)

This document is the **original adoption proposal** (2025-11-06). It is retained as a historical
record of the decision, NOT as a description of how the mechanism works today — its Phase 1-5
rollout plan no longer matches the shipped implementation. The proposal was accepted, implemented,
and then **further restructured in v9.11.0** in a way this document's original body does not
reflect. Treat everything below §0 as a **point-in-time design snapshot**; treat this section as
the current source of truth for how canonical-source referencing actually works in v9.12.0.

**What's live today:**

- **Canonical repository**: <https://github.com/DewyHRite/Domain-Zero-Protocol> — the single
  source of truth this proposal envisioned. Root `CLAUDE.md` carries an active
  "📍 CANONICAL SOURCE" section with the current protocol version and a pointer to
  `scripts/verify-protocol.(ps1|sh)` for canonical-alignment checks — the verification mechanism
  §5 of this document proposed, now implemented and shipped.
- **File hierarchy superseded this proposal's own design**: §3.1 below proposed adding the
  canonical block to `protocol/CLAUDE.md`'s header. That is **no longer where it lives**. Since
  v8.13.0 (revised v9.11.0), the **root** `./CLAUDE.md` is the single source of truth and
  `protocol/CLAUDE.md` is a ~15-line compatibility stub/pointer that redirects to the root file.
  The canonical-source block accordingly lives in the **root** `CLAUDE.md`, not
  `protocol/CLAUDE.md`.
- **Two-repo isolation (v9.9.0+)**: development happens on a private `dev` remote (branches like
  `Main-vX.Y.Z`); the canonical `origin` public repository receives only sanitized,
  maintainer-published releases on `DZP-vX.Y.Z` branches via the `dzp-publish` tool. This is a
  stronger separation than this proposal's original "single repository, branch protection"
  design (§2/§8) — it followed a dedicated 2026-06-24 dev/release isolation decision
  (`SEC-ISOL-001..014`), not this document.
- **Sanitized releases**: each `DZP-vX.Y.Z` branch is a maintainer-published, sanitized release
  cut from `dev` via a PR + automated-review gate (CodeRabbit) — the "PR template gate" and
  "review history centralized" outcomes §2 and §10 of this proposal aimed for, now realized as
  the maintainer-internal release process. Root `CLAUDE.md` explicitly documents this process as
  **maintainer-internal, not part of the consumer protocol** — the exact "governance centralized,
  local needs not blocked" balance §8 of this proposal called for.
- **Payload verification (v9.10.2+)**: every release ships a `dzp-payload-vX.Y.Z.zip` + manifest
  as a GitHub Release asset, verified BEFORE extraction: `scripts/verify-payload.py` checks the
  payload zip's own hash against its manifest, cross-checks the manifest's recorded release branch against
  a live `git ls-remote` of the canonical repository, and (with `--deep-verify`) byte-compares
  every file against a shallow clone of the canonical commit. This is a stronger drift/tamper
  detector than the VERSION-file `curl` comparison §5 of this proposal sketched — it verifies
  supply-chain provenance, not just a version-number match.
- **Verification tooling**: `scripts/verify-protocol.(ps1|sh)` — referenced live in root
  `CLAUDE.md`'s "📍 CANONICAL SOURCE" section — checks canonical alignment for an installed copy,
  fulfilling §5's original design intent (though implemented directly rather than via the
  YAML-driven pseudocode sketched below, which was never built as written).

**What was proposed here but never built as specified:** the `canonical_repository:` block in
`protocol.config.yaml` (§3.2), the `--canonical-sync` update-script flag (§6), and the PR-template
canonical-alignment checklist (§10) were early design sketches for mechanisms that were ultimately
implemented differently (verify-protocol scripts, the dzp-publish sanitized-release pipeline, and
payload verification, respectively) rather than built to this document's literal spec. Sections
1-15 below are preserved as-written for historical context; do not treat their code/config
snippets as live configuration.

---

## 1. Executive Summary
Adopting a single canonical public repository for the Domain Zero Protocol ("DZP") centralizes governance, eliminates drift, ensures consistent security posture, and improves AI assistant interoperability. All downstream projects should *reference* rather than *redefine* protocol content. Local changes become configuration overrides—not forks of the core logic.

**Outcome**: Faster onboarding, consistent enforcement, auditable evolution, reduced fragmentation, and improved confidence in protocol integrity.

---

## 2. Benefits Overview

| Area | Impact | Description |
|------|--------|-------------|
| Single Source of Truth | ★★★★★ | All agents & tools resolve to one URL; no stale variants |
| Governance & Compliance | ★★★★★ | CODEOWNERS + branch protection + review history centralized |
| Security Posture | ★★★★☆ | Easier to apply uniform scanning & secret policies |
| AI Assistant Consistency | ★★★★☆ | Copilot/Claude/Cursor/Cody all follow same canonical pointer |
| Update Velocity | ★★★★☆ | Changes shipped once → pulled everywhere; fewer manual merges |
| Drift Prevention | ★★★★★ | Verification script can compare local vs canonical commit/tag |
| Auditability | ★★★★★ | Full PR history & review rationale preserved in one place |
| Reusability | ★★★★☆ | Protocol packs, scripts, templates distributed predictably |

---

## 3. Repository Referencing Pattern (original design — see §0 for what actually shipped)
### 3.1 Canonical Block (originally proposed for `protocol/CLAUDE.md` header — lives in root `CLAUDE.md` since v9.11.0, see §0)
```markdown
> Canonical Source: https://github.com/DewyHRite/Domain-Zero-Protocol
> Current Local Protocol Version: v6.2.8
> Pinned Commit: <SHA>
> Verification: Run `./scripts/verify-protocol.(ps1|sh)` – checks canonical alignment
```

### 3.2 Config Injection (`protocol.config.yaml`) — proposed shape, not the shipped mechanism (see §0)
```yaml
canonical_repository:
  url: "https://github.com/DewyHRite/Domain-Zero-Protocol"
  version: "v6.2.8"
  commit: "<PINNED_SHA>"
  auto_update:
    enabled: false          # Set true if downstream wants automatic pulls
    strategy: "tag"          # tag | commit | latest
    check_on_verify: true    # Verification script warns on mismatch
```

### 3.3 README Badge
```markdown
[![Canonical Protocol](https://img.shields.io/badge/Protocol-Domain_Zero_Canonical-blue)](https://github.com/DewyHRite/Domain-Zero-Protocol)
```

---

## 4. Required File Adjustments (Phase 1 — historical; see §0 for current file hierarchy)

| File | Addition | Purpose |
|------|----------|---------|
| `protocol/CLAUDE.md` | Canonical Source block | Declares authority & current version |
| `protocol.config.yaml` | `canonical_repository` section | Machine-readable alignment |
| `README.md` | Badge + Canonical Source section | Discovery & onboarding |
| `AI_INSTRUCTIONS.md` | Link to canonical repo | Cross-assistant resolution |
| `scripts/verify-protocol.*` | Canonical version check | Drift detection |
| `.github/PULL_REQUEST_TEMPLATE.md` | Checkbox: "Matches canonical version" | Review gate |

> **Note (2026-08-07)**: the "canonical block" row above now lives in the **root** `CLAUDE.md`,
> not `protocol/CLAUDE.md` — see §0.

---

## 5. Verification Script Enhancements (design sketch — see §0 for the shipped tool)
Add a new step:
```bash
# Pseudocode for verify-protocol.sh
if [ -f protocol.config.yaml ]; then
  LOCAL_VER=$(yq '.canonical_repository.version' protocol.config.yaml)
  REMOTE_VER=$(curl -s https://raw.githubusercontent.com/DewyHRite/Domain-Zero-Protocol/main/VERSION 2>/dev/null || echo "unknown")
  if [ "$REMOTE_VER" != "unknown" ] && [ "$LOCAL_VER" != "$REMOTE_VER" ]; then
    write_warn "Canonical version mismatch: local=$LOCAL_VER remote=$REMOTE_VER"
  else
    write_pass "Canonical version aligned: $LOCAL_VER"
  fi
fi
```
PowerShell equivalent:
```powershell
$LocalVer = (Select-String -Path protocol.config.yaml -Pattern 'version:' | ForEach-Object { $_.ToString().Split(':')[1].Trim() })
$RemoteVer = try { (Invoke-WebRequest -UseBasicParsing https://raw.githubusercontent.com/DewyHRite/Domain-Zero-Protocol/main/VERSION).Content.Trim() } catch { 'unknown' }
if ($RemoteVer -ne 'unknown' -and $LocalVer -ne $RemoteVer) {
  Write-Warn "Canonical version mismatch: local=$LocalVer remote=$RemoteVer"
} else {
  Write-Pass "Canonical version aligned: $LocalVer"
}
```

> **Note (2026-08-07)**: the shipped `scripts/verify-protocol.(ps1|sh)` does not implement this
> exact `curl`/VERSION-file comparison; see §0 for the tooling that actually ships (including the
> stronger `scripts/verify-payload.py` supply-chain check added in v9.10.2).

---

## 6. Update Scripts Extension (proposed — not built as specified; see §0)
Enhance `update-instructions.sh` & `.ps1` to support:
- `--canonical-sync` flag (fetch latest CLAUDE.md + protocol agents)
- Integrity validation (SHA compare before replace)
- Dry-run preview
- Automatic backup: `CLAUDE.md.backup.<timestamp>`

Example invocation:
```bash
./scripts/update-instructions.sh --canonical-sync --dry-run
./scripts/update-instructions.sh --canonical-sync --apply
```

---

## 7. Rollout Plan (historical — all phases below completed or superseded; see §0)

| Phase | Goal | Tasks | Success Metric |
|-------|------|-------|----------------|
| 1 | Preparation | Add canonical blocks & config | All key files reference URL |
| 2 | Tooling | Upgrade verify + update scripts | Drift warnings operational |
| 3 | Enforcement | PR template gate | 100% protocol PRs include version checkbox |
| 4 | Adoption | Migrate 3 downstream projects | All pointing to canonical repo |
| 5 | Automation (Optional) | Auto-pull tagged releases | No manual copy operations |

---

## 8. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Link rot / repo rename | Breaks all references | Keep redirect stub repo or GitHub rename redirect; version badges still work |
| Unauthorized canonical edits | Propagates flawed protocol | CODEOWNERS + branch protection + mandatory reviews |
| Version drift ignored | Downstream using outdated rules | Verification warnings & CI failing on major mismatch |
| Over-centralization | Local needs blocked | Allow override via local config sections (e.g. `local_overrides:`) |
| Breaking changes | Downstream adoption painful | Semantic versioning + CHANGELOG + deprecation windows |

---

## 9. Semantic Versioning Policy

| Increment | Trigger | Examples |
|----------|---------|----------|
| PATCH (x.y.Z) | Typos, non-functional doc updates | v6.1.1 |
| MINOR (x.Y.z) | New optional sections, scripts, non-breaking config keys | v6.2.0 |
| MAJOR (X.y.z) | Structural changes, removed keys, workflow shifts | v7.0.0 |

Add `VERSION` file to canonical repo root to enable automated checks.

> **Note (2026-08-07)**: the shipped versioning policy additionally caps minor/patch components
> at 0-19 (`9.19.19` is the last release before `10.0.0`) — see root `CLAUDE.md`'s "Component Cap
> Policy" — a refinement added well after this document was written.

---

## 10. Recommended Additions to PR Template (historical — see §0; the shipped process is
maintainer-internal and not part of the consumer-facing protocol)
```markdown
### Canonical Alignment
- [ ] Uses canonical repository reference
- [ ] Local `protocol.config.yaml` version matches canonical VERSION
- [ ] No unauthorized changes to canonical-derived sections
- [ ] If divergence: Justification provided under "Protocol Deviations"
```

---

## 11. Local Override Strategy
Permit deliberate deviations while preserving audit clarity:
```yaml
local_overrides:
  enabled: true
  rationale: "Experimenting with alternative security scan cadence"
  deviations:
    - key: ai.multi_model_review.enabled
      local_value: false
      reason: "Resource constraints in ephemeral environment"
```
Verification script marks overrides as INFO (not WARN) when rationale present.

---

## 12. AI Assistant Integration Notes

| Assistant | Benefit of Canonical Reference | Action |
|-----------|-------------------------------|--------|
| Copilot | Faster resolution of main protocol context | Add link in `.github/copilot-instructions.md` |
| Claude | Direct deep context retrieval for reasoning | Keep CLAUDE.md unchanged; add canonical block |
| Cursor | Project context indexing via single repo pointer | Add canonical pointer in AI_INSTRUCTIONS.md |
| Cody/Tabnine | Unified prompt injection through discovery shim | Mirror canonical reference in docs |

---

## 13. Success Metrics (Post-Adoption — historical targets; not re-measured against current
telemetry as part of this refresh)

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Downstream alignment rate | ≥ 90% within 30 days | Verification script reports |
| Drift incidents | < 2 per quarter | PR audit log |
| Unauthorized protocol edits | 0 | Protected branch metrics |
| AI assistant protocol resolution time | ↓ 30% | Observation / anecdotal + logs |
| Time to apply protocol update downstream | < 5 min | User feedback / timing |

---

## 14. Implementation Checklist (historical — see §0 for current state)
- [x] Add canonical block to `CLAUDE.md` (root, not `protocol/CLAUDE.md` — see §0)
- [ ] ~~Insert `canonical_repository` section in `protocol.config.yaml`~~ (superseded — verify-protocol scripts read differently; see §0)
- [x] `VERSION.md` exists in canonical repo (superset of the originally proposed bare `VERSION` file)
- [x] README Canonical Source reference
- [x] Verification scripts shipped (`scripts/verify-protocol.(ps1|sh)`, `scripts/verify-payload.py`)
- [ ] ~~Extend update scripts with `--canonical-sync`~~ (not built as specified; superseded by the dzp-publish sanitized-release pipeline)
- [ ] ~~Enhance PR template with canonical alignment checklist~~ (release PR process is maintainer-internal, not a consumer-facing PR template)
- [x] Override handling exists via `protocol.config.yaml` local overrides
- [x] Semantic versioning & override policy documented (root `CLAUDE.md`, "VERSION CONTROL & UPDATE ENFORCEMENT")

---

## 15. Final Recommendation (historical, 2025-11-06)
Proceed immediately with Phase 1 (declarative references) to lock a single authoritative source before further protocol enhancements. The cost of centralization is low compared to the ongoing friction of distributed, slightly divergent protocol copies. Treat the canonical repository as **infrastructure**, not just documentation—every automation (verification, update, drift detection) improves reliability and reduces manual cognitive load.

**Adopt now. Drift prevention today avoids costly audit/reconciliation work later.**

*(2026-08-07 postscript: this recommendation was followed. See §0 for how the adopted mechanism
actually looks today, nine minor/major releases later.)*

---

**Canonical Source Adoption – Elevating Domain Zero from powerful protocol to governed, reproducible platform.**

The weight is real. The protocol is absolute. The source is singular.
