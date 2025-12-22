# Gojo Tier Validation Skill
<!-- [SKILL] - Domain Zero Protocol v8.9.0 -->

**Skill Name**: gojo-tier-validation
**Owner**: Gojo (Mission Control)
**Version**: 1.0.0
**Created**: 2025-12-17
**Category**: Operational / Tier Enforcement

---

## Purpose

This skill provides comprehensive tier validation, monitoring, and statistics tracking for all Domain Zero Protocol workflows. As Mission Control, Gojo uses this skill to ensure tier requirements are met and track tier usage patterns across all project work.

---

## When to Use This Skill

**Invoke this skill when**:
- Briefing agents on tier requirements before task assignment
- Monitoring tier compliance during active work sessions
- Verifying tier statistics after task completion
- Generating tier analytics for Trigger 19 intelligence reports
- Enforcing tier-specific behaviors (Tier 1 speed, Tier 2 production, Tier 3 critical)

---

## ✅ TIER VALIDATION (v8.8.0+)

**NEW IN v8.8.0**: As Mission Control, I enforce tier validation across all agents and track tier usage statistics.

**Tier Configuration Source**: `protocol/tier-defaults.yaml`

### My Tier Enforcement Responsibilities

**As Mission Control, I must**:
1. **Enforce tier selection before task assignment** - Verify agents know their tier before work begins
2. **Monitor tier compliance during execution** - Alert if tier requirements violated
3. **Verify tier statistics update after task completion** - Ensure statistics remain accurate
4. **Track tier usage patterns** - Identify trends in Trigger 19 reports

### Step 1: Enforce Tier Selection Before Task Assignment

**When briefing agents, I must**:
1. Determine the current tier:
   - Check if user specified `--tier [rapid|standard|critical]` flag
   - If not specified, read from `session-state.json`
   - If no tier found, **default to Tier 2 (Standard)**
2. Brief the agent on tier requirements:
   - Tier 1: "This is rapid prototyping - skip tests and security review"
   - Tier 2: "This is standard production - test-first + security review recommended (advisory)"
   - Tier 3: "This is critical feature - enhanced testing + multi-model security recommended (advisory)"
3. Verify agent acknowledges tier guidelines before proceeding

**Tier Briefing Format**:
```markdown
Current Tier: Tier [1|2|3]
Requirements:
- [List tier-specific requirements from tier-defaults.yaml]

Proceed only after confirming tier compliance.
```

### Step 2: Monitor Tier Compliance During Execution

**I must monitor for tier violations** (passive observation when enabled):
- ❌ **ALERT**: Yuuji writes implementation before tests (Tier 2/3 violation)
- ❌ **ALERT**: Yuuji skips security review handoff (Tier 2/3 violation)
- ❌ **ALERT**: Megumi skips enhanced review for Tier 3 feature
- ❌ **ALERT**: Yuuji skips E2E tests for Tier 3 feature
- ❌ **ALERT**: User bypasses tier requirements (track in statistics)

**Violation Alert Format**:
```markdown
⚠️ TIER VALIDATION ALERT

Tier: Tier [1|2|3]
Violation: [description]
Agent: [agent name]
Recommended Action: [action to resolve]

This violation has been logged. Proceed with remediation?
```

### Step 3: Verify Tier Statistics Update After Task Completion

**After each task completion, I must verify** (Phase 4 Component 2 - Week 2):
1. Check `project-state.json → tier_usage_statistics`
2. Verify tier counter incremented for active tier
3. Verify `last_used` timestamp updated (ISO-8601)
4. Verify `avg_time_minutes` updated (rolling average)
5. If statistics not updated, alert user and update manually

**Statistics Verification Checklist**:
- [ ] Tier counter incremented (`tier_X_rapid|standard|critical.total_features++`)
- [ ] `last_used` timestamp updated
- [ ] `avg_time_minutes` recalculated
- [ ] Changes saved to project-state.json

**Manual Statistics Update** (if auto-update fails):
```json
{
  "tier_usage_statistics": {
    "tier_2_standard": {
      "total_features": 15,
      "avg_time_minutes": 42,
      "last_used": "2025-12-06T10:30:00Z"
    }
  }
}
```

### Step 4: Track Tier Usage Patterns (Trigger 19)

**AUTOMATIC TIER STATISTICS (v8.8.0+)**:

Tier usage is now tracked automatically using `scripts/tier-statistics.py` and stored in `project-state.json`.

**In Trigger 19 intelligence reports, I must**:
1. **Read tier statistics** from `project-state.json` → `tier_statistics` section
2. **Generate markdown report** using: `python scripts/tier-statistics.py --report --format markdown`
3. **Include tier analysis** in Trigger 19 output under "Tier Usage Analysis (v8.8.0)"
4. **Add recommendations** based on compliance rates and tier selection patterns

**How to Generate Tier Statistics for Trigger 19**:
```bash
# Option 1: Call tier-statistics.py directly
python scripts/tier-statistics.py --report --format markdown

# Option 2: Read from project-state.json
# Read .protocol-state/project-state.json → tier_statistics section
# Format into markdown report manually
```

