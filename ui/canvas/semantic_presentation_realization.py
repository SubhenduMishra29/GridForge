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
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.sld.sld_equipment_identity import equipment_type_for_semantic
from ui.sld.sld_vocabulary import semantic_type

from .sld_canvas_projection import SLDCanvasNode


@dataclass(frozen=True, slots=True)
class PresentationSelection:
    """Immutable resolved presentation identity."""

    semantic_type: str
    equipment_type: str
    symbol_id: str
    representation_id: str = "symbol"
    symbol_instance: SymbolBase | None = None

    def __post_init__(self) -> None:
        for name in ("semantic_type", "equipment_type", "symbol_id", "representation_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


class SemanticPresentationRealization:
    """Orchestrate canonical semantic, equipment, and symbol authorities."""

    def __init__(self, equipment_registry: EquipmentRegistry, symbol_registry: SymbolRegistry) -> None:
        if not isinstance(equipment_registry, EquipmentRegistry):
            raise TypeError("equipment_registry must be an EquipmentRegistry")
        if not isinstance(symbol_registry, SymbolRegistry):
            raise TypeError("symbol_registry must be a SymbolRegistry")
        self._equipment_registry = equipment_registry
        self._symbol_registry = symbol_registry

    @property
    def equipment_registry(self) -> EquipmentRegistry:
        return self._equipment_registry

    @property
    def symbol_registry(self) -> SymbolRegistry:
        return self._symbol_registry

    def realize(self, node: SLDCanvasNode) -> PresentationSelection:
        if not isinstance(node, SLDCanvasNode):
            raise TypeError("node must be an SLDCanvasNode")
        element_type = node.properties.get("element_type")
        canonical_semantic = semantic_type(element_type)
        equipment_type = equipment_type_for_semantic(canonical_semantic)
        definition = self._equipment_registry.require(equipment_type)

        if node.presentation is None:
            symbol_instance = SymbolBase(
                symbol_id=definition.symbol_id,
                definition_id=definition.symbol_id,
            )
        else:
            symbol_instance = node.presentation

        if symbol_instance.definition_id != symbol_instance.symbol_id:
            raise ValueError(
                f"SLD symbol presentation definition identity mismatch: "
                f"{symbol_instance.definition_id!r} != {symbol_instance.symbol_id!r}"
            )
        if symbol_instance.representation_id != "symbol":
            raise ValueError(
                f"Unsupported SLD symbol representation: "
                f"{symbol_instance.representation_id!r}"
            )

        self._symbol_registry.require(symbol_instance.symbol_id)
        return PresentationSelection(
            semantic_type=canonical_semantic,
            equipment_type=equipment_type,
            symbol_id=symbol_instance.symbol_id,
            representation_id=symbol_instance.representation_id,
            symbol_instance=SymbolBase.from_dict(symbol_instance.to_dict()),
        )


__all__ = ["PresentationSelection", "SemanticPresentationRealization"]
