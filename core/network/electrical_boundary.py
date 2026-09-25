from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.model import Branch, Breaker, Cable, Disconnector, Fuse, Line, Switch, Transformer
from core.model.endpoint_reference import EndpointReference, EndpointReferenceKind


class ElectricalBoundaryType(str, Enum):
    BUS_TERMINATION = "BUS_TERMINATION"
    SWITCHING_BOUNDARY = "SWITCHING_BOUNDARY"
    BRANCH_BOUNDARY = "BRANCH_BOUNDARY"


class EndpointCompatibilityError(ValueError):
    """Raised when endpoint identity or Simple Wire compatibility is invalid."""


@dataclass(frozen=True, slots=True)
class ElectricalBoundary:
    equipment_id: str
    terminal_role: str
    boundary_type: ElectricalBoundaryType
    attached_bus_id: str | None
    opposite_terminal: EndpointReference | None
    conductive: bool


class EndpointCompatibility:
    """Canonical Core endpoint compatibility and resolution contract."""

    _DOMAIN_ROLES = {
        "current_transformer": {"P1": "primary", "P2": "primary", "S1": "secondary", "S2": "secondary"},
        "potential_transformer": {"primary_a": "primary", "primary_b": "primary", "secondary_a": "secondary", "secondary_b": "secondary"},
        "capacitive_voltage_transformer": {"H1": "primary", "H2": "primary", "X1": "secondary", "X2": "secondary"},
    }

    @classmethod
    def validate_pair(cls, first: EndpointReference, second: EndpointReference, network: Any | None = None) -> None:
        if not isinstance(first, EndpointReference) or not isinstance(second, EndpointReference):
            raise EndpointCompatibilityError("Simple Wire endpoints must be EndpointReference values.")
        if first == second:
            raise EndpointCompatibilityError("A Simple Wire cannot connect an endpoint to itself.")
        if network is not None:
            cls.validate_reference(first, network)
            cls.validate_reference(second, network)
        if first.is_bus or second.is_bus:
            return
        if first.equipment_type == second.equipment_type and first.object_id == second.object_id:
            raise EndpointCompatibilityError("A Simple Wire cannot connect two terminals on the same equipment.")
        if cls.domain(first) != cls.domain(second):
            raise EndpointCompatibilityError("Terminal compatibility violation: endpoints belong to different electrical domains.")

    @classmethod
    def validate_reference(cls, reference: EndpointReference, network: Any) -> None:
        if not isinstance(reference, EndpointReference):
            raise EndpointCompatibilityError("Endpoint must be an EndpointReference.")
        if reference.is_bus:
            from core.model.bus import Bus
            try:
                bus = network.get_by_identity(reference.object_id)
            except KeyError as exc:
                raise EndpointCompatibilityError(f"Bus '{reference.object_id}' is not registered.") from exc
            if not isinstance(bus, Bus):
                raise EndpointCompatibilityError(f"Endpoint '{reference.object_id}' is not a registered Bus.")
            return
        if reference.equipment_type is None or not reference.terminal_role:
            raise EndpointCompatibilityError("Terminal endpoint requires equipment type and terminal role.")
        try:
            equipment = network.get_by_identity(reference.object_id)
        except KeyError as exc:
            raise EndpointCompatibilityError(f"Terminal equipment '{reference.object_id}' is not registered.") from exc
        expected = reference.equipment_type.value.strip().lower()
        actual = str(getattr(equipment, "element_type", "")).strip().lower()
        if actual != expected:
            raise EndpointCompatibilityError(f"Endpoint '{reference.object_id}' declares '{expected}' but resolves to '{actual}'.")
        matches = [t for t in getattr(equipment, "terminals", ()) if t.owner is equipment and t.role == reference.terminal_role]
        if len(matches) != 1:
            raise EndpointCompatibilityError(f"Endpoint {reference} must resolve to exactly one owned terminal.")

    @classmethod
    def domain(cls, reference: EndpointReference) -> str:
        if reference.equipment_type is None:
            return "generic"
        return cls._DOMAIN_ROLES.get(reference.equipment_type.value, {}).get(reference.terminal_role or "", "generic")


