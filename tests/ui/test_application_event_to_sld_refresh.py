from __future__ import annotations

from core.application.bootstrap import create_application
from core.application.commands.model_commands import CreateBusCommand
from core.network.network import Network
from ui.events.sld_update_coordinator import SLDUpdateCoordinator
from core.application.events import ElementCreated
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_projection_manager import SLDProjectionManager
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer


def test_application_event_reaches_sld_refresh_path():
    network = Network()
    application = create_application(network)
    document = SLDDocument(
        document_id="sld-test",
        name="Test SLD",
        project_id="project-test",
    )
    synchronizer = SLDReadSynchronizer(SLDProjectionManager())
    refresh_calls = []

    coordinator = SLDUpdateCoordinator(
        application=application,
        synchronizer=synchronizer,
        canvas_refresh=lambda: refresh_calls.append(True),
    )
    coordinator.bind_document(document)
    application.event_bus.subscribe(ElementCreated, coordinator.refresh)

    application.execute(
        CreateBusCommand(
            bus_id="bus-test",
            name="Bus",
            nominal_voltage_kv=132.0,
            voltage_pu=1.0,
            angle_deg=0.0,
            frequency_hz=50.0,
            in_service=True,
        )
    )

    assert refresh_calls == [True]
    assert coordinator._projection_manager.projection("bus-test") is not None

