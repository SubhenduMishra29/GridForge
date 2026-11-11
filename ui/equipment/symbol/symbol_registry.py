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

        variant_key = (
            definition.symbol_family_id,
            definition.standard_id,
            definition.variant_id,
        )
        if any(
            (
                item.symbol_family_id,
                item.standard_id,
                item.variant_id,
            ) == variant_key
            for item in self._definitions.values()
        ):
            raise ValueError(
                "Symbol family/standard/variant already registered: "
                f"{variant_key!r}"
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

    def variants_for_family(
        self,
        symbol_family_id: str,
        *,
        standard_id: str | None = None,
    ) -> tuple[SymbolDefinition, ...]:
        """Return deterministic variants for one family and optional standard."""
        self._validate_id(symbol_family_id)
        if standard_id is not None:
            self._validate_id(standard_id)
            standard_id = standard_id.strip().lower()
        return tuple(
            sorted(
                (
                    item for item in self._definitions.values()
                    if item.symbol_family_id == symbol_family_id.strip().lower()
                    and (standard_id is None or item.standard_id == standard_id)
                ),
                key=lambda item: (item.standard_id, item.variant_id, item.symbol_id),
            )
        )

    def approved_variants_for_family(
        self,
        symbol_family_id: str,
        *,
        standard_id: str | None = None,
    ) -> tuple[SymbolDefinition, ...]:
        """Return only explicitly approved variants with reviewed geometry and anchors.

        Equipment-specific terminal-role reconciliation remains a separate
        mandatory gate in EquipmentRegistry before a candidate is selectable.
        """
        return tuple(
            item for item in self.variants_for_family(
                symbol_family_id, standard_id=standard_id
            )
            if item.review_status == "approved"
            and item.geometry_reviewed
            and item.terminal_anchors_reviewed
            and bool(item.standard_reference_id)
            and bool(item.geometry_review_reference_id)
            and bool(item.terminal_anchor_review_reference_id)
            and bool(item.source_document_title)
            and bool(item.source_document_revision)
            and item.source_use_status in {"licensed", "permission_granted", "public_domain"}
        )

    def get_variant(
        self,
        symbol_family_id: str,
        standard_id: str,
        variant_id: str,
    ) -> SymbolDefinition | None:
        """Resolve one exact family/standard/variant tuple, if registered."""
        for value, name in (
            (symbol_family_id, "symbol_family_id"),
            (standard_id, "standard_id"),
            (variant_id, "variant_id"),
        ):
            self._validate_id(value)
        family = symbol_family_id.strip().lower()
        standard = standard_id.strip().lower()
        variant = variant_id.strip().lower()
        return next(
            (
                item for item in self._definitions.values()
                if item.symbol_family_id == family
                and item.standard_id == standard
                and item.variant_id == variant
            ),
            None,
        )

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
