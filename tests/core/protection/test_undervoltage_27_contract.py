# ============================================================
# File: tests/core/protection/test_undervoltage_27_contract.py
# GridForge V2 — ANSI 27 Under-Voltage Tests
# Author: Subhendu Mishra
# ============================================================

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.model.relay import Relay
from core.protection.context import ProtectionContext
from core.protection.relay_input import RelayInput
from core.protection.voltage.undervoltage_relay import (
    UnderVoltageRelay,
    UnderVoltageSettings,
)


def _relay(value: float | complex, available: bool = True) -> UnderVoltageRelay:
    channel = MeasurementChannel(
        id="VCH-27",
        signal_type=MeasurementSignalType.VOLTAGE,
        name="Voltage",
        unit="V",
        available=available,
        quality=MeasurementQuality.GOOD if available else MeasurementQuality.INVALID,
        raw_value=value,
    )
    relay = Relay("R1", "VOLTAGE", function_type="27")
    relay_input = RelayInput("voltage", channel)
    return UnderVoltageRelay(
        relay=relay,
        relay_inputs={"voltage": relay_input},
        element_id="UV27",
        settings=UnderVoltageSettings(pickup=100.0),
    )


def test_27_voltage_above_pickup_does_not_trip() -> None:
    decision = _relay(110.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is False
    assert decision.operate is False
    assert decision.trip_request is False


def test_27_voltage_at_pickup_trips_instantaneously() -> None:
    decision = _relay(100.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is True
    assert decision.operate is True
    assert decision.trip_request is True
    assert decision.operating_time == 0.0


def test_27_voltage_below_pickup_trips_instantaneously() -> None:
    decision = _relay(90.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is True
    assert decision.operate is True
    assert decision.trip_request is True
    assert decision.operating_time == 0.0


def test_27_uses_voltage_phasor_magnitude() -> None:
    decision = _relay(60.0 + 80.0j).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is True
    assert decision.trip_request is True
    assert decision.metadata["voltage"] == 100.0


def test_27_unusable_measurement_is_invalid() -> None:
    decision = _relay(90.0, available=False).evaluate(ProtectionContext(time=1.0))
    assert decision.valid is False
    assert decision.trip_request is False
