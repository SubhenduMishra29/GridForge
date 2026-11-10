# ============================================================
# File: ui/canvas/semantic_presentation_realization.py
# GridForge V2 — Semantic Presentation Realization
# Author: Subhendu Mishra
# ============================================================
"""Resolve SLD semantics into immutable renderer-neutral presentation data."""

from __future__ import annotations

from dataclasses import dataclass

from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.symbol_base import SymbolBase
from ui.equipment.symbol.symbol_factory import SymbolFactory
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.equipment.terminal_contract import reconcile_terminal_contract
from ui.sld.sld_equipment_identity import equipment_type_for_semantic
from ui.sld.sld_vocabulary import SLD_SEMANTIC_TYPES, semantic_type

from .sld_canvas_projection import SLDCanvasNode


@dataclass(frozen=True, slots=True)
class PresentationSelection:
    """Immutable resolved presentation identity."""

    semantic_type: str
    equipment_type: str
    symbol_id: str
    representation_id: str = "symbol"
    symbol_instance: SymbolBase | None = None
    symbol_family_id: str = ""
    standard_id: str = "unspecified"
    variant_id: str = "default"
    standard_reference_id: str = ""

    def __post_init__(self) -> None:
        for name in ("semantic_type", "equipment_type", "symbol_id", "representation_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        family_id = self.symbol_family_id or self.symbol_id
        for name, value in (
            ("symbol_family_id", family_id),
            ("standard_id", self.standard_id),
            ("variant_id", self.variant_id),
            ("standard_reference_id", self.standard_reference_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
            object.__setattr__(self, name, value.strip().lower())
        if self.symbol_instance is not None:
            if (
                self.symbol_instance.symbol_id != self.symbol_id
                or self.symbol_instance.symbol_family_id != self.symbol_family_id
                or self.symbol_instance.standard_id != self.standard_id
                or self.symbol_instance.variant_id != self.variant_id
                or self.symbol_instance.standard_reference_id != self.standard_reference_id
            ):
                raise ValueError("PresentationSelection identity does not match its symbol instance.")


class SemanticPresentationRealization:
    """Orchestrate canonical semantic, equipment, and symbol authorities."""

    def __init__(self, equipment_registry: EquipmentRegistry, symbol_registry: SymbolRegistry) -> None:
        if not isinstance(equipment_registry, EquipmentRegistry):
            raise TypeError("equipment_registry must be an EquipmentRegistry")
        if not isinstance(symbol_registry, SymbolRegistry):
            raise TypeError("symbol_registry must be a SymbolRegistry")
        self._equipment_registry = equipment_registry
        self._symbol_registry = symbol_registry
        # Validate the complete advertised SLD vocabulary at composition time.
        # This keeps the vocabulary, EquipmentRegistry identity bridge, and
        # SymbolRegistry in lockstep instead of discovering missing coverage
        # only after a persisted node reaches the canvas renderer.
        for semantic in SLD_SEMANTIC_TYPES:
            equipment_type = equipment_type_for_semantic(semantic)
            definition = self._equipment_registry.require(equipment_type)
            self._symbol_registry.require(definition.symbol_id)
        # Use the canonical SymbolFactory with the already-composed registry.
        # The factory creates only renderer-neutral instances; SymbolRegistry
        # remains the sole symbol-definition authority.
        self._symbol_factory = SymbolFactory(symbol_registry)

    @property
    def equipment_registry(self) -> EquipmentRegistry:
        return self._equipment_registry

    @property
    def symbol_registry(self) -> SymbolRegistry:
        return self._symbol_registry

    @property
    def symbol_factory(self) -> SymbolFactory:
        """Return the canonical factory backed by the composed SymbolRegistry."""
        return self._symbol_factory

    def realize(self, node: SLDCanvasNode) -> PresentationSelection:
        if not isinstance(node, SLDCanvasNode):
            raise TypeError("node must be an SLDCanvasNode")
        # The Application read model is the authoritative source for the
        # equipment type whenever it is available. Persisted SLD properties
        # are a compatibility fallback for presentation-only/legacy nodes;
        # they must not override current projected domain identity.
        element_type = (
            node.read_model.element_type
            if node.read_model is not None
            else node.properties.get("element_type")
        )
        canonical_semantic = semantic_type(element_type)
        equipment_type = equipment_type_for_semantic(canonical_semantic)
        definition = self._equipment_registry.require(equipment_type)

        default_definition = self._symbol_registry.require(definition.symbol_id)
        if node.presentation is None:
            symbol_instance = self._symbol_factory.create(definition.symbol_id)
        else:
            persisted = node.presentation
            # Presentation identity may select another definition only within
            # the equipment's registered symbol family. Equipment identity
            # and terminal identity remain owned by their existing contracts.
            symbol_definition = self._symbol_registry.require(persisted.symbol_id)
            if persisted.definition_id != persisted.symbol_id:
                raise ValueError(
                    f"SLD symbol definition identity mismatch: "
                    f"{persisted.definition_id!r} != {persisted.symbol_id!r}"
                )
            if symbol_definition.symbol_family_id != default_definition.symbol_family_id:
                raise ValueError(
                    f"SLD symbol family mismatch for {equipment_type!r}: "
                    f"{symbol_definition.symbol_family_id!r} != "
                    f"{default_definition.symbol_family_id!r}"
                )
            if (
                persisted.symbol_family_id != symbol_definition.symbol_family_id
                or persisted.standard_id != symbol_definition.standard_id
                or persisted.variant_id != symbol_definition.variant_id
                or persisted.standard_reference_id != symbol_definition.standard_reference_id
            ):
                raise ValueError(
                    f"Persisted symbol variant metadata does not match "
                    f"registered definition {symbol_definition.symbol_id!r}"
                )

            terminal_report = reconcile_terminal_contract(
                definition,
                creation_definition=definition.creation_definition,
                symbol_definition=symbol_definition,
            )
            if terminal_report.errors:
                raise ValueError(
                    f"SLD symbol variant {symbol_definition.symbol_id!r} "
                    f"violates the terminal contract for {equipment_type!r}: "
                    + " ".join(terminal_report.errors)
                )
            symbol_instance = self._symbol_factory.create(
                symbol_definition.symbol_id,
                scale=persisted.scale,
                rotation=persisted.rotation,
                visible=persisted.visible,
                representation_id=persisted.representation_id,
                properties=persisted.properties,
            )

        if symbol_instance.representation_id != "symbol":
            raise ValueError(
                f"Unsupported SLD symbol representation: "
                f"{symbol_instance.representation_id!r}"
            )

        return PresentationSelection(
            semantic_type=canonical_semantic,
            equipment_type=equipment_type,
            symbol_id=symbol_instance.symbol_id,
            symbol_family_id=symbol_instance.symbol_family_id,
            standard_id=symbol_instance.standard_id,
            variant_id=symbol_instance.variant_id,
            standard_reference_id=symbol_instance.standard_reference_id,
            representation_id=symbol_instance.representation_id,
            symbol_instance=SymbolBase.from_dict(symbol_instance.to_dict()),
        )


__all__ = ["PresentationSelection", "SemanticPresentationRealization"]
