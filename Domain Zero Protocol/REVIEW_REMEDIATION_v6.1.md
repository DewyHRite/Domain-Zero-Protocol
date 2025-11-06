# Domain Zero Protocol v6.1 Review Remediation & Fix Plan
Date: 2025-11-06  
Scope: PR corrections, documentation alignment, configuration hygiene, workflow robustness, markdown lint compliance
Status: Proposed – Ready for Patch Application  
Owner: Protocol Guardian (Gojo) / Repository Maintainers

---
## 1. Executive Summary
The review surfaced accuracy gaps, lint violations, outdated model references, path mismatches, incomplete feature flags, and documentation drifts. This plan consolidates all actionable fixes into a structured remediation sequence to reach a clean, compliant, and internally consistent v6.1 baseline.

Priorities:
1. Integrity & Accuracy (remove or align misrepresented files, fix broken links, correct PR summary)
2. Security & Protection (CODEOWNERS placement, workflow auth interpolation, model version currency)
3. Consistency (self-identification, config guidance, permission alignment)
4. Tooling Robustness (scripts path logic, argument handling, regex portability)
5. Lint & UX Polish (language specifiers, headings, capitalization, URL formatting)

---
## 2. High-Priority (Blocking) Fixes
| ID | Issue | File | Action | Rationale |
|----|-------|------|--------|-----------|
| HP-01 | Committed local-only settings file | `.claude/settings.local.json` | Remove from repo & keep ignored OR justify tracking | Violates stated rule (local-only, privacy) |
| HP-02 | Broken reference to `protocol/NOBARA.md` | `.github/copilot-instructions.md` | Create missing `protocol/NOBARA.md` (preferred) or remove link | Role completeness & onboarding |
| HP-03 | CODEOWNERS ineffective due to path | `Domain Zero Protocol/CODEOWNERS` | Move/duplicate to repo root or `.github/CODEOWNERS` | Enforce protection rules |
| HP-04 | PR summary mismatch (describes v6.0) | `PR_SUMMARY.md` | Rewrite to reflect actual v6.1 changes | Prevent audit confusion |
| HP-05 | Workflow actor variable not interpolated | `.github/workflows/security-scan-example.yml` | Pass `github.actor` via env & use `$GITHUB_ACTOR` | Authorization check currently inert |
| HP-06 | Outdated / invalid model references | `protocol.config.yaml` | Replace retired/nonexistent models; update comments | Prevent runtime model selection failure |
| HP-07 | Incorrect path usage in desktop wrapper sample | `DESKTOP_WRAPPER.md` (core.js snippet) | Adjust paths to actual repo structure | Avoid user copying broken example |

---
## 3. Medium-Priority Fixes
| ID | Issue | File | Action |
|----|-------|------|--------|
| MP-01 | Missing language specifiers (multiple) | Various md | Add appropriate language tags (`text`, `bash`, `json`, `codeowners`, etc.) |
| MP-02 | Headings formatted as emphasis | Multiple md | Convert emphasized titles to proper `##` headings |
| MP-03 | Bare URLs triggering linter warnings | `CLAUDE.md`, `CANONICAL_SOURCE_ADOPTION.md` | Wrap in `< >` where required |
| MP-04 | Unused `--fix` option | `scripts/verify-protocol.sh` | Remove flag & variable or implement basic auto-fix |
| MP-05 | Regex portability (`\s` vs `[[:space:]]`) | `scripts/verify-protocol.sh` | Replace with POSIX character class |
| MP-06 | Argument parsing exit code (unknown option) | `scripts/update-instructions.sh` | Non-zero exit on invalid args |
| MP-07 | Pattern matching for instruction files | `scripts/update-instructions.sh` | Correct directory-aware pattern search |
| MP-08 | Precise string matches for protocol pointer | `scripts/update-instructions.sh` | Use `grep -F` for fixed strings |
| MP-09 | Using echo instead of printf | `scripts/update-instructions.sh` | Switch to `printf '%s\n'` |
| MP-10 | Add guidance for `<PINNED_SHA>` placeholder | `protocol.config.yaml` | Clarify optional commit pinning comment |

---
## 4. Low-Priority Polish
| ID | Issue | File | Action |
|----|-------|------|--------|
| LP-01 | GitHub capitalization | README, AI_INSTRUCTIONS, others | Replace "Github" with "GitHub" |
| LP-02 | Verb style clarity ("fix", "resolves") | Template & docs | Minor wording adjustments for formal tone |
| LP-03 | Repetitive wording (observes/Observation) | `CLAUDE.md` glossary | Slight wording alternation |
| LP-04 | Missing consent prompt language specifier | `GOJO.md` | Add `text` to fenced block |
| LP-05 | Example CODEOWNERS block language tag | `CLAUDE.md` | Use `codeowners` or `text` |
| LP-06 | Add explicit EXIT CODES section | `scripts/update-instructions.sh` | Document drift detection behavior |

