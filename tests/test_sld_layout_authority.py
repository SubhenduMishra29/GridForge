"""
GridForge V2
===========

File:
    tests/test_sld_layout_authority.py

Purpose:
    Define the canonical presentation-geometry contract during the
    unified SLD rendering migration.

Author:
    Subhendu Mishra
"""

from core.application.read_models import ElementReadModel, NetworkReadModel
from ui.canvas.sld_canvas_projection import SLDCanvasProjection
from ui.sld.sld_controller import SLDController
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_layout import SLDLayout
from ui.sld.sld_model import SLDNode
from ui.sld.sld_projection_manager import SLDProjectionManager
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer


def _registered_document() -> tuple[SLDController, SLDDocument]:
    controller = SLDController()
    document = SLDDocument("sld-1")
    controller.register_document(document)
    return controller, document


def test_graphical_position_update_persists_in_sld_document() -> None:
    controller, document = _registered_document()
    controller.add_node(SLDNode("bus-1", equipment_id="bus-1"))

    controller.set_node_position("bus-1", 120.0, 240.0)

    assert document.model.get_node("bus-1").position == (120.0, 240.0)

    restored = SLDDocument.from_dict(document.to_dict())
    assert restored.model.get_node("bus-1").position == (120.0, 240.0)


def test_layout_is_derived_geometry_and_does_not_mutate_sld_document() -> None:
    _, document = _registered_document()
    document.model.add_node(
        SLDNode("bus-1", equipment_id="bus-1", x=10.0, y=20.0)
    )
    layout = SLDLayout()

    placement = layout.apply({"bus-1": (120.0, 240.0)})[0]

    assert placement.object_id == "bus-1"
    assert placement.x == 120.0
    assert placement.y == 240.0
    assert document.model.get_node("bus-1").position == (10.0, 20.0)


def test_canvas_projection_reads_canonical_sld_node_geometry() -> None:
    _, document = _registered_document()
    document.model.add_node(
        SLDNode("bus-1", equipment_id="bus-1", x=120.0, y=240.0)
    )

    snapshot = SLDCanvasProjection().project(document.model)

    assert snapshot.nodes[0].x == 120.0
    assert snapshot.nodes[0].y == 240.0


def test_read_synchronizer_preserves_existing_graphical_position() -> None:
    _, document = _registered_document()
    document.model.add_node(
        SLDNode("bus-1", equipment_id="bus-1", x=120.0, y=240.0)
    )
    synchronizer = SLDReadSynchronizer(SLDProjectionManager())
    read_model = NetworkReadModel(
        elements=(
            ElementReadModel(
                object_id="bus-1",
                element_type="buses",
                labels={"name": "Bus 1"},
                connectivity_refs=(),
                attributes={},
            ),
        )
    )

    synchronizer.synchronize_network(document, read_model)

    assert document.model.get_node("bus-1").position == (120.0, 240.0)
