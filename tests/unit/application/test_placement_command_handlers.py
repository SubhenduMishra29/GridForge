from core.application.commands.placement_commands import PlaceBusCommand
from core.application.placement_command_handlers import BusPlacementCommandHandler
from core.application.results import ApplicationResult
from core.application.transaction import Transaction


class RecordingModelService:
    def __init__(self):
        self.calls = []
        self.state = []

    def create_bus(self, **kwargs):
        self.calls.append(kwargs)
        self.state.append(kwargs["bus_id"])
        kwargs["transaction"].record_undo(lambda: self.state.remove(kwargs["bus_id"]))
        return ApplicationResult.success_result(
            value=kwargs["bus_id"],
            message="Bus created.",
            metadata={"element_type": "bus", "element_id": kwargs["bus_id"]},
        )


class RecordingSLDService:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.calls = []
        self.state = []

    def add_node(self, *, node_id, equipment_id, x, y, transaction):
        if self.fail:
            raise RuntimeError("presentation failure")
        self.calls.append((node_id, equipment_id, x, y))
        self.state.append(node_id)
        transaction.record_undo(lambda: self.state.remove(node_id))
        return ApplicationResult.success_result(
            message="SLD node added.",
            metadata={"presentation_operation": "add_node", "node_id": node_id},
        )


def test_bus_placement_uses_one_transaction_for_model_and_presentation():
    model = RecordingModelService()
    sld = RecordingSLDService()
    handler = BusPlacementCommandHandler(model, sld)
    transaction = Transaction()

    command = PlaceBusCommand(bus_id="bus-1", x=120.0, y=80.0)
    result = handler(command, object(), transaction)

    assert result.success
    assert model.state == ["bus-1"]
    assert sld.state == ["bus-1"]
    assert model.calls[0]["transaction"] is transaction
    assert sld.calls == [("bus-1", "bus-1", 120.0, 80.0)]


def test_bus_placement_failure_rolls_back_both_mutations():
    model = RecordingModelService()
    sld = RecordingSLDService(fail=True)
    handler = BusPlacementCommandHandler(model, sld)
    transaction = Transaction()

    command = PlaceBusCommand(bus_id="bus-2", x=20.0, y=30.0)

    try:
        handler(command, object(), transaction)
    except RuntimeError as exc:
        assert str(exc) == "presentation failure"
    else:
        raise AssertionError("expected presentation failure")

    transaction.rollback()
    assert model.state == []
    assert sld.state == []
