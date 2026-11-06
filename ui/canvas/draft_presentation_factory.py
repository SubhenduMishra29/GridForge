# ============================================================
# GridForge V2 — Draft SLD Presentation Factory
# ============================================================
"""Create presentation-only graphics for immutable Draft SLD nodes."""

from __future__ import annotations

from typing import Any

from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.canvas.symbol_preview_item import SymbolPreviewItem
from ui.canvas.draft_sld_projection import DraftSLDCanvasNode


class DraftPresentationFactory:
    """Realize DraftSLDCanvasNode without constructing Core/read-model equipment."""

    def __init__(
        self,
        equipment_registry: EquipmentRegistry,
        symbol_registry: SymbolRegistry,
    ) -> None:
        if not isinstance(equipment_registry, EquipmentRegistry):
            raise TypeError("equipment_registry must be an EquipmentRegistry.")
        if not isinstance(symbol_registry, SymbolRegistry):
            raise TypeError("symbol_registry must be a SymbolRegistry.")
        self._equipment_registry = equipment_registry
        self._symbol_registry = symbol_registry

    def create_node(self, node: DraftSLDCanvasNode) -> SymbolPreviewItem:
        if not isinstance(node, DraftSLDCanvasNode):
            raise TypeError("node must be a DraftSLDCanvasNode.")
        definition = self._equipment_registry.require(node.equipment_type)
        symbol = self._symbol_registry.require(definition.symbol_id)
        return SymbolPreviewItem(
            symbol,
            position=(node.x, node.y),
            rotation=node.rotation,
            presentation_state=node.presentation,
            draft_id=node.draft_id,
            terminal_names=node.terminal_roles,
            element_type=node.equipment_type,
        )


__all__ = ["DraftPresentationFactory"]
