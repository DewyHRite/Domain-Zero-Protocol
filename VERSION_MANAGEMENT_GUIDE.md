# Domain Zero Protocol - Version Management Quick Reference

**Version:** 2.0
**Last Updated:** November 7, 2025
**Tool:** `system-update.py`

---

## Quick Start

### Basic Version Bump

```bash
# 1. Navigate to repository
cd "Domain Zero Protocol"  # Or your working directory

# 2. Preview the update
python system-update.py minor --preview

# 3. Apply the update
python system-update.py minor

# 4. Follow prompts to:
#    - Edit CHANGELOG.md (optional)
#    - Review changes
#    - Push to remote (y/n)
```

---

## Version Bump Types

| Command | From | To | Use When |
|---------|------|-----|----------|
| `patch` | 6.2.6 | 6.2.7 | Bug fixes, documentation updates, minor corrections (backward-compatible) |
| `minor` | 6.2.6 | 6.3.0 | New features, enhancements (backward-compatible) |
| `major` | 6.2.6 | 7.0.0 | Breaking changes, major redesigns (NOT backward-compatible) |

### Semantic Versioning Rules

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes (incompatible API changes)
- **MINOR:** New functionality (backward-compatible)
- **PATCH:** Bug fixes (backward-compatible)

**Examples:**
- Adding verification script v2.0: **PATCH** (v6.2.6 → v6.2.7)
- Adding new agent type: **MINOR** (v6.2.6 → v6.3.0)
- Redesigning protocol structure: **MAJOR** (v6.2.6 → v7.0.0)

---

## Command Reference

### Preview Changes (Recommended First)

```bash
python system-update.py patch --preview
python system-update.py minor --preview
python system-update.py major --preview
```

**What it shows:**
- Current version
- New version
- Version consistency check
- Files that would be updated
- Diffs of changes
- Git operations that would occur

### Apply Version Bump

```bash
python system-update.py patch   # Bug fixes
python system-update.py minor   # New features
python system-update.py major   # Breaking changes
```

**What it does:**
1. Validates environment (Git, files, version consistency)
2. Updates version numbers in all files
3. Inserts CHANGELOG template
4. Creates Git commit
5. Creates Git tag
6. (Optional) Pushes to remote

### Options

```bash
-h, --help       Show help message
-p, --preview    Preview mode (dry run, no changes)
```

---

## Step-by-Step Workflow

### Scenario: Releasing a Minor Version (New Feature)

**Starting state:** v6.2.6

#### Step 1: Ensure Clean Working Directory

```bash
git status

# If uncommitted changes exist:
git add .
git commit -m "Prepare for v6.3.0 release"
```

#### Step 2: Preview the Update

```bash
python system-update.py minor --preview
```

**Review the output:**
- ✓ Current version: v6.2.6
- ✓ New version: v6.3.0
- ✓ Version consistency checks passed
- ✓ Files to update: VERSION.md, protocol.config.yaml, README.md, etc.

#### Step 3: Run the Update

```bash
python system-update.py minor
```

**Follow prompts:**

1. **Continue with update?** → `y`

2. **CHANGELOG update:**
   - Option 1: Edit now (recommended)
   - Option 2: Insert template, edit later
   - Option 3: Skip (not recommended)

   **Choose 1**, then edit CHANGELOG.md:
   ```markdown
   ## [6.3.0] - 2025-11-07

   ### Added
   - New NOBARA agent for creative strategy and UX design
   - Tier transition guide for upgrading/downgrading tiers

   ### Changed
   - Enhanced protocol.config.yaml with new agent settings

   ### Performance
   - Improved agent coordination efficiency
   ```

3. **Press Enter** when done editing

4. **Review commit message** (auto-generated)

5. **Push to remote?** → `y` or `n`
   - `y`: Pushes branch + tag immediately
   - `n`: You can push manually later

#### Step 4: Verify Success

```bash
# Check commit
git log -1

# Check tag
git tag -l "v6.3.*"

# View changes
git show HEAD
```

#### Step 5: Create GitHub Release (Optional)

```bash
# Using GitHub CLI
gh release create v6.3.0 --generate-notes

# Or manually:
# https://github.com/DewyHRite/Domain-Zero-Protocol/releases/new
# Tag: v6.3.0
# Title: Domain Zero Protocol v6.3.0
# Description: Copy from CHANGELOG.md
```

---

## Troubleshooting

### Error: "Version inconsistencies detected"

