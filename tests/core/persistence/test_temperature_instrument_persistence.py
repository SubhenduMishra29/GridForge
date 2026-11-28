from core.model import TemperatureInstrumentInventory
from core.persistence.temperature_instrument_serializer import (
    TEMPERATURE_INSTRUMENT_SCHEMA_VERSION,
    TemperatureInstrumentSerializationError,
    deserialize_temperature_instruments,
    serialize_temperature_instruments,
)


def test_empty_temperature_inventory_round_trip():
    value = TemperatureInstrumentInventory()
    payload = serialize_temperature_instruments(value)
    assert payload["schema"] == TEMPERATURE_INSTRUMENT_SCHEMA_VERSION
    assert deserialize_temperature_instruments(payload) == value


def test_legacy_absence_does_not_infer_temperature_service():
    assert deserialize_temperature_instruments(None) == TemperatureInstrumentInventory()


def test_unknown_schema_is_rejected():
    try:
        deserialize_temperature_instruments({
            "schema": 2, "instruments": [], "interfaces": [], "alarm_trip_bindings": [],
        })
    except TemperatureInstrumentSerializationError:
        pass
    else:
        raise AssertionError("Unknown schema must fail closed.")


def test_unknown_top_level_fields_are_rejected():
    try:
        deserialize_temperature_instruments({
            "schema": 1, "instruments": [], "interfaces": [],
            "alarm_trip_bindings": [], "legacy_guess": True,
        })
    except TemperatureInstrumentSerializationError:
        pass
    else:
        raise AssertionError("Non-canonical payload must fail closed.")


def test_temperature_calibration_evidence_round_trip_and_legacy_payload_compatibility():
    from core.model import (
        TemperatureCalibrationPoint, TemperatureCalibrationRecord,
        TemperatureInstrument, TemperatureService, TemperatureSensorTechnology,
        TemperatureInputMode,
    )

    instrument = TemperatureInstrument(
        id="temp-persist-cal", tag="BTD-PERSIST-CAL", service=TemperatureService.BTD,
        asset_id="motor-persist", location="DE bearing", sensor_equipment_id="rtd-persist",
        sensor_technology=TemperatureSensorTechnology.RTD,
        input_mode=TemperatureInputMode.DIRECT_SENSOR,
        unit="degC", calibration_id="cal-persist",
    )
    calibration = TemperatureCalibrationRecord(
        id="cal-persist", instrument_id=instrument.id, revision="REV-2",
        input_unit="ohm", output_unit="degC",
        points=(TemperatureCalibrationPoint(100.0, 0.0), TemperatureCalibrationPoint(138.5, 100.0)),
        calibration_standard="LAB-CERT-2026-004",
        calibrated_at="2026-10-02T12:30:00+05:30",
        expanded_uncertainty=0.2,
    )
    inventory = TemperatureInstrumentInventory(
        instruments=(instrument,), calibrations=(calibration,),
    )
    payload = serialize_temperature_instruments(inventory)
    assert payload["calibrations"][0]["id"] == calibration.id
    assert deserialize_temperature_instruments(payload) == inventory

    legacy = serialize_temperature_instruments(TemperatureInstrumentInventory())
    legacy.pop("calibrations")
    assert deserialize_temperature_instruments(legacy) == TemperatureInstrumentInventory()
