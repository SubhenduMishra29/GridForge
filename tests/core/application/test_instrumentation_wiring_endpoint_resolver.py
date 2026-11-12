from types import SimpleNamespace

from core.application.control_signal_mapping import (
    ControlSignalBinding,
    ControlSignalDestination,
    ControlSignalMapping,
    ControlSignalSource,
)
from core.application.instrumentation_wiring_endpoint_resolver import (
    resolve_signal_endpoint_bindings,
)
from core.model.instrument_wiring import (
    CableAssembly,
    CableCore,
    CarrierKind,
    InstrumentationWiringInventory,
    SignalCarrierBinding,
    SignalDefinition,
    SignalEndpointBinding,
    SignalEndpointKind,
    SignalEndpointReference,
    SignalKind,
    WiringConductorRole,
    WiringTerminalReference,
)


def _signal_inventory(*bindings):
    signal = SignalDefinition(
        id="signal-1", tag="SIG-1", description="Phase A current",
        kind=SignalKind.CURRENT, unit="A", phase="A",
    )
    cable = CableAssembly(
        id="cable-1", tag="C-1", service="instrument signal", core_count=1,
    )
    core = CableCore(
        id="core-1", cable_id=cable.id, core_number=1,
        role=WiringConductorRole.SIGNAL,
        terminal_path=(
            WiringTerminalReference("CT-101", "S1", "S1"),
            WiringTerminalReference("TB-101", "1", "1"),
        ),
    )
    carrier = SignalCarrierBinding(
        id="carrier-1", signal_id=signal.id,
        carrier_kind=CarrierKind.CABLE_CORE, carrier_id=core.id,
    )
    return InstrumentationWiringInventory(
        cables=(cable,), cores=(core,), signals=(signal,),
        signal_bindings=(carrier,), endpoint_bindings=tuple(bindings),
    )


def _channel(channel_id="channel-1"):
    return SimpleNamespace(
        channel_id=channel_id,
        signal_type="CURRENT",
        source_id="CT-101",
        source_terminal={
            "kind": "TERMINAL",
            "equipment_id": "CT-101",
            "terminal_role": "S1",
        },
    )


def _endpoint_binding(binding_id, kind, endpoint_id, owner_id=None, port=None):
    return SignalEndpointBinding(
        id=binding_id,
        signal_id="signal-1",
        endpoint=SignalEndpointReference(
            kind=kind, endpoint_id=endpoint_id, owner_id=owner_id, port=port,
        ),
    )


def test_measurement_channel_endpoint_resolves_only_by_stable_channel_id():
    binding = _endpoint_binding(
        "channel-ref", SignalEndpointKind.MEASUREMENT_CHANNEL, "channel-1",
    )
    result = resolve_signal_endpoint_bindings(
        _signal_inventory(binding),
        measurement_channels=(_channel(),),
        control_signal_mapping=None,
        protection_configuration=None,
    )
    assert result[0].status == "RESOLVED"


def test_missing_measurement_channel_is_reported_unresolved():
    binding = _endpoint_binding(
        "channel-ref", SignalEndpointKind.MEASUREMENT_CHANNEL, "missing-channel",
    )
    result = resolve_signal_endpoint_bindings(
        _signal_inventory(binding),
        measurement_channels=(),
        control_signal_mapping=None,
        protection_configuration=None,
    )
    assert result[0].status == "UNRESOLVED"
    assert "not present" in result[0].diagnostics[0]


def test_control_input_requires_exact_active_control_mapping_and_channel_provenance():
    channel_ref = _endpoint_binding(
        "channel-ref", SignalEndpointKind.MEASUREMENT_CHANNEL, "channel-1",
    )
    control_ref = _endpoint_binding(
        "control-ref", SignalEndpointKind.CONTROL_INPUT,
        "component-1", "control-1", "PV",
    )
    mapping = ControlSignalMapping(bindings=(
        ControlSignalBinding(
            source=ControlSignalSource(
                domain="measurement", element_type="channel",
                object_id="channel-1", signal="value",
            ),
            destination=ControlSignalDestination(
                control_id="control-1", component_id="component-1",
                input_name="PV",
            ),
        ),
    ))
    result = resolve_signal_endpoint_bindings(
        _signal_inventory(channel_ref, control_ref),
        measurement_channels=(_channel(),),
        control_signal_mapping=mapping,
        protection_configuration=None,
    )
    assert tuple(item.status for item in result) == ("RESOLVED", "RESOLVED")


