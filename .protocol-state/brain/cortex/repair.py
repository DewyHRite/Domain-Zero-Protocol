"""Owner-only permission repair for PRE-EXISTING Cortex storage.

SEC-CORTEXSTOR-9.12.0-001 (accepted-p3 residual of the v9.12.0 Wave B2 fix,
commit 46a6670): `recovery.ensure_owner_only_dir()` / `paths.py` / `store.py`
harden Cortex's directories at CREATION time only (POSIX 0700 / Windows
icacls). A directory that already existed BEFORE that fix shipped -- which is
every pre-v9.12.0 install's live brain, e.g. the on-disk data dir under
`%LOCALAPPDATA%\\dzp-cortex\\<install-id>` -- is left untouched; the code only
warns (rate-limited to once per process; see `recovery.ensure_owner_only_dir`'s
own docstring, "EXISTING-PATH GAP"). SEC-CORTEXSTOR-9.12.0-001 records two
residuals: (a) pre-existing dirs are never auto-remediated, and (b) brain.db
itself gets no FILE-level hardening at first connect. This module closes (a)
outright and closes the practical exposure of (b) as a side effect (brain.db,
when present, is one of the files this module hardens).

This is a SANCTIONED, ONE-SHOT, OWNER-INITIATED repair tool -- `brain
repair-perms` (see brain.py) -- NOT new always-on machinery. It deliberately
does not touch `ensure_owner_only_dir`'s creation-time behavior or its
warning; running the repair is what makes that warning stop firing (the
condition it warns about becomes false), not a suppression flag.

Ordering contract (per-path record -> apply -> verify, spec-mandated):
  1. `scan()`      -- pure read: snapshot every present path's prior
                       owner-only state. NO mutation.
  2. manifest       -- the CALLER (see `run_repair()`) writes the FULL
                       pre-repair snapshot to a timestamped, owner-only
                       report BEFORE any path is touched, so the prior state
                       is never lost even if a later path's repair fails.
  3. `apply_repairs()` -- for each present path: if already owner-only,
                       ALREADY-OK; otherwise harden and re-verify. POSIX
                       (SEC-001 fix, see below): validation and mutation are
                       bound to ONE `os.O_NOFOLLOW`-opened descriptor
                       (fstat/fchmod), not re-resolved by pathname. Windows:
                       `crypto._harden_windows_acl` -- the SAME primitive
                       `ensure_owner_only_dir`/`load_or_create_salt` already
                       use, kind-aware via its `is_dir` parameter -- see
                       BUG-CORTEXREPAIR-9.12.0-001 below, narrowed by an
                       immediate pre-call identity re-check (accepted
                       residual, SEC-001). A failed harden or a failed
                       post-harden verify is reported as FAILED-<reason> --
                       never silently skipped. For a DIR, a successful
                       self-verify is followed by a CHILD-AWARE check
                       (`_dir_children_orphaned()`) that any existing
                       immediate children remain accessible; if a child was
                       orphaned the outcome is FAILED-children-orphaned, not
                       REPAIRED.

SEC-001 (MEDIUM, 2026-08-06 Toji audit
audits/2026-08-06-toji-v9-12-0-release-train-and-remediation.md, CWE-59
Improper Link Resolution Before File Access / CWE-367 Time-of-check
Time-of-use Race Condition): SEC-003 (below) closed the scan()-to-
apply_repairs() window by re-checking link/reparse status and containment
immediately before use, but that re-check was itself followed by two
SEPARATE pathname-based operations -- `recovery.verify_owner_only(path)`
then `_harden_existing(path, kind)` -- each of which re-resolved `path`
independently, leaving a narrower but still-present window in which a node
could be replaced between the re-check and either of those uses.
`apply_repairs()` now captures an `lstat()` immediately after the re-check
and, on POSIX, opens `path` with `os.O_NOFOLLOW` (`os.O_DIRECTORY` added for
dirs) to obtain ONE descriptor used for verification (`os.fstat`), mutation
(`os.fchmod`, threaded through `_harden_existing`'s new `fd` parameter), and
re-verification -- with an `st_dev`/`st_ino` identity comparison against the
captured lstat catching a non-symlink object swap that `O_NOFOLLOW` alone
would not. On Windows, no fd/handle-based hardening primitive is available
in this codebase's dependency set (`icacls` is pathname-based; a true
handle-bound `SetSecurityInfo` port needs `pywin32`, a hard dependency this
base-path module deliberately avoids -- see recovery.py's WINDOWS PRIMITIVE
CHOICE note) -- the window is NARROWED, not eliminated: an immediate
re-`lstat()` directly before the `_harden_existing()` call rejects on any
reparse-bit or identity change relative to the captured lstat. A swap
strictly between that re-lstat and `_harden_existing()`'s own icacls
invocation remains possible and is an ACCEPTED RESIDUAL for this wave,
reported for Megumi to rate rather than presented as a full fix. See
`tests/brain/test_repair_perms.py::test_apply_repairs_rejects_replacement_after_final_validation_before_harden`
for the regression proving the POSIX close.

**Windows interim follow-up (2026-08-06, Megumi review finding 3, [SEC-ID pending
mint -- CORTEXREPAIR subsystem; family SEC is Megumi-sole, Yuuji's
`residentid-yuuji.sh new SEC ...` attempt failed closed with `error: yuuji not
authorized for family SEC`, routed to Gojo/Megumi to mint])**: `apply_repairs()`'s
Windows branch now ALSO re-`lstat()`s immediately AFTER `_harden_existing()`
returns and compares against the pre-harden lstat, reporting
`FAILED-identity-changed-during-harden` (never `REPAIRED`) on a mismatch. This
DETECTS a race won strictly during the icacls call itself -- the one sub-window
the pre-harden check cannot observe -- but still does not PREVENT it (same
no-fd/handle-primitive constraint as above); a full fix remains the tracked
`pywin32`-based handle-bound port.

BUG-CORTEXREPAIR-9.12.0-001 (v9.12.0, discovered in this same Wave B4 rollout;
confirmed on the live brain by Gojo investigation 2026-08-05): the claim this
docstring originally made -- that reusing `crypto._harden_windows_acl`
unchanged for directories was "no new platform logic" -- was true of the
CALL SITE but incomplete about the PRIMITIVE's own behavior: it granted a
PLAIN, non-inheritable ACE (correct for its original FILE-only purpose, the
encryption salt sidecar) regardless of `kind`. Applied to a DIRECTORY with
EXISTING children relying on inherited ACEs, Windows' automatic-inheritance
propagation strips those children's inherited ACEs when the parent stops
publishing anything inheritable, leaving any child with no ACE of its own
with an EMPTY DACL -- deny everyone, including the object's own owner. This
module's own `verify_owner_only()` post-check only inspected the TARGET
path, so a repair that silently bricked every child still reported 8/8
REPAIRED. Fixed by making `crypto._harden_windows_acl` kind-aware (an
`is_dir` parameter selects an inheritable `(OI)(CI)F` grant for
directories, unchanged plain `F` for files) and by adding the child-aware
post-verify described above. See `crypto._harden_windows_acl`'s docstring
for the full mechanism writeup.

Idempotent: a path already owner-only reports ALREADY-OK and is left alone;
running twice in a row yields ALL ALREADY-OK on the second run.

PROV-REPAIR-002 (Megumi @approved fold-in, defense-in-depth advisory): run this
tool when no OTHER Cortex process holds an active connection to this data_dir
(e.g. no concurrent `brain index`/`brain query`/etc. against the same brain).
POSIX chmod and Windows DACL replacement do not themselves require closed file
handles to succeed, but running concurrently with another live Cortex process
against the same data_dir is UNTESTED territory for this tool -- treat it as
an operator precaution, not an enforced precondition.
"""
from __future__ import annotations

