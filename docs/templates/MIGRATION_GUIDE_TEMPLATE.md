# Migration Guide Template

**Purpose:** Template for creating migration guides between Domain Zero Protocol versions

**Instructions:** Copy this template when releasing a new major version and fill in the bracketed sections.

---

# Migration Guide: v[OLD_VERSION] → v[NEW_VERSION]

**Release Date:** [RELEASE_DATE]
**Migration Difficulty:** [Easy / Moderate / Complex]
**Estimated Time:** [TIME_ESTIMATE]

---

## Overview

### What Changed

[Brief summary of major changes in new version]

**Breaking Changes:**
- [List all breaking changes]
- [Include impact on existing projects]

**New Features:**
- [List new features that may require action]
- [Include opt-in vs automatic features]

**Deprecations:**
- [List deprecated features]
- [Include timeline for removal]

---

## Should You Migrate?

### Required Migration (Breaking Changes)

Migrate **immediately** if:
- [ ] [Condition 1 requiring migration]
- [ ] [Condition 2 requiring migration]
- [ ] [Condition 3 requiring migration]

### Optional Migration (New Features)

Migrate **when convenient** if:
- [ ] You want [new feature 1]
- [ ] You need [new feature 2]
- [ ] You're starting a new project

### Can Skip Migration

Stay on v[OLD_VERSION] if:
- [ ] No breaking changes affect you
- [ ] Current version meets your needs
- [ ] Migration effort outweighs benefits

**Support Timeline:**
- **v[NEW_VERSION]:** Fully supported
- **v[OLD_VERSION]:** Supported until [END_OF_LIFE_DATE]
- **Older versions:** End of life

---

## Pre-Migration Checklist

### Before You Start

- [ ] **Backup Everything**
  ```bash
  git commit -m "Backup before migrating to v[NEW_VERSION]"
  git tag pre-migration-v[OLD_VERSION]
  ```

