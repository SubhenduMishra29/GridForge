# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/terminal_resolver.py
#
# Purpose:
#     Resolves logical equipment terminals for connection
#     interaction.
#
# Architectural Role:
#     Provides the bridge between spatial interaction and logical
#     terminal identity.
#
# Responsibilities:
#     - register terminal objects;
#     - resolve terminal IDs;
#     - retrieve equipment ownership;
#     - enumerate terminals.
#
# Does NOT:
#     - perform graphical hit testing itself;
#     - create QGraphicsItems;
#     - create connections;
#     - validate topology.
#
# Detailed Working:
#
#     Canvas interaction
#          |
#          v
#     spatial candidate
#          |
#          v
#     TerminalResolver
#          |
#          v
#     EquipmentTerminal
#          |
#          v
#     ConnectionValidator
#
# ============================================================

"""
GridForge V2 — Terminal Resolver.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from ui.equipment.terminal import EquipmentTerminal


class TerminalResolver:
    """
    Registry and lookup service for logical SLD terminals.
    """

    def __init__(self) -> None:
        self._terminals: Dict[
            str,
            EquipmentTerminal,
        ] = {}

    def register(
        self,
        terminal: EquipmentTerminal,
    ) -> None:
        if terminal.terminal_id in self._terminals:
            raise ValueError(
                f"Terminal already registered: "
                f"{terminal.terminal_id}"
            )

        self._terminals[
            terminal.terminal_id
        ] = terminal

    def unregister(
        self,
        terminal_id: str,
    ) -> EquipmentTerminal:
        terminal = self._terminals.pop(
            terminal_id,
            None,
        )

        if terminal is None:
            raise KeyError(terminal_id)

        return terminal

    def get(
        self,
        terminal_id: str,
    ) -> Optional[EquipmentTerminal]:
        return self._terminals.get(
            terminal_id
        )

    def require(
        self,
        terminal_id: str,
    ) -> EquipmentTerminal:
        terminal = self.get(terminal_id)

        if terminal is None:
            raise KeyError(
                f"Unknown terminal: {terminal_id}"
            )

        return terminal

    def contains(
        self,
        terminal_id: str,
    ) -> bool:
        return terminal_id in self._terminals

    def terminals(
        self,
    ) -> Iterable[EquipmentTerminal]:
        return tuple(
            self._terminals.values()
        )

    def terminals_for_equipment(
        self,
        equipment_id: str,
    ) -> tuple[EquipmentTerminal, ...]:
        return tuple(
            terminal
            for terminal in self._terminals.values()
            if terminal.equipment_id
            == equipment_id
        )

    def clear(self) -> None:
        self._terminals.clear()

    def __len__(self) -> int:
        return len(self._terminals)
