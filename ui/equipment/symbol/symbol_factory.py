# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/symbol/symbol_factory.py
#
# Purpose:
#     Creates logical symbol instances from registered symbol
#     definitions.
#
# Architectural Role:
#     Separates symbol construction from equipment, tools,
#     canvas and rendering code.
#
# Responsibilities:
#     - resolve symbol definitions;
#     - create stable symbol instances;
#     - apply instance transformations;
#     - apply instance properties.
#
# Does NOT:
#     - create QGraphicsItem;
#     - paint symbols;
#     - perform scene management.
#
# ============================================================

"""
GridForge V2 — Symbol Factory.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .symbol_base import SymbolBase
from .symbol_registry import SymbolRegistry


class SymbolFactory:
    """
    Factory for logical SLD symbol instances.
    """

    def __init__(
        self,
        registry: SymbolRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "registry must not be None"
            )

        self._registry = registry

    @property
    def registry(self) -> SymbolRegistry:
        return self._registry

    def create(
        self,
        definition_id: str,
        symbol_id: str,
        *,
        scale: float = 1.0,
        rotation: float = 0.0,
        visible: bool = True,
        properties: Optional[
            Dict[str, Any]
        ] = None,
    ) -> SymbolBase:
        """
        Create a symbol instance.

        Definition lookup is performed before construction so an invalid
        symbol cannot silently enter the SLD model.
        """
        if not symbol_id:
            raise ValueError(
                "symbol_id must not be empty"
            )

        self._registry.require(
            definition_id
        )

        return SymbolBase(
            symbol_id=symbol_id,
            definition_id=definition_id,
            scale=scale,
            rotation=rotation,
            visible=visible,
            properties=properties,
        )
