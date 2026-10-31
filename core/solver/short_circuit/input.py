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
