# System Update Framework - Public Implementation Guide (v8.5.1 Final)

> **Status:** Domain Zero Protocol v8.5.1 is the final internal development build. From this version onward, the protocol, agents, and system-update framework are **open source** and may be freely downloaded and customized by users.
>
> **Guarantee:** The system-update framework exists to (1) preserve the original intent and core safety properties of Domain Zero by default, and (2) protect every user's existing project from accidental deletion or overwrite **unless the user explicitly says otherwise**.

---

## 1. Purpose & Scope

This guide explains how the **System Update Framework** behaves now that:

- Domain Zero Protocol (DZP) and Domain Zero Agents (DZA) are public and customizable.
- v8.5.1 is the last internal development build; all future variations are user-controlled forks or derivatives.
- The update system must:
  - Protect existing projects from accidental damage.
  - Keep core safety guarantees intact by default.
  - Allow users to customize DZP as they see fit, when they explicitly choose to.

This document is **external-facing**: it describes behavior and guarantees, but does **not** expose internal file layouts or implementation details of the system-update framework.

---

## 2. High-Level Behavior

### 2.1 What the System Update Framework Does

- Provides a structured way to:
  - Install DZP into a new project.
  - Upgrade an existing DZP installation to a new version or local customization.
- Enforces **safety-first rules**:
  - Never deletes or overwrites user code or project state without explicit permission.
  - Keeps `.protocol-state/` and other project-specific state safe during updates.
  - Requires backups and rollback plans before making significant changes.
- Preserves **original protocol intent** by default:
  - All core safety, backup, and security rules remain active unless the user explicitly opts out or rewrites them.

### 2.2 What It Does *Not* Do

- It does **not** enforce a single canonical configuration across all users.
- It does **not** prevent users from modifying protocol files or behavior.
- It does **not** track or phone home about customizations (all behavior is local to the user’s machine/repo).

---

## 3. Open-Source Customization Model

### 3.1 User Freedom

With v8.5.1 public:

- You are free to:
  - Fork DZP and DZA.
  - Edit any protocol or agent file.
  - Change tier rules, safety thresholds, or agent personalities.
  - Remove, expand, or replace entire sections of the protocol.
- The recommended, low-friction path is:
  - **Start from v8.5.1 as a base.**
  - Make targeted edits in your fork.
  - Keep core safety behavior (backups, rollback, CLAUDE.md protection) unless you understand the consequences of changing them.

### 3.2 Default Behavior vs. Opt-Out

- **Default:** The system-update framework assumes you want **original DZP safety and behavior**.
- **Opt-out or Modify:**
  - To deviate from default safety or behavior, you must:
    - Edit protocol/config files yourself, or
    - Explicitly instruct Gojo (see §7) to apply a specific, described change.

---

## 4. Project Safety Guarantees

The system-update framework treats user projects as **primary** and the protocol as **replaceable scaffolding**.

### 4.1 No Accidental Deletion

The framework is designed so that, by default:

- It will **not** delete:
  - Your application source code (e.g., `src/`, `apps/`, etc.).
  - Your tests (e.g., `tests/`, `Test/`).
  - Your project documentation.
- Any action that *could* delete or truncate user files must:
  - Be clearly described in the prompt/plan, **and**
  - Require explicit user approval.

### 4.2 State Protection (`.protocol-state/` and Related Files)

For existing projects with DZP already installed:

- The framework **must not overwrite**:
  - `.protocol-state/project-state.json` (except for controlled field merges, see below).
  - `.protocol-state/dev-notes.md`.
  - `.protocol-state/security-review.md`.
  - `.protocol-state/trigger-19.md`.
- On upgrade, the only allowed automatic modification to `project-state.json` is **field-level merging** (for example, updating `protocol_version` or adding new fields without clobbering existing ones).
- Any broader change to project state must be:
  - Presented to the user as a proposed diff or summarized plan.
  - Approved explicitly.

### 4.3 Backups and Rollback Plans

Before any significant change (install or upgrade), the system-update workflow must:

1. Create a backup of relevant protocol/state files.
2. Record where the backup is stored.
3. Document a simple rollback plan (how to restore the previous state if needed).

Even as DZP becomes fully customizable, this backup+rollback pattern remains part of the **core safety contract**.

---

## 5. New vs Existing Projects

The system-update framework distinguishes clearly between:

### 5.1 New Projects (Fresh Install)

