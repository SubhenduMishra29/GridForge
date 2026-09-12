"""R3 canonical project persistence tests."""

from core.model.bus import Bus
from core.model.line import Line
from core.network import Network
from core.persistence.project_persistence import LoadedProject, ProjectPersistenceService
from core.application.project import ProjectContext
from ui.sld.sld_document import SLDDocument


def _network() -> Network:
    network = Network()
    bus_1 = Bus("BUS-001", name="Bus 1", nominal_voltage_kv=132.0)
    bus_2 = Bus("BUS-002", name="Bus 2", nominal_voltage_kv=33.0)
    network.add_bus(bus_1)
    network.add_bus(bus_2)
    network.add_line(Line(
        id="LINE-001",
        endpoint_from=bus_1,
        endpoint_to=bus_2,
        resistance_ohm=0.12,
        reactance_ohm=0.45,
    ))
    network.rebuild_topology()
    return network


def _sld() -> SLDDocument:
    document = SLDDocument(
        document_id="SLD-001",
        name="Main SLD",
        project_id="PROJECT-001",
    )
    document.model.create_node("SLD-NODE-001", "BUS-001", 100.0, 200.0)
    document.model.create_node("SLD-NODE-002", "BUS-002", 640.0, 320.0)
    document.model.create_connection("SLD-CONN-001", "SLD-NODE-001", "SLD-NODE-002")
    return document


def test_project_package_persists_sld_document_geometry_and_connections(tmp_path):
    service = ProjectPersistenceService()
    context = ProjectContext("PROJECT-001", "Persistence Test", None)
    network = _network()
    document = _sld()
    path = tmp_path / "roundtrip.gridforge"

    service.save(context, network, document.to_dict(), path)
    loaded = service.load(path)

    assert isinstance(loaded, LoadedProject)
    assert loaded.presentation is not None
    restored = SLDDocument.from_dict(loaded.presentation)

    assert restored.document_id == document.document_id
    assert restored.project_id == document.project_id
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
    assert line.endpoint_from is bus_1
    assert line.endpoint_to is bus_2
    assert line.endpoint_from.owner is line
    assert line.endpoint_to.owner is line
    assert loaded.network.topology_valid is True


def test_project_package_without_sld_remains_loadable(tmp_path):
    service = ProjectPersistenceService()
    context = ProjectContext("PROJECT-001", "Core Only", None)
    path = tmp_path / "core-only.gridforge"

    service.save(context, _network(), None, path)
    loaded = service.load(path)

    assert loaded.presentation is None
    assert loaded.network.get_by_id("bus", "BUS-001").id == "BUS-001"
