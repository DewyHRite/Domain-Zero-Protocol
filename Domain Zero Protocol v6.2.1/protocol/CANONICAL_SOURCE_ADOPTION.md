# Canonical Source Adoption & Repository Referencing Strategy
## Repository: <https://github.com/DewyHRite/Domain_Zero_Protocol_DZP>

**Date**: 2025-11-06  
**Protocol Version Target**: v6.1.x (Transition from distributed copies to canonical reference)  
**Status**: Proposed – Ready for Implementation  
**Owner**: Protocol Guardian (Gojo) / Repository Admins  

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

## 3. Repository Referencing Pattern
### 3.1 Canonical Block (Add to `protocol/CLAUDE.md` header)
```markdown
> Canonical Source: https://github.com/DewyHRite/Domain_Zero_Protocol_DZP  
> Current Local Protocol Version: v6.1.0  
> Pinned Commit: <SHA>  
> Verification: Run `./scripts/verify-protocol.(ps1|sh)` – checks canonical alignment
```

### 3.2 Config Injection (`protocol.config.yaml`)
```yaml
canonical_repository:
  url: "https://github.com/DewyHRite/Domain_Zero_Protocol_DZP"
  version: "v6.1.0"
  commit: "<PINNED_SHA>"
  auto_update:
    enabled: false          # Set true if downstream wants automatic pulls
    strategy: "tag"          # tag | commit | latest
    check_on_verify: true    # Verification script warns on mismatch
```

### 3.3 README Badge
```markdown
[![Canonical Protocol](https://img.shields.io/badge/Protocol-Domain_Zero_Canonical-blue)](https://github.com/DewyHRite/Domain_Zero_Protocol_DZP)
```

---

## 4. Required File Adjustments (Phase 1)

| File | Addition | Purpose |
|------|----------|---------|
| `protocol/CLAUDE.md` | Canonical Source block | Declares authority & current version |
| `protocol.config.yaml` | `canonical_repository` section | Machine-readable alignment |
| `README.md` | Badge + Canonical Source section | Discovery & onboarding |
| `AI_INSTRUCTIONS.md` | Link to canonical repo | Cross-assistant resolution |
| `scripts/verify-protocol.*` | Canonical version check | Drift detection |
| `.github/PULL_REQUEST_TEMPLATE.md` | Checkbox: "Matches canonical version" | Review gate |

---

## 5. Verification Script Enhancements
Add a new step:
```bash
# Pseudocode for verify-protocol.sh
if [ -f protocol.config.yaml ]; then
  LOCAL_VER=$(yq '.canonical_repository.version' protocol.config.yaml)
  REMOTE_VER=$(curl -s https://raw.githubusercontent.com/DewyHRite/Domain_Zero_Protocol_DZP/main/VERSION 2>/dev/null || echo "unknown")
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
$RemoteVer = try { (Invoke-WebRequest -UseBasicParsing https://raw.githubusercontent.com/DewyHRite/Domain_Zero_Protocol_DZP/main/VERSION).Content.Trim() } catch { 'unknown' }
if ($RemoteVer -ne 'unknown' -and $LocalVer -ne $RemoteVer) {
  Write-Warn "Canonical version mismatch: local=$LocalVer remote=$RemoteVer"
} else {
  Write-Pass "Canonical version aligned: $LocalVer"
}
```

---

## 6. Update Scripts Extension
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

## 7. Rollout Plan

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

---

## 10. Recommended Additions to PR Template
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

## 13. Success Metrics (Post-Adoption)

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Downstream alignment rate | ≥ 90% within 30 days | Verification script reports |
| Drift incidents | < 2 per quarter | PR audit log |
| Unauthorized protocol edits | 0 | Protected branch metrics |
| AI assistant protocol resolution time | ↓ 30% | Observation / anecdotal + logs |
| Time to apply protocol update downstream | < 5 min | User feedback / timing |

---

## 14. Implementation Checklist
- [ ] Add canonical block to `protocol/CLAUDE.md`
- [ ] Insert `canonical_repository` section in `protocol.config.yaml`
- [ ] Create `VERSION` file in canonical repo (initial: v6.1.0)
- [ ] Add README badge & Canonical Source section
- [ ] Upgrade verification scripts with version compare
- [ ] Extend update scripts with `--canonical-sync`
- [ ] Enhance PR template with canonical alignment checklist
- [ ] Add override handling logic (optional)
- [ ] Document semantic versioning & override policy

---

## 15. Final Recommendation
Proceed immediately with Phase 1 (declarative references) to lock a single authoritative source before further protocol enhancements. The cost of centralization is low compared to the ongoing friction of distributed, slightly divergent protocol copies. Treat the canonical repository as **infrastructure**, not just documentation—every automation (verification, update, drift detection) improves reliability and reduces manual cognitive load.

**Adopt now. Drift prevention today avoids costly audit/reconciliation work later.**

---

**Canonical Source Adoption – Elevating Domain Zero from powerful protocol to governed, reproducible platform.**

The weight is real. The protocol is absolute. The source is singular.
