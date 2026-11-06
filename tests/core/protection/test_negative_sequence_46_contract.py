# ============================================================
# File: tests/core/protection/test_negative_sequence_46_contract.py
# GridForge V2 — ANSI 46 Negative-Sequence Overcurrent Tests
# Author: Subhendu Mishra
# ============================================================

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementPhase,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.model.relay import Relay
from core.protection.context import ProtectionContext
from core.protection.overcurrent.negative_sequence_relay import (
    NegativeSequenceOvercurrentRelay,
    NegativeSequenceOvercurrentSettings,
)
from core.protection.relay_input import RelayInput


def _relay(
    value: float | complex,
    *,
    available: bool = True,
    phase: MeasurementPhase = MeasurementPhase.NEGATIVE_SEQUENCE,
) -> NegativeSequenceOvercurrentRelay:
    channel = MeasurementChannel(
        id="I2CH-46",
        signal_type=MeasurementSignalType.CURRENT,
        name="Negative Sequence Current",
        unit="A",
        phase=phase,
        available=available,
        quality=MeasurementQuality.GOOD if available else MeasurementQuality.INVALID,
        raw_value=value,
    )
    relay = Relay("R46", "OVER_CURRENT", function_type="46")
    relay_input = RelayInput("negative_sequence_current", channel)
    return NegativeSequenceOvercurrentRelay(
        relay=relay,
        relay_inputs={"negative_sequence_current": relay_input},
        element_id="NS46",
        settings=NegativeSequenceOvercurrentSettings(pickup=100.0),
    )


def test_46_negative_sequence_current_below_pickup_does_not_trip() -> None:
    decision = _relay(90.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is False
    assert decision.operate is False
    assert decision.trip_request is False


def test_46_negative_sequence_current_at_pickup_trips_instantaneously() -> None:
    decision = _relay(100.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is True
    assert decision.operate is True
    assert decision.trip_request is True
    assert decision.operating_time == 0.0


def test_46_negative_sequence_current_above_pickup_trips_instantaneously() -> None:
    decision = _relay(125.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is True
    assert decision.trip_request is True


def test_46_uses_negative_sequence_current_phasor_magnitude() -> None:
    decision = _relay(60.0 + 80.0j).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is True
    assert decision.trip_request is True
    assert decision.metadata["negative_sequence_current"] == 100.0


def test_46_requires_negative_sequence_current_channel() -> None:
    decision = _relay(150.0, phase=MeasurementPhase.POSITIVE_SEQUENCE).evaluate(
        ProtectionContext(time=1.0)
    )
    assert decision.valid is False
    assert decision.trip_request is False


def test_46_unusable_measurement_is_invalid() -> None:
    decision = _relay(150.0, available=False).evaluate(ProtectionContext(time=1.0))
    assert decision.valid is False
    assert decision.trip_request is False
