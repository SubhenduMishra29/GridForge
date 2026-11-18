"""Schema-6 persistence for canonical instrumentation signal endpoints."""

import pytest

from core.model.instrument_wiring import (
    InstrumentationWiringInventory,
    SignalDefinition,
    SignalEndpointBinding,
    SignalEndpointKind,
    SignalEndpointReference,
    SignalKind,
    WiringTerminalReference,
)
from core.persistence.instrument_wiring_serializer import (
    InstrumentationWiringSerializationError,
    deserialize_instrumentation_wiring,
    serialize_instrumentation_wiring,
)


def _inventory() -> InstrumentationWiringInventory:
    signal = SignalDefinition(
        id="signal-persist-1",
        tag="SIG-PERSIST-1",
        description="Relay phase current",
        kind=SignalKind.CURRENT,
        unit="A",
        phase="A",
        measurement_channel_id="channel-persist-1",
    )
    endpoint = SignalEndpointReference(
        kind=SignalEndpointKind.PROTECTION_INPUT,
        endpoint_id="protection-binding-persist-1",
        owner_id="protection-element-persist-1",
        port="phase_a_current",
        physical_terminal=WiringTerminalReference(
            equipment_id="RELAY-PERSIST-1",
            terminal_role="IA",
            designation="IA",
        ),
    )
    binding = SignalEndpointBinding(
        id="endpoint-persist-1",
        signal_id=signal.id,
        endpoint=endpoint,
    )
    return InstrumentationWiringInventory(
        signals=(signal,),
        endpoint_bindings=(binding,),
    )


def test_schema_six_round_trips_signal_endpoint_binding_without_losing_identity():
    inventory = _inventory()

    payload = serialize_instrumentation_wiring(inventory)
    restored = deserialize_instrumentation_wiring(payload)

    assert payload["schema"] == 6
    assert restored == inventory


def test_schema_five_payload_remains_readable_without_endpoint_bindings():
    payload = serialize_instrumentation_wiring(InstrumentationWiringInventory())
    payload["schema"] = 5
    payload.pop("endpoint_bindings")

    restored = deserialize_instrumentation_wiring(payload)

    assert restored == InstrumentationWiringInventory()
    assert restored.endpoint_bindings == ()


def test_schema_six_rejects_malformed_physical_sink_terminal_reference():
    payload = serialize_instrumentation_wiring(_inventory())
    del payload["endpoint_bindings"][0]["endpoint"]["physical_terminal"]["terminal_point_id"]

    with pytest.raises(InstrumentationWiringSerializationError, match="Malformed wiring terminal reference"):
        deserialize_instrumentation_wiring(payload)
