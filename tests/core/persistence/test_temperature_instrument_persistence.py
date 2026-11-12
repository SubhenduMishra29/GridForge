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
