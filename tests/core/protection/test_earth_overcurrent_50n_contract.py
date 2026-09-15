# ============================================================
# File: tests/core/protection/test_earth_overcurrent_50n_contract.py
# GridForge V2 — ANSI 50N Earth Overcurrent Tests
# Author: Subhendu Mishra
# ============================================================

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.protection.context import ProtectionContext
from core.protection.overcurrent.earth_instantaneous_relay import (
    EarthInstantaneousOvercurrentRelay,
    EarthInstantaneousOvercurrentSettings,
)
from core.protection.relay_input import RelayInput


def _relay(value: float, available: bool = True) -> EarthInstantaneousOvercurrentRelay:
    channel = MeasurementChannel(
        id="ICH-50N",
        signal_type=MeasurementSignalType.CURRENT,
        name="Residual current",
        unit="A",
        available=available,
        quality=MeasurementQuality.GOOD if available else MeasurementQuality.INVALID,
        raw_value=value,
    )
    relay_input = RelayInput("residual_current", channel)
    return EarthInstantaneousOvercurrentRelay(
        relay_input=relay_input,
        relay_id="R1",
        element_id="OC50N",
        settings=EarthInstantaneousOvercurrentSettings(pickup=5.0),
    )


def test_50n_below_pickup_does_not_trip() -> None:
    decision = _relay(2.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is False
    assert decision.trip_request is False


def test_50n_at_or_above_pickup_trips_instantaneously() -> None:
    decision = _relay(5.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is True
    assert decision.operate is True
    assert decision.trip_request is True
    assert decision.operating_time == 0.0


def test_50n_unusable_measurement_is_invalid() -> None:
    decision = _relay(10.0, available=False).evaluate(ProtectionContext(time=1.0))
    assert decision.valid is False
    assert decision.trip_request is False
