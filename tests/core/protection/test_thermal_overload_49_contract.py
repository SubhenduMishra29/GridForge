# ============================================================
# File: tests/core/protection/test_thermal_overload_49_contract.py
# GridForge V2 — ANSI 49 Thermal Overload Tests
# Author: Subhendu Mishra
# ============================================================

"""Contract tests for bounded ANSI 49. Tests are authored but not executed."""

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.model.relay import Relay
from core.protection.context import ProtectionContext
from core.protection.relay_input import RelayInput
from core.protection.thermal import ThermalOverloadRelay, ThermalOverloadSettings


def _relay(value: float, available: bool = True) -> ThermalOverloadRelay:
    channel = MeasurementChannel(
        id="TCH-49",
        signal_type=MeasurementSignalType.CUSTOM,
        name="Thermal temperature",
        unit="degC",
        available=available,
        quality=MeasurementQuality.GOOD if available else MeasurementQuality.INVALID,
        raw_value=value,
    )
    relay = Relay("R1", "THERMAL", function_type="49")
    relay_input = RelayInput("temperature", channel)
    return ThermalOverloadRelay(
        relay=relay,
        relay_inputs={"temperature": relay_input},
        element_id="TH49",
        settings=ThermalOverloadSettings(pickup=100.0),
    )


def test_49_temperature_below_pickup_does_not_trip() -> None:
    decision = _relay(90.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is False
    assert decision.trip_request is False


def test_49_temperature_at_pickup_trips_instantaneously() -> None:
    decision = _relay(100.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is True
    assert decision.operate is True
    assert decision.trip_request is True
    assert decision.operating_time == 0.0


def test_49_temperature_above_pickup_trips() -> None:
    decision = _relay(120.0).evaluate(ProtectionContext(time=1.0))
    assert decision.trip_request is True


def test_49_unusable_measurement_is_invalid() -> None:
    decision = _relay(120.0, available=False).evaluate(ProtectionContext(time=1.0))
    assert decision.valid is False
    assert decision.trip_request is False
