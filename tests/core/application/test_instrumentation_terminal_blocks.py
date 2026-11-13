"""Application lifecycle and detached read-model coverage for terminal blocks."""

from core.application.project import ProjectContext
from core.application.services.instrumentation_wiring_service import InstrumentationWiringService
from core.model.instrument_wiring import (
    CableAssembly,
    CableCore,
    InstrumentationWiringInventory,
    TerminalBlock,
    TerminalPoint,
    WiringConductorRole,
    WiringTerminalReference,
)


class _NetworkMustNotResolveTerminalBlocks:
    def get_by_identity(self, equipment_id):
        raise AssertionError(
            f"Panel terminal block {equipment_id!r} must resolve from the wiring inventory, not Core Network."
        )


def test_terminal_block_points_activate_and_project_as_detached_application_data():
    first_block = TerminalBlock(
        id="tb-app-1", tag="TB-APP-1", panel_id="PANEL-A",
        location="JB-01", terminal_count=2,
    )
    second_block = TerminalBlock(
        id="tb-app-2", tag="TB-APP-2", panel_id="PANEL-A",
        location="PANEL-01", terminal_count=2,
    )
    first_point = TerminalPoint(
        id="tp-app-1", terminal_block_id=first_block.id,
        terminal_number="1", designation="X1:1",
    )
    second_point = TerminalPoint(
        id="tp-app-2", terminal_block_id=second_block.id,
        terminal_number="2", designation="X2:2",
    )
    cable = CableAssembly(
        id="c-app-1", tag="C-APP-1", service="instrument", core_count=1,
    )
    core = CableCore(
        id="cc-app-1", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(
            WiringTerminalReference(
                equipment_id=first_block.id, terminal_role="1",
                designation="X1:1", terminal_point_id=first_point.id,
            ),
            WiringTerminalReference(
                equipment_id=second_block.id, terminal_role="2",
                designation="X2:2", terminal_point_id=second_point.id,
            ),
        ),
    )
    inventory = InstrumentationWiringInventory(
        cables=(cable,), cores=(core,),
        terminal_blocks=(first_block, second_block),
        terminal_points=(first_point, second_point),
    )
    service = InstrumentationWiringService()
    context = ProjectContext(project_id="terminal-block-project", name="Terminal Block", path=None)
    service.activate(
        context, inventory,
        network=_NetworkMustNotResolveTerminalBlocks(), generation=1,
    )

    read_model = service.read_model()
    assert len(read_model.terminal_blocks) == 2
    assert len(read_model.terminal_points) == 2
    assert read_model.cores[0]["terminal_path"][0]["terminal_point_id"] == first_point.id
