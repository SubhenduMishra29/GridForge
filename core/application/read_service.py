# ============================================================
# File: core/application/read_service.py
# GridForge V2 — Application Read Services
# Author: Subhendu Mishra
# ============================================================
"""Read-only Application boundaries for authoritative Core state."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.network.network import Network
from core.protection.protection_system import ProtectionSystem

from .read_models import (
    ElementReadModel,
    NetworkReadModel,
    ProtectionReadModel,
    RelayInputBindingReadModel,
    RelayReadModel,
)


_ELEMENT_COLLECTIONS = (
    "buses", "grids", "generators", "synchronous_machines", "loads",
    "motors", "shunts", "capacitors", "reactors", "solar", "batteries",
    "current_transformers", "potential_transformers", "capacitive_voltage_transformers",
    "lines", "cables", "transformers", "breakers", "switches",
    "disconnectors", "fuses",
)

_FIELD_CONTRACTS: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "buses": (
        ("nominal_voltage_kv", ("nominal_voltage_kv",)), ("voltage_pu", ("voltage_pu",)),
        ("angle_deg", ("angle_deg",)), ("frequency_hz", ("frequency_hz",)), ("in_service", ("in_service",)),
    ),
    "lines": (
        ("resistance_ohm", ("resistance_ohm", "r")), ("reactance_ohm", ("reactance_ohm", "x")),
        ("shunt_susceptance_siemens", ("shunt_susceptance_siemens", "b")), ("rate_mva", ("rate_mva", "rated_power")),
        ("in_service", ("in_service",)),
    ),
    "cables": (
        ("length_km", ("length_km",)), ("rated_voltage_kv", ("rated_voltage_kv",)),
        ("rated_current_a", ("rated_current_a",)), ("r1_ohm_per_km", ("r1_ohm_per_km",)),
        ("x1_ohm_per_km", ("x1_ohm_per_km",)), ("b1_us_per_km", ("b1_us_per_km",)),
        ("r0_ohm_per_km", ("r0_ohm_per_km",)), ("x0_ohm_per_km", ("x0_ohm_per_km",)),
        ("b0_us_per_km", ("b0_us_per_km",)), ("thermal_limit_mva", ("thermal_limit_mva",)),
        ("conductor_count", ("conductor_count",)), ("in_service", ("in_service",)),
    ),
    "transformers": (
        ("r", ("r",)), ("x", ("x",)), ("b", ("b",)), ("impedance_basis", ("impedance_basis",)),
        ("impedance_base_mva", ("impedance_base_mva",)), ("impedance_base_voltage_kv", ("impedance_base_voltage_kv",)),
        ("rate_mva", ("rate_mva", "rated_power")), ("tap", ("tap",)), ("tap_ratio", ("tap_ratio",)),
        ("turns_ratio", ("turns_ratio",)), ("shift", ("shift",)), ("phase_shift_rad", ("phase_shift_rad",)),
        ("phase_shift_deg", ("phase_shift_deg",)), ("in_service", ("in_service",)),
    ),
    "switches": (
        ("closed", ("closed",)), ("in_service", ("in_service",)), ("normally_closed", ("normally_closed",)),
        ("rated_voltage_kv", ("rated_voltage_kv",)), ("rated_current_a", ("rated_current_a",)),
    ),
    "breakers": (
        ("closed", ("closed",)), ("failed", ("failed",)), ("in_service", ("in_service",)),
        ("voltage_kv", ("voltage_kv", "rated_voltage_kv")), ("current_a", ("current_a", "rated_current_a")),
        ("interrupting_ka", ("interrupting_ka",)),
    ),
    "disconnectors": (
        ("closed", ("closed",)), ("in_service", ("in_service",)), ("normally_closed", ("normally_closed",)),
        ("voltage_kv", ("voltage_kv", "rated_voltage_kv")), ("rated_current_a", ("rated_current_a",)),
        ("operating_time", ("operating_time",)),
    ),
    "fuses": (
        ("in_service", ("in_service",)), ("blown", ("blown",)), ("rated_current_a", ("rated_current_a",)),
        ("rated_voltage_v", ("rated_voltage_v",)), ("interrupting_rating_ka", ("interrupting_rating_ka",)),
    ),
    "loads": (("p", ("p",)), ("q", ("q",)), ("in_service", ("in_service",))),
    "generators": (
        ("p", ("p", "active_power_injection_mw")), ("q", ("q", "reactive_power_injection_mvar")),
        ("V_setpoint", ("V_setpoint", "v_setpoint")), ("q_min", ("q_min",)), ("q_max", ("q_max",)),
        ("in_service", ("in_service",)),
    ),
    "synchronous_machines": (
        ("active_power_injection_mw", ("active_power_injection_mw",)),
        ("reactive_power_injection_mvar", ("reactive_power_injection_mvar",)),
        ("rated_power_mva", ("rated_power_mva",)), ("rated_voltage_kv", ("rated_voltage_kv",)),
        ("frequency_hz", ("frequency_hz",)), ("in_service", ("in_service",)),
    ),
    "motors": (
        ("rated_mva", ("rated_mva",)), ("rated_kv", ("rated_kv",)), ("power_factor", ("power_factor",)),
        ("p", ("p",)), ("q", ("q",)), ("efficiency", ("efficiency",)), ("slip", ("slip",)),
        ("starting_current_pu", ("starting_current_pu",)), ("running", ("running",)), ("in_service", ("in_service",)),
    ),
    "shunts": (("g_pu", ("g_pu",)), ("b_pu", ("b_pu",)), ("in_service", ("in_service",))),
    "capacitors": (("reactive_power_injection_mvar", ("reactive_power_injection_mvar", "q")), ("in_service", ("in_service",))),
    "reactors": (("reactive_power_injection_mvar", ("reactive_power_injection_mvar", "q")), ("in_service", ("in_service",))),
    "solar": (
        ("p_mw", ("p_mw", "p")), ("q_mvar", ("q_mvar", "q")), ("p_min_mw", ("p_min_mw",)),
        ("p_max_mw", ("p_max_mw",)), ("q_min_mvar", ("q_min_mvar",)), ("q_max_mvar", ("q_max_mvar",)),
        ("in_service", ("in_service",)),
    ),
    "batteries": (
        ("p_mw", ("p_mw", "p")), ("q_mvar", ("q_mvar", "q")), ("max_charge_mw", ("max_charge_mw",)),
        ("max_discharge_mw", ("max_discharge_mw",)), ("energy_capacity_mwh", ("energy_capacity_mwh",)),
        ("soc", ("soc",)), ("soc_min", ("soc_min",)), ("soc_max", ("soc_max",)), ("in_service", ("in_service",)),
    ),
    "grids": (
        ("nominal_voltage_kv", ("nominal_voltage_kv",)), ("frequency_hz", ("frequency_hz",)),
        ("voltage_pu", ("voltage_pu",)), ("angle_deg", ("angle_deg",)), ("p_mw", ("p_mw", "p")),
        ("q_mvar", ("q_mvar", "q")), ("short_circuit_mva", ("short_circuit_mva",)),
        ("x_over_r", ("x_over_r",)), ("z1_pu", ("z1_pu",)), ("z2_pu", ("z2_pu",)), ("z0_pu", ("z0_pu",)),
        ("in_service", ("in_service",)), ("grounded", ("grounded",)),
    ),
    "current_transformers": (
        ("primary_rated_current_a", ("primary_rated_current_a",)), ("secondary_rated_current_a", ("secondary_rated_current_a",)),
        ("ratio", ("ratio",)), ("burden_va", ("burden_va",)), ("accuracy_class", ("accuracy_class",)),
        ("frequency_hz", ("frequency_hz",)), ("polarity", ("polarity",)), ("in_service", ("in_service",)),
    ),
    "potential_transformers": (
        ("primary_voltage_kv", ("primary_voltage_kv",)), ("secondary_voltage_v", ("secondary_voltage_v",)),
        ("voltage_ratio", ("voltage_ratio", "ratio")), ("accuracy_class", ("accuracy_class",)),
        ("burden_va", ("burden_va",)), ("phase_displacement_deg", ("phase_displacement_deg",)), ("in_service", ("in_service",)),
    ),
    "capacitive_voltage_transformers": (
        ("rated_primary_voltage_kv", ("rated_primary_voltage_kv",)), ("rated_secondary_voltage_v", ("rated_secondary_voltage_v",)),
        ("voltage_ratio", ("voltage_ratio", "ratio")), ("accuracy_class", ("accuracy_class",)),
        ("rated_burden_va", ("rated_burden_va",)), ("polarity", ("polarity",)), ("frequency_hz", ("frequency_hz",)),
        ("in_service", ("in_service",)),
    ),
}


class ReadService(ABC):
    """Framework-neutral contract for Application network read operations."""

    @abstractmethod
    def network(self) -> NetworkReadModel:
        raise NotImplementedError

    @abstractmethod
    def element(self, element_type: str, object_id: str) -> ElementReadModel:
        raise NotImplementedError


class NetworkReadService(ReadService):
    """Default read adapter over the authoritative Core Network aggregate."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("NetworkReadService requires a Network")
        self._network = network

    def network(self) -> NetworkReadModel:
        elements: list[ElementReadModel] = []
        for element_type in _ELEMENT_COLLECTIONS:
            for model in getattr(self._network, element_type):
                elements.append(self._to_read_model(element_type, model))
        return NetworkReadModel(elements=tuple(elements))

    def element(self, element_type: str, object_id: str) -> ElementReadModel:
        key = element_type.strip().lower()
        model = self._network.get_by_id(key, object_id)
        return self._to_read_model(key, model)

    @staticmethod
    def _value(model: Any, names: tuple[str, ...]) -> Any:
        for name in names:
            value = getattr(model, name, None)
            if value is not None:
                return value.value if hasattr(value, "value") else value
        return None

    @classmethod
    def _project_attributes(cls, element_type: str, model: Any) -> dict[str, Any]:
        attributes: dict[str, Any] = {}
        for canonical, aliases in _FIELD_CONTRACTS.get(element_type, ()):
            value = cls._value(model, aliases)
            if value is not None and isinstance(value, (str, int, float, bool)):
                attributes[canonical] = value
        if element_type == "fuses" and "in_service" in attributes and "blown" in attributes:
            attributes["conducts"] = bool(attributes["in_service"] and not attributes["blown"])
        if element_type == "disconnectors" and "closed" in attributes:
            attributes["conducts"] = bool(attributes["closed"] and attributes.get("in_service", True))
        if element_type == "reactors" and "reactive_power_injection_mvar" in attributes:
            attributes["absorption_mvar"] = abs(float(attributes["reactive_power_injection_mvar"]))
        if element_type == "batteries":
            if "soc" in attributes:
                attributes["state_of_charge"] = attributes["soc"]
                attributes["soc_percent"] = float(attributes["soc"]) * 100.0
            if "energy_capacity_mwh" in attributes and "soc" in attributes:
                stored = float(attributes["energy_capacity_mwh"]) * float(attributes["soc"])
                attributes["stored_energy_mwh"] = stored
                attributes["available_energy_mwh"] = max(0.0, float(attributes["energy_capacity_mwh"]) - stored)
        return attributes

    @staticmethod
    def _to_read_model(element_type: str, model: Any) -> ElementReadModel:
        object_id = str(getattr(model, "id"))
        name = getattr(model, "name", None)
        labels = {"name": str(name)} if name is not None else {}
        connectivity_refs, terminal_connectivity = NetworkReadService._connectivity(model)
        attributes = NetworkReadService._project_attributes(element_type, model)
        endpoint_from_id, endpoint_to_id = NetworkReadService._branch_endpoint_ids(model)
        if endpoint_from_id is not None:
            attributes["from_endpoint"] = endpoint_from_id
            attributes["endpoint_from_id"] = endpoint_from_id
        if endpoint_to_id is not None:
            attributes["to_endpoint"] = endpoint_to_id
            attributes["endpoint_to_id"] = endpoint_to_id
        if terminal_connectivity:
            attributes["terminal_connectivity"] = terminal_connectivity
        return ElementReadModel(object_id=object_id, element_type=element_type, labels=labels,
                                 connectivity_refs=connectivity_refs, attributes=attributes)

    @staticmethod
    def _connectivity(model: Any) -> tuple[tuple[str, ...], tuple[tuple[str, str | None], ...]]:
        refs: list[str] = []
        terminal_connectivity: list[tuple[str, str | None]] = []
        terminals = getattr(model, "terminals", None)
        if terminals is not None:
            for terminal in terminals:
                role = getattr(terminal, "role", None)
                terminal_id = getattr(terminal, "id", None)
                endpoint = getattr(terminal, "endpoint", None)
                endpoint_id = getattr(endpoint, "id", None)
                if terminal_id is not None:
                    refs.append(str(terminal_id))
                if role is not None:
                    terminal_connectivity.append((str(role), None if endpoint_id is None else str(endpoint_id)))
            return tuple(dict.fromkeys(refs)), tuple(terminal_connectivity)
        for attribute in ("from_terminal", "to_terminal", "terminal"):
            value = getattr(model, attribute, None)
            value_id = getattr(value, "id", None) if value is not None else None
            if value_id is not None:
                refs.append(str(value_id))
        return tuple(dict.fromkeys(refs)), ()

    @staticmethod
    def _branch_endpoint_ids(model: Any) -> tuple[str | None, str | None]:
        def endpoint_id(terminal: Any) -> str | None:
            if terminal is None:
                return None
            endpoint = getattr(terminal, "endpoint", None)
            value = getattr(endpoint, "id", None)
            return None if value is None else str(value)
        return endpoint_id(getattr(model, "from_terminal", None)), endpoint_id(getattr(model, "to_terminal", None))


