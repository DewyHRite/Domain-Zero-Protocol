<!-- [CORE FILE] - Domain Zero Protocol v9.7.2 -->
# DZP Distribution & Release Workflow

How the **dev repo** (canonical) becomes a **sanitized public distribution**, how the
`distro/` release folder works, the **mandatory CodeRabbit PR review gate**, and how to
**replicate this pattern** for other projects (website, mobile app) for deployment/release.

> TL;DR: You develop on a private-by-default `Main-vX.Y.Z` branch that contains personal
> data and dev-only material. A tool (`dzp-publish`) copies an **allowlist** of files into a
> separate `distro/` git worktree, **scrubs identity/PII**, **audits** for forbidden content,
> **gates on version consistency**, and commits a clean `DZP-vX.Y.Z` branch. That branch is
> opened as a **PR**, reviewed by **CodeRabbit**, fixed, re-reviewed, and only then merged and
> set as the repo default. The dev branch is **never** pushed to the public canonical.

---

## 1. Why a dev/distro split?

The development tree intentionally holds things that must **never** ship publicly:

- Personal data (owner name, email, usernames, machine paths).
- Dev-only material: `internal-docs/`, PATCH reports, the agent registry, `.dzp-domain/`,
  `.protocol-state/` runtime state, `tests/`, backups.

A naive "just push `main`" would leak all of that. The split guarantees that **only a
reviewed, sanitized subset** ever reaches the public repository.

```
  PRIVATE / LOCAL                         PUBLIC CANONICAL (GitHub)
  ┌───────────────────────┐   dzp-publish   ┌──────────────────────────┐
  │ Main-vX.Y.Z (dev)     │  ───────────▶   │ DZP-vX.Y.Z (sanitized)   │
  │  • full source        │  allowlist +    │  • allowlisted files only │
  │  • internal-docs/     │  scrub + audit  │  • identity/PII scrubbed  │
  │  • PII, state, tests  │  + version gate │  • version-consistent     │
  └───────────────────────┘                 └──────────────────────────┘
        (never pushed public)                 (PR → CodeRabbit → merge)
```

---

## 2. The moving pieces

| Piece | What it is |
|-------|-----------|
| **Canonical repo** | The GitHub repository (`origin`). Its **default branch always points to the latest `DZP-vX.Y.Z`**, so the public face and the `check-updates` target are the newest release. |
| **`Main-vX.Y.Z` dev branch** | Active development line for a version bump. Carries PII + dev-only content. **Local-only** until a *private* dev remote exists; **never** pushed to the public canonical. |
| **`distro/` worktree** | A git **worktree** bound to an **orphan** branch named `DZP-vX.Y.Z`. It holds the sanitized published tree. Created once, reused every release. |
| **`scripts/distro/publish-manifest.yaml`** | The **allowlist**: exactly which folders/files/scripts/state get copied into the distro, plus forbidden tokens and exclude paths. |
| **`scripts/distro/dzp_publish_core.py`** | The engine: `stage` (copy allowlist), `scrub_identity`, `scrub_state`, `materialize_templates`, `content_scrub`, `content_audit` (PII), `exclude_audit` (forbidden paths). |
| **`scripts/dzp-publish.(ps1\|sh)`** | The operator entry point that orchestrates the above + the version gate + commit/push. |
| **`scripts/distro/assert_version.py`** | The **version-consistency gate**: every version-bearing file (CLAUDE.md ×2, VERSION.md, config, AI_INSTRUCTIONS, README, project-state, 10 agents) must agree, or publish aborts. |
| **`.coderabbit.yaml`** | Configures CodeRabbit to auto-review release/dev PRs and request changes until findings are addressed. |

---

## 3. The release folder (orphan worktree) — one-time setup

`distro/` is **not** a normal subfolder; it is a second working tree of the same repo,
checked out to an **orphan** history (`DZP-vX.Y.Z`) so the public branch shares **no commits**
with the dev branch.

```bash
# one-time, from repo root:
git worktree add --orphan -b DZP-v0.0.0 distro/
# distro/ now tracks its own DZP-* branch; the publish tool renames it per release.
```

Its own ignore rules live in `scripts/distro/distro.gitignore`. The publish tool **wipes
and re-stages** `distro/` from the manifest on every run (after taking a timestamped backup
to `.protocol-state/backups/distro-publish_<ts>/`), so the distro tree is always a clean
projection of canonical — never hand-edited.

---

## 4. The publish pipeline, step by step

Run from the dev branch (`Main-vX.Y.Z`) with the version cascade already complete
(`assert_version.py --root .` green).

