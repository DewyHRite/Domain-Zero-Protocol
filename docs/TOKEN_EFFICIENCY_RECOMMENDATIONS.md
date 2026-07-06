<!-- [CORE FILE] - Domain Zero Protocol v9.9.1 -->
# Domain Zero Protocol - Token Efficiency Recommendations

> **Classification:** CORE FILE
> **Version:** 8.5.1
> **Last Updated:** 2025-11-27
> **Purpose:** Formal guidelines for maintaining token efficiency while preserving full protocol behavior

## Scope

This document captures practical recommendations and instructions for maintaining token efficiency in Domain Zero Protocol (DZP) while preserving full protocol behavior. It focuses on:
- Modular protocol architecture
- Subagent vs delegated-agent design
- Installation/upgrade patterns
- Day-to-day usage patterns when invoking agents

---

## 1. Modular Protocol Architecture

**Goal:** Avoid repeating large shared sections across multiple agent files and core docs.

- **Use shared modules for cross-cutting concerns.**
  - Keep common behavior (Emergency Stop, User Levels, Mask Mode, Safety, Escape Paths, Binding Oath, Mission Control Isolation, etc.) in `protocol/modules/*.md`.
  - Reference these modules from `CLAUDE.md` and all `.agent.md` files instead of inlining the full text.
- **Keep agent files focused.**
  - Agent files should prioritize:
    - Role definition and responsibilities
    - Tool access matrix
    - Tier behaviors
    - Handoff rules and escape paths
  - Move long, reusable explanations into modules or `docs/` and link to them.
- **Prefer links over duplication.**
  - When adding new guidance, ask: "Is this agent-specific or protocol-wide?"
    - Protocol-wide → add/extend a module in `protocol/modules/` and link.
    - Agent-specific → keep in that agent’s `.agent.md` only.

---

## 2. Subagent vs Delegated-Agent Design

**Goal:** Use true subagents only where they add real value, and rely on lightweight delegation patterns elsewhere.

### 2.1 Core vs Extended Agents

- **Core Four (real subagents):**
  - `yuuji`, `megumi`, `nobara`, `gojo` are the only true subagent types.
  - Their behavior is defined in `protocol/yuuji.agent.md`, `protocol/megumi.agent.md`, `protocol/nobara.agent.md`, `protocol/gojo.agent.md`.
  - These are the agents that should be registered/configured explicitly in Claude Code / tooling where subagent types are supported.

- **Extended Four (delegated roles):**
  - `todo`, `maki`, `panda`, `inumaki` are **delegated agents**, not separate subagent types.
  - They are implemented as role prompts that run **on top of** an existing subagent (typically Gojo or a general-purpose subagent).
  - Their behavior is documented in `protocol/todo.agent.md`, `protocol/maki.agent.md`, `protocol/panda.agent.md`, `protocol/inumaki.agent.md`, but they are *invocation patterns*, not separate system-level subagents.

### 2.2 Why This Hybrid Model Saves Tokens

- Keeps the subagent registry small (Core Four only), which:
  - Reduces boilerplate context the system must load to describe every subagent.
  - Avoids duplicating shared behavior blocks across 8+ subagents.
- Uses **short delegation prompts** for Extended Four, referencing existing modules instead of reloading full agent specs.
- Avoids needing an 8x expansion of subagent definitions and their associated per-call context.

### 2.3 Delegation Pattern for Extended Four

When an Extended agent is needed, prefer this pattern:

- **From Gojo (Mission Control):**
  - Use Gojo (or a general-purpose subagent) with a short, structured role prompt like:

    ```text
    Act in the role of the Domain Zero {AGENT_NAME} delegated agent.
    - Base behavior: follow the responsibilities and constraints from `protocol/{agent}.agent.md`.
    - Do NOT restate or reload the full protocol; assume it is already active.
    - Focus only on the specific task and reference shared modules by name instead of re-describing them.
    ```

- **Examples:**
  - Todo (Database):
    ```text
    Act as the Todo delegated agent for database and backend design.
    Follow `protocol/todo.agent.md` for responsibilities and consult shared modules (safety, tiers, kill switch) by name only.
    Focus on schema design, migrations, and query optimization for this specific task.
    ```
  - Maki (Performance):
    ```text
    Act as the Maki delegated agent for performance optimization.
    Follow `protocol/maki.agent.md` at a high level; do not restate the full protocol.
    Focus on profiling, bottlenecks, and concrete optimization steps for this feature only.
    ```

- **Instruction:** When documenting new flows in Gojo or other protocols, always:
  - Reference Extended Four as *delegated agents*.
  - Avoid language that implies they are separate subagent types.
  - Encourage short prompts that assume the protocol is already in context.

---

## 3. Installation & Update Patterns (Token-Aware)

**Goal:** Avoid loading unnecessary template/state content and keep prompts focused during installs/upgrades.

- **Separate Fresh Install vs Upgrade in docs and scripts.**
  - Fresh install: safe to copy full `core-files-vX.Y.Z/` structure, including `.protocol-state` templates.
  - Upgrade: **never** overwrite project-specific `.protocol-state` files (`project-state.json`, `dev-notes.md`, `security-review.md`, `trigger-19.md`).