- [ ] **Read Release Notes**
  - [CHANGELOG.md](CHANGELOG.md)
  - [VERSION.md](VERSION.md)
  - This migration guide (you're reading it!)

- [ ] **Check Compatibility**
  - AI assistant versions supported
  - Dependencies updated
  - Custom integrations still work

- [ ] **Plan Downtime** (if applicable)
  - Notify team
  - Schedule migration window
  - Prepare rollback plan

- [ ] **Test in Non-Production First**
  - Create test branch
  - Migrate test environment
  - Validate functionality

---

## Step-by-Step Migration

### Step 1: Update Protocol Files

**Time:** [ESTIMATE]

1. **Download v[NEW_VERSION]:**
   ```bash
   git clone https://github.com/DewyHRite/Domain-Zero-Protocol
   cd Domain-Zero-Protocol
   git checkout v[NEW_VERSION]
   ```

2. **Backup Current Protocol:**
   ```bash
   cd your-project
   cp -r protocol protocol.backup.v[OLD_VERSION]
   cp protocol.config.yaml protocol.config.yaml.backup
   ```

3. **Copy New Protocol Files:**
   ```bash
   # Copy core protocol files
   cp -r ~/Domain-Zero-Protocol/protocol/* ./protocol/

   # DO NOT overwrite protocol.config.yaml yet
   ```

4. **Verify File Structure:**
   ```bash
   # Check for new files
   ls protocol/
   # Expected: CLAUDE.md, YUUJI.md, MEGUMI.md, GOJO.md, NOBARA.md, [NEW_FILES]
   ```

---

### Step 2: Update Configuration

**Time:** [ESTIMATE]

1. **Compare Configuration Files:**
   ```bash
   diff protocol.config.yaml.backup ~/Domain-Zero-Protocol/protocol.config.yaml
   ```

2. **Merge New Settings:**
   - Open both files side-by-side
   - Add new sections from v[NEW_VERSION]
   - Keep your customized values
   - Update version number to v[NEW_VERSION]

3. **Key Changes in protocol.config.yaml:**

   **Added:**
   ```yaml
   [new_section]:
     [new_setting]: [default_value]  # [Explanation]
   ```

   **Modified:**
   ```yaml
   [existing_section]:
     [renamed_setting]: [new_format]  # Previously: [old_setting]
   ```

   **Removed:**
   ```yaml
   # [removed_section] - No longer needed, removed because [reason]
   ```

4. **Validation:**
   ```bash
   # Run verification script
   ./scripts/verify-protocol.sh  # Unix/Linux/macOS
   .\scripts\verify-protocol.ps1  # Windows

   # Should show no errors
   ```

---

### Step 3: Update State Files

**Time:** [ESTIMATE]

1. **Backup Current State:**
   ```bash
   cp -r .protocol-state .protocol-state.backup.v[OLD_VERSION]
   ```

2. **Migrate project-state.json:**
   - Add new required fields:
     ```json
     {
       "[new_field]": "[value]"
     }
     ```
   - Remove deprecated fields:
     ```json
     // DELETE: "[old_field]": "..."
     ```

3. **Update State Templates:**
   ```bash
   # Copy new templates (if changed)
   cp ~/Domain-Zero-Protocol/.protocol-state/*.md .protocol-state/
   ```

4. **Preserve Your Data:**
   - Restore your dev-notes.md
   - Restore your security-review.md
   - Restore your trigger-19.md (if exists)

---

### Step 4: Update Scripts

**Time:** [ESTIMATE]

1. **Update Verification Scripts:**
   ```bash
   cp ~/Domain-Zero-Protocol/scripts/verify-protocol.sh ./scripts/
   cp ~/Domain-Zero-Protocol/scripts/verify-protocol.ps1 ./scripts/
   ```

2. **Update Integration Scripts:**
   ```bash
   cp ~/Domain-Zero-Protocol/scripts/update-instructions.sh ./scripts/
   cp ~/Domain-Zero-Protocol/scripts/update-instructions.ps1 ./scripts/
   ```

3. **Test Scripts:**
   ```bash
   # Unix/Linux/macOS
   chmod +x ./scripts/*.sh
   ./scripts/verify-protocol.sh

   # Windows
   .\scripts\verify-protocol.ps1
   ```

---

### Step 5: Handle Breaking Changes

**Time:** [ESTIMATE]

#### Breaking Change 1: [NAME]

**What Changed:**
[Explanation of breaking change]

**Impact:**
[Who is affected and how]

**Migration Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Before:**
```yaml
[old_syntax]
```

**After:**
```yaml
[new_syntax]
```

**Validation:**
```bash
[command_to_verify_change]
```

---

#### Breaking Change 2: [NAME]

[Repeat structure for each breaking change]

---

### Step 6: Adopt New Features (Optional)

**Time:** [ESTIMATE]

#### New Feature 1: [NAME]

**Description:**
[What this feature does]

**Benefits:**
- [Benefit 1]
- [Benefit 2]

**Setup:**
1. [Step 1]
2. [Step 2]

**Example:**
```[language]
[code_example]
```

---

#### New Feature 2: [NAME]

[Repeat structure for each new feature]

---

### Step 7: Update AI Assistant Memory

**Time:** 5-10 minutes

1. **Claude (claude.ai or API):**
   ```
   Update memory: Domain Zero Protocol updated to v[NEW_VERSION]

   I now use Domain Zero Protocol v[NEW_VERSION].
   Key changes:
   - [Change 1]
   - [Change 2]
   - [Change 3]

   Protocol files: protocol/CLAUDE.md (v[NEW_VERSION])
   Canonical source: https://github.com/DewyHRite/Domain-Zero-Protocol
   ```

2. **ChatGPT Custom Instructions:**
   - Update version number to v[NEW_VERSION]
   - Add notes about breaking changes

3. **GitHub Copilot:**
   - Update `.github/copilot-instructions.md`
   - Change version references to v[NEW_VERSION]

---

### Step 8: Test Migration

**Time:** [ESTIMATE]

1. **Run Protocol Verification:**
   ```bash
   ./scripts/verify-protocol.sh
   ```
   Expected: All checks pass ✅

2. **Test Tier 1 Workflow:**
   - Invoke Yuuji for simple feature
   - Verify TDD process works
   - Check output format

3. **Test Tier 2 Workflow:**
   - Invoke Yuuji with security review
   - Verify Megumi handoff works
   - Check @security-review tag

4. **Test Tier 3 Workflow (if applicable):**
   - Invoke full critical workflow
   - Verify enhanced requirements
   - Test multi-model review (if configured)

5. **Test Gojo Integration:**
   ```
   Read protocol/GOJO.md
   ```
   - Choose option 1: Status Report
   - Verify project state loaded correctly
   - Check Trigger 19 if available

---

## Post-Migration Checklist

### Verification

- [ ] **Protocol verification passes**
  ```bash
  ./scripts/verify-protocol.sh  # All checks pass
  ```

- [ ] **Configuration valid**
  ```bash
  grep "version:" protocol.config.yaml
  # Should show: version: "v[NEW_VERSION]"
  ```

- [ ] **State files intact**
  ```bash
  ls .protocol-state/
  # Verify: project-state.json, dev-notes.md, security-review.md
  ```

- [ ] **Scripts executable**
  ```bash
  ./scripts/verify-protocol.sh  # Works
  ```

- [ ] **AI assistant updated**
  - Claude memory shows v[NEW_VERSION]
  - ChatGPT custom instructions updated
  - Copilot instructions updated

### Functional Testing

- [ ] **Tier 1 workflow tested** - Rapid prototyping works
- [ ] **Tier 2 workflow tested** - TDD + security review works
- [ ] **Tier 3 workflow tested** - Critical workflow works (if applicable)
- [ ] **Gojo initialization tested** - Project state loads correctly
- [ ] **Agent handoffs work** - Yuuji → Megumi transitions

### Cleanup

- [ ] **Remove backups** (after confirming everything works)
  ```bash
  rm -rf protocol.backup.v[OLD_VERSION]
  rm protocol.config.yaml.backup
  rm -rf .protocol-state.backup.v[OLD_VERSION]
  ```

- [ ] **Commit migration**
  ```bash
  git add .
  git commit -m "Migrate to Domain Zero Protocol v[NEW_VERSION]"
  git tag migration-v[NEW_VERSION]-complete
  ```

- [ ] **Document migration**
  - Update dev-notes.md with migration date
  - Record any customizations made
  - Note any issues encountered

---

## Rollback Plan

If migration fails or causes issues:

### Quick Rollback

```bash
# Restore from backup
git checkout pre-migration-v[OLD_VERSION]

# Or manual restore
cp -r protocol.backup.v[OLD_VERSION]/* ./protocol/
cp protocol.config.yaml.backup protocol.config.yaml
cp -r .protocol-state.backup.v[OLD_VERSION]/* ./.protocol-state/

# Verify rollback
./scripts/verify-protocol.sh
```

### Partial Rollback

If only specific component broken:

**Protocol files only:**
```bash
cp -r protocol.backup.v[OLD_VERSION]/* ./protocol/
```

**Configuration only:**
```bash
cp protocol.config.yaml.backup protocol.config.yaml
```

**Scripts only:**
```bash
cp -r scripts.backup.v[OLD_VERSION]/* ./scripts/
```

---

## Common Migration Issues

### Issue 1: Verification Script Fails

**Symptoms:**
```
[FAIL] [error_message]
```

**Causes:**
- [Cause 1]
- [Cause 2]

**Solutions:**
1. [Solution 1]
2. [Solution 2]

---

### Issue 2: AI Assistant Doesn't Recognize New Version

**Symptoms:**
- Agent still thinks it's v[OLD_VERSION]
- Agent doesn't recognize new features

**Solution:**
1. Re-read protocol: `"Read protocol/CLAUDE.md"`
2. Update AI memory with v[NEW_VERSION]
3. Start new conversation session

---

### Issue 3: [COMMON_ISSUE_3]

[Repeat structure for each common issue]

---

## Getting Help

### Documentation
- [README.md](README.md) - Main documentation
- [CHANGELOG.md](CHANGELOG.md) - Complete version history
- [FAQ.md](FAQ.md) - Frequently asked questions
- [SECURITY.md](SECURITY.md) - Security reporting

### Community Support
- **GitHub Issues:** https://github.com/DewyHRite/Domain-Zero-Protocol/issues
- Tag with `migration` and `v[NEW_VERSION]`
- Include error messages and logs

### Direct Support
- **Email:** dwaynewright1@outlook.com (critical migration issues only)
- **GitHub Discussions:** Community migration help

---

## Version Compatibility Matrix

| Your Version | Target Version | Difficulty | Direct Migration? |
|--------------|----------------|------------|-------------------|
| v[OLD_MINOR] | v[NEW_VERSION] | [Easy/Moderate/Complex] | ✅ Yes |
| v[OLDER_MINOR] | v[NEW_VERSION] | [Easy/Moderate/Complex] | ⚠️ Via v[OLD_MINOR] recommended |
| v[OLDEST_MINOR] | v[NEW_VERSION] | Complex | ❌ Multi-step required |

**Recommendation:** Migrate one major version at a time for complex upgrades.

---

## Success Stories

> "Migrated from v[OLD_VERSION] to v[NEW_VERSION] in 45 minutes. [New feature] is a game-changer!"
> — [Anonymous User]

> "Breaking change [X] was scary but migration guide made it painless."
> — [Anonymous User]

[Add real migration feedback when available]

---

## Changelog Reference

Full changes in v[NEW_VERSION]:

```
[Include full CHANGELOG entry for new version]
```

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

---

## Credits

**Migration Guide Prepared By:** [AUTHOR_NAME]
**Release Manager:** [RELEASE_MANAGER]
**Contributors:** [CONTRIBUTOR_LIST]

---

**Version:** v[NEW_VERSION]
**Last Updated:** [DATE]
**Canonical Source:** https://github.com/DewyHRite/Domain-Zero-Protocol

---

## Template Usage Notes

**For Future Release Managers:**

1. **Copy this template** when creating new major version (vX.0.0)
2. **Rename file** to `MIGRATION_GUIDE_v[OLD]_to_v[NEW].md`
3. **Fill in all bracketed [SECTIONS]**
4. **Test migration** yourself before publishing guide
5. **Include in release** package alongside new version
6. **Link from CHANGELOG.md** and README.md

**Example:**
- v6.x.x → v7.0.0: Create `MIGRATION_GUIDE_v6_to_v7.md`
- v7.x.x → v8.0.0: Create `MIGRATION_GUIDE_v7_to_v8.md`

**Keep template updated** as migration patterns evolve.
