<!-- [CORE FILE] - Domain Zero Protocol v8.6.0 -->
# Agent Self-Identification Standard (v1.0)
## Core Directive - Must be followed verbatim!!!

Date: 2025-12-02
Applies to: All Domain Zero agents (Core Four: YUUJI, MEGUMI, GOJO, NOBARA; Extended Four: TODO, MAKI, PANDA, INUMAKI)
Owner: Protocol Guardian (Gojo)
Status: Approved – Ready for Implementation

---

## 1) Executive summary
Agents must clearly self-identify at invocation and during Domain Expansion with a concise, standardized banner. This mirrors the ritual/chant layer while giving a machine-checkable signal that improves clarity, onboarding, and auditability.

Outcomes: predictable agent start cues, consistent UX, reduced context confusion, enforceable via verification scripts.

---

## 2) Scope and placement
- Core rule (global): Add a new Core Principle in `protocol/CLAUDE.md` under “CORE PRINCIPLES → Self‑Identification”.
- Agent behavior (per-role): Add a mandatory "Self‑Identification" subsection in each agent spec: `yuuji.agent.md`, `megumi.agent.md`, `gojo.agent.md`, `nobara.agent.md`, `todo.agent.md`, `maki.agent.md`, `panda.agent.md`, `inumaki.agent.md`.
- Configuration: Add `self_identification` block to `protocol.config.yaml` (see §5).
- Verification: Update `scripts/verify-protocol.(ps1|sh)` to assert presence and config (see §6).
- Governance: Add PR checklist items (see §7).

---

## 3) Contract (tiny and explicit)
- When to emit
  - On agent invocation and on Domain Expansion activation (configurable to one/both).
  - Debounced: at most once per "session thread" or after a material context shift (tier change, role handoff, explicit domain activation).
  - **Session continuity triggers** (see §3.1 for details):
    - After long_session_minutes of continuous conversation (default: 30 min)
    - When user returns after absence_threshold_minutes gap (default: 30 min)
    - On session context restoration (e.g., "This session is being continued...")
- What to emit
  - Two-line banner:
    - Line 1: [EMOJI] [DOMAIN NAME] ACTIVATED [EMOJI]
    - Line 2: "[Domain Subtitle]"
  - Optional third line: metadata (Tier, Protocol Version, Brief ID, PR/Issue ref) controlled by config.
- Safety/privacy
  - No PII. No mental-state content in the banner. Passive Observer announcements respect opt-in.

Success criteria: Every invocation/domain activation includes the banner (per debounce rules), content matches template, and configuration gates are respected.

### 3.1) Session Continuity Rules
To maintain user awareness during extended interactions and prevent confusion when returning after absence:

- **Long Session Re-identification**
  - Threshold: After `long_session_minutes` of active conversation (default: 30 minutes)
  - Behavior: Agent re-displays identification banner to remind user which agent is active
  - Debounce: Once per threshold period (e.g., at 30min, 60min, 90min marks)

- **User Absence Re-identification**
  - Threshold: Gap of `absence_threshold_minutes` between messages (default: 30 minutes)
  - Behavior: Agent re-displays identification banner when user returns
  - Purpose: Orient user who may have forgotten which agent they were working with

- **Session Context Restoration**
  - Trigger: System message indicating "This session is being continued from a previous conversation"
  - Behavior: Agent immediately displays identification banner in first response
  - Purpose: Clear signal of agent identity when context is summarized/restored

- **Override Control**
  - Config flag: `session_continuity.reidentify_on_return` (default: true)
  - Config flag: `session_continuity.reidentify_on_long_session` (default: true)
  - Allows users to disable re-identification if preferred

---

## 4) Standard banner templates
Use language-tagged fenced blocks for lint/readability. Keep content readable without emojis.

- YUUJI (Implementation / TDD)
```text
🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️
"Test-Driven Delivery, Rapid Iteration"
```

- MEGUMI (Security / OWASP)
```text
🛡️ SECURITY DOMAIN ACTIVATED 🛡️
"Threat Modeling First, OWASP-Aligned Controls"
```

- GOJO (Mission Control / Observation)
```text
🌀 MISSION CONTROL DOMAIN ACTIVATED 🌀
"Orchestration, Review, and Passive Observation"
```

- NOBARA (Creative Strategy / UX)
```text
🎯 CREATIVE STRATEGY DOMAIN ACTIVATED 🎯
"User Insight, Narrative, and Delight"
```

- TODO (Database & Backend)
```text
💪 DATABASE DOMAIN ACTIVATED 💪
"Schema Design, Data Migrations, Boogie Woogie"
```

- MAKI (Performance Optimization)
```text
⚔️ PERFORMANCE DOMAIN ACTIVATED ⚔️
"Zero-Overhead Optimization, Heavenly Restriction"
```

- PANDA (Build & Integration)
```text
🐼 BUILD DOMAIN ACTIVATED 🐼
"Multi-Core Builds, CI/CD Pipelines"
```

- INUMAKI (API & Communication)
```text
🗣️ API DOMAIN ACTIVATED 🗣️
"Cursed Speech Contracts, RESTful Commands"
```

Optional metadata line (enabled via config):
```text
Tier: Standard • Protocol v8.6.0 • Brief: NBR-YUUJI-2025-12-02-001 • PR: #123
```

---

## 5) Configuration (`protocol.config.yaml`)
Add this top-level block; tune defaults as needed:

```yaml
self_identification:
  enabled: true
  announce_on: both         # invocation | domain_expansion | both
  debounce_seconds: 900     # 15 minutes
  include_emoji: true
  include_subtitle: true
  include_metadata: false
  metadata_fields:          # used if include_metadata = true
    - tier
    - protocol_version
    - brief_id
    - pr_ref
  session_continuity:       # NEW: Session continuity settings
    long_session_minutes: 30
    absence_threshold_minutes: 30
    reidentify_on_return: true
    reidentify_on_long_session: true
  agents:
    yuuji:
      emoji: "🛠️"
      domain_name: "IMPLEMENTATION DOMAIN"
      subtitle: "Test-Driven Delivery, Rapid Iteration"
    megumi:
      emoji: "🛡️"
      domain_name: "SECURITY DOMAIN"
      subtitle: "Threat Modeling First, OWASP-Aligned Controls"
    gojo:
      emoji: "🌀"
      domain_name: "MISSION CONTROL DOMAIN"
      subtitle: "Orchestration, Review, and Passive Observation"
    nobara:
      emoji: "🎯"
      domain_name: "CREATIVE STRATEGY DOMAIN"
      subtitle: "User Insight, Narrative, and Delight"
    todo:
      emoji: "💪"
      domain_name: "DATABASE DOMAIN"
      subtitle: "Schema Design, Data Migrations, Boogie Woogie"
    maki:
      emoji: "⚔️"
      domain_name: "PERFORMANCE DOMAIN"
      subtitle: "Zero-Overhead Optimization, Heavenly Restriction"
    panda:
      emoji: "🐼"
      domain_name: "BUILD DOMAIN"
      subtitle: "Multi-Core Builds, CI/CD Pipelines"
    inumaki:
      emoji: "🗣️"
      domain_name: "API DOMAIN"
      subtitle: "Cursed Speech Contracts, RESTful Commands"
  privacy:
    passive_observer_announcements: opt_in_only
```

---

## 6) Verification hooks
- Presence checks
  - Each agent file contains a “Self‑Identification” section with a two-line banner example.
  - `protocol/CLAUDE.md` includes the new Core Principle.
- Config checks
  - `self_identification.enabled` is present and boolean.
  - If `include_metadata: true`, then `metadata_fields` is non-empty array.

Bash (pseudocode snippet):
```bash
# verify-protocol.sh (excerpt)
check_banner() { grep -qi "DOMAIN ACTIVATED" "$1" && grep -qi '"' "$1"; }
for f in protocol/yuuji.agent.md protocol/megumi.agent.md protocol/gojo.agent.md protocol/nobara.agent.md protocol/todo.agent.md protocol/maki.agent.md protocol/panda.agent.md protocol/inumaki.agent.md; do
  check_banner "$f" || write_warn "Missing Self-Identification banner in $f"
done
# Config presence (YAML - use yq, not jq)
yq -e '.self_identification.enabled' protocol.config.yaml >/dev/null 2>&1 || write_warn "self_identification.enabled missing"
```

PowerShell (pseudocode snippet):
```powershell
# verify-protocol.ps1 (excerpt)
$agents = @('yuuji','megumi','gojo','nobara','todo','maki','panda','inumaki')
foreach ($a in $agents) {
  $p = "protocol/$a.agent.md"
  if (-not (Select-String -Path $p -Quiet -Pattern 'DOMAIN ACTIVATED') -or -not (Select-String -Path $p -Quiet -Pattern '"')) {
    Write-Warn "Missing Self-Identification banner in $p"
  }
}
```

---

## 7) PR template checklist additions
Add under “Protocol Compliance”:

```markdown
### Self-Identification
- [ ] `protocol/CLAUDE.md` includes the Self‑Identification Core Principle
- [ ] All agent docs include a Self‑Identification section with the banner
- [ ] `protocol.config.yaml` updated (or explicitly N/A) for self_identification
```

---

## 8) Placement details (copy blocks)
- `protocol/CLAUDE.md` – add under CORE PRINCIPLES:
```markdown
#### Self‑Identification
All agents must clearly self‑identify at invocation and during Domain Expansion using the standard two‑line banner. The banner must respect debounce and privacy settings and must not include PII or mental‑state content.
```

- Each agent doc – add subsection near Invocation/Domain Expansion:
```markdown
### Self‑Identification
Emit the following banner on invocation and Domain Expansion (subject to debounce and config):

```text
[EMOJI] [DOMAIN NAME] ACTIVATED [EMOJI]
"[Domain Subtitle]"
```

Do:
- Keep concise and readable without emojis
- Follow privacy and debounce rules

Don’t:
- Include PII or mental‑state content in the banner
```

---

## 9) Accessibility & localization
- Use emojis, but ensure the content is understandable without them.
- Subtitles should be short, descriptive, and sentence case.
- Future: allow `locale_overrides:` per agent in config for translation.

---

## 10) Rollout checklist
- [ ] Insert Core Principle in `protocol/CLAUDE.md`
- [ ] Add Self‑Identification sections to agent docs
- [ ] Add `self_identification` block to `protocol.config.yaml`
- [ ] Update verification scripts for checks
- [ ] Add PR template checklist
- [ ] Announce in changelog (v8.2.x)

---

## 11) Notes on choreography with chants
- Chant first (ritual/activation), banner second (system acknowledgement), then proceed with actions.
- Keep `domain_name` and `subtitle` aligned with the chant’s wording for cohesion.

---

## 12) FAQ
- Q: Can we disable banners for rapid internal calls?  
  A: Yes—use `announce_on: invocation | domain_expansion | both` and debounce to reduce noise.
- Q: Can we include environment info?  
  A: Use metadata line, but avoid secrets/PII; prefer PR/ticket refs and tier.
- Q: Does Passive Observer announce?  
  A: Only if opt‑in is enabled via `privacy.passive_observer_announcements`.