---
## 5. Model Version Remediation
Current config uses:
```
claude-3-5-sonnet-20241022   (retired Oct 2025)
claude-3-5-haiku-20241022    (still valid)
claude-3-5-opus-20241022     (nonexistent; use Opus 4)
```
Recommended replacements:
```yaml
ai:
  default_models:
    - provider: "Anthropic"
      model: "claude-3-5-haiku-20241022"   # Rapid / low-cost
      scope: "rapid-tier"
      priority: 2
    - provider: "Anthropic"
      model: "claude-3-5-sonnet-20241022"  # Mark as legacy OR replace if new Sonnet available
      scope: "all-clients"
      priority: 3
    - provider: "Anthropic"
      model: "claude-opus-4-20250514"      # High rigor security reviews
      scope: "megumi-only"
      priority: 1
```
Add comment noting Sonnet retirement and pending upgrade path. If latest Sonnet/Haiku snapshots exist, replace accordingly once verified.

---
## 6. Permissions Alignment
Documentation lists `Bash(git add:*)` while JSON omits it.
Action: Remove `.claude/settings.local.json` from version control (preferred) OR update JSON.
If updating (less preferred):
```json
{
  "permissions": {
    "allow": [
      "Bash(git commit:*)",
      "Bash(find:*)",
      "Bash(git add:*)"
    ],
    "deny": [],
    "ask": []
  }
}
```
Add note in `permissions-schema.md`: “Example allow list; local teams may expand.”

---
## 7. CODEOWNERS Relocation
Move file from `Domain Zero Protocol/CODEOWNERS` to either:
- Repository root: `/CODEOWNERS`
- Or `.github/CODEOWNERS`
Sample content (ensure admin team handle):
```codeowners
protocol/CLAUDE.md @repo-admins
protocol/*.md      @repo-admins
scripts/*.sh       @dev-leads
scripts/*.ps1      @dev-leads
```

---
## 8. Desktop Wrapper Sample Path Corrections
Existing hard-coded paths use `domain_zero/` while actual layout is `Domain Zero Protocol/` or if installed inside a consumer repo, recommended flattening. Provide dual-mode logic:
```js
const LEGACY_ROOT = "Domain Zero Protocol"; // current
const ALT_ROOT = "domain_zero";             // target standard name (future)

function resolveConfigPath(root) {
  const candidates = [
    path.join(root, LEGACY_ROOT, "protocol.config.yaml"),
    path.join(root, ALT_ROOT, "protocol.config.yaml")
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  throw new Error("protocol.config.yaml not found in expected locations");
}
```
Update glob usage to directly read `protocol/YUUJI.md` and `protocol/MEGUMI.md` instead of wildcard patterns that currently miss.

---
## 9. Workflow Authorization Fix
Replace actor interpolation logic; ensure accurate handling of first commit.
Diff excerpt:
```diff
env:
-  PROTOCOL_MAINTAINERS: ${{ secrets.PROTOCOL_MAINTAINERS }}
+  PROTOCOL_MAINTAINERS: ${{ secrets.PROTOCOL_MAINTAINERS }}
+  GITHUB_ACTOR: ${{ github.actor }}
@@
-CHANGED_FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null || git diff --name-only HEAD)
+if [ "$COMMIT_COUNT" -eq 1 ]; then
+  CHANGED_FILES=$(git ls-tree -r --name-only HEAD)
+else
+  CHANGED_FILES=$(git diff --name-only HEAD~1..HEAD)
+fi
@@
-if [[ ! " ${AUTHORIZED_USERS[@]} " =~ " ${{ github.actor }} " ]]; then
+if [[ ! " ${AUTHORIZED_USERS[@]} " =~ " $GITHUB_ACTOR " ]]; then
```
Add comment recommending pinning action versions and note template nature.

---
## 10. Script Remediation
### `scripts/update-instructions.sh`
- Adjust usage function to accept exit code.
- Correct pattern matching for subdirectories.
- Replace `echo` with `printf`.
- Add EXIT CODES section.
- Use `grep -F` for fixed-string detection.

### `scripts/verify-protocol.sh`
Option A (minimal): Remove `--fix` references entirely.
Option B (basic fix feature): Implement placeholder correction (e.g., replace `<PINNED_SHA>` with actual SHA when provided env var).
Recommended now: Option A for clarity.

### Regex portability fix:
```bash
# Before
grep -q "claude_md_protected:\s*true"
# After
grep -q "claude_md_protected:[[:space:]]*true"
```

---
## 11. Markdown Lint Fix Matrix
| Rule | Example Offender | Fix |
|------|------------------|-----|
| MD040 (language) | Multiple fenced blocks | Add `text`, `bash`, `json`, `powershell`, etc. |
| MD036 (emphasis as heading) | PASSIVE_OBSERVER.md line 3 | Convert to `##` heading |
| MD034 (bare URL) | Canonical source lines | Wrap `<https://...>` |
| MD058 (tables blank lines) | CANONICAL_SOURCE_ADOPTION.md | Insert blank lines before/after tables |
| MD051 (link fragments) | README internal anchors | Validate or adjust section IDs |

