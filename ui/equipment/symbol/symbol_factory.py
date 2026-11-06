# ============================================================
# File: ui/equipment/symbol/symbol_factory.py
# GridForge V2 — Symbol Factory
# ============================================================
"""Create renderer-neutral symbol instances from one registry identity."""

from __future__ import annotations

from typing import Any

from .symbol_base import SymbolBase
from .symbol_registry import SymbolRegistry


class SymbolFactory:
    """Factory using SymbolDefinition.symbol_id as the sole definition identity."""

    def __init__(self, registry: SymbolRegistry) -> None:
        if not isinstance(registry, SymbolRegistry):
            raise TypeError("registry must be a SymbolRegistry")
        self._registry = registry

    @property
    def registry(self) -> SymbolRegistry:
        return self._registry

    def create(self, symbol_id: str, *, scale: float = 1.0, rotation: float = 0.0,
               visible: bool = True, representation_id: str = "symbol",
               properties: dict[str, Any] | None = None) -> SymbolBase:
        """Create a logical symbol instance for a registered symbol ID."""
        definition = self._registry.require(symbol_id)
        return SymbolBase(symbol_id=definition.symbol_id,
                          definition_id=definition.symbol_id,
                          scale=scale, rotation=rotation,
                          visible=visible, representation_id=representation_id,
                          properties=properties)


__all__ = ["SymbolFactory"]
