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
    terminal_role: str
    designation: str
    terminal_point_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "equipment_id", _required_text(self.equipment_id, "equipment_id"))
        object.__setattr__(self, "terminal_role", _required_text(self.terminal_role, "terminal_role"))
        object.__setattr__(self, "designation", _required_text(self.designation, "designation"))
        object.__setattr__(self, "terminal_point_id", _optional_text(self.terminal_point_id, "terminal_point_id"))

    @property
    def identity(self) -> tuple[str, str, Optional[str]]:
        return self.equipment_id, self.terminal_role, self.terminal_point_id


class WiringConductorRole(str, Enum):
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


class TerminalAccessoryKind(str, Enum):
    FIXED_LINK = "FIXED_LINK"
    TEST_DISCONNECT = "TEST_DISCONNECT"
    SHORTING_LINK = "SHORTING_LINK"
    EARTH_LINK = "EARTH_LINK"
    FUSE_LINK = "FUSE_LINK"
    ISOLATING_LINK = "ISOLATING_LINK"
    OTHER = "OTHER"


class TerminalAccessoryState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    REMOVED = "REMOVED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class TerminalBlock:
    """Stable panel/junction terminal-block identity, independent of its tag."""

    id: str
    tag: str
    panel_id: str
    location: str
    terminal_count: int
    terminal_type: Optional[str] = None
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    revision: int = 1
    lifecycle_status: str = "PLANNED"

    def __post_init__(self) -> None:
        for name in ("id", "tag", "panel_id", "location", "lifecycle_status"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        object.__setattr__(self, "terminal_count", _positive_int(self.terminal_count, "terminal_count"))
        object.__setattr__(self, "revision", _positive_int(self.revision, "revision"))
        for name in ("terminal_type", "manufacturer", "part_number"):
            object.__setattr__(self, name, _optional_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class TerminalPoint:
    """One stable terminal position within a terminal block."""

    id: str
    terminal_block_id: str
    terminal_number: str
    designation: str
    function: str = "FEED_THROUGH"
    side: Optional[str] = None
    manufacturer_designation: Optional[str] = None
    lifecycle_status: str = "PLANNED"

    def __post_init__(self) -> None:
        for name in ("id", "terminal_block_id", "terminal_number", "designation", "function", "lifecycle_status"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        object.__setattr__(self, "function", self.function.upper())
        for name in ("side", "manufacturer_designation"):
            object.__setattr__(self, name, _optional_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class TerminalAccessory:
    """Explicit terminal accessory and its conductive bridge state."""

    id: str
    tag: str
    terminal_block_id: str
    kind: TerminalAccessoryKind
    state: TerminalAccessoryState
    terminal_point_ids: tuple[str, ...]
    conductive_pairs: tuple[tuple[str, str], ...] = ()
    rated_voltage_v: Optional[float] = None
    rated_current_a: Optional[float] = None
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None

    def __post_init__(self) -> None:
        for name in ("id", "tag", "terminal_block_id"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        if not isinstance(self.kind, TerminalAccessoryKind):
            raise TypeError("kind must be a TerminalAccessoryKind.")
        if not isinstance(self.state, TerminalAccessoryState):
            raise TypeError("state must be a TerminalAccessoryState.")
        point_ids = tuple(_required_text(value, "terminal_point_id") for value in self.terminal_point_ids)
        if not point_ids or len(point_ids) != len(set(point_ids)):
            raise ValueError("terminal_point_ids must be non-empty and unique.")
        object.__setattr__(self, "terminal_point_ids", point_ids)
        pairs = []
        for pair in self.conductive_pairs:
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise TypeError("conductive_pairs must contain two-terminal pairs.")
            first, second = (_required_text(value, "conductive_pair terminal ID") for value in pair)
            if first == second or first not in point_ids or second not in point_ids:
                raise ValueError("conductive pairs must connect two distinct declared accessory terminals.")
            canonical = tuple(sorted((first, second)))
            if canonical in pairs:
                raise ValueError("conductive_pairs cannot contain duplicate terminal pairs.")
            pairs.append(canonical)
        object.__setattr__(self, "conductive_pairs", tuple(pairs))
        for name in ("rated_voltage_v", "rated_current_a"):
            object.__setattr__(self, name, _non_negative_finite(getattr(self, name), name))
        for name in ("manufacturer", "part_number"):
            object.__setattr__(self, name, _optional_text(getattr(self, name), name))


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
    role: WiringConductorRole
    terminal_path: tuple[WiringTerminalReference, ...] = ()
    colour: Optional[str] = None
    pair_id: Optional[str] = None
    core_tag: Optional[str] = None

    def __post_init__(self) -> None:
        for field in ("id", "cable_id"):
            object.__setattr__(self, field, _required_text(getattr(self, field), field))
        object.__setattr__(self, "core_number", _positive_int(self.core_number, "core_number"))
        if not isinstance(self.role, WiringConductorRole):
            raise TypeError("role must be a WiringConductorRole.")
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
    role: WiringConductorRole
    terminal_path: tuple[WiringTerminalReference, ...]
    cross_section_mm2: Optional[float] = None
    colour: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required_text(self.id, "id"))
        object.__setattr__(self, "tag", _required_text(self.tag, "tag"))
        if not isinstance(self.role, WiringConductorRole):
            raise TypeError("role must be a WiringConductorRole.")
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
    """Binds a signal carrier to its explicit source MeasurementChannel.

    source_channel_id remains optional only for lossless decoding of legacy
    schema-2/schema-3 records. Application resolution fails closed until a
    physical carrier has an explicit source-channel owner.
    """

    id: str
    signal_id: str
    carrier_kind: CarrierKind
    carrier_id: str
    direction: str = "BIDIRECTIONAL"
    source_channel_id: Optional[str] = None

    def __post_init__(self) -> None:
        for field in ("id", "signal_id", "carrier_id"):
            object.__setattr__(self, field, _required_text(getattr(self, field), field))
        object.__setattr__(
            self, "source_channel_id",
            _optional_text(self.source_channel_id, "source_channel_id"),
        )
        if not isinstance(self.carrier_kind, CarrierKind):
            raise TypeError("carrier_kind must be a CarrierKind.")
        direction = _required_text(self.direction, "direction").upper()
        if direction not in {"SOURCE_TO_SINK", "SINK_TO_SOURCE", "BIDIRECTIONAL"}:
            raise ValueError("direction must be SOURCE_TO_SINK, SINK_TO_SOURCE or BIDIRECTIONAL.")
        object.__setattr__(self, "direction", direction)



class SignalEndpointKind(str, Enum):
    """Explicit logical endpoint category for a signal designation."""

    MEASUREMENT_CHANNEL = "MEASUREMENT_CHANNEL"
    CONTROL_INPUT = "CONTROL_INPUT"
    PROTECTION_INPUT = "PROTECTION_INPUT"


@dataclass(frozen=True, slots=True)
class SignalEndpointReference:
    """Stable reference to an existing logical signal endpoint.

    MEASUREMENT_CHANNEL: endpoint_id is the MeasurementChannel ID.
    CONTROL_INPUT: owner_id is Control ID, endpoint_id is component ID,
    and port is the input name.
    PROTECTION_INPUT: owner_id is protection element ID, endpoint_id is
    ProtectionMeasurementBinding ID, and port is the relay-input ID.
    CONTROL_INPUT/PROTECTION_INPUT physical_terminal identifies the exact
    physical sink terminal reached by the carrier route.
    """

    kind: SignalEndpointKind
    endpoint_id: str
    owner_id: Optional[str] = None
    port: Optional[str] = None
    physical_terminal: Optional[WiringTerminalReference] = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, SignalEndpointKind):
            raise TypeError("kind must be a SignalEndpointKind.")
        object.__setattr__(self, "endpoint_id", _required_text(self.endpoint_id, "endpoint_id"))
        object.__setattr__(self, "owner_id", _optional_text(self.owner_id, "owner_id"))
        object.__setattr__(self, "port", _optional_text(self.port, "port"))
        if self.physical_terminal is not None and not isinstance(self.physical_terminal, WiringTerminalReference):
            raise TypeError("physical_terminal must be a WiringTerminalReference or None.")
        if self.kind is SignalEndpointKind.MEASUREMENT_CHANNEL:
            if self.owner_id is not None or self.port is not None or self.physical_terminal is not None:
                raise ValueError("MeasurementChannel endpoint references use endpoint_id only.")
        elif self.kind is SignalEndpointKind.CONTROL_INPUT:
            if self.owner_id is None or self.port is None:
                raise ValueError("Control input references require control owner_id and input port.")
        elif self.kind is SignalEndpointKind.PROTECTION_INPUT:
            if self.owner_id is None or self.port is None:
                raise ValueError("Protection input references require protection element owner_id and relay-input port.")

    @property
    def identity(self) -> tuple[str, str, Optional[str], Optional[str]]:
        """Return the exact endpoint reference identity, including binding ID."""
        return self.kind.value, self.endpoint_id, self.owner_id, self.port

    @property
    def logical_identity(self) -> tuple[str, ...]:
        """Return the consumer endpoint identity, independent of binding member ID."""
        if self.kind is SignalEndpointKind.MEASUREMENT_CHANNEL:
            return self.kind.value, self.endpoint_id
        if self.kind is SignalEndpointKind.CONTROL_INPUT:
            return self.kind.value, str(self.owner_id), self.endpoint_id, str(self.port)
        return self.kind.value, str(self.owner_id), str(self.port)


@dataclass(frozen=True, slots=True)
class SignalEndpointBinding:
    """Binds one signal designation to one explicit logical endpoint."""

    id: str
    signal_id: str
    endpoint: SignalEndpointReference
    direction: str = "SOURCE_TO_SINK"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required_text(self.id, "id"))
        object.__setattr__(self, "signal_id", _required_text(self.signal_id, "signal_id"))
        if not isinstance(self.endpoint, SignalEndpointReference):
            raise TypeError("endpoint must be a SignalEndpointReference.")
        direction = _required_text(self.direction, "direction").upper()
        if direction not in {"SOURCE_TO_SINK", "SINK_TO_SOURCE", "BIDIRECTIONAL"}:
            raise ValueError("direction must be SOURCE_TO_SINK, SINK_TO_SOURCE or BIDIRECTIONAL.")
        object.__setattr__(self, "direction", direction)


@dataclass(frozen=True, slots=True)
class WiringTagSeries:
    """Explicit project-defined sequential tag series for one record category."""

    record_kind: str
    prefix: str
    separator: str = ""
    minimum_digits: int = 3
    next_number: int = 1

    def __post_init__(self) -> None:
        kind = _required_text(self.record_kind, "record_kind").upper()
        prefix = _required_text(self.prefix, "prefix")
        if not isinstance(self.separator, str):
            raise TypeError("separator must be a string.")
        if self.separator != self.separator.strip():
            raise ValueError("separator must not contain leading or trailing whitespace.")
        object.__setattr__(self, "record_kind", kind)
        object.__setattr__(self, "prefix", prefix)
        object.__setattr__(self, "minimum_digits", _positive_int(self.minimum_digits, "minimum_digits"))
        object.__setattr__(self, "next_number", _positive_int(self.next_number, "next_number"))

    def format(self, number: int) -> str:
        number = _positive_int(number, "number")
        return self.prefix + self.separator + str(number).zfill(self.minimum_digits)


@dataclass(frozen=True, slots=True)
class WiringTagPolicy:
    """Project-owned tag series; no standard syntax or prefix is assumed."""

    series: tuple[WiringTagSeries, ...] = ()

    def __post_init__(self) -> None:
        values = tuple(self.series)
        if any(not isinstance(item, WiringTagSeries) for item in values):
            raise TypeError("series must contain only WiringTagSeries values.")
        kinds = [item.record_kind for item in values]
        if len(kinds) != len(set(kinds)):
            raise ValueError("Tag policy contains duplicate record_kind series.")
        object.__setattr__(self, "series", values)

    def allocate(
        self, record_kind: str, *, used_tags: tuple[str, ...] | list[str] | set[str] = ()
    ) -> tuple[str, "WiringTagPolicy"]:
        """Return the next unused tag and a new policy with an advanced counter."""
        kind = _required_text(record_kind, "record_kind").upper()
        matches = [item for item in self.series if item.record_kind == kind]
        if len(matches) != 1:
            raise ValueError(f"No unique tag series is configured for {kind!r}.")
        used_values = tuple(used_tags)
        if any(not isinstance(item, str) for item in used_values):
            raise TypeError("used_tags must contain strings.")
        used = set(used_values)
        current = matches[0]
        number = current.next_number
        tag = current.format(number)
        while tag in used:
            number += 1
            tag = current.format(number)
        advanced = WiringTagSeries(
            record_kind=current.record_kind,
            prefix=current.prefix,
            separator=current.separator,
            minimum_digits=current.minimum_digits,
            next_number=number + 1,
        )
        updated = tuple(advanced if item is current else item for item in self.series)
        return tag, WiringTagPolicy(updated)


@dataclass(frozen=True, slots=True)
class InstrumentationWiringInventory:
    """Validated project-level snapshot of instrumentation wiring records.

    This aggregate enforces cross-record identity and ownership invariants.
    Persistence and controlled mutation remain Application responsibilities.
    """

    cables: tuple[CableAssembly, ...] = ()
    cores: tuple[CableCore, ...] = ()
    panel_wires: tuple[PanelWire, ...] = ()
    signals: tuple[SignalDefinition, ...] = ()
    signal_bindings: tuple[SignalCarrierBinding, ...] = ()
    tag_policy: WiringTagPolicy = WiringTagPolicy()
    endpoint_bindings: tuple[SignalEndpointBinding, ...] = ()
    terminal_blocks: tuple[TerminalBlock, ...] = ()
    terminal_points: tuple[TerminalPoint, ...] = ()
    terminal_accessories: tuple[TerminalAccessory, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.tag_policy, WiringTagPolicy):
            raise TypeError("tag_policy must be a WiringTagPolicy.")
        collections = (
            ("cables", self.cables, CableAssembly),
            ("cores", self.cores, CableCore),
            ("panel_wires", self.panel_wires, PanelWire),
            ("signals", self.signals, SignalDefinition),
            ("signal_bindings", self.signal_bindings, SignalCarrierBinding),
            ("endpoint_bindings", self.endpoint_bindings, SignalEndpointBinding),
            ("terminal_blocks", self.terminal_blocks, TerminalBlock),
            ("terminal_points", self.terminal_points, TerminalPoint),
            ("terminal_accessories", self.terminal_accessories, TerminalAccessory),
        )
        for name, values, expected_type in collections:
            values = tuple(values)
            if any(not isinstance(value, expected_type) for value in values):
                raise TypeError(f"{name} must contain only {expected_type.__name__} records.")
            object.__setattr__(self, name, values)
            ids = [value.id for value in values]
            if len(ids) != len(set(ids)):
                raise ValueError(f"{name} contains duplicate stable IDs.")

        all_ids = [
            record.id
            for _, values, _ in collections
            for record in values
        ]
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("Instrumentation wiring records must have globally unique stable IDs.")

        self._validate_unique_tags(self.cables, "cable")
        self._validate_unique_tags(self.panel_wires, "panel wire")
        self._validate_unique_tags(self.signals, "signal")
        self._validate_unique_tags(self.terminal_blocks, "terminal block")
        self._validate_unique_tags(self.terminal_accessories, "terminal accessory")
        core_tags = [item.core_tag for item in self.cores if item.core_tag is not None]
        if len(core_tags) != len(set(core_tags)):
            raise ValueError("Cable cores contain duplicate core tags.")

        cable_by_id = {item.id: item for item in self.cables}
        core_numbers: set[tuple[str, int]] = set()
        for core in self.cores:
            cable = cable_by_id.get(core.cable_id)
            if cable is None:
                raise ValueError(f"Cable core '{core.id}' references missing cable '{core.cable_id}'.")
            if core.core_number > cable.core_count:
                raise ValueError(f"Cable core '{core.id}' exceeds cable '{cable.id}' core_count.")
            key = (core.cable_id, core.core_number)
            if key in core_numbers:
                raise ValueError(f"Cable '{core.cable_id}' has duplicate core number {core.core_number}.")
            core_numbers.add(key)

        signal_ids = {item.id for item in self.signals}
        carrier_ids = (
            {item.id for item in self.cores}
            | {item.id for item in self.panel_wires}
        )
        for binding in self.signal_bindings:
            if binding.signal_id not in signal_ids:
                raise ValueError(f"Signal binding '{binding.id}' references missing signal '{binding.signal_id}'.")
            if binding.carrier_kind is CarrierKind.CABLE_CORE and binding.carrier_id not in {item.id for item in self.cores}:
                raise ValueError(f"Signal binding '{binding.id}' references missing cable core '{binding.carrier_id}'.")
            if binding.carrier_kind is CarrierKind.PANEL_WIRE and binding.carrier_id not in {item.id for item in self.panel_wires}:
                raise ValueError(f"Signal binding '{binding.id}' references missing panel wire '{binding.carrier_id}'.")
            if binding.carrier_kind in {CarrierKind.FIBRE, CarrierKind.LOGICAL} and binding.carrier_id in carrier_ids:
                raise ValueError(
                    f"Signal binding '{binding.id}' reuses a physical core/wire ID "
                    "for a different carrier kind."
                )

        terminal_blocks_by_id = {item.id: item for item in self.terminal_blocks}
        terminal_points_by_id = {item.id: item for item in self.terminal_points}
        terminal_numbers: set[tuple[str, str]] = set()
        terminal_designations: set[tuple[str, str]] = set()
        for point in self.terminal_points:
            block = terminal_blocks_by_id.get(point.terminal_block_id)
            if block is None:
                raise ValueError(f"Terminal point '{point.id}' references missing terminal block '{point.terminal_block_id}'.")
            if sum(1 for item in self.terminal_points if item.terminal_block_id == block.id) > block.terminal_count:
                raise ValueError(f"Terminal block '{block.id}' has more terminal points than its declared terminal_count.")
            number_key = (point.terminal_block_id, point.terminal_number)
            designation_key = (point.terminal_block_id, point.designation)
            if number_key in terminal_numbers:
                raise ValueError(f"Terminal block '{block.id}' has duplicate terminal number {point.terminal_number!r}.")
            if designation_key in terminal_designations:
                raise ValueError(f"Terminal block '{block.id}' has duplicate terminal designation {point.designation!r}.")
            terminal_numbers.add(number_key)
            terminal_designations.add(designation_key)

        for reference in (
            [ref for core in self.cores for ref in core.terminal_path]
            + [ref for wire in self.panel_wires for ref in wire.terminal_path]
            + [binding.endpoint.physical_terminal for binding in self.endpoint_bindings if binding.endpoint.physical_terminal is not None]
        ):
            if reference.terminal_point_id is None:
                if reference.equipment_id in terminal_blocks_by_id:
                    raise ValueError(
                        f"Terminal reference to terminal block '{reference.equipment_id}' must include terminal_point_id."
                    )
                continue
            point = terminal_points_by_id.get(reference.terminal_point_id)
            if point is None:
                raise ValueError(f"Terminal reference points to missing terminal point '{reference.terminal_point_id}'.")
            if (
                point.terminal_block_id != reference.equipment_id
                or point.terminal_number != reference.terminal_role
                or point.designation != reference.designation
            ):
                raise ValueError(
                    f"Terminal reference '{reference.terminal_point_id}' does not match its canonical terminal point record."
                )

        for accessory in self.terminal_accessories:
            if accessory.terminal_block_id not in terminal_blocks_by_id:
                raise ValueError(
                    f"Terminal accessory '{accessory.id}' references missing terminal block '{accessory.terminal_block_id}'."
                )
            if any(point_id not in terminal_points_by_id for point_id in accessory.terminal_point_ids):
                raise ValueError(f"Terminal accessory '{accessory.id}' references a missing terminal point.")
            if any(terminal_points_by_id[point_id].terminal_block_id != accessory.terminal_block_id for point_id in accessory.terminal_point_ids):
                raise ValueError(f"Terminal accessory '{accessory.id}' references a terminal point from another block.")
            if accessory.state is TerminalAccessoryState.CLOSED and accessory.kind is not TerminalAccessoryKind.OTHER and not accessory.conductive_pairs:
                raise ValueError(f"Closed terminal accessory '{accessory.id}' requires explicit conductive_pairs.")

        endpoint_signals: dict[tuple[str, ...], str] = {}
        for binding in self.endpoint_bindings:
            if binding.signal_id not in signal_ids:
                raise ValueError(
                    f"Signal endpoint binding '{binding.id}' references missing signal '{binding.signal_id}'."
                )
            key = binding.endpoint.logical_identity
            existing_signal = endpoint_signals.get(key)
            if existing_signal is not None and (
                existing_signal != binding.signal_id
                or binding.endpoint.kind is not SignalEndpointKind.PROTECTION_INPUT
            ):
                raise ValueError("A logical endpoint may have only one canonical signal designation.")
            endpoint_signals[key] = binding.signal_id

    @staticmethod
    def _validate_unique_tags(records: tuple, label: str) -> None:
        tags = [record.tag for record in records]
        if len(tags) != len(set(tags)):
            raise ValueError(f"Duplicate {label} tag in wiring inventory.")


__all__ = [
    "WiringTerminalReference",
    "WiringConductorRole",
    "SignalKind",
    "CarrierKind",
    "TerminalAccessoryKind",
    "TerminalAccessoryState",
    "TerminalBlock",
    "TerminalPoint",
    "TerminalAccessory",
    "CableAssembly",
    "CableCore",
    "PanelWire",
    "SignalDefinition",
    "SignalCarrierBinding",
    "SignalEndpointKind",
    "SignalEndpointReference",
    "SignalEndpointBinding",
    "WiringTagSeries",
    "WiringTagPolicy",
    "InstrumentationWiringInventory",
]
