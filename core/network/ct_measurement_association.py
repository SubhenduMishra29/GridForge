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
from .topology_endpoint_reference import TopologyEndpointReference


@dataclass(frozen=True, slots=True)
class CTMeasurementAssociation:
    """Immutable CT terminal association derived from canonical connectivity."""

    ct_id: str
    p1_terminal_reference: EndpointReference
    p1_component: tuple[TopologyEndpointReference, ...]
    p2_terminal_reference: EndpointReference
    p2_component: tuple[TopologyEndpointReference, ...]
    s1_terminal_reference: EndpointReference
    s2_terminal_reference: EndpointReference
    positive_current_direction: str
    in_service: bool
    topology_revision: int

    def branch_current_direction(
        self,
        branch_terminal_reference: EndpointReference,
        branch_side: str,
    ) -> int:
        """Return branch-current sign relative to physical CT P1->P2.

        The CT is inserted inline on a SimpleWire. Its primary terminals
        therefore identify separate topology components, not necessarily
        separate Bus IDs. The configured Branch terminal must belong to
        exactly one of those components.

        Positive branch current is FROM->TO. For a FROM-side CT, P2 must
        face the Branch terminal for P1->P2 to agree with positive current.
        For a TO-side CT, P1 must face the Branch terminal.
        """
        if not isinstance(branch_terminal_reference, EndpointReference) or not branch_terminal_reference.is_terminal:
            raise TypeError("branch_terminal_reference must be a terminal EndpointReference.")
        if not isinstance(branch_side, str) or branch_side.strip().upper() not in {"FROM", "TO"}:
            raise ValueError("branch_side must be explicitly FROM or TO.")
        side = branch_side.strip().upper()
        expected_role = side
        if branch_terminal_reference.terminal_role != expected_role:
            raise ValueError(
                f"Branch side {side!r} does not match terminal role "
                f"{branch_terminal_reference.terminal_role!r}."
            )
        topology_reference = TopologyEndpointReference.from_terminal(branch_terminal_reference)
        p1_matches = topology_reference in self.p1_component
        p2_matches = topology_reference in self.p2_component
        if p1_matches == p2_matches:
            raise ValueError(
                f"Configured Branch terminal {branch_terminal_reference!r} must belong to "
                f"exactly one primary topology component of CT {self.ct_id!r}."
            )
        ct_terminal_at_branch = "P1" if p1_matches else "P2"
        if side == "FROM":
            return 1 if ct_terminal_at_branch == "P2" else -1
        return 1 if ct_terminal_at_branch == "P1" else -1

    def __post_init__(self) -> None:
        if not isinstance(self.ct_id, str) or not self.ct_id.strip():
            raise ValueError("ct_id must be a non-empty string.")
        object.__setattr__(self, "ct_id", self.ct_id.strip())
        if not isinstance(self.positive_current_direction, str) or not self.positive_current_direction.strip():
            raise ValueError("positive_current_direction must be a non-empty string.")
        object.__setattr__(self, "positive_current_direction", self.positive_current_direction.strip())
        for name in ("p1_component", "p2_component"):
            component = tuple(getattr(self, name))
            if not component or any(not isinstance(item, TopologyEndpointReference) for item in component):
                raise TypeError(f"{name} must contain canonical topology endpoint references.")
            object.__setattr__(self, name, component)
        p1_set = set(self.p1_component)
        p2_set = set(self.p2_component)
        if p1_set & p2_set:
            raise ValueError("CT P1 and P2 must resolve to distinct SimpleWire topology components.")
        if TopologyEndpointReference.from_terminal(self.p1_terminal_reference) not in p1_set:
            raise ValueError("P1 topology component must contain the canonical CT P1 terminal.")
        if TopologyEndpointReference.from_terminal(self.p2_terminal_reference) not in p2_set:
            raise ValueError("P2 topology component must contain the canonical CT P2 terminal.")
        if any(item.is_junction for item in self.p1_component + self.p2_component):
            raise ValueError("CT primary SimpleWire components must not traverse a Junction.")
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
        p1_component = self._resolve_primary_component(ct, p1)
        p2_component = self._resolve_primary_component(ct, p2)
        if set(p1_component) & set(p2_component):
            raise ValueError(
                f"CT {ct.id!r} P1 and P2 resolve to the same SimpleWire topology component."
            )

        polarity = getattr(ct.polarity, "value", ct.polarity)
        if polarity not in {"P1_P2", "P2_P1"}:
            raise ValueError(f"CT {ct.id!r} has unsupported polarity {polarity!r}.")
        return CTMeasurementAssociation(
            ct_id=ct.id,
            p1_terminal_reference=p1,
            p1_component=p1_component,
            p2_terminal_reference=p2,
            p2_component=p2_component,
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

    def _resolve_primary_component(
        self,
        ct: CurrentTransformer,
        reference: EndpointReference,
    ) -> tuple[TopologyEndpointReference, ...]:
        try:
            component = self._connectivity.topology_component(
                TopologyEndpointReference.from_terminal(reference)
            )
        except (ConnectivityError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Could not resolve CT {ct.id!r} {reference.terminal_role} SimpleWire component: {exc}"
            ) from exc
        if len(component) < 2:
            raise ValueError(
                f"CT {ct.id!r} primary terminal {reference.terminal_role} is not connected "
                "through a committed SimpleWire relationship."
            )
        return component

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
