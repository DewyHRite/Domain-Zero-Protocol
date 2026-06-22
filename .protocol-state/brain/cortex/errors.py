"""Shared Cortex exceptions and exit codes."""


class CortexError(Exception):
    """Base class for expected Cortex failures."""

    exit_code = 1


class DependencyError(CortexError):
    """Required vector or embedding dependency is unavailable."""

    exit_code = 3


class UnsafePathError(CortexError):
    """A configured path escapes the accepted safety boundary."""

    exit_code = 4


class QueryUnavailable(CortexError):
    """Query cannot run because the store is missing or empty."""

    exit_code = 2


class SchemaTooNewError(CortexError):
    """The Cortex DB schema (PRAGMA user_version) is newer than this engine
    supports. v9.3.4 preflight (PLAN-DESIGN-001 §0): an old engine must fail
    closed rather than write v1 rows into a migrated (v2) shared DB."""

    exit_code = 5


class SchemaMismatchError(CortexError):
    """The canonical schema marker (PRAGMA user_version) and its metadata mirror
    (metadata.schema_version) disagree. Indicates a partially migrated or
    repaired DB; the engine fails closed instead of guessing (IMPL-001)."""

    exit_code = 6


class GraphSchemaError(CortexError):
    """Graph tables are absent or at incompatible schema — requires v9.6.0+ engine.
    Raised when a caller attempts a graph operation on a v2 (pre-migration) DB,
    or when required graph tables are missing from the schema. (WI-5, v9.6.0)"""

    exit_code = 7


class CortexKeyUnavailableError(CortexError):
    """The encryption key could not be resolved (no env key, no keystore entry,
    and no interactive TTY for a passphrase prompt). v9.8.0 PLAN-CORTEX-ENC-001
    (SEC-CORTEX-ACCESS-007b): non-interactive lifecycle events must surface this
    as exit code 8 and fail-soft when the step is not required."""

    exit_code = 8
