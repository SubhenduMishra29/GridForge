# ============================================================
# File: core/persistence/network_serializer.py
# GridForge V2 — Network Persistence Serializer
# Author: Subhendu Mishra
# ============================================================

"""Canonical serialization of Network membership and connectivity."""

from __future__ import annotations

from typing import Any

from core.model.terminal import Terminal
from core.network import Network

from .model_dto import ModelDTO, model_to_dto, restore_state
from .type_registry import ModelTypeRegistry, network_adder_name


class NetworkSerializationError(ValueError):
    """Raised when a Network cannot be reconstructed without loss."""


_COLLECTIONS = (
    "buses",
    "grids",
    "generators",
    "synchronous_machines",
    "loads",
    "motors",
    "shunts",
    "capacitors",
    "reactors",
    "solar",
    "batteries",
    "current_transformers",
    "capacitive_voltage_transformers",
    "potential_transformers",
    "lines",
    "cables",
    "transformers",
    "breakers",
    "switches",
    "disconnectors",
    "fuses",
)

_ENDPOINT_TYPES = {
    "Bus": "bus",
    "Grid": "grid",
    "Generator": "generator",
    "SynchronousMachine": "synchronous_machine",
    "Load": "load",
    "Motor": "motor",
    "Shunt": "shunt",
    "Capacitor": "capacitor",
    "Reactor": "reactor",
    "Solar": "solar",
    "Battery": "battery",
    "CurrentTransformer": "current_transformer",
    "CT": "current_transformer",
    "PT": "potential_transformer",
    "PotentialTransformer": "potential_transformer",
    "CVT": "capacitive_voltage_transformer",
    "Line": "line",
    "Cable": "cable",
    "Transformer": "transformer",
    "Breaker": "breaker",
    "Switch": "switch",
    "Disconnector": "disconnector",
    "Fuse": "fuse",
}


def serialize_network(network: Network) -> dict[str, Any]:
    """Return the complete canonical engineering Network representation."""
    if not isinstance(network, Network):
        raise TypeError("network must be a Network.")

    elements: list[dict[str, Any]] = []
    seen: set[int] = set()
    for collection_name in _COLLECTIONS:
        for element in getattr(network, collection_name):
            identity = id(element)
            if identity in seen:
                continue
            seen.add(identity)
            elements.append(model_to_dto(element).to_dict())

    elements.sort(key=lambda item: (item["type"], item["id"]))
    return {
        "schema": 1,
        "elements": elements,
    }


def _endpoint_type(name: str) -> str:
    try:
        return _ENDPOINT_TYPES[name]
    except KeyError as exc:
        raise NetworkSerializationError(
            f"Unsupported endpoint model type in project: {name}"
        ) from exc


def deserialize_network(data: dict[str, Any], *, registry: ModelTypeRegistry | None = None) -> Network:
    """Reconstruct a Network from canonical persisted engineering data."""
    if not isinstance(data, dict):
        raise TypeError("Persisted project state must be an object.")
    if data.get("schema") != 1:
        raise NetworkSerializationError(
            f"Unsupported project network schema: {data.get('schema')!r}"
        )

    type_registry = registry or ModelTypeRegistry()
    network = Network()
    pending_terminals: list[tuple[Any, dict[str, Any]]] = []

    for raw in data.get("elements", ()):
        dto = ModelDTO.from_dict(raw)
        model_type = type_registry.resolve(dto.type)
        if dto.id.strip() == "":
            raise NetworkSerializationError("Persisted model ID cannot be empty.")

        model = object.__new__(model_type)
        # Stable identity and all model state are restored exactly from the DTO.
        restore_state(model, dto.state)
        if getattr(model, "id", None) != dto.id:
            object.__setattr__(model, "_id", dto.id)

        for terminal_data in dto.terminals:
            terminal = Terminal(owner=model, role=terminal_data.role)
            setattr(model, terminal_data.attribute, terminal)
            if terminal_data.endpoint_type is not None:
                pending_terminals.append(
                    (
                        terminal,
                        {
                            "type": terminal_data.endpoint_type,
                            "id": terminal_data.endpoint_id,
                        },
                    )
                )

        adder_name = network_adder_name(model_type)
        getattr(network, adder_name)(model)

    for terminal, endpoint_ref in pending_terminals:
        endpoint_type = _endpoint_type(endpoint_ref["type"])
        endpoint_id = endpoint_ref["id"]
        if endpoint_id is None:
            raise NetworkSerializationError("Terminal endpoint ID cannot be null.")
        try:
            endpoint = network.get_by_id(endpoint_type, endpoint_id)
        except KeyError as exc:
            raise NetworkSerializationError(
                f"Terminal endpoint does not exist: {endpoint_type}:{endpoint_id}"
            ) from exc
        if isinstance(endpoint, Terminal):
            raise NetworkSerializationError("Terminal-to-Terminal connectivity is not supported.")
        terminal.attach(endpoint)

    network.rebuild_topology()
    return network


__all__ = [
    "NetworkSerializationError",
    "deserialize_network",
    "serialize_network",
]