---
## 12. PR Summary Rewrite Template (v6.1)
```markdown
# PR Summary – Domain Zero Protocol v6.1
Branch: protocol-v6.1-no-desktop
Commits: 6

## Key Enhancements
- Self-Identification Standard (agent banners, continuity rules)
- Canonical Source Adoption (CLAUDE.md pointer + config block)
- Privacy Reinforcement (Passive Observer OFF by default + consent flow)
- AI Model Configuration Alignment (high-rigor security model scope)
- Lint & Documentation Polish (language tags, headings normalization)

## Added Files
- `protocol/AGENT_SELF_IDENTIFICATION_STANDARD.md`
- `protocol/CANONICAL_SOURCE_ADOPTION.md`

## Modified Files (Selected)
- `protocol/CLAUDE.md` (version metadata, canonical block, self-ID principle)
- `protocol/GOJO.md` (consent prompt formatting)
- `protocol/MEGUMI.md` (tooling integration expansion)
- `protocol.config.yaml` (self_identification + canonical_repository sections)

## Removed / Not Included
- Desktop wrapper (deferred; examples retained only as guidance)

## Compliance & Security
- CODEOWNERS relocation planned
- Workflow authorization fix queued
- Model version modernization pending (Opus 4)

## Backward Compatibility
- No breaking changes; all new sections additive.

## Next Steps
- Apply script improvements
- Pin action versions when enabling CI template
```

---
## 13. Ordered Remediation Sequence
1. Remove `.claude/settings.local.json` (git rm) – ensure ignore retained.
2. Relocate CODEOWNERS to root.
3. Create/verify `protocol/NOBARA.md` if missing.
4. Rewrite `PR_SUMMARY.md` using template.
5. Update `protocol.config.yaml` model list + `<PINNED_SHA>` comment.
6. Patch workflow authorization & first-commit logic.
7. Adjust desktop wrapper code snippet paths.
8. Script fixes (`update-instructions.sh`, `verify-protocol.sh`).
9. Add language specifiers + heading fixes across docs.
10. Apply regex portability adjustments.
11. Wrap bare URLs & fix tables spacing.
12. Final lint and verification run.

---
## 14. Verification Checklist Post-Remediation
| Check | Tool / Method | Target Result |
|-------|---------------|---------------|
| CODEOWNERS active | GitHub UI / test PR | Ownership rules enforced |
| Workflow auth | Dry run action | Blocks unauthorized actor edit |
| Model validity | Test minimal AI call | All configured models resolve |
| Self-ID presence | grep banners | All 4 agent files contain standard block |
| Lint pass | markdownlint-cli2 | Zero MD040/MD036/MD034 errors |
| Script robustness | shellcheck / pwsh tests | No unused vars / proper exit codes |
| Removal of local-only file | git status | `.claude/settings.local.json` absent |

---
## 15. Diff Snippet Examples
### CODEOWNERS relocation
```diff
- Domain Zero Protocol/CODEOWNERS
+ CODEOWNERS
```
### verify-protocol.sh remove fix flag
```diff
- FIX=false
@@
-        --fix)
-            FIX=true
-            shift
-            ;;
```
### update-instructions.sh usage exit code
```diff
-function usage() {
+function usage() {
@@
-    exit 0
+    exit ${1:-0}
}
```

---
## 16. Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Model mismatch persists | Security review degraded | Explicit validation after config patch |
| Local-only file recommitted | Privacy leakage | Pre-commit hook to block `.claude/settings.local.json` |
| Workflow still not pinned | Future breakage | Add TODO comments & follow-up ticket |
| Drift in CODEOWNERS path | Protection ineffective | CI check verifying file presence at root |

---
## 17. Follow-Up (Post v6.1 Stabilization)
- Implement `--fix` automation (placeholder and pointer insertion)
- Add VERSION file or retire reference in adoption doc (choose single source)
- Introduce optional localization overrides for banners
- Add automated model currency audit (compare against provider API)

---
## 18. Approval & Execution
Approvals required:
- Security Lead (model & workflow changes)
- Protocol Guardian (structural doc changes)
- Repo Admin (CODEOWNERS relocation)

Execution window recommended: Single branch patch with atomic commits per remediation category (to simplify review).

---
## 19. Summary
This remediation plan aligns documentation, config, workflows, and scripts to the declared v6.1 feature set while eliminating inconsistencies and strengthening enforcement mechanisms. Applying these changes yields a clean, auditable, and future-ready protocol baseline.

Proceed with implementation per ordered sequence to avoid dependency conflicts (e.g., remove local-only file before committing CODEOWNERS adjustments).

---
**The protocol must be consistent to be trustworthy. Consistency begins with this remediation.**