**Characteristics:**
- No existing `protocol/` or `.protocol-state/` from DZP, or user has explicitly requested a fresh install.

**Behavior:**
- It may copy the full distribution (e.g., `core-files-v8.5.1/`) into the project:
  - `protocol/` files
  - `.protocol-state/` templates
  - `docs/` and helper scripts
- Safety still applies:
  - No unrelated project files are overwritten.
  - Backups of any touched directories are created when in doubt.

### 5.2 Existing Projects (In-Place Upgrade)

**Characteristics:**
- Project already contains a DZP installation (`protocol/`, `.protocol-state/`, etc.).

**Behavior:**
- **Never** blindly overwrite `.protocol-state/` or user-modified protocol files.
- Use a **merge strategy**:
  - Update version metadata (e.g., `protocol_version`, `config_version`).
  - Add new files or sections that did not exist before.
  - Leave user changes intact unless the user has requested otherwise.
- Provide a clear summary of proposed changes and possible conflicts.

---

## 6. Internal vs External Files (Conceptual)

Even though the codebase is public, DZP distinguishes between:

### 6.1 INTERNAL Files / Docs (Conceptual Category)

- These are files that define the **guts** of the system-update framework and other internal mechanisms.
- They are intended for:
  - Protocol maintainers.
  - Advanced users who understand the implications of changing them.
- Examples (conceptual only; paths may vary):
  - System-update classification rules.
  - Internal manifests describing which files are protocol vs project-specific.
  - Low-level scripts that orchestrate multi-step updates.

**Policy:**
- Internal files are still readable in your fork (open source), but:
  - Only **Gojo** (Mission Control) is allowed to use tools that read/write them as part of **automated** update flows.
  - Other agents must treat them as read-only or off-limits, following the same spirit as `protocol/CLAUDE.md` protection.

### 6.2 External-Facing Docs

- These are documents intended for everyday users of DZP:
  - `README.md`
  - `PROTOCOL_QUICKSTART.md`
  - `docs/installation/IMPLEMENTATION_GUIDE.md`
  - `docs/TOKEN_EFFICIENCY_RECOMMENDATIONS.md`
  - Other guides and FAQs

**Requirement:**
- External docs must:
  - Clearly state that DZP is open source, downloadable, and customizable.
  - Explain that the system-update framework exists to preserve safety and intended behavior by default.
  - Emphasize that users can modify anything—**but** core safety behavior is recommended unless they explicitly choose to change it.

---

## 7. Agent Rules for System Update Operations

The same protection model used for `protocol/CLAUDE.md` applies to the system-update framework, with **Gojo** as the sole agent allowed to orchestrate global modifications.

### 7.1 Gojo Authority (Mission Control)

- **Only Gojo** may:
  - Read and edit all files directly related to the system-update framework as part of automated or semi-automated updates.
  - Propose and apply large-scale changes to protocol structure (e.g., migrating to a new major version, altering module layouts).
- Even Gojo must:
  - Obtain explicit user permission for any change that could affect project state.
  - Create backups and document rollback steps before applying changes.
  - Summarize what was changed and where.

### 7.2 Other Agents (Yuuji, Megumi, Nobara, Extended Four)

- May **use** the protocol as updated, but must not:
  - Modify system-update internals.
  - Bypass or weaken safety checks defined by the framework.
- Their responsibilities remain scoped:
  - Yuuji: implementation + tests
  - Megumi: security review and verification
  - Nobara: UX/strategy
  - Extended agents (Todo, Maki, Panda, Inumaki): delegated specialties

**Cross-Agent Edit Restriction (Non-Gojo Agents):**

- No non-Gojo agent is allowed to edit another non-Gojo agent's definition files.
- Concretely, for files such as `protocol/yuuji.agent.md`, `protocol/megumi.agent.md`, `protocol/nobara.agent.md`, `protocol/todo.agent.md`, `protocol/maki.agent.md`, `protocol/panda.agent.md`, and `protocol/inumaki.agent.md`:
  - Each non-Gojo agent has **read-only** access to all other agent files.
  - They may **not** propose or apply edits to any other agent's `.agent.md` file.
- Any structural or behavioral change to an agent definition must either:
  - Be made directly by the user, **or**
  - Be coordinated through Gojo with explicit user permission (Gojo may then edit agent files as part of a controlled update).

### 7.3 User Supremacy