import json
import os
import stat
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path

from . import recovery

# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

# Fixed-name directories this tool hardens (path relative names, resolved
# against data_dir). Sourced from the concrete, already-owner-only-intended
# locations elsewhere in this codebase:
#   - data_dir itself      : paths.data_dir() / store.py Store.__init__ (db_path.parent)
#   - memories              : paths.memories_dir()
#   - model-cache           : paths.model_cache()
#   - backups               : store.py Store.backup_db() (brain.db copies + .manifest.json siblings)
#   - recovery-exports      : brain.py _do_memory_export()'s default out_dir (escrow-wrapped snapshots)
_FIXED_DIR_NAMES = ("memories", "model-cache", "backups", "recovery-exports")

# Fixed-name files this tool hardens, directly under data_dir. Sourced from:
#   - brain.db               : store.py primary DB (SEC-CORTEXSTOR-9.12.0-001 residual (b))
#   - brain.db.salt          : crypto.py KDF salt sidecar (load_or_create_salt)
#   - key-generation.json    : recovery.py allocate_key_generation's counter record
#   - key-generation.lock    : recovery.py allocate_key_generation's O_EXCL lock (ephemeral;
#                              POSIX-mode-safe already, but never Windows-ACL-hardened)
#   - recovery-journal.jsonl : cortex/recover.py RecoveryJournal (written via write_owner_only)
#   - content-refs.highwater : recovery.py high-water baseline (advisory, low-sensitivity, but
#                              lives alongside the above and costs nothing extra to include)
#
# PROV-REPAIR-001 (Megumi @approved fold-in): this list is DELIBERATELY BROADER than the
# original v9.9.x write-path secrecy classification. key-generation.json is written via
# recovery.py's plain `_atomic_write` (NOT `write_owner_only`) -- that module's own header
# comment marks `_atomic_write` as "must NOT be used for key-equivalent content"; a *.db.manifest.json
# sidecar (recovery.write_manifest, also via `_atomic_write`) is likewise documented as
# non-secret (RecoveryManifest carries digests/timestamps/schema markers, no key material).
# Hardening them anyway is a STRICTLY-SAFE TIGHTENING, not a misreading of that classification --
# owner-only permissions are never wrong to have on data that lives in the same directory as
# genuinely secret siblings (brain.db.salt, key-generation lock/counter, escrow exports), even
# when the individual file's own content isn't itself secret. Do not read the blanket coverage
# here as evidence the original write-path secrecy split was mistaken; it wasn't -- this module
# just doesn't need to preserve that split's granularity to do its job safely.
_FIXED_FILE_NAMES = (
    "brain.db",
    "brain.db.salt",
    "key-generation.json",
    "key-generation.lock",
    "recovery-journal.jsonl",
    "content-refs.highwater",
)


