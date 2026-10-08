# ============================================================
# File: core/network/topology_endpoint_reference.py
# GridForge V2 — Topology Endpoint Identity
# Author: Subhendu Mishra
# ============================================================

"""Immutable connectivity-endpoint identity for Core topology."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from core.model.endpoint_reference import EndpointReference, EndpointReferenceKind


class TopologyEndpointReferenceKind(str, Enum):
    """Semantic kind of a connectivity endpoint."""

    TERMINAL = "terminal"


@dataclass(frozen=True, slots=True)
class TopologyEndpointReference:
    """Immutable identity of one endpoint participating in Core topology.

    The identity deliberately contains no mutable Core model object.  During
    this foundation migration only Terminal endpoints are representable.
    """

    kind: TopologyEndpointReferenceKind
    identity: EndpointReference

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TopologyEndpointReferenceKind):
            raise TypeError(
                "kind must be a TopologyEndpointReferenceKind."
            )
        if not isinstance(self.identity, EndpointReference):
            raise TypeError(
                "identity must be an EndpointReference."
            )
        if self.kind is TopologyEndpointReferenceKind.TERMINAL:
            if self.identity.kind is not EndpointReferenceKind.TERMINAL:
                raise ValueError(
                    "Terminal topology endpoints require a terminal EndpointReference."
                )
            return
        raise ValueError(
            f"Unsupported topology endpoint reference kind: {self.kind!r}."
        )

    @classmethod
    def from_terminal(
        cls,
        endpoint_reference: EndpointReference,
    ) -> "TopologyEndpointReference":
        """Convert the canonical Terminal identity without changing it."""
        if not isinstance(endpoint_reference, EndpointReference):
            raise TypeError(
                "from_terminal requires an EndpointReference."
            )
        if endpoint_reference.kind is not EndpointReferenceKind.TERMINAL:
            raise ValueError(
                "from_terminal requires a terminal EndpointReference."
            )
        return cls(
            kind=TopologyEndpointReferenceKind.TERMINAL,
            identity=endpoint_reference,
        )

    @property
    def endpoint_reference(self) -> EndpointReference:
        """Return the canonical underlying Terminal identity."""
        return self.identity

    @property
    def is_terminal(self) -> bool:
        return self.kind is TopologyEndpointReferenceKind.TERMINAL

    def to_mapping(self) -> Mapping[str, Any]:
        """Return the deterministic canonical Terminal identity mapping.

        The persisted/read-side shape intentionally remains the existing
        EndpointReference mapping so terminal-only projects remain semantically
        identical across this migration.
        """
        return self.identity.to_mapping()

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
    ) -> "TopologyEndpointReference":
        """Reconstruct a topology endpoint from its deterministic identity mapping."""
        if not isinstance(data, Mapping):
            raise TypeError(
                "Topology endpoint reference mapping must be a mapping."
            )
        if data.get("kind") != EndpointReferenceKind.TERMINAL.value:
            raise ValueError(
                "Only terminal topology endpoint mappings are supported."
            )
        from core.model import EquipmentType

        try:
            equipment_type = EquipmentType(
                str(data["equipment_type"]).strip().lower()
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "Topology terminal mapping contains an invalid equipment type."
            ) from exc

        try:
            endpoint = EndpointReference.terminal(
                equipment_type=equipment_type,
                equipment_id=data["object_id"],
                terminal_role=data["terminal_role"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "Topology terminal mapping is invalid."
            ) from exc
        return cls.from_terminal(endpoint)

    def __str__(self) -> str:
        return (
            "TopologyEndpointReference("
            f"{self.kind.value}:{self.identity})"
        )


__all__ = [
    "TopologyEndpointReference",
    "TopologyEndpointReferenceKind",
]
