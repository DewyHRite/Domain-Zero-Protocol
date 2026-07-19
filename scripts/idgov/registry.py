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
    def __init__(self, target, ttl=120, max_attempts=50):
        self.path = pathlib.Path(str(target) + ".lock")
        self.ttl = ttl
        self.max_attempts = max_attempts
        self.token = f"{os.getpid()}-{os.getppid()}"
        self._owned = False  # did THIS context create the lock file?
    def __enter__(self):
        for _ in range(self.max_attempts):
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f"owner={self.token}\n".encode()); os.close(fd)
                self._owned = True
                return self
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
                else:
                    # Unparseable holder content -- fall back to the
                    # original age-based signal (legacy/corrupt lock only).
                    try:
                        is_stale = (time.time() - self.path.stat().st_mtime) > self.ttl
                    except FileNotFoundError:
                        continue
                if not is_stale:
                    time.sleep(0.1)
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
        raise TimeoutError(f"could not acquire {self.path}")
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


def append(path, event: dict) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with Lock(p):
        _backup_before_append(p)
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
            f.flush(); os.fsync(f.fileno())
