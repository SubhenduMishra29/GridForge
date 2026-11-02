"""Explicit ANSI 21 protected-line and breaker/CT boundary ownership contract.

The contract is intentionally distance-function-specific. It records the
physical protected line ends and CT/breaker boundaries; it does not treat
impedance Zones 1/2/3 as separate physical protection zones.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.model import Breaker, Cable, CVT, EndpointReference, Line, PT
from core.model.endpoint_reference import EquipmentType
from core.network.conductive_reachability import ConductiveReachabilityResolver
from core.network.ct_measurement_association import CTMeasurementAssociationResolver


@dataclass(frozen=True, slots=True)
class DistanceProtectionCoverage:
    coverage_id: str
    protected_equipment_id: str
    from_ct_id: str
    from_ct_line_side: str
    from_breaker_id: str
    from_breaker_terminal_role: str
    to_ct_id: str
    to_ct_line_side: str
    to_breaker_id: str
    to_breaker_terminal_role: str
    local_end: str
    current_binding_id: str
    voltage_binding_id: str
    project_id: str
    activation_generation: int
    topology_revision: int

    def __post_init__(self) -> None:
        string_fields = (
            "coverage_id", "protected_equipment_id", "from_ct_id",
            "from_breaker_id", "from_breaker_terminal_role", "to_ct_id",
            "to_breaker_id", "to_breaker_terminal_role", "current_binding_id",
            "voltage_binding_id", "project_id",
        )
        for name in string_fields:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a canonical non-empty string.")
        for name in ("from_ct_line_side", "to_ct_line_side"):
            value = getattr(self, name)
            if value not in {"P1_SIDE", "P2_SIDE"}:
                raise ValueError(f"{name} must explicitly be P1_SIDE or P2_SIDE.")
        if self.local_end not in {"FROM", "TO"}:
            raise ValueError("local_end must be explicitly FROM or TO.")
        if self.from_ct_id == self.to_ct_id or self.from_breaker_id == self.to_breaker_id:
            raise ValueError("A two-ended distance coverage requires distinct CTs and breakers.")
        if self.from_breaker_terminal_role == self.to_breaker_terminal_role and self.from_breaker_id == self.to_breaker_id:
            raise ValueError("The two breaker boundaries cannot be the same terminal.")
        for name in ("activation_generation",):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "DistanceProtectionCoverage":
        if not isinstance(data, Mapping):
            raise TypeError("distance_coverage must be a mapping.")
        required = {
            "coverage_id", "protected_equipment_id", "from_ct_id", "from_ct_line_side",
            "from_breaker_id", "from_breaker_terminal_role", "to_ct_id", "to_ct_line_side",
            "to_breaker_id", "to_breaker_terminal_role", "local_end", "current_binding_id",
            "voltage_binding_id", "project_id", "activation_generation", "topology_revision",
        }
        if set(data) != required:
            raise ValueError(
                f"distance_coverage requires exactly {sorted(required)!r}; "
                f"received {sorted(data)!r}."
            )
        return cls(**{key: data[key] for key in required})

    def to_dict(self) -> dict[str, Any]:
        return {
            name: getattr(self, name)
            for name in (
                "coverage_id", "protected_equipment_id", "from_ct_id", "from_ct_line_side",
                "from_breaker_id", "from_breaker_terminal_role", "to_ct_id", "to_ct_line_side",
                "to_breaker_id", "to_breaker_terminal_role", "local_end", "current_binding_id",
                "voltage_binding_id", "project_id", "activation_generation", "topology_revision",
            )
        }

    def validate(
        self,
        network: Any,
        *,
        project_id: str,
        activation_generation: int,
        topology_revision: int,
        current_binding: Any,
        voltage_binding: Any,
    ) -> None:
        """Prove both physical CT/breaker boundaries and local PT/CVT association."""
        if self.project_id != project_id or self.activation_generation != activation_generation:
            raise ValueError("Distance coverage belongs to a different project activation.")
        if self.topology_revision != topology_revision or network.state.topology_revision != topology_revision:
            raise ValueError("Distance coverage topology revision is stale.")
        protected = network.get_by_identity(self.protected_equipment_id)
        if not isinstance(protected, (Line, Cable)):
            raise ValueError("ANSI 21 coverage must identify one canonical Line or Cable.")
        line_type = EquipmentType.LINE if isinstance(protected, Line) else EquipmentType.CABLE
        line_endpoints = {
            "FROM": EndpointReference.terminal(equipment_type=line_type, equipment_id=protected.id, terminal_role="FROM"),
            "TO": EndpointReference.terminal(equipment_type=line_type, equipment_id=protected.id, terminal_role="TO"),
        }
        associations = CTMeasurementAssociationResolver(network)
        reachability = ConductiveReachabilityResolver(network)
        boundary_specs = (
            ("FROM", self.from_ct_id, self.from_ct_line_side, self.from_breaker_id, self.from_breaker_terminal_role),
            ("TO", self.to_ct_id, self.to_ct_line_side, self.to_breaker_id, self.to_breaker_terminal_role),
        )
        for end, ct_id, declared_line_side, breaker_id, breaker_role in boundary_specs:
            ct = network.get_by_identity(ct_id)
            breaker = network.get_by_identity(breaker_id)
            if not isinstance(breaker, Breaker):
                raise ValueError(f"{end} boundary equipment {breaker_id!r} is not a canonical Breaker.")
            if not bool(getattr(ct, "in_service", False)):
                raise ValueError(f"{end} boundary CT {ct_id!r} is out of service.")
            association = associations.resolve(ct)
            if association.locate_measurement_endpoint(line_endpoints[end]) != declared_line_side:
                raise ValueError(f"{end} boundary CT {ct_id!r} line-side declaration contradicts committed topology.")
            line_side_terminal = association.p1_terminal_reference if declared_line_side == "P1_SIDE" else association.p2_terminal_reference
            external_terminal = association.p2_terminal_reference if declared_line_side == "P1_SIDE" else association.p1_terminal_reference
            breaker_type = EquipmentType.BREAKER
            breaker_endpoint = EndpointReference.terminal(
                equipment_type=breaker_type, equipment_id=breaker_id, terminal_role=breaker_role
            )
            path = reachability.resolve_path(
                external_terminal, breaker_endpoint, excluded_equipment_ids=frozenset({ct_id})
            )
            line_side_path = reachability.resolve_path(
                line_endpoints[end], line_side_terminal,
                excluded_equipment_ids=frozenset({ct_id}),
            )
            if line_side_path is None:
                raise ValueError(
                    f"{end} protected Line/Cable terminal is not connected to the declared "
                    f"CT {ct_id!r} line-side terminal without traversing the CT."
                )
            bypass_path = reachability.resolve_path(
                line_endpoints[end], breaker_endpoint,
                excluded_equipment_ids=frozenset({ct_id}),
            )
            if bypass_path is not None:
                raise ValueError(
                    f"{end} breaker boundary {breaker_id!r} can be reached from the protected "
                    f"line end while CT {ct_id!r} is excluded; the declared CT is not a unique "
                    "physical cut boundary in the active topology."
                )
            if path is None:
                raise ValueError(
                    f"{end} boundary CT {ct_id!r} external primary side is not conductively connected "
                    f"to configured breaker terminal {breaker_id}:{breaker_role} when the CT is treated as a cut boundary."
                )
            # The line-side CT terminal must be in the same committed primary
            # wire component as the protected Line/Cable terminal.
            if line_side_terminal not in association.p1_component + association.p2_component:
                raise ValueError(f"{end} CT line-side primary terminal is not part of its canonical topology component.")

        expected_local_ct = self.from_ct_id if self.local_end == "FROM" else self.to_ct_id
        if current_binding.instrument_id != expected_local_ct:
            raise ValueError("ANSI 21 current binding instrument must be the CT at the configured local line end.")
        if current_binding.source_equipment_id != self.protected_equipment_id:
            raise ValueError("ANSI 21 current binding must identify the protected Line/Cable as its measured source equipment.")
        if (
            not current_binding.source_endpoint_reference.is_terminal
            or current_binding.source_endpoint_reference.object_id != self.protected_equipment_id
            or current_binding.source_endpoint_reference.terminal_role != self.local_end
        ):
            raise ValueError("ANSI 21 current binding source endpoint must be the configured local terminal of the protected Line/Cable.")
        if current_binding.binding_id != self.current_binding_id:
            raise ValueError("ANSI 21 current binding identity does not match distance coverage.")
        if voltage_binding.binding_id != self.voltage_binding_id:
            raise ValueError("ANSI 21 voltage binding identity does not match distance coverage.")
        if voltage_binding.measurement_type.strip().lower() != "voltage":
            raise ValueError("ANSI 21 voltage coverage must reference a voltage binding.")
        if current_binding.measurement_type.strip().lower() != "current":
            raise ValueError("ANSI 21 current coverage must reference a current binding.")
        if not voltage_binding.source_endpoint_reference.is_terminal:
            raise ValueError("ANSI 21 voltage source must be an explicit PT/CVT primary terminal.")
        voltage_source = network.get_by_identity(voltage_binding.instrument_id)
        if not isinstance(voltage_source, (PT, CVT)):
            raise ValueError("ANSI 21 voltage binding must reference a physical PT or CVT.")
        primary_role = voltage_binding.source_endpoint_reference.terminal_role.upper()
        if primary_role not in {"PRIMARY_A", "PRIMARY_B", "H1", "H2"}:
            raise ValueError("ANSI 21 voltage binding must identify a PT/CVT primary terminal.")
        local_line_endpoint = line_endpoints[self.local_end]
        reachable = set(reachability.reachable(local_line_endpoint))
        from core.network.topology_endpoint_reference import TopologyEndpointReference
        voltage_endpoint = TopologyEndpointReference.from_terminal(voltage_binding.source_endpoint_reference)
        if voltage_endpoint not in reachable:
            raise ValueError("Configured PT/CVT primary terminal is not conductively associated with the local protected-line end.")


__all__ = ["DistanceProtectionCoverage"]