def inventory(data_dir: "str | Path") -> list[tuple[Path, str]]:
    """Return the full candidate list of `(path, kind)` this tool considers,
    where `kind` is `"dir"` or `"file"`. Existence is NOT checked here (pure
    path construction) -- callers (`scan()`) filter by lexists()/link/
    containment (see SEC-003 note below).

    Order: data_dir itself first, then the other fixed dirs, then fixed
    files, then the DYNAMIC contents of backups/ and recovery-exports/ (every
    file directly inside each, if the directory exists -- brain-*.db +
    *.manifest.json backup copies, and escrow-wrapped memory-export
    artifacts, whose exact filenames are timestamped and not fixed).

    PROV-REPAIR-001: the *.manifest.json siblings enumerated here are hardened
    too, even though recovery.RecoveryManifest's own fields are documented as
    non-secret (digests/timestamps/schema markers) -- same "strictly-safe
    tightening, not a misclassification" reasoning as `_FIXED_FILE_NAMES`
    above (see that block's comment for the full rationale).

    SEC-003 (MEDIUM, 2026-08-06 Toji audit,
    audits/2026-08-06-toji-v9-12-0-recent-work.md, CWE-59): the dynamic-
    enumeration step below is the ONE place `inventory()` does its own
    filesystem I/O (`is_dir()` / `iterdir()`), and both follow symlinks --
    so a `backups`/`recovery-exports` entry that is itself a symlink/
    junction to a directory OUTSIDE data_dir would previously have its
    contents walked and returned as if they were ordinary in-root dynamic
    candidates. `_is_link_or_reparse()` (lstat-based, never follows the
    final component) is checked FIRST so this function never walks through
    such a link at all -- the linked `backups`/`recovery-exports` entry
    ITSELF is still returned via `_FIXED_DIR_NAMES` above, where `scan()`
    rejects it directly. Each individual child is also excluded the same
    way if IT is a link (`child.is_file()` alone follows a symlink to a
    real file, so it cannot be relied on to exclude one).

    NOTE: this deliberately uses `_is_link_or_reparse()`, NOT
    `Path.is_symlink()` -- confirmed during this fix's own verification
    (real `mklink /J` on Windows) that an NTFS junction does NOT satisfy
    `is_symlink()`/`os.path.islink()` on CPython (junctions carry the
    MOUNT_POINT reparse tag, not the SYMLINK tag `os.path.islink` checks
    for) even though it is unambiguously a reparse point that must be
    rejected. `is_symlink()` alone would silently miss exactly the
    real-world case this fix targets; see
    test_windows_scan_rejects_junction_reparse_point for the regression
    that catches a future accidental revert to `is_symlink()` here.
    """
    d = Path(data_dir)
    entries: list[tuple[Path, str]] = [(d, "dir")]
    entries += [(d / name, "dir") for name in _FIXED_DIR_NAMES]
    entries += [(d / name, "file") for name in _FIXED_FILE_NAMES]

    for dyn_dir_name in ("backups", "recovery-exports"):
        dyn_dir = d / dyn_dir_name
        if _is_link_or_reparse(dyn_dir):
            continue
        if dyn_dir.is_dir():
            for child in sorted(dyn_dir.iterdir()):
                if child.is_file() and not _is_link_or_reparse(child):
                    entries.append((child, "file"))
    return entries


# ---------------------------------------------------------------------------
# Result record
# ---------------------------------------------------------------------------


