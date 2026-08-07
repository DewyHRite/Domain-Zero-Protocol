<!-- [CORE FILE] - Domain Zero Protocol v9.12.0 -->
# System Update Framework - Public Implementation Guide

> **Status:** Domain Zero Protocol has been open source since v8.5.1 — the protocol, agents, and
> system-update framework may be freely downloaded and customized by users. This is **not** a
> frozen baseline: the canonical maintainer has continued to actively develop and release the
> protocol from the [canonical repository](https://github.com/DewyHRite/Domain-Zero-Protocol) for
> 40+ releases since v8.5.1 (v8.6 through the current release; see root `CLAUDE.md`'s "📍 CANONICAL
> SOURCE" section and "Recent Version History" table for the live count). Open-source and
> customizable does not mean unmaintained — the recommended path for most users is to **sync to
> the canonical source** rather than diverge into a permanent fork, exactly as root `CLAUDE.md`
> states: *"If discrepancies arise between your local protocol files and the canonical source, you
> MUST update your local files to match the canonical version before proceeding with any
> development work."* Forking and
> customizing remains fully supported for users who want it; it is a choice, not the default.
>
> **Guarantee:** The system-update framework exists to (1) preserve the original intent and core safety properties of Domain Zero by default, and (2) protect every user's existing project from accidental deletion or overwrite **unless the user explicitly says otherwise**.

---

## 1. Purpose & Scope

This guide explains how the **System Update Framework** behaves now that:

- Domain Zero Protocol (DZP) and Domain Zero Agents (DZA) are public and customizable.
- v8.5.1 was the version at which DZP went open source. Since then, the canonical maintainer has continued to actively develop, version, and release the protocol from the canonical repository — this is ongoing, centrally-maintained development, not a one-time hand-off to a frozen fork.
- The update system must:
  - Protect existing projects from accidental damage.
  - Keep core safety guarantees intact by default.
  - Allow users to customize DZP as they see fit, when they explicitly choose to.
  - Allow users who prefer to stay current to sync with the canonical source's ongoing releases instead of maintaining a permanent fork.

This document is **external-facing**: it describes behavior and guarantees, but does **not** expose internal file layouts or implementation details of the system-update framework.

---

## 2. High-Level Behavior

### 2.1 What the System Update Framework Does

- Provides a structured way to:
  - Install DZP into a new project.
  - Upgrade an existing DZP installation to a new version — whether that is the canonical source's latest release or a local customization.
- Enforces **safety-first rules**:
  - Never deletes or overwrites user code or project state without explicit permission.
  - Keeps `.protocol-state/` and other project-specific state safe during updates.
  - Requires backups and rollback plans before making significant changes.
- Preserves **original protocol intent** by default:
  - All core safety, backup, and security rules remain active unless the user explicitly opts out or rewrites them.

### 2.2 What It Does *Not* Do

- It does **not** force every installation onto the canonical source's exact configuration — forking and local customization remain fully supported.
- It does **not** prevent users from modifying protocol files or behavior.
- It does **not** track or phone home about customizations (all behavior is local to the user's machine/repo).

---

## 3. Open-Source Customization Model

### 3.1 User Freedom

Since v8.5.1, with DZP public:

- You are free to:
  - Fork DZP and DZA.
  - Edit any protocol or agent file.
  - Change tier rules, safety thresholds, or agent personalities.
  - Remove, expand, or replace entire sections of the protocol.
- There are two supported paths, and the choice is yours:
  - **Stay in sync with the canonical source** (recommended for most users): pull the canonical repository's current release, keep your `protocol.config.yaml` identity fields, and get ongoing fixes and features as the canonical maintainer ships them. This is the default root `CLAUDE.md` describes.
  - **Maintain a diverging fork**: start from any canonical release as a base, make targeted edits, and accept the maintenance cost of tracking canonical changes yourself. Keep core safety behavior (backups, rollback, CLAUDE.md protection) unless you understand the consequences of changing them.

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
  - `.dzp-domain/domain.record.md`.
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
- It may copy the full distribution (the current canonical release, or the release payload zip — see root `CLAUDE.md`'s "Release payload" policy) into the project:
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
  - Other agents must treat them as read-only or off-limits, following the same spirit as root `CLAUDE.md` protection.

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
  - Emphasize that users can modify anything — **but** core safety behavior is recommended unless they explicitly choose to change it — and that staying synced with the canonical source is the recommended path for most users.

---

## 7. Agent Rules for System Update Operations

The same protection model used for root `CLAUDE.md` applies to the system-update framework, with **Gojo** as the sole agent allowed to orchestrate global modifications.

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

1. **Clone or copy** the current canonical DZP repository (or the release payload) into your project.
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

1. Update your local copy of DZP (e.g., pull the latest canonical release, or copy newer content from your own fork to a temporary location).
2. Ask Gojo to plan an upgrade:
   - "Read `protocol/gojo.agent.md` and plan an in-place upgrade of this project to the current canonical release." (or "...to my current DZP fork," if you maintain one)
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

The **System Update Framework** is also embodied by a dedicated resident agent persona:

- **Sukuna (`protocol/sukuna.agent.md`)**:
  - Represents the adversarial-but-aligned system-update specialist.
  - Is invoked **only through Gojo** (or directly by the user) for planning and executing protocol/system updates.
  - Always defaults to **plan-first mode**: clarifying the requested update, classifying protocol vs project files, proposing a step-by-step plan with backups/rollback/tests, and waiting for explicit user approval before making any changes.
  - Engages in adversarial review with Gojo (JJK flavor when Mask Mode is ON) to stress-test update plans, but is always aligned with user safety and goals.
- Non-Gojo resident agents (Yuuji, Megumi, Nobara, Todo, Maki, Panda, Inumaki):
  - Treat Sukuna the same way they treat Gojo: as a higher-level authority they do **not** command directly.
  - May not modify `sukuna.agent.md` or request system updates from Sukuna directly; all such work is coordinated via Gojo.
- Toji Fushiguro (`protocol/toji.agent.md`), the external, non-resident auditor, is a distinct role: report-only, zero execution privileges, and outside this update-authority chain entirely — he is never party to applying a system update.

Forks of DZP are free to modify or remove Sukuna, but should carefully consider how changes affect safety, update clarity, and the adversarial review benefits of the default design.

---

## 10. Communicating Open-Source Status in External Docs

All external-facing docs (e.g., `README.md`, `PROTOCOL_QUICKSTART.md`, `docs/installation/IMPLEMENTATION_GUIDE.md`) should communicate these points clearly:

- **Open Source & Customizable:**
  - "Domain Zero Protocol has been open source since v8.5.1. You can download, fork, and customize it however you like."
- **Actively, Centrally Maintained:**
  - "DZP is not a frozen baseline. The canonical maintainer continues to release new versions from the canonical repository; most users are better served syncing to the canonical source than maintaining a permanent fork."
- **System-Update Framework Purpose:**
  - "The system-update framework exists to keep your projects safe and to preserve the original protocol behavior by default. It will not delete or overwrite your work without explicit permission."
- **User Control:**
  - "You may change any part of DZP, including safety rules, in your own fork. The recommendations and defaults are there to help you avoid accidental damage, not to limit your freedom."

This guide itself is a reference for how those statements are implemented at a high level.

---

## 11. Summary

- **v8.5.1** is the version at which DZP and DZA went open-source and user-customizable — it is not the end of centrally-maintained development. The canonical source has continued shipping releases since (v8.6 through the current release; see root `CLAUDE.md` for the live count).
- The **system-update framework** is responsible for:
  - Safe installs and upgrades — whether syncing to the canonical source or applying a local fork's changes.
  - Protecting existing projects (no accidental deletion or overwrite).
  - Preserving original protocol behavior and safety by default.
- **Internal files/docs** remain conceptually internal to agent workflows; Gojo alone coordinates their use in updates, with user approval.
- **External docs** must clearly state that DZP is open source, actively and centrally maintained, and explain that the update framework enforces safety unless the user chooses otherwise.
- As the user, you are always free to change any of this in your own copy; these rules govern how **agents** behave when assisting you.

This guide should be read alongside `README.md`, `PROTOCOL_QUICKSTART.md`, and `docs/installation/IMPLEMENTATION_GUIDE.md` when adopting or customizing the Domain Zero Protocol.