class ProtectionReadService:
    """Read adapter over authoritative physical Relays in ProtectionSystem."""

    def __init__(self, protection_system: ProtectionSystem) -> None:
        if not isinstance(protection_system, ProtectionSystem):
            raise TypeError("ProtectionReadService requires a ProtectionSystem")
        self._protection_system = protection_system

    def protection(self) -> ProtectionReadModel:
        return ProtectionReadModel(relays=tuple(self._to_read_model(relay) for relay in self._protection_system.relays()))

    def relay(self, object_id: str) -> RelayReadModel:
        for relay in self._protection_system.relays():
            if relay.id == object_id:
                return self._to_read_model(relay)
        raise KeyError(f"Relay '{object_id}' is not represented by ProtectionSystem")

    @staticmethod
    def _to_read_model(relay: Any) -> RelayReadModel:
        bindings = tuple(
            RelayInputBindingReadModel(
                input_name=str(name),
                channel_id=None if getattr(channel, "id", None) is None else str(getattr(channel, "id")),
            )
            for name, channel in sorted(relay.input_channels.items())
        )
        return RelayReadModel(
            object_id=str(relay.id), name=str(relay.name), relay_type=str(relay.type),
            function_type=str(relay.function_type), plugin_id=None if relay.plugin_id is None else str(relay.plugin_id),
            settings=relay.settings, in_service=bool(relay.in_service), enabled=bool(relay.enabled),
            blocked=bool(relay.blocked), picked_up=bool(relay.picked_up), tripped=bool(relay.tripped),
            input_channel_bindings=bindings,
        )


__all__ = ["NetworkReadService", "ProtectionReadService", "ReadService"]