@dataclass
class PathResult:
    path: str
    kind: str  # "dir" | "file"
    existed: bool
    prior_owner_only: "bool | None"  # None if the path did not exist
    prior_mode_octal: "str | None"  # POSIX only; None on Windows or if absent
    outcome: str
    # PENDING            -- scan() only, not yet processed by apply_repairs()
    # SKIPPED-ABSENT     -- path did not exist
    # ALREADY-OK         -- already owner-only, untouched
    # WOULD-REPAIR       -- dry-run: not owner-only, would be hardened
    # REPAIRED           -- hardened and re-verified owner-only
    # FAILED-harden-error:<exc>   -- the harden call itself raised
    # FAILED-verify-after-harden -- harden ran (no exception) but re-verify still failed
    # FAILED-children-orphaned   -- (dir only, BUG-CORTEXREPAIR-9.12.0-001) the
    #                                target itself re-verified owner-only, but an
    #                                existing immediate child became inaccessible
    #                                (empty/deny-everyone DACL) as a side effect
    # FAILED-identity-changed-during-harden -- (Windows only;
    #                                SEC-CORTEXREPAIR-9.12.0-003, accepted-p3,
    #                                minted by Gojo on Megumi's documented
    #                                recommendation 2026-08-06,
    #                                Megumi review 2026-08-06 finding 3 "cheaper
    #                                interim" recommendation) `_harden_existing()`'s own
    #                                icacls invocation is itself a SEPARATE pathname-
    #                                based mutation that can race with a node
    #                                replacement occurring strictly between the
    #                                pre-harden `narrow_lstat` capture and this call
    #                                returning -- the one sub-window the pre-harden
    #                                re-lstat check (see SEC-001 note below) cannot see,
    #                                since it runs BEFORE the call, not after. A
    #                                post-harden `os.lstat()` compared against
    #                                `narrow_lstat` (st_ino/st_dev + reparse-attribute
    #                                bit) DETECTS a won race in that sub-window and
    #                                reports it here instead of REPAIRED -- it does NOT
    #                                prevent the race (no fd/handle primitive exists on
    #                                this path; see the module-level SEC-001 note), so a
    #                                replacement that happens to still read back as
    #                                owner-only via `recovery.verify_owner_only()` is
    #                                still surfaced instead of silently certified.
    # FAILED-link-rejected       -- (SEC-003, MEDIUM, 2026-08-06 Toji audit, CWE-59;
    #                                narrowed further by SEC-001, MEDIUM, 2026-08-06
    #                                Toji release-train audit, CWE-367) the path node
    #                                exists but is untrustworthy: it is itself a
    #                                symlink/junction/reparse point, OR its resolved
    #                                location falls outside data_dir (e.g. a symlinked
    #                                ancestor directory), OR it was replaced with one
    #                                of the above BETWEEN scan() and apply_repairs()
    #                                (TOCTOU, SEC-003), OR (SEC-001) the bound
    #                                verify/harden descriptor could not be opened
    #                                without following a link (POSIX O_NOFOLLOW ELOOP)
    #                                or its post-open identity did not match the
    #                                pre-open lstat. Never stat/chmod/ACL'd -- reported
    #                                and skipped, exactly like SKIPPED-ABSENT, but
    #                                counted as a FAILED-* outcome so `brain
    #                                repair-perms`'s existing fail-closed exit-code
    #                                logic (any FAILED-* present -> exit 1) covers it
    #                                with no separate CLI wiring.


# Windows reparse-point flag. `stat.FILE_ATTRIBUTE_REPARSE_POINT` is a plain
# integer constant defined in every CPython build regardless of host OS (it is
# not itself an OS call), so referencing it here does not need an `os.name`
# guard -- only the `st_file_attributes` attribute it is compared against is
# Windows-only, and that is guarded at the call site below.
_FILE_ATTRIBUTE_REPARSE_POINT = stat.FILE_ATTRIBUTE_REPARSE_POINT


def _lexists(path: Path) -> bool:
    """`Path.exists()` follows the final symlink component: a symlink whose
    TARGET is missing would read as "absent" even though the link node
    itself -- the exact thing this module must detect and refuse to touch
    -- is present. `os.lstat()` never follows the final path component, so
    a successful lstat is proof the node itself exists, independent of
    what it points at or whether that target exists (SEC-003)."""
    try:
        os.lstat(path)
    except OSError:
        return False
    return True


def _is_link_or_reparse(path: Path) -> bool:
    """True if `path` is a symbolic link OR (Windows only) carries the
    FILE_ATTRIBUTE_REPARSE_POINT flag -- i.e. any filesystem object whose
    apparent location is not its actual, physical location (CWE-59:
    Improper Link Resolution Before File Access). Junctions are covered by
    `stat.S_ISLNK` via `os.lstat` on Python 3.8+ (junctions report as
    symlinks since bpo-37834), so the reparse-point check below is
    defense-in-depth for reparse points that are NOT classified as
    symlinks by `os.lstat` (e.g. other third-party reparse tags).

    Uses `os.lstat()` exclusively -- never `Path.stat()`/`os.stat()`, which
    would follow the very link this function exists to detect."""
    try:
        st = os.lstat(path)
    except OSError:
        # Vanished between the caller's _lexists() check and this call --
        # not this function's concern; the caller's own existence handling
        # already covers that race.
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    if os.name == "nt":
        attrs = getattr(st, "st_file_attributes", 0)
        if attrs & _FILE_ATTRIBUTE_REPARSE_POINT:
            return True
    return False


def _within_data_root(path: Path, root: "str | Path") -> bool:
    """True only if `path`'s fully RESOLVED (canonical, symlink-following)
    location is contained within `root`'s fully resolved location. This
    catches the case `_is_link_or_reparse(path)` alone cannot: `path`
    itself is an ordinary file/dir, but an ANCESTOR directory in its path
    (e.g. a symlinked `backups/`) is a link, so the physical location the
    OS actually opens/chmods is somewhere else entirely (SEC-003).

    C2 advisory (2026-08-06 combined Toji-remediation review, no SEC-ID --
    theoretical only, not demonstrated exploitable): every caller of this
    function (`scan()`) has already confirmed `path` exists via `_lexists()`
    (an `os.lstat()` call) immediately before invoking it, so `path` is
    always lstat-confirmed present. `resolve(strict=True)` is therefore used
    for `path` -- a strict resolution failure (e.g. a symlink loop, or a
    component vanishing in a TOCTOU race between the `_lexists()` check and
    this call) is treated as fail-closed (NOT within root, i.e. rejected)
    rather than silently falling back to a loose, potentially
    case-folded/partial resolution. `root` keeps `strict=False`: it is the
    caller-supplied data_dir root, not itself lstat-confirmed by this
    function, and may legitimately be compared against even if some root
    ancestor is momentarily in flux."""
    try:
        resolved_root = Path(root).resolve(strict=False)
    except OSError:
        return False
    try:
        resolved_path = path.resolve(strict=True)
    except OSError:
        # Fail-closed: an unresolvable path (broken symlink target,
        # resolution race, symlink loop) is treated as NOT contained
        # within root -- never silently trusted via a loose fallback.
        return False
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        return False
    return True


