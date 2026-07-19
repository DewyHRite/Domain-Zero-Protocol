#!/usr/bin/env python3
"""FEAT-IDGOV-001 registry I/O — append-only JSONL event ledger. Latest-rev per id
is authoritative. read/project here; writes go through append()."""
import json, pathlib, os, time

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


class Lock:
    def __init__(self, target, ttl=30):
        self.path = pathlib.Path(str(target) + ".lock")
        self.ttl = ttl
        self.token = f"{os.getpid()}-{os.getppid()}"
        self._owned = False  # did THIS context create the lock file?
    def __enter__(self):
        for _ in range(50):
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f"owner={self.token}\n".encode()); os.close(fd)
                self._owned = True
                return self
            except FileExistsError:
                # Reentrant: if the existing lock is OURS, treat as already-held.
                try:
                    holder = self.path.read_text(encoding="utf-8").strip()
                except FileNotFoundError:
                    continue
                if holder == f"owner={self.token}":
                    self._owned = False
                    return self
                if self.path.exists() and (time.time() - self.path.stat().st_mtime) > self.ttl:
                    try: self.path.unlink()
                    except FileNotFoundError: pass
                    continue
                time.sleep(0.1)
        raise TimeoutError(f"could not acquire {self.path}")
    def __exit__(self, *a):
        if self._owned:  # only the creator removes it
            try:
                # Re-read before unlink: if our lock was TTL-reaped and
                # re-acquired by another process while we held it, the
                # on-disk holder is no longer ours -- do NOT delete it.
                if self.path.read_text(encoding="utf-8").strip() == f"owner={self.token}":
                    self.path.unlink()
            except FileNotFoundError:
                pass

def append(path, event: dict) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with Lock(p):
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
            f.flush(); os.fsync(f.fileno())
