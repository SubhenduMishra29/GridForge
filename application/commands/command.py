# ============================================================
# File: application/commands/command.py
# GridForge V2 — Application Command Boundary
# Author: Subhendu Mishra
# ============================================================
"""Immutable application intent representation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Command:
    """Describe an application intent without performing it."""

    name: str
    payload: Any = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must not be empty")


__all__ = ["Command"]
