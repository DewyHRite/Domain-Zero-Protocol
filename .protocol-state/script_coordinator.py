#!/usr/bin/env python3
"""DZP script orchestration coordinator.

Runs named lifecycle events from .protocol-state/script_dependencies.yaml and
stores compact results in project-state.json::script_orchestration.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment configuration
    raise SystemExit("PyYAML is required to load script_dependencies.yaml") from exc

STATE_DIR = Path(__file__).resolve().parent
REPO_ROOT = STATE_DIR.parent
DEFAULT_REGISTRY = STATE_DIR / "script_dependencies.yaml"
PROJECT_STATE = STATE_DIR / "project-state.json"
MAX_EVENTS = 50
OUTPUT_LIMIT = 500

# v9.10.2 item-5 carried note: detached-log rotation. The rolling detached-step
# log (see the BUG-CORTEX-008 R5 note below) previously grew unbounded. A
# simple single-backup, size-based rotation (mirrors the well-understood
# logging.handlers.RotatingFileHandler scheme) caps it at roughly 2x this
# threshold: when the live log exceeds DETACHED_LOG_MAX_BYTES, it is renamed
# to a ".1" backup (overwriting any prior backup) before the new entry is
# appended. No daemon/scheduler is introduced -- rotation is checked inline,
# synchronously, at the start of each detached spawn (DZP stays no-daemon).
DETACHED_LOG_MAX_BYTES = 2 * 1024 * 1024  # 2 MB
DETACHED_LOG_BACKUP_SUFFIX = ".1"

# BUG-CORTEX-008 R5 (2026-07-18, Sukuna): detached-step logging. A `detach: true`
# step's child process is launched fully independent of the coordinator (see
# ScriptCoordinator._spawn_detached) and outlives it; its stdout/stderr cannot be
# captured synchronously, so they are appended to a rolling log instead
# (instance attributes self.log_dir / self.detached_log, derived from each
# coordinator's own state_dir -- see __init__ -- so a coordinator constructed
# against a custom repo_root, e.g. in tests, never writes into the real repo).
# Gitignored (`.protocol-state/logs/` — never committed; see .gitignore).

if str(STATE_DIR) not in sys.path:
    sys.path.insert(0, str(STATE_DIR))

try:
    from project_state_manager import ProjectStateManager
except ImportError:  # pragma: no cover - fallback tested through direct JSON path
    ProjectStateManager = None  # type: ignore[assignment]


class RegistryError(Exception):
    """Raised when the orchestration registry is invalid."""


class ScriptCoordinator:
    """Load event definitions, run steps, and record compact outcomes."""

    def __init__(
        self,
        repo_root: Path | str = REPO_ROOT,
        registry_path: Path | str | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.state_dir = self.repo_root / ".protocol-state"
        self.registry_path = (
            Path(registry_path).resolve()
            if registry_path is not None
            else self.state_dir / "script_dependencies.yaml"
        )
        self.project_state_path = self.state_dir / "project-state.json"
        # BUG-CORTEX-008 R5: derived from THIS instance's state_dir (not the
        # module-level STATE_DIR/LOG_DIR constants, which are bound to the real
        # repo) so a coordinator constructed against a custom repo_root (e.g. in
        # tests) writes its detached-step log under that same tree.
        self.log_dir = self.state_dir / "logs"
        self.detached_log = self.log_dir / "cortex-detached.log"
        # v9.10.2 item-5 carried note: instance attribute (not just the module
        # constant) so tests can override it to a small value without writing
        # multi-megabyte fixtures.
        self._detached_log_max_bytes = DETACHED_LOG_MAX_BYTES

    def load_registry(self) -> dict[str, Any]:
        """Load and validate the YAML event registry."""
        if not self.registry_path.exists():
            raise RegistryError(f"Registry not found: {self._display(self.registry_path)}")
        if self.registry_path.is_symlink():
            raise RegistryError(f"Registry cannot be a symlink: {self._display(self.registry_path)}")

        with self.registry_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

        if not isinstance(data, dict):
            raise RegistryError("Registry root must be a mapping")

        # v9.10.2 item-5 carried note: 'defaults' (if present at all) must
        # itself be a mapping. Previously an unvalidated non-mapping (e.g. a
        # YAML list) crashed with a raw AttributeError at the per-step
        # timeout-default lookup below ('list' object has no attribute 'get'),
        # deep inside this method rather than as a clear diagnostic.
        defaults = data.get("defaults", {})
        if not isinstance(defaults, dict):
            raise RegistryError("Registry 'defaults' must be a mapping")

        events = data.get("events")
        if not isinstance(events, dict) or not events:
            raise RegistryError("Registry must define a non-empty events mapping")

        for event_name, event_cfg in events.items():
            if not isinstance(event_cfg, dict):
                raise RegistryError(f"Event {event_name!r} must be a mapping")
            steps = event_cfg.get("steps")
            if not isinstance(steps, list) or not steps:
                raise RegistryError(f"Event {event_name!r} must define at least one step")
            # IMPL-001: collects every (index, name) pair where this event's
            # step sets 'terminal_validator: true' -- validated as a separate
            # pass AFTER the per-step loop below (see after the loop) so
            # "more than one configured" is reported as its own diagnosis
            # instead of being masked by whichever offending step the
            # per-step loop happens to reach first.
            terminal_validator_hits: list[tuple[int, str]] = []
            for index, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    raise RegistryError(f"Event {event_name!r} step {index} must be a mapping")
                command = step.get("command")
                if not isinstance(command, list) or not command:
                    raise RegistryError(f"Event {event_name!r} step {index} needs a command list")
                if not all(isinstance(part, str) for part in command):
                    raise RegistryError(f"Event {event_name!r} step {index} command parts must be strings")
                timeout = step.get("timeout_seconds", defaults.get("timeout_seconds", 30))
                if not isinstance(timeout, int) or timeout < 1:
                    raise RegistryError(f"Event {event_name!r} step {index} has invalid timeout_seconds")
                # v9.10.2 item-5 carried note: per-step 'env' (if present) must
                # be a mapping. Previously an unvalidated non-mapping crashed
                # later, inside _run_step()'s `.items()` call, with a raw
                # AttributeError surfacing from a completely different method
                # than the one that loaded (and should have rejected) it.
                env = step.get("env", {})
                if not isinstance(env, dict):
                    raise RegistryError(
                        f"Event {event_name!r} step {index} 'env' must be a mapping"
                    )
                # SEC-TRANSFER-9.11.0-009 (P3, CWE-693): `non_blocking: true`
                # silently and completely neuters `required: true` at
                # run_event() time (`step_required = False if non_blocking
                # else required`) -- a step declaring BOTH is contradictory
                # config and, before this guard, loaded without complaint on
                # ANY event, not just session-transfer. Reject it here, fail
                # closed at LOAD time, rather than relying on a single
                # event-specific regression test to catch a future mistaken
                # or tampered combination. Checked against the EXPLICIT
                # values only (`required is True`) -- a step where
                # `required` is simply absent (defaulted later from the
                # event's fail_soft setting) or explicitly `false` is not
                # this contradiction and must load exactly as before.
                if step.get("required") is True and step.get("non_blocking") is True:
                    step_label = step.get("name", f"#{index}")
                    raise RegistryError(
                        f"Event {event_name!r} step {step_label!r} (index {index}) cannot set "
                        "both 'required: true' and 'non_blocking: true' -- non_blocking "
                        "silently neuters required, which is almost certainly a "
                        "configuration mistake (SEC-TRANSFER-9.11.0-009)"
                    )
                # IMPL-001 (Toji audit 2026-07-30): 'terminal_validator: true'
                # opts a step OUT of the main step loop entirely -- run_event()
                # instead runs it AFTER _record_result() has persisted this
                # event's own outcome to project-state.json (see run_event()
                # for the full rationale: _record_result()'s own save is
                # ALWAYS the true last project-state.json mutation of any
                # event, so a step meant to describe the "terminal" state must
                # run after that save, not before it -- no matter where it
                # sits in the configured step list). Just record the hit here;
                # validated as a whole-event pass below.
                if step.get("terminal_validator") is True:
                    terminal_validator_hits.append((index, step.get("name", f"#{index}")))

            # IMPL-001: two invariants enforced here, at LOAD time, rather
            # than left to silently do the wrong thing at runtime:
            #   1. at most one 'terminal_validator: true' step per event
            #      (there is only one "after record" execution slot);
            #   2. it must be that event's LAST configured step (anything
            #      else would make "terminal" a lie about ordering intent,
            #      even though only the flagged step is actually deferred).
            # A terminal_validator step can never affect the event's
            # recorded success/failure (it runs after that decision is
            # already made and saved), so combining it with `required: true`
            # is rejected as a misleading contradiction, mirroring the
            # non_blocking+required guard above.
            if len(terminal_validator_hits) > 1:
                names = ", ".join(repr(name) for _, name in terminal_validator_hits)
                raise RegistryError(
                    f"Event {event_name!r} defines more than one 'terminal_validator: true' "
                    f"step ({names}) -- at most one is allowed per event (IMPL-001)"
                )
            if terminal_validator_hits:
                index, step_label = terminal_validator_hits[0]
                if index != len(steps):
                    raise RegistryError(
                        f"Event {event_name!r} step {step_label!r} (index {index} of "
                        f"{len(steps)}) sets 'terminal_validator: true' but is not the "
                        "event's LAST step -- a terminal validator must be the final "
                        "configured step (IMPL-001)"
                    )
                validator_step = steps[index - 1]
                if validator_step.get("required") is True:
                    raise RegistryError(
                        f"Event {event_name!r} step {step_label!r} cannot combine "
                        "'terminal_validator: true' with 'required: true' -- a terminal "
                        "validator runs AFTER the event's result is already recorded and "
                        "can never affect success/failure, so 'required: true' is "
                        "misleading (IMPL-001)"
                    )
        return data

    def run_event(
        self,
        event_name: str,
        *,
        strict: bool = False,
        dry_run: bool = False,
        json_output: bool = False,
    ) -> int:
        """Run one registry event and return a process-style exit code."""
        started_at = self._now()
        registry = self.load_registry()
        events = registry["events"]
        if event_name not in events:
            raise RegistryError(f"Unknown event: {event_name}")

        defaults = registry.get("defaults", {}) if isinstance(registry.get("defaults"), dict) else {}
        event_cfg = events[event_name]
        event_fail_soft = bool(event_cfg.get("fail_soft", defaults.get("fail_soft", True)))
        fail_closed = strict or not event_fail_soft
        all_steps = event_cfg["steps"]

        # IMPL-001 (Toji audit 2026-07-30): a step opts in as this event's
        # SOLE terminal validator via `terminal_validator: true`
        # (load_registry() guarantees at most one per event, and that it is
        # the event's LAST configured step). That step is excluded from the
        # main loop below and is instead run AFTER self._record_result()
        # has persisted this event's own outcome to project-state.json --
        # closing the gap where the coordinator's own bookkeeping write was
        # itself always the true last project-state.json mutation of any
        # event, occurring AFTER a step that was supposed to describe the
        # terminal state. See the finding for the full reproduction:
        # validation-state.json recorded a project-state.json checksum/seq
        # that the coordinator's own post-loop _record_result() call
        # immediately superseded, regardless of step order.
        terminal_validator_step = None
        steps: list[dict[str, Any]] = []
        for step in all_steps:
            if step.get("terminal_validator") is True:
                terminal_validator_step = step
            else:
                steps.append(step)

        results: list[dict[str, Any]] = []
        success = True

        for step in steps:
            step_result = self._dry_step_result(step) if dry_run else self._run_step(step, defaults)
            results.append(step_result)
            required = bool(step.get("required", not event_fail_soft))
            # DESIGN-001 (Toji audit 2026-07-29): a step may opt out of the
            # EVENT-level fail-closed policy entirely via `non_blocking: true`.
            # Without this, an event-level `fail_soft: false` makes even a
            # `required: false` optional-tail step both break the loop AND
            # mark the whole event failed -- the step's own `required` flag
            # cannot preserve an optional failure under a fail-closed event
            # (see script_dependencies.yaml's session-transfer event: this is
            # exactly what made cortex-medium/cortex-distill/validation-refresh
            # fail-closed in practice despite being documented as optional).
            # `non_blocking` is opt-in per step and changes NOTHING for any
            # step that does not set it -- existing events/tests are
            # unaffected. `--strict` is an explicit, stronger CLI override and
            # always wins over `non_blocking` (belt-and-braces semantics
            # unchanged for events that document `--strict` as a stricter
            # invocation mode).
            non_blocking = bool(step.get("non_blocking", False)) and not strict
            step_fail_closed = False if non_blocking else fail_closed
            step_required = False if non_blocking else required
            # BUG-CORTEX-008 R5: "launched" (a detach: true step that was
            # successfully spawned off-path) is a SUCCESS outcome — the step
            # returned immediately by design, not because it failed. Only the
            # spawn itself failing (status "failure", see _run_detached_step)
            # counts against the event.
            failed = step_result["status"] not in ("success", "launched")
            if failed and (step_fail_closed or step_required):
                success = False
                if step_fail_closed:
                    break
            elif failed:
                step_result["warning"] = (
                    "optional step failed under fail-soft event"
                    if not non_blocking
                    else "non_blocking step failed; does not affect overall event status"
                )

        result = {
            "event": event_name,
            "started_at": started_at,
            "finished_at": self._now(),
            "success": success,
            "status": "success" if success else "failure",
            "fail_soft": event_fail_soft,
            "strict": strict,
            "dry_run": dry_run,
            "steps": results,
        }

        if not dry_run:
            self._record_result(result)

        if terminal_validator_step is not None:
            # Runs strictly AFTER self._record_result() above -- this is the
            # entire fix. Its result is appended to `result["steps"]` ONLY
            # for this call's printed/returned output (operator visibility);
            # it is never persisted via a second _record_result() call, since
            # doing so would just reproduce the exact post-record mutation
            # this ordering exists to close. Its outcome can therefore never
            # retroactively change `success`/`status` above -- a failure
            # here only WARNS loudly, per Toji's explicit recommendation
            # that a failing terminal validator must never fail an
            # already-completed event.
            validator_result = (
                self._dry_step_result(terminal_validator_step)
                if dry_run
                else self._run_step(terminal_validator_step, defaults)
            )
            validator_failed = validator_result["status"] not in ("success", "launched")
            if validator_failed:
                validator_result["warning"] = (
                    "terminal validator step failed; it runs AFTER this event's own "
                    "result was recorded (IMPL-001) and therefore can never affect "
                    "this event's recorded success/status -- investigate separately"
                )
                print(
                    f"WARNING: event {event_name!r} terminal validator step "
                    f"{validator_result['name']!r} failed (status="
                    f"{validator_result['status']!r}); this does not affect the "
                    "already-recorded event outcome (IMPL-001)",
                    file=sys.stderr,
                )
            result["steps"].append(validator_result)

        self._print_result(result, as_json=json_output)
        return 0 if success else 1

    def status(self, *, json_output: bool = False) -> int:
        """Print coordinator registry and last-run status."""
        registry_ok = True
        registry_error = None
        try:
            registry = self.load_registry()
        except Exception as exc:  # noqa: BLE001 - status should report all registry failures
            registry_ok = False
            registry_error = str(exc)
            registry = {"events": {}}

        state = self._load_project_state()
        orchestration = state.get("script_orchestration", {})
        payload = {
            "registry_ok": registry_ok,
            "registry_error": registry_error,
            "registry": self._display(self.registry_path),
            "events": sorted(registry.get("events", {}).keys()),
            "last_event": orchestration.get("last_event"),
            "last_updated": orchestration.get("last_updated"),
            "last_status_by_event": orchestration.get("last_status_by_event", {}),
        }
        if json_output:
            print(json.dumps(payload, indent=2))
        else:
            print(f"registry: {'ok' if registry_ok else 'error'} ({payload['registry']})")
            if registry_error:
                print(f"error: {registry_error}")
            print("events: " + ", ".join(payload["events"]))
            print(f"last_event: {payload['last_event'] or 'none'}")
        return 0 if registry_ok else 1

    def doctor(self, *, json_output: bool = False) -> int:
        """Validate registry shape and command targets."""
        checks: list[str] = []
        warnings: list[str] = []
        errors: list[str] = []

        try:
            registry = self.load_registry()
            checks.append(f"registry loaded: {self._display(self.registry_path)}")
        except Exception as exc:  # noqa: BLE001
            registry = {"events": {}}
            errors.append(str(exc))

        if not self.project_state_path.exists():
            errors.append(f"missing state file: {self._display(self.project_state_path)}")
        else:
            checks.append(f"state file present: {self._display(self.project_state_path)}")

        for event_name, event_cfg in registry.get("events", {}).items():
            for step in event_cfg.get("steps", []):
                command = step["command"]
                target = self._command_target(command)
                if target is None:
                    continue
                if not target.exists():
                    errors.append(f"{event_name}/{step.get('name', command[0])}: missing {self._display(target)}")
                elif not self._is_inside_repo(target):
                    errors.append(f"{event_name}/{step.get('name', command[0])}: target escapes repo")
                else:
                    checks.append(f"{event_name}/{step.get('name', command[0])}: {self._display(target)}")

        if os.environ.get("DZP_AGENT", "").lower() == "gojo":
            warnings.append("DZP_AGENT=gojo is advisory only; it is not used as an authorization boundary")

        payload = {
            "status": "error" if errors else ("warning" if warnings else "ok"),
            "checks": checks,
            "warnings": warnings,
            "errors": errors,
        }
        if json_output:
            print(json.dumps(payload, indent=2))
        else:
            print(f"doctor: {payload['status']}")
            for item in checks:
                print(f"ok: {item}")
            for item in warnings:
                print(f"warning: {item}")
            for item in errors:
                print(f"error: {item}")
        return 1 if errors else 0

    # P2-b (Megumi Tier-3 bundle review, v9.10.1): scripts/distro/** is
    # intentionally maintainer-only tooling that never ships in the public
    # distro (see scripts/distro/distro.gitignore + publish-manifest.yaml).
    # Used by _missing_script_diagnostic() to distinguish that specific,
    # documented case from any other missing script.
    _DISTRO_MAINTAINER_ONLY_PREFIX = "scripts/distro/"

    def _missing_script_diagnostic(self, command: list[str]) -> str | None:
        """Return a clear diagnostic message if `command` targets a script
        path that does not exist on disk, or None if the target exists (or
        the command has no resolvable file target at all, e.g. a bare `-c`
        inline script — subprocess handles that exactly as before).

        Without this check, `pre-release`/`pre-publish` running
        scripts/distro/assert_version.py or check_version_stamps.py on a
        consumer install (where scripts/distro/** is deliberately unshipped)
        hit subprocess.run() launching a REAL Python interpreter against a
        nonexistent script path — surfacing Python's own raw "can't open
        file ... No such file or directory" as the failure. That is
        undiagnosable for a consumer with no way to know this tooling is
        intentionally absent. Fail-closed semantics are UNCHANGED by this
        helper — the caller (_run_step) still reports "failure"; only the
        message differs, and only for a genuinely missing target.
        """
        target = self._command_target(command)
        if target is None or target.exists():
            return None
        try:
            rel = target.resolve().relative_to(self.repo_root).as_posix()
        except ValueError:
            rel = str(target)
        if rel.startswith(self._DISTRO_MAINTAINER_ONLY_PREFIX):
            return (
                f"maintainer-only tooling not present in this install: {rel} "
                "(scripts/distro/** is intentionally unshipped in the public "
                "DZP distro — see scripts/distro/publish-manifest.yaml). This "
                "event is documented as maintainer-only; see AI_INSTRUCTIONS.md."
            )
        return f"script not found: {rel}"

    def _run_step(self, step: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
        name = str(step.get("name") or step["command"][0])
        command = self._normalize_command(step["command"])

        # P2-b: a step targeting a script that does not exist on disk fails
        # with a clear diagnostic instead of a raw subprocess file-not-found
        # error. The step still FAILS either way (fail-closed preserved) —
        # a dev checkout where the script genuinely exists is unaffected.
        missing_diagnostic = self._missing_script_diagnostic(command)
        if missing_diagnostic is not None:
            return {
                "name": name,
                "command": self._display_command(command),
                "status": "failure",
                "exit_code": None,
                "duration_seconds": 0.0,
                "stdout": "",
                "stderr": missing_diagnostic,
            }

        # BUG-CORTEX-008 R5 (2026-07-18): a `detach: true` step short-circuits to
        # a fire-and-forget spawn instead of the blocking subprocess.run(timeout=)
        # path below. This is what removes embedding-delta-bound Cortex re-index
        # steps from the session-lifecycle critical path — see
        # _run_detached_step()/_spawn_detached() and the step's `timeout_seconds`
        # comment in script_dependencies.yaml (kept as the detach-DISABLED
        # fallback, i.e. only consulted if `detach` is ever removed/false).
        if step.get("detach"):
            return self._run_detached_step(name, command)

        timeout = int(step.get("timeout_seconds", defaults.get("timeout_seconds", 30)))
        env = os.environ.copy()
        for key, value in step.get("env", {}).items():
            env[str(key)] = str(value)

        # Force UTF-8 on both the child's stdout/stderr pipe (PYTHONUTF8=1 makes
        # the child's own I/O layer use UTF-8 instead of the OS default, e.g.
        # cp1252 on Windows) AND our capture side (encoding= / errors=).
        env.setdefault("PYTHONUTF8", "1")
        started = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                shell=False,
            )
            status = "success" if proc.returncode == 0 else "failure"
            return {
                "name": name,
                "command": self._display_command(command),
                "status": status,
                "exit_code": proc.returncode,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": self._compact(proc.stdout),
                "stderr": self._compact(proc.stderr),
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "name": name,
                "command": self._display_command(command),
                "status": "timeout",
                "exit_code": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": self._compact(exc.stdout),
                "stderr": self._compact(exc.stderr),
                "timeout_seconds": timeout,
            }

    def _run_detached_step(self, name: str, command: list[str]) -> dict[str, Any]:
        """BUG-CORTEX-008 R5 (2026-07-18): launch `command` fully detached from the
        coordinator process and return immediately with status "launched"
        (exit_code None) instead of blocking on subprocess.run(timeout=...).

        Root cause this closes: the pre-R5 synchronous `cortex-high`/`cortex-medium`
        Cortex re-index steps at session-end/session-update are embedding-DELTA-
        bound (not corpus-size-bound), so the ONE run immediately after a heavy
        session's largest content delta chronically blew even a generously raised
        timeout — independent of --level. Detaching removes the step from the
        session-lifecycle critical path entirely rather than racing a bigger
        timeout budget. See internal-docs/Patch Report/Bug Report/
        BUG-CORTEX-008-sessionend-high-rebuild-timeout-2026-07-13.md §11.

        Single-flight safety: this adds NO new concurrency hazard. Cortex's own
        index.lock (cortex/store.py, mtime-TTL self-healing per v9.4.1) already
        serializes concurrent index runs — a detached step racing a still-running
        prior detached run, or a synchronous `cortex-high --strict` release gate,
        simply observes the lock via Cortex's existing lock semantics (skip/wait),
        exactly as two ordinary sequential invocations would.

        Scope discipline: only `detach: true` steps take this path (opt-in per
        step in script_dependencies.yaml — currently session-end.cortex-medium and
        session-update.cortex-medium). The `cortex-high --strict` gates in
        pre-release/pre-publish/post-migration/post-rotation are deliberately NOT
        detached — those are infrequent, user-initiated gates where a synchronous,
        must-complete rebuild is the correct (and desired fail-closed) behavior.
        """
        started = time.monotonic()
        try:
            self._spawn_detached(command, name)
            return {
                "name": name,
                "command": self._display_command(command),
                "status": "launched",
                "exit_code": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": "",
                "stderr": "",
                "detached": True,
                "log_file": self._display(self.detached_log),
            }
        except OSError as exc:
            # Spawn itself failed (e.g. interpreter/script missing) — this is a
            # genuine failure, distinct from "launched successfully and running
            # off-path". Reported as "failure" so required:true/fail-closed
            # events still catch it; the detach steps in script_dependencies.yaml
            # are required: false (fail-soft), so this degrades gracefully.
            return {
                "name": name,
                "command": self._display_command(command),
                "status": "failure",
                "exit_code": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": "",
                "stderr": f"detach launch failed: {exc}",
            }

    def _rotate_detached_log_if_needed(self) -> None:
        """v9.10.2 item-5 carried note: single-backup, size-based rotation for
        the rolling detached-step log (`.protocol-state/logs/cortex-detached.log`).

        Every `detach: true` step (currently session-update/session-end's
        cortex-medium, BUG-CORTEX-008 R5) appends to this one file forever;
        without a cap it grows unbounded over the life of a repo. When the
        live log exceeds `self._detached_log_max_bytes`, it is renamed to a
        single `.1` backup (overwriting any prior backup) before the caller
        appends its new entry -- mirroring the well-understood
        `logging.handlers.RotatingFileHandler(backupCount=1)` scheme, with no
        daemon/scheduler involved (checked inline at each detached spawn).

        Fail-soft by design: ANY error here (permissions, a concurrent writer
        holding the file open on Windows, etc.) is swallowed. A rotation
        failure must never block a detached spawn -- avoiding exactly that
        kind of blocking is the entire point of detaching a step in the first
        place. On failure, the coordinator simply keeps appending to the
        oversized file until a future spawn's rotation attempt succeeds.
        """
        try:
            if not self.detached_log.exists():
                return
            if self.detached_log.stat().st_size <= self._detached_log_max_bytes:
                return
            backup = self.detached_log.with_suffix(
                self.detached_log.suffix + DETACHED_LOG_BACKUP_SUFFIX
            )
            if backup.exists():
                backup.unlink()
            self.detached_log.replace(backup)
        except OSError:
            pass

    def _spawn_detached(self, command: list[str], name: str) -> None:
        """Launch `command` as a fully detached child process that survives this
        coordinator process's exit (BUG-CORTEX-008 R5, 2026-07-18).

        Platform detachment:
          - Windows: CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS so the child is
            not part of the coordinator's console/process group and is not killed
            when the coordinator (or its parent shell) exits.
          - POSIX: start_new_session=True (setsid) for the equivalent detachment.

        stdin is DEVNULL (no interactive input possible/expected). stdout+stderr
        are appended to the gitignored rolling log DETACHED_LOG so failures
        remain observable even though the coordinator no longer waits on the
        child. The log file handle is opened, written to (a timestamped header),
        and closed in this method; the child receives its own duplicated file
        descriptor at process-creation time (standard subprocess.Popen behavior),
        so closing our copy afterward does not affect the child's ability to keep
        writing to it.
        """
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._rotate_detached_log_if_needed()
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        kwargs: dict[str, Any] = {
            "cwd": self.repo_root,
            "env": env,
            "stdin": subprocess.DEVNULL,
            "close_fds": True,
        }
        if os.name == "nt":
            kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
        else:
            kwargs["start_new_session"] = True

        with open(self.detached_log, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n=== {self._now()} :: {name} :: {' '.join(command)} ===\n")
            log_file.flush()
            subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT, **kwargs)

    def _dry_step_result(self, step: dict[str, Any]) -> dict[str, Any]:
        command = self._normalize_command(step["command"])
        return {
            "name": str(step.get("name") or step["command"][0]),
            "command": self._display_command(command),
            "status": "success",
            "exit_code": 0,
            "dry_run": True,
            "stdout": "",
            "stderr": "",
        }

    def _normalize_command(self, command: list[str]) -> list[str]:
        if command[0] in {"python", "python3"}:
            return [sys.executable] + command[1:]
        return command

    def _command_target(self, command: list[str]) -> Path | None:
        normalized = self._normalize_command(command)
        if not normalized:
            return None
        if Path(normalized[0]).resolve() == Path(sys.executable).resolve() and len(normalized) > 1:
            candidate = Path(normalized[1])
        else:
            candidate = Path(normalized[0])
        if candidate.is_absolute():
            return candidate.resolve()
        if candidate.suffix:
            return (self.repo_root / candidate).resolve()
        return None

    def _record_result(self, result: dict[str, Any]) -> None:
        state = self._load_project_state()
        orchestration = state.setdefault("script_orchestration", {})
        orchestration["_schema_version"] = 1
        orchestration["last_updated"] = result["finished_at"]
        orchestration["last_event"] = result["event"]
        event_summary = self._event_summary(result)
        events = orchestration.setdefault("events", [])
        if not isinstance(events, list):
            events = []
            orchestration["events"] = events
        events.append(event_summary)
        del events[:-MAX_EVENTS]
        by_event = orchestration.setdefault("last_status_by_event", {})
        if not isinstance(by_event, dict):
            by_event = {}
            orchestration["last_status_by_event"] = by_event
        by_event[result["event"]] = event_summary
        self._save_project_state(state)

    def _event_summary(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "event": result["event"],
            "finished_at": result["finished_at"],
            "success": result["success"],
            "status": result["status"],
            "fail_soft": result["fail_soft"],
            "steps": [
                {
                    "name": step["name"],
                    "status": step["status"],
                    "exit_code": step["exit_code"],
                    "duration_seconds": step.get("duration_seconds"),
                }
                for step in result["steps"]
            ],
        }

    def _load_project_state(self) -> dict[str, Any]:
        if ProjectStateManager is not None and self.project_state_path.exists():
            return ProjectStateManager(self.repo_root).load_project_state()
        if not self.project_state_path.exists():
            return {}
        with self.project_state_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save_project_state(self, state: dict[str, Any]) -> None:
        if ProjectStateManager is not None:
            ProjectStateManager(self.repo_root).save_project_state(state)
            return
        self.project_state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.project_state_path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")

    def _print_result(self, result: dict[str, Any], *, as_json: bool) -> None:
        if as_json:
            print(json.dumps(result, indent=2))
            return
        print(f"event {result['event']}: {result['status']}")
        for step in result["steps"]:
            print(f"  {step['name']}: {step['status']} ({step['exit_code']})")

    def _display_command(self, command: list[str]) -> list[str]:
        display = []
        for part in command:
            path = Path(part)
            if path.is_absolute() and self._is_inside_repo(path):
                display.append(self._display(path))
            else:
                display.append(part)
        return display

    def _display(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.repo_root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _is_inside_repo(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.repo_root)
            return True
        except ValueError:
            return False

    def _compact(self, value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        value = value.strip()
        if len(value) <= OUTPUT_LIMIT:
            return value
        return value[:OUTPUT_LIMIT] + "...[truncated]"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DZP script orchestration coordinator")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Path to script dependency registry")
    sub = parser.add_subparsers(dest="command", required=True)

    event = sub.add_parser("event", help="Run a lifecycle event")
    event.add_argument("event_name")
    event.add_argument("--strict", action="store_true", help="Treat the event as fail-closed")
    event.add_argument("--dry-run", action="store_true", help="Show steps without executing")
    event.add_argument("--json", action="store_true", help="Print JSON result")

    status = sub.add_parser("status", help="Show registry and last event status")
    status.add_argument("--json", action="store_true")

    doctor = sub.add_parser("doctor", help="Validate coordinator setup")
    doctor.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    coordinator = ScriptCoordinator(registry_path=args.registry)
    try:
        if args.command == "event":
            return coordinator.run_event(
                args.event_name,
                strict=args.strict,
                dry_run=args.dry_run,
                json_output=args.json,
            )
        if args.command == "status":
            return coordinator.status(json_output=args.json)
        if args.command == "doctor":
            return coordinator.doctor(json_output=args.json)
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
