# ============================================================
# GridForge V2 — SLD Equipment Presentation Regression Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from ui.canvas.semantic_presentation_realization import SemanticPresentationRealization
from ui.canvas.sld_canvas_projection import SLDCanvasNode
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory


def test_non_bus_semantic_equipment_has_a_presentation_representation():
    node = SLDCanvasNode(
        node_id="tx-1",
        x=10.0,
        y=20.0,
        properties={"element_type": "transformer"},
    )

    selection = SemanticPresentationRealization().realize(node)

    assert selection.representation_id == "equipment"


def test_equipment_factory_creates_presentation_only_item():
    node = SLDCanvasNode(
        node_id="breaker-1",
        x=10.0,
        y=20.0,
        properties={"element_type": "breaker"},
    )
    selection = SemanticPresentationRealization().realize(node)

    item = SLDGraphicsItemFactory().create_node(node, selection)

    assert item.object_id == "breaker-1"
    assert item.element_type == "breaker"