**Cause:** VERSION.md or CHANGELOG.md has different version than protocol.config.yaml

**Solution:**
```bash
# 1. Check protocol.config.yaml
grep "protocol_version" protocol.config.yaml
# versioning:
#   protocol_version: "6.2.6"

# 2. Check VERSION.md
head -5 VERSION.md
# **Version:** v6.2.6

# 3. Check CHANGELOG.md
head -20 CHANGELOG.md
# ## [6.2.6] - 2025-11-07

# 4. Fix mismatches manually, then retry
```

### Error: "Not in a git repository"

**Cause:** Not inside a Git repository

**Solution:**
```bash
# Initialize if needed
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO

# Then retry
python system-update.py minor
```

### Error: "Git is not installed"

**Cause:** Git not in PATH

**Solution:**
```bash
# Windows
# Download from: https://git-scm.com/download/win
# Install and restart terminal

# macOS
brew install git

# Linux
sudo apt-get install git  # Debian/Ubuntu
sudo yum install git       # RedHat/CentOS
```

### Error: "Tag v6.3.0 already exists"

**Cause:** Tag already created (perhaps from previous run)

**Options:**
1. **Delete and recreate:**
   ```bash
   git tag -d v6.3.0
   git push origin :refs/tags/v6.3.0  # Delete from remote
   python system-update.py minor
   ```

2. **Skip to next version:**
   ```bash
   # Increment version again or use patch
   python system-update.py patch  # Creates v6.3.1 instead
   ```

### Warning: "Uncommitted changes detected"

**Cause:** Files modified but not committed

**Options:**
1. **Commit changes:**
   ```bash
   git add .
   git commit -m "Prepare for release"
   python system-update.py minor
   ```

2. **Stash changes:**
   ```bash
   git stash
   python system-update.py minor
   git stash pop  # After update completes
   ```

3. **Continue anyway:** (in preview mode, this is automatic)
   - Script will prompt: "Continue anyway? (y/n)"

### Error: "PyYAML not installed"

**Cause:** Python YAML library missing

**Solution:**
```bash
pip install pyyaml
```

---

## Advanced Usage

### Manual Rollback

If update fails or you want to undo:

```bash
# 1. Reset to previous commit
git reset --hard HEAD~1

# 2. Delete tag
git tag -d v6.3.0

# 3. If already pushed, delete from remote
git push origin :refs/tags/v6.3.0
git push origin main --force  # Use with caution!
```

### Dry Run Without Preview Flag

Preview mode is built-in, but you can also test manually:

```bash
# Create a test branch
git checkout -b test-version-bump
python system-update.py minor
git log -1
git diff HEAD~1

# If looks good, merge to main
git checkout main
git merge test-version-bump
git push origin main
git push origin v6.3.0

# Clean up
git branch -d test-version-bump
```

### Batch Operations

Update multiple repositories:

```bash
# Script to update multiple repos
for repo in repo1 repo2 repo3; do
  cd "$repo"
  python ../system-update.py patch
  cd ..
done
```

---

## File Patterns

### What Gets Updated

The script updates version references in these files:

| File | Pattern Matched | Example |
|------|----------------|---------|
| `VERSION.md` | `**Version:** vX.Y.Z` | `**Version:** v6.3.0` |
| `protocol.config.yaml` | `protocol_version: "X.Y.Z"` | `protocol_version: "6.3.0"` |
| `README.md` | `Domain Zero Protocol vX.Y.Z` | `Domain Zero Protocol v6.3.0` |
| `FAQ.md` | `Protocol Version:** vX.Y.Z` | `Protocol Version:** v6.3.0` |
| `CHANGELOG.md` | Manual template insertion | `## [6.3.0] - 2025-11-07` |
| `protocol/*.md` | `Protocol vX.Y.Z` | `Protocol v6.3.0` |

### What Doesn't Get Updated

**Safe patterns (context-aware):**
- Dependency versions: `Django v3.2.1`, `Node v18.0.0`
- Example versions: `vX.Y.Z` (placeholders)
- Historical versions: Past versions in CHANGELOG

**Binary files (skipped automatically):**
- `.png`, `.jpg`, `.pdf`, `.zip`, `.tar`, `.gz`

---

## Integration with GitHub

### Create Release from Tag

**Option 1: GitHub CLI (recommended)**
```bash
gh release create v6.3.0 \
  --title "Domain Zero Protocol v6.3.0" \
  --generate-notes
```

