# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/terminal_resolver.py
#
# Purpose:
#     Resolve logical equipment terminals for SLD connection
#     interaction.
#
# Architectural Role:
#     TerminalResolver is the logical lookup boundary between
#     spatial/UI interaction and logical terminal identity.
#
# Responsibilities:
#     - register logical EquipmentTerminal objects;
#     - unregister logical terminals;
#     - resolve terminal IDs;
#     - require known terminal IDs;
#     - resolve terminal ownership;
#     - enumerate registered terminals;
#     - enumerate terminals belonging to equipment;
#     - report registry membership;
#     - clear the registry.
#
# Does NOT:
#     - perform graphical hit testing;
#     - access QGraphicsItem objects;
#     - perform snapping;
#     - create connections;
#     - route connections;
#     - validate topology;
#     - mutate Core topology;
#     - own equipment objects;
#     - own terminal objects.
#
# Architecture
# ------------
#
#     Canvas / Interaction
#             |
#             v
#     spatial candidate
#             |
#             v
#     TerminalResolver
#             |
#       +-----+------+
#       |            |
#       v            v
#    Terminal    Equipment ID
#       |
#       v
# ConnectionValidator
#
# Ownership
# ---------
# EquipmentTerminal instances remain externally owned.
# TerminalResolver stores references to them only for logical
# lookup during the lifetime of the connection interaction
# context.
#
# Qt
# --
# No Qt dependency is permitted in this module.
#
# Core
# ----
# TerminalResolver has no direct dependency on GridForge Core.
#
# ============================================================

