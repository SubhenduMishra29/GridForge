# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/connection_validator.py
#
# Purpose:
#     Validate an SLD connection candidate before commitment.
#
# Architectural Role:
#     UI-level structural validation boundary for the
#     connection workflow.
#
# Responsibilities:
#     - validate terminal identifiers;
#     - verify terminal existence;
#     - reject self-connections;
#     - reject same-equipment connections;
#     - reject duplicate connections;
#     - return immutable validation results.
#
# Does NOT:
#     - create connections;
#     - mutate connection state;
#     - perform graphical routing;
#     - perform hit testing;
#     - modify terminal data;
#     - perform electrical topology analysis;
#     - modify Core state.
#
# Core remains authoritative for electrical-network validity.
#
# ============================================================

"""
GridForge V2 — Connection Validator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, runtime_checkable

from .connection import Connection


# ============================================================
# TERMINAL RESOLVER CONTRACT
# ============================================================


@runtime_checkable
class TerminalResolverProtocol(Protocol):
    """
    Minimal resolver contract required by ConnectionValidator.

    The validator depends only on the resolver API it actually
    consumes and does not depend on the concrete resolver class.
    """

    def contains(
        self,
        terminal_id: str,
    ) -> bool:
        """Return whether a terminal exists."""

        ...

    def require(
        self,
        terminal_id: str,
    ) -> object:
        """Return a terminal or raise when it does not exist."""

        ...

    def require_equipment_id(
        self,
        terminal_id: str,
    ) -> str:
        """Return the owning equipment ID for a terminal."""

        ...


# ============================================================
# VALIDATION RESULT
# ============================================================


@dataclass(frozen=True)
class ValidationResult:
    """
    Immutable result of UI-level connection validation.

    Parameters
    ----------
    valid:
        True when all UI structural checks pass.

    reason:
        Diagnostic reason when validation fails.
        Empty when validation succeeds.
    """

    valid: bool
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.valid, bool):
            raise TypeError(
                "valid must be a boolean."
            )

        if not isinstance(self.reason, str):
            raise TypeError(
                "reason must be a string."
            )

        reason = self.reason.strip()

        if self.valid and reason:
            raise ValueError(
                "A successful validation result must have "
                "an empty reason."
            )

        if not self.valid and not reason:
            raise ValueError(
                "A failed validation result must have "
                "a non-empty reason."
            )

        object.__setattr__(
            self,
            "reason",
            reason,
        )

    @classmethod
    def success(
        cls,
    ) -> "ValidationResult":
        """Create a successful validation result."""

        return cls(
            valid=True,
            reason="",
        )

    @classmethod
    def failure(
        cls,
        reason: str,
    ) -> "ValidationResult":
        """Create a failed validation result."""

        if not isinstance(reason, str):
            raise TypeError(
                "reason must be a string."
            )

        reason = reason.strip()

        if not reason:
            raise ValueError(
                "reason must not be empty."
            )

        return cls(
            valid=False,
            reason=reason,
        )


# ============================================================
# CONNECTION VALIDATOR
# ============================================================


class ConnectionValidator:
    """
    Validate logical SLD connection candidates.

    Only UI-level structural rules belong here.

    Electrical-network validity remains the responsibility of
    the Core topology/domain layer.
    """

    def __init__(
        self,
        terminal_resolver: TerminalResolverProtocol,
    ) -> None:
        """
        Initialize the validator.

        The dependency is structural and requires the resolver
        contract defined by TerminalResolverProtocol.
        """

        if terminal_resolver is None:
            raise ValueError(
                "terminal_resolver must not be None."
            )

        if not isinstance(
            terminal_resolver,
            TerminalResolverProtocol,
        ):
            raise TypeError(
                "terminal_resolver must provide contains(), "
                "require(), and require_equipment_id()."
            )

        self._terminal_resolver = terminal_resolver

    # ========================================================
    # ACCESS
    # ========================================================

    @property
    def terminal_resolver(
        self,
    ) -> TerminalResolverProtocol:
        """Return the configured terminal resolver."""

        return self._terminal_resolver

    def get_terminal_resolver(
        self,
    ) -> TerminalResolverProtocol:
        """Return the configured terminal resolver."""

        return self._terminal_resolver

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
        source_terminal_id: str,
        target_terminal_id: str,
        existing_connections: Iterable[Connection],
    ) -> ValidationResult:
        """
        Validate an SLD connection candidate.

        Validation order:

        1. validate source identifier;
        2. validate target identifier;
        3. validate existing connection collection;
        4. reject self-connection;
        5. verify source terminal;
        6. verify target terminal;
        7. resolve equipment ownership;
        8. reject same-equipment connection;
        9. reject duplicate connection;
        10. return success.
        """

        result = self._validate_terminal_id(
            source_terminal_id,
            "source_terminal_id",
        )

        if result is not None:
            return result

        result = self._validate_terminal_id(
            target_terminal_id,
            "target_terminal_id",
        )

        if result is not None:
            return result

        if existing_connections is None:
            return ValidationResult.failure(
                "existing_connections must not be None."
            )

        try:
            connections = tuple(existing_connections)
        except TypeError:
            return ValidationResult.failure(
                "existing_connections must be iterable."
            )

        # ----------------------------------------------------
        # Self connection
        # ----------------------------------------------------

        if source_terminal_id == target_terminal_id:
            return ValidationResult.failure(
                "A terminal cannot connect to itself."
            )

        # ----------------------------------------------------
        # Terminal existence
        # ----------------------------------------------------

        if not self._terminal_resolver.contains(
            source_terminal_id
        ):
            return ValidationResult.failure(
                "Unknown source terminal: "
                f"{source_terminal_id}"
            )

        if not self._terminal_resolver.contains(
            target_terminal_id
        ):
            return ValidationResult.failure(
                "Unknown target terminal: "
                f"{target_terminal_id}"
            )

        # ----------------------------------------------------
        # Equipment ownership
        # ----------------------------------------------------

        try:
            source_equipment_id = (
                self._terminal_resolver.require_equipment_id(
                    source_terminal_id
                )
            )
        except (KeyError, LookupError):
            return ValidationResult.failure(
                "Unable to resolve source equipment for "
                f"terminal: {source_terminal_id}"
            )

        try:
            target_equipment_id = (
                self._terminal_resolver.require_equipment_id(
                    target_terminal_id
                )
            )
        except (KeyError, LookupError):
            return ValidationResult.failure(
                "Unable to resolve target equipment for "
                f"terminal: {target_terminal_id}"
            )

        if not isinstance(
            source_equipment_id,
            str,
        ) or not source_equipment_id.strip():
            return ValidationResult.failure(
                "Source terminal resolved to an invalid "
                "equipment ID."
            )

        if not isinstance(
            target_equipment_id,
            str,
        ) or not target_equipment_id.strip():
            return ValidationResult.failure(
                "Target terminal resolved to an invalid "
                "equipment ID."
            )

        # ----------------------------------------------------
        # Same equipment
        # ----------------------------------------------------

        if source_equipment_id == target_equipment_id:
            return ValidationResult.failure(
                "Terminals belonging to the same equipment "
                "cannot be connected by a normal SLD connection."
            )

        # ----------------------------------------------------
        # Duplicate connection
        # ----------------------------------------------------

        for connection in connections:

            if not self._is_connection_like(
                connection
            ):
                return ValidationResult.failure(
                    "existing_connections contains an "
                    "invalid connection object."
                )

            if self._is_duplicate_connection(
                connection,
                source_terminal_id,
                target_terminal_id,
            ):
                return ValidationResult.failure(
                    "The connection already exists."
                )

        return ValidationResult.success()

    # ========================================================
    # DUPLICATE CONNECTION
    # ========================================================

    @staticmethod
    def _is_duplicate_connection(
        connection: Connection,
        source_terminal_id: str,
        target_terminal_id: str,
    ) -> bool:
        """
        Return True when the existing connection joins the
        same terminal pair.

        Direction is ignored at this UI structural level.
        """

        existing_source = (
            connection.source_terminal_id
        )

        existing_target = (
            connection.target_terminal_id
        )

        return (
            (
                existing_source == source_terminal_id
                and existing_target == target_terminal_id
            )
            or
            (
                existing_source == target_terminal_id
                and existing_target == source_terminal_id
            )
        )

    # ========================================================
    # CONNECTION CONTRACT
    # ========================================================

    @staticmethod
    def _is_connection_like(
        connection: object,
    ) -> bool:
        """
        Validate the minimum connection contract.

        A connection must expose non-empty string source and
        target terminal identifiers.
        """

        if connection is None:
            return False

        source = getattr(
            connection,
            "source_terminal_id",
            None,
        )

        target = getattr(
            connection,
            "target_terminal_id",
            None,
        )

        return (
            isinstance(source, str)
            and bool(source.strip())
            and isinstance(target, str)
            and bool(target.strip())
        )

    # ========================================================
    # TERMINAL ID VALIDATION
    # ========================================================

    @staticmethod
    def _validate_terminal_id(
        terminal_id: str,
        name: str,
    ) -> ValidationResult | None:
        """Validate a logical terminal identifier."""

        if not isinstance(terminal_id, str):
            return ValidationResult.failure(
                f"{name} must be a string."
            )

        if not terminal_id.strip():
            return ValidationResult.failure(
                f"{name} must not be empty."
            )

        return None

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """Return a concise diagnostic representation."""

        try:
            count = len(self._terminal_resolver)
        except TypeError:
            count = "?"

        return (
            "ConnectionValidator("
            f"terminals={count}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ConnectionValidator",
    "TerminalResolverProtocol",
    "ValidationResult",
]