**Option 2: Web Interface**
1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/releases/new`
2. Choose tag: `v6.3.0`
3. Title: `Domain Zero Protocol v6.3.0`
4. Description: Copy from CHANGELOG.md
5. Click "Publish release"

### Automated Release (GitHub Actions)

Create `.github/workflows/release.yml`:

```yaml
name: Create Release
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

Now pushing a tag auto-creates a GitHub release:
```bash
python system-update.py minor
# (choose 'y' to push)
# GitHub Actions automatically creates release!
```

---

## Best Practices

### Before Every Release

1. ✅ **Run tests:**
   ```bash
   ./scripts/verify-protocol.sh --quick
   pytest tests/
   ```

2. ✅ **Update documentation:**
   - README.md with new features
   - FAQ.md with new Q&A
   - Protocol files with changes

3. ✅ **Review changes:**
   ```bash
   git status
   git diff
   ```

4. ✅ **Preview update:**
   ```bash
   python system-update.py minor --preview
   ```

### Version Bump Guidelines

**PATCH (6.2.6 → 6.2.7):**
- Bug fixes
- Documentation updates
- Script enhancements (no breaking changes)
- Security patches

**MINOR (6.2.6 → 6.3.0):**
- New features
- New agents
- New configuration options (backward-compatible)
- Performance improvements

**MAJOR (6.2.6 → 7.0.0):**
- Protocol structure changes
- Breaking configuration changes
- Incompatible agent changes
- Requires migration guide

### CHANGELOG Best Practices

Use Keep a Changelog format:

```markdown
## [6.3.0] - 2025-11-07

### Added
- New features that were added

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future versions

### Removed
- Features that were removed

### Fixed
- Bug fixes

### Security
- Security fixes or improvements
```

---

## Audit Trail

Every version update creates an audit log:

**Location:** `.protocol-state/version-update-{version}.json`

**Example:**
```json
{
  "old_version": "6.2.6",
  "new_version": "6.3.0",
  "bump_type": "minor",
  "timestamp": "2025-11-07T14:30:00.000Z",
  "user": "Dewy",
  "files_updated": [
    "VERSION.md",
    "protocol.config.yaml",
    "README.md",
    "CHANGELOG.md"
  ],
  "git_commit": "a1b2c3d4e5f6g7h8i9j0",
  "git_tag": "v6.3.0"
}
```

**Usage:**
- Track update history
- Debug issues
- Compliance auditing
- Rollback reference

---

## FAQ

### Q: Can I use this script with forks?

**A:** Yes! The script reads the remote URL from your git config automatically.

### Q: What if I forget to update CHANGELOG?

**A:** You can edit CHANGELOG.md manually anytime and amend the commit:
```bash
# Edit CHANGELOG.md
git add CHANGELOG.md
git commit --amend --no-edit
git push --force-with-lease
```

### Q: Can I skip the push step?

**A:** Yes! When prompted "Push to remote?", choose `n`. Push manually later:
```bash
git push origin main
git push origin v6.3.0
```

### Q: How do I see what changed between versions?

**A:** Use git diff with tags:
```bash
git diff v6.2.6 v6.3.0
git log v6.2.6..v6.3.0
```

### Q: Can I use this in CI/CD?

**A:** Yes! Use preview mode first, then apply in pipeline:
```bash
# In .github/workflows/release.yml
python system-update.py minor
git push origin main --tags
```

---

## Migration from Old System

If you're using the old versioned folders approach:

### Step 1: Choose Canonical Repository

```bash
# Use the latest version folder
cd "Domain Zero Protocol v6.2.6"
```

### Step 2: Update Version Consistency

```bash
# Ensure protocol.config.yaml matches folder version
# Edit: versioning.protocol_version: "6.2.6"
```

### Step 3: Test New Script

```bash
python ../system-update.py patch --preview
```

### Step 4: Archive Old Folders

```bash
mkdir "../Domain Zero Protocol Backups"
mv "../Domain Zero Protocol v6.2.1" "../Domain Zero Protocol Backups/"
# Repeat for v6.2.2, v6.2.3, etc.
```

### Step 5: Use New Workflow

```bash
# Going forward, use git tags
python ../system-update.py minor
```

---

## Support

**Issues:** https://github.com/DewyHRite/Domain-Zero-Protocol/issues
**Documentation:** README.md, SYSTEM_UPDATE_V2_IMPLEMENTATION.md
**Version History:** CHANGELOG.md

---

**Last Updated:** November 7, 2025
**Script Version:** 2.0.0
**Protocol Version:** v6.2.6
