"""Lossless JSON codec for canonical instrumentation wiring inventory."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.model.instrument_wiring import (
    CableAssembly, CableCore, CarrierKind, InstrumentationWiringInventory, PhysicalConnectionHop,
    PanelWire, SignalCarrierBinding, SignalDefinition, SignalKind,
    WiringConductorRole, WiringTerminalReference, WiringTagSeries, WiringTagPolicy,
)

WIRING_SCHEMA_VERSION = 3


class InstrumentationWiringSerializationError(ValueError):
    """Raised when a wiring inventory cannot be serialized without loss."""


def _terminal_to_dict(item: WiringTerminalReference) -> dict[str, str]:
    return {
        "equipment_id": item.equipment_id,
        "terminal_role": item.terminal_role,
        "designation": item.designation,
    }


def _terminal_from_dict(data: Mapping[str, Any]) -> WiringTerminalReference:
    if not isinstance(data, Mapping) or set(data) != {"equipment_id", "terminal_role", "designation"}:
        raise InstrumentationWiringSerializationError("Malformed wiring terminal reference.")
    return WiringTerminalReference(**dict(data))


def _check_record_fields(data: Mapping[str, Any], *, required: set[str], optional: set[str], label: str) -> None:
    keys = set(data)
    missing = required - keys
    unknown = keys - required - optional
    if missing or unknown:
        details = []
        if missing:
            details.append("missing " + ", ".join(sorted(missing)))
        if unknown:
            details.append("unknown " + ", ".join(sorted(str(item) for item in unknown)))
        raise InstrumentationWiringSerializationError(
            label + " fields are not canonical: " + "; ".join(details)
        )


def serialize_instrumentation_wiring(
    inventory: InstrumentationWiringInventory,
) -> dict[str, Any]:
    """Serialize the complete immutable inventory; never include canvas geometry."""
    if not isinstance(inventory, InstrumentationWiringInventory):
        raise TypeError("inventory must be an InstrumentationWiringInventory.")
    return {
        "schema": WIRING_SCHEMA_VERSION,
        "cables": [
            {
                "id": item.id, "tag": item.tag, "service": item.service,
                "core_count": item.core_count, "cable_type": item.cable_type,
                "conductor_material": item.conductor_material,
                "cross_section_mm2": item.cross_section_mm2,
                "rated_voltage_v": item.rated_voltage_v, "length_m": item.length_m,
                "from_location": item.from_location, "to_location": item.to_location,
                "revision": item.revision, "lifecycle_status": item.lifecycle_status,
            }
            for item in inventory.cables
        ],
        "cores": [
            {
                "id": item.id, "cable_id": item.cable_id,
                "core_number": item.core_number, "role": item.role.value,
                "terminal_path": [_terminal_to_dict(ref) for ref in item.terminal_path],
                "colour": item.colour, "revision": item.revision, "pair_id": item.pair_id, "core_tag": item.core_tag, "revision": item.revision,
            }
            for item in inventory.cores
        ],
        "panel_wires": [
            {
                "id": item.id, "tag": item.tag, "role": item.role.value,
                "terminal_path": [_terminal_to_dict(ref) for ref in item.terminal_path],
                "cross_section_mm2": item.cross_section_mm2, "colour": item.colour,
            }
            for item in inventory.panel_wires
        ],
        "signals": [
            {
                "id": item.id, "tag": item.tag, "description": item.description,
                "kind": item.kind.value, "unit": item.unit, "phase": item.phase,
            }
            for item in inventory.signals
        ],
        "tag_policy": [
            {
                "record_kind": item.record_kind, "prefix": item.prefix,
                "separator": item.separator, "minimum_digits": item.minimum_digits,
                "next_number": item.next_number,
            }
            for item in inventory.tag_policy.series
        ],
        "signal_bindings": [
            {
                "id": item.id, "signal_id": item.signal_id,
                "carrier_kind": item.carrier_kind.value,
                "carrier_id": item.carrier_id, "direction": item.direction,
            }
            for item in inventory.signal_bindings
        ],
    }


def deserialize_instrumentation_wiring(data: Mapping[str, Any] | None) -> InstrumentationWiringInventory:
    """Validate and reconstruct a project-owned wiring inventory."""
    if data is None:
        return InstrumentationWiringInventory()
    if not isinstance(data, Mapping):
        raise InstrumentationWiringSerializationError("Instrumentation wiring payload must be an object.")
    expected = {"schema", "cables", "cores", "panel_wires", "signals", "signal_bindings", "tag_policy"}
    if set(data) != expected:
        raise InstrumentationWiringSerializationError(
            "Instrumentation wiring payload fields are not canonical: "
            + ", ".join(sorted(str(key) for key in set(data) ^ expected))
        )
    if isinstance(data.get("schema"), bool) or data.get("schema") != WIRING_SCHEMA_VERSION:
        raise InstrumentationWiringSerializationError(
            f"Unsupported instrumentation wiring schema {data.get('schema')!r}."
        )
    for key in ("cables", "cores", "panel_wires", "signals", "signal_bindings", "tag_policy"):
        if not isinstance(data.get(key), list) or any(not isinstance(item, Mapping) for item in data[key]):
            raise InstrumentationWiringSerializationError(f"Instrumentation wiring {key} must be an array of objects.")

    try:
        _field_contracts = (
            ("cables", {"id", "tag", "service", "core_count"}, {"cable_type", "conductor_material", "cross_section_mm2", "rated_voltage_v", "length_m", "from_location", "to_location", "revision", "lifecycle_status"}, "Cable assembly"),
            ("cores", {"id", "cable_id", "core_number", "role"}, {"terminal_path", "colour", "pair_id", "core_tag"}, "Cable core"),
            ("panel_wires", {"id", "tag", "role", "terminal_path"}, {"cross_section_mm2", "colour"}, "Panel wire"),
            ("signals", {"id", "tag", "description", "kind"}, {"unit", "phase"}, "Signal definition"),
            ("signal_bindings", {"id", "signal_id", "carrier_kind", "carrier_id"}, {"direction"}, "Signal carrier binding"),
            ("tag_policy", {"record_kind", "prefix"}, {"separator", "minimum_digits", "next_number"}, "Wiring tag series"),
        )
        for collection_name, required, optional, label in _field_contracts:
            for item in data[collection_name]:
                _check_record_fields(item, required=required, optional=optional, label=label)
        cables = tuple(CableAssembly(**dict(item)) for item in data["cables"])
        cores = tuple(
            CableCore(
                id=item["id"], cable_id=item["cable_id"], core_number=item["core_number"],
                role=WiringConductorRole(item["role"]),
                terminal_path=tuple(_terminal_from_dict(ref) for ref in item.get("terminal_path", ())),
                colour=item.get("colour"), pair_id=item.get("pair_id"), core_tag=item.get("core_tag"),
            )
            for item in data["cores"]
        )
        panel_wires = tuple(
            PanelWire(
                id=item["id"], tag=item["tag"], role=WiringConductorRole(item["role"]),
                terminal_path=tuple(_terminal_from_dict(ref) for ref in item["terminal_path"]),
                cross_section_mm2=item.get("cross_section_mm2"), colour=item.get("colour"),
            )
            for item in data["panel_wires"]
        )
        signals = tuple(
            SignalDefinition(
                id=item["id"], tag=item["tag"], description=item["description"],
                kind=SignalKind(item["kind"]), unit=item.get("unit"), phase=item.get("phase"),
            )
            for item in data["signals"]
        )
        tag_policy = WiringTagPolicy(series=tuple(
            WiringTagSeries(**dict(item)) for item in data["tag_policy"]
        ))
        bindings = tuple(
            SignalCarrierBinding(
                id=item["id"], signal_id=item["signal_id"],
                carrier_kind=CarrierKind(item["carrier_kind"]),
                carrier_id=item["carrier_id"], direction=item.get("direction", "BIDIRECTIONAL"),
            )
            for item in data["signal_bindings"]
        )
        return InstrumentationWiringInventory(
            cables=cables, cores=cores, panel_wires=panel_wires,
            signals=signals, signal_bindings=bindings, tag_policy=tag_policy,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise InstrumentationWiringSerializationError(
            f"Invalid instrumentation wiring inventory: {exc}"
        ) from exc


__all__ = [
    "WIRING_SCHEMA_VERSION",
    "InstrumentationWiringSerializationError",
    "serialize_instrumentation_wiring",
    "deserialize_instrumentation_wiring",
]
