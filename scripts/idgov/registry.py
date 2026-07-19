#!/usr/bin/env python3
"""FEAT-IDGOV-001 registry I/O — append-only JSONL event ledger. Latest-rev per id
is authoritative. read/project here; writes go through append()."""
import json, pathlib, os, sys, time, shutil

SCHEMA_VERSION = 1

# SEC-IDGOV-F-002 (P1): single source of the sentinel `attested_writer` value
# a legacy=True backfill row MUST carry (engine.validate() enforces this
# positively; scripts/backfill_issue_registry.py imports this same constant
# instead of a locally-duplicated literal, so the two can never drift apart).
LEGACY_ATTESTED_WRITER = "backfill"

def read_events(path) -> list:
    p = pathlib.Path(path)
    if not p.exists():
        return []
    out = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{p}:{i}: invalid JSONL: {e}")
    return out

def project_latest(events) -> dict:
    # Cumulative merge in file order (order matches ascending rev under the lock):
    # a `transition` event carries only state/rev/writer fields, so a naive
    # highest-rev-wins replace would drop family/subsystem/title/origin/etc.
    # set only by the original `assign`. Merging preserves them.
    latest = {}
    for ev in events:
        eid = ev["id"]
        merged = dict(latest.get(eid, {}))
        merged.update(ev)
        latest[eid] = merged
    return latest

def all_ids(events) -> set:
    return {ev["id"] for ev in events}

def max_seq(events, key_tuple) -> int:
    fam, sub, ver, tag = key_tuple
    best = 0
    for ev in events:
        if ev.get("event") != "assign":
            continue
        if (ev.get("family"), ev.get("subsystem"), ev.get("version"), ev.get("tag")) == (fam, sub, ver, tag):
            best = max(best, int(ev.get("seq", 0)))
    return best

def max_rev(events, id_) -> int:
    return max((int(ev.get("rev", 0)) for ev in events if ev.get("id") == id_), default=0)


