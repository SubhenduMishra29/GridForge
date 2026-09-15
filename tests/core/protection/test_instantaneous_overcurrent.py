# ============================================================
# File: tests/core/protection/test_instantaneous_overcurrent.py
# GridForge V2 — ANSI 50 Instantaneous Overcurrent Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import pytest

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.model.relay import Relay
from core.protection.context import ProtectionContext
from core.protection.overcurrent.instantaneous_relay import (
    InstantaneousOvercurrentRelay,
    InstantaneousOvercurrentSettings,
)
from core.protection.relay_input import RelayInput


def _relay_input(value: float) -> RelayInput:
    channel = MeasurementChannel(
        id="CH-I",
        signal_type=MeasurementSignalType.CURRENT,
        unit="A",
        quality=MeasurementQuality.GOOD,
        raw_value=value,
    )
    return RelayInput("current", channel)


def _function(current: float, pickup: float = 100.0) -> InstantaneousOvercurrentRelay:
    relay = Relay("R1", "OVER_CURRENT")
    return InstantaneousOvercurrentRelay(
        relay,
        element_id="OC50-1",
        relay_inputs={"current": _relay_input(current)},
        settings=InstantaneousOvercurrentSettings(pickup=pickup),
    )


def test_ansi_50_below_pickup_does_not_operate() -> None:
    decision = _function(99.0).evaluate(ProtectionContext(time=0.0))

    assert decision.function_code == "50"
    assert decision.valid is True
    assert decision.pickup is False
    assert decision.operate is False
    assert decision.trip_request is False


def test_ansi_50_exact_pickup_operates_instantaneously() -> None:
    decision = _function(100.0).evaluate(ProtectionContext(time=0.0))

    assert decision.pickup is True
    assert decision.operate is True
    assert decision.trip_request is True
    assert decision.operating_time == pytest.approx(0.0)


def test_ansi_50_above_pickup_operates_instantaneously() -> None:
    decision = _function(250.0).evaluate(ProtectionContext(time=0.0))

    assert decision.pickup is True
    assert decision.operate is True
    assert decision.trip_request is True
    assert decision.operating_time == pytest.approx(0.0)


def test_ansi_50_rejects_unusable_measurement_without_fabricating_trip() -> None:
    relay = Relay("R1", "OVER_CURRENT")
    input_binding = _relay_input(250.0)
    input_binding.channel.update(250.0, quality=MeasurementQuality.INVALID)
    function = InstantaneousOvercurrentRelay(
        relay,
        element_id="OC50-1",
        relay_inputs={"current": input_binding},
        settings=InstantaneousOvercurrentSettings(pickup=100.0),
    )

    decision = function.evaluate(ProtectionContext(time=0.0))

    assert decision.valid is False
    assert decision.pickup is False
    assert decision.operate is False
    assert decision.trip_request is False
