#!/usr/bin/env python3
"""FEAT-PAYLOAD-9.10.2-001 -- DZP release-payload consumer verifier.

Verifies a downloaded ``dzp-payload-vX.Y.Z.zip`` + its sibling
``dzp-payload-vX.Y.Z.manifest.json`` (both GitHub Release assets) BEFORE you
install them, per ``docs/guides/DISTRO_RELEASE_WORKFLOW.md`` Section 9.

STDLIB ONLY (hashlib, zipfile, json, subprocess, argparse, pathlib) -- this
script is meant to be the FIRST thing you run against a fresh download, before
any DZP install exists, and before any third-party package is installed.

Fail-CLOSED check order:
  1. Manifest schema -- required keys present with the expected shapes.
  2. `payload_sha256` -- must match the actual sha256 of the downloaded zip
     file on disk (catches a zip that was swapped/corrupted after upload).
  3. Embedded-vs-external manifest consistency -- the manifest bundled
     INSIDE the zip must be byte-identical to the external sibling manifest
     you downloaded (catches a mismatched pair).
  4. `verifier_sha256` -- must match the sha256 of the EXACT
     `scripts/verify-payload.py` bytes packaged inside THIS zip (a
     deterministic, redundant integrity anchor for the verifier file itself
     -- see the module docstring in `scripts/distro/dzp_payload.py` for why
     this is checked against the SHIPPED copy, never the copy currently
     executing on your machine).
  5. Per-file integrity -- every file the manifest declares must be present
     in the zip with a matching sha256/size; the zip must not contain any
     file the manifest doesn't declare (no undeclared/extra content).
  6. Canonical-origin PINNING + cross-check -- the manifest's
     `canonical_repo_url` is first validated against a HARDCODED constant
     (`CANONICAL_REPO_URL` below, matching `dzp_payload.py`'s own
     `DEFAULT_CANONICAL_URL` byte-for-byte) BEFORE any network call is made;
     a mismatch fails closed (exit 9) unless an explicit, loud
     `--allow-alternate-origin URL` opt-in is given that matches the
     manifest's own declared URL exactly (for genuine, deliberately-trusted
     forks/mirrors -- never a workaround for an unexpected origin). Only
     once the URL is confirmed pinned (or explicitly authorized) does
     `git ls-remote` run: the manifest's recorded `release_branch` must
     resolve, on that repo, to the manifest's recorded `source_commit`. A tag
     ref (`refs/tags/<release_branch>`) is authoritative over a branch ref
     (`refs/heads/<release_branch>`) when both exist, because tags are
     conventionally treated as immutable once published. The whole step
     (pinning check + ls-remote) is skippable via `--skip-origin-check`
     (LOUD warning, offline use only -- never the default).

Exit codes:
  0  all requested checks passed (including a `--skip-origin-check` run).
  1  manifest schema invalid / unreadable.
  2  `payload_sha256` mismatch -- the zip file itself does not match its
     recorded hash.
  3  per-file content mismatch: a declared file's hash/size differs, a
     declared file is missing from the zip, an undeclared file is present in
     the zip, or the embedded-vs-external manifest copies disagree.
  4  `verifier_sha256` mismatch -- the shipped `verify-payload.py` inside
     this zip does not match its manifest-recorded hash.
  5  canonical-origin cross-check FAILED: the recorded commit could not be
     confirmed at the recorded ref on the canonical repo.
  6  canonical-origin cross-check could not EXECUTE (git missing, network
     failure, etc.) and `--skip-origin-check` was NOT given. Distinct from 5
     (a real, confirmed mismatch) -- mirrors the execution-failure-vs-
     genuine-finding split used throughout this codebase's other guards
     (e.g. `dzp_publish_core.DirtyGuardExecutionError`).
  7  `--deep-verify` requested and the cloned canonical commit's file
     contents differ from what the zip actually contains (see below).
  8  the zip looks like a zip-bomb / has an unsafe entry (path traversal,
     symlink, absolute path, or the uncompressed size/entry-count exceeds
     the safety caps, INCLUDING a running cap enforced against bytes
     actually produced while streaming/hashing/extracting, independent of
     whatever the zip's own declared metadata claims) -- refused before any
     extraction is attempted.
  9  canonical-origin PINNING mismatch -- the manifest's `canonical_repo_url`
     does not match the hardcoded `CANONICAL_REPO_URL` constant (nor an
     explicitly-authorized `--allow-alternate-origin`). Distinct from 5 (a
     confirmed ls-remote mismatch): this fires BEFORE any network call is
     made, because the URL itself is self-attested manifest content and
     cannot be trusted as the ls-remote target without first being pinned.

Threat-model notes (read before relying on this tool for anything beyond
"is this download internally consistent and does it point somewhere real"):

  - The canonical-origin cross-check is only as trustworthy as the URL it
    resolves against. `manifest['canonical_repo_url']` is READ FROM THE SAME
    manifest under verification -- an attacker distributing a self-consistent
    forged zip+manifest pair could otherwise point that field at their own
    repo and have every check, including the origin cross-check, report
    PASS. This is why `CANONICAL_REPO_URL` below is a HARDCODED constant,
    validated (with documented trailing-slash / `.git`-suffix normalization)
    against the manifest's claim BEFORE any `ls-remote` call is made; a
    mismatch fails closed (exit 9) unless `--allow-alternate-origin` is
    explicitly, loudly passed and matches the manifest's own URL exactly.
  - `git ls-remote` over HTTPS confirms the recorded commit is REACHABLE on
    the (now-pinned/authorized) canonical repo's named ref. It is NOT a
    content-safety guarantee: it cannot detect that the canonical repo itself
    was compromised, nor that a maintainer with legitimate push access
    shipped something malicious. This tool's trust boundary is IDENTICAL to
    `git clone`-ing the canonical URL directly -- it is a supply-chain
    CONSISTENCY check, not a code-review substitute.
  - The default (non-`--deep-verify`) mode does NOT cryptographically bind
    the zip's file bytes to the canonical commit's git tree -- a plain
    sha256 of a file's raw bytes is not the same value as that file's git
    blob hash (git hashes `blob <len>\\0<content>`). `--deep-verify`
    (network + a real shallow clone of the canonical repo at the recorded
    ref) closes this gap by directly byte-comparing every manifest file
    against the corresponding file in that clone. This is opt-in (cost:
    bandwidth + time), never the default.
  - TOCTOU between "verify" and "install": if you verify this zip now and
    install from a COPY or a LATER re-read of the same path, the file on
    disk could have been swapped in between. Use `--extract-to DIR` so
    extraction happens in the SAME process, immediately after every
    requested check has already passed -- never re-open/trust the zip path
    again after this script exits. Verifying now and installing later from a
    relocated/copied file reintroduces the exact race this flag exists to
    close.
  - Extraction (`--extract-to`) is zip-slip-hardened: every entry's resolved
    path is required to stay under the destination directory (rejects `..`
    components, absolute paths, and Windows drive-letter paths); symlink
    entries are rejected outright; total uncompressed size and entry count
    are capped (zip-bomb defense-in-depth) before any bytes are written.
    This defends against a maliciously crafted file merely CLAIMING to be a
    DZP payload, independent of whatever the manifest says.

Usage::

    python scripts/verify-payload.py dzp-payload-v9.10.2.zip
    python scripts/verify-payload.py dzp-payload-v9.10.2.zip --extract-to ./dzp-install
    python scripts/verify-payload.py dzp-payload-v9.10.2.zip --skip-origin-check   # offline, LOUD warning
    python scripts/verify-payload.py dzp-payload-v9.10.2.zip --deep-verify         # strongest check, needs network+git
    python scripts/verify-payload.py dzp-payload-v9.10.2.zip \\
        --allow-alternate-origin https://github.com/some-org/dzp-fork   # explicit, loud, trusted-fork opt-in only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REQUIRED_MANIFEST_KEYS = (
    "schema_version", "protocol_version", "canonical_repo_url", "release_branch",
    "source_commit", "files", "payload_sha256", "verifier_path", "verifier_sha256",
)

MAX_TOTAL_UNCOMPRESSED_BYTES = 2 * 1024 ** 3  # 2 GiB safety cap (zip-bomb defense-in-depth)
MAX_ENTRIES = 200_000
_READ_CHUNK_SIZE = 1 << 20  # 1 MiB -- bounds how much any single decompression call produces

# SEC-PAYLOAD-9.10.2-001: the ONE canonical repo this tool will ever trust for
# the origin cross-check, HARDCODED -- never read from the manifest under
# verification. MUST match scripts/distro/dzp_payload.py's own
# DEFAULT_CANONICAL_URL byte-for-byte (a repo-wide test asserts this).
CANONICAL_REPO_URL = "https://github.com/DewyHRite/Domain-Zero-Protocol"


class VerifyError(Exception):
    """Carries the intended process exit code alongside a human message."""

    def __init__(self, code: int, message: str):
        self.code = code
        super().__init__(message)


def _normalize_repo_url(url: str) -> str:
    """Normalize a repo URL for equivalence comparison against
    `CANONICAL_REPO_URL`. Strips surrounding whitespace, any number of
    trailing slashes, and (after that) a single trailing `.git` suffix --
    then strips any trailing slash left behind by removing `.git` (handles
    a `.../Domain-Zero-Protocol.git/` style URL too). These forms are all
    semantically the SAME git remote and must be treated as equivalent:
    'https://github.com/OWNER/REPO', '.../REPO/', and '.../REPO.git' are not
    meaningfully different origins. Case is preserved -- GitHub owner/repo
    path segments ARE case-sensitive in practice, unlike hostnames."""
    normalized = url.strip()
    while normalized.endswith("/"):
        normalized = normalized[:-1]
    if normalized.endswith(".git"):
        normalized = normalized[: -len(".git")]
    while normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized


class _DecompressionBudget:
    """Tracks ACTUAL decompressed bytes produced while streaming zip entries,
    counted as data comes out of the decompressor -- independent of
    attacker-declared `ZipInfo.file_size`/central-directory metadata
    (SEC-PAYLOAD-9.10.2-002). Only bytes that have genuinely been read count
    toward the safety cap enforced here, so this check cannot be satisfied
    by metadata alone."""

    def __init__(self, cap: int):
        self.cap = cap
        self.consumed = 0

    def consume(self, n: int, context: str) -> None:
        self.consumed += n
        if self.consumed > self.cap:
            raise VerifyError(
                8,
                f"decompressed byte cap exceeded while reading {context!r} -- "
                f"{self.consumed} actual bytes produced so far, exceeding the safety "
                f"cap ({self.cap} bytes). Refusing (zip-bomb defense: measured against "
                "bytes ACTUALLY decompressed, not declared zip metadata).",
            )


def _hash_zip_entry_capped(zf: zipfile.ZipFile, arcname: str, budget: "_DecompressionBudget") -> tuple:
    """Stream-hash a zip entry's decompressed bytes in bounded chunks,
    enforcing `budget` against each chunk as it comes out of the
    decompressor. Returns (sha256_hex, actual_size)."""
    h = hashlib.sha256()
    size = 0
    with zf.open(arcname) as fh:
        while True:
            chunk = fh.read(_READ_CHUNK_SIZE)
            if not chunk:
                break
            budget.consume(len(chunk), arcname)
            size += len(chunk)
            h.update(chunk)
    return h.hexdigest(), size


def _copy_zip_entry_capped(src, out, budget: "_DecompressionBudget", context: str) -> None:
    """Copy an already-open zip entry stream to `out` in bounded chunks,
    enforcing `budget` against each chunk as it is produced -- the
    extraction-side counterpart to `_hash_zip_entry_capped`."""
    while True:
        chunk = src.read(_READ_CHUNK_SIZE)
        if not chunk:
            break
        budget.consume(len(chunk), context)
        out.write(chunk)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(manifest_path: Path) -> dict:
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise VerifyError(1, f"could not read/parse manifest {manifest_path}: {exc}") from exc
    validate_manifest_schema(data)
    return data


def validate_manifest_schema(data: dict) -> None:
    if not isinstance(data, dict):
        raise VerifyError(1, "manifest is not a JSON object")
    missing = [k for k in REQUIRED_MANIFEST_KEYS if k not in data]
    if missing:
        raise VerifyError(1, f"manifest missing required key(s): {', '.join(missing)}")
    if not isinstance(data["files"], list) or not data["files"]:
        raise VerifyError(1, "manifest 'files' must be a non-empty list")
    for i, entry in enumerate(data["files"]):
        if not isinstance(entry, dict) or not {"path", "sha256", "size"} <= entry.keys():
            raise VerifyError(1, f"manifest 'files[{i}]' missing path/sha256/size")
    for key in ("protocol_version", "canonical_repo_url", "release_branch",
                "source_commit", "payload_sha256", "verifier_path", "verifier_sha256"):
        if not isinstance(data[key], str) or not data[key]:
            raise VerifyError(1, f"manifest key '{key}' must be a non-empty string")


def verify_payload_hash(zip_path: Path, manifest: dict) -> None:
    actual = _sha256_file(zip_path)
    expected = manifest["payload_sha256"]
    if actual != expected:
        raise VerifyError(
            2,
            f"payload_sha256 mismatch: zip file hash {actual} != manifest {expected} "
            f"-- the downloaded zip does not match its recorded hash.",
        )


def _root_dir_name(zf: zipfile.ZipFile, release_branch: str) -> str:
    """Derive the trusted root folder name.

    PRIMARY (SEC-PAYLOAD-9.10.2-005): the manifest's own `release_branch`
    field -- our own builder always nests content under
    "<release_branch>/". Validated (not just assumed) by confirming at
    least one real zip entry actually lives under that prefix, so a
    manifest that merely CLAIMS a release_branch with no matching content
    can't silently redirect the root.

    FALLBACK: only when no entry is found under the release_branch-derived
    root do we fall back to deriving the root from the first
    non-directory entry's physical position in `namelist()` -- this is
    fragile against a maliciously reordered/misleading first entry (the
    original, sole implementation prior to this remediation), but remains
    fail-closed today either way: a wrong root causes downstream checks
    (embedded-manifest lookup, per-file lookup) to fail rather than to
    silently pass."""
    prefix = release_branch + "/"
    for name in zf.namelist():
        if name == release_branch or name.startswith(prefix):
            return release_branch
    for name in zf.namelist():
        if "/" in name:
            return name.split("/", 1)[0]
    return release_branch


def verify_embedded_manifest_consistency(zf: zipfile.ZipFile, external_manifest: dict, root: str) -> None:
    """The embedded copy is written BEFORE the zip (and therefore
    `payload_sha256`) exists -- it structurally cannot include that field
    (chicken-and-egg: the zip's hash depends on its own contents, which
    includes the embedded manifest). Compare everything EXCEPT that one
    field; every other field must be byte-for-byte identical."""
    arcname = f"{root}/payload-manifest.json"
    try:
        embedded_bytes = zf.read(arcname)
    except KeyError as exc:
        raise VerifyError(3, f"zip does not contain the expected embedded manifest at {arcname}") from exc
    try:
        embedded = json.loads(embedded_bytes)
    except ValueError as exc:
        raise VerifyError(3, f"embedded manifest at {arcname} is not valid JSON: {exc}") from exc
    external_sans_payload_hash = {k: v for k, v in external_manifest.items() if k != "payload_sha256"}
    if embedded != external_sans_payload_hash:
        raise VerifyError(
            3,
            "embedded manifest (inside the zip) does NOT match the external "
            "sibling manifest you downloaded (aside from the necessarily-absent "
            "payload_sha256 field) -- this pair is inconsistent and must not be trusted.",
        )


def verify_verifier_self_hash(zf: zipfile.ZipFile, manifest: dict, root: str) -> None:
    verifier_rel = manifest["verifier_path"]
    arcname = f"{root}/{verifier_rel}"
    try:
        data = zf.read(arcname)
    except KeyError as exc:
        raise VerifyError(4, f"zip does not contain the declared verifier at {arcname}") from exc
    actual = _sha256_bytes(data)
    expected = manifest["verifier_sha256"]
    if actual != expected:
        raise VerifyError(
            4,
            f"verifier_sha256 mismatch: {arcname} hashes to {actual}, manifest "
            f"declares {expected} -- the shipped verifier inside this zip does "
            "not match its own manifest record.",
        )


def verify_files(zf: zipfile.ZipFile, manifest: dict, root: str) -> None:
    declared = {entry["path"]: entry for entry in manifest["files"]}
    present = set()
    out_of_root = []
    prefix = root + "/"
    # SEC-PAYLOAD-9.10.2-003: scan the FULL infolist -- ANY entry not under
    # the expected root is an unconditional offender, not silently ignored.
    for info in zf.infolist():
        if not info.filename.startswith(prefix):
            out_of_root.append(info.filename)
            continue
        if info.is_dir():
            continue
        rel = info.filename[len(prefix):]
        if rel == "payload-manifest.json":
            continue  # the embedded manifest itself is not a declared content file
        present.add(rel)

    offenders = []
    if out_of_root:
        offenders.append(
            f"{len(out_of_root)} zip entr{'y' if len(out_of_root) == 1 else 'ies'} outside "
            f"the expected root {root!r}: {sorted(out_of_root)}"
        )

    missing = sorted(set(declared) - present)
    extra = sorted(present - set(declared))
    if missing:
        offenders.append(f"missing from zip: {missing}")
    if extra:
        offenders.append(f"undeclared extra file(s) in zip: {extra}")

    mismatched = []
    # SEC-PAYLOAD-9.10.2-002: hash via bounded streaming reads, enforcing a
    # running decompressed-byte budget against ACTUAL bytes produced --
    # independent of (and never trusting) declared ZipInfo.file_size.
    budget = _DecompressionBudget(MAX_TOTAL_UNCOMPRESSED_BYTES)
    for rel in sorted(set(declared) & present):
        entry = declared[rel]
        actual_hash, actual_size = _hash_zip_entry_capped(zf, f"{root}/{rel}", budget)
        if actual_hash != entry["sha256"] or actual_size != entry["size"]:
            mismatched.append(rel)
    if mismatched:
        offenders.append(f"content/size mismatch: {mismatched}")

    if offenders:
        raise VerifyError(3, "per-file integrity check failed -- " + "; ".join(offenders))


def _check_zip_safety(zf: zipfile.ZipFile) -> None:
    infos = zf.infolist()
    if len(infos) > MAX_ENTRIES:
        raise VerifyError(8, f"zip has {len(infos)} entries, exceeding the safety cap ({MAX_ENTRIES})")
    total = sum(i.file_size for i in infos)
    if total > MAX_TOTAL_UNCOMPRESSED_BYTES:
        raise VerifyError(
            8, f"zip's total uncompressed size ({total} bytes) exceeds the safety cap "
               f"({MAX_TOTAL_UNCOMPRESSED_BYTES} bytes) -- refusing (zip-bomb defense)."
        )
    for info in infos:
        name = info.filename
        # Symlink entries: unix mode bits live in the top 16 bits of external_attr.
        unix_mode = (info.external_attr >> 16) & 0xFFFF
        if unix_mode and (unix_mode & 0o170000) == 0o120000:
            raise VerifyError(8, f"zip entry {name!r} is a symlink -- refusing to extract")
        if os.path.isabs(name) or (len(name) > 1 and name[1] == ":"):
            raise VerifyError(8, f"zip entry {name!r} has an absolute/drive-letter path -- refusing")
        norm = os.path.normpath(name)
        if norm.startswith("..") or norm.split(os.sep)[0] == "..":
            raise VerifyError(8, f"zip entry {name!r} attempts path traversal -- refusing")


def safe_extract(zf: zipfile.ZipFile, dest: Path, root: str) -> None:
    """Zip-slip-hardened extraction: only called AFTER every other check has
    already passed. Every resolved target path is verified to remain under
    `dest` before any bytes are written. Strips the leading `root/` (release
    branch) folder so extracted content lands directly under `dest` (e.g.
    `dest/CLAUDE.md`, not `dest/DZP-vX.Y.Z/CLAUDE.md`); the embedded
    `payload-manifest.json` copy is skipped (it is a provenance artifact, not
    installable content -- the external sibling manifest is the one to keep)."""
    _check_zip_safety(zf)
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    prefix = root + "/"
    # SEC-PAYLOAD-9.10.2-002: running decompressed-byte budget enforced
    # against ACTUAL bytes produced during the copy, independent of (and
    # never trusting) declared ZipInfo.file_size -- self-defending even if
    # the _check_zip_safety() aggregate pre-check above were ever bypassed,
    # skipped, or refactored away by a future caller.
    budget = _DecompressionBudget(MAX_TOTAL_UNCOMPRESSED_BYTES)
    for info in zf.infolist():
        if info.is_dir():
            continue
        if not info.filename.startswith(prefix):
            continue
        rel = info.filename[len(prefix):]
        if rel == "payload-manifest.json":
            continue
        target = (dest / rel).resolve()
        try:
            target.relative_to(dest)
        except ValueError as exc:
            raise VerifyError(8, f"zip entry {info.filename!r} resolves outside the destination directory") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zf.open(info) as src, open(target, "wb") as out:
                _copy_zip_entry_capped(src, out, budget, info.filename)
        except VerifyError:
            # Fail-closed: never leave a partial/truncated file behind for a
            # caller to mistakenly trust after an abort mid-copy.
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
            raise


def _run(cmd, timeout=30):
    try:
        return subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",
                               timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerifyError(6, f"could not execute {' '.join(cmd)}: {exc}") from exc


def _validate_pinned_canonical_url(url: str, allow_alternate_origin: str = None) -> None:
    """SEC-PAYLOAD-9.10.2-001: refuse to treat `manifest['canonical_repo_url']`
    (self-attested content of the very manifest under verification) as a
    trustworthy `git ls-remote` target unless it is normalized-equal to the
    hardcoded `CANONICAL_REPO_URL`, OR an explicit `--allow-alternate-origin`
    was given that ITSELF is normalized-equal to that same manifest URL (an
    opt-in that authorizes exactly the URL it names -- never anything else).
    Called BEFORE any network call. Raises VerifyError(9) on failure -- a
    dedicated code, distinct from 5 (a confirmed ls-remote mismatch) and 6
    (an execution failure), because this is neither: it is a refusal to even
    attempt the network check against an unpinned, self-attested origin."""
    pinned_norm = _normalize_repo_url(CANONICAL_REPO_URL)
    manifest_norm = _normalize_repo_url(url)

    if manifest_norm == pinned_norm:
        return

    if allow_alternate_origin is not None:
        alt_norm = _normalize_repo_url(allow_alternate_origin)
        if alt_norm != manifest_norm:
            raise VerifyError(
                9,
                f"--allow-alternate-origin ({allow_alternate_origin!r}) does not match "
                f"the manifest's canonical_repo_url ({url!r}) -- it must authorize EXACTLY "
                "the URL the manifest declares. Refusing.",
            )
        print(
            "[verify-payload] WARNING: --allow-alternate-origin is authorizing a "
            f"NON-CANONICAL origin: manifest declares canonical_repo_url={url!r}, which "
            f"differs from the pinned canonical repo ({CANONICAL_REPO_URL!r}). This is "
            "appropriate ONLY for a genuine, deliberately-trusted fork/mirror -- never use "
            "this flag to work around an unexpected or untrusted origin.",
            file=sys.stderr,
        )
        return

    raise VerifyError(
        9,
        "canonical-origin PINNING mismatch: manifest declares "
        f"canonical_repo_url={url!r}, but this verifier's pinned canonical repo is "
        f"{CANONICAL_REPO_URL!r}. Refusing to cross-check a self-attested, non-canonical "
        "origin -- an attacker-controlled manifest could otherwise point this check at "
        "their own repo/commit and always PASS. If you genuinely intend to install from a "
        f"trusted fork/mirror, re-run with --allow-alternate-origin {url!r} (loud, "
        "explicit opt-in only).",
    )


def verify_canonical_origin(manifest: dict, allow_alternate_origin: str = None) -> None:
    url = manifest["canonical_repo_url"]
    branch = manifest["release_branch"]
    commit = manifest["source_commit"]
    _validate_pinned_canonical_url(url, allow_alternate_origin=allow_alternate_origin)
    proc = _run(["git", "ls-remote", url, f"refs/tags/{branch}", f"refs/heads/{branch}"])
    if proc.returncode != 0:
        raise VerifyError(6, f"`git ls-remote {url}` failed: {proc.stderr.strip() or proc.stdout.strip()}")

    refs = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or "\t" not in line:
            continue
        sha, ref = line.split("\t", 1)
        refs[ref] = sha

    tag_ref = f"refs/tags/{branch}"
    tag_peeled = f"{tag_ref}^{{}}"
    branch_ref = f"refs/heads/{branch}"

    resolved = None
    if tag_peeled in refs:
        resolved = refs[tag_peeled]  # annotated tag: peeled commit is authoritative
    elif tag_ref in refs:
        resolved = refs[tag_ref]  # lightweight tag: ref sha IS the commit
    elif branch_ref in refs:
        resolved = refs[branch_ref]

    if resolved is None:
        raise VerifyError(
            5,
            f"neither refs/tags/{branch} nor refs/heads/{branch} was found on the "
            f"canonical repo ({url}) -- cannot confirm this release's provenance.",
        )
    if resolved != commit:
        raise VerifyError(
            5,
            f"canonical-origin mismatch: {branch} resolves to {resolved} on {url}, "
            f"but the manifest records source_commit={commit}.",
        )


def deep_verify(manifest: dict, zf: zipfile.ZipFile, root: str) -> None:
    """Optional, stronger (network + real clone) check: shallow-clone the
    canonical repo at the recorded ref and byte-compare every manifest file
    against the corresponding file in that clone. Closes the gap the default
    mode leaves open (see module docstring)."""
    url = manifest["canonical_repo_url"]
    branch = manifest["release_branch"]
    commit = manifest["source_commit"]
    with tempfile.TemporaryDirectory(prefix="dzp-deepverify-") as tmp:
        clone_dir = Path(tmp) / "clone"
        proc = _run(["git", "clone", "--depth", "1", "--branch", branch, url, str(clone_dir)], timeout=300)
        if proc.returncode != 0:
            # Some hosts refuse shallow-clone-by-tag; retry against the plain URL + fetch.
            clone_dir.mkdir(parents=True, exist_ok=True)
            init = _run(["git", "init", "-q", str(clone_dir)])
            if init.returncode != 0:
                raise VerifyError(7, f"deep-verify: could not init a clone dir: {init.stderr}")
            fetch = _run(["git", "-C", str(clone_dir), "fetch", "--depth", "1", url, commit], timeout=300)
            if fetch.returncode != 0:
                raise VerifyError(7, f"deep-verify: could not fetch {commit} from {url}: {fetch.stderr}")
            _run(["git", "-C", str(clone_dir), "checkout", "-q", "FETCH_HEAD"], timeout=60)

        head = _run(["git", "-C", str(clone_dir), "rev-parse", "HEAD"])
        if head.returncode != 0 or head.stdout.strip() != commit:
            raise VerifyError(
                7,
                f"deep-verify: cloned HEAD ({head.stdout.strip() or 'unknown'}) does not "
                f"match manifest source_commit ({commit}).",
            )

        mismatched = []
        for entry in manifest["files"]:
            rel = entry["path"]
            local = clone_dir / rel
            if not local.is_file():
                mismatched.append(f"{rel} (absent from canonical clone)")
                continue
            zip_bytes = zf.read(f"{root}/{rel}")
            if _sha256_bytes(local.read_bytes()) != _sha256_bytes(zip_bytes):
                mismatched.append(rel)
        if mismatched:
            raise VerifyError(7, f"deep-verify content mismatch vs canonical clone: {mismatched}")


def verify(zip_path: Path, manifest_path: Path = None, skip_origin_check: bool = False,
           extract_to: Path = None, deep_verify_mode: bool = False,
           allow_alternate_origin: str = None) -> dict:
    """Run every check in fail-closed order. Returns the validated manifest
    dict on full success. Raises VerifyError(code, message) on any failure."""
    zip_path = Path(zip_path)
    if manifest_path is None:
        # default sibling naming: dzp-payload-vX.Y.Z.zip -> dzp-payload-vX.Y.Z.manifest.json
        manifest_path = zip_path.with_name(zip_path.stem + ".manifest.json")
    else:
        manifest_path = Path(manifest_path)

    if not zip_path.is_file():
        raise VerifyError(1, f"zip file not found: {zip_path}")
    if not manifest_path.is_file():
        raise VerifyError(1, f"manifest file not found: {manifest_path} (pass --manifest explicitly?)")

    manifest = load_manifest(manifest_path)
    verify_payload_hash(zip_path, manifest)

    with zipfile.ZipFile(zip_path, "r") as zf:
        _check_zip_safety(zf)
        root = _root_dir_name(zf, manifest["release_branch"])
        verify_embedded_manifest_consistency(zf, manifest, root)
        verify_verifier_self_hash(zf, manifest, root)
        verify_files(zf, manifest, root)

        if skip_origin_check:
            print(
                "[verify-payload] WARNING: --skip-origin-check is set -- the canonical-origin "
                "cross-check (git ls-remote) is BEING SKIPPED. This provides ZERO supply-chain "
                "provenance assurance beyond internal zip/manifest self-consistency. Use only "
                "when genuinely offline; never as a routine default.",
                file=sys.stderr,
            )
        else:
            verify_canonical_origin(manifest, allow_alternate_origin=allow_alternate_origin)

        if deep_verify_mode:
            deep_verify(manifest, zf, root)

        if extract_to is not None:
            safe_extract(zf, Path(extract_to), root)

    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify a DZP release payload zip + manifest before installing.")
    ap.add_argument("zip_path", type=Path)
    ap.add_argument("--manifest", type=Path, default=None,
                     help="path to the sibling manifest.json (default: derived from zip name)")
    ap.add_argument("--skip-origin-check", action="store_true",
                     help="skip the git ls-remote canonical-origin cross-check (LOUD warning; offline use only)")
    ap.add_argument("--deep-verify", action="store_true",
                     help="also shallow-clone the canonical repo and byte-compare every file (network+time cost)")
    ap.add_argument("--extract-to", type=Path, default=None,
                     help="if every check passes, safely extract into this directory (created if absent)")
    ap.add_argument("--allow-alternate-origin", type=str, default=None, metavar="URL",
                     help="explicitly authorize a non-canonical manifest['canonical_repo_url'] "
                          "(must match it EXACTLY) for a genuinely-trusted fork/mirror -- loud, "
                          "non-default, opt-in only; has no effect together with --skip-origin-check")
    args = ap.parse_args(argv)

    try:
        manifest = verify(
            args.zip_path, manifest_path=args.manifest,
            skip_origin_check=args.skip_origin_check,
            extract_to=args.extract_to, deep_verify_mode=args.deep_verify,
            allow_alternate_origin=args.allow_alternate_origin,
        )
    except VerifyError as exc:
        print(f"VERIFY FAILED (exit {exc.code}): {exc}", file=sys.stderr)
        return exc.code

    print(f"VERIFY OK: DZP v{manifest['protocol_version']} ({manifest['release_branch']} @ "
          f"{manifest['source_commit'][:12]})")
    print(f"  files verified: {len(manifest['files'])}")
    if args.skip_origin_check:
        print("  canonical-origin check: SKIPPED (--skip-origin-check)")
    elif args.allow_alternate_origin:
        print(f"  canonical-origin check: PASSED (authorized alternate origin: {args.allow_alternate_origin})")
    else:
        print("  canonical-origin check: PASSED (pinned canonical origin)")
    # SEC-PAYLOAD-9.10.2-SEC-003 (Toji audit 2026-07-27): surface the same
    # trust-boundary caveat the module docstring already documents, at the
    # point a user actually reads it -- the runtime success output -- not
    # only in the docstring, so "VERIFY OK" is never mistaken for a stronger
    # guarantee than the default (non-deep-verify) mode actually provides.
    if not args.deep_verify:
        print("  NOTE: this does not cryptographically bind the zip's file bytes to the canonical "
              "commit's git tree (see 'Threat-model notes' in this script's module docstring); "
              "re-run with --deep-verify for that guarantee.")
    if args.deep_verify:
        print("  deep-verify (canonical clone byte-compare): PASSED")
    if args.extract_to:
        print(f"  extracted to: {args.extract_to}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
