# ============================================================
# GridForge V2 — SLD Equipment Presentation Regression Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from ui.canvas.semantic_presentation_realization import SemanticPresentationRealization
from ui.canvas.sld_canvas_projection import SLDCanvasNode
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory


def _node(node_id: str, element_type: str) -> SLDCanvasNode:
    return SLDCanvasNode(
        node_id=node_id,
        equipment_id=node_id,
        x=10.0,
        y=20.0,
        properties={"element_type": element_type},
    )


def test_non_bus_semantic_equipment_has_a_presentation_representation():
    selection = SemanticPresentationRealization().realize(_node("tx-1", "transformer"))
    assert selection.representation_id == "equipment"


def test_equipment_factory_creates_presentation_only_item():
    node = _node("breaker-1", "breaker")
    selection = SemanticPresentationRealization().realize(node)

    item = SLDGraphicsItemFactory().create_node(node, selection)

    assert item.object_id == "breaker-1"
    assert item.element_type == "breaker"
