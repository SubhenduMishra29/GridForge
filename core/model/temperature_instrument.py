"""Canonical BTD/OTD/WTD service contracts, independent of sensor technology.

The service identity (bearing/oil/winding) is not inferred from an RTD or
thermocouple type. All terminal and interface declarations are engineering
inputs; this module does not invent wiring, ranges, thresholds or settings.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
import re
from typing import Optional

from .instrument_wiring import WiringTerminalReference


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value.strip()


def _optional(value: Optional[str], field: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string or None.")
    return value.strip() or None


def _number(value: Optional[float], field: str) -> Optional[float]:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric.") from exc
    if not isfinite(result):
        raise ValueError(f"{field} must be finite.")
    return result


class TemperatureService(str, Enum):
    BTD = "BTD"
    OTD = "OTD"
    WTD = "WTD"


class TemperatureSensorTechnology(str, Enum):
    RTD = "RTD"
    THERMOCOUPLE = "THERMOCOUPLE"
    OTHER = "OTHER"


class TemperatureInputMode(str, Enum):
    DIRECT_SENSOR = "DIRECT_SENSOR"
    TRANSMITTER = "TRANSMITTER"
    TEMPERATURE_MONITOR = "TEMPERATURE_MONITOR"
    THERMAL_IMAGE = "THERMAL_IMAGE"


class TemperatureConsumerKind(str, Enum):
    CONTROL = "CONTROL"
    PROTECTION = "PROTECTION"
    ALARM = "ALARM"
    TRIP = "TRIP"


@dataclass(frozen=True, slots=True)
class TemperatureTerminalMapping:
    """Manufacturer-declared sensor pin to interface input terminal mapping."""

    sensor_terminal: WiringTerminalReference
    interface_terminal: WiringTerminalReference
    polarity: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.sensor_terminal, WiringTerminalReference) or not isinstance(self.interface_terminal, WiringTerminalReference):
            raise TypeError("Temperature terminal mappings require canonical terminal references.")
        polarity = _optional(self.polarity, "polarity")
        if polarity is not None:
            polarity = polarity.upper()
            if polarity not in {"POSITIVE", "NEGATIVE"}:
                raise ValueError("Temperature terminal mapping polarity must be POSITIVE or NEGATIVE.")
        object.__setattr__(self, "polarity", polarity)


@dataclass(frozen=True, slots=True)
class TemperatureInstrument:
    """Service-specific temperature instrument identity and declared endpoints.

    sensor_equipment_id identifies the actual sensing element. The service
    identifies what is measured and where; technology/configuration identifies
    how it is measured. A WTD thermal-image arrangement is explicitly distinct
    from a direct winding RTD/thermocouple.
    """

    id: str
    tag: str
    service: TemperatureService
    asset_id: str
    location: str
    sensor_equipment_id: str
    sensor_technology: TemperatureSensorTechnology
    input_mode: TemperatureInputMode
    sensor_configuration: Optional[str] = None
    interface_equipment_id: Optional[str] = None
    measurement_channel_id: Optional[str] = None
    unit: Optional[str] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    sensor_terminals: tuple[WiringTerminalReference, ...] = ()
    receiver_terminals: tuple[WiringTerminalReference, ...] = ()
    sensor_input_mappings: tuple[TemperatureTerminalMapping, ...] = ()

    def __post_init__(self) -> None:
        for field in ("id", "tag", "asset_id", "location", "sensor_equipment_id"):
            object.__setattr__(self, field, _text(getattr(self, field), field))
        for field, enum_type in (
            ("service", TemperatureService),
            ("sensor_technology", TemperatureSensorTechnology),
            ("input_mode", TemperatureInputMode),
        ):
            if not isinstance(getattr(self, field), enum_type):
                raise TypeError(f"{field} must be a {enum_type.__name__}.")
        for field in ("sensor_configuration", "interface_equipment_id", "measurement_channel_id", "unit"):
            object.__setattr__(self, field, _optional(getattr(self, field), field))
        low = _number(self.range_min, "range_min")
        high = _number(self.range_max, "range_max")
        if (low is None) != (high is None) or (low is not None and high <= low):
            raise ValueError("range_min and range_max must both be supplied with range_max > range_min.")
        object.__setattr__(self, "range_min", low)
        object.__setattr__(self, "range_max", high)
        sensor_terms = tuple(self.sensor_terminals)
        receiver_terms = tuple(self.receiver_terminals)
        mappings = tuple(self.sensor_input_mappings)
        if any(not isinstance(item, TemperatureTerminalMapping) for item in mappings):
            raise TypeError("sensor_input_mappings must contain TemperatureTerminalMapping values.")
        if any(not isinstance(item, WiringTerminalReference) for item in sensor_terms + receiver_terms):
            raise TypeError("sensor_terminals and receiver_terminals must contain WiringTerminalReference values.")
        if len({item.identity for item in sensor_terms}) != len(sensor_terms):
            raise ValueError("sensor_terminals contains duplicate terminal identities.")
        if len({item.identity for item in receiver_terms}) != len(receiver_terms):
            raise ValueError("receiver_terminals contains duplicate terminal identities.")
        if any(item.equipment_id != self.sensor_equipment_id for item in sensor_terms):
            raise ValueError("Every sensor terminal must belong to sensor_equipment_id.")
        if self.input_mode is TemperatureInputMode.DIRECT_SENSOR and self.interface_equipment_id:
            raise ValueError("DIRECT_SENSOR must not declare an intermediary interface equipment.")
        if self.input_mode is not TemperatureInputMode.DIRECT_SENSOR and not self.interface_equipment_id:
            raise ValueError("A transmitter, temperature monitor or thermal-image mode requires interface_equipment_id.")
        if self.service is TemperatureService.WTD and self.input_mode is TemperatureInputMode.THERMAL_IMAGE:
            if self.sensor_technology is not TemperatureSensorTechnology.OTHER:
                raise ValueError("THERMAL_IMAGE WTD must identify its non-direct sensing technology as OTHER.")
        if self.input_mode is TemperatureInputMode.THERMAL_IMAGE and self.service is not TemperatureService.WTD:
            raise ValueError("THERMAL_IMAGE input mode is reserved for an explicitly declared WTD.")
        if self.sensor_technology is TemperatureSensorTechnology.RTD and self.sensor_configuration:
            match = re.search(r"\b([234])\s*[- ]?wire\b", self.sensor_configuration, re.IGNORECASE)
            if match and sensor_terms and len(sensor_terms) != int(match.group(1)):
                raise ValueError(
                    f"RTD {match.group(1)}-wire configuration requires exactly {match.group(1)} declared sensor terminals."
                )
        if self.sensor_technology is TemperatureSensorTechnology.THERMOCOUPLE and sensor_terms and len(sensor_terms) != 2:
            raise ValueError("Thermocouple sensor wiring must declare exactly two measurement terminals; screen/earth is separate.")
        if len({item.sensor_terminal.identity for item in mappings}) != len(mappings):
            raise ValueError("sensor_input_mappings contains duplicate sensor pins.")
        if len({item.interface_terminal.identity for item in mappings}) != len(mappings):
            raise ValueError("sensor_input_mappings contains duplicate interface input pins.")
        if any(item.sensor_terminal not in sensor_terms for item in mappings):
            raise ValueError("Every mapped sensor pin must be in sensor_terminals.")
        if self.sensor_technology is TemperatureSensorTechnology.THERMOCOUPLE and mappings:
            polarities = {item.polarity for item in mappings}
            if None in polarities or polarities != {"POSITIVE", "NEGATIVE"}:
                raise ValueError("Thermocouple mappings must explicitly identify positive and negative polarity.")
        elif any(item.polarity is not None for item in mappings):
            raise ValueError("Polarity labels are only valid for thermocouple terminal mappings.")
        object.__setattr__(self, "sensor_terminals", sensor_terms)
        object.__setattr__(self, "receiver_terminals", receiver_terms)
        object.__setattr__(self, "sensor_input_mappings", mappings)


@dataclass(frozen=True, slots=True)
class TemperatureInterfaceDevice:
    """Declared transmitter/temperature-monitor capability and terminal contract."""

    id: str
    tag: str
    equipment_kind: TemperatureInputMode
    supported_sensor_technologies: tuple[TemperatureSensorTechnology, ...]
    supported_sensor_configurations: tuple[str, ...]
    input_terminals: tuple[WiringTerminalReference, ...]
    output_terminals: tuple[WiringTerminalReference, ...]
    output_signal_kind: str
    output_unit: str
    output_range_min: Optional[float] = None
    output_range_max: Optional[float] = None
    measurement_channel_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "id"))
        object.__setattr__(self, "tag", _text(self.tag, "tag"))
        if self.equipment_kind not in {TemperatureInputMode.TRANSMITTER, TemperatureInputMode.TEMPERATURE_MONITOR, TemperatureInputMode.THERMAL_IMAGE}:
            raise ValueError("equipment_kind must describe an intermediary temperature interface.")
        technologies = tuple(self.supported_sensor_technologies)
        if not technologies or any(not isinstance(item, TemperatureSensorTechnology) for item in technologies):
            raise ValueError("supported_sensor_technologies must declare at least one valid technology.")
        configs = tuple(_text(item, "supported_sensor_configurations entry") for item in self.supported_sensor_configurations)
        inputs, outputs = tuple(self.input_terminals), tuple(self.output_terminals)
        if not inputs or not outputs:
            raise ValueError("Interface device must declare input and output terminal contracts.")
        if any(not isinstance(item, WiringTerminalReference) for item in inputs + outputs):
            raise TypeError("Interface terminals must be WiringTerminalReference values.")
        if any(item.equipment_id != self.id for item in inputs + outputs):
            raise ValueError("Interface terminals must belong to the interface equipment ID.")
        low, high = _number(self.output_range_min, "output_range_min"), _number(self.output_range_max, "output_range_max")
        if (low is None) != (high is None) or (low is not None and high <= low):
            raise ValueError("Output range bounds must both be supplied with maximum greater than minimum.")
        object.__setattr__(self, "supported_sensor_technologies", technologies)
        object.__setattr__(self, "supported_sensor_configurations", configs)
        object.__setattr__(self, "input_terminals", inputs)
        object.__setattr__(self, "output_terminals", outputs)
        object.__setattr__(self, "output_signal_kind", _text(self.output_signal_kind, "output_signal_kind"))
        object.__setattr__(self, "output_unit", _text(self.output_unit, "output_unit"))
        object.__setattr__(self, "output_range_min", low)
        object.__setattr__(self, "output_range_max", high)
        object.__setattr__(self, "measurement_channel_id", _optional(self.measurement_channel_id, "measurement_channel_id"))


@dataclass(frozen=True, slots=True)
class TemperatureAlarmTripBinding:
    """Explicit association; thresholds and reset policy are never defaulted."""

    id: str
    instrument_id: str
    signal_id: str
    consumer_kind: TemperatureConsumerKind
    consumer_id: str
    function_id: str
    stage: str
    threshold: Optional[float] = None
    unit: Optional[str] = None
    latching: Optional[bool] = None
    reset_policy: Optional[str] = None

    def __post_init__(self) -> None:
        for field in ("id", "instrument_id", "signal_id", "consumer_id", "function_id", "stage"):
            object.__setattr__(self, field, _text(getattr(self, field), field))
        if not isinstance(self.consumer_kind, TemperatureConsumerKind):
            raise TypeError("consumer_kind must be a TemperatureConsumerKind.")
        object.__setattr__(self, "threshold", _number(self.threshold, "threshold"))
        object.__setattr__(self, "unit", _optional(self.unit, "unit"))
        object.__setattr__(self, "reset_policy", _optional(self.reset_policy, "reset_policy"))
        if self.latching is not None and not isinstance(self.latching, bool):
            raise TypeError("latching must be bool or None.")


@dataclass(frozen=True, slots=True)
class TemperatureInstrumentInventory:
    """Immutable service-specific inventory; no implicit legacy classification."""

    instruments: tuple[TemperatureInstrument, ...] = ()
    interfaces: tuple[TemperatureInterfaceDevice, ...] = ()
    alarm_trip_bindings: tuple[TemperatureAlarmTripBinding, ...] = ()

    def __post_init__(self) -> None:
        groups = (
            ("instruments", self.instruments, TemperatureInstrument),
            ("interfaces", self.interfaces, TemperatureInterfaceDevice),
            ("alarm_trip_bindings", self.alarm_trip_bindings, TemperatureAlarmTripBinding),
        )
        all_ids: list[str] = []
        for name, values, expected in groups:
            values = tuple(values)
            if any(not isinstance(item, expected) for item in values):
                raise TypeError(f"{name} must contain only {expected.__name__} records.")
            ids = [item.id for item in values]
            if len(ids) != len(set(ids)):
                raise ValueError(f"{name} contains duplicate stable IDs.")
            all_ids.extend(ids)
            object.__setattr__(self, name, values)
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("Temperature instrument records must have globally unique IDs.")
        instruments = {item.id: item for item in self.instruments}
        interfaces = {item.id: item for item in self.interfaces}
        tags = [item.tag for item in self.instruments]
        if len(tags) != len(set(tags)):
            raise ValueError("Temperature instrument tags must be unique within this inventory.")
        interface_tags = [item.tag for item in self.interfaces]
        if len(interface_tags) != len(set(interface_tags)):
            raise ValueError("Temperature interface tags must be unique within this inventory.")
        for instrument in self.instruments:
            if instrument.interface_equipment_id:
                interface = interfaces.get(instrument.interface_equipment_id)
                if interface is None:
                    raise ValueError(f"Temperature instrument '{instrument.id}' references a missing interface device.")
                if interface.equipment_kind is not instrument.input_mode:
                    raise ValueError(f"Temperature instrument '{instrument.id}' input mode does not match its interface.")
                if instrument.sensor_technology not in interface.supported_sensor_technologies:
                    raise ValueError(f"Temperature interface '{interface.id}' does not support the declared sensor technology.")
                if instrument.sensor_configuration and interface.supported_sensor_configurations and instrument.sensor_configuration not in interface.supported_sensor_configurations:
                    raise ValueError(f"Temperature interface '{interface.id}' does not support the declared sensor configuration.")
        for binding in self.alarm_trip_bindings:
            if binding.instrument_id not in instruments:
                raise ValueError(f"Temperature alarm/trip binding '{binding.id}' references a missing instrument.")


__all__ = [
    "TemperatureService", "TemperatureSensorTechnology", "TemperatureInputMode",
    "TemperatureConsumerKind", "TemperatureInstrument", "TemperatureInterfaceDevice",
    "TemperatureTerminalMapping", "TemperatureAlarmTripBinding", "TemperatureInstrumentInventory",
]
