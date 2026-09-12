"""R3 SLD local-view dirty state must not become project dirty authority."""

from core.application.bootstrap import create_application
from core.application.commands.sld_commands import SetSLDNodePositionCommand
from core.application.services.sld_service import SLDService
from core.model.bus import Bus
from core.network import Network
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_state import SLDState


def test_sld_state_dirty_is_local_view_state_only():
    state = SLDState()
    assert state.dirty is False
    assert state.local_view_dirty is False
    state.mark_dirty()
    assert state.dirty is True
    assert state.local_view_dirty is True
    state.mark_clean()
    assert state.dirty is False
    assert state.local_view_dirty is False


def test_local_sld_dirty_does_not_compete_with_application_dirty_authority():
    network = Network()
    network.add_bus(Bus("BUS-001", name="Bus 1", nominal_voltage_kv=132.0))
    application = create_application(network)
    document = SLDDocument(document_id="SLD-001", project_id="PROJECT-001")
    document.model.create_node("SLD-NODE-001", "BUS-001", 10.0, 20.0)
    application.attach_sld_service(SLDService(document))

    state = SLDState()
    state.mark_dirty()
    assert state.local_view_dirty is True
    assert application.is_dirty is False

    result = application.execute(SetSLDNodePositionCommand(node_id="SLD-NODE-001", x=30.0, y=40.0))
    assert result.success is True
    assert application.is_dirty is True
    assert state.local_view_dirty is True