- **Merge, don’t replace, `project-state.json`.**
  - On upgrade, only update version-related fields (e.g., `protocol_version`) instead of re-initializing the whole file.
  - This avoids needing large prompts to reconstruct lost state.
- **Keep installation prompts tight.**
  - When guiding an AI through installation, avoid re-pasting large README sections.
  - Instead, reference the guide by path (e.g., "Follow `docs/installation/IMPLEMENTATION_GUIDE.md`, section 'In-Place Upgrade'") and summarize only the delta.
- **Use the system-update framework.**
  - For scripted tools, let them classify files (protocol vs project-specific) using the internal system-update metadata instead of embedding large rule explanations into every AI prompt.

---

## 4. Day-to-Day Usage Patterns

**Goal:** Keep routine interactions with agents lean while preserving safety and protocol guarantees.

### 4.1 Avoid Re-Reading the Entire Protocol Each Time

- Do **not** prepend full `protocol/CLAUDE.md` or all agent files on every request.
- Preferred patterns:
  - Long-lived sessions (Claude Code, IDE plugins): Let the environment maintain context; just say for example:
    - `"Read protocol/yuuji.agent.md and implement [feature]"` once per feature or per logical work chunk.
  - Short sessions: Reference protocol by name and version instead of inlining the entire file:
    - "Follow Domain Zero Protocol v8.5.1 (already loaded) and use Yuuji for implementation."

### 4.2 Be Specific with Tasks

- Formulate tasks narrowly to avoid wide-ranging reasoning:
  - Good: "Implement password reset endpoint (Tier 2) in `src/auth/reset.py` and update tests in `tests/auth/test_reset.py`."
  - Less efficient: "Improve the auth system" (forces broader context loading and analysis).

### 4.3 Use Tiers Intentionally

- Tier choice directly impacts how much context is needed:
  - **Tier 1 (Rapid):** Minimal tests & no security review → smaller context for prototypes.
  - **Tier 2 (Standard):** Normal TDD + security → default for production features.
  - **Tier 3 (Critical):** Heavier test + security requirements → accept higher token use only when necessary (auth, payments, sensitive data).
- Document tier in the prompt once per feature; do not re-explain the whole tier system in every message.

---

## 5. Documentation & Authoring Guidelines

**Goal:** Keep docs richly informative for humans while minimizing what AI must read per task.

- **Structure long docs with clear sections and anchors.**
  - This allows prompts like: "See `docs/installation/IMPLEMENTATION_GUIDE.md`, section 'In-Place Upgrade (Existing Projects)'" instead of copying the whole document.
- **Prefer small, targeted reference docs for recurring patterns.**
  - Example: `docs/DZP_DZA_INSTALLATION_REVIEW.md` for install/upgrade behavior, referenced as needed.
- **Avoid duplicating the same large explanation across many files.**
  - Put shared rationale in one doc and link to it.
- **When updating docs, check for reuse opportunities.**
  - Before adding a large new section, ask: can this be a new module or a short section in an existing focused doc?

---

## 6. Checklist for Token-Efficient Changes

Use this checklist when adding or modifying protocol content:

1. **Is this behavior shared across agents?**
   - Yes → Put it in `protocol/modules/` and reference it.
   - No → Keep it localized to the relevant `.agent.md` or doc.

2. **Does this require a new subagent type?**
   - Only if it needs distinct tools/permissions and persistent identity.
   - Otherwise, implement as a delegated role on top of an existing subagent.

3. **Are you copying more than a few dozen lines into multiple files?**
   - If yes, refactor into a module or shared doc and link to it.

4. **Does an install/upgrade step mention copying `.protocol-state/`?**
   - Ensure it is clearly scoped to **fresh installs** only.
   - For upgrades, emphasize merge-only behavior and protection of project state.

5. **Does a recommended prompt include full protocol text?**
   - If yes, replace with a reference to protocol files and version.

---

## 7. Future Improvements (Non-Blocking)

These are optional enhancements that can further improve token efficiency over time:

- **Local MCP servers / tools:**
  - Move expensive operations (search, code analysis, state inspection) into tools so the AI calls them instead of re-reading many files.
- **Pre-baked "skills" for common flows:**
  - Encapsulate repeated long instructions (e.g., "Tier 2 security review flow") into reusable skills or snippets, invoked by short names instead of repeated text.
- **Automated protocol loader:**
  - For IDE integrations, preload `protocol/` files once per workspace and avoid re-sending them in prompts.

---

**Summary:**

Token efficiency in Domain Zero comes from three pillars:
- Shared modules instead of duplicated text
- A hybrid subagent/delegated-agent design (Core Four as real subagents; Extended Four as delegated roles)
- Focused prompts and installation/update patterns that avoid unnecessary state and documentation reloads.

Follow the guidelines above whenever you extend agents, update docs, or design new workflows.

---

## Where This Is Linked From

This document is intended to be discoverable in the main docs via:
- A reference in `README.md` under the architecture or advanced topics section.
- A reference in `docs/installation/IMPLEMENTATION_GUIDE.md` near the discussion of installation/upgrade flows and `.protocol-state` handling.

When you update those docs, ensure they continue to point here so token-efficiency guidance stays easy to find.