from core.application.control_signal_mapping import ControlSignalDestination
from core.application.services.instrumentation_receiver_compatibility import (
    validate_control_receiver,
    validate_protection_receiver,
)
from core.model.instrument_wiring import SignalDefinition, SignalKind


def _signal(**overrides):
    values = dict(
        id="signal-current-1",
        tag="CT-001.SEC",
        description="Current transformer secondary current",
        kind=SignalKind.CURRENT,
        unit="A",
        phase="A",
    )
    values.update(overrides)
    return SignalDefinition(**values)


def test_control_receiver_requires_explicit_matching_type_phase_and_unit():
    destination = ControlSignalDestination(
        control_id="CTRL-1",
        component_id="PID-1",
        input_name="PV",
        expected_signal_types=("CURRENT",),
        expected_phases=("A",),
        accepted_units=("A",),
    )
    assert validate_control_receiver(_signal(), destination).compatible
    result = validate_control_receiver(_signal(unit="mA"), destination)
    assert not result.compatible
    assert any("exact units" in item for item in result.diagnostics)


def test_control_receiver_fails_closed_when_required_phase_or_unit_is_missing():
    destination = ControlSignalDestination(
        control_id="CTRL-1",
        component_id="PID-1",
        input_name="PV",
        expected_signal_types=("CURRENT",),
        expected_phases=("A",),
        accepted_units=("A",),
    )
    result = validate_control_receiver(_signal(phase=None, unit=None), destination)
    assert not result.compatible
    assert any("phase is not declared" in item for item in result.diagnostics)
    assert any("unit is not declared" in item for item in result.diagnostics)


def test_protection_receiver_uses_canonical_function_input_contract():
    result = validate_protection_receiver(
        _signal(), function_code="50", input_name="current", element_id="PROT-1",
    )
    assert result.compatible
    wrong_unit = validate_protection_receiver(
        _signal(unit="kA"), function_code="50", input_name="current", element_id="PROT-1",
    )
    assert not wrong_unit.compatible


def test_unsupported_protection_contract_and_ambiguous_signal_kind_fail_closed():
    unsupported = validate_protection_receiver(
        _signal(kind=SignalKind.TEMPERATURE, unit="degC"),
        function_code="49", input_name="temperature", element_id="PROT-49",
    )
    assert not unsupported.compatible
    assert any("no supported canonical input contract" in item for item in unsupported.diagnostics)

    ambiguous = validate_control_receiver(
        _signal(kind=SignalKind.ANALOG),
        ControlSignalDestination(
            control_id="CTRL-1", component_id="PID-1", input_name="PV",
            expected_signal_types=("CURRENT",), expected_phases=("A",), accepted_units=("A",),
        ),
    )
    assert not ambiguous.compatible
    assert any("no authoritative MeasurementSignalType mapping" in item for item in ambiguous.diagnostics)



def test_control_receiver_with_incomplete_capability_contract_fails_closed():
    destination = ControlSignalDestination(
        control_id="CTRL-1",
        component_id="PID-LEGACY",
        input_name="PV",
    )
    result = validate_control_receiver(_signal(), destination)
    assert not result.compatible
    assert any("no declared accepted signal types" in item for item in result.diagnostics)
    assert any("no declared accepted phases" in item for item in result.diagnostics)
    assert any("no declared accepted engineering units" in item for item in result.diagnostics)



def test_control_binding_requires_persisted_mapping_to_reference_signal_identity():
    from core.application.control_signal_mapping import (
        ControlSignalBinding,
        ControlSignalMapping,
        ControlSignalSource,
    )
    from core.application.services.instrumentation_receiver_compatibility import (
        validate_control_mapping_binding,
    )

    signal = _signal()
    destination = ControlSignalDestination(
        control_id="CTRL-1",
        component_id="PID-1",
        input_name="PV",
        expected_signal_types=("CURRENT",),
        expected_phases=("A",),
        accepted_units=("A",),
    )
    matching = ControlSignalMapping(bindings=(
        ControlSignalBinding(
            source=ControlSignalSource(
                domain="instrumentation",
                element_type="signal",
                object_id=signal.id,
                signal="value",
            ),
            destination=destination,
        ),
    ))
    assert validate_control_mapping_binding(signal, matching, destination).compatible

    wrong_source = ControlSignalMapping(bindings=(
        ControlSignalBinding(
            source=ControlSignalSource(
                domain="instrumentation",
                element_type="signal",
                object_id="another-signal",
                signal="value",
            ),
            destination=destination,
        ),
    ))
    result = validate_control_mapping_binding(signal, wrong_source, destination)
    assert not result.compatible
    assert any("does not identify instrumentation signal" in item for item in result.diagnostics)


def test_control_binding_without_persisted_mapping_fails_closed():
    from core.application.control_signal_mapping import ControlSignalMapping
    from core.application.services.instrumentation_receiver_compatibility import (
        validate_control_mapping_binding,
    )

    destination = ControlSignalDestination(
        control_id="CTRL-1",
        component_id="PID-1",
        input_name="PV",
        expected_signal_types=("CURRENT",),
        expected_phases=("A",),
        accepted_units=("A",),
    )
    result = validate_control_mapping_binding(_signal(), ControlSignalMapping(), destination)
    assert not result.compatible
    assert any("exactly one persisted canonical mapping" in item for item in result.diagnostics)