```powershell
# 1) DRY RUN — stage + scrub + audit + version gate, NO commit/push. Always do this first.
scripts/dzp-publish.ps1 -DryRun -ForceClean

# 2) Build the release branch LOCALLY (commit to DZP-vX.Y.Z, no push):
scripts/dzp-publish.ps1 -NoPush -ForceClean

# 3) Push + release-gate (see §5). The script pushes DZP-vX.Y.Z and prints the gate.
scripts/dzp-publish.ps1 -ForceClean
```
(`scripts/dzp-publish.sh` is the POSIX/Git-Bash equivalent. Run with the **same git** that
created the worktree — not WSL against a Windows-created worktree.)

What each run does internally: backup `distro/` → wipe → `stage` allowlist → `scrub_identity`
→ `scrub_state` → `materialize_templates` → `content_scrub` → **`content_audit` (PII) — aborts
on any hit** → **`exclude_audit` (forbidden paths) — aborts on any hit** → **`assert_version`
on the distro tree — aborts on drift** → commit `DZP-vX.Y.Z` → (push unless `-NoPush`).

**Any audit or version failure aborts the publish** — a leak or drift can never reach a commit.

---

## 5. MANDATORY release gate — PR + CodeRabbit review loop

**No `DZP-vX.Y.Z` release may be merged without passing this gate.** It is enforced by policy
(this doc), by the publish scripts' closing instructions, and by `.coderabbit.yaml`.

```
 push DZP-vX.Y.Z ─▶ OPEN PR ─▶ CodeRabbit reviews ─▶ findings? ──yes──▶ fix on SAME PR ─┐
                                      │                                                  │
                                      │ no findings / all addressed                     │
                                      ▼                                                  │
                            re-request review ◀──────────────────────────────────────────┘
                                      │ clean
                                      ▼
                          MERGE PR ─▶ set repo default to DZP-vX.Y.Z
```

1. **Open a PR** for the release branch (base = the current default `DZP-vX.Y.Z`):
   ```bash
   gh pr create --base <current-default-DZP> --head DZP-vX.Y.Z --title "DZP-vX.Y.Z"
   ```
   (PR title mirrors the branch name, matching the version-bump naming convention.)
2. **Wait for CodeRabbit** to finish its automated review on the PR.
3. **Address every finding.** Fix on the dev side, re-run `dzp-publish` (or push fixes) to
   update the **same** `DZP-vX.Y.Z` branch/PR — do **not** open a new PR per fix.
4. **Re-request CodeRabbit review.** Repeat 2–3 until the review is clean (no unresolved
   change requests).
5. **Only then merge**, and **set the repo default branch to `DZP-vX.Y.Z`** so it becomes the
   latest public release and the `check-updates` target.

**Hard rules:** never merge before CodeRabbit review is addressed; never force-push the release
branch; never push a `Main-vX.Y.Z` dev branch to the public canonical (PII leak).

> Tip: protect `DZP-v*` with a branch-protection rule requiring the CodeRabbit check + ≥1
> approval, so step 5 is enforced by GitHub, not just convention.

### 5a. Operational commands (the CodeRabbit cycle in practice)

```bash
# After dzp-publish pushes DZP-vX.Y.Z, open the gated PR (once per release):
gh pr create --base <current-default-DZP> --head DZP-vX.Y.Z --title "DZP-vX.Y.Z" --body "..."

# Poll the review decision. NOTE: CodeRabbit emits emoji/unicode; on Windows pipe through
# Python with UTF-8 forced or you'll hit cp1252 'charmap' decode errors:
PYTHONUTF8=1 gh pr view <#> --json state,reviewDecision,reviews
gh api repos/<owner>/<repo>/pulls/<#>/comments --paginate   # inline findings

#   reviewDecision: CHANGES_REQUESTED  → triage + fix; APPROVED → gate cleared.
#   CodeRabbit's first comment is a "review in progress" placeholder — wait for the
#   real review (inline findings appear, a review is submitted, or that marker clears).

# Fix every finding on the DEV side (Main-vX.Y.Z), then update the SAME release branch/PR:
bash scripts/dzp-publish.sh --force-clean          # re-stage+scrub+audit+gate+commit+push (fast-forward, never --force)

# Re-request review (CodeRabbit also auto-reviews new pushes):
gh pr comment <#> --body "@coderabbitai review"

# Repeat until reviewDecision == APPROVED, then merge + promote to default:
gh pr merge <#> --merge        # merge commit; do NOT delete the DZP-vX.Y.Z branch — it becomes the default
gh api -X PATCH repos/<owner>/<repo> -f default_branch=DZP-vX.Y.Z
```

