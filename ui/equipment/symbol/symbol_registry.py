# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/symbol/symbol_registry.py
#
# Purpose:
#     Registry of available SLD symbol definitions.
#
# Architectural Role:
#     Provides central lookup of renderer-neutral symbol definitions.
#
# Responsibilities:
#     - register symbols;
#     - unregister symbols;
#     - retrieve definitions;
#     - enumerate available symbols.
#
# Does NOT:
#     - render symbols;
#     - instantiate QGraphicsItem;
#     - manage canvas state.
#
# ============================================================

"""
GridForge V2 — Symbol Registry.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .symbol_definition import SymbolDefinition


class SymbolRegistry:
    """
    Registry of renderer-neutral SLD symbol definitions.
    """

    def __init__(self) -> None:
        self._definitions: Dict[
            str,
            SymbolDefinition,
        ] = {}

    def register(
        self,
        definition: SymbolDefinition,
    ) -> None:
        definition_id = definition.definition_id

        if definition_id in self._definitions:
            raise ValueError(
                f"Symbol already registered: "
                f"{definition_id}"
            )

        self._definitions[
            definition_id
        ] = definition

    def unregister(
        self,
        definition_id: str,
    ) -> SymbolDefinition:
        definition = self._definitions.pop(
            definition_id,
            None,
        )

        if definition is None:
            raise KeyError(definition_id)

        return definition

    def get(
        self,
        definition_id: str,
    ) -> Optional[SymbolDefinition]:
        return self._definitions.get(
            definition_id
        )

    def require(
        self,
        definition_id: str,
    ) -> SymbolDefinition:
        definition = self.get(
            definition_id
        )

        if definition is None:
            raise KeyError(
                f"Unknown symbol definition: "
                f"{definition_id}"
            )

        return definition

    def contains(
        self,
        definition_id: str,
    ) -> bool:
        return definition_id in self._definitions

    def definitions(
        self,
    ) -> Iterable[SymbolDefinition]:
        return tuple(
            self._definitions.values()
        )

    def clear(self) -> None:
        self._definitions.clear()

    def __len__(self) -> int:
        return len(self._definitions)

    def __contains__(
        self,
        definition_id: str,
    ) -> bool:
        return self.contains(definition_id)
