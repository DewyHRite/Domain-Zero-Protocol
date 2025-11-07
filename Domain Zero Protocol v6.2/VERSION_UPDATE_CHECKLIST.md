# Version Update Checklist

This document tracks all locations where version numbers must be updated when releasing a new version of the Domain Zero Protocol.

## Current Version: v6.2.1

---

## Version Update Process

When releasing a new version (e.g., v6.1 → v6.2), update the following files:

### 1. Folder Name
**Location**: Repository root
**Current**: `Domain Zero Protocol v6.1`
**Action**: Rename folder to match new version
```bash
git mv "Domain Zero Protocol v6.1" "Domain Zero Protocol v6.2"
```

### 2. VERSION File
**Location**: `Domain Zero Protocol v6.X/VERSION`
**Current**: `v6.1.0`
**Format**: `vMAJOR.MINOR.PATCH`
**Action**: Update single line with new version

### 3. protocol.config.yaml
**Location**: `Domain Zero Protocol v6.X/protocol.config.yaml`
**Lines to Update**:
- Line 11: `version: "v6.X.0"`

### 4. protocol/CLAUDE.md
**Location**: `Domain Zero Protocol v6.X/protocol/CLAUDE.md`
**Lines to Update**:
- Line 1: `# JUJUTSU KAISEN AI PROTOCOL SYSTEM v6.X`
- Line 4: `**Version**: 6.X`
- Line 6: `**Last Updated**: YYYY-MM-DD`
- Line 14: `> **Current Local Protocol Version**: v6.X`
- Line 657: Update version history entry

### 5. protocol/YUUJI.md
**Location**: `Domain Zero Protocol v6.X/protocol/YUUJI.md`
**Lines to Update**:
- Line 2: `## Agent Protocol File v6.X`
- Line 6: `**Protocol Version**: 6.X`

### 6. protocol/MEGUMI.md
**Location**: `Domain Zero Protocol v6.X/protocol/MEGUMI.md`
**Lines to Update**:
- Line 2: `## Agent Protocol File v6.X`
- Line 6: `**Protocol Version**: 6.X`

### 7. protocol/NOBARA.md
**Location**: `Domain Zero Protocol v6.X/protocol/NOBARA.md`
**Lines to Update**:
- Line 2: `## Agent Protocol File v6.X`
- Line 6: `**Protocol Version**: 6.X`

### 8. protocol/GOJO.md
**Location**: `Domain Zero Protocol v6.X/protocol/GOJO.md`
**Lines to Update**:
- Line 2: `## Agent Protocol File v6.X`
- Line 6: `**Protocol Version**: 6.X`

### 9. PR_SUMMARY.md
**Location**: `Domain Zero Protocol v6.X/PR_SUMMARY.md`
**Lines to Update**:
- Line 6: `**Protocol Version**: v6.X.0`
- Line 7: `**Release Date**: YYYY-MM-DD`

### 10. README.md
**Location**: `Domain Zero Protocol v6.X/README.md`
**Lines to Update**:
- Line 152-155: Update folder name in bash cp commands
- Line 161-164: Update folder name in PowerShell commands
- Line 170-173: Update folder name in cmd commands
- Various: Update references to "Domain Zero Protocol v6.X"

### 11. REVIEW_REMEDIATION_vX.X.md
**Location**: `Domain Zero Protocol v6.X/REVIEW_REMEDIATION_v6.X.md`
**Action**:
- Rename file to match new version
- Update version references inside

---

## Version Numbering Scheme

**Format**: vMAJOR.MINOR.PATCH

- **MAJOR** (6): Breaking changes or complete system overhauls
- **MINOR** (1): New features, enhancements, backward-compatible changes
- **PATCH** (0): Bug fixes, documentation updates, minor corrections

### Examples:
- `v6.1.0` → `v6.1.1`: Bug fix or documentation update
- `v6.1.0` → `v6.2.0`: New agent added, new features, enhanced workflow
- `v6.1.0` → `v7.0.0`: Breaking changes to protocol structure

---

## Automated Version Update Script (Future Enhancement)

Consider creating a script to automate version updates:

```bash
#!/bin/bash
# update-version.sh - Update all version references

OLD_VERSION=$1
NEW_VERSION=$2

if [ -z "$OLD_VERSION" ] || [ -z "$NEW_VERSION" ]; then
    echo "Usage: ./update-version.sh v6.1.0 v6.2.0"
    exit 1
fi

echo "Updating version from $OLD_VERSION to $NEW_VERSION..."

# Update VERSION file
echo "$NEW_VERSION" > "Domain Zero Protocol v${NEW_VERSION}/VERSION"

# Update folder name
git mv "Domain Zero Protocol v${OLD_VERSION}" "Domain Zero Protocol v${NEW_VERSION}"

# Update protocol.config.yaml
sed -i "s/version: \"$OLD_VERSION\"/version: \"$NEW_VERSION\"/" protocol.config.yaml

# Update CLAUDE.md
sed -i "s/v${OLD_VERSION}/v${NEW_VERSION}/g" protocol/CLAUDE.md

# ... (add more automated replacements)

echo "✅ Version update complete!"
echo "Review changes with: git diff"
```

---

## Verification Checklist

After updating version numbers, verify:

- [ ] Folder name matches new version
- [ ] VERSION file contains new version
- [ ] protocol.config.yaml version updated
- [ ] All agent protocol files (CLAUDE, YUUJI, MEGUMI, NOBARA, GOJO) updated
- [ ] README.md installation commands reference correct folder name
- [ ] PR_SUMMARY.md reflects new version
- [ ] All documentation paths updated
- [ ] No references to old version remain (search: `grep -r "v6.0" .`)
- [ ] Git commit message includes version change
- [ ] Git tag created: `git tag v6.X.0`

---

## Release Process

1. **Update all version numbers** (use this checklist)
2. **Update CHANGELOG.md** (create if doesn't exist)
3. **Run verification scripts**: `./scripts/verify-protocol.sh`
4. **Commit changes**: `git commit -m "Domain Zero v6.X.0 Release"`
5. **Create git tag**: `git tag -a v6.X.0 -m "Domain Zero Protocol v6.X.0"`
6. **Push to remote**: `git push && git push --tags`
7. **Create GitHub release** with release notes
8. **Update canonical repository** if this is the canonical source

---

**Last Updated**: 2025-11-06
**Maintainer**: Protocol Guardians
