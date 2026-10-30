# ============================================================
# File: core/network/ct_measurement_association.py
# GridForge V2 — CT Measurement Association
# Author: Subhendu Mishra
# ============================================================

"""Resolve configured CT primary and secondary terminal references.

P1/P2 identify the primary electrical measurement location through committed
Core connectivity. S1/S2 identify the physical secondary circuit terminals
available to measurement-channel provisioning.

This resolver does not infer a protected feeder, protection zone, relay input,
or trip target. Those are explicit engineering configuration contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.model import CurrentTransformer, EndpointReference, EquipmentType
from .connectivity import ConnectivityError, ConnectivityResolver
from .network import Network


@dataclass(frozen=True, slots=True)
class CTMeasurementAssociation:
    """Immutable CT terminal association derived from canonical connectivity."""

    ct_id: str
    p1_terminal_reference: EndpointReference
    p1_bus_id: str
    p2_terminal_reference: EndpointReference
    p2_bus_id: str
    s1_terminal_reference: EndpointReference
    s2_terminal_reference: EndpointReference
    positive_current_direction: str
    in_service: bool
    topology_revision: int

    def branch_current_direction(self, from_bus_id: str, to_bus_id: str) -> int:
        """Return branch-reference sign relative to configured CT P1->P2.

        +1 means branch from/to follows P1->P2; -1 means it is reversed.
        The branch must terminate at the exact two Buses resolved from the
        CT's canonical primary terminals. CT polarity is intentionally not
        included here; MeasurementGeneration applies that physical polarity
        separately exactly once.
        """
        for name, value in (("from_bus_id", from_bus_id), ("to_bus_id", to_bus_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty Bus identity.")
        from_bus_id = from_bus_id.strip()
        to_bus_id = to_bus_id.strip()
        if from_bus_id == self.p1_bus_id and to_bus_id == self.p2_bus_id:
            return 1
        if from_bus_id == self.p2_bus_id and to_bus_id == self.p1_bus_id:
            return -1
        raise ValueError(
            f"Branch terminals {from_bus_id!r}->{to_bus_id!r} do not match "
            f"CT {self.ct_id!r} primary measurement boundary "
            f"{self.p1_bus_id!r}<->{self.p2_bus_id!r}."
        )

    def __post_init__(self) -> None:
        if not isinstance(self.ct_id, str) or not self.ct_id.strip():
            raise ValueError("ct_id must be a non-empty string.")
        object.__setattr__(self, "ct_id", self.ct_id.strip())
        for name in ("p1_bus_id", "p2_bus_id", "positive_current_direction"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        if self.p1_bus_id == self.p2_bus_id:
            raise ValueError("CT primary terminals must resolve to distinct Bus locations.")
        expected_roles = {
            "p1_terminal_reference": "P1",
            "p2_terminal_reference": "P2",
            "s1_terminal_reference": "S1",
            "s2_terminal_reference": "S2",
        }
        for name, role in expected_roles.items():
            reference = getattr(self, name)
            if not isinstance(reference, EndpointReference) or not reference.is_terminal:
                raise TypeError(f"{name} must be a terminal EndpointReference.")
            if reference.equipment_id != self.ct_id or reference.terminal_role != role:
                raise ValueError(f"{name} must identify CT {self.ct_id!r} terminal {role}.")
        if self.positive_current_direction not in {"P1_TO_P2", "P2_TO_P1"}:
            raise ValueError("positive_current_direction must be P1_TO_P2 or P2_TO_P1.")
        if not isinstance(self.in_service, bool):
            raise TypeError("in_service must be a boolean.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")


class CTMeasurementAssociationResolver:
    """Resolve CT terminal locations without guessing protection ownership."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Core Network.")
        self._network = network
        self._connectivity = ConnectivityResolver(network)

    def resolve(self, ct: CurrentTransformer | str) -> CTMeasurementAssociation:
        """Resolve one registered CT from authoritative primary connectivity."""
        if isinstance(ct, str):
            if not ct.strip():
                raise ValueError("ct_id must be a non-empty string.")
            try:
                ct = self._network.get_by_identity(ct.strip())
            except KeyError as exc:
                raise ValueError(f"CurrentTransformer {ct!r} is not registered in the Network.") from exc
        if not isinstance(ct, CurrentTransformer):
            raise TypeError("ct must be a CurrentTransformer or registered CT identity.")
        try:
            registered = self._network.get_by_identity(ct.id)
        except KeyError as exc:
            raise ValueError(f"CurrentTransformer {ct.id!r} is not registered in the Network.") from exc
        if registered is not ct:
            raise ValueError(
                f"CurrentTransformer {ct.id!r} is not the canonical object registered in the Network."
            )

        p1 = self._terminal_reference(ct, "P1")
        p2 = self._terminal_reference(ct, "P2")
        s1 = self._terminal_reference(ct, "S1")
        s2 = self._terminal_reference(ct, "S2")
        p1_bus = self._resolve_primary_bus(ct, p1)
        p2_bus = self._resolve_primary_bus(ct, p2)
        if p1_bus == p2_bus:
            raise ValueError(
                f"CT {ct.id!r} P1 and P2 resolve to the same Bus {p1_bus!r}; "
                "the primary measurement location is not distinguishable."
            )

        polarity = getattr(ct.polarity, "value", ct.polarity)
        if polarity not in {"P1_P2", "P2_P1"}:
            raise ValueError(f"CT {ct.id!r} has unsupported polarity {polarity!r}.")
        return CTMeasurementAssociation(
            ct_id=ct.id,
            p1_terminal_reference=p1,
            p1_bus_id=p1_bus,
            p2_terminal_reference=p2,
            p2_bus_id=p2_bus,
            s1_terminal_reference=s1,
            s2_terminal_reference=s2,
            positive_current_direction="P1_TO_P2" if polarity == "P1_P2" else "P2_TO_P1",
            in_service=bool(ct.in_service),
            topology_revision=self._network.state.topology_revision,
        )

    def resolve_all(self) -> tuple[CTMeasurementAssociation, ...]:
        """Return deterministic associations for all registered CTs."""
        return tuple(
            self.resolve(ct)
            for ct in sorted(self._network.current_transformers, key=lambda item: item.id)
        )

    def _resolve_primary_bus(self, ct: CurrentTransformer, reference: EndpointReference) -> str:
        try:
            bus_ids = self._connectivity.bus_ids_for_terminal(reference)
        except (ConnectivityError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Could not resolve CT {ct.id!r} {reference.terminal_role} connectivity: {exc}"
            ) from exc
        if len(bus_ids) != 1:
            detail = "unconnected" if not bus_ids else f"connected to multiple Buses {bus_ids!r}"
            raise ValueError(f"CT {ct.id!r} primary terminal {reference.terminal_role} is {detail}.")
        return bus_ids[0]

    @staticmethod
    def _terminal_reference(ct: CurrentTransformer, role: str) -> EndpointReference:
        terminal = getattr(ct, f"{role.lower()}_terminal")
        if terminal.owner is not ct or terminal.role != role:
            raise ValueError(f"CT {ct.id!r} has an invalid authoritative {role} terminal.")
        return EndpointReference.terminal(
            equipment_type=EquipmentType.CURRENTTRANSFORMER,
            equipment_id=ct.id,
            terminal_role=role,
        )


__all__ = [
    "CTMeasurementAssociation",
    "CTMeasurementAssociationResolver",
]
