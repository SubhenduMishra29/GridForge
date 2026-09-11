# ============================================================
# File: core/application/read_models.py
# GridForge V2 — Application Read Models
# Author: Subhendu Mishra
# ============================================================
"""Immutable read-side DTOs exposed across the Application boundary."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


_CANONICAL_ATTRIBUTES: dict[str, tuple[str, ...]] = {
    "BUS": ("nominal_voltage_kv", "voltage_pu", "angle_deg", "frequency_hz", "in_service"),
    "LINE": ("resistance_ohm", "reactance_ohm", "shunt_susceptance_siemens", "rate_mva", "in_service"),
    "CABLE": ("length_km", "rated_voltage_kv", "rated_current_a", "r1", "x1", "b1", "r0", "x0", "b0", "thermal_limit_mva", "conductor_count", "in_service"),
    "TRANSFORMER": ("r", "x", "b", "impedance_basis", "impedance_base_mva", "impedance_base_voltage_kv", "rate_mva", "tap", "tap_ratio", "turns_ratio", "shift", "phase_shift_rad", "phase_shift_deg", "in_service"),
    "SWITCH": ("closed", "in_service", "normally_closed", "rated_voltage_kv", "rated_current_a"),
    "BREAKER": ("closed", "failed", "in_service", "voltage_kv", "current_a", "interrupting_ka"),
    "DISCONNECTOR": ("closed", "in_service", "normally_closed", "voltage_kv", "rated_current_a", "operating_time"),
    "FUSE": ("in_service", "blown", "rated_current_a", "rated_voltage_v", "interrupting_rating_ka"),
    "LOAD": ("p", "q", "in_service"),
    "GENERATOR": ("p", "q", "V_setpoint", "q_min", "q_max", "in_service"),
    "SYNCHRONOUS_MACHINE": ("active_power_injection_mw", "reactive_power_injection_mvar", "rated_power_mva", "rated_voltage_kv", "frequency_hz", "in_service"),
    "MOTOR": ("rated_mva", "rated_kv", "power_factor", "p", "q", "efficiency", "slip", "starting_current_pu", "running", "in_service"),
    "SHUNT": ("g_pu", "b_pu", "in_service"),
    "CAPACITOR": ("reactive_power_injection_mvar", "in_service"),
    "REACTOR": ("reactive_power_injection_mvar", "in_service"),
    "SOLAR": ("p_mw", "q_mvar", "p_min_mw", "p_max_mw", "q_min_mvar", "q_max_mvar", "in_service"),
    "BATTERY": ("p_mw", "q_mvar", "max_charge_mw", "max_discharge_mw", "energy_capacity_mwh", "soc", "soc_min", "soc_max", "in_service"),
    "GRID": ("nominal_voltage_kv", "frequency_hz", "voltage_pu", "angle_deg", "p_mw", "q_mvar", "short_circuit_mva", "x_over_r", "z1_pu", "z2_pu", "z0_pu", "in_service", "grounded"),
    "CT": ("primary_rated_current_a", "secondary_rated_current_a", "ratio", "burden_va", "accuracy_class", "frequency_hz", "polarity", "in_service"),
    "PT": ("primary_voltage_kv", "secondary_voltage_v", "voltage_ratio", "accuracy_class", "burden_va", "phase_displacement_deg", "in_service"),
    "CVT": ("rated_primary_voltage_kv", "rated_secondary_voltage_v", "voltage_ratio", "accuracy_class", "rated_burden_va", "polarity", "frequency_hz", "in_service"),
}


def _freeze(value: Any) -> Any:
    """Recursively freeze supported container values for read-side snapshots."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class ElementReadModel:
    """Stable, UI-neutral immutable snapshot of one network element."""

    object_id: str
    element_type: str
    labels: Mapping[str, str]
    connectivity_refs: tuple[str, ...]
    attributes: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.object_id, str) or not self.object_id:
            raise ValueError("ElementReadModel.object_id must be non-empty")
        if not isinstance(self.element_type, str) or not self.element_type:
            raise ValueError("ElementReadModel.element_type must be non-empty")
        if not isinstance(self.labels, Mapping):
            raise TypeError("ElementReadModel.labels must be a mapping")
        if not isinstance(self.connectivity_refs, tuple):
            raise TypeError("ElementReadModel.connectivity_refs must be a tuple")
        if not isinstance(self.attributes, Mapping):
            raise TypeError("ElementReadModel.attributes must be a mapping")
        attributes = dict(self.attributes)
        semantic_type = self.element_type.strip().upper()
        for key in _CANONICAL_ATTRIBUTES.get(semantic_type, ()):
            attributes.setdefault(key, None)
        object.__setattr__(self, "labels", _freeze(self.labels))
        object.__setattr__(self, "attributes", _freeze(attributes))


@dataclass(frozen=True, slots=True)
class NetworkReadModel:
    """Immutable collection snapshot used by presentation projections."""

    elements: tuple[ElementReadModel, ...]


@dataclass(frozen=True, slots=True)
class RelayInputBindingReadModel:
    """Immutable identifier-only relay input binding."""

    input_name: str
    channel_id: str | None


@dataclass(frozen=True, slots=True)
class RelayReadModel:
    """Immutable presentation snapshot of one authoritative physical Relay."""

    object_id: str
    name: str
    relay_type: str
    function_type: str
    plugin_id: str | None
    settings: Mapping[str, Any]
    in_service: bool
    enabled: bool
    blocked: bool
    picked_up: bool
    tripped: bool
    input_channel_bindings: tuple[RelayInputBindingReadModel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "settings", _freeze(self.settings))
        object.__setattr__(self, "input_channel_bindings", tuple(self.input_channel_bindings))


@dataclass(frozen=True, slots=True)
class ProtectionReadModel:
    """Immutable collection snapshot of protection-domain read data."""

    relays: tuple[RelayReadModel, ...]


__all__ = [
    "ElementReadModel",
    "NetworkReadModel",
    "ProtectionReadModel",
    "RelayInputBindingReadModel",
    "RelayReadModel",
]
