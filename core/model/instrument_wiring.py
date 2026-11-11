"""Canonical physical instrumentation wiring and signal identity records.

These records are independent of power-network Branch/Cable and of
MeasurementChannel. They contain engineering identity and connectivity only;
canvas geometry and Qt objects are deliberately excluded.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Optional


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value.strip()


def _optional_text(value: Optional[str], field: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string or None.")
    value = value.strip()
    return value or None


def _positive_int(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer.")
    return value


def _non_negative_finite(value: Optional[float], field: str) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric.") from exc
    if not isfinite(number) or number < 0:
        raise ValueError(f"{field} must be finite and non-negative.")
    return number


@dataclass(frozen=True, slots=True)
class WiringTerminalReference:
    """Stable reference to a physical terminal; designation is its visible label."""

    equipment_id: str
    terminal_id: str
    designation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "equipment_id", _required_text(self.equipment_id, "equipment_id"))
        object.__setattr__(self, "terminal_id", _required_text(self.terminal_id, "terminal_id"))
        object.__setattr__(self, "designation", _required_text(self.designation, "designation"))

    @property
    def identity(self) -> tuple[str, str]:
        return self.equipment_id, self.terminal_id


class ConductorRole(str, Enum):
    SIGNAL = "SIGNAL"
    RETURN = "RETURN"
    SUPPLY = "SUPPLY"
    PROTECTIVE_EARTH = "PROTECTIVE_EARTH"
    SCREEN = "SCREEN"
    DRAIN = "DRAIN"
    ARMOUR = "ARMOUR"
    SPARE = "SPARE"
    RESERVED = "RESERVED"
    COMMUNICATION = "COMMUNICATION"
    OTHER = "OTHER"


class SignalKind(str, Enum):
    ANALOG = "ANALOG"
    DIGITAL = "DIGITAL"
    COMMUNICATION = "COMMUNICATION"
    CURRENT = "CURRENT"
    VOLTAGE = "VOLTAGE"
    TEMPERATURE = "TEMPERATURE"
    CUSTOM = "CUSTOM"


class CarrierKind(str, Enum):
    CABLE_CORE = "CABLE_CORE"
    PANEL_WIRE = "PANEL_WIRE"
    FIBRE = "FIBRE"
    LOGICAL = "LOGICAL"


@dataclass(frozen=True, slots=True)
class CableAssembly:
    """Installed cable identity and declared construction metadata.

    This is an instrumentation/interconnection cable record, not the
    power-flow Cable branch in core.model.cable.
    """

    id: str
    tag: str
    service: str
    core_count: int
    cable_type: Optional[str] = None
    conductor_material: Optional[str] = None
    cross_section_mm2: Optional[float] = None
    rated_voltage_v: Optional[float] = None
    length_m: Optional[float] = None
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    revision: int = 1
    lifecycle_status: str = "PLANNED"

    def __post_init__(self) -> None:
        for field in ("id", "tag", "service", "lifecycle_status"):
            object.__setattr__(self, field, _required_text(getattr(self, field), field))
        object.__setattr__(self, "core_count", _positive_int(self.core_count, "core_count"))
        for field in ("cable_type", "conductor_material", "from_location", "to_location"):
            object.__setattr__(self, field, _optional_text(getattr(self, field), field))
        for field in ("cross_section_mm2", "rated_voltage_v", "length_m"):
            value = _non_negative_finite(getattr(self, field), field)
            if field == "cross_section_mm2" and value == 0:
                raise ValueError("cross_section_mm2 must be positive when supplied.")
            object.__setattr__(self, field, value)
        object.__setattr__(self, "revision", _positive_int(self.revision, "revision"))


@dataclass(frozen=True, slots=True)
class CableCore:
    """One identifiable conductor/core within a cable assembly."""

    id: str
    cable_id: str
    core_number: int
    role: ConductorRole
    terminal_path: tuple[WiringTerminalReference, ...] = ()
    colour: Optional[str] = None
    pair_id: Optional[str] = None
    core_tag: Optional[str] = None

    def __post_init__(self) -> None:
        for field in ("id", "cable_id"):
            object.__setattr__(self, field, _required_text(getattr(self, field), field))
        object.__setattr__(self, "core_number", _positive_int(self.core_number, "core_number"))
        if not isinstance(self.role, ConductorRole):
            raise TypeError("role must be a ConductorRole.")
        path = tuple(self.terminal_path)
        if any(not isinstance(item, WiringTerminalReference) for item in path):
            raise TypeError("terminal_path entries must be WiringTerminalReference values.")
        if len(path) == 1:
            raise ValueError("terminal_path must be empty or contain at least two terminals.")
        if len({item.identity for item in path}) != len(path):
            raise ValueError("terminal_path must not repeat a terminal.")
        object.__setattr__(self, "terminal_path", path)
        for field in ("colour", "pair_id", "core_tag"):
            object.__setattr__(self, field, _optional_text(getattr(self, field), field))


@dataclass(frozen=True, slots=True)
class PanelWire:
    """Individually identified panel wire, jumper or inter-terminal link."""

    id: str
    tag: str
    role: ConductorRole
    terminal_path: tuple[WiringTerminalReference, ...]
    cross_section_mm2: Optional[float] = None
    colour: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required_text(self.id, "id"))
        object.__setattr__(self, "tag", _required_text(self.tag, "tag"))
        if not isinstance(self.role, ConductorRole):
            raise TypeError("role must be a ConductorRole.")
        path = tuple(self.terminal_path)
        if len(path) < 2 or any(not isinstance(item, WiringTerminalReference) for item in path):
            raise ValueError("terminal_path must contain at least two terminal references.")
        if len({item.identity for item in path}) != len(path):
            raise ValueError("terminal_path must not repeat a terminal.")
        object.__setattr__(self, "terminal_path", path)
        area = _non_negative_finite(self.cross_section_mm2, "cross_section_mm2")
        if area == 0:
            raise ValueError("cross_section_mm2 must be positive when supplied.")
        object.__setattr__(self, "cross_section_mm2", area)
        object.__setattr__(self, "colour", _optional_text(self.colour, "colour"))


@dataclass(frozen=True, slots=True)
class SignalDefinition:
    """Engineering meaning and designation of a signal, independent of carrier."""

    id: str
    tag: str
    description: str
    kind: SignalKind
    unit: Optional[str] = None
    phase: Optional[str] = None

    def __post_init__(self) -> None:
        for field in ("id", "tag", "description"):
            object.__setattr__(self, field, _required_text(getattr(self, field), field))
        if not isinstance(self.kind, SignalKind):
            raise TypeError("kind must be a SignalKind.")
        for field in ("unit", "phase"):
            object.__setattr__(self, field, _optional_text(getattr(self, field), field))


@dataclass(frozen=True, slots=True)
class SignalCarrierBinding:
    """Binds a logical signal to a physical/logical carrier without owning either."""

    id: str
    signal_id: str
    carrier_kind: CarrierKind
    carrier_id: str
    direction: str = "BIDIRECTIONAL"

    def __post_init__(self) -> None:
        for field in ("id", "signal_id", "carrier_id"):
            object.__setattr__(self, field, _required_text(getattr(self, field), field))
        if not isinstance(self.carrier_kind, CarrierKind):
            raise TypeError("carrier_kind must be a CarrierKind.")
        direction = _required_text(self.direction, "direction").upper()
        if direction not in {"SOURCE_TO_SINK", "SINK_TO_SOURCE", "BIDIRECTIONAL"}:
            raise ValueError("direction must be SOURCE_TO_SINK, SINK_TO_SOURCE or BIDIRECTIONAL.")
        object.__setattr__(self, "direction", direction)


__all__ = [
    "WiringTerminalReference",
    "ConductorRole",
    "SignalKind",
    "CarrierKind",
    "CableAssembly",
    "CableCore",
    "PanelWire",
    "SignalDefinition",
    "SignalCarrierBinding",
]
