# ============================================================
# File: application/commands/command_result.py
# GridForge V2 — Application Command Result
# Author: Subhendu Mishra
# ============================================================
"""Immutable result returned by application command execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    """Represent successful or failed command execution."""

    success: bool
    value: Any = None
    error: str | None = None

    @classmethod
    def ok(cls, value: Any = None) -> "CommandResult":
        return cls(success=True, value=value)

    @classmethod
    def failure(cls, error: str) -> "CommandResult":
        if not error:
            raise ValueError("error must not be empty")
        return cls(success=False, error=error)


__all__ = ["CommandResult"]
