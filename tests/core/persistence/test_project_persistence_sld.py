"""R3 canonical project persistence tests."""

import pytest

from core.application.project import ProjectContext
from core.model.bus import Bus
from core.model.line import Line
from core.network import Network
from core.persistence.project_persistence import LoadedProject, ProjectPersistenceError, ProjectPersistenceService
from core.persistence.migration import ProjectPersistenceMigration, SLDMigrationError, validate_canonical_sld
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_model import SLDEndpoint, SLDEndpointKind, SLDRoute, SLDAnnotationBlock, SLDPresentationLayer
from ui.equipment.symbol.symbol_base import SymbolBase


def _network() -> Network:
    network = Network()
    bus_1 = Bus("BUS-001", name="Bus 1", nominal_voltage_kv=132.0)
    bus_2 = Bus("BUS-002", name="Bus 2", nominal_voltage_kv=33.0)
    network.add_bus(bus_1)
    network.add_bus(bus_2)
    network.add_line(Line(id="LINE-001", endpoint_from=bus_1, endpoint_to=bus_2,
                          resistance_ohm=0.12, reactance_ohm=0.45))
    network.rebuild_topology()
    return network


def _sld() -> SLDDocument:
    document = SLDDocument(document_id="SLD-001", name="Main SLD", project_id="PROJECT-001")
    document.model.create_node("SLD-NODE-001", "BUS-001", 100.0, 200.0)
    document.model.create_node("SLD-NODE-002", "BUS-002", 640.0, 320.0)
    document.model.create_connection("SLD-CONN-001", "SLD-NODE-001", "SLD-NODE-002")
    return document


def test_project_package_persists_sld_document_geometry_and_connections(tmp_path):
    service = ProjectPersistenceService()
    context = ProjectContext("PROJECT-001", "Persistence Test", None)
    path = tmp_path / "roundtrip.gridforge"
    service.save(context, _network(), _sld().to_dict(), path)
    loaded = service.load(path)

    assert isinstance(loaded, LoadedProject)
    assert loaded.presentation is not None
    restored = SLDDocument.from_dict(loaded.presentation)
    assert restored.document_id == "SLD-001"
    assert restored.project_id == "PROJECT-001"
    assert restored.model.get_node("SLD-NODE-001").equipment_id == "BUS-001"
    assert restored.model.get_node("SLD-NODE-001").position == (100.0, 200.0)
    assert restored.model.get_node("SLD-NODE-002").position == (640.0, 320.0)
    connection = restored.model.get_connection("SLD-CONN-001")
    assert connection.source_node_id == "SLD-NODE-001"
    assert connection.target_node_id == "SLD-NODE-002"


def test_project_round_trip_preserves_core_identity_terminals_and_rebuilt_topology(tmp_path):
    service = ProjectPersistenceService()
    context = ProjectContext("PROJECT-001", "Persistence Test", None)
    path = tmp_path / "roundtrip.gridforge"
    service.save(context, _network(), _sld().to_dict(), path)
    loaded = service.load(path)

    bus_1 = loaded.network.get_by_id("bus", "BUS-001")
    bus_2 = loaded.network.get_by_id("bus", "BUS-002")
    line = loaded.network.get_by_id("line", "LINE-001")
    assert bus_1.id == "BUS-001"
    assert bus_2.id == "BUS-002"
    assert line.id == "LINE-001"
    assert line.from_endpoint is bus_1
    assert line.to_endpoint is bus_2
    assert line.from_terminal.endpoint is bus_1
    assert line.to_terminal.endpoint is bus_2
    assert line.from_terminal.owner is line
    assert line.to_terminal.owner is line
    assert loaded.network.topology_valid is True


def test_project_package_without_sld_remains_loadable(tmp_path):
    service = ProjectPersistenceService()
    context = ProjectContext("PROJECT-001", "Core Only", None)
    path = tmp_path / "core-only.gridforge"
    service.save(context, _network(), None, path)
    loaded = service.load(path)
    assert loaded.presentation is None
    assert loaded.network.get_by_id("bus", "BUS-001").id == "BUS-001"


