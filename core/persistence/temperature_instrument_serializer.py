"""Strict schema-1 codec for service-specific temperature instrument records."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.model.instrument_wiring import WiringTerminalReference
from core.model.temperature_instrument import (
    TemperatureAlarmTripBinding, TemperatureConsumerKind, TemperatureInputMode,
    TemperatureInstrument, TemperatureInstrumentInventory, TemperatureInterfaceDevice,
    TemperatureSensorTechnology, TemperatureService, TemperatureTerminalMapping,
)

TEMPERATURE_INSTRUMENT_SCHEMA_VERSION = 1


class TemperatureInstrumentSerializationError(ValueError):
    """Raised when temperature instrument data is not losslessly canonical."""


def _terminal_to_dict(item: WiringTerminalReference) -> dict[str, str]:
    return {"equipment_id": item.equipment_id, "terminal_role": item.terminal_role, "designation": item.designation}


def _terminal_from_dict(data: Mapping[str, Any]) -> WiringTerminalReference:
    if not isinstance(data, Mapping) or set(data) != {"equipment_id", "terminal_role", "designation"}:
        raise TemperatureInstrumentSerializationError("Malformed temperature instrument terminal reference.")
    return WiringTerminalReference(**dict(data))


def _record(data: Any, required: set[str], optional: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise TemperatureInstrumentSerializationError(f"{label} must be an object.")
    missing, unknown = required - set(data), set(data) - required - optional
    if missing or unknown:
        raise TemperatureInstrumentSerializationError(
            f"{label} fields are not canonical; missing={sorted(missing)}, unknown={sorted(unknown)}."
        )
    return data


def serialize_temperature_instruments(inventory: TemperatureInstrumentInventory) -> dict[str, Any]:
    if not isinstance(inventory, TemperatureInstrumentInventory):
        raise TypeError("inventory must be a TemperatureInstrumentInventory.")
    return {
        "schema": TEMPERATURE_INSTRUMENT_SCHEMA_VERSION,
        "instruments": [{
            "id": x.id, "tag": x.tag, "service": x.service.value, "asset_id": x.asset_id,
            "location": x.location, "sensor_equipment_id": x.sensor_equipment_id,
            "sensor_technology": x.sensor_technology.value, "input_mode": x.input_mode.value,
            "sensor_configuration": x.sensor_configuration, "interface_equipment_id": x.interface_equipment_id,
            "measurement_channel_id": x.measurement_channel_id, "unit": x.unit,
            "range_min": x.range_min, "range_max": x.range_max,
            "sensor_terminals": [_terminal_to_dict(t) for t in x.sensor_terminals],
            "receiver_terminals": [_terminal_to_dict(t) for t in x.receiver_terminals],
            "sensor_input_mappings": [{
                "sensor_terminal": _terminal_to_dict(m.sensor_terminal),
                "interface_terminal": _terminal_to_dict(m.interface_terminal),
                "polarity": m.polarity,
            } for m in x.sensor_input_mappings],
        } for x in inventory.instruments],
        "interfaces": [{
            "id": x.id, "tag": x.tag, "equipment_kind": x.equipment_kind.value,
            "supported_sensor_technologies": [v.value for v in x.supported_sensor_technologies],
            "supported_sensor_configurations": list(x.supported_sensor_configurations),
            "input_terminals": [_terminal_to_dict(t) for t in x.input_terminals],
            "output_terminals": [_terminal_to_dict(t) for t in x.output_terminals],
            "output_signal_kind": x.output_signal_kind, "output_unit": x.output_unit,
            "output_range_min": x.output_range_min, "output_range_max": x.output_range_max,
            "measurement_channel_id": x.measurement_channel_id,
        } for x in inventory.interfaces],
        "alarm_trip_bindings": [{
            "id": x.id, "instrument_id": x.instrument_id, "signal_id": x.signal_id,
            "consumer_kind": x.consumer_kind.value, "consumer_id": x.consumer_id,
            "function_id": x.function_id, "stage": x.stage, "threshold": x.threshold,
            "unit": x.unit, "latching": x.latching, "reset_policy": x.reset_policy,
        } for x in inventory.alarm_trip_bindings],
    }


def deserialize_temperature_instruments(data: Mapping[str, Any] | None) -> TemperatureInstrumentInventory:
    if data is None:
        return TemperatureInstrumentInventory()
    expected = {"schema", "instruments", "interfaces", "alarm_trip_bindings"}
    if not isinstance(data, Mapping) or set(data) != expected:
        raise TemperatureInstrumentSerializationError("Temperature instrument payload has non-canonical top-level fields.")
    if isinstance(data.get("schema"), bool) or data.get("schema") != TEMPERATURE_INSTRUMENT_SCHEMA_VERSION:
        raise TemperatureInstrumentSerializationError(f"Unsupported temperature instrument schema {data.get('schema')!r}.")
    for key in ("instruments", "interfaces", "alarm_trip_bindings"):
        if not isinstance(data[key], list):
            raise TemperatureInstrumentSerializationError(f"{key} must be an array.")
    try:
        instruments = []
        for raw in data["instruments"]:
            x = _record(raw, {"id", "tag", "service", "asset_id", "location", "sensor_equipment_id", "sensor_technology", "input_mode"},
                        {"sensor_configuration", "interface_equipment_id", "measurement_channel_id", "unit", "range_min", "range_max", "sensor_terminals", "receiver_terminals", "sensor_input_mappings"}, "TemperatureInstrument")
            instruments.append(TemperatureInstrument(
                id=x["id"], tag=x["tag"], service=TemperatureService(x["service"]), asset_id=x["asset_id"],
                location=x["location"], sensor_equipment_id=x["sensor_equipment_id"],
                sensor_technology=TemperatureSensorTechnology(x["sensor_technology"]), input_mode=TemperatureInputMode(x["input_mode"]),
                sensor_configuration=x.get("sensor_configuration"), interface_equipment_id=x.get("interface_equipment_id"),
                measurement_channel_id=x.get("measurement_channel_id"), unit=x.get("unit"), range_min=x.get("range_min"),
                range_max=x.get("range_max"), sensor_terminals=tuple(_terminal_from_dict(t) for t in x.get("sensor_terminals", [])),
                receiver_terminals=tuple(_terminal_from_dict(t) for t in x.get("receiver_terminals", [])),
                sensor_input_mappings=tuple(TemperatureTerminalMapping(
                    sensor_terminal=_terminal_from_dict(m["sensor_terminal"]),
                    interface_terminal=_terminal_from_dict(m["interface_terminal"]),
                    polarity=m.get("polarity"),
                ) for m in x.get("sensor_input_mappings", [])),
            ))
        interfaces = []
        for x in data["interfaces"]:
            x = _record(x, {"id", "tag", "equipment_kind", "supported_sensor_technologies", "supported_sensor_configurations", "input_terminals", "output_terminals", "output_signal_kind", "output_unit"},
                        {"output_range_min", "output_range_max", "measurement_channel_id"}, "TemperatureInterfaceDevice")
            interfaces.append(TemperatureInterfaceDevice(
                id=x["id"], tag=x["tag"], equipment_kind=TemperatureInputMode(x["equipment_kind"]),
                supported_sensor_technologies=tuple(TemperatureSensorTechnology(v) for v in x["supported_sensor_technologies"]),
                supported_sensor_configurations=tuple(x["supported_sensor_configurations"]),
                input_terminals=tuple(_terminal_from_dict(t) for t in x["input_terminals"]),
                output_terminals=tuple(_terminal_from_dict(t) for t in x["output_terminals"]),
                output_signal_kind=x["output_signal_kind"], output_unit=x["output_unit"],
                output_range_min=x.get("output_range_min"), output_range_max=x.get("output_range_max"),
                measurement_channel_id=x.get("measurement_channel_id"),
            ))
        bindings = []
        for x in data["alarm_trip_bindings"]:
            x = _record(x, {"id", "instrument_id", "signal_id", "consumer_kind", "consumer_id", "function_id", "stage"},
                        {"threshold", "unit", "latching", "reset_policy"}, "TemperatureAlarmTripBinding")
            bindings.append(TemperatureAlarmTripBinding(
                id=x["id"], instrument_id=x["instrument_id"], signal_id=x["signal_id"],
                consumer_kind=TemperatureConsumerKind(x["consumer_kind"]), consumer_id=x["consumer_id"],
                function_id=x["function_id"], stage=x["stage"], threshold=x.get("threshold"),
                unit=x.get("unit"), latching=x.get("latching"), reset_policy=x.get("reset_policy"),
            ))
        return TemperatureInstrumentInventory(tuple(instruments), tuple(interfaces), tuple(bindings))
    except (KeyError, TypeError, ValueError) as exc:
        raise TemperatureInstrumentSerializationError(f"Invalid temperature instrument inventory: {exc}") from exc


__all__ = [
    "TEMPERATURE_INSTRUMENT_SCHEMA_VERSION", "TemperatureInstrumentSerializationError",
    "serialize_temperature_instruments", "deserialize_temperature_instruments",
]
