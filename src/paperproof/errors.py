"""Domain error types carrying the CLI exit-code convention (docs/10 §4).

exit 0  ok
exit 1  validation/domain failure (errors[] carries V-* ids)
exit 2  usage error
exit 3  corrupted state (verify failure, bad JSONL line)
"""

from __future__ import annotations

from typing import Any


class PaperproofError(Exception):
    """Base domain error. Carries structured errors + optional data/warnings."""

    exit_code = 1

    def __init__(
        self,
        errors: list[str] | None = None,
        *,
        data: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        message: str | None = None,
    ) -> None:
        self.errors = list(errors) if errors else ([message] if message else [])
        self.data = data or {}
        self.warnings = warnings or []
        super().__init__("; ".join(self.errors) or self.__class__.__name__)


class DomainError(PaperproofError):
    """Expected, handleable failure (exit 1)."""

    exit_code = 1


class UsageError(PaperproofError):
    """Bad invocation (exit 2)."""

    exit_code = 2


class CorruptStateError(PaperproofError):
    """Corrupted state - stop and tell the human (exit 3)."""

    exit_code = 3
