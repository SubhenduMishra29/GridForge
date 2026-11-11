from __future__ import annotations

import pytest

from core.application.bootstrap import create_application
from core.network.network import Network
from core.model.bus import Bus
from core.application.services.sld_service import SLDService
from core.application.commands.sld_commands import AddSLDNodeCommand, AddSLDConnectionCommand, RemoveSLDNodeCommand, RemoveSLDConnectionCommand, SetSLDNodePositionCommand, SetSLDNodeTransformsCommand, CreateSLDLayerCommand, UpdateSLDLayerCommand, DeleteSLDLayerCommand, ReorderSLDLayersCommand
from core.application.commands.selection_commands import DeleteSelectionBatchCommand
from core.application.commands.model_commands import CreateBusCommand
from core.application.events import SLDPresentationChanged
from core.application.errors import ExecutionError
from core.application.services.sld_service import SLDService
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_model import SLDAnnotationBlock
from ui.equipment.symbol.symbol_base import SymbolBase


def _application():
    network = Network()
    network.add_bus(Bus("bus-1", nominal_voltage_kv=132.0))
    application = create_application(network)
    application.attach_sld_service(SLDService(SLDDocument("initial:sld", project_id="initial"), symbol_presentation_factory=lambda _element_type: SymbolBase("bus", "bus").to_dict()))
    application.configure_project_presentation_contract(
        factory=lambda context: SLDDocument(f"{context.project_id}:sld", project_id=context.project_id),
        serializer=lambda value: value.to_dict(),
        deserializer=lambda data: SLDDocument.from_dict(data),
    )
    application.new_project("Project A", project_id="project-a")
    application.execute(CreateBusCommand(bus_id="bus-1", name="Bus 1", nominal_voltage_kv=132.0, voltage_pu=1.0, angle_deg=0.0, frequency_hz=50.0, in_service=True))
    application.clear_history()
    return application, application.presentation

def test_sld_command_uses_application_history_and_undo_redo() -> None:
    application, document = _application()

    result = application.execute(AddSLDNodeCommand(node_id="bus-1", equipment_id="bus-1", element_type="BUS", x=10, y=20))

    assert result.success
    assert document.model.get_node("bus-1").position == (10.0, 20.0)
    assert application.undo_count() == 1

    application.undo()
    assert not document.model.has_node("bus-1")
    assert application.redo_count() == 1

    application.redo()
    assert document.model.get_node("bus-1").position == (10.0, 20.0)
    assert application.undo_count() == 1


def test_failed_sld_command_does_not_create_history_or_change_state() -> None:
    application, document = _application()

    with pytest.raises(ExecutionError):
        application.execute(SetSLDNodePositionCommand(node_id="missing", x=1, y=2))

    assert document.model.node_count == 0
    assert application.undo_count() == 0
    assert application.redo_count() == 0


def test_successful_sld_mutation_publishes_semantic_presentation_event() -> None:
    application, _ = _application()
    events: list[SLDPresentationChanged] = []
    application.event_bus.subscribe(SLDPresentationChanged, events.append)

    application.execute(AddSLDNodeCommand(node_id="bus-1", equipment_id="bus-1", element_type="BUS", x=10, y=20))

    assert len(events) == 1
    assert events[0].event_type == "sld.presentation.changed"
    assert events[0].payload["operation"] == "execute"
    assert events[0].payload["presentation_operation"] == "add_node"


def test_undo_and_redo_publish_presentation_events() -> None:
    application, _ = _application()
    events: list[SLDPresentationChanged] = []
    application.event_bus.subscribe(SLDPresentationChanged, events.append)

    application.execute(AddSLDNodeCommand(node_id="bus-1", x=10, y=20))
    application.undo()
    application.redo()

    assert [event.payload["operation"] for event in events] == ["execute", "undo", "redo"]



def _group_transform_fixture():
    application, document = _application()
    first = document.model.create_node(
        "bus-1", equipment_id="bus-1", x=10, y=20,
        presentation=SymbolBase(
            "symbol-1", "bus", rotation=0.0, scale=1.0,
            properties={"mirror_x": False, "mirror_y": False},
        ),
        properties={"position_owner": "core", "symbol_owner": "catalogue"},
    )
    second = document.model.create_node(
        "bus-2", equipment_id="bus-1", x=110, y=120,
        presentation=SymbolBase(
            "symbol-2", "bus", rotation=90.0, scale=1.5,
            properties={"mirror_x": True, "mirror_y": False},
        ),
        properties={"position_owner": "core", "symbol_owner": "catalogue"},
    )
    before = {
        node.node_id: {
            "position": tuple(node.position),
            "presentation": node.presentation.to_dict(),
            "properties": dict(node.properties),
        }
        for node in (first, second)
    }
    transforms = [
        {
            "node_id": "bus-1", "x": 35.0, "y": 45.0,
            "presentation": SymbolBase(
                "symbol-1", "bus", rotation=90.0, scale=1.0,
                properties={"mirror_x": False, "mirror_y": False},
            ).to_dict(),
        },
        {
            "node_id": "bus-2", "x": 135.0, "y": 145.0,
            "presentation": SymbolBase(
                "symbol-2", "bus", rotation=180.0, scale=1.5,
                properties={"mirror_x": True, "mirror_y": True},
            ).to_dict(),
        },
    ]
    return application, document, before, transforms


