"""Targeted protection decision -> application -> breaker integration test.

Author: Subhendu Mishra
"""

from core.application.commands.breaker_commands import TripBreakerCommand
from core.application.services.model_service import ModelService
from core.application.transaction import Transaction
from core.model.breaker import Breaker
from core.model.bus import Bus
from core.network.network import Network
from core.protection.decision import ProtectionDecision
from core.application.services.protection_output_service import ProtectionOutputService


def test_actionable_protection_decision_trips_breaker_through_application_boundary():
    network = Network()
    bus_a = Bus("B1", nominal_voltage_kv=132.0)
    bus_b = Bus("B2", nominal_voltage_kv=132.0)
    breaker = Breaker("CB1", endpoint_from=bus_a, endpoint_to=bus_b, closed=True)
    network.add_bus(bus_a)
    network.add_bus(bus_b)
    network.add_breaker(breaker)
    network.rebuild_topology()

    decision = ProtectionDecision(
        relay_id="R1",
        element_id="R1-50",
        function_code="50",
        pickup=True,
        operate=True,
        trip_request=True,
        timestamp=1.25,
    )
    command = TripBreakerCommand(breaker_id="CB1")
    assert command.payload["breaker_id"] == "CB1"

    transaction = Transaction()
    result = ProtectionOutputService(ModelService(network)).trip_from_decision(
        decision=decision,
        breaker_id=command.payload["breaker_id"],
        transaction=transaction,
    )

    assert result.value is breaker
    assert breaker.is_open
    assert network.topology_dirty