"""
GridForge V2 — Terminal Resolver.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Dict, Optional

from ui.equipment.terminal import EquipmentTerminal


class TerminalResolver:
    """
    Registry and lookup service for logical SLD terminals.

    TerminalResolver is intentionally a small, deterministic
    service. It translates stable terminal identifiers into
    externally owned EquipmentTerminal objects and provides
    equipment ownership lookup.

    It does not perform spatial or graphical operations.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Initialize an empty terminal registry.
        """

        self._terminals: Dict[
            str,
            EquipmentTerminal,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        terminal: EquipmentTerminal,
    ) -> None:
        """
        Register one logical terminal.

        Parameters
        ----------
        terminal:
            Externally owned EquipmentTerminal instance.

        Raises
        ------
        TypeError
            If terminal is not an EquipmentTerminal or does not
            expose a valid terminal identifier.

        ValueError
            If the terminal identifier is empty or already
            registered.
        """

        self._validate_terminal(
            terminal
        )

        terminal_id = self._normalize_id(
            terminal.terminal_id,
            "terminal_id",
        )

        if terminal_id in self._terminals:
            raise ValueError(
                "Terminal already registered: "
                f"{terminal_id}"
            )

        self._terminals[
            terminal_id
        ] = terminal

    # --------------------------------------------------------

    def unregister(
        self,
        terminal_id: str,
    ) -> EquipmentTerminal:
        """
        Remove and return a registered terminal.

        Parameters
        ----------
        terminal_id:
            Stable logical terminal identifier.

        Raises
        ------
        KeyError
            If the terminal is not registered.
        """

        terminal_id = self._normalize_id(
            terminal_id,
            "terminal_id",
        )

        try:
            return self._terminals.pop(
                terminal_id
            )

        except KeyError as exc:
            raise KeyError(
                terminal_id
            ) from exc

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        terminal_id: str,
    ) -> Optional[EquipmentTerminal]:
        """
        Return a registered terminal if present.

        Unknown terminal IDs return None.

        Parameters
        ----------
        terminal_id:
            Stable logical terminal identifier.

        Raises
        ------
        TypeError
            If terminal_id is not a string.

        ValueError
            If terminal_id is empty.
        """

        terminal_id = self._normalize_id(
            terminal_id,
            "terminal_id",
        )

        return self._terminals.get(
            terminal_id
        )

    # --------------------------------------------------------

    def require(
        self,
        terminal_id: str,
    ) -> EquipmentTerminal:
        """
        Return a registered terminal.

        Unlike get(), this method raises when the terminal is
        unknown.

        Raises
        ------
        KeyError
            If the terminal is not registered.
        """

        terminal_id = self._normalize_id(
            terminal_id,
            "terminal_id",
        )

        terminal = self._terminals.get(
            terminal_id
        )

        if terminal is None:
            raise KeyError(
                f"Unknown terminal: {terminal_id}"
            )

        return terminal

    # --------------------------------------------------------

    def contains(
        self,
        terminal_id: str,
    ) -> bool:
        """
        Return True when terminal_id is registered.
        """

        terminal_id = self._normalize_id(
            terminal_id,
            "terminal_id",
        )

        return terminal_id in self._terminals

    # ========================================================
    # EQUIPMENT OWNERSHIP
    # ========================================================

    def get_equipment_id(
        self,
        terminal_id: str,
    ) -> Optional[str]:
        """
        Resolve the owning equipment ID for a terminal.

        Parameters
        ----------
        terminal_id:
            Stable logical terminal identifier.

        Returns
        -------
        Optional[str]
            Owning equipment identifier, or None when the
            terminal is not registered.

        Notes
        -----
        EquipmentTerminal remains the authoritative source for
        the ownership relationship. This resolver only exposes
        that relationship through the terminal lookup boundary.
        """

        terminal = self.get(
            terminal_id
        )

        if terminal is None:
            return None

        equipment_id = getattr(
            terminal,
            "equipment_id",
            None,
        )

        if equipment_id is None:
            return None

        return self._normalize_id(
            equipment_id,
            "equipment_id",
        )

    # --------------------------------------------------------

    def require_equipment_id(
        self,
        terminal_id: str,
    ) -> str:
        """
        Resolve and require the owning equipment ID.

        Raises
        ------
        KeyError
            If the terminal is not registered.

        ValueError
            If the registered terminal does not expose a valid
            equipment identifier.
        """

        terminal = self.require(
            terminal_id
        )

        equipment_id = getattr(
            terminal,
            "equipment_id",
            None,
        )

        if equipment_id is None:
            raise ValueError(
                "Registered terminal has no equipment_id: "
                f"{terminal.terminal_id}"
            )

        return self._normalize_id(
            equipment_id,
            "equipment_id",
        )

    # ========================================================
    # ENUMERATION
    # ========================================================

    def terminals(
        self,
    ) -> tuple[EquipmentTerminal, ...]:
        """
        Return all registered terminals.

        A tuple snapshot is returned so callers cannot mutate
        the registry through the returned collection.
        """

        return tuple(
            self._terminals.values()
        )

    # --------------------------------------------------------

    def terminal_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return all registered terminal IDs.

        The registry insertion order is preserved.
        """

        return tuple(
            self._terminals.keys()
        )

    # --------------------------------------------------------

    def terminals_for_equipment(
        self,
        equipment_id: str,
    ) -> tuple[EquipmentTerminal, ...]:
        """
        Return all terminals belonging to one equipment object.

        Parameters
        ----------
        equipment_id:
            Stable logical equipment identifier.

        Returns
        -------
        tuple[EquipmentTerminal, ...]
            Matching terminal snapshot in registration order.
        """

        equipment_id = self._normalize_id(
            equipment_id,
            "equipment_id",
        )

        return tuple(
            terminal
            for terminal in self._terminals.values()
            if getattr(
                terminal,
                "equipment_id",
                None,
            )
            == equipment_id
        )

    # --------------------------------------------------------

    def has_equipment(
        self,
        equipment_id: str,
    ) -> bool:
        """
        Return True when at least one registered terminal belongs
        to the specified equipment.
        """

        equipment_id = self._normalize_id(
            equipment_id,
            "equipment_id",
        )

        return any(
            getattr(
                terminal,
                "equipment_id",
                None,
            )
            == equipment_id
            for terminal in self._terminals.values()
        )

    # ========================================================
    # REGISTRY STATE
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all registered terminal references.

        EquipmentTerminal instances themselves are not destroyed.
        """

        self._terminals.clear()

    # --------------------------------------------------------

    def __len__(
        self,
    ) -> int:
        """
        Return the number of registered terminals.
        """

        return len(
            self._terminals
        )

    # --------------------------------------------------------

    def __contains__(
        self,
        terminal_id: object,
    ) -> bool:
        """
        Support:

            terminal_id in resolver

        Invalid/non-string values simply return False.
        """

        if not isinstance(
            terminal_id,
            str,
        ):
            return False

        terminal_id = terminal_id.strip()

        if not terminal_id:
            return False

        return terminal_id in self._terminals

    # --------------------------------------------------------

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "TerminalResolver("
            f"count={len(self._terminals)}"
            ")"
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_terminal(
        terminal: EquipmentTerminal,
    ) -> None:
        """
        Validate a terminal registration object.
        """

        if not isinstance(
            terminal,
            EquipmentTerminal,
        ):
            raise TypeError(
                "terminal must be an EquipmentTerminal."
            )

        TerminalResolver._normalize_id(
            terminal.terminal_id,
            "terminal.terminal_id",
        )

        TerminalResolver._normalize_id(
            terminal.equipment_id,
            "terminal.equipment_id",
        )

    # --------------------------------------------------------

    @staticmethod
    def _normalize_id(
        value: str,
        name: str,
    ) -> str:
        """
        Validate and normalize a stable logical identifier.

        IDs are stripped of surrounding whitespace.

        Empty identifiers are rejected.

        Boolean values are explicitly rejected because bool is a
        subclass of int and should never be accepted as a logical
        identifier accidentally.
        """

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{name} must not be empty."
            )

        return value


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "TerminalResolver",
]