def _group_state(document, node_ids=("bus-1", "bus-2")):
    return {
        node_id: {
            "position": tuple(document.model.get_node(node_id).position),
            "presentation": document.model.get_node(node_id).presentation.to_dict(),
            "properties": dict(document.model.get_node(node_id).properties),
        }
        for node_id in node_ids
    }


def test_group_transform_undo_redo_restores_exact_complete_member_state() -> None:
    application, document, before, transforms = _group_transform_fixture()

    result = application.execute(SetSLDNodeTransformsCommand(transforms=transforms))
    assert result.success
    after = _group_state(document)
    assert after != before
    assert application.undo_count() == 1

    application.undo()
    assert _group_state(document) == before
    assert application.redo_count() == 1

    application.redo()
    assert _group_state(document) == after
    assert application.undo_count() == 1


def test_group_transform_stale_member_rejects_undo_without_partial_restore() -> None:
    application, document, before, transforms = _group_transform_fixture()

    application.execute(SetSLDNodeTransformsCommand(transforms=transforms))
    after = _group_state(document)
    stale_member = document.model.get_node("bus-2")
    stale_member.set_presentation(
        SymbolBase(
            "symbol-2", "bus", rotation=225.0, scale=1.5,
            properties={"mirror_x": True, "mirror_y": True},
        ).to_dict()
    )
    externally_changed = _group_state(document)

    with pytest.raises(ExecutionError):
        application.undo()

    # The first member must not be restored if validation of the second member
    # fails: group inverse preflights the entire set before changing any member.
    assert _group_state(document) == externally_changed
    assert _group_state(document)["bus-1"] == after["bus-1"]
    assert before["bus-1"] != after["bus-1"]


def test_layer_commands_are_atomic_and_undo_redo_membership_with_content():
    application, document = _application()
    document.model.create_node("layer-node-a", "bus-1", 10, 20)
    document.model.create_node("layer-node-b", "bus-1", 30, 40)
    document.model.create_connection("layer-wire", "layer-node-a", "layer-node-b")
    document.add_annotation_block(SLDAnnotationBlock(
        block_id="layer-note", node_id="layer-node-a", fields=("identity",),
    ))
    original_ids = (
        tuple(node.node_id for node in document.model.nodes),
        tuple(connection.connection_id for connection in document.model.connections),
    )

    application.execute(CreateSLDLayerCommand(
        layer_id="details", name="Details", visible=True, opacity=0.8,
    ))
    for node in document.model.nodes:
        node.layer_id = "details"
    for connection in document.model.connections:
        connection.layer_id = "details"
    document.replace_annotation_blocks([
        {**block.to_dict(), "layer_id": "details"}
        for block in document.annotation_blocks
    ])
    application.execute(UpdateSLDLayerCommand(
        layer_id="details", name="Engineering details", visible=False, opacity=0.45,
    ))
    application.execute(ReorderSLDLayersCommand(layer_ids=("details", "default")))
    assert [layer.layer_id for layer in document.layers] == ["details", "default"]
    assert document.layers[0].visible is False
    assert document.layers[0].opacity == 0.45

    application.execute(DeleteSLDLayerCommand(layer_id="details", reassign_to="default"))
    assert [layer.layer_id for layer in document.layers] == ["default"]
    assert all(node.layer_id == "default" for node in document.model.nodes)
    assert all(connection.layer_id == "default" for connection in document.model.connections)
    assert document.annotation_blocks[0].layer_id == "default"
    assert (
        tuple(node.node_id for node in document.model.nodes),
        tuple(connection.connection_id for connection in document.model.connections),
    ) == original_ids

    application.undo()
    assert [layer.layer_id for layer in document.layers] == ["details", "default"]
    assert document.model.get_node("layer-node-a").layer_id == "details"
    assert document.model.get_connection("layer-wire").layer_id == "details"
    assert document.annotation_blocks[0].layer_id == "details"

    application.redo()
    assert [layer.layer_id for layer in document.layers] == ["default"]
    assert all(node.layer_id == "default" for node in document.model.nodes)
    assert document.annotation_blocks[0].layer_id == "default"


def test_layer_commands_reject_default_deletion_and_locked_layer_deletion():
    application, document = _application()
    with pytest.raises(ValueError, match="default"):
        DeleteSLDLayerCommand(layer_id="default")

    application.execute(CreateSLDLayerCommand(layer_id="locked", name="Locked"))
    application.execute(UpdateSLDLayerCommand(layer_id="locked", locked=True))
    before = document.layer_state_snapshot()
    history_before = application.undo_count()
    with pytest.raises(ExecutionError):
        application.execute(DeleteSLDLayerCommand(layer_id="locked"))
    assert document.layer_state_snapshot() == before
    assert application.undo_count() == history_before


