# Migration Guide: v8.7.0 → v8.8.0
# Domain Zero Protocol - Breaking Changes & Migration Instructions

**From Version**: 8.7.0
**To Version**: 8.8.0
**Migration Date**: 2025-12-06
**Estimated Migration Time**: 15-30 minutes
**Difficulty**: Medium (breaking behavioral changes, backward compatibility available)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Breaking Changes](#breaking-changes)
3. [New Features](#new-features)
4. [Migration Paths](#migration-paths)
5. [Step-by-Step Migration](#step-by-step-migration)
6. [Testing & Verification](#testing--verification)
7. [Rollback Instructions](#rollback-instructions)
8. [FAQ](#faq)

---

## Overview

### What Changed in v8.8.0?

DZP v8.8.0 introduces **Tier Validation System** with automatic enforcement of tier-specific workflow requirements. This is a **breaking behavioral change** that affects how agents enforce test-first development, security reviews, and tier compliance.

**Key Changes**:
- ✅ **Tier validation now enforced** - Agents actively enforce tier requirements (test-first, security reviews, etc.)
- ✅ **New configuration file** - `protocol/tier-defaults.yaml` defines tier profiles
- ✅ **All 9 agents updated** - Tier-aware behavior in yuuji, megumi, gojo, nobara, todo, maki, panda, inumaki, sukuna
- ✅ **Working directory verification** - New safety check ensures scripts run from correct directory
- ⚠️ **Backward compatibility available** - Optional grace period and legacy mode for gradual migration

### Why This Change?

**Problem Solved**: In v8.7.0 and earlier, tier system was **advisory only** - agents would *suggest* tier-appropriate workflows but wouldn't *enforce* them. This led to:
- Tier 2/3 features shipping without tests
- Security reviews being skipped
- Inconsistent workflow rigor

**Solution**: v8.8.0 makes tier requirements **mandatory** with active enforcement, but provides migration options for existing users.

---

## Breaking Changes

### 1. Tier Enforcement is Now Active (BREAKING)

**Before (v8.7.0)**:
- Yuuji would *recommend* writing tests first for Tier 2/3
- Yuuji would *suggest* security review but wouldn't block if skipped
- Users could ignore tier recommendations

**After (v8.8.0)**:
- Yuuji **BLOCKS** implementation if tests not written first (Tier 2/3)
- Yuuji **REQUIRES** security review handoff for Tier 2/3 features
- Gojo **MONITORS** tier compliance and alerts on violations

**Impact**:
- **HIGH** - If you've been skipping tests or security reviews, you'll now be blocked
- **MEDIUM** - If you've been following tier guidelines, minimal impact

**Migration Required**: Yes - review workflow to ensure tier compliance

---

### 2. Agent Behavioral Contracts Modified (BREAKING)

**Before (v8.7.0)**:
- Agents had tier-aware *guidance* but no enforcement logic
- Tier system was documented in CLAUDE.md only

**After (v8.8.0)**:
- All 9 agents have tier validation sections in their .agent.md files
- Tier requirements defined in `protocol/tier-defaults.yaml`
- Agents actively check tier compliance before proceeding

**Impact**:
- **MEDIUM** - Agent invocation patterns unchanged, but behavior is stricter
- **LOW** - If using agents correctly, compliance should be automatic

**Migration Required**: Yes - understand new tier enforcement behavior

---

### 3. New Required Configuration File (BREAKING)

**Before (v8.7.0)**:
- No `protocol/tier-defaults.yaml` file

**After (v8.8.0)**:
- **REQUIRED**: `protocol/tier-defaults.yaml` must exist
- Defines tier profiles (Rapid/Standard/Critical)
- Agents read tier requirements from this file

**Impact**:
- **LOW** - File created automatically during migration
- **NONE** - If file exists, no action needed

**Migration Required**: Yes - ensure file exists (automated in migration script)

---

### 4. Backward Compatibility Flag Added (NON-BREAKING with opt-in)

**New in v8.8.0**:
- `protocol.config.yaml` has new `tiers.backward_compatibility` section
- Optional grace period (30 days default)
- Optional legacy mode (disable tier validation entirely)

**Impact**:
- **NONE** - Defaults to strict enforcement (recommended)
- **OPTIONAL** - Users can enable grace period or legacy mode

**Migration Required**: No - but understanding options is recommended

---

## New Features

### Feature 1: Tier Validation System

**What it does**:
- Enforces tier-specific workflow requirements
- Validates tier compliance before allowing operations
- Tracks tier usage statistics (Component 2 - Week 2)

**Tier Profiles**:

| Tier | Tests Required | Security Review | Coverage | Use Cases |
|------|----------------|-----------------|----------|-----------|
| **Tier 1 (Rapid)** | No | No | N/A | Prototypes, experiments |
| **Tier 2 (Standard)** [DEFAULT] | Yes (test-first) | Yes (standard) | 80% | Production features |
| **Tier 3 (Critical)** | Yes (test-first + integration + E2E) | Yes (enhanced + multi-model) | 95% | Auth, payments, sensitive data |

**How to use**:
```bash
# Tier 1 (Rapid) - Prototypes only
"Read yuuji.agent.md --tier rapid and create file renaming script"

# Tier 2 (Standard) - Default (no flag needed)
"Read yuuji.agent.md and implement user profile feature"

# Tier 3 (Critical) - Sensitive features
"Read yuuji.agent.md --tier critical and implement payment processing"
```

---

### Feature 2: Working Directory Verification

**What it does**:
- New utility `scripts/verify_working_directory.py`
- Ensures scripts run from correct project root
- Prevents accidental operations in wrong directories

**How to use**:
```python
# In scripts (future integration)
from verify_working_directory import ensure_project_root

if __name__ == '__main__':
    ensure_project_root()  # Exits if not in project root
    # ... rest of script
```

**Current status**: Utility created, integration with existing scripts in future phase

---

### Feature 3: Tier-Aware Agent Behaviors

**What changed**:
All 9 agents now have tier-specific behaviors:

- **Yuuji** - Enforces test-first (Tier 2/3), performance benchmarks (Tier 3)
- **Megumi** - Standard vs enhanced security review (Tier 2 vs Tier 3)
- **Gojo** - Monitors compliance, tracks statistics, Trigger 19 analytics
- **Nobara** - WCAG AA vs AAA compliance (Tier 2 vs Tier 3)
- **Todo** - Encryption + audit logging for Tier 3 data
- **Maki** - Performance benchmarks REQUIRED for Tier 3
- **Panda** - CI/CD gates + staging deployment for Tier 3
- **Inumaki** - Rate limiting + request signing for Tier 3 APIs
- **Sukuna** - Preserves tier logic during system updates

---

## Migration Paths

### Path A: Full Migration (Recommended)

**Who should use this**:
- Teams already following tier guidelines
- New projects starting with v8.8.0
- Users who want strict tier enforcement

**What you get**:
- ✅ Strict tier enforcement (immediate)
- ✅ Zero tolerance for tier violations
- ✅ Full tier validation benefits

**Downside**:
- ⚠️ May require fixing existing workflows if not tier-compliant

**Configuration**:
```yaml
# protocol.config.yaml
tiers:
  backward_compatibility:
    allow_tier_bypass: false           # Strict enforcement
    legacy_mode_enabled: false         # Use tier system
```

---

### Path B: Gradual Migration (Grace Period)

**Who should use this**:
- Teams transitioning from v8.7.0
- Projects with existing non-compliant workflows
- Users who need time to adapt

**What you get**:
- ✅ Tier violations generate WARNINGS (not blocks)
- ✅ 30-day grace period to fix workflows
- ✅ Violations logged for tracking

**Downside**:
- ⚠️ Less strict enforcement during grace period
- ⚠️ Must eventually migrate to strict enforcement

**Configuration**:
```yaml
# protocol.config.yaml
tiers:
  backward_compatibility:
    allow_tier_bypass: false                        # Recommended
    migration_grace_period_days: 30                 # 30-day grace period
    migration_start_date: "2025-12-06"              # Today's date
    grace_period_behavior:
      tier_violations_as_warnings: true             # Warn instead of block
      log_violations: true                          # Track violations
      migration_report_on_trigger19: true           # Include in reports
```

**Timeline**:
- **Week 1-2**: Fix Tier 3 violations (critical features)
- **Week 3-4**: Fix Tier 2 violations (standard features)
- **After 30 days**: Set `tier_violations_as_warnings: false` for strict enforcement

---

### Path C: Legacy Mode (NOT Recommended)

**Who should use this**:
- **ONLY for temporary emergency rollback**
- Projects that cannot migrate immediately due to external constraints

**What you get**:
- ✅ Pre-v8.8.0 behavior (no tier enforcement)
- ✅ Immediate compatibility with existing workflows

**Downside**:
- ❌ **Loses all tier validation benefits**
- ❌ **NOT recommended for production use**
- ❌ **May be removed in future versions**

**Configuration**:
```yaml
# protocol.config.yaml
tiers:
  backward_compatibility:
    allow_tier_bypass: false           # Ignored in legacy mode
    legacy_mode_enabled: true          # ⚠️ DISABLE tier system (NOT recommended)
```

**Warning**: Legacy mode is provided for emergency rollback only. Plan to migrate to Path A or B as soon as possible.

---

## Step-by-Step Migration

### Prerequisites

- [ ] Domain Zero Protocol v8.7.0 currently installed
- [ ] Git repository with clean working directory
- [ ] Backup/snapshot created (recommended)

### Step 1: Backup Your Project

**Create pre-migration snapshot** (if snapshot system available):
```bash
python .protocol-state/create-snapshot.py --tier 3 --trigger manual --description "Pre-v8.8.0 migration snapshot"
```

**Or create manual backup**:
```bash
# Create backup directory
mkdir -p backups/pre-v8.8.0-migration

# Backup protocol files
cp -r protocol/ backups/pre-v8.8.0-migration/protocol/
cp protocol.config.yaml backups/pre-v8.8.0-migration/
cp -r .protocol-state/ backups/pre-v8.8.0-migration/.protocol-state/
```

### Step 2: Update Protocol Files

**Option A: Manual Update** (download from GitHub)
1. Download v8.8.0 release from canonical repository
2. Replace `protocol/` directory with new version
3. Replace `protocol.config.yaml` with new version (merge your custom settings)
4. Copy new files:
   - `protocol/tier-defaults.yaml` (NEW)
   - `scripts/verify_working_directory.py` (NEW)

**Option B: Git Update** (if using canonical repository)
```bash
git fetch origin
git checkout v8.8.0
git merge v8.8.0  # Resolve conflicts if any
```

### Step 3: Verify New Files Exist

```bash
# Check tier-defaults.yaml exists
ls -l protocol/tier-defaults.yaml

# Check verify_working_directory.py exists
ls -l scripts/verify_working_directory.py

# Verify all 9 agent files updated
grep -l "TIER VALIDATION" protocol/*.agent.md | wc -l
# Should output: 9 (all agents have tier validation)
```

### Step 4: Choose Migration Path

**Decision Matrix**:

| If you... | Choose... |
|-----------|-----------|
| Already follow tier guidelines strictly | **Path A (Full Migration)** |
| Need time to adapt workflows | **Path B (Gradual Migration)** |
| Cannot migrate immediately | **Path C (Legacy Mode)** ⚠️ |

**Update `protocol.config.yaml`** with your chosen path (see configurations in [Migration Paths](#migration-paths) section above)

### Step 5: Test Tier Validation

**Test Tier 1 (Rapid)**:
```
"Read yuuji.agent.md --tier rapid and create a simple Hello World script"

Expected: Yuuji skips tests, no security review
```

**Test Tier 2 (Standard)**:
```
"Read yuuji.agent.md and implement a basic user profile feature"

Expected: Yuuji requires tests first, prompts for security review
```

**Test Tier 3 (Critical)**:
```
"Read yuuji.agent.md --tier critical and implement password reset"

Expected: Yuuji requires tests + integration tests + E2E tests + benchmarks
```

### Step 6: Verify Working Directory Utility

```bash
python scripts/verify_working_directory.py

# Expected output:
# [OK] Working directory verified: [your project path]
# [OK] Verification PASSED
```

### Step 7: Review Tier Usage

**Check tier statistics**:
```bash
# View current tier usage
cat .protocol-state/project-state.json | grep -A 10 "tier_usage_statistics"

# Expected: All zeros initially (statistics tracking in Component 2 - Week 2)
```

### Step 8: Update Documentation (If Custom)

If you have custom documentation referencing tier system:
- Update references to tier behavior (now enforced, not advisory)
- Add note about backward compatibility options
- Reference `protocol/tier-defaults.yaml` for tier requirements

---

## Testing & Verification

### Verification Checklist

Use the comprehensive verification checklist:
```bash
cat .protocol-state/system-update-framework/tier-validation-verification-checklist.md
```

**Key Tests**:
- [ ] tier-defaults.yaml valid YAML
- [ ] All 9 agents have tier validation sections
- [ ] Backward compatibility flag configured
- [ ] verify_working_directory.py works
- [ ] Tier 1/2/3 workflows behave as expected

### Automated Verification (Optional)

```bash
# Run YAML validation
python -c "import yaml; yaml.safe_load(open('protocol/tier-defaults.yaml'))"

# Verify working directory utility
python scripts/verify_working_directory.py

# Check agent files
grep -l "TIER VALIDATION" protocol/*.agent.md
```

---

## Rollback Instructions

### If Migration Fails

**Option 1: Restore from Snapshot**
```bash
python .protocol-state/restore-snapshot.py [snapshot-id]
```

**Option 2: Manual Rollback**
```bash
# Restore from backup
cp -r backups/pre-v8.8.0-migration/protocol/ protocol/
cp backups/pre-v8.8.0-migration/protocol.config.yaml .
cp -r backups/pre-v8.8.0-migration/.protocol-state/ .protocol-state/

# Remove v8.8.0 files
rm protocol/tier-defaults.yaml
rm scripts/verify_working_directory.py
```

**Option 3: Enable Legacy Mode (Temporary)**
```yaml
# protocol.config.yaml
tiers:
  backward_compatibility:
    legacy_mode_enabled: true  # Revert to v8.7.0 behavior
```

---

## FAQ

### Q1: Do I need to migrate immediately?

**A**: No. v8.8.0 provides backward compatibility options:
- **Grace period mode**: 30 days to adapt (warnings instead of blocks)
- **Legacy mode**: Temporarily disable tier validation (not recommended)

**Recommendation**: Use grace period mode for gradual migration, plan to complete within 30 days.

---

### Q2: Will my existing Tier 1/2/3 usage still work?

**A**: Yes, with one change:
- **Before**: Tier requirements were *suggested* (not enforced)
- **After**: Tier requirements are *enforced* (agents block non-compliance)

If you've been following tier guidelines, no workflow changes needed.

---

### Q3: What if I've been skipping tests or security reviews?

**A**: You have 2 options:
1. **Fix workflows** - Start writing tests first, complete security reviews (recommended)
2. **Use grace period** - 30 days to adapt with warnings instead of blocks

**NOT recommended**: Legacy mode (disables all tier validation)

---

### Q4: Can I customize tier requirements?

**A**: Yes! Edit `protocol/tier-defaults.yaml`:
```yaml
tier_2_standard:
  requirements:
    tests: true
    security_review: true
    code_coverage: 80  # Change to your requirement (e.g., 70)
```

**Warning**: Lowering requirements reduces safety guarantees. Review carefully.

---

### Q5: What happens after the 30-day grace period?

**A**: You must choose:
1. **Strict enforcement** - Set `tier_violations_as_warnings: false` (recommended)
2. **Extend grace period** - Increase `migration_grace_period_days` (not recommended)
3. **Legacy mode** - Disable tier validation entirely (NOT recommended)

**Best practice**: Fix tier violations during grace period, then enable strict enforcement.

---

### Q6: How do I know which tier to use?

**Decision Tree**:
```
Is this code going to production?
  NO → Tier 1 (Rapid)
  YES → Does it handle sensitive data or operations?
    YES (auth/payments/medical/legal) → Tier 3 (Critical)
    NO → Tier 2 (Standard)
```

**See**: `protocol/TIER-SELECTION-GUIDE.md` for complete guidance

---

### Q7: Will tier statistics work immediately?

**A**: Tier statistics **tracking** is implemented in Component 2 (Week 2).

**Current (v8.8.0 Phase 4 Component 1)**:
- ✅ Tier validation enforced
- ⏳ Statistics tracking (manual only, auto-update in Component 2)

**Future (Component 2 - Week 2)**:
- ✅ Auto-increment tier counters on task completion
- ✅ Trigger 19 tier analytics reports

---

### Q8: Can I disable tier validation for specific features?

**A**: Yes, with user bypass:
```
User: "Skip tier validation for this prototype"

Agent: "Acknowledged. Bypassing Tier 2 requirements for this feature.
        Bypass logged to project-state.json."
```

**Warning**: Bypasses are tracked. Excessive bypasses trigger warnings in Trigger 19 reports.

---

### Q9: What if I'm using a forked/custom DZP version?

**A**: Manual merge required:
1. Review changes in v8.8.0
2. Merge `protocol/tier-defaults.yaml`
3. Merge tier validation sections into your custom agent files
4. Merge backward compatibility flag into your `protocol.config.yaml`
5. Test thoroughly before deployment

**Recommendation**: Consult v8.8.0 changelist for detailed file-by-file changes.

---

### Q10: How do I get help with migration issues?

**Resources**:
1. **Verification Checklist**: `.protocol-state/system-update-framework/tier-validation-verification-checklist.md`
2. **Tier Defaults**: `protocol/tier-defaults.yaml` (inline comments explain all options)
3. **Canonical Repo**: https://github.com/DewyHRite/Domain-Zero-Protocol (issues, discussions)
4. **Rollback Available**: Snapshot 848ccedd or manual backup

**Emergency Rollback**: Enable legacy mode temporarily while investigating issues.

---

## Summary

**v8.8.0 Migration Checklist**:
- [ ] Backup created (snapshot or manual)
- [ ] New files added (tier-defaults.yaml, verify_working_directory.py)
- [ ] All 9 agent files updated
- [ ] Backward compatibility configured (Path A/B/C)
- [ ] Tier validation tested (Tier 1/2/3)
- [ ] Working directory utility tested
- [ ] Documentation updated (if custom)
- [ ] Rollback plan documented

**Migration Complete**: You're now using DZP v8.8.0 with Tier Validation System! 🎉

**Next Steps**:
- Monitor tier compliance during grace period (if using Path B)
- Plan transition to strict enforcement after 30 days
- Review tier usage in Trigger 19 reports
- Update team workflows to align with tier requirements

---

**Document Version**: 1.0.0
**Created**: 2025-12-06
**Last Updated**: 2025-12-06
**Maintained By**: Domain Zero Protocol Team