def test_control_input_without_exact_mapping_is_unresolved():
    control_ref = _endpoint_binding(
        "control-ref", SignalEndpointKind.CONTROL_INPUT,
        "component-1", "control-1", "PV",
    )
    result = resolve_signal_endpoint_bindings(
        _signal_inventory(control_ref),
        measurement_channels=(),
        control_signal_mapping=ControlSignalMapping(),
        protection_configuration=None,
    )
    assert result[0].status == "UNRESOLVED"


def test_protection_input_requires_matching_binding_owner_port_and_channel():
    channel_ref = _endpoint_binding(
        "channel-ref", SignalEndpointKind.MEASUREMENT_CHANNEL, "channel-1",
    )
    protection_ref = _endpoint_binding(
        "protection-ref", SignalEndpointKind.PROTECTION_INPUT,
        "protection-binding-1", "element-1", "IA",
    )
    binding = SimpleNamespace(
        protection_element_id="element-1",
        relay_input_id="IA",
        channel_id="channel-1",
    )
    element = SimpleNamespace(input_channel_ids={"IA": "channel-1"})
    configuration = SimpleNamespace(
        get_measurement_binding=lambda binding_id: binding,
        get=lambda element_id: element,
    )
    result = resolve_signal_endpoint_bindings(
        _signal_inventory(channel_ref, protection_ref),
        measurement_channels=(_channel(),),
        control_signal_mapping=None,
        protection_configuration=configuration,
    )
    assert tuple(item.status for item in result) == ("RESOLVED", "RESOLVED")



def test_control_core_source_is_checked_through_application_read_service():
    control_ref = _endpoint_binding(
        "control-ref", SignalEndpointKind.CONTROL_INPUT,
        "component-1", "control-1", "PV",
    )
    mapping = ControlSignalMapping(bindings=(
        ControlSignalBinding(
            source=ControlSignalSource(
                domain="core", element_type="bus",
                object_id="BUS-1", signal="voltage_pu",
            ),
            destination=ControlSignalDestination(
                control_id="control-1", component_id="component-1",
                input_name="PV",
            ),
        ),
    ))
    class ReadService:
        def element(self, element_type, object_id):
            assert (element_type, object_id) == ("bus", "BUS-1")
            return SimpleNamespace(attributes={"voltage_pu": 1.0})

    result = resolve_signal_endpoint_bindings(
        _signal_inventory(control_ref),
        measurement_channels=(),
        control_signal_mapping=mapping,
        protection_configuration=None,
        read_service=ReadService(),
    )
    assert result[0].status == "RESOLVED"


def test_control_core_source_missing_from_read_service_is_unresolved():
    control_ref = _endpoint_binding(
        "control-ref", SignalEndpointKind.CONTROL_INPUT,
        "component-1", "control-1", "PV",
    )
    mapping = ControlSignalMapping(bindings=(
        ControlSignalBinding(
            source=ControlSignalSource(
                domain="core", element_type="bus",
                object_id="missing-bus", signal="voltage_pu",
            ),
            destination=ControlSignalDestination(
                control_id="control-1", component_id="component-1",
                input_name="PV",
            ),
        ),
    ))
    class ReadService:
        def element(self, element_type, object_id):
            raise KeyError(object_id)

    result = resolve_signal_endpoint_bindings(
        _signal_inventory(control_ref),
        measurement_channels=(),
        control_signal_mapping=mapping,
        protection_configuration=None,
        read_service=ReadService(),
    )
    assert result[0].status == "UNRESOLVED"
