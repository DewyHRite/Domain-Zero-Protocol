# Domain Zero Protocol - Git Workflow & Branching Strategy

**Version:** 1.0.0
**Date:** November 7, 2025
**Status:** Official Workflow

---

## Official Versioning & Release Workflow

### Core Principle

**Every version update MUST be pushed to a new branch and merged via Pull Request.**

This ensures:
- ✅ Review opportunity before merging to `main`
- ✅ CI/CD validation runs on PR
- ✅ Clean merge history
- ✅ Rollback capability
- ✅ Audit trail for all version changes

---

## Workflow Steps

### Step 1: Create Version Update

Use the system-update.py script to update version across all files:

```bash
# For patch updates (6.2.7 → 6.2.8)
python scripts/system-update.py patch

# For minor updates (6.2.7 → 6.3.0)
python scripts/system-update.py minor

# For major updates (6.2.7 → 7.0.0)
python scripts/system-update.py major
```

**What this does:**
1. Updates version in all protocol files
2. Updates CHANGELOG.md with template
3. Prompts you to edit CHANGELOG with actual changes
4. Updates VERSION.md
5. Creates Git commit with proper message
6. Creates annotated Git tag (e.g., `v6.2.8`)

---

### Step 2: Push to Feature Branch

**NEVER push directly to `main`.** Always push to a version-specific branch:

```bash
# Branch naming convention: version-v{MAJOR}.{MINOR}.{PATCH}
git push origin main:version-v6.2.8

# Or if you're on a different branch:
git push origin HEAD:version-v6.2.8
```

**Branch Naming Convention:**
- Patch updates: `version-v6.2.8`, `version-v6.2.9`
- Minor updates: `version-v6.3.0`, `version-v6.4.0`
- Major updates: `version-v7.0.0`, `version-v8.0.0`

---

### Step 3: Push Tags

Push the version tag to remote:

```bash
# Push specific tag
git push origin v6.2.8

# Or push all tags
git push origin --tags
```

---

### Step 4: Create Pull Request

Create a PR from the version branch to `main`:

```bash
# Using GitHub CLI (recommended)
gh pr create \
  --base main \
  --head version-v6.2.8 \
  --title "Release v6.2.8: [Brief Description]" \
  --body "$(cat <<'EOF'
## Release v6.2.8

### Changes
- [List key changes from CHANGELOG.md]

### Checklist
- [x] Version updated across all files
- [x] CHANGELOG.md updated
- [x] VERSION.md updated with release notes
- [x] Git tag created (v6.2.8)
- [x] All tests passing (if applicable)
- [x] Documentation updated

### Breaking Changes
[If any, list here. Otherwise: None]

### Migration Notes
[If required, list here. Otherwise: Not required]

---

🤖 Generated with system-update.py v2.0
EOF
)"
```

**Or manually on GitHub:**
1. Go to: https://github.com/DewyHRite/Domain-Zero-Protocol/pulls
2. Click "New Pull Request"
3. Select `base: main` ← `compare: version-v6.2.8`
4. Fill in title and description
5. Click "Create Pull Request"

---

### Step 5: Review & Merge

**Manual Review Steps:**
1. Review the PR diff on GitHub
2. Verify version consistency across files:
   - `protocol.config.yaml` → `versioning.protocol_version`
   - `protocol.config.yaml` → `canonical_repository.version`
   - `VERSION.md` → header
   - `CHANGELOG.md` → latest entry
3. Check that CHANGELOG entry is complete and accurate
4. Verify Git tag matches version
5. Run verification script (optional):
   ```bash
   ./scripts/verify-protocol.sh
   ```

**Merge PR:**
1. Click "Merge Pull Request" on GitHub
2. Choose merge method:
   - **Squash and merge**: For multiple WIP commits (recommended for clean history)
   - **Create a merge commit**: For preserving commit history (use for major releases)
   - **Rebase and merge**: For linear history (use if single commit)
