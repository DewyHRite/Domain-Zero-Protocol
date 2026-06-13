<!-- [CORE FILE] - Domain Zero Protocol v8.13.0 -->
# Skill Builder - Domain Zero Protocol
## Create New Skills Quickly and Consistently

**Version**: 1.0.0
**Agent**: Any (recommended: Gojo)
**Purpose**: Rapidly create properly formatted skills for the Domain Zero Protocol

---

## Quick Start

When you want to create a new skill, use this skill to ensure consistency and save tokens.

**Invocation**:
```
skill: "skill-builder"

Create a skill for: [DESCRIPTION]
```

---

## Skill Creation Workflow

### Step 1: Gather Requirements

**USE AskUserQuestion TOOL** to clarify:

```
Questions to ask the user:
1. What agent(s) will use this skill? (yuuji/megumi/nobara/gojo/all)
2. What is the primary purpose? (e.g., "standardize API error responses")
3. Should this skill include escape paths for missing info? (yes/no)
4. Any specific tools required? (read/write/edit/bash/websearch/etc.)
```

### Step 2: Generate Skill Template

Use this template for all new skills:

```markdown
# [Skill Name] - Domain Zero Protocol
## [One-line Description]

**Version**: 1.0.0
**Agent(s)**: [yuuji|megumi|nobara|gojo|all]
**Category**: [implementation|security|ux|orchestration|document|utility]
**Token Efficiency**: [low|medium|high] token savings

---

## Purpose

[2-3 sentences explaining what this skill does and why it saves time/tokens]

---

## Prerequisites

**BEFORE using this skill, ensure**:
- [ ] [Prerequisite 1]
- [ ] [Prerequisite 2]
- [ ] [Prerequisite 3]

**ESCAPE PATH**: If prerequisites cannot be met:
1. [What to do instead]
2. [How to ask user for missing info]
3. [Graceful degradation approach]

---

## Quick Invocation

\`\`\`
skill: "[skill-name]"

[Brief context or task description]
\`\`\`

---

## Workflow Steps

### Step 1: [Name]

**Action**: [What to do]

**Tools**: [read|write|edit|bash|websearch|askuserquestion]

**ESCAPE PATH** if blocked:
- [Alternative approach 1]
- [Alternative approach 2]
- Use `AskUserQuestion` to clarify: "[specific question]"

### Step 2: [Name]

**Action**: [What to do]

**Tools**: [list tools]

**ESCAPE PATH** if blocked:
- [Alternative approach]
- Provide partial output with: "Completed X, need Y to finish Z"

---

## Output Template

[Standard output format for this skill]

---

## Escape Paths Summary

| Situation | Escape Path |
|-----------|-------------|
| Missing [X] | Ask user via AskUserQuestion: "[question]" |
| Cannot access [Y] | Provide partial results with explanation |
| Unclear requirements | Default to [safe option] and note assumption |

---

## Examples

### Example 1: [Scenario Name]

**Input**:
\`\`\`
skill: "[skill-name]"
[example input]
\`\`\`

**Output**:
\`\`\`
[example output]
\`\`\`

---

## Related Skills

- [skill-1]: [brief description]
- [skill-2]: [brief description]
```

### Step 3: Add Escape Paths (CRITICAL)

**Every skill MUST have escape paths for**:

1. **Missing Information**
   - What if user didn't provide required context?
   - Answer: Use `AskUserQuestion` tool with specific options

2. **Inaccessible Resources**
   - What if a file/URL/API is unavailable?
   - Answer: Provide partial results + explain what's missing

3. **Ambiguous Requirements**
   - What if the task could be interpreted multiple ways?
   - Answer: Default to safest/most common interpretation + note assumption

4. **Hard Blockers**
   - What if the skill truly cannot proceed?
   - Answer: Output "BLOCKED: [reason]" with clear next steps for user

### Step 4: Register in AGENT_SKILLS_MAP.yaml

Add to `protocol/skills/AGENT_SKILLS_MAP.yaml`:

```yaml
agents:
  [agent_name]:
    custom_skills:
      - [new-skill-name]
```

---

## Escape Path Best Practices

### DO: Soft Requirements

```markdown
**Prerequisites**:
- Project has package.json (PREFERRED)
  - If missing: Ask user about package manager preference
- Node.js installed (PREFERRED)
  - If missing: Provide instructions for manual approach
```

### DON'T: Hard Requirements

```markdown
# BAD - Agent will hang or fail silently
**Prerequisites**:
- MUST have package.json
- MUST have Node.js >= 18
```

### DO: Progressive Disclosure

```markdown
**Step 1**: Try automatic detection
**Step 2** (if Step 1 fails): Ask user for clarification
**Step 3** (if Step 2 unavailable): Provide generic template with [PLACEHOLDER] markers
```

### DO: Clear "I'm Stuck" Output

```markdown
## BLOCKED: Cannot Proceed

**Reason**: [Clear explanation]

**What I Need**:
1. [Specific item 1]
2. [Specific item 2]

**User Action Required**:
- Option A: Provide [X] via AskUserQuestion
- Option B: Skip this step (will result in [Y])
- Option C: Cancel and [Z]
```

---

## AskUserQuestion Integration

**ALWAYS use AskUserQuestion for**:
- Ambiguous requirements
- Multiple valid approaches
- Missing context
- User preferences

**Template**:
```
{
  "questions": [
    {
      "question": "Which approach should I use for [task]?",
      "header": "Approach",
      "options": [
        {"label": "Option A", "description": "Best for [scenario]"},
        {"label": "Option B", "description": "Best for [scenario]"},
        {"label": "Option C", "description": "Best for [scenario]"}
      ],
      "multiSelect": false
    }
  ]
}
```

---

## Quality Checklist

Before finalizing a new skill:

- [ ] Has clear purpose statement
- [ ] Lists prerequisites with ESCAPE PATHS
- [ ] Every step has an escape path
- [ ] Uses AskUserQuestion for ambiguity
- [ ] Has output template
- [ ] Includes examples
- [ ] Registered in AGENT_SKILLS_MAP.yaml
- [ ] Token efficient (avoids redundant processing)

---

## Meta: This Skill's Escape Paths

| Situation | Escape Path |
|-----------|-------------|
| User doesn't specify agent | Default to "all" agents, note assumption |
| User's description is vague | Use AskUserQuestion to clarify purpose |
| Cannot determine category | Ask user to select from: implementation, security, ux, orchestration, document, utility |
| Skill conflicts with existing | Ask user if they want to extend existing or create new |

---

**Remember**: A skill that hangs or outputs nothing is worse than a skill that asks for help. Always provide an escape path.
