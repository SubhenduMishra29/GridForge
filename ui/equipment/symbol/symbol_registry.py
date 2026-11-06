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
#     Provides central lookup of renderer-neutral symbol
#     definitions.
#
# Does NOT:
#     - render symbols;
#     - instantiate QGraphicsItem;
#     - manage canvas state;
# ============================================================

"""
GridForge V2 — Symbol Registry.
"""

from __future__ import annotations

from .symbol_definition import SymbolDefinition


class SymbolRegistry:
    """
    Registry of renderer-neutral SLD symbol definitions.

    The registry owns definitions by their stable ``symbol_id``.
    It does not create runtime SymbolBase instances.
    """

    def __init__(self) -> None:
        self._definitions: dict[
            str,
            SymbolDefinition,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        definition: SymbolDefinition,
    ) -> None:
        """Register a symbol definition."""

        if not isinstance(
            definition,
            SymbolDefinition,
        ):
            raise TypeError(
                "definition must be a SymbolDefinition."
            )

        definition_id = definition.symbol_id

        if definition_id in self._definitions:
            raise ValueError(
                f"Symbol already registered: "
                f"{definition_id}"
            )

        self._definitions[
            definition_id
        ] = definition

    # ========================================================
    # REMOVAL
    # ========================================================

    def unregister(
        self,
        definition_id: str,
    ) -> SymbolDefinition:
        """Remove and return a registered definition."""

        self._validate_id(definition_id)

        definition = self._definitions.pop(
            definition_id,
            None,
        )

        if definition is None:
            raise KeyError(
                f"Unknown symbol definition: "
                f"{definition_id}"
            )

        return definition

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        definition_id: str,
    ) -> SymbolDefinition | None:
        """Return a definition if registered."""

        self._validate_id(definition_id)

        return self._definitions.get(
            definition_id
        )

    # --------------------------------------------------------

    def require(
        self,
        definition_id: str,
    ) -> SymbolDefinition:
        """Return a definition or raise KeyError."""

        self._validate_id(definition_id)

        definition = self._definitions.get(
            definition_id
        )

        if definition is None:
            raise KeyError(
                f"Unknown symbol definition: "
                f"{definition_id}"
            )

        return definition

    # ========================================================
    # MEMBERSHIP
    # ========================================================

    def contains(
        self,
        definition_id: str,
    ) -> bool:
        """Return whether a definition is registered."""

        self._validate_id(definition_id)

        return definition_id in self._definitions

    # ========================================================
    # ENUMERATION
    # ========================================================

    def definitions(
        self,
    ) -> tuple[SymbolDefinition, ...]:
        """
        Return a stable snapshot of registered definitions.
        """

        return tuple(
            self._definitions.values()
        )

    def symbol_ids(
        self,
    ) -> tuple[str, ...]:
        """Return a stable snapshot of registered IDs."""

        return tuple(
            self._definitions.keys()
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """Remove all registered definitions."""

        self._definitions.clear()

    # ========================================================
    # COLLECTION PROTOCOL
    # ========================================================

    def __len__(self) -> int:
        """Return the number of registered definitions."""

        return len(self._definitions)

    def __contains__(
        self,
        definition_id: str,
    ) -> bool:
        """Support ``definition_id in registry``."""

        return self.contains(definition_id)

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @staticmethod
    def _validate_id(
        definition_id: str,
    ) -> None:
        """Validate a symbol-definition identifier."""

        if (
            not isinstance(definition_id, str)
            or not definition_id.strip()
        ):
            raise ValueError(
                "definition_id must be a "
                "non-empty string."
            )


__all__ = [
    "SymbolRegistry",
]