def test_add_sld_objects_use_requested_layer_and_locked_layer_rejects_edits():
    application, document = _application()
    application.execute(CreateSLDLayerCommand(layer_id="detail", name="Detail"))
    application.execute(AddSLDNodeCommand(node_id="detail-a", layer_id="detail", x=1, y=2))
    application.execute(AddSLDNodeCommand(node_id="detail-b", layer_id="detail", x=3, y=4))
    application.execute(AddSLDConnectionCommand(
        connection_id="detail-wire",
        source_node_id="detail-a",
        target_node_id="detail-b",
        layer_id="detail",
    ))
    assert document.model.get_node("detail-a").layer_id == "detail"
    assert document.model.get_connection("detail-wire").layer_id == "detail"

    application.execute(UpdateSLDLayerCommand(layer_id="detail", locked=True))
    before = document.layer_state_snapshot()
    with pytest.raises(ExecutionError):
        application.execute(SetSLDNodePositionCommand(node_id="detail-a", x=100, y=200))
    with pytest.raises(ExecutionError):
        application.execute(AddSLDNodeCommand(node_id="blocked", layer_id="detail"))
    assert document.layer_state_snapshot() == before
    assert not document.model.has_node("blocked")


def test_atomic_selection_batch_deletes_mixed_sld_nodes_and_connections_with_one_history_entry():
    application, document = _application()
    application.execute(AddSLDNodeCommand(node_id="selection-a"))
    application.execute(AddSLDNodeCommand(node_id="selection-b"))
    application.execute(AddSLDConnectionCommand(
        connection_id="selection-link",
        source_node_id="selection-a",
        target_node_id="selection-b",
        presentation_owner="engineer",
    ))
    application.clear_history()
    events = []
    application.event_bus.subscribe(SLDPresentationChanged, events.append)

    result = application.execute(DeleteSelectionBatchCommand(
        document_id=document.document_id,
        commands=(
            RemoveSLDNodeCommand(node_id="selection-a"),
            RemoveSLDConnectionCommand(connection_id="selection-link"),
            RemoveSLDNodeCommand(node_id="selection-b"),
        ),
    ))

    assert result.success
    assert not document.model.has_node("selection-a")
    assert not document.model.has_node("selection-b")
    assert not document.model.has_connection("selection-link")
    assert application.undo_count() == 1
    assert len(events) == 1

    application.undo()
    assert document.model.has_node("selection-a")
    assert document.model.has_node("selection-b")
    assert document.model.has_connection("selection-link")
    application.redo()
    assert not document.model.has_node("selection-a")
    assert not document.model.has_node("selection-b")
    assert not document.model.has_connection("selection-link")


def test_atomic_selection_batch_rolls_back_earlier_connection_removal_on_late_child_failure():
    application, document = _application()
    application.execute(AddSLDNodeCommand(node_id="rollback-a"))
    application.execute(AddSLDNodeCommand(node_id="rollback-b"))
    application.execute(AddSLDNodeCommand(
        node_id="projection-owned",
        presentation_owner="projection",
        projection_source="application_read_model",
    ))
    application.execute(AddSLDConnectionCommand(
        connection_id="rollback-link",
        source_node_id="rollback-a",
        target_node_id="rollback-b",
        presentation_owner="engineer",
    ))
    application.clear_history()

    with pytest.raises(ExecutionError):
        application.execute(DeleteSelectionBatchCommand(
            document_id=document.document_id,
            commands=(
                RemoveSLDConnectionCommand(connection_id="rollback-link"),
                RemoveSLDNodeCommand(node_id="projection-owned"),
            ),
        ))

    assert document.model.has_connection("rollback-link")
    assert document.model.has_node("projection-owned")
    assert application.undo_count() == 0
    assert application.redo_count() == 0


def test_atomic_selection_batch_rejects_locked_sld_connection_layer_before_mutation():
    application, document = _application()
    application.execute(CreateSLDLayerCommand(layer_id="locked-selection", name="Locked"))
    application.execute(AddSLDNodeCommand(node_id="locked-a", layer_id="locked-selection"))
    application.execute(AddSLDNodeCommand(node_id="locked-b", layer_id="locked-selection"))
    application.execute(AddSLDConnectionCommand(
        connection_id="locked-link",
        source_node_id="locked-a",
        target_node_id="locked-b",
        layer_id="locked-selection",
        presentation_owner="engineer",
    ))
    application.execute(UpdateSLDLayerCommand(layer_id="locked-selection", locked=True))
    application.clear_history()

    with pytest.raises(ExecutionError):
        application.execute(DeleteSelectionBatchCommand(
            document_id=document.document_id,
            commands=(RemoveSLDConnectionCommand(connection_id="locked-link"),),
        ))

    assert document.model.has_connection("locked-link")
    assert application.undo_count() == 0
