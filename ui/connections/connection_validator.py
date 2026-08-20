# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/connection_validator.py
#
# Purpose:
#     Validates an SLD connection candidate before it is committed.
#
# Architectural Role:
#     Central validation boundary for UI-level connection rules.
#
# Responsibilities:
#     - validate terminal existence;
#     - reject self-connections;
#     - reject duplicate connections;
#     - validate basic terminal compatibility;
#     - return explicit validation results.
#
# Does NOT:
#     - perform full electrical topology analysis;
#     - run power-flow;
#     - calculate impedances;
#     - mutate the model;
#
# Important:
#     This is deliberately a UI structural validator. The Core remains
#     authoritative for electrical-network validity.
#
# ============================================================

"""
GridForge V2 — Connection Validator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .connection import Connection
from .terminal_resolver import TerminalResolver


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of connection validation.
    """

    valid: bool
    reason: str = ""

    @classmethod
    def success(cls) -> "ValidationResult":
        return cls(True, "")

    @classmethod
    def failure(
        cls,
        reason: str,
    ) -> "ValidationResult":
        return cls(False, reason)


class ConnectionValidator:
    """
    Validates logical connection candidates.
    """

    def __init__(
        self,
        terminal_resolver: TerminalResolver,
    ) -> None:
        if terminal_resolver is None:
            raise ValueError(
                "terminal_resolver must not be None"
            )

        self._terminal_resolver = terminal_resolver

    def validate(
        self,
        source_terminal_id: str,
        target_terminal_id: str,
        existing_connections: Iterable[Connection],
    ) -> ValidationResult:
        if not source_terminal_id:
            return ValidationResult.failure(
                "Source terminal is empty"
            )

        if not target_terminal_id:
            return ValidationResult.failure(
                "Target terminal is empty"
            )

        if source_terminal_id == target_terminal_id:
            return ValidationResult.failure(
                "A terminal cannot connect to itself"
            )

        if not self._terminal_resolver.contains(
            source_terminal_id
        ):
            return ValidationResult.failure(
                f"Unknown source terminal: "
                f"{source_terminal_id}"
            )

        if not self._terminal_resolver.contains(
            target_terminal_id
        ):
            return ValidationResult.failure(
                f"Unknown target terminal: "
                f"{target_terminal_id}"
            )

        source = self._terminal_resolver.require(
            source_terminal_id
        )
        target = self._terminal_resolver.require(
            target_terminal_id
        )

        if source.equipment_id == target.equipment_id:
            return ValidationResult.failure(
                "Terminals belonging to the same equipment "
                "cannot be connected by a normal SLD connection"
            )

        for connection in existing_connections:
            if {
                connection.source_terminal_id,
                connection.target_terminal_id,
            } == {
                source_terminal_id,
                target_terminal_id,
            }:
                return ValidationResult.failure(
                    "The connection already exists"
                )

        return ValidationResult.success()
