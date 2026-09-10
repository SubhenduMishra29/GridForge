from __future__ import annotations

import pytest

from core.control.measurement_input import ControlInput
from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementSignalType,
)


def test_control_input_consumes_measurement_channel_without_copying_source_state() -> None:
    channel = MeasurementChannel(
        id="BUS-101-V",
        signal_type=MeasurementSignalType.VOLTAGE,
        unit="pu",
        raw_value=0.78,
        available=True,
        quality=MeasurementQuality.GOOD,
        timestamp=12.5,
    )

    control_input = ControlInput.from_measurement(channel)

    assert control_input.source_id == "BUS-101-V"
    assert control_input.value == channel.engineering_value
    assert control_input.timestamp == 12.5
    assert control_input.quality is MeasurementQuality.GOOD
    assert control_input.is_usable is True
    assert not hasattr(control_input, "source")


def test_unusable_measurement_is_rejected_by_control_input() -> None:
    channel = MeasurementChannel(
        id="BUS-101-V",
        signal_type=MeasurementSignalType.VOLTAGE,
        unit="pu",
        raw_value=0.78,
        available=False,
        quality=MeasurementQuality.UNKNOWN,
        timestamp=12.5,
    )

    with pytest.raises(ValueError, match="not usable"):
        ControlInput.from_measurement(channel, require_usable=True)
