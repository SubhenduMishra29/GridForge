"""Numerical short-circuit execution boundary."""

from __future__ import annotations

import cmath
import math
from typing import Any

import numpy as np

from .fault_types import FaultType
from .input import ShortCircuitInput
from .result import (
    ContributionStatus,
    ShortCircuitBranchCurrent,
    ShortCircuitEquipmentCurrent,
    ShortCircuitResult,
    ShortCircuitSourceContribution,
)
from .sequence_snapshot import SequenceBranchSnapshot, SequenceSourceSnapshot
from .symmetrical_fault import SymmetricalFault
from .unsymmetrical_fault import UnsymmetricalFault


class ShortCircuitSolver:
    """Execute a prepared short-circuit problem without live Core access."""

    def __init__(self, input_data: ShortCircuitInput) -> None:
        if not isinstance(input_data, ShortCircuitInput):
            raise TypeError("ShortCircuitSolver requires a ShortCircuitInput.")
        self.input = input_data
        self.last_result: ShortCircuitResult | None = None

    def _execute(self) -> dict:
        data = self.input
        if data.fault_type is FaultType.THREE_PHASE:
            if data.thevenin_impedance is None:
                raise ValueError("Three-phase short-circuit input requires a Thevenin impedance.")
            return SymmetricalFault(data.thevenin_impedance).calculate_three_phase_fault(
                bus_index=data.fault_bus_index,
                Vprefault=data.prefault_voltage,
                Zf=data.fault_impedance,
            )
        if data.sequence_snapshot is None:
            raise ValueError("Unsymmetrical short-circuit input requires a sequence snapshot.")
        return UnsymmetricalFault(
            data.sequence_snapshot,
            fault_bus_index=data.fault_bus_index,
        ).calculate(
            fault_type=data.fault_type,
            elements=data.sequence_elements,
            Vprefault=data.prefault_voltage,
            Zf=data.fault_impedance,
        )

    @staticmethod
    def _phase_from_sequence(sequence_currents: dict[str, complex]) -> dict[str, complex]:
        i1 = complex(sequence_currents.get("I1", 0.0j))
        i2 = complex(sequence_currents.get("I2", 0.0j))
        i0 = complex(sequence_currents.get("I0", 0.0j))
        a = cmath.exp(1j * 2.0 * math.pi / 3.0)
        return {
            "Ia": i0 + i1 + i2,
            "Ib": i0 + (a ** 2) * i1 + a * i2,
            "Ic": i0 + a * i1 + (a ** 2) * i2,
        }

    def _fault_typed_quantities(self, values: dict) -> dict[str, Any]:
        sequence = {str(key): complex(value) for key, value in values.get("sequence_currents", {}).items()}
        phase = {str(key): complex(value) for key, value in values.get("phase_currents", {}).items()}
        if not phase:
            phase = self._phase_from_sequence(sequence)
        if self.input.fault_type is FaultType.THREE_PHASE:
            fault = complex(values["fault_current"])
            sequence = {"I1": fault, "I2": 0.0j, "I0": 0.0j}
            a = cmath.exp(1j * 2.0 * math.pi / 3.0)
            phase = {"Ia": fault, "Ib": fault * a ** 2, "Ic": fault * a}
            ground = 0.0j
        else:
            ground = complex(values.get("ground_current", sum(phase.values())))
        return {
            "fault_current": complex(values["fault_current"]),
            "fault_current_magnitude": float(values["fault_current_magnitude"]),
            "fault_current_angle_deg": float(values["fault_current_angle_deg"]),
            "sequence_currents": sequence,
            "phase_currents": phase,
            "ground_current": ground,
            "ground_current_magnitude": float(abs(ground)),
        }

    def _bus_voltages(self, typed: dict[str, Any]) -> dict[str, np.ndarray] | None:
        snapshot = self.input.sequence_snapshot
        prefault = self.input.prefault_voltages
        if snapshot is None or prefault is None:
            return None
        prefault_vector = np.asarray(prefault, dtype=complex)
        if len(prefault_vector) != len(self.input.bus_ids):
            return None
        fault_index = self.input.fault_bus_index
        voltages: dict[str, np.ndarray] = {}
        sequences = ("positive",) if self.input.fault_type is FaultType.THREE_PHASE else ("positive", "negative", "zero")
        fault_currents = typed["sequence_currents"]
        names = {"positive": "I1", "negative": "I2", "zero": "I0"}
        for sequence in sequences:
            if not snapshot.has_matrix(sequence):
                return None
            matrix = snapshot.get_matrix(sequence)
            base = prefault_vector if sequence == "positive" else np.zeros(len(prefault_vector), dtype=complex)
            current = complex(fault_currents.get(names[sequence], 0.0j))
            voltages[sequence] = base - matrix[:, fault_index] * current
        return voltages

    def _required_for_fault(self) -> tuple[str, ...]:
        if self.input.fault_type is FaultType.THREE_PHASE:
            return ("positive",)
        if self.input.fault_type is FaultType.LINE_LINE:
            return ("positive", "negative")
        return ("positive", "negative", "zero")

    def _source_current_sequences(self, source: SequenceSourceSnapshot, voltages: dict[str, np.ndarray]) -> dict[str, complex] | None:
        required = self._required_for_fault()
        result: dict[str, complex] = {}
        names = {"positive": "I1", "negative": "I2", "zero": "I0"}
        for sequence in required:
            impedance = getattr(source, sequence)
            if impedance is None:
                return None
            voltage = voltages[sequence][source.bus_index]
            internal = source.internal_voltage if sequence == "positive" else 0.0j
            result[names[sequence]] = (internal - voltage) / impedance
        return result

    def _branch_current_sequences(self, branch: SequenceBranchSnapshot, voltages: dict[str, np.ndarray]) -> dict[str, complex] | None:
        required = self._required_for_fault()
        result: dict[str, complex] = {}
        names = {"positive": "I1", "negative": "I2", "zero": "I0"}
        for sequence in required:
            impedance = getattr(branch, sequence)
            if impedance is None:
                return None
            result[names[sequence]] = (voltages[sequence][branch.from_bus_index] - voltages[sequence][branch.to_bus_index]) / impedance
        return result

    @staticmethod
    def _polar(current: complex) -> tuple[float, float]:
        return float(abs(current)), float(math.degrees(cmath.phase(current)))

    def _calculate_contributions(self, typed: dict[str, Any]) -> tuple[dict[str, ShortCircuitSourceContribution], dict[str, ShortCircuitEquipmentCurrent], dict[str, ShortCircuitBranchCurrent]]:
        snapshot = self.input.sequence_snapshot
        if snapshot is None or not snapshot.bus_ids or self.input.prefault_voltages is None:
            return {}, {}, {}
        voltages = self._bus_voltages(typed)
        if voltages is None:
            return {}, {}, {}

        sources: dict[str, ShortCircuitSourceContribution] = {}
        equipment: dict[str, ShortCircuitEquipmentCurrent] = {}
        branches: dict[str, ShortCircuitBranchCurrent] = {}

        for source in snapshot.sources:
            sequence_currents = self._source_current_sequences(source, voltages)
            if sequence_currents is None:
                continue
            phase = self._phase_from_sequence(sequence_currents)
            current = phase["Ia"]
            magnitude, angle = self._polar(current)
            sources[source.source_id] = ShortCircuitSourceContribution(
                source_id=source.source_id,
                source_type=source.source_type,
                bus_id=source.bus_id,
                current=current,
                magnitude=magnitude,
                angle_deg=angle,
                sequence_currents=sequence_currents,
                phase_currents=phase,
            )
            equipment[source.source_id] = ShortCircuitEquipmentCurrent(
                equipment_id=source.source_id,
                equipment_type=source.source_type,
                current=current,
                magnitude=magnitude,
                angle_deg=angle,
                bus_id=source.bus_id,
                sequence_currents=sequence_currents,
                phase_currents=phase,
            )

        for branch in snapshot.branches:
            sequence_currents = self._branch_current_sequences(branch, voltages)
            if sequence_currents is None:
                continue
            phase = self._phase_from_sequence(sequence_currents)
            current = phase["Ia"]
            magnitude, angle = self._polar(current)
            branches[branch.branch_id] = ShortCircuitBranchCurrent(
                branch_id=branch.branch_id,
                from_bus_id=branch.from_bus_id,
                to_bus_id=branch.to_bus_id,
                current=current,
                magnitude=magnitude,
                angle_deg=angle,
                sequence_currents=sequence_currents,
                phase_currents=phase,
            )
            if branch.branch_id in equipment:
                raise ValueError(f"Duplicate equipment identity '{branch.branch_id}' in short-circuit contribution data.")
            equipment[branch.branch_id] = ShortCircuitEquipmentCurrent(
                equipment_id=branch.branch_id,
                equipment_type=branch.equipment_type,
                current=current,
                magnitude=magnitude,
                angle_deg=angle,
                sequence_currents=sequence_currents,
                phase_currents=phase,
            )
        return sources, equipment, branches

    def _contribution_status(
        self,
        sources: dict[str, ShortCircuitSourceContribution],
        equipment: dict[str, ShortCircuitEquipmentCurrent],
        branches: dict[str, ShortCircuitBranchCurrent],
    ) -> tuple[ContributionStatus, tuple[str, ...]]:
        """Classify contribution coverage without silently dropping unavailable records."""
        snapshot = self.input.sequence_snapshot
        if snapshot is None:
            return ContributionStatus.UNAVAILABLE, ("Sequence-network contribution snapshot is unavailable.",)
        expected_sources = {record.source_id for record in snapshot.sources}
        expected_branches = {record.branch_id for record in snapshot.branches}
        prepared_ids = expected_sources | expected_branches
        expected_ids = {str(element_id) for element_id in self.input.sequence_elements}
        diagnostics: list[str] = []
        missing_sources = sorted(expected_sources - set(sources))
        missing_branches = sorted(expected_branches - set(branches))
        omitted_inputs = sorted(expected_ids - prepared_ids)
        if missing_sources:
            diagnostics.append(f"Source contribution unavailable for: {', '.join(missing_sources)}.")
        if missing_branches:
            diagnostics.append(f"Branch contribution unavailable for: {', '.join(missing_branches)}.")
        if omitted_inputs:
            diagnostics.append(f"Prepared contribution input omitted from the snapshot: {', '.join(omitted_inputs)}.")
        if not expected_sources and not expected_branches:
            if omitted_inputs:
                return ContributionStatus.PARTIAL, tuple(diagnostics)
            return ContributionStatus.UNAVAILABLE, ("No prepared source or branch contribution records are available.",)
        if diagnostics:
            return ContributionStatus.PARTIAL, tuple(diagnostics)
        return ContributionStatus.COMPLETE, ()

    def solve(self) -> ShortCircuitResult:
        """Execute exactly once from the immutable input contract."""
        values = self._execute()
        typed = self._fault_typed_quantities(values)
        source_contributions, equipment_currents, branch_currents = self._calculate_contributions(typed)
        contribution_status, contribution_diagnostics = self._contribution_status(source_contributions, equipment_currents, branch_currents)
        provenance = {
            "input_contract": "ShortCircuitInput",
            "fault_bus_id": self.input.fault_bus_id,
            "bus_ids": tuple(self.input.bus_ids),
            "sequence_snapshot": self.input.sequence_snapshot is not None,
            "source_ids": tuple(source_contributions.keys()),
            "equipment_ids": tuple(equipment_currents.keys()),
            "branch_ids": tuple(branch_currents.keys()),
        }
        values = dict(values)
        values.update({
            "source_contributions": source_contributions,
            "equipment_currents": equipment_currents,
            "branch_currents": branch_currents,
            "contribution_status": contribution_status,
            "contribution_diagnostics": contribution_diagnostics,
        })
        result = ShortCircuitResult(
            fault_type=self.input.fault_type,
            fault_bus_index=self.input.fault_bus_index,
            fault_bus_id=self.input.fault_bus_id,
            success=True,
            values=values,
            fault_current=typed["fault_current"],
            fault_current_magnitude=typed["fault_current_magnitude"],
            fault_current_angle_deg=typed["fault_current_angle_deg"],
            sequence_currents=typed["sequence_currents"],
            phase_currents=typed["phase_currents"],
            ground_current=typed["ground_current"],
            ground_current_magnitude=typed["ground_current_magnitude"],
            source_contributions=source_contributions,
            equipment_currents=equipment_currents,
            branch_currents=branch_currents,
            provenance=provenance,
            contribution_status=contribution_status,
            diagnostics=contribution_diagnostics,
        )
        self.last_result = result
        return result

    def calculate(self) -> ShortCircuitResult:
        return self.solve()

    def reset(self) -> None:
        self.last_result = None

    def summary(self) -> dict:
        return {
            "solver": "ShortCircuitSolver",
            "version": "2.0",
            "fault_type": self.input.fault_type.value,
            "bus_index": self.input.fault_bus_index,
            "sequence_data_available": self.input.sequence_snapshot is not None,
            "contribution_data_available": bool(self.input.sequence_snapshot and self.input.sequence_snapshot.sources),
            "last_result_available": self.last_result is not None,
        }

    def __repr__(self) -> str:
        return f"ShortCircuitSolver(fault_type={self.input.fault_type.value}, bus_index={self.input.fault_bus_index})"


__all__ = ["ShortCircuitSolver"]