3. Confirm merge
4. Delete the version branch (GitHub will prompt)

---

### Step 6: Create GitHub Release

After merging, create a GitHub Release from the tag:

```bash
# Using GitHub CLI (recommended)
gh release create v6.2.8 \
  --title "Domain Zero Protocol v6.2.8" \
  --notes "$(cat VERSION.md | sed -n '/## Release Summary/,/## Upgrade Notes/p')" \
  --verify-tag

# Or manually on GitHub:
# 1. Go to: https://github.com/DewyHRite/Domain-Zero-Protocol/releases
# 2. Click "Draft a new release"
# 3. Select tag: v6.2.8
# 4. Title: Domain Zero Protocol v6.2.8
# 5. Description: Copy from VERSION.md
# 6. Click "Publish release"
```

---

## Quick Reference

### Complete Version Update Workflow

```bash
# 1. Create version update
python scripts/system-update.py patch

# 2. Edit CHANGELOG.md with actual changes
# [Script will pause and wait for you to edit]

# 3. Push to version branch
git push origin main:version-v6.2.8

# 4. Push tag
git push origin v6.2.8

# 5. Create PR
gh pr create --base main --head version-v6.2.8 \
  --title "Release v6.2.8: [Description]" \
  --body "[PR description]"

# 6. Review and merge PR on GitHub

# 7. Create GitHub Release
gh release create v6.2.8 --generate-notes
```

---

## Branch Protection Rules (Recommended)

To enforce this workflow, configure branch protection on `main`:

**Settings → Branches → Branch protection rules → Add rule:**

✅ **Branch name pattern:** `main`

**Protect matching branches:**
- ✅ Require a pull request before merging
  - ✅ Require approvals: 1 (for team projects)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners (if using CODEOWNERS)
- ✅ Require status checks to pass before merging (if using CI/CD)
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ✅ Include administrators (enforce rules for everyone)

**Rules applied to everyone including administrators:**
- ✅ Restrict who can push to matching branches
  - Only allow: Pull Requests

---

## Rollback Procedure

If a version needs to be rolled back:

### Option 1: Revert via PR (Recommended)

```bash
# 1. Create revert branch
git checkout main
git pull origin main
git revert <commit-hash-of-bad-release>
git push origin HEAD:revert-v6.2.8

# 2. Create PR
gh pr create --base main --head revert-v6.2.8 \
  --title "Revert v6.2.8: [Reason]" \
  --body "Reverts version v6.2.8 due to [issue]"

# 3. Merge PR after review
```

### Option 2: Hotfix via New Version

```bash
# 1. Create hotfix (e.g., 6.2.7 → 6.2.9, skipping broken 6.2.8)
python scripts/system-update.py patch

# 2. Follow normal workflow
git push origin main:version-v6.2.9
git push origin v6.2.9

# 3. Create PR noting it fixes issues from v6.2.8
```

---

## Examples

### Example 1: Patch Release (Bug Fix)

```bash
# Starting from v6.2.7
python scripts/system-update.py patch
# → Creates v6.2.8

# Edit CHANGELOG.md:
## [6.2.8] - 2025-11-08

### Fixed
- Fix verification script encoding issue on Windows
- Correct typo in GOJO.md header

git push origin main:version-v6.2.8
git push origin v6.2.8

gh pr create --base main --head version-v6.2.8 \
  --title "Release v6.2.8: Bug fixes for verification script" \
  --body "Patch release fixing Windows encoding issues"

# Review PR, merge, create release
```

### Example 2: Minor Release (New Feature)

```bash
# Starting from v6.2.8
python scripts/system-update.py minor
# → Creates v6.3.0

# Edit CHANGELOG.md:
## [6.3.0] - 2025-11-15

### Added
- New NOBARA agent workflow for design sprints
- Enhanced Trigger 19 analytics dashboard

git push origin main:version-v6.3.0
git push origin v6.3.0

gh pr create --base main --head version-v6.3.0 \
  --title "Release v6.3.0: Design sprint workflow" \
  --body "Minor release adding Nobara design sprint capabilities"

# Review PR, merge, create release
```