def test_failed_presentation_serialization_leaves_existing_package_untouched(tmp_path):
    service = ProjectPersistenceService()
    context = ProjectContext("PROJECT-001", "Persistence Test", None)
    path = tmp_path / "roundtrip.gridforge"
    service.save(context, _network(), _sld().to_dict(), path)

    with pytest.raises(ProjectPersistenceError):
        service.save(context, _network(), {"not_json": object()}, path)

    restored = SLDDocument.from_dict(service.load(path).presentation)
    assert restored.model.get_node("SLD-NODE-001").position == (100.0, 200.0)



def test_project_round_trip_preserves_symbol_transforms_terminal_identity_and_engineer_route(tmp_path):
    service = ProjectPersistenceService()
    context = ProjectContext("PROJECT-001", "Presentation Transform Round Trip", None)
    path = tmp_path / "transformed.gridforge"
    document = SLDDocument(
        document_id="SLD-TRANSFORM-001",
        name="Transformed SLD",
        project_id="PROJECT-001",
    )
    source_symbol = SymbolBase(
        "symbol-bus-001",
        "busbar",
        scale=1.25,
        rotation=90.0,
        properties={"mirror_x": True, "mirror_y": False},
        symbol_family_id="busbar",
        standard_id="unspecified",
        variant_id="default",
    )
    target_symbol = SymbolBase(
        "symbol-bus-002",
        "busbar",
        scale=0.9,
        rotation=270.0,
        properties={"mirror_x": False, "mirror_y": True},
        symbol_family_id="busbar",
        standard_id="unspecified",
        variant_id="default",
    )
    document.model.create_node(
        "SLD-BREAKER-001", "BUS-001", 125.0, 240.0,
        presentation=source_symbol,
    )
    document.model.create_node(
        "SLD-TRANSFORMER-001", "BUS-002", 620.0, 410.0,
        presentation=target_symbol,
    )
    source_endpoint = SLDEndpoint(
        kind=SLDEndpointKind.EQUIPMENT,
        node_id="SLD-BREAKER-001",
        equipment_id="BUS-001",
        terminal_role="LINE",
    )
    target_endpoint = SLDEndpoint(
        kind=SLDEndpointKind.EQUIPMENT,
        node_id="SLD-TRANSFORMER-001",
        equipment_id="BUS-002",
        terminal_role="HV",
    )
    authored_bends = ((260.0, 240.0), (260.0, 360.0), (540.0, 360.0))
    document.model.create_connection(
        "SLD-CONN-TRANSFORMED-001",
        "SLD-BREAKER-001",
        "SLD-TRANSFORMER-001",
        source_endpoint=source_endpoint,
        target_endpoint=target_endpoint,
        route=SLDRoute(
            routing_mode="orthogonal",
            ownership="engineer",
            points=authored_bends,
        ),
    )

    service.save(context, _network(), document.to_dict(), path)
    first_load = SLDDocument.from_dict(service.load(path).presentation)
    first_source = first_load.model.get_node("SLD-BREAKER-001")
    first_target = first_load.model.get_node("SLD-TRANSFORMER-001")
    first_connection = first_load.model.get_connection("SLD-CONN-TRANSFORMED-001")

    assert first_source.position == (125.0, 240.0)
    assert first_target.position == (620.0, 410.0)
    assert first_source.presentation.to_dict() == source_symbol.to_dict()
    assert first_target.presentation.to_dict() == target_symbol.to_dict()
    assert first_connection.source_endpoint == source_endpoint
    assert first_connection.target_endpoint == target_endpoint
    assert first_connection.route.ownership == "engineer"
    assert first_connection.route.routing_mode == "orthogonal"
    assert first_connection.route.points == authored_bends

    # Exercise a second package cycle so the assertions cover persisted state,
    # not only a one-time in-memory reconstruction.
    service.save(context, _network(), first_load.to_dict(), path)
    second_load = SLDDocument.from_dict(service.load(path).presentation)
    second_connection = second_load.model.get_connection("SLD-CONN-TRANSFORMED-001")
    assert second_load.model.get_node("SLD-BREAKER-001").presentation.to_dict() == source_symbol.to_dict()
    assert second_load.model.get_node("SLD-TRANSFORMER-001").presentation.to_dict() == target_symbol.to_dict()
    assert second_connection.source_endpoint == source_endpoint
    assert second_connection.target_endpoint == target_endpoint
    assert second_connection.route.points == authored_bends