**Trigger 19 Tier Section Format (v8.8.0+)**:
```markdown
### TIER USAGE ANALYSIS (v8.8.0)

**Tier Distribution (Lifetime)**:
- Tier 1 (Rapid): 5 features (20%)
- Tier 2 (Standard): 15 features (60%)
- Tier 3 (Critical): 5 features (20%)

**Compliance Rates**:
- Tier 1: 100% [OK]
- Tier 2: 92% [WARN] (investigate 2 violations)
- Tier 3: 87% [WARN] (needs improvement)

**Average Time Per Tier**:
- Tier 1: 12 min (within target)
- Tier 2: 38 min (within target)
- Tier 3: 75 min (within target)

**Tier Bypass Events**: 1 total
**Tier Violations**: 2 total

**Last 30 Days**:
- Tier 1: 3 features
- Tier 2: 12 features
- Tier 3: 2 features

**Recommendations**:
1. Tier 2 compliance at 92% - investigate 2 violations
2. Tier selection appropriate (60% Tier 2 aligns with production focus)
3. Time estimates accurate across all tiers
4. Consider Tier 3 for upcoming user data export (PII handling)
```

**Statistics Source**: `.protocol-state/project-state.json` → `tier_statistics`
**Utility**: `scripts/tier-statistics.py`
**Configuration**: `protocol.config.yaml` → `tier_statistics`

### My Tier-Specific Behaviors (Gojo Mission Control)

**Tier 1 (Rapid) - I permit speed**:
- ✅ Allow test-first skip (prototype workflow)
- ✅ Allow security review skip (deliberate for Tier 1)
- ⚠️ **Still enforce** backup requirement (safety baseline)
- ⚠️ **Still enforce** rollback plan requirement (safety baseline)
- ⏱️ Monitor: Target 10-15 minutes total

**Tier 2 (Standard) - I enforce production workflow** [DEFAULT]:
- ✅ **Enforce** test-first requirement (block if violated)
- ✅ **Prompt** for security review after implementation
- ✅ **Verify** backup created before changes
- ✅ **Verify** rollback plan documented
- ❌ **Alert** if security review skipped (Tier 2 violation)
- ⏱️ Monitor: Target 30-45 minutes total

**Tier 3 (Critical) - I enforce maximum safety**:
- ✅ **Enforce** test-first requirement (strict enforcement)
- ✅ **Enforce** integration tests requirement
- ✅ **Enforce** E2E tests requirement (Playwright/Cypress)
- ✅ **Enforce** enhanced security review
- ✅ **Prompt** for multi-model security review (Opus when available)
- ✅ **Verify** performance benchmarks included
- ✅ **Verify** comprehensive backup (code + database)
- ✅ **Verify** extensive rollback plan with verification steps
- ❌ **Block** deployment if any Tier 3 requirement missing
- ⏱️ Monitor: Target 60-90 minutes total

### Tier Enforcement Actions

**If I detect a tier violation**:
1. **PAUSE workflow** - stop current operation
2. **ALERT user** - explain violation and tier requirement
3. **OFFER options**:
   - Option A: Meet tier requirement (recommended)
   - Option B: User bypasses tier requirement (logged)
   - Option C: Change tier (e.g., Tier 3 → Tier 2)
4. **LOG decision** - record in project-state.json → tier_settings.bypass_tracking
5. **RESUME** - only after user authorization

**Tier Compliance Priority** (Advisory + Statistics Tracking):
- **P0**: Tier 3 safety requirements (authentication, payments) - STRONGLY RECOMMENDED (bypasses logged, user decision)
- **P1**: Tier 2/3 test-first guideline - RECOMMENDED (bypasses logged, user decision)
- **P2**: Tier 2/3 security review - PROMPT (skip logged, user decision)
- **P3**: Tier statistics update - VERIFY (manual update if needed)

**Note**: Tier system is ADVISORY. Users may bypass recommendations, but all deviations are logged in tier statistics for transparency.

### Integration with Existing Tier System

**This new validation system** (v8.8.0+) **works with** existing Mission Control functions:
- ✅ Tier briefing added to Option 1 (Resume) and Option 2 (New Project)
- ✅ Tier compliance monitoring added to passive observation
- ✅ Tier analytics added to Trigger 19 intelligence reports
- ✅ Tier enforcement added to workflow management

**See**:
- `protocol/tier-defaults.yaml` - Tier profile definitions
- `protocol/TIER-SELECTION-GUIDE.md` - User guidance on tier selection
- `protocol/gojo.agent.md` - Mission Control operational procedures

---

## Skill Outputs

**Expected outputs when using this skill**:
1. **Tier briefing message** for agents (formatted markdown)
2. **Tier violation alerts** (when monitoring detects issues)
3. **Tier statistics report** (for Trigger 19 intelligence)
4. **Enforcement decisions** (pause/resume workflow based on compliance)

---

## Dependencies

**This skill requires**:
- `protocol/tier-defaults.yaml` - Tier configuration profiles
- `.protocol-state/project-state.json` - Tier statistics storage
- `.protocol-state/session-state.json` - Current tier setting
- `scripts/tier-statistics.py` - Statistics utility (optional)

---

## Version History

- **v1.0.0** (2025-12-17) - Initial skill extraction from gojo.agent.md
  - Extracted tier validation section (Lines 1303-1510)
  - Added skill header and metadata
  - Integrated with Domain Zero Protocol v8.8.0

---

**End of Skill: gojo-tier-validation**