def _describe_mode(path: Path) -> "str | None":
    if sys.platform == "win32":  # pragma: no cover - Windows only
        return None
    return oct(stat.S_IMODE(path.stat().st_mode))


def scan(data_dir: "str | Path") -> list[PathResult]:
    """Phase 1 (pure, no mutation): snapshot every candidate path's prior
    owner-only state. Absent paths are recorded as SKIPPED-ABSENT (terminal --
    `apply_repairs()` leaves them unchanged); present paths are recorded as
    PENDING for `apply_repairs()` to process.

    SEC-003 (MEDIUM, 2026-08-06 Toji audit, CWE-59): a present path is
    rejected as FAILED-link-rejected (also terminal) BEFORE this function
    ever calls `recovery.verify_owner_only()` or `_describe_mode()` --
    both of which stat the path and would follow a link -- if it is itself
    a symlink/reparse point, or if its resolved location falls outside
    data_dir. Uses `_lexists()`, not `path.exists()`, for the initial
    presence check (see that helper's docstring for why).
    """
    root = Path(data_dir)
    results: list[PathResult] = []
    for path, kind in inventory(data_dir):
        if not _lexists(path):
            results.append(PathResult(str(path), kind, False, None, None, "SKIPPED-ABSENT"))
            continue
        if _is_link_or_reparse(path) or not _within_data_root(path, root):
            results.append(PathResult(str(path), kind, True, None, None, "FAILED-link-rejected"))
            continue
        prior_ok = recovery.verify_owner_only(path)
        prior_mode = _describe_mode(path)
        results.append(PathResult(str(path), kind, True, prior_ok, prior_mode, "PENDING"))
    return results


# ---------------------------------------------------------------------------
# Repair
# ---------------------------------------------------------------------------


def _harden_existing(path: Path, kind: str, *, fd: "int | None" = None) -> None:
    """Apply owner-only permissions to an EXISTING dir/file.

    POSIX: `os.chmod` sets the EXACT requested bits (unlike creation-time
    `os.makedirs(mode=...)`/`os.open(mode=...)`, chmod does not consult
    umask at all) -- 0o700 for a directory, 0o600 for a file.

    SEC-001 (MEDIUM, 2026-08-06 Toji audit
    audits/2026-08-06-toji-v9-12-0-release-train-and-remediation.md,
    CWE-59/CWE-367): `fd`, when provided (POSIX only), is an ALREADY-OPEN,
    `os.O_NOFOLLOW`-opened descriptor for `path` -- the SAME descriptor
    `apply_repairs()` also used to re-verify current state immediately
    beforehand. When present, hardening applies `os.fchmod(fd, ...)` to
    that descriptor instead of `os.chmod(path, ...)`, so the object mutated
    is PROVABLY the one just validated, not a fresh pathname resolution
    that a concurrent local actor could have redirected to a different
    (e.g. symlinked) node in the interim. `fd=None` (the default) preserves
    the original pathname-based behavior for every pre-existing caller
    (direct test invocations, and this function's own Windows branch, which
    has no fd-based equivalent available -- see that branch's note below).

    Windows: delegates to the EXISTING `crypto._harden_windows_acl` primitive
    -- the SAME icacls-based, pywin32-free primitive already used for the
    salt sidecar file (crypto.py) and for directory creation-time hardening
    (`recovery.ensure_owner_only_dir`). `kind` is passed through as that
    primitive's `is_dir` parameter (BUG-CORTEXREPAIR-9.12.0-001): a
    directory needs the INHERITABLE `(OI)(CI)F` grant so existing children
    keep receiving an equivalent owner-only ACE via inheritance instead of
    being orphaned with an empty DACL -- see that primitive's docstring for
    the full mechanism writeup. This is still the one shared primitive
    (extended with a parameter), not a new platform code path. That
    primitive is fail-soft (never raises; prints its own stderr warning on
    failure) -- the caller must re-verify via `recovery.verify_owner_only()`
    afterward to detect a silent failure.

    SEC-001 WINDOWS RESIDUAL (accepted, this wave): `icacls` (and the
    `_harden_windows_acl` primitive that shells out to it) is inherently
    PATHNAME-based -- there is no fd/handle-based equivalent reachable
    without a hard `pywin32` dependency (`SetSecurityInfo` against an open
    handle), which this base-path module deliberately avoids requiring (see
    the WINDOWS PRIMITIVE CHOICE note in `recovery.py`). The Windows call
    path in `apply_repairs()` therefore still re-resolves `path` by name
    here, narrowed (not eliminated) by an immediate pre-call re-lstat
    identity check at the call site -- see that call site's own comment
    and the module-level SEC-001 note for the full accepted-residual
    statement. A true handle-bound port is a tracked follow-up, not this
    wave.
    """
    if sys.platform == "win32":  # pragma: no cover - Windows only
        from .crypto import _harden_windows_acl

        _harden_windows_acl(path, is_dir=(kind == "dir"))
    elif fd is not None:
        os.fchmod(fd, 0o700 if kind == "dir" else 0o600)
    else:
        os.chmod(path, 0o700 if kind == "dir" else 0o600)


