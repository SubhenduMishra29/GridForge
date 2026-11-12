import pytest

from core.model import TemperatureInputMode, TemperatureInstrumentInventory, TemperatureInterfaceDevice, TemperatureSensorTechnology


def interface(identifier):
    return TemperatureInterfaceDevice(
        id=identifier, tag="TT-001", equipment_kind=TemperatureInputMode.TRANSMITTER,
        supported_sensor_technologies=(TemperatureSensorTechnology.RTD,),
        supported_sensor_configurations=("Pt100 3-wire",),
        input_terminals=(
            __import__("core.model", fromlist=["WiringTerminalReference"]).WiringTerminalReference(identifier, "A", "A"),
        ),
        output_terminals=(
            __import__("core.model", fromlist=["WiringTerminalReference"]).WiringTerminalReference(identifier, "OUT", "OUT"),
        ),
        output_signal_kind="4-20mA", output_unit="degC",
    )


def test_interface_tags_are_unique_within_their_namespace():
    with pytest.raises(ValueError, match="interface tags must be unique"):
        TemperatureInstrumentInventory(interfaces=(interface("tx-1"), interface("tx-2")))
