from types import SimpleNamespace

from core.application.commands.placement_commands import PlaceBusCommand
from core.application.placement_command_handlers import BusPlacementCommandHandler
from core.application.results import ApplicationResult
from core.application.services.model_service import ModelService
from core.application.services.sld_service import SLDService
from core.application.transaction import Transaction
from core.network import Network


class RecordingSLDService(SLDService):
    def __init__(self, *, fail=False):
        self.fail = fail
        self.calls = []
        self.state = []

    def execute(self, command, transaction):
        if self.fail:
            raise RuntimeError("presentation failure")
        self.calls.append((command.payload["node_id"], command.payload["equipment_id"], command.payload["x"], command.payload["y"]))
        self.state.append(command.payload["node_id"])
        transaction.record_undo(lambda: self.state.remove(command.payload["node_id"]))
        return ApplicationResult.success_result(
            message="SLD node added.",
            metadata={"presentation_operation": "add_node", "node_id": command.payload["node_id"]},
        )


def test_bus_placement_uses_one_transaction_for_model_and_presentation():
    network = Network()
    model = ModelService(network)
    sld = RecordingSLDService()
    handler = BusPlacementCommandHandler(sld, model)
    transaction = Transaction()

    command = PlaceBusCommand(bus_id="bus-1", x=120.0, y=80.0)
    result = handler(command, SimpleNamespace(network=network), transaction)

    assert result.success
    assert network.get_by_id("bus", "bus-1") is not None
    assert sld.state == ["bus-1"]
    assert sld.calls == [("bus-1", "bus-1", 120.0, 80.0)]


def test_bus_placement_failure_rolls_back_both_mutations():
    network = Network()
    model = ModelService(network)
    sld = RecordingSLDService(fail=True)
    handler = BusPlacementCommandHandler(sld, model)
    transaction = Transaction()

    command = PlaceBusCommand(bus_id="bus-2", x=20.0, y=30.0)

    try:
        handler(command, SimpleNamespace(network=network), transaction)
    except RuntimeError as exc:
        assert str(exc) == "presentation failure"
    else:
        raise AssertionError("expected presentation failure")

    transaction.rollback()
    assert network.get_by_id("bus", "bus-2") is None
    assert sld.state == []
