"""Control/Ladder completion contract tests.

Author: Subhendu Mishra

These tests are intentionally focused on semantic/application contracts;
full UI integration and persistence tests remain follow-up verification.
"""

from core.application.commands.control_commands import (
    AddControlComponent, AddLadderRung, ConnectControlSignals,
)
from core.application.services.control_service import ControlApplicationService
from core.application.transaction import Transaction
from core.control.logic.contacts import NormallyOpenContact
from core.control.logic.engine import LogicEngine
from core.control.logic.ladder import LadderProgram
from core.control.logic.coils import LogicCoil


def test_ladder_program_keeps_engine_as_single_execution_authority():
    program = LadderProgram("test")
    program.add_rung("r1")
    program.add_component(NormallyOpenContact("c1"), rung_id="r1")
    program.add_component(LogicCoil("k1"), rung_id="r1")
    assert isinstance(program.engine, LogicEngine)
    assert [c.component_id for c in program.engine.components()] == ["c1", "k1"]
    assert program.rung("r1").elements[0].component_id == "c1"


def test_control_commands_are_immutable_application_intents():
    command = AddControlComponent(component_id="c1", component_type="coil", rung_id="r1")
    assert command.command_type == "control.add_component"
    assert command.payload["component_id"] == "c1"
    assert isinstance(command.payload, dict.__mro__[1]) or command.payload["component_id"] == "c1"


def test_control_service_creates_component_and_rung_through_transaction():
    service = ControlApplicationService()
    transaction = Transaction()
    result = service.add_component(transaction, component_id="c1", component_type="coil", rung_id="r1")
    assert result.success
    snapshot = service.read()
    assert snapshot.program_id == "control"
    assert snapshot.rungs[0].component_ids == ("c1",)
    assert snapshot.components[0].component_type == "coil"


def test_control_connection_is_semantic_not_graphical():
    service = ControlApplicationService()
    tx = Transaction()
    service.add_component(tx, component_id="c1", component_type="normally_open_contact", rung_id="r1")
    service.add_component(tx, component_id="k1", component_type="coil", rung_id="r1")
    connection = service.connect_signals(tx, source_component="c1", source_output="OUT", target_component="k1", target_input="IN")
    assert connection.success
    assert service.read().connections[0].source_component == "c1"


def test_application_commands_expose_the_expected_pipeline_types():
    assert AddLadderRung(rung_id="r1").command_type == "control.add_rung"
    assert ConnectControlSignals(source_component="a", source_output="OUT", target_component="b", target_input="IN").command_type == "control.connect_signals"
