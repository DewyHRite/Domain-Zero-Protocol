# RESEARCH MODE SPECIFICATION
## Domain Zero Protocol v7.2.0

**Purpose**: Establish a standardized, auditable, privacy‑respecting workflow that allows each agent (Yuuji, Megumi, Nobara, Gojo) to perform recurring, specialization‑aligned web / literature / standards research, producing structured, citable updates that feed back into project decision making without contaminating core protocol files.

---
## 1. Scope & Goals
**Goals**:
- Keep each agent current on evolving best practices (implementation patterns, OWASP/secure coding, UX standards, orchestration & governance).
- Provide structured, cite‑back outputs with clear provenance, freshness timestamps, and confidence indicators.
- Avoid uncontrolled prompt drift by confining research outputs to dedicated state artifacts (NEVER directly rewriting protocol/*.md without authorized process).
- Enable scheduled or on‑demand sessions with transparent tagging (`@research-start`, `@research-update`, `@research-complete`).
- Preserve privacy: raw notes & transient scrape logs remain gitignored; only curated summaries enter tracked state.

**Out of Scope**:
- Automated execution of unverified code found online.
- Blind incorporation of speculative / unverified claims.
- Non-public or paywalled content without license clearance.

---
## 2. Configuration Additions (protocol.config.yaml)
Add a top‑level `research:` section (planned; doc does not modify config yet):
```yaml
research:
  enabled: true                 # Master toggle (Gojo enforces if false)
  allowed_agents: ["yuuji", "megumi", "nobara", "gojo"]
  cadence:
    yuuji: "weekly"            # cron‑like or human readable: daily|weekly|monthly|manual
    megumi: "weekly"
    nobara: "biweekly"
    gojo: "monthly"            # Intelligence synthesis
  max_session_minutes: 25        # Hard cap per session to prevent fatigue
  source_policy:
    max_sources: 12
    min_primary_sources: 3       # Authoritative standards (RFC, OWASP, W3C, ISO, NIST)
    allow_blogs: true
    allow_forums: false          # Avoid low‑moderation sources by default
    require_publication_year: true
    freshness_years: 3           # Prefer sources <= 3 years old unless canonical
  citation:
    style: "domain-zero-v1"     # Custom inline format defined below
    include_access_timestamp: true
    include_confidence: true
  output:
    aggregate_index: ".protocol-state/research/research-index.json"
    per_agent_dir: ".protocol-state/research/{agent}"  # Dynamic pathing
    summary_filename: "summary.md"      # Curated digest (version controlled optional)
    raw_notes_filename: "raw.log"        # Gitignored scratchpad
  privacy:
    gitignore_raw: true
    redact_pii: true
    store_urls_only: true            # Fetch summary passages; avoid full dumps
  verification:
    run_plagiarism_check: false      # Placeholder for future tool integration
    require_dual_source_corrob: true
    require_security_vuln_crossref: true  # Megumi only
  escalation:
    stale_days_warning: 14           # Notify if no update beyond X days
    critical_domain_stale_days: 7    # OWASP / auth / encryption topics
```

---
## 3. Directory & State Structure
Create (when implemented):
```
.protocol-state/
  research/
    research-index.json            # Global index (JSON schema below)
    yuuji/
      2025-11-09T14-30-00Z.summary.md
      2025-11-09T14-30-00Z.raw.log   (gitignored)
    megumi/
      ...
    nobara/
      ...
    gojo/
      ...
```
**`research-index.json` Schema**:
```jsonc
{
  "version": "1.0",
  "last_global_update": "2025-11-09T14:30:00Z",
  "agents": {
    "yuuji": {
      "last_session": "ISO-8601",
      "recent_topics": ["fastapi testing", "async fixtures"],
      "open_followups": ["Compare pytest plugins coverage"]
    },
    "megumi": {
      "last_session": "ISO-8601",
      "recent_topics": ["OWASP 2025 draft", "JWT best practices"],
      "unresolved_risks": ["New padding oracle paper"]
    },
    "nobara": {
      "last_session": "ISO-8601",
      "recent_topics": ["WCAG 2.2 updates", "Onboarding UX"]
    },
    "gojo": {
      "last_session": "ISO-8601",
      "synthesis_notes_ref": "2025-11-01T10-00-00Z.summary.md"
    }
  }
}
```

---
## 4. Standard Session Workflow
**Phases**:
1. **Initiation** (`@research-start`):
   - Gojo validates `research.enabled` & agent allowed.
   - Loads last session meta for continuity.
2. **Scoping**: Agent forms 3–5 focused questions; rejects overly broad queries.
3. **Source Selection**: Build candidate list; filter via `source_policy`. Require minimum primary sources before blog posts.
4. **Collection**: Retrieve summaries / excerpts (not full dumps). Log URL + snippet + access timestamp.
5. **Triangulation**: Cross-check at least 2 independent sources for each key claim. Mark confidence `High|Medium|Low`.
6. **Synthesis** (`@research-update`): Produce structured summary (see template) with actionable recommendations & follow‑ups.
7. **Validation**:
   - Megumi: map security items to OWASP Top 10, CVE feeds, or NIST.
   - Yuuji: propose code quality / refactor experiments, not direct protocol edits.
   - Nobara: translate findings into UX heuristics / accessibility adjustments.
   - Gojo: integrate into Trigger 19 strategic intelligence (non‑intrusive).
8. **Completion** (`@research-complete`): Persist curated summary, update index; raw notes remain private.

**Session Hard Stops**:
- Reaching `max_session_minutes`.
- Fewer than required primary sources.
- Detection of contradictory high‑impact claims without resolution path.

---
## 5. Output Templates
### 5.1 Summary File (`{timestamp}.summary.md`)
```markdown
# Research Summary – [Agent] – [Timestamp UTC]

## Focus Questions
1. What changed in [...]
2. How are emerging practices addressing [...]
3. ...

## Key Findings
| Topic | Insight | Sources | Confidence |
|-------|---------|---------|------------|
| JWT Refresh Rotation | 30m rotation + short lived access tokens reducing replay window. | [S1][S3] | High |
| Async Test Isolation | Use per-test event loop fixtures to prevent cross-task leakage. | [S2][S5] | Medium |

## Detailed Notes
### 1. JWT Refresh Rotation
- Summary: ...
- Implementation Impact (Yuuji): Proposed experiment ...
- Security Impact (Megumi): Aligns with OWASP A07 updates ...
- UX Impact (Nobara): Surface upcoming token expiry gently ...

### 2. Async Test Isolation
...

## Recommendations (Actionable)
- R1 (Short-term): Introduce rotating refresh token store abstraction.
- R2 (Medium-term): Add automated benchmark for test fixture teardown times.
- R3 (Long-term): Evaluate structured security header generation tool.

## Follow-Ups
- Investigate new padding oracle research (Paper DOI: ...)
- Validate WCAG 2.2 success criteria impact on existing components.

## Source Citations
[S1] OWASP Cheat Sheet: JWT (2024) – https://owasp.org/... (Accessed 2025-11-09) (Confidence: High)
[S2] PyTest Docs – Async Fixtures Section (Accessed 2025-11-09) (Confidence: Medium)
[S3] RFC 9068 OAuth 2.0 JWT Profile (2023) – https://www.rfc-editor.org/rfc/rfc9068 (Accessed 2025-11-09) (High)
[S5] Blog: Testing Async Patterns – <blog URL> (Accessed 2025-11-09) (Low – corroborated by [S2])

## Integrity & Verification
- Dual Source Corroboration: All High confidence items cross‑checked.
- Security Cross‑Reference: Megumi mapped 2 items to OWASP 2025 draft.
- No unlicensed proprietary material stored.

## Session Metadata
Duration: 22 minutes
Primary Sources: 4 / Required: 3
Total Sources: 6
Tags: jwt, async-testing, accessibility
@research-complete
```

### 5.2 Raw Notes File (`{timestamp}.raw.log`) – (gitignored)
Plain text scratchpad: incremental queries, discarded sources, unfiltered snippets. Automatically redacted for obvious PII patterns (email, credit card regex).

---
## 6. Citation Style (domain-zero-v1)
Format: `[S#] Title – URL (Accessed YYYY-MM-DD) (Confidence: High|Medium|Low)`
- **S#**: Sequential per session.
- **Confidence**: Derived from source type + corroboration count:
  - Primary standard + corroborated ⇒ High
  - Reputable documentation (framework, official blog) ⇒ Medium
  - Single blog/forum / not corroborated ⇒ Low

---
## 7. Role-Specific Focus
| Agent  | Primary Focus | Secondary Axes | Exclusions |
|--------|---------------|----------------|------------|
| Yuuji  | Implementation patterns, TDD tooling updates | Build performance, test isolation | Direct protocol edits |
| Megumi | Emerging vulns, OWASP revisions, cryptography papers | Performance regression security ties | Implementation patches |
| Nobara | UX guidelines (WCAG, usability heuristics), onboarding flows | Accessibility tooling evolution | Low-quality marketing blogs |
| Gojo   | Meta trends, coordination tooling, risk landscape | Process optimization metrics | Direct feature design |

---
## 8. Privacy & Compliance
- Raw logs gitignored (config `privacy.gitignore_raw: true`).
- Redaction pipeline masks emails, tokens, obvious secrets.
- No log of personal user browsing history—only explicit research sources.
- GDPR/HIPAA: Avoid storing sensitive medical / personal content unless anonymized.

---
## 9. Verification & Quality Gates
Before persisting `summary.md`:
- [ ] Minimum primary sources met.
- [ ] All High confidence findings have ≥2 sources.
- [ ] No protocol violation (attempt to auto‑modify CLAUDE.md).
- [ ] Security items mapped / dismissed explicitly (Megumi sessions).
- [ ] Accessibility claims tied to WCAG criterion IDs (Nobara).
- [ ] Implementation recommendations framed as experiments (Yuuji) not mandates.

Future script (`scripts/research.ps1`) will automate this checklist.

---
## 10. Scheduling & Staleness Handling
- Gojo compares `last_session` vs `cadence` per agent.
- If `stale_days_warning` exceeded → emit reminder block in next Mission Control interface.
- Critical domains (security/auth) use accelerated threshold (`critical_domain_stale_days`).

---
## 11. Tags & Cross-Linking
Use tags in summaries to allow trend detection (jwt, async-testing, accessibility). Gojo may aggregate frequency in Trigger 19.

---
## 12. Change Management
Protocol changes proposed from research must go through:
1. Research summary recommendation.
2. User approval.
3. Optional Megumi risk vetting.
4. Authorized CLAUDE.md edit (USER or Gojo with explicit authorization).

---
## 13. Future Enhancements (Backlog)
- Automated source freshness scoring.
- Plagiarism / duplication scanning.
- Semantic diff generation vs previous summary.
- Confidence decay model (stale findings auto‑downgraded).
- Optional multi‑model cross‑validation (Tier 3 research sessions).

---
## 14. Implementation Checklist (When Enacting)
1. Add `research` block to `protocol.config.yaml`.
2. Create `.protocol-state/research/` structure & gitignore raw logs.
3. Add invocation guidance sections to agent protocol files.
4. Implement `scripts/research.ps1` with validation pipeline.
5. Update `GOJO.md` with scheduling & staleness reminders.
6. Integrate index updates in Mission Control resume flow.
7. Add quality gate: research summary verification.

---
## 15. Status
This document defines the specification only. Configuration & script changes pending.

@research-spec v1.0