### Example 3: Major Release (Breaking Change)

```bash
# Starting from v6.3.0
python scripts/system-update.py major
# → Creates v7.0.0

# Edit CHANGELOG.md:
## [7.0.0] - 2025-12-01

### BREAKING CHANGES
- Complete protocol restructure
- New agent communication protocol
- Migration guide: See MIGRATION_GUIDE_v7.md

### Added
- Five-agent system (added TOGE)
- Real-time collaboration mode

git push origin main:version-v7.0.0
git push origin v7.0.0

gh pr create --base main --head version-v7.0.0 \
  --title "Release v7.0.0: Five-agent system [BREAKING]" \
  --body "Major release with breaking changes. See MIGRATION_GUIDE_v7.md"

# Review PR carefully, merge, create release with migration notes
```

---

## Common Mistakes to Avoid

❌ **DON'T:**
- Push directly to `main` branch
- Forget to push the Git tag
- Skip the Pull Request process
- Merge without reviewing version consistency
- Create releases without updating CHANGELOG

✅ **DO:**
- Always create a version-specific branch
- Always create a Pull Request
- Always review the PR diff before merging
- Always verify version consistency
- Always create a GitHub Release after merging

---

## Troubleshooting

### Issue: "Updates were rejected (non-fast-forward)"

**Solution:** You're trying to push directly to `main`. Use the version branch workflow:

```bash
# Instead of:
git push origin main  # ❌ WRONG

# Do this:
git push origin main:version-v6.2.8  # ✅ CORRECT
```

### Issue: "Tag already exists"

**Solution:** Either:
1. You already created this version (check `git tag -l`)
2. Use the next version number
3. If it's an error, delete the tag and recreate:

```bash
git tag -d v6.2.8          # Delete local tag
git push origin :v6.2.8    # Delete remote tag
# Then recreate with system-update.py
```

### Issue: "Branch protection rules prevent direct push"

**Solution:** This is working as intended! Use the PR workflow:

```bash
git push origin HEAD:version-v6.2.8  # Push to feature branch
# Then create PR on GitHub
```

---

## Version History Tracking

All versions are tracked via:
1. **Git Tags**: `v6.2.7`, `v6.2.8`, etc.
2. **CHANGELOG.md**: Human-readable change log
3. **VERSION.md**: Detailed release notes
4. **GitHub Releases**: Public release announcements

To view version history:

```bash
# List all tags
git tag -l

# Show tag details
git show v6.2.8

# Show commits between versions
git log v6.2.7..v6.2.8 --oneline

# View specific version
git checkout v6.2.8
```

---

## Integration with system-update.py

The `scripts/system-update.py` script handles:
- ✅ Version number calculation
- ✅ File updates across all protocol files
- ✅ CHANGELOG template insertion
- ✅ Git commit creation
- ✅ Git tag creation

**It does NOT handle:**
- ❌ Branch creation
- ❌ Remote pushing
- ❌ Pull Request creation
- ❌ GitHub Release creation

These steps are **intentionally manual** to ensure human review before publishing.

---

## Future Enhancements

Potential additions to workflow (not yet implemented):

1. **Automated PR creation**: Add `--create-pr` flag to system-update.py
2. **CI/CD validation**: Run tests automatically on version branches
3. **Automated changelog generation**: Use conventional commits
4. **Release notes automation**: Generate from git history
5. **Version preview**: `system-update.py --preview` shows what would change

---

**END OF GIT_WORKFLOW.md**

For questions or issues with this workflow, see:
- VERSION_MANAGEMENT_GUIDE.md - User-friendly version management guide
- SYSTEM_UPDATE_V2_IMPLEMENTATION.md - Technical implementation details
- CONTRIBUTING.md - General contribution guidelines (if exists)