def _dir_children_orphaned(path: Path) -> bool:
    """Windows-only post-harden safety check for a DIR repair
    (BUG-CORTEXREPAIR-9.12.0-001): confirms existing immediate children were
    not left with an inaccessible (empty/deny-everyone) DACL by the harden
    call. This is a FUNCTIONAL probe (attempt to open/list each immediate
    child), not an ACL-shape check -- it is independent of whether a
    child's own ACL is owner-only, broader, or narrower; an orphaned child
    denies EVERYONE, including this very process/owner, which is exactly
    the failure mode a non-inheritable parent grant produces via Windows'
    automatic-inheritance propagation.

    Only immediate (one-level) children are probed, matching this module's
    existing enumeration depth (`inventory()` never recurses below one
    level either -- see its own docstring).

    POSIX: a parent's chmod never affects children's own permission bits,
    so this always returns False (nothing orphaned) there without doing
    any filesystem work.

    Fails OPEN on enumeration errors (e.g. the directory disappeared between
    harden and this check) -- an inability to enumerate is not itself
    evidence of orphaning, and `apply_repairs()`'s caller already surfaces
    the harden/verify outcome for the parent itself.
    """
    if sys.platform != "win32":  # pragma: no cover - POSIX branch
        return False
    try:
        children = list(path.iterdir())
    except OSError:
        return False
    for child in children:
        try:
            if child.is_dir():
                os.listdir(str(child))
            else:
                with open(child, "rb"):
                    pass
        except OSError:
            return True
    return False


