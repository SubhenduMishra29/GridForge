# ============================================================
# File: core/application/read_service.py
# GridForge V2 — Application Read Service
# Author: Subhendu Mishra
# ============================================================
"""Read-only Application boundary for authoritative Network state.

Presentation consumers use this service instead of reaching into Core models
or NetworkRegistry directly. The service creates immutable read snapshots;
it never mutates Core state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.network.network import Network

from .read_models import ElementReadModel, NetworkReadModel


_ELEMENT_COLLECTIONS = (
    "buses", "grids", "generators", "synchronous_machines", "loads",
    "motors", "shunts", "capacitors", "reactors", "solar", "batteries",
    "lines", "cables", "transformers", "breakers", "switches",
    "disconnectors", "fuses",
)


class ReadService(ABC):
    """Framework-neutral contract for Application read operations."""

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
        connectivity_refs = NetworkReadService._connectivity_refs(model)

        attributes: dict[str, Any] = {}
        for name in ("r", "x", "b", "rated_power", "voltage"):
            value = getattr(model, name, None)
            if isinstance(value, (str, int, float, bool)):
                attributes[name] = value

        endpoint_from_id, endpoint_to_id = NetworkReadService._branch_endpoint_ids(model)
        if endpoint_from_id is not None:
            attributes["endpoint_from_id"] = endpoint_from_id
        if endpoint_to_id is not None:
            attributes["endpoint_to_id"] = endpoint_to_id

        return ElementReadModel(
            object_id=object_id,
            element_type=element_type,
            labels=labels,
            connectivity_refs=connectivity_refs,
            attributes=attributes,
        )

    @staticmethod
    def _connectivity_refs(model: Any) -> tuple[str, ...]:
        refs: list[str] = []
        for attribute in ("from_terminal", "to_terminal", "terminal"):
            value = getattr(model, attribute, None)
            if value is None:
                continue
            value_id = getattr(value, "id", None)
            if value_id is not None:
                refs.append(str(value_id))
        return tuple(dict.fromkeys(refs))

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


__all__ = ["NetworkReadService", "ReadService"]
