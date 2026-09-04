from __future__ import annotations

from core.application.bootstrap import create_application
from core.application.commands.model_commands import CreateBusCommand
from core.network.network import Network


def _create_bus_command(bus_id: str = "bus-test") -> CreateBusCommand:
    return CreateBusCommand(
        bus_id=bus_id,
        name="Bus",
        nominal_voltage_kv=132.0,
        voltage_pu=1.0,
        angle_deg=0.0,
        frequency_hz=50.0,
        in_service=True,
    )


def test_application_create_bus_mutates_network_and_publishes_event():
    network = Network()
    application = create_application(network)
    events = []
    application.event_bus.subscribe(events.append)

    result = application.execute(_create_bus_command())

    assert result.success is True
    assert network.get_bus("bus-test") is not None
    assert len(events) == 1
    assert events[0].operation == "model.create_bus"


def test_application_create_bus_duplicate_id_fails_without_second_event():
    network = Network()
    application = create_application(network)
    events = []
    application.event_bus.subscribe(events.append)

    application.execute(_create_bus_command())

    try:
        application.execute(_create_bus_command())
    except Exception:
        pass
    else:
        raise AssertionError("duplicate Bus creation must fail")

    assert len(events) == 1
    assert network.get_bus("bus-test") is not None