**Triage discipline:** evaluate each finding (real issue vs false positive) before implementing — don't blind-apply. Route code fixes through Yuuji (TDD) and protocol/doc fixes through Sukuna; keep unrelated/concurrent work out of the release commit. Worked example: PR #99 (DZP-v9.4.1) — CodeRabbit `CHANGES_REQUESTED` (8 findings: 3 code Majors incl. a pre-commit fail-open, 5 docs) → fixed on dev + re-published → `APPROVED` on re-review → merged + set default.

---

## 6. Branch & remote rules (PII protection)

- **Dev (`Main-vX.Y.Z`)**: contains PII/dev-only content. Lives local-only, or on a **private**
  remote if one is configured. Its PR (if any) is opened **only** on that private remote.
- **Release (`DZP-vX.Y.Z`)**: sanitized; the **only** thing pushed to the public canonical.
- **Default branch**: always the latest `DZP-vX.Y.Z`.
- If your only remote is the public canonical (the common case), you can publish `DZP-*` but you
  **cannot** open a `Main-*` PR there — configure a private remote first.

---

## 7. Replicating this pattern for other projects (website, mobile app)

The same five primitives generalize to any "private source → reviewed public/production
release" pipeline:

1. **Allowlist manifest** — declare exactly what ships (never "everything minus excludes").
2. **Secret/PII scrub + audit** — strip identity/secrets, then *fail the build* if any remain.
3. **Version/consistency gate** — refuse to release on drift.
4. **Isolated release branch/worktree** — an orphan branch so release history ≠ dev history.
5. **PR + automated review gate (CodeRabbit) before merge/deploy.**

### 7a. Website (static site / Next.js / etc.)
- **Dev branch** `main` holds source, `.env`, fixtures, internal notes.
- **Manifest** allowlists only the built/publishable assets (or the source needed by the host)
  — exclude `.env*`, `*.local`, analytics keys, design source, `tests/`.
- **Scrub/audit**: run a secret scanner (gitleaks/trufflehog) + a PII grep; **fail CI** on hit.
- **Release branch** `release` (orphan) or a `gh-pages`/deploy branch; or push the audited build
  artifact to the host (Vercel/Netlify/S3).
- **Gate**: PR `release` → CodeRabbit + secret scan must pass → merge → the host auto-deploys
  the default/production branch. Map "set repo default to latest DZP" → "promote to Production".

### 7b. Mobile app (iOS / Android)
- **Dev branch** holds signing configs, API keys, internal build flavors.
- **Manifest/flavor** = the *release* product flavor only; exclude debug-only code, mock servers,
  `*.keystore`/provisioning profiles (inject those from CI secrets, never commit).
- **Scrub/audit**: strip debug endpoints/keys; **fail the release build** if a secret or staging
  URL is present in the release flavor.
- **Version gate**: `versionName`/`versionCode` (Android) or `CFBundleShortVersionString`/build
  (iOS) must match the release tag — analogous to `assert_version.py`.
- **Release branch/tag** `release/vX.Y.Z` (orphan or tag) feeds the store pipeline (Fastlane →
  TestFlight / Play Internal track).
- **Gate**: PR `release/vX.Y.Z` → CodeRabbit + security scan → merge → CI uploads to the store.
  "Set default to latest DZP" → "promote build to the production track."

### 7c. Replication checklist
- [ ] Define the **allowlist manifest** (what ships) — not a denylist.
- [ ] Add an **identity/secret/PII scrub** + an **audit that fails the build** on any hit.
- [ ] Add a **version/consistency gate** that aborts on drift.
- [ ] Create an **isolated release branch/worktree** (orphan) or a clean artifact pipeline.
- [ ] Wire the **dry-run → build → push** stages (mirror `-DryRun` / `-NoPush` / push).
- [ ] Enforce the **PR + CodeRabbit (or equivalent) review loop before merge/deploy**
      (`.coderabbit.yaml` + branch protection).
- [ ] Keep the **dev branch private**; only the sanitized release reaches public/production.

---

## 8. Quick command reference

```powershell
# Validate version consistency on the dev tree (must pass before publishing):
python scripts/distro/assert_version.py --root .

# Dry run (no side effects):
scripts/dzp-publish.ps1 -DryRun -ForceClean

# Build the release branch locally (no push):
scripts/dzp-publish.ps1 -NoPush -ForceClean

# Publish (push DZP-vX.Y.Z, then follow the §5 PR + CodeRabbit gate):
scripts/dzp-publish.ps1 -ForceClean

# Open the release PR (base = current default DZP branch):
gh pr create --base <current-default-DZP> --head DZP-vX.Y.Z --title "DZP-vX.Y.Z"
```

---

**See also:** `scripts/distro/publish-manifest.yaml` (allowlist), `scripts/distro/assert_version.py`
(version gate), `.coderabbit.yaml` (review gate), `docs/superpowers/specs/2026-06-13-distro-publish-design.md`
(original design).
