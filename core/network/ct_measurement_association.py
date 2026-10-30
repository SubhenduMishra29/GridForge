# ============================================================
# File: core/network/ct_measurement_association.py
# GridForge V2 — CT Measurement Association
# Author: Subhendu Mishra
# ============================================================

"""Resolve CT primary placement against authoritative Core connectivity.

The resolver consumes committed Network membership and terminal connectivity.
It never reads SLD graphics, canvas geometry, or UI state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.model import CurrentTransformer, EndpointReference, EquipmentType
from .connectivity import ConnectivityError, ConnectivityResolver
from .network import Network


class CTMeasurementAssociationError(ValueError):
    """Raised when a CT primary measurement location cannot be resolved safely."""


class CTMeasurementAssociationStatus(str, Enum):
    """Strength of the CT-to-network equipment correlation."""

    RESOLVED = "RESOLVED"
    LOCATION_ONLY = "LOCATION_ONLY"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class CTMeasurementAssociation:
    """Immutable result of resolving one CT's primary measurement location."""

    ct_id: str
    in_service: bool
    p1_bus_id: str
    p2_bus_id: str
    positive_current_direction: str
    monitored_equipment_id: str | None
    candidate_equipment_ids: tuple[str, ...]
    status: CTMeasurementAssociationStatus
    topology_revision: int

    def __post_init__(self) -> None:
        for name in ("ct_id", "p1_bus_id", "p2_bus_id", "positive_current_direction"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        if not isinstance(self.in_service, bool):
            raise TypeError("in_service must be a boolean.")
        if self.p1_bus_id == self.p2_bus_id:
            raise ValueError("A CT primary measurement location must span two distinct Buses.")
        candidates = tuple(self.candidate_equipment_ids)
        if any(not isinstance(value, str) or not value.strip() for value in candidates):
            raise ValueError("candidate_equipment_ids must contain non-empty identities.")
        if candidates != tuple(sorted(set(candidates))):
            raise ValueError("candidate_equipment_ids must be unique and deterministically ordered.")
        object.__setattr__(self, "candidate_equipment_ids", candidates)
        if not isinstance(self.status, CTMeasurementAssociationStatus):
            raise TypeError("status must be a CTMeasurementAssociationStatus.")
        if self.status is CTMeasurementAssociationStatus.RESOLVED:
            if self.monitored_equipment_id is None or candidates != (self.monitored_equipment_id,):
                raise ValueError("RESOLVED association requires exactly one monitored equipment candidate.")
        elif self.monitored_equipment_id is not None:
            raise ValueError("Only a RESOLVED association may identify monitored_equipment_id.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")


class CTMeasurementAssociationResolver:
    """Resolve a CurrentTransformer's P1/P2 terminals to network measurement location.

    A unique two-terminal line, cable, or transformer spanning the same pair
    of primary-side Buses is returned as monitored equipment. No candidate
    produces LOCATION_ONLY; multiple candidates produce AMBIGUOUS. The
    resolver never picks an arbitrary candidate.
    """

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Core Network.")
        self._network = network
        self._connectivity = ConnectivityResolver(network)

    def resolve(self, ct: CurrentTransformer | str) -> CTMeasurementAssociation:
        """Resolve one registered CT using its authoritative P1/P2 connectivity."""
        if isinstance(ct, str):
            if not ct.strip():
                raise ValueError("ct_id must be a non-empty string.")
            try:
                ct = self._network.get_by_identity(ct.strip())
            except KeyError as exc:
                raise CTMeasurementAssociationError(
                    f"CurrentTransformer '{ct}' is not registered in the Network."
                ) from exc
        if not isinstance(ct, CurrentTransformer):
            raise TypeError("ct must be a CurrentTransformer or registered CT identity.")
        try:
            registered = self._network.get_by_identity(ct.id)
        except KeyError as exc:
            raise CTMeasurementAssociationError(
                f"CurrentTransformer '{ct.id}' is not registered in the Network."
            ) from exc
        if registered is not ct:
            raise CTMeasurementAssociationError(
                f"CurrentTransformer '{ct.id}' does not resolve to the supplied canonical Network object."
            )
        p1_bus_id = self._resolve_primary_bus(ct, "P1", ct.p1_terminal)
        p2_bus_id = self._resolve_primary_bus(ct, "P2", ct.p2_terminal)
        if p1_bus_id == p2_bus_id:
            raise CTMeasurementAssociationError(
                f"CurrentTransformer '{ct.id}' primary terminals resolve to the same Bus '{p1_bus_id}'."
            )

        candidates = self._find_monitored_equipment(p1_bus_id, p2_bus_id)
        if len(candidates) == 1:
            status = CTMeasurementAssociationStatus.RESOLVED
            monitored_id = candidates[0]
        elif candidates:
            status = CTMeasurementAssociationStatus.AMBIGUOUS
            monitored_id = None
        else:
            status = CTMeasurementAssociationStatus.LOCATION_ONLY
            monitored_id = None

        direction = "P1_TO_P2" if ct.polarity.value == "P1_P2" else "P2_TO_P1"
        return CTMeasurementAssociation(
            ct_id=ct.id,
            in_service=ct.in_service,
            p1_bus_id=p1_bus_id,
            p2_bus_id=p2_bus_id,
            positive_current_direction=direction,
            monitored_equipment_id=monitored_id,
            candidate_equipment_ids=candidates,
            status=status,
            topology_revision=self._network.state.topology_revision,
        )

    def resolve_all(self) -> tuple[CTMeasurementAssociation, ...]:
        """Return deterministic associations for all registered CTs."""
        return tuple(
            self.resolve(ct)
            for ct in sorted(self._network.current_transformers, key=lambda item: item.id)
        )

    def _resolve_primary_bus(self, ct: CurrentTransformer, role: str, terminal: Any) -> str:
        if terminal.owner is not ct or terminal.role != role:
            raise CTMeasurementAssociationError(
                f"CurrentTransformer '{ct.id}' has an invalid authoritative {role} terminal."
            )
        reference = self._terminal_reference(ct, role)
        try:
            bus_ids = self._connectivity.bus_ids_for_terminal(reference)
        except (ConnectivityError, KeyError, TypeError, ValueError) as exc:
            raise CTMeasurementAssociationError(
                f"Could not resolve CurrentTransformer '{ct.id}' {role} connectivity: {exc}"
            ) from exc
        if len(bus_ids) != 1:
            detail = "unconnected" if not bus_ids else f"connected to multiple Buses {bus_ids!r}"
            raise CTMeasurementAssociationError(
                f"CurrentTransformer '{ct.id}' primary terminal {role} is {detail}."
            )
        return bus_ids[0]

    def _find_monitored_equipment(self, p1_bus_id: str, p2_bus_id: str) -> tuple[str, ...]:
        """Find supported two-terminal network elements spanning the CT Bus pair."""
        matches: set[str] = set()
        for group in (self._network.lines, self._network.cables, self._network.transformers):
            for equipment in group:
                terminals = tuple(getattr(equipment, "terminals", ()))
                if len(terminals) != 2:
                    continue
                terminal_buses: list[str] = []
                for terminal in terminals:
                    if terminal.owner is not equipment:
                        break
                    reference = self._terminal_reference(equipment, terminal.role)
                    try:
                        buses = self._connectivity.bus_ids_for_terminal(reference)
                    except (ConnectivityError, KeyError, TypeError, ValueError):
                        break
                    if len(buses) != 1:
                        break
                    terminal_buses.append(buses[0])
                if len(terminal_buses) == 2 and set(terminal_buses) == {p1_bus_id, p2_bus_id}:
                    matches.add(equipment.id)
        return tuple(sorted(matches))

    @staticmethod
    def _terminal_reference(equipment: Any, role: str) -> EndpointReference:
        raw_type = str(getattr(equipment, "element_type", "")).strip().lower()
        if raw_type == "electrical_object":
            raw_type = type(equipment).__name__.strip().lower()
        try:
            equipment_type = EquipmentType(raw_type)
        except (TypeError, ValueError) as exc:
            raise CTMeasurementAssociationError(
                f"Equipment '{getattr(equipment, 'id', '<unknown>')}' has no supported terminal EquipmentType."
            ) from exc
        return EndpointReference.terminal(
            equipment_type=equipment_type,
            equipment_id=equipment.id,
            terminal_role=role,
        )


__all__ = [
    "CTMeasurementAssociation",
    "CTMeasurementAssociationError",
    "CTMeasurementAssociationResolver",
    "CTMeasurementAssociationStatus",
]
