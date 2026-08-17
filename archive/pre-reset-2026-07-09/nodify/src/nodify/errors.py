"""Domain errors carrying structured error lists; exit-code convention 0/1/2."""

from __future__ import annotations


class NodifyError(Exception):
    exit_code = 1

    def __init__(self, errors: list[str] | None = None, *, message: str | None = None):
        self.errors = list(errors or ([] if message is None else [message]))
        super().__init__("; ".join(self.errors))


class DomainError(NodifyError):
    exit_code = 1


class UsageError(NodifyError):
    exit_code = 2
