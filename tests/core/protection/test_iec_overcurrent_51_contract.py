# ============================================================
# File: tests/core/protection/test_iec_overcurrent_51_contract.py
# GridForge V2 — IEC 51 Protection Contract Tests
# Author: Subhendu Mishra
# ============================================================

"""Headless contract tests for the canonical IEC 51 function.

These tests are intentionally authored during implementation and are
not executed as part of this change, per the project workflow.
"""

import math

import pytest

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.model.relay import Relay
from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.overcurrent.iec_relay import (
    IECOvercurrentRelay,
    IECOvercurrentSettings,
)
from core.protection.relay_input import RelayInput


class _OperationalRelay(Relay):
    """Small relay fixture exposing the canonical operational state."""

    @property
    def operational(self) -> bool:
        return self.in_service and self.enabled and not self.blocked


def _make_51(current: float = 100.0) -> tuple[IECOvercurrentRelay, MeasurementChannel]:
    relay = _OperationalRelay(
        id="R-51",
        relay_type="OVER_CURRENT",
        name="Test IEC 51 Relay",
    )
    channel = MeasurementChannel(
        id="I-51",
        signal_type=MeasurementSignalType.CURRENT,
        unit="A",
        raw_value=current,
        quality=MeasurementQuality.GOOD,
    )
    relay_input = RelayInput("current", channel)
    function = IECOvercurrentRelay(
        relay,
        element_id="OC51",
        relay_inputs={"current": relay_input},
        settings=IECOvercurrentSettings(
            pickup=100.0,
            curve="SI",
            TMS=1.0,
        ),
    )
    return function, channel


def test_51_below_pickup_does_not_pick_up() -> None:
    function, _ = _make_51(current=99.999)

    decision = function.evaluate(ProtectionContext(time=0.0))

    assert isinstance(decision, ProtectionDecision)
    assert not decision.pickup
    assert not decision.operate
    assert not decision.trip_request


def test_51_exact_pickup_does_not_start_inverse_time_operation() -> None:
    function, _ = _make_51(current=100.0)

    decision = function.evaluate(ProtectionContext(time=0.0))

    assert not decision.pickup
    assert not decision.trip_request


def test_51_above_pickup_starts_timed_operation() -> None:
    function, _ = _make_51(current=200.0)

    first = function.evaluate(ProtectionContext(time=0.0))
    assert first.pickup
    assert not first.operate
    assert not first.trip_request
    assert first.operating_time is not None
    assert math.isfinite(first.operating_time)
    assert first.operating_time > 0.0


def test_51_operates_when_elapsed_time_reaches_characteristic_time() -> None:
    function, _ = _make_51(current=200.0)

    first = function.evaluate(ProtectionContext(time=0.0))
    assert first.operating_time is not None

    second = function.evaluate(
        ProtectionContext(time=first.operating_time)
    )

    assert second.pickup
    assert second.operate
    assert second.trip_request
    assert second.operating_time == pytest.approx(first.operating_time)


def test_51_pickup_interval_resets_when_current_falls_below_pickup() -> None:
    function, channel = _make_51(current=200.0)

    first = function.evaluate(ProtectionContext(time=0.0))
    assert first.pickup

    channel.update(90.0, timestamp=0.5, quality=MeasurementQuality.GOOD)
    reset = function.evaluate(ProtectionContext(time=0.5))

    assert not reset.pickup
    assert not reset.operate
    assert not reset.trip_request

    channel.update(200.0, timestamp=1.0, quality=MeasurementQuality.GOOD)
    restarted = function.evaluate(ProtectionContext(time=1.0))

    assert restarted.pickup
    assert not restarted.trip_request
    assert restarted.metadata["pickup_start_time"] == pytest.approx(1.0)


def test_51_does_not_operate_without_authoritative_evaluation_time() -> None:
    function, _ = _make_51(current=200.0)

    decision = function.evaluate()

    assert not decision.valid
    assert not decision.operate
    assert not decision.trip_request


def test_51_rejects_backwards_evaluation_time() -> None:
    function, _ = _make_51(current=200.0)

    function.evaluate(ProtectionContext(time=10.0))

    with pytest.raises(ValueError, match="timestamp cannot move backwards"):
        function.evaluate(ProtectionContext(time=9.0))


def test_51_reset_clears_timing_and_latched_operation() -> None:
    function, _ = _make_51(current=200.0)

    first = function.evaluate(ProtectionContext(time=0.0))
    assert first.operating_time is not None
    operated = function.evaluate(ProtectionContext(time=first.operating_time))
    assert operated.trip_request

    function.reset()
    after_reset = function.evaluate(ProtectionContext(time=0.0))

    assert after_reset.pickup
    assert not after_reset.operate
    assert not after_reset.trip_request
