# ============================================================
# File: tests/core/protection/test_earth_overcurrent_50n_contract.py
# GridForge V2 — ANSI 50N Earth Overcurrent Tests
# Author: Subhendu Mishra
# ============================================================

from core.protection.context import ProtectionContext
from core.protection.overcurrent.earth_instantaneous_relay import (
    EarthInstantaneousOvercurrentRelay,
    EarthInstantaneousOvercurrentSettings,
)


def test_50n_below_pickup_does_not_trip(measurement_channel_factory) -> None:
    channel = measurement_channel_factory(available=True, value=2.0)
    relay_input = EarthInstantaneousOvercurrentRelay.input_binding(channel)
    relay = EarthInstantaneousOvercurrentRelay(
        relay_input=relay_input,
        relay_id="R1",
        element_id="OC50N",
        settings=EarthInstantaneousOvercurrentSettings(pickup=5.0),
    )

    decision = relay.evaluate(ProtectionContext(time=1.0))

    assert decision.pickup is False
    assert decision.trip_request is False


def test_50n_at_or_above_pickup_trips_instantaneously(measurement_channel_factory) -> None:
    channel = measurement_channel_factory(available=True, value=5.0)
    relay_input = EarthInstantaneousOvercurrentRelay.input_binding(channel)
    relay = EarthInstantaneousOvercurrentRelay(
        relay_input=relay_input,
        relay_id="R1",
        element_id="OC50N",
        settings=EarthInstantaneousOvercurrentSettings(pickup=5.0),
    )

    decision = relay.evaluate(ProtectionContext(time=1.0))

    assert decision.pickup is True
    assert decision.operate is True
    assert decision.trip_request is True
    assert decision.operating_time == 0.0


def test_50n_unusable_measurement_is_invalid(measurement_channel_factory) -> None:
    channel = measurement_channel_factory(available=False, value=10.0)
    relay_input = EarthInstantaneousOvercurrentRelay.input_binding(channel)
    relay = EarthInstantaneousOvercurrentRelay(
        relay_input=relay_input,
        relay_id="R1",
        element_id="OC50N",
        settings=EarthInstantaneousOvercurrentSettings(pickup=5.0),
    )

    decision = relay.evaluate(ProtectionContext(time=1.0))

    assert decision.valid is False
    assert decision.trip_request is False