def _pid_alive(pid) -> bool:
    """Best-effort liveness check, no external deps (psutil-free per design).
    Returns True if `pid` looks like a live process, False if it is
    confirmed dead. A malformed/non-positive pid is treated as dead (never
    blocks a reap on garbage input)."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        import ctypes.wintypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if not handle:
            # CodeRabbit PR#112 Round 2 (#1): OpenProcess can fail with
            # ERROR_ACCESS_DENIED for a LIVE process owned by another
            # account/token (a dead/nonexistent pid never produces
            # ACCESS_DENIED -- it produces ERROR_INVALID_PARAMETER). Treating
            # every OpenProcess failure as "dead" misclassified a live
            # foreign-account holder as dead and reaped its lock, violating
            # this class's own "a live recorded owner is NEVER reaped"
            # invariant (finding 13). ACCESS_DENIED is proof of EXISTENCE
            # (the OS found a process to deny us), so treat it as
            # alive/indeterminate and err on the side of NOT reaping. Any
            # other failure (e.g. ERROR_INVALID_PARAMETER=87 -- no such pid)
            # means the process genuinely does not exist.
            ERROR_ACCESS_DENIED = 5
            if ctypes.GetLastError() == ERROR_ACCESS_DENIED:
                return True
            return False
        try:
            # A terminated process's handle can remain openable as long as
            # ANY reference to it exists (e.g. an un-closed subprocess.Popen
            # handle in this same process) -- OpenProcess succeeding is NOT
            # sufficient proof of liveness on Windows. GetExitCodeProcess
            # returning something other than STILL_ACTIVE means it has
            # actually exited despite the handle still being valid.
            exit_code = ctypes.wintypes.DWORD()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(
                handle, ctypes.byref(exit_code)
            )
            if not ok:
                return False
            return exit_code.value == STILL_ACTIVE
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    else:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # exists, just owned by another user
        except OSError:
            return False
        return True


def _parse_holder_pid(holder: str):
    """Extract the pid component from a lock holder string 'owner=<pid>-<ppid>'.
    Returns None for a missing/malformed/non-numeric pid (legacy or corrupt
    lock content) -- callers fall back to age-based reaping for that case
    only, preserving test_stale_lock_reclaimed's pre-existing contract for a
    non-pid holder like 'owner=ghost'."""
    if not holder.startswith("owner="):
        return None
    tok = holder[len("owner="):]
    pid_str = tok.split("-", 1)[0]
    try:
        return int(pid_str)
    except ValueError:
        return None


class Lock:
    # CRITICAL (CodeRabbit PR#112 finding 13, CWE-362): pure age-based
    # reaping treated ANY lock older than `ttl` as abandoned, even one held
    # by a genuinely live, still-working process (a valid mint/backfill
    # operation lasting >30s). Combined with a stat()-then-unlink() TOCTOU
    # window, two processes could both end up believing they held the same
    # lock. Fix: reap is now PID-liveness-gated (a live recorded owner is
    # NEVER reaped, however old the lock file is) with age used only as a
    # fallback for a lock whose holder pid can't be parsed (legacy/corrupt
    # content); and the reap itself is one atomic os.replace() (no unlink
    # step at all), with a post-replace re-read to detect -- and yield to --
    # a concurrent reaper that won the same race.
    # CodeRabbit PR#112 Round 2 (#3): the retry budget is now DERIVED from
    # ttl (sleep_interval-scaled) instead of a fixed 50-attempts/~5s
    # constant that was decoupled from ttl -- a batch operation (e.g.
    # backfill's run_backfill, which holds this Lock across a whole
    # multi-file scan+append) can legitimately run for up to `ttl` seconds
    # (or longer, while remaining alive and correctly un-reaped per finding
    # 13's liveness gate) without a concurrent Lock attempt spuriously
    # giving up. An explicit max_attempts always wins outright (e.g. tests
    # wanting a fast, deterministic TimeoutError against a still-alive
    # holder should pass an explicit small value, not rely on ttl).
    #
    # v9.10.1 Block C (Megumi Tier-3 review of the above, two residuals):
    #
    # C1 (P2) -- two-reaper race window: the reap above is two separate
    # syscalls (os.replace() then a re-read), not one atomic compare-and-
    # swap. A second, independently-racing reaper can land its own
    # os.replace() AFTER a first reaper's replace+re-read already returned
    # "owned", silently overwriting the on-disk holder out from under it.
    # The first reaper's NEXT append()-time Lock() call correctly detects
    # the foreign holder (via the reentrant-holder check above) and waits --
    # but by the time it eventually re-acquires (legitimately, once the
    # second reaper releases), its OUTER caller (engine.mint()/
    # transition()) already computed its event from an events snapshot that
    # predates whatever the second reaper committed in the interim.
    # Evaluated both suggested fixes: (a) a true OS advisory lock (fcntl/
    # msvcrt/LockFileEx) would close the acquisition-level race itself, but
    # adds a platform-specific dependency for marginal benefit over (b); (b)
    # -- CHOSEN -- re-validate the event's structural invariants against a
    # FRESH read taken inside append()'s own held lock, immediately before
    # the write, raising the new retryable ConflictError on a mismatch. (b)
    # is smaller, fully platform-safe, and protects the actual invariant
    # that matters (what lands in the ledger) regardless of exactly how any
    # given Lock() acquisition raced to get there. See append() /
    # _validate_fresh_before_write() below and
    # tests/test_issue_id_registry.py's "C1" test block.
    #
    # C2 (P3) -- PID-recycle reap starvation + no manual unlock:
    # _parse_holder_pid() only recovers the pid half of `owner=<pid>-<ppid>`
    # (ppid discarded); if the OS recycles that pid number onto an unrelated
    # live process after the true holder exits, _pid_alive() reports "alive"
    # forever and the lock becomes permanently unreapable (the ttl
    # age-based fallback only fires for an UNPARSEABLE holder, not this
    # case). Suggested fix (1) -- cross-checking the recorded ppid against
    # the live pid's ACTUAL current parent -- is NOT implemented: on POSIX
    # this needs /proc (absent on macOS) and on Windows it needs a
    # CreateToolhelp32Snapshot walk via ctypes, both materially heavier than
    # this class's existing dependency-free design for a P3 residual;
    # ACCEPTED as a documented residual. Implemented instead: (2) a hard age
    # backstop, `_STARVATION_TTL_MULTIPLIER` (10x ttl), that overrides even
    # a "confirmed alive" liveness claim once a lock has been held far
    # longer than any legitimate operation on this registry ever runs (a
    # single mint()/transition() completes in milliseconds; the largest
    # legitimate batch, run_backfill's whole-batch hold, completes in well
    # under a second for hundreds of rows) -- 10x is generous enough to
    # never fire on a genuinely slow-but-real operation while still being a
    # bounded, finite backstop against permanent starvation; and (3) an
    # explicit, human-invoked break-glass, force_break() (below), for the
    # rare case neither (2) nor the ttl multiplier have caught yet -- its
    # exact invocation is also printed in the TimeoutError message raised at
    # the end of __enter__.
    _RETRY_SLEEP_S = 0.1
    _MIN_ATTEMPTS_FLOOR = 50  # sane floor for a very small/zero ttl
    _STARVATION_TTL_MULTIPLIER = 10  # C2 fix (2): hard age backstop multiplier

    def __init__(self, target, ttl=120, max_attempts=None):
        self.path = pathlib.Path(str(target) + ".lock")
        self.ttl = ttl
        if max_attempts is not None:
            self.max_attempts = max_attempts
        else:
            self.max_attempts = max(
                self._MIN_ATTEMPTS_FLOOR, int(ttl / self._RETRY_SLEEP_S) + 1
            )
        self.token = f"{os.getpid()}-{os.getppid()}"
        self._owned = False  # did THIS context create the lock file?
    def __enter__(self):
        for _ in range(self.max_attempts):
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                try:
                    holder = self.path.read_text(encoding="utf-8").strip()
                except FileNotFoundError:
                    continue  # raced with a concurrent release; just retry
                # Reentrant: if the existing lock is OURS, treat as already-held.
                if holder == f"owner={self.token}":
                    self._owned = False
                    return self
                holder_pid = _parse_holder_pid(holder)
                if holder_pid is not None:
                    is_stale = not _pid_alive(holder_pid)
                    if not is_stale:
                        # C2 fix (2): PID-recycle starvation backstop. A
                        # recorded pid that liveness-checks as "alive" might
                        # actually be a DIFFERENT process the OS recycled the
                        # pid number to, long after the true holder exited
                        # (see the class docstring's C2 rationale -- a full
                        # ppid-mismatch cross-check, item (1), is an
                        # accepted, documented residual). A lock held for
                        # far longer than any legitimate operation on this
                        # registry ever runs -- _STARVATION_TTL_MULTIPLIER
                        # (10x) times ttl -- is therefore treated as
                        # abandoned regardless of the liveness claim.
                        try:
                            age = time.time() - self.path.stat().st_mtime
                        except FileNotFoundError:
                            continue
                        is_stale = age > (self.ttl * self._STARVATION_TTL_MULTIPLIER)
                else:
                    # Unparseable holder content -- fall back to the
                    # original age-based signal (legacy/corrupt lock only).
                    try:
                        is_stale = (time.time() - self.path.stat().st_mtime) > self.ttl
                    except FileNotFoundError:
                        continue
                if not is_stale:
                    time.sleep(self._RETRY_SLEEP_S)
                    continue
                # Atomic reap: write our claim to a temp file, then
                # os.replace() it over the stale lock in ONE syscall -- no
                # unlink()/recreate gap for another process to slip into.
                tmp = self.path.with_name(f"{self.path.name}.tmp{os.getpid()}.{time.time_ns()}")
                try:
                    tfd = os.open(str(tmp), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.write(tfd, f"owner={self.token}\n".encode()); os.close(tfd)
                    os.replace(str(tmp), str(self.path))
                except OSError:
                    try: tmp.unlink()
                    except FileNotFoundError: pass
                    continue
                # Verify we actually ended up as the owner -- another
                # reaper's os.replace() may have landed after ours.
                try:
                    reread = self.path.read_text(encoding="utf-8").strip()
                except FileNotFoundError:
                    continue
                if reread == f"owner={self.token}":
                    self._owned = True
                    return self
                continue  # lost the race; retry from the top
            else:
                # CodeRabbit PR#112 Round 2 (#2): os.open() succeeded (we own
                # a freshly-created, empty lock file) but the write/close
                # itself previously had no try/finally -- an OSError from
                # os.write (e.g. disk full) would leak `fd` AND leave a
                # partially-written, UNOWNED lock file behind that only
                # self-healed via the age-based TTL fallback (irrelevant now
                # that reaping is PID-liveness-gated -- an unparseable/empty
                # holder falls back to age, but that could still be a long
                # wait). Close is now guaranteed via try/finally, and on a
                # write failure the just-created lock is best-effort unlinked
                # before the error propagates, so a disk-full mid-acquire
                # doesn't leave a lingering phantom lock at all.
                try:
                    try:
                        os.write(fd, f"owner={self.token}\n".encode())
                    finally:
                        os.close(fd)
                except OSError:
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    raise
                self._owned = True
                return self
        # C2 fix (3): a bare "could not acquire" message gave a human
        # operator nothing to act on. Surface WHO (self-reported) currently
        # holds it, SINCE WHEN, and the exact break-glass invocation to use
        # once independently confirmed abandoned (e.g. a PID-recycle case
        # neither the liveness check nor the starvation backstop above have
        # caught yet).
        try:
            holder_text = self.path.read_text(encoding="utf-8").strip()
        except OSError:
            holder_text = "<unreadable>"
        try:
            held_since = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.path.stat().st_mtime)
            )
        except OSError:
            held_since = "<unknown>"
        raise TimeoutError(
            f"could not acquire {self.path} after {self.max_attempts} attempts "
            f"(currently held by {holder_text!r} since {held_since}); if you have "
            f"independently confirmed this holder is abandoned (e.g. a "
            f"PID-recycle case the liveness check + "
            f"{self._STARVATION_TTL_MULTIPLIER}x-ttl starvation backstop "
            f"haven't caught yet), break it manually: "
            f"python -c \"from scripts.idgov.registry import Lock; "
            f"Lock.force_break(r'{self.path}')\""
        )
    def __exit__(self, *a):
        if self._owned:  # only the creator removes it
            try:
                # Re-read before unlink: if our lock was reaped and
                # re-acquired by another process while we held it, the
                # on-disk holder is no longer ours -- do NOT delete it.
                if self.path.read_text(encoding="utf-8").strip() == f"owner={self.token}":
                    self.path.unlink()
            except FileNotFoundError:
                pass

    @staticmethod
    def force_break(lock_file_path) -> bool:
        """C2 fix (3): manual break-glass removal of an abandoned lock file,
        for a human operator who has INDEPENDENTLY confirmed the recorded
        holder is dead (e.g. a PID-recycle case the automatic liveness check
        and the starvation backstop above haven't caught yet). Deliberately
        NOT part of any automatic path -- only ever invoked explicitly by a
        human (the TimeoutError raised at the end of __enter__ prints the
        exact invocation to use).

        Accepts the LOCK FILE path itself (the same value shown in that
        message / held at `Lock(...).path`), not the underlying registry
        target path -- avoids the ambiguity of re-deriving the ".lock"
        suffix from a caller-supplied target.

        Returns True if a lock file was present and removed, False if there
        was nothing to remove (already clear)."""
        p = pathlib.Path(lock_file_path)
        try:
            holder = p.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return False
        try:
            p.unlink()
        except FileNotFoundError:
            return False
        print(f"[idgov:registry] force_break: manually removed lock {p} "
              f"(was held by {holder!r})", file=sys.stderr)
        return True

# Finding 14 (CodeRabbit PR#112, P2): append() previously wrote directly
# with no pre-op backup or rollback path. Routing this through
# ProjectStateManager (as literally suggested) is architecturally wrong --
# PSM owns a small FIXED set of namespaced JSON *state* dicts under
# read-modify-write + full-file-lock semantics; this registry is an
# append-only JSONL EVENT LEDGER with its own dedicated Lock (finding 13,
# above) and its own FEAT-GUARD-001 byte-prefix append-only guard once
# committed -- git history is the durable rollback path for anything
# already committed. What was actually missing is protection for
# UNCOMMITTED in-progress work (e.g. a mid-backfill crash corrupting the
# last partially-written line). A lightweight, RATE-LIMITED timestamped
# backup closes that gap without the O(rows) I/O cost a naive
# backup-before-every-row would add during a several-hundred-row backfill
# burst (all appends in one such burst land inside the SAME
# _BACKUP_MIN_INTERVAL_S window, so only the first one actually copies).
_BACKUP_MIN_INTERVAL_S = 5.0
_BACKUP_RETENTION = 20


def _backup_before_append(path: pathlib.Path) -> None:
    """Best-effort, rate-limited timestamped backup of the registry file,
    taken immediately before an append. Never raises -- a backup failure
    must not block the append itself (the ledger's own durability comes
    from fsync + eventual git commit, not this convenience copy)."""
    try:
        if not path.exists() or path.stat().st_size == 0:
            return  # nothing to protect yet
        backup_dir = path.parent / "backups" / "issue-registry"
        backup_dir.mkdir(parents=True, exist_ok=True)
        existing = sorted(backup_dir.glob(f"{path.name}_*.jsonl"))
        if existing:
            last_mtime = existing[-1].stat().st_mtime
            if (time.time() - last_mtime) < _BACKUP_MIN_INTERVAL_S:
                return  # a recent backup already covers this burst
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        dest = backup_dir / f"{path.name}_{ts}_{os.getpid()}.jsonl"
        shutil.copy2(str(path), str(dest))
        stale = sorted(backup_dir.glob(f"{path.name}_*.jsonl"))
        for f in stale[:-_BACKUP_RETENTION]:
            try: f.unlink()
            except OSError: pass
    except OSError as e:
        print(f"[idgov:registry] WARNING: pre-append backup of {path} failed "
              f"(continuing without it): {e}", file=sys.stderr)


class ConflictError(Exception):
    """C1 fix (b): raised by append() when a FRESH re-read of the ledger,
    taken immediately before the write while genuinely holding the lock,
    shows the caller's event conflicts with a row committed by a DIFFERENT
    writer since the caller's own (possibly stale) outer events-snapshot was
    taken -- e.g. a two-reaper race (see Lock's class docstring, C1) where a
    caller's snapshot predates a concurrent writer's legitimate commit.

    RETRYABLE: this signals the caller's decision was made from stale data,
    not a permanent failure. A caller (e.g. idgov.engine.mint()/
    transition()) should re-read fresh state, recompute its event, and
    retry the whole read-decide-append cycle rather than treat this as fatal.
    """


class DuplicateIdConflictError(ConflictError):
    """P2-a (Megumi Tier-3 bundle review, v9.10.1): raised specifically by
    _validate_fresh_before_write() for the duplicate-id assign conflict —
    another writer already committed a row with the EXACT id string this
    caller just tried to assign. This is the one NON-retryable ConflictError
    case (engine.mint() must fail fast, never burn its retry budget on it);
    every other ConflictError (stale seq / stale rev) remains a plain,
    RETRYABLE ConflictError.

    Before this subclass existed, engine.mint() distinguished the two cases
    by substring-matching the exception's MESSAGE text
    (`"already assigned" in str(exc)`) — brittle: any future rewording of
    the message (even one that keeps the same meaning) would silently
    misclassify a genuine duplicate-id conflict as retryable, burning the
    retry budget and surfacing a confusing generic timeout instead of the
    correct fail-fast RuntimeError. Callers must now branch on
    `isinstance(exc, DuplicateIdConflictError)`, which survives any
    rewording of the message.
    """


def _validate_fresh_before_write(path: pathlib.Path, event: dict) -> None:
    """C1 fix (b) (two-reaper race window, Megumi Tier-3 review P2): re-
    validate the event's structural invariants against a FRESH read of the
    ledger taken INSIDE append()'s held lock, immediately before the write.
    Closes the window where an outer caller's events-snapshot (read before
    it definitively/exclusively held the lock across a reap race -- see
    Lock's class docstring) could be stale relative to a write legitimately
    committed by a different writer in the interim.

    Only checks invariants registry.py itself already owns:
      - assign: no duplicate id; and, ONLY when the event actually carries a
        `seq` (i.e. is not None -- a legacy=True backfill row always sets
        seq=None and a raw/low-level caller that omits the field entirely
        also reads as None via .get(), both deliberately exempt), the seq is
        still the NEXT value for its (family, subsystem, version, tag)
        counter key.
      - transition: rev is still the NEXT value for its id.
    Policy-level checks (writer authority, transition legality, grammar)
    remain idgov.engine.py's job on the caller's NEXT (fresh) attempt after
    catching ConflictError -- this function never duplicates them.
    """
    fresh = read_events(path)
    etype = event.get("event")
    eid = event.get("id")
    if etype == "assign":
        if eid in all_ids(fresh):
            # P2-a: this specific branch raises the DuplicateIdConflictError
            # subclass (not a plain ConflictError) so callers can classify it
            # by TYPE, never by parsing this message string.
            raise DuplicateIdConflictError(
                f"stale snapshot: {eid} was already assigned by another "
                f"writer since this event was decided"
            )
        seq = event.get("seq")
        if seq is not None:
            key = (event.get("family"), event.get("subsystem"),
                   event.get("version"), event.get("tag"))
            expected_seq = max_seq(fresh, key) + 1
            if seq != expected_seq:
                raise ConflictError(
                    f"stale snapshot: seq {seq!r} for counter key {key} is no "
                    f"longer the next value (expected {expected_seq}) -- "
                    f"another writer minted in this key concurrently"
                )
    elif etype == "transition":
        rev = event.get("rev")
        expected_rev = max_rev(fresh, eid) + 1
        if rev != expected_rev:
            raise ConflictError(
                f"stale snapshot: rev {rev!r} for {eid} is no longer the "
                f"next value (expected {expected_rev}) -- another writer "
                f"transitioned it concurrently"
            )
    # unknown event types are not structurally checked here (schema/policy
    # validation is idgov.engine.validate()'s job on the committed ledger).


def append(path, event: dict) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with Lock(p):
        _validate_fresh_before_write(p, event)
        _backup_before_append(p)
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
            f.flush(); os.fsync(f.fileno())