def test_sld_schema4_layer_membership_round_trips_with_document():
    document = SLDDocument(
        document_id="SLD-LAYERS-001",
        name="Layered SLD",
        project_id="PROJECT-001",
        layers=[
            SLDPresentationLayer("default", "Default", order=0),
            SLDPresentationLayer("protection", "Protection", visible=False, locked=True, opacity=0.6, order=1),
        ],
    )
    document.model.create_node("NODE-001", "BUS-001", 10.0, 20.0, layer_id="protection")
    document.model.create_node("NODE-002", "BUS-002", 30.0, 40.0)
    document.model.create_connection("CONN-001", "NODE-001", "NODE-002", layer_id="protection")
    document.add_annotation_block(SLDAnnotationBlock(
        block_id="ANN-001", node_id="NODE-001", fields=("identity",), layer_id="protection",
    ))

    restored = SLDDocument.from_dict(document.to_dict())
    assert [layer.to_dict() for layer in restored.layers] == [layer.to_dict() for layer in document.layers]
    assert restored.model.get_node("NODE-001").layer_id == "protection"
    assert restored.model.get_connection("CONN-001").layer_id == "protection"
    assert restored.annotation_blocks[0].layer_id == "protection"


def test_sld_schema3_migration_assigns_all_legacy_content_to_default_layer():
    document = _sld()
    document.add_annotation_block(SLDAnnotationBlock(
        block_id="ANN-LEGACY-001", node_id="SLD-NODE-001", fields=("identity",),
    ))
    legacy = document.to_dict()
    legacy["schema"] = 3
    legacy.pop("layers")
    for node in legacy["model"]["nodes"]:
        node.pop("layer_id")
    for connection in legacy["model"]["connections"]:
        connection.pop("layer_id")
    for block in legacy["annotation_blocks"]:
        block.pop("layer_id")

    migrated = ProjectPersistenceMigration()._migrate_sld(
        legacy,
        project_id="PROJECT-001",
        document_index=0,
        existing_document_ids=set(),
    )
    assert migrated["schema"] == 4
    assert migrated["layers"] == [{
        "layer_id": "default", "name": "Default", "visible": True,
        "locked": False, "opacity": 1.0, "order": 0,
    }]
    assert all(node["layer_id"] == "default" for node in migrated["model"]["nodes"])
    assert all(connection["layer_id"] == "default" for connection in migrated["model"]["connections"])
    assert all(block["layer_id"] == "default" for block in migrated["annotation_blocks"])


def test_sld_schema4_validator_rejects_unknown_layer_membership():
    payload = _sld().to_dict()
    payload["model"]["nodes"][0]["layer_id"] = "missing-layer"
    with pytest.raises(SLDMigrationError, match="unknown presentation layer"):
        validate_canonical_sld(payload)

    payload = _sld().to_dict()
    payload["layers"][0]["opacity"] = 1.5
    with pytest.raises(SLDMigrationError, match="opacity"):
        validate_canonical_sld(payload)


def test_project_package_round_trip_preserves_layer_registry_and_all_memberships(tmp_path):
    service = ProjectPersistenceService()
    context = ProjectContext("PROJECT-001", "Layered SLD Persistence", None)
    path = tmp_path / "layered-roundtrip.gridforge"
    document = _sld()
    document.add_layer(SLDPresentationLayer(
        "protection", "Protection", visible=False, locked=True,
        opacity=0.55, order=1,
    ))
    document.model.get_node("SLD-NODE-001").layer_id = "protection"
    document.model.get_connection("SLD-CONN-001").layer_id = "protection"
    document.add_annotation_block(SLDAnnotationBlock(
        block_id="ANN-LAYER-001",
        node_id="SLD-NODE-001",
        fields=("identity",),
        layer_id="protection",
    ))

    service.save(context, _network(), document.to_dict(), path)
    first = SLDDocument.from_dict(service.load(path).presentation)
    assert [layer.to_dict() for layer in first.layers] == [
        layer.to_dict() for layer in document.layers
    ]
    assert first.model.get_node("SLD-NODE-001").layer_id == "protection"
    assert first.model.get_connection("SLD-CONN-001").layer_id == "protection"
    assert first.annotation_blocks[0].layer_id == "protection"

    service.save(context, _network(), first.to_dict(), path)
    second = SLDDocument.from_dict(service.load(path).presentation)
    assert second.to_dict() == first.to_dict()
