"""GridForge V2 voltage-protection package export tests.

Author: Subhendu Mishra
"""


def test_voltage_package_exports_canonical_27_and_59_relays():
    from core.protection.voltage import (
        OverVoltageRelay,
        OverVoltageSettings,
        UnderVoltageRelay,
        UnderVoltageSettings,
    )

    assert OverVoltageRelay.FUNCTION_CODE == "59"
    assert OverVoltageRelay.FUNCTION_NAME == "OVER-VOLTAGE"
    assert OverVoltageRelay.VOLTAGE_INPUT == "voltage"
    assert OverVoltageSettings is not None
    assert UnderVoltageRelay.FUNCTION_CODE == "27"
    assert UnderVoltageSettings is not None