def apply_repairs(
    results: list[PathResult],
    *,
    dry_run: bool = False,
    data_dir: "str | Path | None" = None,
) -> list[PathResult]:
    """Phase 3: process every PENDING result from `scan()`.

    Fail-closed discipline (v9.9.x write_owner_only precedent): a failed
    harden or a failed post-harden verify is reported as FAILED-<reason> and
    processing CONTINUES to the next path -- never silently skipped, and the
    caller (`run_repair()`/the CLI) is responsible for surfacing a non-zero
    exit code when any FAILED-* outcome is present.

    SEC-003 (MEDIUM, 2026-08-06 Toji audit, CWE-59): every PENDING path is
    RE-CHECKED for link/reparse status and data_dir containment here,
    immediately before use -- `scan()`'s classification happened earlier
    and cannot be trusted to still hold; a path can be deleted and replaced
    with a symlink in the window between the two calls (TOCTOU). A path
    that fails this re-check is reported `FAILED-link-rejected` and never
    reaches the harden call, exactly like a path `scan()` rejected outright.

    SEC-001 (MEDIUM, 2026-08-06 Toji release-train audit, CWE-59/CWE-367):
    SEC-003's re-check above was itself followed by two SEPARATE
    pathname-based operations -- verify, then harden -- each re-resolving
    `path` independently, leaving a narrower window open. On POSIX, this is
    now closed: an `os.O_NOFOLLOW`-opened descriptor (captured right after
    the re-check, identity-compared via `st_dev`/`st_ino` against the lstat
    taken at that moment) is used for verification, mutation
    (`os.fchmod` via `_harden_existing(..., fd=...)`), and re-verification --
    ONE bound object, never re-resolved. On Windows, no fd/handle-based
    hardening primitive is available in this codebase's dependency set
    (`icacls` is pathname-based); the window is narrowed via an immediate
    pre-harden re-lstat identity check but not eliminated -- an ACCEPTED
    RESIDUAL for this wave, documented at the call site above.

    `data_dir` -- the containment root for the re-check above. Optional:
    when omitted (pre-SEC-003 call sites, including most of this test
    module's direct `apply_repairs(results, dry_run=...)` calls), the root
    is INFERRED from `results[0].path` -- `scan()`'s own ordering contract
    guarantees `inventory()`'s first entry is always data_dir itself (see
    `test_inventory_includes_data_dir_itself_first`), so this is exact, not
    a guess, for every caller passing `scan()`'s untouched output straight
    through (which is every caller in this codebase). `run_repair()` below
    passes it explicitly rather than relying on the inference.
    """
    root = Path(data_dir) if data_dir is not None else (Path(results[0].path) if results else None)
    final: list[PathResult] = []
    for r in results:
        if r.outcome != "PENDING":
            final.append(r)
            continue
        path = Path(r.path)
        if root is not None and (_is_link_or_reparse(path) or not _within_data_root(path, root)):
            final.append(replace(r, outcome="FAILED-link-rejected", prior_owner_only=None, prior_mode_octal=None))
            continue

        # SEC-001 (MEDIUM, 2026-08-06 Toji audit
        # audits/2026-08-06-toji-v9-12-0-release-train-and-remediation.md,
        # CWE-59/CWE-367): capture an lstat of `path` at the moment it passes
        # the containment/link re-check immediately above. Both platform
        # branches below use this as the "last known good" identity to
        # detect a swap occurring between this point and their own
        # verify/harden/re-verify use.
        try:
            pre_use_lstat = os.lstat(path)
        except OSError:
            final.append(replace(r, outcome="FAILED-link-rejected", prior_owner_only=None, prior_mode_octal=None))
            continue

        if os.name != "nt":
            # POSIX fix: bind validation, mutation, and re-verification to
            # ONE os.O_NOFOLLOW-opened descriptor instead of re-resolving
            # `path` by name for each step (the prior separate
            # recovery.verify_owner_only(path) / _harden_existing(path, kind)
            # / recovery.verify_owner_only(path) sequence each re-resolved
            # the pathname independently, leaving a window after the
            # containment re-check above where the node could be replaced
            # with a link or a different object). O_NOFOLLOW makes a
            # symlinked final path component fail with ELOOP outright; the
            # st_dev/st_ino identity comparison against `pre_use_lstat`
            # additionally catches a same-path object swap that is not
            # itself a symlink (e.g. a delete+recreate race, or an ancestor
            # directory swapped to a symlink between the two lstat/open
            # calls -- O_NOFOLLOW alone only guards the FINAL component).
            open_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            if r.kind == "dir":
                open_flags |= getattr(os, "O_DIRECTORY", 0)
            try:
                fd = os.open(str(path), open_flags)
            except OSError:
                # ELOOP (symlink swapped in since pre_use_lstat) or the node
                # vanished -- never stat/chmod anything; same terminal class
                # as a path scan()/the containment re-check rejected.
                final.append(
                    replace(r, outcome="FAILED-link-rejected", prior_owner_only=None, prior_mode_octal=None)
                )
                continue
            try:
                opened_st = os.fstat(fd)
                if (opened_st.st_dev, opened_st.st_ino) != (pre_use_lstat.st_dev, pre_use_lstat.st_ino):
                    final.append(
                        replace(r, outcome="FAILED-link-rejected", prior_owner_only=None, prior_mode_octal=None)
                    )
                    continue
                if (stat.S_IMODE(opened_st.st_mode) & 0o077) == 0:
                    final.append(replace(r, outcome="ALREADY-OK"))
                    continue
                if dry_run:
                    final.append(replace(r, outcome="WOULD-REPAIR"))
                    continue
                try:
                    _harden_existing(path, r.kind, fd=fd)
                except Exception as exc:  # noqa: BLE001 - reported, never swallowed silently
                    final.append(replace(r, outcome=f"FAILED-harden-error:{exc}"))
                    continue
                verify_st = os.fstat(fd)
                if (stat.S_IMODE(verify_st.st_mode) & 0o077) != 0:
                    final.append(replace(r, outcome="FAILED-verify-after-harden"))
                    continue
            finally:
                os.close(fd)
        else:
            # Windows: no fd/handle-based hardening primitive is available
            # in this codebase's dependency set -- `icacls` (and the
            # `_harden_windows_acl` primitive that shells out to it) is
            # inherently pathname-based; a true handle-bound port
            # (`SetSecurityInfo` against an open handle) needs a hard
            # `pywin32` dependency this base-path module deliberately avoids
            # (see recovery.py's WINDOWS PRIMITIVE CHOICE note). ACCEPTED
            # RESIDUAL, this wave: the window is narrowed, not eliminated --
            # re-lstat immediately before the harden call and reject on any
            # reparse-bit or identity (st_ino/st_dev, where populated) change
            # relative to `pre_use_lstat` above. A replacement occurring
            # strictly between THIS re-lstat and `_harden_existing()`'s own
            # icacls invocation is still possible; a SEPARATE post-harden
            # re-lstat immediately below (Megumi review 2026-08-06, finding 3
            # "cheaper interim" recommendation) DETECTS that narrower race --
            # it does not prevent it (no fd/handle primitive exists on this
            # path) -- by comparing against `narrow_lstat` and reporting
            # FAILED-identity-changed-during-harden instead of REPAIRED on a
            # mismatch, so a won race is surfaced rather than silently
            # certified even if the replacement object happens to also read
            # back as owner-only.
            if recovery.verify_owner_only(path):
                final.append(replace(r, outcome="ALREADY-OK"))
                continue
            if dry_run:
                final.append(replace(r, outcome="WOULD-REPAIR"))
                continue
            try:
                narrow_lstat = os.lstat(path)
            except OSError:
                final.append(
                    replace(r, outcome="FAILED-link-rejected", prior_owner_only=None, prior_mode_octal=None)
                )
                continue
            reparse_before = bool(getattr(pre_use_lstat, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT)
            reparse_now = bool(getattr(narrow_lstat, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT)
            identity_changed = (
                reparse_now
                or reparse_before != reparse_now
                or (narrow_lstat.st_ino, narrow_lstat.st_dev) != (pre_use_lstat.st_ino, pre_use_lstat.st_dev)
            )
            if identity_changed:
                final.append(
                    replace(r, outcome="FAILED-link-rejected", prior_owner_only=None, prior_mode_octal=None)
                )
                continue
            try:
                _harden_existing(path, r.kind)
            except Exception as exc:  # noqa: BLE001 - reported, never swallowed silently
                final.append(replace(r, outcome=f"FAILED-harden-error:{exc}"))
                continue

            # SEC-CORTEXREPAIR-9.12.0-003 (accepted-p3; minted by Gojo on
            # Megumi's documented recommendation, 2026-08-06).
            # `_harden_existing()`'s own icacls invocation just
            # above is a SEPARATE pathname-based mutation -- a node
            # replacement occurring strictly between the pre-harden
            # `narrow_lstat` capture (above) and this call RETURNING is a
            # sub-window the pre-harden re-lstat check cannot see (it runs
            # before the call, not after). This post-harden re-lstat DETECTS
            # that race by comparing against `narrow_lstat`; it does not
            # PREVENT it (no fd/handle-based hardening primitive is
            # available on this path -- see the module-level SEC-001 note).
            # A mismatch is reported as FAILED-identity-changed-during-harden
            # -- never silently certified as REPAIRED -- even if the
            # replacement object happens to also read back as owner-only via
            # `recovery.verify_owner_only()` below.
            try:
                post_harden_lstat = os.lstat(path)
            except OSError:
                final.append(
                    replace(
                        r,
                        outcome="FAILED-identity-changed-during-harden",
                        prior_owner_only=None,
                        prior_mode_octal=None,
                    )
                )
                continue
            reparse_after = bool(getattr(post_harden_lstat, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT)
            identity_changed_during_harden = (
                reparse_after
                or (post_harden_lstat.st_ino, post_harden_lstat.st_dev) != (narrow_lstat.st_ino, narrow_lstat.st_dev)
            )
            if identity_changed_during_harden:
                final.append(
                    replace(
                        r,
                        outcome="FAILED-identity-changed-during-harden",
                        prior_owner_only=None,
                        prior_mode_octal=None,
                    )
                )
                continue

            if not recovery.verify_owner_only(path):
                final.append(replace(r, outcome="FAILED-verify-after-harden"))
                continue

        # BUG-CORTEXREPAIR-9.12.0-001: the target's own re-verify above only
        # proves the TARGET is owner-only -- it says nothing about whether
        # hardening it silently bricked existing children (the historical
        # failure mode: 8/8 REPAIRED reported while children were left with
        # an empty DACL). Child-aware check closes that gap for directories.
        if r.kind == "dir" and _dir_children_orphaned(path):
            final.append(replace(r, outcome="FAILED-children-orphaned"))
            continue
        final.append(replace(r, outcome="REPAIRED"))
    return final


# ---------------------------------------------------------------------------
# Manifest (backup report) -- written BEFORE any mutation
# ---------------------------------------------------------------------------


def write_repair_manifest(data_dir: "str | Path", results: list[PathResult]) -> Path:
    """Write the full PRE-repair snapshot (prior mode/ACL state) to a
    timestamped report inside data_dir, itself owner-only via
    `recovery.write_owner_only` (O_EXCL -- the timestamped filename already
    guarantees no collision). This is the rollback knowledge: once a path is
    chmod'd, its prior mode is not otherwise recoverable.

    Only entries with `existed=True` are included (an absent path has no
    prior state worth recording). Called with the PENDING (pre-apply)
    results from `scan()` -- callers must call this BEFORE `apply_repairs()`
    so the manifest reflects state as observed, not post-mutation.
    """
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    manifest_path = Path(data_dir) / f"repair-perms-{ts}.manifest.json"
    present = [r for r in results if r.existed]
    payload = json.dumps(
        {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data_dir": str(data_dir),
            "issue": "SEC-CORTEXSTOR-9.12.0-001",
            "paths": [
                {
                    "path": r.path,
                    "kind": r.kind,
                    "prior_owner_only": r.prior_owner_only,
                    "prior_mode_octal": r.prior_mode_octal,
                }
                for r in present
            ],
        },
        indent=2,
    ).encode("utf-8")
    recovery.write_owner_only(manifest_path, payload)
    return manifest_path


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_repair(data_dir: "str | Path", *, dry_run: bool = False) -> tuple[list[PathResult], "Path | None"]:
    """Full record -> apply -> verify pipeline (spec-mandated ordering).

    Returns `(results, manifest_path)`. `manifest_path` is None when
    `dry_run=True` (dry-run changes nothing, including not writing a
    manifest file) or when there was nothing present to repair.
    """
    pre = scan(data_dir)
    manifest_path: "Path | None" = None
    if not dry_run and any(r.existed for r in pre):
        manifest_path = write_repair_manifest(data_dir, pre)
    # SEC-003: pass data_dir explicitly rather than relying on
    # apply_repairs()'s results[0]-inference fallback -- this is the one
    # call site that can state the root directly, with no ambiguity.
    final = apply_repairs(pre, dry_run=dry_run, data_dir=data_dir)
    return final, manifest_path
