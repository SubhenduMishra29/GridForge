# ============================================================
# File: tests/core/protection/test_earth_overcurrent_51n_contract.py
# GridForge V2 — ANSI 51N Earth Overcurrent Tests
# Author: Subhendu Mishra
# ============================================================

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.protection.context import ProtectionContext
from core.protection.overcurrent import (
    EarthIECOvercurrentRelay,
    EarthIECOvercurrentSettings,
)
from core.protection.relay_input import RelayInput


def _relay(value: float, available: bool = True) -> EarthIECOvercurrentRelay:
    channel = MeasurementChannel(
        id="ICH-51N",
        signal_type=MeasurementSignalType.CURRENT,
        name="Residual current",
        unit="A",
        available=available,
        quality=MeasurementQuality.GOOD if available else MeasurementQuality.INVALID,
        raw_value=value,
    )
    relay_input = RelayInput("residual_current", channel)
    return EarthIECOvercurrentRelay(
        relay_input=relay_input,
        relay_id="R1",
        element_id="OC51N",
        settings=EarthIECOvercurrentSettings(pickup=5.0, curve="SI", TMS=1.0),
    )


def test_51n_below_pickup_does_not_trip() -> None:
    decision = _relay(2.0).evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is False
    assert decision.trip_request is False


def test_51n_pickup_starts_timed_operation() -> None:
    relay = _relay(10.0)
    decision = relay.evaluate(ProtectionContext(time=1.0))
    assert decision.pickup is True
    assert decision.operate is False
    assert decision.trip_request is False
    assert decision.operating_time is not None
    assert decision.operating_time > 0.0


def test_51n_operates_when_elapsed_time_reaches_characteristic() -> None:
    relay = _relay(10.0)
    first = relay.evaluate(ProtectionContext(time=1.0))
    assert first.operating_time is not None
    second = relay.evaluate(
        ProtectionContext(time=1.0 + first.operating_time)
    )
    assert second.pickup is True
    assert second.operate is True
    assert second.trip_request is True


def test_51n_pickup_resets_when_residual_current_falls_below_pickup() -> None:
    relay = _relay(10.0)
    relay.evaluate(ProtectionContext(time=1.0))
    relay_input = relay.get_input("residual_current")
    relay_input.channel.raw_value = 2.0
    reset_decision = relay.evaluate(ProtectionContext(time=2.0))
    assert reset_decision.pickup is False
    assert reset_decision.trip_request is False


def test_51n_missing_evaluation_time_is_invalid() -> None:
    decision = _relay(10.0).evaluate()
    assert decision.valid is False
    assert decision.trip_request is False


def test_51n_unusable_measurement_is_invalid() -> None:
    decision = _relay(10.0, available=False).evaluate(ProtectionContext(time=1.0))
    assert decision.valid is False
    assert decision.trip_request is False