- As always, the **user** outranks all agents:
  - You can edit any file, including system-update internals and `CLAUDE.md`, in your own fork.
  - You can instruct Gojo to apply specific changes, or instruct all agents to treat certain rules as advisory.
  - You can disable or replace the system-update framework entirely in your own copy.

The rules in this section apply to how **agents** behave, not to what you are allowed to do as a human maintainer.

---

## 8. How to Use the System Update Framework

### 8.1 Typical New Project Flow

1. **Clone or copy** the DZP repository (or the `core-files-v8.5.1` distribution) into your project.
2. Follow `PROTOCOL_QUICKSTART.md` to:
   - Configure `protocol.config.yaml`.
   - Initialize `.protocol-state/` (for new projects, templates are safe).
3. Invoke Gojo:
   - "Read `protocol/gojo.agent.md` and initialize Domain Zero for this project."
4. Gojo will:
   - Detect this is a new project.
   - Set up state and basic structure.
   - Confirm that no existing project files are being overwritten.

### 8.2 Typical Upgrade Flow (Existing DZP Project)

1. Update your local copy of DZP (e.g., pull from a fork or copy newer `core-files-v8.5.1` content to a temporary location).
2. Ask Gojo to plan an upgrade:
   - "Read `protocol/gojo.agent.md` and plan an in-place upgrade of this project to my current DZP fork."
3. Gojo will:
   - Classify files as protocol vs project-specific.
   - Propose a set of changes (adds/merges) without overwriting state.
   - Present a summary for your approval.
4. After your approval, Gojo will:
   - Create backups.
   - Apply the minimal safe set of changes.
   - Record what was changed.

---

## 9. Sukuna as System-Update Persona

In the stock v8.5.1 configuration, the **System Update Framework** is also embodied by a dedicated agent persona:

- **Sukuna (`protocol/sukuna.agent.md`)**:
  - Represents the adversarial-but-aligned system-update specialist.
  - Is invoked **only through Gojo** for planning and executing protocol/system updates.
  - Always defaults to **plan-first mode**: clarifying the requested update, classifying protocol vs project files, proposing a step-by-step plan with backups/rollback/tests, and waiting for explicit user approval before making any changes.
  - Engages in adversarial review with Gojo (JJK flavor when Mask Mode is ON) to stress-test update plans, but is always aligned with user safety and goals.
- Non-Gojo agents (Yuuji, Megumi, Nobara, Todo, Maki, Panda, Inumaki):
  - Treat Sukuna the same way they treat Gojo: as a higher-level authority they do **not** command directly.
  - May not modify `sukuna.agent.md` or request system updates from Sukuna directly; all such work is coordinated via Gojo.

Forks of DZP are free to modify or remove Sukuna, but should carefully consider how changes affect safety, update clarity, and the adversarial review benefits of the default design.

---

## 10. Communicating Open-Source Status in External Docs

All external-facing docs (e.g., `README.md`, `PROTOCOL_QUICKSTART.md`, `docs/installation/IMPLEMENTATION_GUIDE.md`) should communicate these points clearly:

- **Open Source & Customizable:**
  - "Domain Zero Protocol v8.5.1 is available as an open-source framework. You can download, fork, and customize it however you like."
- **System-Update Framework Purpose:**
  - "The system-update framework exists to keep your projects safe and to preserve the original protocol behavior by default. It will not delete or overwrite your work without explicit permission."
- **User Control:**
  - "You may change any part of DZP, including safety rules, in your own fork. The recommendations and defaults are there to help you avoid accidental damage, not to limit your freedom."

This guide itself is a reference for how those statements are implemented at a high level.

---

## 11. Summary

- **v8.5.1** is the final internal development build; from here, DZP and DZA are open-source and user-customizable.
- The **system-update framework** is responsible for:
  - Safe installs and upgrades.
  - Protecting existing projects (no accidental deletion or overwrite).
  - Preserving original protocol behavior and safety by default.
- **Internal files/docs** remain conceptually internal to agent workflows; Gojo alone coordinates their use in updates, with user approval.
- **External docs** must clearly state that DZP is open source and explain that the update framework enforces safety unless the user chooses otherwise.
- As the user, you are always free to change any of this in your own copy; these rules govern how **agents** behave when assisting you.

This guide should be read alongside `README.md`, `PROTOCOL_QUICKSTART.md`, and `docs/installation/IMPLEMENTATION_GUIDE.md` when adopting or customizing the Domain Zero Protocol.