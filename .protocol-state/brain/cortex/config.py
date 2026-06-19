"""Load and validate Cortex configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import os

import yaml

from . import paths


DEFAULT_CONFIG: dict[str, Any] = {
    "model": "BAAI/bge-small-en-v1.5",
    "top_k": 5,
    "max_file_bytes": 6_000_000,  # SEC-CORTEX-003 (v9.3.2): config-driven per-file cap
    # SEC-002 (v9.3.3): positive ALLOWLIST of indexable extensions (defense-in-depth with
    # the existing BINARY_SUFFIXES denylist). Files not in this list are excluded.
    # Empty string key ("") allows extension-less files only when explicitly listed.
    #
    # DESIGN INTENT (v9.3.3): Cortex is NOT a protocol-only index. This default set is
    # deliberately project-agnostic — it spans the mainstream documentation, scripting,
    # config/data, web, and systems languages so Cortex works out-of-the-box for ANY user
    # project, not just the DZP files. Scope (which folders/files are indexed) is separately
    # user-configurable via include_folders / include_code / include_files in brain.config.yaml,
    # and users may add or trim extensions here. Binary formats remain blocked by
    # BINARY_SUFFIXES, oversized files by max_file_bytes, and secrets by contains_secret —
    # so broadening the allowlist does not weaken the trust or secret-scrub guarantees.
    "index_extensions": [
        # Docs / prose
        ".md", ".markdown", ".txt", ".rst", ".adoc",
        # Python
        ".py", ".pyi",
        # Shell / scripting
        ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
        # Config / data / serialization
        ".yaml", ".yml", ".json", ".jsonc", ".toml", ".ini", ".cfg", ".conf",
        ".properties", ".xml", ".csv", ".tsv",
        # Web / JS / TS / styles
        ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte",
        ".css", ".scss", ".sass", ".less",
        # JVM / systems languages
        ".go", ".rs", ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
        ".java", ".kt", ".kts", ".scala", ".swift",
        # Other languages
        ".rb", ".php", ".pl", ".lua", ".r", ".jl", ".ex", ".exs", ".erl",
        ".clj", ".cljs", ".hs", ".dart", ".groovy",
        # Query / schema / IDL
        ".sql", ".graphql", ".gql", ".proto",
        # Build / infra
        ".gradle", ".cmake", ".mk", ".tf", ".hcl",
        # Markup
        ".tex",
    ],
    # SEC-002 (v9.3.3): per-file chunk cap. 0 = unlimited (no cap). Positive values
    # drop the entire file and emit a warning when the chunk count would exceed this.
    "max_file_chunks": 0,  # 0 = no cap (safe default; can be tightened in config)
    # SCOPE (project-agnostic): these defaults cover a DZP install, but any user project
    # extends them in brain.config.yaml — e.g. include_code: ["src", "lib", "app"] — to index
    # its own source tree. Cortex indexes whatever scope you point it at, not just protocol files.
    "include_folders": ["protocol", "docs"],
    "include_files": [
        "CLAUDE.md",
        "protocol/CLAUDE.md",
        "AI_INSTRUCTIONS.md",
        "README.md",
        ".protocol-state/session_monitor.py",
        ".protocol-state/project_state_manager.py",
        ".protocol-state/troubleshooting_tracker.py",
    ],
    "include_protected": [
        ".protocol-state/dev-notes.md",
        ".protocol-state/security-review.md",
        ".dzp-domain/domain.record.md",
    ],
    "include_reports": [],
    "include_code": ["scripts"],
    "exclude_tokens": [
        "backups",
        "__pycache__",
        "node_modules",
        ".env",
        ".dzp-killswitch",
        "brain.db",
        "cortex-snapshot.md",
        "project-state.json",
        "troubleshooting-history.json",
        ".protocol-state/internal-docs",
        ".protocol-state/stress_tests",
        ".protocol-state/system-update-framework",
        "internal-docs",
        "docs/superpowers",
    ],
    # FEAT-CORTEX-EXCL-001 (v9.4.1): more-specific re-include list that overrides
    # broader exclude_tokens entries.  Matching is on the normalised lowercase
    # relative POSIX path, same basis as exclude_tokens — a path is re-admitted
    # only when it equals an exception entry OR starts with "<entry>/", so partial
    # path-component matches (e.g. "plans-archive" vs "plans") are not widened.
    # All other guards (BINARY_SUFFIXES, index_extensions, max_file_bytes,
    # generated-files, contains_secret at chunk time) still apply to re-admitted
    # files — the exception bypasses only the exclude_tokens sweep.
    "exclude_exceptions": [
        # Re-admit DZP planning documents while keeping the rest of docs/superpowers/
        # (Anthropic skill boilerplate) excluded.
        "docs/superpowers/plans",
    ],
    "chunk": {"md_max_chars": 1200, "code_max_chars": 1500, "overlap": 120},
    "index": {"batch_size": 64},
    # WI-14 (PLAN-CORTEX-GRAPH-001 Phase 2, v9.6.0): Hybrid retrieval config.
    # query_cache_ttl_seconds: 0 means DISABLED by default (Maki F5 — opt-in).
    # Set > 0 in brain.config.yaml to enable result caching.
    "query_cache_ttl_seconds": 0,
    # rrf_k: Reciprocal Rank Fusion k-constant (TRUE RRF formula, Maki F1).
    # score(rank) = 1 / (rrf_k + rank). Standard default is 60.
    "rrf_k": 60,
    # hybrid_recency_half_life_days: half-life for additive recency bias.
    # A chunk indexed 30 days ago gets half the recency boost of one indexed today.
    "hybrid_recency_half_life_days": 30,
    # bm25_enabled: set False to disable BM25 even when FTS5 is available.
    # Useful for environments where BM25 adds latency without recall benefit.
    "bm25_enabled": True,
    # WI-20 (v9.6.0): cold_start_threshold — brain seed only fires when content_refs
    # count is below this value. Prevents seeding an already-populated index.
    # Set to 0 to disable cold-start seeding entirely.
    "cold_start_threshold": 50,
    # -------------------------------------------------------------------
    # WI-S3-1 (Stage 3 Phase 1, v9.7.0): Storage Elasticity — eviction config.
    # -------------------------------------------------------------------
    # storage_budget_mb: per-install storage cap (in MB). None = unlimited.
    # When set and the DB size exceeds this value after an index run, the
    # eviction engine (_evict_to_budget) is invoked (fail-soft).
    # Must be None or a POSITIVE INTEGER (bool is rejected per SEC-CORTEX-004 pattern).
    "storage_budget_mb": None,
    # compaction_threshold_mb: DB size at which compaction (VACUUM) is considered.
    # Phase 2 (Lever 3) reserved — config key present now for forward compatibility.
    "compaction_threshold_mb": 200,
    # compaction_budget_fraction: fraction of storage_budget_mb to target during compaction.
    # Phase 2 (Lever 4) reserved — config key present now for forward compatibility.
    "compaction_budget_fraction": 0.8,
    # lru_eviction_enabled: opt-in LRU (least-recently-recalled) eviction within tiers.
    # DEFAULT: False — S3-RISK-004 (privacy): last_recalled_at is a new data-collection
    # surface. LRU tracking is disabled by default. Set True to enable recall-hit
    # tracking (last_recalled_at updated after every search) and LRU within-tier ordering.
    "lru_eviction_enabled": False,
    # group_storage_budget_mb: shared-group storage cap (Lever 5 reserved).
    # Phase 2+ only — config key present now for forward compatibility.
    "group_storage_budget_mb": None,
    # backup_retention_count: maximum number of backup files to keep in
    # <data_dir>/backups/.  Oldest brain-*.db files beyond this count are pruned
    # after each new backup.  SEC-CORTEX-ACCESS-009 (v9.7.1).
    "backup_retention_count": 3,
}


def config_path(repo_root: str | Path) -> Path:
    return Path(repo_root) / ".protocol-state" / "brain" / "brain.config.yaml"


def load(repo_root: str | Path, *, allow_unsafe: bool = False) -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    path = config_path(repo_root)
    if path.exists():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError("brain.config.yaml must contain a mapping")
        cfg = _deep_merge(cfg, loaded)

    env_data_dir = os.environ.get("DZP_CORTEX_DATA_DIR")
    if env_data_dir:
        cfg["data_dir"] = env_data_dir

    validate(cfg, repo_root, allow_unsafe=allow_unsafe)
    return cfg


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


_REDOS_ADVERSARIAL = "a" * 100 + "!"
_REDOS_TIMEOUT_SECONDS = 0.5  # budget: 500 ms per pattern


def _redos_probe(compiled_pattern, entity_type: str, pattern_str: str) -> None:
    """SEC-GRAPH-009 (v9.6.0): ReDoS heuristic — match adversarial string under timeout.

    Attempts to detect catastrophic-backtracking patterns before they reach ingest.

    Strategy (in priority order):
      1. `regex` module with timeout kwarg (best cross-platform option, if installed).
      2. `threading.Timer` watchdog (stdlib, available on CPython/PyPy).
      3. Best-effort fallback: run without timeout (documents residual risk).

    Raises ValueError for patterns that exceed the time budget or trigger a known
    catastrophic-backtracking signal.

    Documented residual limitation: on platforms without threading support, patterns
    that catastrophically backtrack may not be caught here and will only fail at ingest
    time. The timeout budget (_REDOS_TIMEOUT_SECONDS) should be tuned if needed.
    """
    import re as _re

    # Strategy 1: `regex` module timeout (best option)
    try:
        import regex as _regex  # type: ignore[import]
        try:
            _regex.match(pattern_str, _REDOS_ADVERSARIAL, timeout=_REDOS_TIMEOUT_SECONDS)
        except _regex.TimeoutError:
            raise ValueError(
                f"entity_extraction_patterns[{entity_type!r}]: pattern rejected — "
                f"ReDoS heuristic probe exceeded {_REDOS_TIMEOUT_SECONDS}s timeout on "
                f"adversarial input. Avoid unbounded quantifiers on wide character "
                f"classes (e.g. (a+)+ or (.*)* style). Pattern: {pattern_str!r}"
            )
        return  # pattern passed the probe
    except ImportError:
        pass  # `regex` not installed — fall through to threading watchdog

    # Strategy 2: threading.Timer watchdog (stdlib)
    import threading

    timed_out = threading.Event()
    probe_raised: list[Exception] = []

    def _run():
        try:
            compiled_pattern.match(_REDOS_ADVERSARIAL)
        except Exception as exc:
            probe_raised.append(exc)

    t = threading.Thread(target=_run, daemon=True)
    timer = threading.Timer(_REDOS_TIMEOUT_SECONDS, timed_out.set)
    timer.start()
    t.start()
    t.join(timeout=_REDOS_TIMEOUT_SECONDS + 0.1)
    timer.cancel()

    if timed_out.is_set() or t.is_alive():
        raise ValueError(
            f"entity_extraction_patterns[{entity_type!r}]: pattern rejected — "
            f"ReDoS heuristic probe exceeded {_REDOS_TIMEOUT_SECONDS}s timeout on "
            f"adversarial input. Avoid unbounded quantifiers on wide character "
            f"classes (e.g. (a+)+ or (.*)* style). Pattern: {pattern_str!r}"
        )

    # Pattern passed — no ReDoS detected


def validate(cfg: dict[str, Any], repo_root: str | Path | None = None, *, allow_unsafe: bool = False) -> None:
    if not isinstance(cfg.get("model"), str) or not cfg["model"].strip():
        raise ValueError("model must be a non-empty string")
    if int(cfg.get("top_k", 0)) <= 0:
        raise ValueError("top_k must be positive")
    # SEC-CORTEX-004 (v9.3.2): reject non-positive / non-int / bool max_file_bytes.
    # bool is a subclass of int, so it must be rejected explicitly.
    mfb = cfg.get("max_file_bytes", DEFAULT_CONFIG["max_file_bytes"])
    if isinstance(mfb, bool) or not isinstance(mfb, int) or mfb <= 0:
        raise ValueError("max_file_bytes must be a positive integer")
    for key in ("include_folders", "include_files", "include_protected", "include_reports", "include_code", "exclude_tokens"):
        if not isinstance(cfg.get(key), list):
            raise ValueError(f"{key} must be a list")
    # FEAT-CORTEX-EXCL-001 (v9.4.1): validate exclude_exceptions list.
    ee = cfg.get("exclude_exceptions", DEFAULT_CONFIG["exclude_exceptions"])
    if not isinstance(ee, list):
        raise ValueError("exclude_exceptions must be a list")
    if not all(isinstance(e, str) for e in ee):
        raise ValueError("exclude_exceptions entries must all be strings")
    # SEC-EXCL-001 (P3): exclude_exceptions match the normalised relative POSIX path,
    # so absolute / drive-rooted / UNC / leading-separator / ".."-traversal entries can
    # never legitimately match. They were accepted silently (functionally inert) — instead
    # fail closed at load time (OWASP A05 / CWE-1284) naming the offending entry.
    for e in ee:
        if e.startswith("/") or e.startswith("\\"):
            raise ValueError(
                f"exclude_exceptions entry must be a relative path, not absolute/rooted: {e!r}"
            )
        if len(e) >= 2 and e[1] == ":" and e[0].isalpha():
            raise ValueError(
                f"exclude_exceptions entry must be a relative path, not a drive-rooted path: {e!r}"
            )
        if ".." in e.replace("\\", "/").split("/"):
            raise ValueError(
                f"exclude_exceptions entry must not contain a '..' path-traversal segment: {e!r}"
            )
    # SEC-002 (v9.3.3): validate extension allowlist and chunk cap.
    ie = cfg.get("index_extensions", DEFAULT_CONFIG["index_extensions"])
    if not isinstance(ie, list):
        raise ValueError("index_extensions must be a list")
    # SEC-CORTEX-DIAG-002 (v9.3.3): fail at load time on non-string entries rather
    # than crashing later in _safe_candidate when ext.lower() hits a non-str.
    if not all(isinstance(ext, str) for ext in ie):
        raise ValueError("index_extensions entries must all be strings")
    mfc = cfg.get("max_file_chunks", DEFAULT_CONFIG["max_file_chunks"])
    if isinstance(mfc, bool) or not isinstance(mfc, int) or mfc < 0:
        raise ValueError("max_file_chunks must be a non-negative integer (0 = unlimited)")
    chunk = cfg.get("chunk")
    if not isinstance(chunk, dict):
        raise ValueError("chunk must be a mapping")
    index = cfg.get("index")
    if not isinstance(index, dict) or int(index.get("batch_size", 0)) <= 0:
        raise ValueError("index.batch_size must be positive")
    if cfg.get("data_dir") and repo_root is not None:
        paths.validate_data_dir(Path(str(cfg["data_dir"])), repo_root, allow_unsafe=allow_unsafe)
    # WI-S3-1 (v9.7.0): validate storage elasticity keys.
    # storage_budget_mb: None (unlimited) or a positive integer (not bool, not 0, not negative).
    smb = cfg.get("storage_budget_mb", DEFAULT_CONFIG["storage_budget_mb"])
    if smb is not None:
        # bool is a subclass of int — reject it explicitly (SEC-CORTEX-004 pattern).
        if isinstance(smb, bool) or not isinstance(smb, int) or smb <= 0:
            raise ValueError(
                "storage_budget_mb must be None (unlimited) or a positive integer; "
                f"got {smb!r}"
            )
    # lru_eviction_enabled: must be a plain bool.
    lru = cfg.get("lru_eviction_enabled", DEFAULT_CONFIG["lru_eviction_enabled"])
    if not isinstance(lru, bool):
        raise ValueError(
            f"lru_eviction_enabled must be a bool (True/False); got {type(lru).__name__!r}"
        )
    # SEC-UNIFIED-003 (P2, WI-22): entity_extraction_patterns config-override validation.
    # At validate() time, attempt re.compile() on each override pattern and catch re.error.
    # Reject invalid patterns with a clear error message to prevent ReDoS/injection at ingest.
    # Pattern values must be valid Python regex strings; keys are entity type names (strings).
    #
    # SEC-GRAPH-009 (v9.6.0): After the syntax check, each pattern is probed with a
    # fixed adversarial string ("a" * 100 + "!") under a short timeout to detect
    # catastrophic-backtracking (ReDoS) patterns before they can be used at ingest time.
    # Timeout strategy: use the `regex` module's timeout parameter if available (best
    # cross-platform option), otherwise fall back to threading-based watchdog. If neither
    # is feasible (e.g. no thread support), the probe is still attempted (best-effort).
    # Known limitation: on platforms without threading or `regex`, the probe is best-effort;
    # patterns that would catastrophically backtrack may still be accepted but will trigger
    # the ReDoS at ingest time (logged as a documented residual limitation).
    eep = cfg.get("entity_extraction_patterns")
    if eep is not None:
        if not isinstance(eep, dict):
            raise ValueError(
                "entity_extraction_patterns must be a mapping of entity_type -> regex string"
            )
        import re as _re
        for entity_type, pattern_str in eep.items():
            if not isinstance(pattern_str, str):
                raise ValueError(
                    f"entity_extraction_patterns[{entity_type!r}] must be a string; "
                    f"got {type(pattern_str).__name__!r}"
                )
            try:
                compiled = _re.compile(pattern_str)
            except _re.error as exc:
                raise ValueError(
                    f"entity_extraction_patterns[{entity_type!r}]: invalid Python regex: {exc}\n"
                    f"  Pattern: {pattern_str!r}\n"
                    f"  Note: config-supplied patterns are compiled at ingest time and must be "
                    f"valid Python regex syntax (re module). Catastrophic-backtracking risk: "
                    f"avoid unbounded quantifiers on wide character classes in user-supplied "
                    f"patterns. See cortex/extractor.py for the default bounded patterns."
                ) from exc
            # SEC-GRAPH-009: ReDoS heuristic probe
            _redos_probe(compiled, entity_type, pattern_str)


def is_stub_model(cfg: dict[str, Any]) -> bool:
    return str(cfg.get("model", "")).upper() == "STUB"
