"""Immutable numerical input contract for short-circuit execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .fault_types import FaultType
from .sequence_snapshot import SequenceNetworkSnapshot


@dataclass(frozen=True, slots=True)
class ShortCircuitInput:
    """Prepared, immutable data consumed by ``ShortCircuitSolver``.

    All Core reads occur before construction. The solver receives this
    value object and therefore has no live ``Network``, ``Bus`` or mutable
    ``SequenceNetwork`` dependency.
    """

    fault_type: FaultType
    fault_bus_index: int
    fault_bus_id: Any
    prefault_voltage: complex
    fault_impedance: complex
    bus_ids: tuple[Any, ...]
    thevenin_impedance: complex | None = None
    zbus: tuple[tuple[complex, ...], ...] | None = None
    sequence_snapshot: SequenceNetworkSnapshot | None = None
    sequence_elements: tuple[Any, ...] = ()
    prefault_voltages: tuple[complex, ...] | None = None
    project_id: str | None = None
    activation_generation: int | None = None
    topology_revision: int | None = None
    base_mva: float | None = None
    bus_voltage_bases_kv: Mapping[str, float] = field(default_factory=dict)
    phase_domain_case: Any | None = None

    def _validate_phase_domain_fault_type(self, case: Any) -> None:
        """Require explicit fault connections to match the selected engineering fault type."""
        from core.network.phase_domain_conductor_network import PhaseDomainNodeKind

        def phase_node(node_id: str):
            node = case.graph.node(node_id)
            if node.kind in {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE, PhaseDomainNodeKind.FAULT_NODE}:
                return None
            return node if node.conductor_role in {"A", "B", "C"} else None

        def earth_node(node_id: str):
            node = case.graph.node(node_id)
            return node if node.kind in {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE} else None

        faults = tuple(case.faults)
        if self.fault_type is FaultType.THREE_PHASE:
            if len(faults) != 3:
                raise ValueError("A phase-domain THREE_PHASE fault requires exactly three phase-to-fault-star connections.")
            phase_roles = set()
            star_ids = set()
            for fault in faults:
                left, right = case.graph.node(fault.from_node_id), case.graph.node(fault.to_node_id)
                phases = [node for node in (phase_node(left.node_id), phase_node(right.node_id)) if node is not None]
                stars = [node for node in (left, right) if node.kind is PhaseDomainNodeKind.FAULT_NODE]
                if len(phases) != 1 or len(stars) != 1:
                    raise ValueError("Each THREE_PHASE fault leg must connect exactly one A/B/C conductor to one explicit FAULT_NODE.")
                phase_roles.add(phases[0].conductor_role)
                star_ids.add(stars[0].node_id)
            if phase_roles != {"A", "B", "C"} or len(star_ids) != 1:
                raise ValueError("THREE_PHASE fault legs must connect A, B, and C exactly once to one common fault-star node.")
            star_id = next(iter(star_ids))
            if case.graph.connections_for_node(star_id):
                raise ValueError("A THREE_PHASE fault-star node cannot have additional graph connections.")
            return

        if self.fault_type is FaultType.LINE_LINE:
            if len(faults) != 1:
                raise ValueError("A phase-domain LINE_LINE fault requires exactly one phase-to-phase fault connection.")
            fault = faults[0]
            left, right = phase_node(fault.from_node_id), phase_node(fault.to_node_id)
            if left is None or right is None or left.conductor_role == right.conductor_role:
                raise ValueError("LINE_LINE fault must connect two distinct A/B/C phase conductors and must not include earth.")
            return

        if self.fault_type is FaultType.SINGLE_LINE_GROUND:
            if len(faults) != 1:
                raise ValueError("A phase-domain SINGLE_LINE_GROUND fault requires exactly one phase-to-earth connection.")
            fault = faults[0]
            phase = phase_node(fault.from_node_id) or phase_node(fault.to_node_id)
            earth = earth_node(fault.to_node_id) or earth_node(fault.from_node_id)
            if phase is None or earth is None:
                raise ValueError("SINGLE_LINE_GROUND fault must connect exactly one A/B/C phase conductor to an explicit earth node.")
            if not case.graph.earth_reachable(earth.node_id):
                raise ValueError("SINGLE_LINE_GROUND fault has no explicit earth-return path to EARTH_REFERENCE.")
            return

        if self.fault_type is FaultType.DOUBLE_LINE_GROUND:
            if len(faults) != 2:
                raise ValueError("A phase-domain DOUBLE_LINE_GROUND fault requires exactly two phase-to-common-earth connections.")
            phase_roles, earth_ids = set(), set()
            for fault in faults:
                phase = phase_node(fault.from_node_id) or phase_node(fault.to_node_id)
                earth = earth_node(fault.to_node_id) or earth_node(fault.from_node_id)
                if phase is None or earth is None:
                    raise ValueError("Each DOUBLE_LINE_GROUND fault leg must connect one A/B/C phase conductor to an explicit earth node.")
                phase_roles.add(phase.conductor_role)
                earth_ids.add(earth.node_id)
                if not case.graph.earth_reachable(earth.node_id):
                    raise ValueError("DOUBLE_LINE_GROUND fault has no explicit earth-return path to EARTH_REFERENCE.")
            if len(phase_roles) != 2 or len(earth_ids) != 1:
                raise ValueError("DOUBLE_LINE_GROUND requires two distinct phases connected to one common explicit earth fault node.")
            return

        raise ValueError(f"Unsupported phase-domain fault classification: {self.fault_type!r}.")

    def __post_init__(self) -> None:
        if isinstance(self.fault_bus_index, bool) or not isinstance(self.fault_bus_index, int):
            raise TypeError("fault_bus_index must be an integer.")
        if not self.bus_ids:
            raise ValueError("bus_ids cannot be empty.")
        if not 0 <= self.fault_bus_index < len(self.bus_ids):
            raise IndexError("fault_bus_index is outside bus_ids.")
        if self.bus_ids[self.fault_bus_index] != self.fault_bus_id:
            raise ValueError("fault_bus_id must match bus_ids[fault_bus_index].")
        object.__setattr__(self, "prefault_voltage", complex(self.prefault_voltage))
        object.__setattr__(self, "fault_impedance", complex(self.fault_impedance))
        object.__setattr__(self, "bus_ids", tuple(self.bus_ids))
        object.__setattr__(self, "sequence_elements", tuple(self.sequence_elements))
        if self.prefault_voltages is not None:
            voltages = tuple(complex(value) for value in self.prefault_voltages)
            if len(voltages) != len(self.bus_ids):
                raise ValueError("prefault_voltages length must match bus_ids.")
            object.__setattr__(self, "prefault_voltages", voltages)
        if self.zbus is not None:
            zbus = tuple(tuple(complex(value) for value in row) for row in self.zbus)
            if len(zbus) != len(self.bus_ids) or any(len(row) != len(self.bus_ids) for row in zbus):
                raise ValueError("zbus dimensions must match bus_ids.")
            object.__setattr__(self, "zbus", zbus)
        if self.thevenin_impedance is not None:
            object.__setattr__(self, "thevenin_impedance", complex(self.thevenin_impedance))
        if self.project_id is not None and not str(self.project_id).strip():
            raise ValueError("Short Circuit project_id must be non-empty when supplied.")
        if self.activation_generation is not None and (isinstance(self.activation_generation, bool) or int(self.activation_generation) < 1):
            raise ValueError("Short Circuit activation_generation must be positive when supplied.")
        if self.topology_revision is not None and (isinstance(self.topology_revision, bool) or int(self.topology_revision) < 0):
            raise ValueError("Short Circuit topology_revision must be non-negative when supplied.")
        if self.base_mva is not None:
            import math
            base_mva = float(self.base_mva)
            if not math.isfinite(base_mva) or base_mva <= 0.0:
                raise ValueError("Short Circuit base_mva must be finite and positive when supplied.")
            object.__setattr__(self, "base_mva", base_mva)
        if self.phase_domain_case is not None:
            from .phase_domain_solver import PhaseDomainShortCircuitCase
            if not isinstance(self.phase_domain_case, PhaseDomainShortCircuitCase):
                raise TypeError("phase_domain_case must be a PhaseDomainShortCircuitCase.")
            case = self.phase_domain_case
            fault_bus_ids = {
                node.bus_id
                for fault in case.faults
                for node in (case.graph.node(fault.from_node_id), case.graph.node(fault.to_node_id))
                if node.kind.value not in {"EARTH_NODE", "EARTH_REFERENCE"} and node.bus_id is not None
            }
            if fault_bus_ids != {str(self.fault_bus_id)}:
                raise ValueError("Every phase-domain fault connection must be located at the ShortCircuitInput fault Bus.")
            self._validate_phase_domain_fault_type(case)
            if (case.graph.project_id, case.graph.activation_generation, case.graph.topology_revision) != (
                self.project_id, self.activation_generation, self.topology_revision
            ):
                raise ValueError("Phase-domain case provenance does not match ShortCircuitInput.")
            if self.base_mva is None or not math.isclose(case.base_mva, float(self.base_mva), rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError("Phase-domain case must use the exact ShortCircuitInput MVA base.")
        if not isinstance(self.bus_voltage_bases_kv, Mapping):
            raise TypeError("bus_voltage_bases_kv must be a mapping.")
        voltage_bases: dict[str, float] = {}
        for bus_id, value in self.bus_voltage_bases_kv.items():
            if not isinstance(bus_id, str) or not bus_id.strip():
                raise ValueError("bus_voltage_bases_kv keys must be non-empty Bus IDs.")
            voltage = float(value)
            import math
            if not math.isfinite(voltage) or voltage <= 0.0:
                raise ValueError(f"Voltage base for Bus {bus_id!r} must be finite and positive.")
            voltage_bases[bus_id.strip()] = voltage
        if not set(voltage_bases).issubset(set(self.bus_ids)):
            raise ValueError("bus_voltage_bases_kv contains a Bus outside bus_ids.")
        object.__setattr__(self, "bus_voltage_bases_kv", MappingProxyType(voltage_bases))
