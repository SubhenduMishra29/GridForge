"""Canonical signal-consumer endpoint identity and aggregate validation."""

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


def _signal(signal_id: str, channel_id: str) -> SignalDefinition:
    return SignalDefinition(
        id=signal_id,
        tag=f"TAG-{signal_id}",
        description="Instrument measurement",
        kind=SignalKind.ANALOG,
        measurement_channel_id=channel_id,
    )


def _endpoint() -> SignalEndpointReference:
    return SignalEndpointReference(
        kind=SignalEndpointKind.CONTROL_INPUT,
        endpoint_id="component-1",
        owner_id="control-1",
        port="PV",
        physical_terminal=WiringTerminalReference(
            equipment_id="PLC-1",
            terminal_role="AI1",
            designation="AI1",
        ),
    )


def test_signal_endpoint_binding_keeps_logical_and_physical_identity_separate():
    endpoint = _endpoint()
    binding = SignalEndpointBinding(
        id="endpoint-binding-1",
        signal_id="signal-1",
        endpoint=endpoint,
    )
    inventory = InstrumentationWiringInventory(
        signals=(_signal("signal-1", "channel-1"),),
        endpoint_bindings=(binding,),
    )

    assert inventory.endpoint_bindings == (binding,)
    assert endpoint.logical_identity == (
        "CONTROL_INPUT", "control-1", "component-1", "PV",
    )
    assert endpoint.identity[-1] == ("PLC-1", "AI1", None)


def test_one_logical_consumer_input_cannot_be_bound_to_multiple_signals():
    first = SignalEndpointBinding("binding-1", "signal-1", _endpoint())
    second = SignalEndpointBinding("binding-2", "signal-2", _endpoint())

    with pytest.raises(ValueError, match="bound more than once"):
        InstrumentationWiringInventory(
            signals=(
                _signal("signal-1", "channel-1"),
                _signal("signal-2", "channel-2"),
            ),
            endpoint_bindings=(first, second),
        )


def test_signal_endpoint_binding_rejects_a_missing_signal():
    binding = SignalEndpointBinding(
        id="binding-missing",
        signal_id="missing-signal",
        endpoint=_endpoint(),
    )

    with pytest.raises(ValueError, match="references missing signal"):
        InstrumentationWiringInventory(endpoint_bindings=(binding,))


def test_protection_endpoint_retains_binding_identity_and_relay_input():
    endpoint = SignalEndpointReference(
        kind=SignalEndpointKind.PROTECTION_INPUT,
        endpoint_id="protection-measurement-binding-1",
        owner_id="protection-element-1",
        port="phase_a_current",
        physical_terminal=WiringTerminalReference(
            equipment_id="RELAY-1",
            terminal_role="IA",
            designation="IA",
        ),
    )
    binding = SignalEndpointBinding(
        id="protection-endpoint-1",
        signal_id="signal-1",
        endpoint=endpoint,
        direction="SOURCE_TO_SINK",
    )

    assert binding.endpoint.endpoint_id == "protection-measurement-binding-1"
    assert binding.endpoint.owner_id == "protection-element-1"
    assert binding.endpoint.port == "phase_a_current"
