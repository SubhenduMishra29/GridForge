from core.model import (
    EndpointReference,
    EquipmentType,
    RTD,
    RTDWiringConfiguration,
    Thermocouple,
    ThermocoupleType,
)


def test_rtd_exposes_configuration_specific_authoritative_terminals():
    rtd = RTD("RTD-1", wiring_configuration=RTDWiringConfiguration.THREE_WIRE)
    assert tuple(terminal.role for terminal in rtd.terminals) == ("A", "B1", "B2")
    assert all(terminal.owner is rtd for terminal in rtd.terminals)
    assert EquipmentType.RTD.value == "rtd"
    assert rtd.element_type == "RTD"


def test_rtd_rejects_endpoint_roles_outside_declared_configuration():
    try:
        RTD("RTD-2", wiring_configuration="2_WIRE", endpoints={"B1": object()})
    except ValueError as exc:
        assert "roles" in str(exc)
    else:
        raise AssertionError("RTD accepted a terminal role outside its declared configuration.")


def test_thermocouple_exposes_polarity_terminals_and_type():
    sensor = Thermocouple("TC-1", thermocouple_type=ThermocoupleType.K)
    assert tuple(terminal.role for terminal in sensor.terminals) == ("POSITIVE", "NEGATIVE")
    assert all(terminal.owner is sensor for terminal in sensor.terminals)
    assert EquipmentType.THERMOCOUPLE.value == "thermocouple"
    assert sensor.element_type == "THERMOCOUPLE"


def test_thermocouple_rejects_unsupported_type():
    try:
        Thermocouple("TC-2", thermocouple_type="TYPE_X")
    except ValueError:
        pass
    else:
        raise AssertionError("Thermocouple accepted an unsupported type.")


def test_temperature_sensor_endpoint_reference_uses_canonical_equipment_type():
    reference = EndpointReference.terminal(
        equipment_type=EquipmentType.RTD,
        equipment_id="RTD-3",
        terminal_role="A",
    )
    assert reference.equipment_id == "RTD-3"
    assert reference.terminal_role == "A"

def test_temperature_sensor_endpoint_reference_rejects_unknown_terminal_role():
    try:
        EndpointReference.terminal(
            equipment_type=EquipmentType.RTD,
            equipment_id="RTD-4",
            terminal_role="POSITIVE",
        )
    except ValueError as exc:
        assert "not valid" in str(exc)
    else:
        raise AssertionError("RTD endpoint reference accepted a non-RTD terminal role.")