class ElectricalBoundaryResolver:
    """Canonical interpretation of physical attachment and conductive boundaries."""

    def __init__(self, network: Any) -> None:
        if network is None:
            raise ValueError("network is required.")
        self.network = network

    def resolve(self, reference: EndpointReference) -> ElectricalBoundary:
        EndpointCompatibility.validate_reference(reference, self.network)
        if reference.kind is EndpointReferenceKind.BUS:
            return ElectricalBoundary(reference.object_id, "bus", ElectricalBoundaryType.BUS_TERMINATION, reference.object_id, None, True)
        equipment = self.network.get_by_identity(reference.object_id)
        terminal = self._terminal(equipment, reference.terminal_role or "")
        attached_bus_id = self._attached_bus_id(terminal)
        from core.model import Breaker, Switch, Disconnector, Fuse, Branch, Line, Cable, Transformer
        if isinstance(equipment, (Breaker, Switch, Disconnector, Fuse)):
            opposite = self._opposite_reference(equipment, terminal)
            return ElectricalBoundary(equipment.id, terminal.role, ElectricalBoundaryType.SWITCHING_BOUNDARY, attached_bus_id, opposite, conduction_state(equipment))
        if isinstance(equipment, (Branch, Line, Cable, Transformer)):
            return ElectricalBoundary(equipment.id, terminal.role, ElectricalBoundaryType.BRANCH_BOUNDARY, attached_bus_id, None, conduction_state(equipment))
        return ElectricalBoundary(equipment.id, terminal.role, ElectricalBoundaryType.BUS_TERMINATION, attached_bus_id, None, True)

    @staticmethod
    def _terminal(equipment: Any, role: str) -> Any:
        matches = [t for t in getattr(equipment, "terminals", ()) if t.owner is equipment and t.role == role]
        if len(matches) != 1:
            raise EndpointCompatibilityError(f"Equipment '{equipment.id}' terminal role '{role}' is not uniquely registered.")
        return matches[0]

    @staticmethod
    def _attached_bus_id(terminal: Any) -> str | None:
        endpoint = getattr(terminal, "endpoint", None)
        if endpoint is None:
            return None
        from core.model.bus import Bus
        if isinstance(endpoint, Bus):
            return endpoint.id
        raise EndpointCompatibilityError(f"Terminal '{terminal.role}' on '{terminal.owner.id}' has a non-Bus physical endpoint.")

    @staticmethod
    def _opposite_reference(equipment: Any, terminal: Any) -> EndpointReference:
        candidates = tuple(t for t in getattr(equipment, "terminals", ()) if t.owner is equipment and t is not terminal)
        if len(candidates) != 1:
            raise EndpointCompatibilityError(f"Equipment '{equipment.id}' does not expose exactly one authoritative opposite terminal.")
        from core.model.endpoint_reference import EquipmentType
        try:
            equipment_type = EquipmentType(str(equipment.element_type).strip().lower())
        except ValueError as exc:
            raise EndpointCompatibilityError(f"Unsupported switching equipment type '{equipment.element_type}'.") from exc
        return EndpointReference.terminal(equipment_type=equipment_type, equipment_id=equipment.id, terminal_role=candidates[0].role)


def conduction_state(element: Any) -> bool:
    """Reusable present conduction contract."""
    conducts = getattr(element, "conducts", None)
    if conducts is not None:
        return bool(conducts)
    if isinstance(element, (Branch, Line, Cable, Transformer)):
        return bool(getattr(element, "in_service", False))
    if isinstance(element, Breaker):
        return bool(getattr(element, "in_service", False)) and bool(getattr(element, "closed", False)) and not bool(getattr(element, "failed", False))
    if isinstance(element, (Switch, Disconnector)):
        return bool(getattr(element, "in_service", False)) and bool(getattr(element, "closed", False))
    if isinstance(element, Fuse):
        return bool(getattr(element, "in_service", False)) and not bool(getattr(element, "blown", False))
    return False


__all__=["ElectricalBoundary","ElectricalBoundaryResolver","ElectricalBoundaryType","EndpointCompatibility","EndpointCompatibilityError","conduction_state"]
