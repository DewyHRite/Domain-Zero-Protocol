[INTERNAL DOCUMENT]

# Domain Zero: Plan Recovery Protocol

> **Classification:** INTERNAL DOCUMENT
> **Framework Version:** 1.3.0
> **Created:** 2025-12-05
> **Purpose:** Procedures for recovering lost plans from session transcripts or incomplete Plan Mode outputs

---

## When to Use This Protocol

Use this protocol when:
- Plan Mode was used but plan not persisted to plan-documentation.md
- Session ended before plan was saved
- Context cleared and plan details lost
- Plan exists in session transcript but not in framework state

**Goal**: Reconstruct complete plan and persist to framework state files

---

## Recovery Procedure

### Step 1: Locate Source Material

**Primary Sources** (check in order):

1. **Session Transcript**: `internal-docs/previous session.md`
   - Look for Plan Mode output
   - Search for phase breakdowns, task lists
   - Extract todo lists and timelines

2. **Implementation Progress**: `.protocol-state/IMPLEMENTATION_PROGRESS.md`
   - May contain partial plan details
   - Shows completed tasks

3. **Commit Messages**: `git log --oneline`
   - Commit messages may reference plan elements
   - Can infer work structure from commit history

4. **Todo Lists**: Search for todo list outputs in session transcript
   - Usually marked with ☐ ☒ symbols
   - May have phase labels

### Step 2: Extract Plan Elements

**Required Information** (extract from sources):

1. **Timeline**: Total weeks, phase breakdown
2. **Phases**: Phase 0, Phase 1, Phase 2, etc. with objectives
3. **Tasks**: Individual tasks per phase
4. **Files**: New files to create, files to modify
5. **Dependencies**: Task ordering and dependencies
6. **Acceptance Criteria**: How to verify each phase complete

**Template for Extraction**:

```markdown
## Extracted Plan Elements

**Source**: [session transcript / commit history / progress file]

### Timeline
- Total duration: [X weeks]
- Phases: [Phase 0 (Week 0), Phase 1 (Weeks 1-2), ...]

### Phase Breakdown

#### Phase 0: [Name]
**Weeks**: [Week X]
**Objective**: [Goal]
**Tasks**:
1. [Task 1]
2. [Task 2]
...

[Repeat for all phases]

### New Files
- [file 1]
- [file 2]
...

### Files to Modify
- [file 1]
- [file 2]
...
```

### Step 3: Reconstruct Missing Details

If plan is incomplete, use these inference methods:

**Method 1: Infer from Completed Work**
- Review `.protocol-state/IMPLEMENTATION_PROGRESS.md`
- Check git log for implemented features
- Deduce planned features from partially completed work

**Method 2: Infer from Todo Lists**
- Extract all ☐ and ☒ tasks from session transcript
- Group tasks by similarity (likely same phase)
- Estimate phase boundaries based on task complexity

**Method 3: Infer from Framework Knowledge**
- Use domain knowledge (e.g., validation framework needs schemas, engine, tests)
- Standard phase structure: Setup → Implementation → Testing → Documentation
- Typical week allocations: 2 weeks per major phase

**Method 4: Ask User for Clarification**
- Use AskUserQuestion tool for critical gaps
- Focus on: phase objectives, acceptance criteria, dependencies

### Step 4: Validate Reconstruction

**Verification Checklist**:

- [ ] All phases identified with objectives
- [ ] Task count matches original todo list (if available)
- [ ] Timeline is reasonable (not too compressed)
- [ ] Dependencies documented
- [ ] Acceptance criteria defined per phase
- [ ] File lists complete (new + modified)
- [ ] Risk assessment included
- [ ] Rollback points identified

**Quality Markers**:
- ✅ Good: Detailed week-by-week breakdown with specific tasks
- ⚠️ Acceptable: Phase-level breakdown with general task groups
- ❌ Insufficient: Only high-level features listed, no phases

### Step 5: Document Recovered Plan

**Location**: `.protocol-state/system-update-framework/plan-documentation.md`

**Format**: Standard UPDATE-{YYYY-MM-DD}-{SEQ} entry with RECOVERED flag

```markdown
## UPDATE-{date}-{seq}: {Feature Name}

**Status**: RECOVERED
**Original Plan Date**: {date if known}
**Recovery Date**: {current date}
**Recovery Source**: {session transcript / commit history / etc}
**Classification**: {UPDATE | FIX | STRUCTURAL_CHANGE}

### Recovery Notes

**Completeness**: {COMPLETE | PARTIAL | MINIMAL}
**Confidence**: {HIGH | MEDIUM | LOW}
**Missing Elements**: {list any gaps}

### Original Plan (Reconstructed)

[Full plan content as extracted/reconstructed]

### Phases

#### Phase 0: {Name}
...

[Continue with all phases]

### Lesson Learned

**Root Cause**: Plan Mode output not persisted before session end
**Prevention**: Framework v1.3.0+ requires mandatory plan persistence verification
**Impact**: {time lost / work delayed / scope unclear}
```

### Step 6: Update Framework State

After documenting recovered plan:

1. Update `version-registry.json` if not already updated
2. Update `backup-manifest.json` if backups exist
3. Create INTERNAL note about recovery in lesson learned section

---

## Prevention (Framework v1.3.0+)

**This protocol should rarely be needed after framework v1.3.0.**

New requirements prevent plan loss:
- ✅ Plan Mode MUST write to plan-documentation.md before exit
- ✅ Verification gate prevents exit without plan persistence
- ✅ User confirmation required: "Plan persisted to framework"

**If this protocol is used repeatedly**: Framework is not being followed correctly.

---

## Example Recovery

### Scenario: v8.8.0 Validation Framework Plan Lost

**Source**: `internal-docs/previous session.md` contains session transcript

**Extraction**:
- Timeline: 9 weeks (Week 0 + Weeks 1-8 + Week 9 documentation)
- Phase 0: Memory Tool Setup (Week 0) - 4 tasks identified
- Phase 1: Validation Engine (Weeks 1-2) - 4 tasks inferred
- Todo list: 32 tasks extracted from session transcript

**Reconstruction**:
- Phase objectives inferred from task names
- Dependencies inferred from logical ordering
- Acceptance criteria reconstructed from framework knowledge

**Result**: PARTIAL recovery (phase-level detail, missing some acceptance criteria)

**Documentation**: Added to plan-documentation.md with RECOVERED flag

---

## Recovery Quality Levels

| Level | Description | Actionable? |
|-------|-------------|-------------|
| **COMPLETE** | All phases, tasks, dependencies, acceptance criteria recovered | ✅ Yes |
| **PARTIAL** | Phases and tasks recovered, some criteria missing | ⚠️ With caution |
| **MINIMAL** | Only high-level features identified | ❌ Reconstruct fully |

**Minimum Acceptable**: PARTIAL recovery with user validation

---

## Notes

- Recovery is time-consuming (1-2 hours typical)
- Quality depends on source material completeness
- Framework v1.3.0+ makes this protocol mostly obsolete
- Keep session transcripts until plans are verified persisted

---

*This protocol is a safety net, not standard practice. Plans should always be created and saved BEFORE work begins.*
