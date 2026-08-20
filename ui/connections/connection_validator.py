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
#     Central UI-level structural validation boundary for the
#     connection workflow.
#
# Responsibilities:
#     - validate source terminal identity;
#     - validate target terminal identity;
#     - validate terminal existence;
#     - reject self-connections;
#     - reject same-equipment connections;
#     - reject duplicate connections;
#     - return explicit immutable validation results.
#
# Does NOT:
#     - create connections;
#     - mutate connection state;
#     - modify TerminalResolver;
#     - perform graphical hit testing;
#     - route graphical lines;
#     - perform electrical topology analysis;
#     - calculate impedances;
#     - execute power-flow;
#     - modify Core domain state.
#
# Architectural Boundary:
#
#     Canvas / Tool
#          |
#          v
#     TerminalResolver
#          |
#          v
#     ConnectionValidator
#          |
#          v
#     Connection
#          |
#          v
#     Core topology / domain validation
#
# Core remains authoritative for electrical-network validity.
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


# ============================================================
# VALIDATION RESULT
# ============================================================


@dataclass(frozen=True)
class ValidationResult:
    """
    Immutable result of connection validation.

    Attributes
    ----------
    valid:
        True when the candidate satisfies all UI-level
        structural validation rules.

    reason:
        Human-readable diagnostic reason when validation fails.
        Empty on success.
    """

    valid: bool
    reason: str = ""

    # --------------------------------------------------------

    @classmethod
    def success(
        cls,
    ) -> "ValidationResult":
        """
        Create a successful validation result.
        """

        return cls(
            valid=True,
            reason="",
        )

    # --------------------------------------------------------

    @classmethod
    def failure(
        cls,
        reason: str,
    ) -> "ValidationResult":
        """
        Create a failed validation result.

        Parameters
        ----------
        reason:
            Explicit diagnostic reason.
        """

        if not isinstance(
            reason,
            str,
        ):
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
    Validates logical SLD connection candidates.

    This validator owns only UI-level structural rules.

    It does not own:

        - terminals;
        - connections;
        - equipment;
        - Core topology;
        - electrical validity;
        - graphical representation.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        terminal_resolver: TerminalResolver,
    ) -> None:
        """
        Initialize the connection validator.

        Parameters
        ----------
        terminal_resolver:
            Resolver providing authoritative UI terminal lookup.
        """

        if terminal_resolver is None:
            raise ValueError(
                "terminal_resolver must not be None."
            )

        if not isinstance(
            terminal_resolver,
            TerminalResolver,
        ):
            raise TypeError(
                "terminal_resolver must be a "
                "TerminalResolver."
            )

        self._terminal_resolver = (
            terminal_resolver
        )

    # ========================================================
    # ACCESS
    # ========================================================

    @property
    def terminal_resolver(
        self,
    ) -> TerminalResolver:
        """
        Return the terminal resolver used by this validator.

        The resolver remains externally owned.
        """

        return self._terminal_resolver

    # --------------------------------------------------------

    def get_terminal_resolver(
        self,
    ) -> TerminalResolver:
        """
        Return the configured terminal resolver.
        """

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

        Validation order
        ----------------
        1. Validate terminal identifiers.
        2. Reject self-connection.
        3. Resolve source terminal.
        4. Resolve target terminal.
        5. Reject same-equipment connection.
        6. Reject duplicate connection.
        7. Return success.

        Parameters
        ----------
        source_terminal_id:
            Logical source terminal identifier.

        target_terminal_id:
            Logical target terminal identifier.

        existing_connections:
            Iterable containing currently existing UI-level
            connections.

        Returns
        -------
        ValidationResult
            Explicit immutable validation result.
        """

        # ----------------------------------------------------
        # Terminal identifier validation.
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Existing connection collection validation.
        # ----------------------------------------------------

        if existing_connections is None:
            return ValidationResult.failure(
                "existing_connections must not be None"
            )

        try:
            connections = tuple(
                existing_connections
            )

        except TypeError:
            return ValidationResult.failure(
                "existing_connections must be iterable"
            )

        # ----------------------------------------------------
        # Self-connection.
        # ----------------------------------------------------

        if (
            source_terminal_id
            == target_terminal_id
        ):
            return ValidationResult.failure(
                "A terminal cannot connect to itself"
            )

        # ----------------------------------------------------
        # Source terminal existence.
        # ----------------------------------------------------

        if not self._terminal_resolver.contains(
            source_terminal_id
        ):
            return ValidationResult.failure(
                "Unknown source terminal: "
                f"{source_terminal_id}"
            )

        # ----------------------------------------------------
        # Target terminal existence.
        # ----------------------------------------------------

        if not self._terminal_resolver.contains(
            target_terminal_id
        ):
            return ValidationResult.failure(
                "Unknown target terminal: "
                f"{target_terminal_id}"
            )

        # ----------------------------------------------------
        # Resolve logical terminals.
        # ----------------------------------------------------

        source = self._terminal_resolver.require(
            source_terminal_id
        )

        target = self._terminal_resolver.require(
            target_terminal_id
        )

        # ----------------------------------------------------
        # Same-equipment protection.
        #
        # A normal SLD connection may not connect two
        # terminals belonging to the same equipment.
        #
        # Special internal equipment topology, when required,
        # belongs to the appropriate domain/Core layer.
        # ----------------------------------------------------

        if (
            source.equipment_id
            == target.equipment_id
        ):
            return ValidationResult.failure(
                "Terminals belonging to the same equipment "
                "cannot be connected by a normal SLD connection"
            )

        # ----------------------------------------------------
        # Duplicate connection detection.
        #
        # Connections are treated as undirected at this UI
        # structural level:
        #
        #     A -> B
        #
        # is equivalent to:
        #
        #     B -> A
        #
        # Electrical directionality, where applicable, is a
        # separate domain concern.
        # ----------------------------------------------------

        for connection in connections:

            if not self._is_connection_like(
                connection
            ):
                return ValidationResult.failure(
                    "existing_connections contains an "
                    "invalid connection object"
                )

            if self._is_duplicate_connection(
                connection,
                source_terminal_id,
                target_terminal_id,
            ):
                return ValidationResult.failure(
                    "The connection already exists"
                )

        # ----------------------------------------------------
        # All UI-level structural checks passed.
        # ----------------------------------------------------

        return ValidationResult.success()

    # ========================================================
    # DUPLICATE DETECTION
    # ========================================================

    @staticmethod
    def _is_duplicate_connection(
        connection: Connection,
        source_terminal_id: str,
        target_terminal_id: str,
    ) -> bool:
        """
        Return True when an existing connection joins the same
        pair of terminals.

        Direction is deliberately ignored.
        """

        existing_source = getattr(
            connection,
            "source_terminal_id",
            None,
        )

        existing_target = getattr(
            connection,
            "target_terminal_id",
            None,
        )

        return {
            existing_source,
            existing_target,
        } == {
            source_terminal_id,
            target_terminal_id,
        }

    # ========================================================
    # CONNECTION CONTRACT
    # ========================================================

    @staticmethod
    def _is_connection_like(
        connection: object,
    ) -> bool:
        """
        Validate the minimal connection interface required by
        this validator.

        The validator intentionally depends only on the
        terminal-ID contract rather than concrete connection
        implementation details.
        """

        if connection is None:
            return False

        return (
            isinstance(
                getattr(
                    connection,
                    "source_terminal_id",
                    None,
                ),
                str,
            )
            and isinstance(
                getattr(
                    connection,
                    "target_terminal_id",
                    None,
                ),
                str,
            )
        )

    # ========================================================
    # TERMINAL IDENTIFIER VALIDATION
    # ========================================================

    @staticmethod
    def _validate_terminal_id(
        terminal_id: str,
        name: str,
    ) -> ValidationResult | None:
        """
        Validate one terminal identifier.

        Returns
        -------
        ValidationResult | None
            Failure result when invalid, otherwise None.
        """

        if not isinstance(
            terminal_id,
            str,
        ):
            return ValidationResult.failure(
                f"{name} must be a string"
            )

        if not terminal_id.strip():
            return ValidationResult.failure(
                f"{name} must not be empty"
            )

        return None

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "ConnectionValidator("
            f"terminals={len(self._terminal_resolver)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ValidationResult",
    "ConnectionValidator",
]
