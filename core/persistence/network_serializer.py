# ============================================================
# File: core/persistence/network_serializer.py
# GridForge V2 — Network Persistence Reconstruction
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
    "buses", "grids", "generators", "synchronous_machines", "loads", "motors", "shunts",
    "capacitors", "reactors", "solar", "batteries", "current_transformers",
    "capacitive_voltage_transformers", "potential_transformers", "relays", "lines", "cables",
    "transformers", "breakers", "switches", "disconnectors", "fuses",
)

def serialize_network(network: Network) -> dict[str, Any]:
    """Return the complete canonical engineering Network representation."""
    if not isinstance(network, Network): raise TypeError("network must be a Network.")
    elements: list[dict[str, Any]] = []
    seen: set[int] = set()
    for collection_name in _COLLECTIONS:
        for element in getattr(network, collection_name):
            identity = id(element)
            if identity in seen: continue
            seen.add(identity)
            elements.append(model_to_dto(element).to_dict())
    elements.sort(key=lambda item: (item["type"], item["id"]))
    return {"schema": 1, "elements": elements}


def deserialize_network(data: dict[str, Any], *, registry: ModelTypeRegistry | None = None) -> Network:
    """Reconstruct a Network from canonical persisted engineering data."""
    if not isinstance(data, dict): raise TypeError("Persisted project state must be an object.")
    if data.get("schema") != 1: raise NetworkSerializationError(f"Unsupported project network schema: {data.get('schema')!r}")
    type_registry = registry or ModelTypeRegistry()
    network = Network()
    pending_terminals: list[tuple[Any, dict[str, Any]]] = []
    for raw in data.get("elements", ()):
        dto = ModelDTO.from_dict(raw)
        model_type = type_registry.resolve(dto.type)
        if dto.id.strip() == "": raise NetworkSerializationError("Persisted model ID cannot be empty.")
        model = object.__new__(model_type)
        restore_state(model, dto.state)
        if getattr(model, "id", None) != dto.id:
            object.__setattr__(model, "_id", dto.id)
        for terminal_data in dto.terminals:
            terminal = Terminal(owner=model, role=terminal_data.role)
            setattr(model, terminal_data.attribute, terminal)
            if terminal_data.endpoint_type is not None:
                pending_terminals.append(
                    (terminal, {"type": terminal_data.endpoint_type, "id": terminal_data.endpoint_id})
                )
        try:
            model.validate()
        except Exception as exc:
            raise NetworkSerializationError(
                f"Invalid reconstructed {model_type.__name__} '{dto.id}': {exc}"
            ) from exc
        try:
            getattr(network, network_adder_name(model_type))(model)
        except (TypeError, ValueError, KeyError) as exc:
            raise NetworkSerializationError(
                f"Unable to register reconstructed {model_type.__name__} '{dto.id}': {exc}"
            ) from exc

    for terminal, endpoint_ref in pending_terminals:
        endpoint_id = endpoint_ref["id"]
        endpoint_type_name = endpoint_ref["type"]
        if endpoint_id is None:
            raise NetworkSerializationError("Terminal endpoint ID cannot be null.")
        try:
            endpoint_type = type_registry.resolve(endpoint_type_name)
            endpoint = network.get_by_identity(endpoint_id)
        except (KeyError, ValueError) as exc:
            raise NetworkSerializationError(
                f"Terminal endpoint does not exist: {endpoint_type_name}:{endpoint_id}"
            ) from exc
        if not isinstance(endpoint, endpoint_type):
            raise NetworkSerializationError(
                f"Terminal endpoint type mismatch for {endpoint_id}: "
                f"persisted={endpoint_type_name}, actual={type(endpoint).__name__}"
            )
        if isinstance(endpoint, Terminal):
            raise NetworkSerializationError(
                "Terminal-to-Terminal connectivity is not supported."
            )
        try:
            terminal.attach(endpoint)
        except (TypeError, ValueError) as exc:
            raise NetworkSerializationError(
                f"Invalid terminal endpoint relationship for '{terminal.role}': {exc}"
            ) from exc

    try:
        network.rebuild_topology()
        network.validate()
    except Exception as exc:
        raise NetworkSerializationError(
            f"Reconstructed Network failed final integrity validation: {exc}"
        ) from exc
    return network


__all__ = ["NetworkSerializationError", "deserialize_network", "serialize_network"]
