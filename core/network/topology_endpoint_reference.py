# ============================================================
# File: core/network/topology_endpoint_reference.py
# GridForge V2 — Topology Endpoint Identity
# Author: Subhendu Mishra
# ============================================================

"""Immutable topology-level endpoint identities for Core connectivity."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from core.model.endpoint_reference import EndpointReference, EndpointReferenceKind


class TopologyEndpointReferenceKind(str, Enum):
    """Semantic kind of a topology endpoint."""

    TERMINAL = "terminal"
    JUNCTION = "junction"


@dataclass(frozen=True, slots=True)
class TopologyEndpointReference:
    """Immutable identity of one endpoint participating in Core topology.

    EndpointReference remains the canonical equipment-terminal identity.
    This type owns the topology discriminator so future topology primitives
    do not need to masquerade as electrical terminals.

    Current connectivity supports only TERMINAL references. JUNCTION is a
    structural identity contract only; it does not resolve to or contain a
    Junction Core object.
    """

    kind: TopologyEndpointReferenceKind
    terminal_reference: EndpointReference | None = None
    junction_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TopologyEndpointReferenceKind):
            raise TypeError("kind must be a TopologyEndpointReferenceKind.")

        if self.kind is TopologyEndpointReferenceKind.TERMINAL:
            if not isinstance(self.terminal_reference, EndpointReference):
                raise TypeError(
                    "terminal_reference must be an EndpointReference for "
                    "a terminal topology endpoint."
                )
            if self.terminal_reference.kind is not EndpointReferenceKind.TERMINAL:
                raise ValueError(
                    "Terminal topology endpoints require a terminal EndpointReference."
                )
            if self.junction_id is not None:
                raise ValueError(
                    "junction_id must be None for a terminal topology endpoint."
                )
            return

        if self.kind is TopologyEndpointReferenceKind.JUNCTION:
            if (
                not isinstance(self.junction_id, str)
                or not self.junction_id.strip()
            ):
                raise ValueError(
                    "junction_id must be a non-empty string for a junction "
                    "topology endpoint."
                )
            object.__setattr__(self, "junction_id", self.junction_id.strip())
            if self.terminal_reference is not None:
                raise ValueError(
                    "terminal_reference must be None for a junction "
                    "topology endpoint."
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
        """Wrap exactly one existing Terminal EndpointReference."""
        if not isinstance(endpoint_reference, EndpointReference):
            raise TypeError("from_terminal requires an EndpointReference.")
        if endpoint_reference.kind is not EndpointReferenceKind.TERMINAL:
            raise ValueError(
                "from_terminal requires a terminal EndpointReference."
            )
        return cls(
            kind=TopologyEndpointReferenceKind.TERMINAL,
            terminal_reference=endpoint_reference,
        )

    @classmethod
    def from_junction(cls, junction_id: str) -> "TopologyEndpointReference":
        """Create an immutable Junction topology identity from canonical ID."""
        return cls(
            kind=TopologyEndpointReferenceKind.JUNCTION,
            junction_id=junction_id,
        )

    @classmethod
    def junction(cls, junction_id: str) -> "TopologyEndpointReference":
        """Compatibility alias for from_junction."""
        return cls.from_junction(junction_id)

    @property
    def identity(self) -> EndpointReference | str:
        """Return the immutable identity payload for this topology endpoint."""
        if self.is_terminal:
            return self.terminal_reference
        return self.junction_id

    @property
    def endpoint_reference(self) -> EndpointReference:
        """Return the Terminal identity for terminal-only compatibility callers."""
        if not self.is_terminal:
            raise ValueError(
                "Junction topology endpoints do not expose an EndpointReference."
            )
        return self.terminal_reference

    @property
    def is_terminal(self) -> bool:
        return self.kind is TopologyEndpointReferenceKind.TERMINAL

    @property
    def is_junction(self) -> bool:
        return self.kind is TopologyEndpointReferenceKind.JUNCTION

    def to_mapping(self) -> Mapping[str, Any]:
        """Return the explicit, discriminator-led persistence/read-model form."""
        if self.is_terminal:
            return {
                "kind": self.kind.value,
                "endpoint": dict(self.terminal_reference.to_mapping()),
            }
        return {
            "kind": self.kind.value,
            "junction_id": self.junction_id,
        }

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
    ) -> "TopologyEndpointReference":
        """Reconstruct a topology endpoint without inferring unknown kinds."""
        if not isinstance(data, Mapping):
            raise TypeError(
                "Topology endpoint reference mapping must be a mapping."
            )

        kind = data.get("kind")
        if kind == TopologyEndpointReferenceKind.TERMINAL.value:
            endpoint_data = data.get("endpoint")

            # Compatibility with the pre-migration terminal mapping.
            if endpoint_data is None:
                endpoint_data = data

            if not isinstance(endpoint_data, Mapping):
                raise ValueError(
                    "Terminal topology endpoint mapping must contain an endpoint object."
                )
            if endpoint_data.get("kind") != EndpointReferenceKind.TERMINAL.value:
                raise ValueError(
                    "Terminal topology endpoint must contain a terminal EndpointReference."
                )

            from core.model import EquipmentType

            try:
                equipment_type = EquipmentType(
                    str(endpoint_data["equipment_type"]).strip().lower()
                )
                endpoint = EndpointReference.terminal(
                    equipment_type=equipment_type,
                    equipment_id=endpoint_data["object_id"],
                    terminal_role=endpoint_data["terminal_role"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    "Topology terminal mapping is invalid."
                ) from exc
            return cls.from_terminal(endpoint)

        if kind == TopologyEndpointReferenceKind.JUNCTION.value:
            return cls.junction(data.get("junction_id"))

        raise ValueError(
            f"Unsupported topology endpoint reference kind: {kind!r}."
        )

    def __str__(self) -> str:
        if self.is_terminal:
            return (
                "TopologyEndpointReference("
                f"terminal:{self.terminal_reference})"
            )
        return (
            "TopologyEndpointReference("
            f"junction:{self.junction_id})"
        )


__all__ = [
    "TopologyEndpointReference",
    "TopologyEndpointReferenceKind",
]
