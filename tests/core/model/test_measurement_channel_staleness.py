from __future__ import annotations

import pytest

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementSignalType,
    MeasurementValidity,
)


@pytest.mark.parametrize("value", [True, False])
def test_measurement_channel_rejects_boolean_stale_after(value: bool) -> None:
    with pytest.raises(TypeError, match="stale_after"):
        MeasurementChannel(
            id="channel-stale-after-bool",
            signal_type=MeasurementSignalType.CURRENT,
            stale_after=value,
        )


def test_measurement_channel_rejects_boolean_current_time() -> None:
    channel = MeasurementChannel(
        id="channel-current-time-bool",
        signal_type=MeasurementSignalType.CURRENT,
        quality=MeasurementQuality.GOOD,
        available=True,
        timestamp=0.0,
        timestamp_domain="simulation",
        stale_after=1.0,
    )

    with pytest.raises(TypeError, match="current_time"):
        channel.validity(current_time=True)


def test_measurement_channel_stale_after_boundary_is_strictly_greater() -> None:
    channel = MeasurementChannel(
        id="channel-stale-after-boundary",
        signal_type=MeasurementSignalType.CURRENT,
        quality=MeasurementQuality.GOOD,
        available=True,
        timestamp=10.0,
        timestamp_domain="simulation",
        stale_after=5.0,
    )

    assert channel.validity(current_time=15.0) is MeasurementValidity.VALID
    assert channel.validity(current_time=15.001) is MeasurementValidity.STALE
