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
