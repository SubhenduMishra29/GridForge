# ============================================================
# File: core/application/read_service.py
# GridForge V2 — Application Read Services
# Author: Subhendu Mishra
# ============================================================
"""Read-only Application boundaries for authoritative Core state.

Presentation consumers use these services instead of reaching into Core
models or registries directly. Services create immutable read snapshots and
never mutate Core state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.network.network import Network
from core.protection.protection_system import ProtectionSystem

from .read_models import (
    ElementReadModel,
    NetworkReadModel,
    ProtectionReadModel,
    RelayReadModel,
)


_ELEMENT_COLLECTIONS = (
    "buses", "grids", "generators", "synchronous_machines", "loads",
    "motors", "shunts", "capacitors", "reactors", "solar", "batteries",
    "current_transformers", "potential_transformers", "capacitive_voltage_transformers",
    "lines", "cables", "transformers", "breakers", "switches",
    "disconnectors", "fuses",
)


class ReadService(ABC):
    """Framework-neutral contract for Application network read operations."""

    @abstractmethod
    def network(self) -> NetworkReadModel:
        """Return an immutable snapshot of authoritative network elements."""
        raise NotImplementedError

    @abstractmethod
    def element(self, element_type: str, object_id: str) -> ElementReadModel:
        """Return one immutable element snapshot."""
        raise NotImplementedError


class NetworkReadService(ReadService):
    """Default read adapter over the authoritative Core Network aggregate."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("NetworkReadService requires a Network")
        self._network = network

    def network(self) -> NetworkReadModel:
        """Snapshot all registered concrete network elements."""
        elements: list[ElementReadModel] = []
        for element_type in _ELEMENT_COLLECTIONS:
            for model in getattr(self._network, element_type):
                elements.append(self._to_read_model(element_type, model))
        return NetworkReadModel(elements=tuple(elements))

    def element(self, element_type: str, object_id: str) -> ElementReadModel:
        """Snapshot one canonical Core element without exposing it to callers."""
        key = element_type.strip().lower()
        model = self._network.get_by_id(key, object_id)
        return self._to_read_model(key, model)

    @staticmethod
    def _to_read_model(element_type: str, model: Any) -> ElementReadModel:
        object_id = str(getattr(model, "id"))
        name = getattr(model, "name", None)
        labels = {"name": str(name)} if name is not None else {}
        connectivity_refs, terminal_connectivity = NetworkReadService._connectivity(model)

        attributes: dict[str, Any] = {}
        for name in (
            "r", "x", "b", "rated_power", "voltage",
            "primary_rated_current_a", "secondary_rated_current_a",
            "primary_voltage_kv", "secondary_voltage_v",
            "rated_primary_voltage_kv", "rated_secondary_voltage_v",
            "burden_va", "rated_burden_va", "accuracy_class",
            "phase_displacement_deg", "polarity", "in_service",
        ):
            value = getattr(model, name, None)
            if isinstance(value, (str, int, float, bool)):
                attributes[name] = value.value if hasattr(value, "value") else value

        ratio = getattr(model, "ratio", None)
        if isinstance(ratio, (int, float)):
            attributes["ratio"] = ratio

        endpoint_from_id, endpoint_to_id = NetworkReadService._branch_endpoint_ids(model)
        if endpoint_from_id is not None:
            attributes["endpoint_from_id"] = endpoint_from_id
        if endpoint_to_id is not None:
            attributes["endpoint_to_id"] = endpoint_to_id

        if terminal_connectivity:
            # Tuple-of-tuples is deliberately used instead of a nested dict so
            # the immutable read snapshot cannot expose mutable Core state.
            attributes["terminal_connectivity"] = terminal_connectivity

        return ElementReadModel(
            object_id=object_id,
            element_type=element_type,
            labels=labels,
            connectivity_refs=connectivity_refs,
            attributes=attributes,
        )

    @staticmethod
    def _connectivity(model: Any) -> tuple[tuple[str, ...], tuple[tuple[str, str | None], ...]]:
        """Extract authoritative terminal identities without traversing topology."""
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
                    terminal_connectivity.append(
                        (str(role), None if endpoint_id is None else str(endpoint_id))
                    )
            return tuple(dict.fromkeys(refs)), tuple(terminal_connectivity)

        for attribute in ("from_terminal", "to_terminal", "terminal"):
            value = getattr(model, attribute, None)
            if value is None:
                continue
            value_id = getattr(value, "id", None)
            if value_id is not None:
                refs.append(str(value_id))

        return tuple(dict.fromkeys(refs)), ()

    @staticmethod
    def _branch_endpoint_ids(model: Any) -> tuple[str | None, str | None]:
        """Expose endpoint identities without exposing Core objects."""
        from_terminal = getattr(model, "from_terminal", None)
        to_terminal = getattr(model, "to_terminal", None)

        def endpoint_id(terminal: Any) -> str | None:
            if terminal is None:
                return None
            endpoint = getattr(terminal, "endpoint", None)
            value = getattr(endpoint, "id", None)
            return None if value is None else str(value)

        return endpoint_id(from_terminal), endpoint_id(to_terminal)


class ProtectionReadService:
    """Read adapter over authoritative physical Relays in ProtectionSystem."""

    def __init__(self, protection_system: ProtectionSystem) -> None:
        if not isinstance(protection_system, ProtectionSystem):
            raise TypeError("ProtectionReadService requires a ProtectionSystem")
        self._protection_system = protection_system

    def protection(self) -> ProtectionReadModel:
        """Return an immutable snapshot of physical Relays represented by ProtectionElements."""
        relays = tuple(
            self._to_read_model(relay)
            for relay in self._protection_system.relays()
        )
        return ProtectionReadModel(relays=relays)

    def relay(self, object_id: str) -> RelayReadModel:
        """Return one authoritative physical Relay snapshot by stable ID."""
        for relay in self._protection_system.relays():
            if relay.id == object_id:
                return self._to_read_model(relay)
        raise KeyError(f"Relay '{object_id}' is not represented by ProtectionSystem")

    @staticmethod
    def _to_read_model(relay: Any) -> RelayReadModel:
        return RelayReadModel(
            object_id=str(relay.id),
            name=str(relay.name),
            relay_type=str(relay.type),
            function_type=str(relay.function_type),
            in_service=bool(relay.in_service),
            enabled=bool(relay.enabled),
            blocked=bool(relay.blocked),
        )


__all__ = ["NetworkReadService", "ProtectionReadService", "ReadService"]
