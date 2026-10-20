# Upcoming Release: Domain Zero Protocol v9.13.0

**Status: in progress, not yet released. Last updated: 2026-10-20.**

This notice is for everyone using the current public release, **v9.12.1**. While building v9.13.0 we found
defects that are also present in v9.12.1. The fixes ship with v9.13.0. Until then, the steps below reduce your
exposure. We will replace this notice when v9.13.0 is published.

Domain Zero Protocol is an independent project inspired by Jujutsu Kaisen and is not affiliated with its rights
holders. See [NOTICE.md](NOTICE.md).

---

## What to do now (v9.12.1 users)

### 1. Commit or stash staged Git work before "Save & Break"
**Impact:** if Gojo's Save & Break checkpoint commit fails, its recovery step can discard work you had already
staged under `.protocol-state/` or `src/`, and a successful checkpoint commit can include other staged changes.
**Do now:** commit or stash anything you have staged before choosing Save & Break, or decline the commit prompt.
If a checkpoint commit fails, check `git status` and `git diff --cached` before continuing.

### 2. Keep a copy of your Cortex data outside its folder
**Impact:** Cortex keeps its backups inside the same data folder they protect, and nothing stops an AI agent or
a script from deleting that folder. A missing data folder is silently recreated empty. On encrypted installs,
nothing warns you if the encryption key has never been backed up, and losing the key means losing the brain.
**Do now:**
- Run `brain status` to find your data folder and copy it somewhere outside that folder.
- Run `brain memory-export` for a portable copy of your stored memories.
- On encrypted installs, run `brain key export` now and keep the result off this machine.
- Never let an agent delete anything under the `dzp-cortex` data folder. To clean up old installs, use
  `brain reset --scope orphans` (it is a dry run unless you confirm).

### 3. Don't restore or reset Cortex while it is indexing
**Impact:** a backup taken while Cortex is writing may be inconsistent, and a restore or reset that runs while an
index is in progress can leave the brain damaged.
**Do now:** check `brain status` first and only run `brain restore` or `brain reset` when no index is running
(not during `/session update` or `/session end`). Take backups when Cortex is idle.

### 4. Re-index fully after an interrupted index
**Impact:** if an index run is killed or interrupted, some files can be recorded as indexed even though their
content was not saved, so they stay missing from search; a run can also hang at exit while holding its lock.
**Do now:** after any interrupted run, run `brain index --full`. If the index lock stays held with no progress,
stop that Python process and run `brain recover --clear-lock`.

### 5. On Windows, index yourself instead of relying on the end-of-session hook
**Impact:** the automatic end-of-session index hook does not run reliably on standard Windows setups and can
fail without telling you.
**Do now:** run `/session update`, `/session end` or `brain index --incremental` yourself.

### 6. Keep generated, minified or very large single-line files out of the index
**Impact:** some unusual file contents (for example very long single lines) make indexing very slow and can
keep a CPU core busy for a long time. Indexing also has no CPU limit and can slow the whole machine.
**Do now:** exclude generated, minified and data/blob files with `exclude_tokens` in `brain.config.yaml`, or lower
`max_file_bytes`. Index when the machine is idle and avoid ending sessions on several projects at once.

### 7. Removed text can remain inside Cortex's keyword index
**Impact:** text from files you removed or re-indexed, or from a `reset --scope self`, can remain inside the
database's keyword index (hidden from results, but still stored, and copied into backups and exports).
**Do now:** if that matters for something sensitive, run `brain reset --scope all --yes` and re-index. Older
backups still contain the text; handle them accordingly.

### 8. Smaller issues
- **Custom entity patterns:** if you configure custom `entity_extraction_patterns`, a bad pattern can hang or
  crash the brain CLI instead of being rejected cleanly. Avoid custom patterns until v9.13.0.
- **Work-session alerts:** the 4h/6h/8h wellbeing alerts do not track real elapsed time. Use your own clock and
  `/session break` / `/session continue`.
- **False failures:** on Windows consoles that are not UTF-8, a session event can report failure after every step
  succeeded (set `PYTHONUTF8=1`); install verification and `doctor` can report errors that are not real on a fresh
  install. Re-run, and check the individual step results.
- **Protected paths:** the Cortex engine files under `.protocol-state/brain/` (including its secret-redaction
  code) are not on the protected-path list. Review any change to them by hand.

---

## Progress on v9.13.0

- **Fixes:** the issues above are fixed in the v9.13.0 development line, along with many issues found in new
  v9.13.0 code before release.
- **Now:** final verification - full test suites, real-browser checks of the new Cortex UI, and performance
  measurements - followed by the public review of the release.
- **Also coming:** the Cortex UI, a local browser control plane for Cortex, ships as a developer preview.
- **Date:** no date is promised. v9.13.0 is published only after every check passes.

## When v9.13.0 is released

- It will be published as the `DZP-v9.13.0` branch and become the default branch.
- Verify the release payload before installing, as described in [SECURITY.md](SECURITY.md#verifying-a-release).
- This notice will be replaced.

## Reporting a problem

Please follow [SECURITY.md](SECURITY.md) for anything security-related. Do not post exploit details in public issues.
