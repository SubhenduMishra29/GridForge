# ============================================================
# File: ui/equipment/symbol/symbol_factory.py
# GridForge V2 — Symbol Factory
# ============================================================
"""
Factory for logical SLD symbol instances.

This module creates runtime SymbolBase objects from registered
SymbolDefinition objects.

It does not create Qt graphics items, render symbols, or manage
the canvas.
"""

from __future__ import annotations

from typing import Any

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
                "registry must not be None."
            )

        if not isinstance(
            registry,
            SymbolRegistry,
        ):
            raise TypeError(
                "registry must be a SymbolRegistry."
            )

        self._registry = registry

    @property
    def registry(self) -> SymbolRegistry:
        """Return the symbol-definition registry."""
        return self._registry

    def create(
        self,
        definition_id: str,
        symbol_id: str,
        *,
        scale: float = 1.0,
        rotation: float = 0.0,
        visible: bool = True,
        properties: dict[str, Any] | None = None,
    ) -> SymbolBase:
        """
        Create a logical symbol instance.

        The referenced definition must already be registered.
        """

        if (
            not isinstance(symbol_id, str)
            or not symbol_id.strip()
        ):
            raise ValueError(
                "symbol_id must be a non-empty string."
            )

        if (
            not isinstance(definition_id, str)
            or not definition_id.strip()
        ):
            raise ValueError(
                "definition_id must be a non-empty string."
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


__all__ = [
    "SymbolFactory",
]
